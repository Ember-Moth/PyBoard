# 使用与部署文档

本文档说明如何配置、启动、部署和维护 PyBoard。

## 系统要求

- Python >= 3.14
- uv
- PostgreSQL 18
- 可选：pg_cron，用于数据库内定时任务调度
- 反向代理：Nginx、Caddy 或同类网关

项目不需要 Redis。运行期缓存使用 PostgreSQL UNLOGGED table，队列使用 PostgreSQL 普通表。

## 组件说明

生产环境建议至少运行两个进程：

```text
Web API/Admin HTML: uvicorn main:app
Queue Worker:       python -m app.queues.worker
```

PostgreSQL 承载：

- 业务数据
- `queue_job` 队列任务
- `failed_jobs` 失败任务
- `runtime_cache` 运行期缓存
- `traffic_cache` 节点流量暂存
- pg_cron 定时入队任务

## 数据库准备

示例 SQL：

```sql
CREATE USER pyboard_admin WITH PASSWORD 'change-this-postgres-password';
CREATE DATABASE pyboard_db OWNER pyboard_admin;
GRANT ALL PRIVILEGES ON DATABASE pyboard_db TO pyboard_admin;
```

## pg_cron 安装配置

生产环境建议启用 pg_cron。项目迁移会自动注册定时任务，用于周期性把任务写入 `queue_job`，然后由 Worker 消费。

项目会注册的任务：

- `pyboard_traffic_update_every_minute`：每分钟入队 `traffic_update`。
- `pyboard_check_order_every_5_minutes`：每 5 分钟入队 `check_order`。
- `pyboard_aggregate_yesterday_stats`：每天 00:05 入队 `aggregate_yesterday_stats`。
- `pyboard_runtime_cache_cleanup`：每 10 分钟清理过期运行期缓存。
- `pyboard_cleanup_log_events_daily`：每天 03:25 入队 `cleanup_log_events`，按分类保留策略清理日志。

### 安装扩展包

Debian / Ubuntu，按实际 PostgreSQL 主版本替换 `18`：

```bash
sudo apt update
sudo apt install postgresql-18-cron
```

RHEL / Rocky Linux / AlmaLinux / CentOS，按实际 PostgreSQL 主版本替换 `18`：

```bash
sudo dnf install pg_cron_18
```

如果使用托管 PostgreSQL，通常需要在控制台的参数组或扩展管理页面启用 pg_cron。不同厂商限制不同，核心要求是数据库实例已经加载 `pg_cron`，并且目标数据库可以执行 `CREATE EXTENSION pg_cron`。

### 配置 postgresql.conf

pg_cron 是后台 worker，必须加入 `shared_preload_libraries` 并重启 PostgreSQL。不要覆盖已有值，如果已有 `pg_stat_statements` 等扩展，需要逗号追加。

```conf
shared_preload_libraries = 'pg_cron'
cron.database_name = 'pyboard_db'
cron.timezone = 'Asia/Shanghai'
```

如果已有其他 preload：

```conf
shared_preload_libraries = 'pg_stat_statements,pg_cron'
```

也可以用 SQL 写入配置。下面示例适用于没有其他 preload 扩展的实例；如果已有其他扩展，需要把所有值一起写入，例如 `'pg_stat_statements,pg_cron'`。

```sql
ALTER SYSTEM SET shared_preload_libraries = 'pg_cron';
ALTER SYSTEM SET cron.database_name = 'pyboard_db';
ALTER SYSTEM SET cron.timezone = 'Asia/Shanghai';
```

然后重启 PostgreSQL：

```bash
sudo systemctl restart postgresql
```

### 创建扩展和授权

建议用 PostgreSQL 管理员账号在业务数据库内创建扩展：

```sql
\c pyboard_db
CREATE EXTENSION IF NOT EXISTS pg_cron;
GRANT USAGE ON SCHEMA cron TO pyboard_admin;
```

如果应用数据库用户本身具备创建扩展权限，也可以让迁移自动执行 `CREATE EXTENSION IF NOT EXISTS pg_cron`。生产环境更推荐提前由 DBA 完成安装和授权，应用用户只保留必要权限。

### 验证 pg_cron

确认扩展已加载：

```sql
SELECT extname, extversion FROM pg_extension WHERE extname = 'pg_cron';
SHOW shared_preload_libraries;
SHOW cron.database_name;
SHOW cron.timezone;
```

