# 开发文档

本文档面向项目开发者，说明本项目的本地开发流程、架构边界、编码约定和扩展方式。

## 环境要求

- Python >= 3.14
- uv
- PostgreSQL 18
- 可选：pg_cron，用于数据库内定时入队

项目已经放弃 SQLite、MySQL 和 Redis。运行期缓存、队列、定时任务和业务数据都围绕 PostgreSQL 设计。

## 本地启动

```bash
uv sync
cp .env.example .env
uv run uvicorn main:app --reload
```

常用地址：

- REST/OpenAPI: `http://127.0.0.1:8000/docs`
- Admin HTML: `http://127.0.0.1:8000/admin`
- 健康检查: `http://127.0.0.1:8000/health`

## 项目结构

```text
main.py
alembic/
app/
  admin_ui/       # Admin HTML 页面、fragment、action 路由
  controllers/    # REST 控制器
  core/           # 配置、数据库、缓存、队列、依赖注入、异常处理
  migrations/     # seed 初始化
  models/         # SQLModel Entity/DTO
  payments/       # 支付网关抽象与实现
  queues/         # PostgreSQL 队列 Worker 与任务
  repositories/   # 数据访问层
  services/       # 业务服务层
  templates/      # Admin、邮件、订阅模板
  utils/          # 密码、模板等工具
tests/
```

## 架构分层

请求链路：

```text
Controller -> Service -> Repository -> PostgreSQL
              |
              +-> Queue / Payment Gateway / Template
```

职责边界：

- Controller：解析请求、依赖注入、返回 `ApiResponse`，不写业务规则。
- Service：业务规则、事务边界、跨 Repository 编排。
- Repository：模型查询和持久化，不写业务流程。
- Model：数据库实体、DTO 和字段定义。
- Template：Admin HTML、邮件、订阅协议输出。

## 依赖注入

依赖集中在 `app/core/deps.py`：

```python
DbDep = Depends(get_db)
CacheDep = Depends(get_cache)
QueueDep = Depends(get_queue)
```

业务控制器优先注入 Service：

```python
@router.get("")
async def list_items(service: ItemService = Depends(get_item_service)):
    return success(data=await service.list_items())
```

不要在 Controller 中直接拼 SQL 或直接创建数据库连接。

## 响应和异常

REST API 统一返回：

```json
{"code": 200, "msg": "success", "data": {}}
```

Controller 使用：

```python
return success(data=item)
return created(data=item)
```

业务错误抛出 `app.core.exceptions` 中的类型化异常：

- `BadRequestException` -> 400
- `UnauthorizedException` -> 401
- `ForbiddenException` -> 403
- `NotFoundException` -> 404
- `ConflictException` -> 409

## 模型规范

每个模型目录通常包含：

```text
app/models/<name>/
  __init__.py
  base.py      # 字段全集，不含 id / 时间戳 / 关系
  entity.py    # SQLModel table 实体
  dto.py       # API 输入输出 DTO
```

时间戳字段使用 `app/models/_columns.py` 中的 helper：

```python
created_at: int | None = created_at_field()
updated_at: int | None = updated_at_field()
```

`created_at` 和 `updated_at` 由 PostgreSQL DEFAULT 和触发器维护。业务代码和 Repository 不应手动写这些字段。

JSON 字段使用 JSONB helper，避免把 JSON 当字符串处理。

## 数据库迁移

修改模型后生成迁移：

```bash
uv run alembic revision --autogenerate -m "add example table"
```

执行迁移：

```bash
uv run alembic upgrade head
```

应用启动时会执行 `init_db()`，自动升级到 head，并执行幂等 seed 初始化。默认配置 seed 位于：

```text
app/services/setting_defaults.py
app/migrations/seeds.py
```

迁移约定：

- 项目只支持 PostgreSQL。
- JSON 类字段使用 JSONB。
- 队列表 `queue_job` 使用 logged table，不能改成 UNLOGGED。
- 运行期缓存和流量暂存使用 UNLOGGED table。
- 强一致业务状态必须落普通业务表，不放 runtime cache。

