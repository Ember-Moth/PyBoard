"""Setting 服务层 —— 类型化读写 + PostgreSQL runtime cache。"""

from typing import Any

import orjson

from app.core.cache import RuntimeCache
from app.core.exceptions import ConflictException, NotFoundException
from app.models.setting.dto import SettingCreate, SettingPublic, SettingRead, SettingUpdate
from app.models.setting.entity import Setting
from app.repositories.setting import SettingRepository
from app.services.setting_defaults import DEFAULT_SETTING_GROUPS, SettingDefault

_CACHE_PREFIX = "setting:"
_CACHE_TTL = 3600


class SettingService:
    """配置业务逻辑，运行期缓存可选。"""

    def __init__(self, repo: SettingRepository, cache: RuntimeCache | None = None):
        self.repo = repo
        self.cache = cache

    # ---- 类型化读取 ----
    async def get_str(self, key: str, default: str = "") -> str:
        val = await self._get_cached(key)
        return val if val is not None else default

    async def get_int(self, key: str, default: int = 0) -> int:
        val = await self._get_cached(key)
        return int(val) if val is not None else default

    async def get_bool(self, key: str, default: bool = False) -> bool:
        val = await self._get_cached(key)
        if val is None:
            return default
        return val.lower() in ("1", "true", "yes")

    async def get_json(self, key: str, default: Any = None) -> Any:
        if default is None:
            default = {}
        val = await self._get_cached(key)
        return orjson.loads(val) if val is not None else default

    # ---- 写入 ----
    async def set(self, key: str, value: Any, type_: str = "str") -> Setting:
        """设置配置值，自动同步运行期缓存。"""
        str_value = orjson.dumps(value).decode() if type_ == "json" else str(value)
        existing = await self.repo.get_by_key(key)
        if existing:
            existing.value = str_value
            existing.type = type_
            setting = await self.repo.update(existing)
        else:
            setting = Setting(key=key, value=str_value, type=type_)
            setting = await self.repo.create(setting)
        await self._cache_set(key, str_value)
        return setting

    # ---- CRUD ----
    async def list_settings(self, offset: int = 0, limit: int = 100) -> list[SettingPublic]:
        items = await self.repo.get_all(offset, limit)
        return [
            SettingPublic(id=item.id, key=item.key, type=item.type, description=item.description, updated_at=item.updated_at)  # type: ignore[arg-type]
            for item in items
        ]

    async def get_setting(self, setting_id: int) -> SettingRead:
        item = await self.repo.get_by_id(setting_id)
        if item is None:
            raise NotFoundException(f"配置 {setting_id} 不存在")
        return SettingRead(id=item.id, key=item.key, value=item.value, type=item.type, description=item.description, updated_at=item.updated_at)  # type: ignore[arg-type]

    async def create_setting(self, data: SettingCreate) -> SettingRead:
        if await self.repo.get_by_key(data.key):
            raise ConflictException(f"配置 {data.key} 已存在")
        item = Setting(key=data.key, value=data.value, type=data.type, description=data.description)
        item = await self.repo.create(item)
        await self._cache_set(data.key, data.value)
        return SettingRead(id=item.id, key=item.key, value=item.value, type=item.type, description=item.description, updated_at=item.updated_at)  # type: ignore[arg-type]

    async def update_setting(self, setting_id: int, data: SettingUpdate) -> SettingRead:
        item = await self.repo.get_by_id(setting_id)
        if item is None:
            raise NotFoundException(f"配置 {setting_id} 不存在")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        item = await self.repo.update(item)
        await self._cache_set(item.key, item.value)
        return SettingRead(id=item.id, key=item.key, value=item.value, type=item.type, description=item.description, updated_at=item.updated_at)  # type: ignore[arg-type]

    async def delete_setting(self, setting_id: int) -> bool:
        item = await self.repo.get_by_id(setting_id)
        if item is None:
            raise NotFoundException(f"配置 {setting_id} 不存在")
        await self.repo.delete(item)
        await self._cache_delete(item.key)
        return True

    # ---- 按后台配置分组获取 ----
    async def fetch_config(self, group_key: str | None = None) -> dict:
        """按后台配置分组结构获取配置。

        支持的分组：ticket, deposit, invite, site, subscribe, frontend,
        server, email, telegram, app, safe
        """
        selected_groups = (
            {group_key: DEFAULT_SETTING_GROUPS[group_key]}
            if group_key and group_key in DEFAULT_SETTING_GROUPS
            else DEFAULT_SETTING_GROUPS
        )
        return {
            group: {
                item.key: await self._get_defaulted_value(item)
                for item in items
            }
            for group, items in selected_groups.items()
        }

    async def _get_defaulted_value(self, item: SettingDefault) -> Any:
        if item.type == "json":
            value = await self.get_json(item.key, item.value)
        elif item.type == "int":
            value = await self.get_int(item.key, int(item.value))
        else:
            value = await self.get_str(item.key, str(item.value))
        if item.zero_as_none and value == 0:
            return None
        return value

    async def save_config(self, key: str, value: str | int | bool | dict | list) -> bool:
        """保存单个配置项，自动判断类型。"""
        if isinstance(value, bool):
            await self.set(key, int(value), type_="int")
        elif isinstance(value, int):
            await self.set(key, value, type_="int")
        elif isinstance(value, (dict, list)):
            await self.set(key, value, type_="json")
        else:
            await self.set(key, value, type_="str")
        return True

    async def batch_save_config(self, items: dict[str, str | int | bool | dict | list]) -> bool:
        """批量保存多个配置项。"""
        for key, value in items.items():
            await self.save_config(key, value)
        return True

    # ---- 缓存 ----
    async def _get_cached(self, key: str) -> str | None:
        cache_key = f"{_CACHE_PREFIX}{key}"
        val = await self.cache.get(cache_key) if self.cache is not None else None
        if val is not None:
            return str(val)
        # 回源 DB
        item = await self.repo.get_by_key(key)
        if item is None:
            return None
        await self._cache_set(key, item.value)
        return item.value

    async def _cache_set(self, key: str, value: str) -> None:
        cache_key = f"{_CACHE_PREFIX}{key}"
        if self.cache is None:
            return
        await self.cache.set(cache_key, value, ex=_CACHE_TTL)

    async def _cache_delete(self, key: str) -> None:
        cache_key = f"{_CACHE_PREFIX}{key}"
        if self.cache is None:
            return
        await self.cache.delete(cache_key)