执行迁移后检查项目任务是否已注册：

```sql
SELECT jobid, jobname, schedule, command, active
FROM cron.job
WHERE jobname LIKE 'pyboard_%'
ORDER BY jobname;
```

确认 Worker 正在消费任务：

```sql
SELECT status, queue, job_name, count(*)
FROM queue_job
GROUP BY status, queue, job_name
ORDER BY status, queue, job_name;
```

如果 `cron.job` 中能看到 `pyboard_%` 任务，但 `queue_job` 任务持续堆积，说明 pg_cron 正常入队，但 Worker 没有正常消费。

如果当前角色没有权限或实例没有安装 pg_cron，迁移会跳过调度注册。应用仍可运行，但周期性任务不会自动入队。

如果 pg_cron 是在迁移完成后才安装的，需要手动补注册项目任务：

```sql
SELECT pyboard_schedule_pg_cron_jobs();

DO $$
BEGIN
    BEGIN
        PERFORM cron.unschedule('pyboard_runtime_cache_cleanup');
    EXCEPTION WHEN others THEN
        NULL;
    END;
    PERFORM cron.schedule(
        'pyboard_runtime_cache_cleanup',
        '*/10 * * * *',
        $cron$SELECT pyboard_cleanup_runtime_cache()$cron$
    );
    BEGIN
        PERFORM cron.unschedule('pyboard_cleanup_log_events_daily');
    EXCEPTION WHEN others THEN
        NULL;
    END;
    PERFORM cron.schedule(
        'pyboard_cleanup_log_events_daily',
        '25 3 * * *',
        $cron$SELECT pyboard_enqueue_queue_job('cleanup_log_events', '[]'::jsonb, '{}'::jsonb, 'default', 'cron:cleanup_log_events:' || to_char(now(), 'YYYYMMDD'))$cron$
    );
END
$$;
```

## 配置文件

复制配置模板：

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

最小配置：

```env
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_ADMIN_PASSWORD=change-this-admin-password

JWT_SECRET_KEY=replace-with-a-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

PG_HOST=127.0.0.1
PG_PORT=5432
PG_USER=pyboard_admin
PG_PASSWORD=change-this-postgres-password
PG_DATABASE=pyboard_db

POOL_SIZE=50
MAX_OVERFLOW=30

QUEUE_DEFAULT_NAME=default
QUEUE_MAX_JOBS=20
QUEUE_POLL_DELAY=0.5
QUEUE_MAX_TRIES=3
QUEUE_RETRY_JOBS=true
QUEUE_HEALTH_CHECK_INTERVAL=300
```

注意：

- 生产环境必须更换 `JWT_SECRET_KEY`。
- `INITIAL_ADMIN_EMAIL` 和 `INITIAL_ADMIN_PASSWORD` 只用于初始化首个管理员。
- `.env` 是本地运行文件，不应提交到版本库。
- Redis 配置已经移除，不需要启动 Redis。

## 初始化数据库

应用启动时会自动执行迁移和 seed。也可以手动执行：

```bash
uv run alembic upgrade head
```

查看当前迁移版本：

```bash
uv run alembic current
```

首次迁移时，如果 `INITIAL_ADMIN_EMAIL` 和 `INITIAL_ADMIN_PASSWORD` 都非空，且系统内没有管理员账户，会自动创建初始管理员。

## 本地运行

安装依赖：

```bash
uv sync
```

启动 Web：

```bash
uv run uvicorn main:app --reload
```

启动 Worker：

```bash
uv run python -m app.queues.worker
```

访问：

- Admin HTML: `http://127.0.0.1:8000/admin`
- API 文档: `http://127.0.0.1:8000/docs`
- 健康检查: `http://127.0.0.1:8000/health`

## 生产运行命令

Web 进程示例：

```bash
uv run uvicorn main:app --host 127.0.0.1 --port 8000 --proxy-headers
```

Worker 进程示例：

```bash
uv run python -m app.queues.worker
```

如果需要限制 Worker 队列：

```bash
uv run python -m app.queues.worker --queue traffic_fetch --queue stat
```

建议使用 systemd、supervisor、Docker Compose 或同类进程管理工具分别托管 Web 和 Worker。

## systemd 示例

Web service：