## PostgreSQL Runtime Cache

`app/core/cache.py` 提供 Redis 替代层：

```python
await cache.get("key")
await cache.set("key", value, ex=60)
await cache.set("key", value, ex=60, nx=True)
await cache.incr("counter", ex=60)
await cache.delete("key")
await cache.mget(["a", "b"])
```

底层表：

- `runtime_cache`：验证码、临时 token、在线状态、限流计数、短期去重。
- `traffic_cache`：节点流量暂存。

这些表是 UNLOGGED，数据库崩溃恢复后可能被清空，只能存放可丢失数据。

## 队列系统

队列使用 PostgreSQL 表队列：

- 入队客户端：`app/core/queue.py`
- Worker：`app/queues/worker.py`
- 任务注册：`app/queues/jobs/__init__.py`
- 队列名：`app/queues/names.py`
- 失败记录：`failed_jobs`

启动 Worker：

```bash
uv run python -m app.queues.worker
```

单次执行一轮，适合测试：

```bash
uv run python -m app.queues.worker --once
```

新增任务：

1. 在 `app/queues/jobs/<name>.py` 中定义 async 函数。
2. 在 `app/queues/jobs/__init__.py` 中注册。
3. 需要指定队列时使用 `app/queues/names.py` 中的常量。
4. 任务参数必须可 JSON 序列化。

周期性任务由 pg_cron 调用数据库函数入队。没有 pg_cron 时，迁移会跳过调度注册，Worker 和手动入队仍可工作。

## Admin HTML

Admin UI 使用 Jinja2 + htmx + Tabler.io，路由不使用 `/api` 前缀。

- 页面路由：`/admin/users`
- Fragment 路由：`/admin/fragments/users/table`
- Action 路由：`/admin/actions/users/{id}`
- 登录 Cookie：`admin_token`
- CSRF Cookie：`admin_csrf`

开发约定：

- 页面模板只负责布局和 fragment 加载点。
- 表格、表单、详情弹窗放在 `app/templates/admin/fragments/`。
- Action 路由调用 Service，返回更新后的 HTML fragment。
- 不在模板中复制业务规则。
- 表单字段使用面向用户的中文标签，不直接暴露 DTO/entity 字段名。

## 订阅模板

订阅模块由 `SubscribeService` 负责取数、格式识别和响应头，协议输出交给模板：

```text
app/templates/subscribe/
  _protocols.j2
  clash.yaml.j2
  singbox.json.j2
  uri.txt.j2
  ...
```

新增客户端格式时：

1. 在模板或 `_protocols.j2` 中实现输出。
2. 在 `_detect_format()` 中加入客户端识别。
3. 在 `_template_for_format()` 中选择模板和 media type。
4. 添加订阅渲染测试。

## 支付网关

支付网关是开放式注册：

```text
app/payments/base.py
app/payments/registry.py
app/payments/epay.py
```

新增网关：

1. 继承 `PaymentGateway`。
2. 实现配置表单、支付链接生成、回调验证。
3. 注册到 registry。
4. 回调只接收 JSON，路径为 `/notify/{gateway}/{uuid}`。

EPay 的支付流程是后端拼好 `submit.php?...` URL 返回给前端，前端负责跳转。

## 测试和检查

```bash
uv run ruff check app tests main.py alembic
uv run ruff check --fix .
uv run pytest
uv run pytest tests/test_admin_ui.py
```

测试默认使用 PostgreSQL。可通过环境变量指定连接：

```bash
PG_HOST=127.0.0.1
PG_PORT=5432
PG_USER=pyboard_admin
PG_PASSWORD=your-password
PG_DATABASE=pyboard_db
```

## 提交前检查

提交前至少执行：

```bash
uv run ruff check app tests main.py alembic
uv run alembic upgrade head
uv run python -m app.queues.worker --once
uv run pytest
```

如修改了依赖，执行：

```bash
uv lock
```
