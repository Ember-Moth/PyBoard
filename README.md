# PyBoard

PyBoard 是一个独立的 FastAPI 后端实现，提供用户、套餐、订单、支付、订阅、节点、日志、统计和管理后台等面板核心能力，并面向 PostgreSQL 重新设计运行时、队列、缓存和迁移体系。

项目采用 Controller -> Service -> Repository 分层架构，提供 REST API、服务端渲染 Admin HTML、支付网关抽象、订阅模板渲染、节点服务端接口和 PostgreSQL 队列 Worker。

## 核心特性

- 只依赖 PostgreSQL，不需要 Redis、SQLite 或 MySQL。
- 使用 PostgreSQL JSONB、UNLOGGED runtime cache、表队列和 pg_cron。
- REST API 统一挂载在 `/api/v1`，节点配置接口为 `/api/v2/server/config`。
- Admin HTML 使用 Jinja2 + htmx + Tabler.io，路由位于 `/admin/*`。
- 支付网关开放式注册，当前内置 EPay，回调路径为 `/notify/{gateway}/{uuid}`。
- 订阅模块使用 Jinja2 模板，支持 Clash/Mihomo、sing-box、Surge、Surfboard、Loon、Quantumult X、Shadowrocket、SIP008、v2rayN/v2rayNG 等客户端格式。
- 队列使用 PostgreSQL `FOR UPDATE SKIP LOCKED` 并发领取任务，失败任务持久化。
- `created_at` / `updated_at` 由 PostgreSQL DEFAULT 和触发器维护。

## 技术栈

| 组件 | 选型 |
|------|------|
| Web 框架 | FastAPI |
| ORM | SQLModel / SQLAlchemy async |
| 数据库 | PostgreSQL |
| 运行期缓存 | PostgreSQL UNLOGGED table |
| 队列 | PostgreSQL table queue |
| 定时任务 | pg_cron |
| 模板 | Jinja2 |
| Admin UI | htmx + Tabler.io |
| 认证 | JWT + Argon2id / Bcrypt upgrade |
| 包管理 | uv |
| Python | >= 3.14 |

## 文档

- [开发文档](docs/development.md)
- [使用与部署文档](docs/deployment.md)
- [环境变量示例](.env.example)

## 主要入口

- REST/OpenAPI: `/docs`
- Admin HTML: `/admin`
- 健康检查: `/health`
- 用户订阅: `/api/v1/client/subscribe`
- 节点配置: `/api/v2/server/config`
- UniProxy 兼容接口: `/api/v1/server/uniproxy/*`
- 支付回调: `/notify/{gateway}/{uuid}`

## 当前状态

项目核心模块已完成：认证、用户、套餐、订单、支付、优惠券、礼品卡、邀请返利、工单、公告、知识库、订阅、节点、统计、日志、邮件、主题、Admin HTML、队列和 PostgreSQL runtime cache。