```ini
[Unit]
Description=PyBoard web
After=network.target postgresql.service

[Service]
WorkingDirectory=/opt/PyBoard
EnvironmentFile=/opt/PyBoard/.env
ExecStart=/opt/PyBoard/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --proxy-headers
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Worker service：

```ini
[Unit]
Description=PyBoard queue worker
After=network.target postgresql.service

[Service]
WorkingDirectory=/opt/PyBoard
EnvironmentFile=/opt/PyBoard/.env
ExecStart=/opt/PyBoard/.venv/bin/python -m app.queues.worker
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

部署时如果使用 `uv run` 启动，也可以把 `ExecStart` 改为：

```ini
ExecStart=/usr/local/bin/uv run uvicorn main:app --host 127.0.0.1 --port 8000 --proxy-headers
```

实际路径以服务器安装位置为准。

## Nginx 反向代理示例

```nginx
server {
    listen 80;
    server_name panel.example.com;

    client_max_body_size 20m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用 HTTPS 后，需要在系统配置里把 `app_url` 设置为外部访问地址，例如：

```text
https://panel.example.com
```

支付回调、订阅地址、Telegram webhook 都依赖正确的外部 URL。

## 常用系统配置

管理后台 `/admin/settings` 可配置站点、订阅、节点、邮件、Telegram、安全等分组。

关键项：

- `app_name`：站点名称。
- `app_url`：外部访问地址。
- `subscribe_url`：订阅地址候选，留空时使用 `app_url`。
- `server_token`：节点服务端鉴权 token。
- `server_push_interval`：节点上报间隔。
- `server_pull_interval`：节点拉取间隔。
- 邮件 SMTP 配置：用于验证码、通知等队列邮件。
- Telegram bot token：用于 Telegram 绑定和通知。

## API 路径

主要入口：

```text
/api/v1/auth/*
/api/v1/user/*
/api/v1/plans
/api/v1/orders
/api/v1/payment-methods
/api/v1/client/subscribe
/api/v2/server/config
/api/v1/server/uniproxy/*
/api/v1/admin/*
/admin/*
/notify/{gateway}/{uuid}
```

REST API 返回 JSON。Admin HTML 返回服务端渲染 HTML，写操作使用 `/admin/actions/*` 并带 CSRF。

## 支付回调

支付回调路径固定为：

```text
/notify/{gateway}/{uuid}
```

当前内置 EPay。支付流程：

1. 后端根据订单和支付方式生成 `submit.php?...` 支付 URL。
2. API 把 URL 返回给前端。
3. 前端跳转到该 URL。
4. 支付网关回调 `/notify/epay/{uuid}`。

回调请求使用 JSON，服务端会校验签名、商户号、支付方式、订单状态和到账金额。

## 节点接入

V2Node 配置接口：

```text
GET /api/v2/server/config?token=<server_token>&node_id=<id>
```

UniProxy 兼容接口：

```text
GET|POST /api/v1/server/uniproxy/user
GET|POST /api/v1/server/uniproxy/push
GET|POST /api/v1/server/uniproxy/alivelist
GET|POST /api/v1/server/uniproxy/alive
```

参数包含：

- `token`：系统配置 `server_token`
- `node_type`：节点协议类型
- `node_id`：节点 ID

UniProxy 的 `config` 接口未实现，配置拉取使用 `/api/v2/server/config`。

## 订阅使用

用户订阅入口：

```text
GET /api/v1/client/subscribe?token=<user_token>
```

可通过 `flag` 或客户端 User-Agent 自动选择输出格式：

- Clash / Mihomo / Clash Meta
- sing-box
- SIP008
- Surge
- Surfboard
- Loon
- Quantumult X
- Shadowrocket
- v2rayN / v2rayNG / SagerNet / PassWall / SSRPlus / v2rayTun

用户端可通过：

```text
GET /api/v1/user/subscribe
GET /api/v1/user/servers
```

获取订阅信息和可用节点列表。

## 日志和队列观察

后台页面：

- `/admin/logs`：系统事件日志。
- `/admin/mail`：邮件发送记录。
- `/admin/failed-jobs`：失败任务。
- `/admin/system`：系统状态和队列状态。
- `/admin/stats`：统计概览。

邮件发送记录写入 `log_event` 的 `mail` 分类；佣金账本保留在 `commission_log`，同时写入 `log_event` 的 `commission` 分类用于审计检索。

队列失败会写入 `failed_jobs`，并记录系统事件。修复问题后可在后台重试或重新入队。

日志清理使用分类保留策略：

- `access`：保留 30 天。
- `queue`：保留 90 天。
- `mail`、`system`：保留 180 天。
- `audit`、`commission`：永久保留，且管理端普通删除动作会拒绝删除。

## 备份与恢复

备份：

```bash
pg_dump -Fc -h 127.0.0.1 -U pyboard_admin -d pyboard_db -f pyboard_db.dump
```

恢复：

```bash
pg_restore -h 127.0.0.1 -U pyboard_admin -d pyboard_db --clean --if-exists pyboard_db.dump
```

说明：

- `runtime_cache` 和 `traffic_cache` 是 UNLOGGED 表，属于可丢失运行期数据。
- 备份重点是业务表、订单、用户、配置、节点、统计、队列表和失败任务。
- 升级前建议先备份数据库。

## 升级流程

```bash
git pull
uv sync
uv run alembic upgrade head
uv run ruff check app tests main.py alembic
uv run pytest
```

然后重启 Web 和 Worker。

生产环境如果不能跑全量测试，至少执行：

```bash
uv run alembic upgrade head
uv run python -m app.queues.worker --once
```

## 生产检查清单

- `JWT_SECRET_KEY` 已更换为随机高强度字符串。
- `.env` 权限受控且未提交到仓库。
- PostgreSQL 已配置备份。
- pg_cron 已安装，`cron.job` 中能看到 `pyboard_%` 定时任务。
- Web 和 Worker 都由进程管理工具托管。
- 反向代理正确传递 `Host`、`X-Forwarded-For`、`X-Forwarded-Proto`。
- `app_url` 是公网 HTTPS 地址。
- `server_token` 已设置为随机字符串。
- 邮件配置可用，验证码邮件能发送。
- 支付网关回调地址可从公网访问。
- `/health` 返回 `{"status":"ok"}`。

## 常见问题

### 启动后没有管理员

确认 `.env` 中同时设置了：

```env
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_ADMIN_PASSWORD=change-this-admin-password
```

该初始化只在系统不存在管理员时创建账号。

### pg_cron 不可用

应用仍可运行。影响的是周期性任务自动入队，例如订单检查、流量落库、统计聚合和运行期缓存清理。

优先检查：

```sql
SHOW shared_preload_libraries;
SHOW cron.database_name;
SELECT extname FROM pg_extension WHERE extname = 'pg_cron';
SELECT jobname, schedule, active FROM cron.job WHERE jobname LIKE 'pyboard_%';
```

如果迁移还没有执行，安装扩展后正常执行：

```bash
uv run alembic upgrade head
```

如果迁移已经执行到最新版本，再安装 pg_cron，则需要在数据库中手动补注册项目任务：

```sql
SELECT pyboard_schedule_pg_cron_jobs();

DO $$
BEGIN
    BEGIN
        PERFORM cron.unschedule('pyboard_runtime_cache_cleanup');
    EXCEPTION WHEN others THEN
        NULL;
    END;
    PERFORM cron.schedule(
        'pyboard_runtime_cache_cleanup',
        '*/10 * * * *',
        $cron$SELECT pyboard_cleanup_runtime_cache()$cron$
    );
    BEGIN
        PERFORM cron.unschedule('pyboard_cleanup_log_events_daily');
    EXCEPTION WHEN others THEN
        NULL;
    END;
    PERFORM cron.schedule(
        'pyboard_cleanup_log_events_daily',
        '25 3 * * *',
        $cron$SELECT pyboard_enqueue_queue_job('cleanup_log_events', '[]'::jsonb, '{}'::jsonb, 'default', 'cron:cleanup_log_events:' || to_char(now(), 'YYYYMMDD'))$cron$
    );
END
$$;
```

### 订阅地址不正确

检查后台系统配置：

- `app_url`
- `subscribe_url`

反向代理后需要保证外部 HTTPS 域名正确。

### 支付回调失败

检查：

- 支付方式是否启用。
- 回调路径是否为 `/notify/{gateway}/{uuid}`。
- EPay 配置 `url`、`pid`、`key` 是否正确。
- 网关是否按 JSON 回调。
- 订单金额和实际到账金额是否一致。

### 节点鉴权失败

检查节点请求中的 `token` 是否等于系统配置 `server_token`，并确认 `node_id` 存在且协议类型匹配。
