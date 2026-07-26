from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "bscout"
    postgres_user: str = "bscout"
    postgres_password: str = "bscout"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    jwt_secret_key: str = "change-me-to-a-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    debug: bool = True
    app_name: str = "BScout API"

    rate_limit_max_requests: int = 120
    rate_limit_window: int = 60
    rate_limit_trust_forwarded_for: bool = False
    auth_rate_limit_max_requests: int = 10
    auth_rate_limit_window: int = 300

    yookassa_webhook_secret: str | None = None

    frontend_base_url: str = "http://localhost:3000"

    smtp_host: str | None = None
    smtp_port: int = 465
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_use_ssl: bool = True
    smtp_from: str = "BScout <no-reply@bscout.ru>"
    mail_backend: str = "console"

    vk_client_id: str | None = None
    vk_client_secret: str | None = None
    vk_redirect_uri: str | None = None

    telegram_bot_token: str | None = None
    telegram_bot_username: str | None = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
