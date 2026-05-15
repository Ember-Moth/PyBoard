"""主题配置服务。"""

import base64
from pathlib import Path
from typing import Any

import orjson

from app.core.exceptions import BadRequestException, NotFoundException
from app.services.setting import SettingService


class ThemeService:
    """读取本地主题配置，并把用户配置保存到 setting 表。"""

    def __init__(self, setting_service: SettingService, theme_path: str = "public/theme"):
        self.setting_service = setting_service
        self.theme_path = Path(theme_path)

    async def list_themes(self) -> dict[str, Any]:
        themes: dict[str, Any] = {}
        if self.theme_path.exists():
            for item in self.theme_path.iterdir():
                if not item.is_dir():
                    continue
                config_file = item / "config.json"
                if not config_file.exists():
                    continue
                try:
                    config = orjson.loads(config_file.read_bytes())
                except orjson.JSONDecodeError:
                    continue
                if isinstance(config, dict) and isinstance(config.get("configs"), list):
                    themes[item.name] = config
        return {
            "themes": themes,
            "active": await self.setting_service.get_str("frontend_theme", "pyboard"),
        }

    async def get_theme_config(self, name: str) -> dict[str, Any]:
        await self._ensure_theme_exists(name)
        return await self.setting_service.get_json(f"theme_config_{name}", {})

    async def save_theme_config(self, name: str, config: str | dict[str, Any]) -> dict[str, Any]:
        theme_config = await self._load_theme_config(name)
        payload = self._decode_payload(config)
        fields = [item.get("field_name") for item in theme_config.get("configs", []) if item.get("field_name")]
        saved = {field: payload.get(field, "") for field in fields}
        await self.setting_service.set(f"theme_config_{name}", saved, "json")
        return saved

    async def _ensure_theme_exists(self, name: str) -> None:
        await self._load_theme_config(name)

    async def _load_theme_config(self, name: str) -> dict[str, Any]:
        if not name or "/" in name or "\\" in name:
            raise BadRequestException("主题名称无效")
        config_file = self.theme_path / name / "config.json"
        if not config_file.exists():
            raise NotFoundException("主题不存在")
        try:
            config = orjson.loads(config_file.read_bytes())
        except orjson.JSONDecodeError as exc:
            raise BadRequestException("主题配置文件无效") from exc
        if not isinstance(config, dict) or not isinstance(config.get("configs"), list):
            raise BadRequestException("主题配置文件无效")
        return config

    def _decode_payload(self, config: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(config, dict):
            return config
        try:
            decoded = base64.b64decode(config)
            payload = orjson.loads(decoded)
        except (ValueError, orjson.JSONDecodeError) as exc:
            raise BadRequestException("主题配置参数无效") from exc
        if not isinstance(payload, dict):
            raise BadRequestException("主题配置参数无效")
        return payload
