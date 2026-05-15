"""全局配置 —— PostgreSQL 专用。"""

from urllib.parse import quote_plus

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，可通过 .env 文件或环境变量覆盖。"""

    # ---- 首次迁移初始化管理员（可选）----
    initial_admin_email: str = ""
    initial_admin_password: str = ""

    # ---- JWT 认证 ----
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    # ---- PostgreSQL ----
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_user: str = "postgres"
    pg_password: str = "postgres"
    pg_database: str = "postgres"

    # ---- 数据库连接池 ----
    pool_size: int = 50       # 常驻连接数
    max_overflow: int = 30    # 溢出上限（峰值可达 pool_size + max_overflow）

    # ---- PostgreSQL 任务队列 ----
    queue_default_name: str = "default"
    queue_max_jobs: int = 20       # Worker 最大并发任务数
    queue_poll_delay: float = 0.5  # 队列轮询间隔（秒）
    queue_max_tries: int = 3       # 任务最大重试次数
    queue_retry_jobs: bool = True  # 失败后是否重试
    queue_health_check_interval: int = 300  # 健康检查间隔（秒）

    @property
    def database_url(self) -> str:
        """拼接 PostgreSQL 连接字符串。"""
        return (
            f"postgresql+asyncpg://{quote_plus(self.pg_user)}:{quote_plus(self.pg_password)}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()  # type: ignore[call-arg]
