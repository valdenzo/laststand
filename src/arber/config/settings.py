from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ARBER_DB_", env_file=".env", extra="ignore")

    dsn: PostgresDsn = Field(
        default=PostgresDsn("postgresql+asyncpg://arber:arber@localhost:5433/arber"),
    )
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False

    @property
    def sync_dsn(self) -> str:
        return str(self.dsn).replace("postgresql+asyncpg", "postgresql+psycopg")

    @property
    def async_dsn(self) -> str:
        return str(self.dsn)


class HttpSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ARBER_HTTP_", env_file=".env", extra="ignore")

    default_timeout_s: float = 15.0
    default_rate_limit_rps: float = 2.0
    user_agent: str = "arber/0.1"


class SchedulerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ARBER_SCHED_", env_file=".env", extra="ignore")

    reference_sync_interval_s: int = 6 * 60 * 60
    bookmaker_fixtures_interval_s: int = 15 * 60
    odds_fetch_interval_s: int = 45
    resolve_unmatched_interval_s: int = 5 * 60
    promote_candidates_interval_s: int = 10 * 60


class ObservabilitySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ARBER_OBS_", env_file=".env", extra="ignore")

    metrics_host: str = "127.0.0.1"
    metrics_port: int = 9464
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "console"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ARBER_", env_file=".env", extra="ignore")

    env: Literal["dev", "test", "prod"] = "dev"
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    http: HttpSettings = Field(default_factory=HttpSettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    obs: ObservabilitySettings = Field(default_factory=ObservabilitySettings)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
