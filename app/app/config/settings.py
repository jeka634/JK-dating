from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(alias="BOT_TOKEN")
    bot_username: str = Field(default="", alias="BOT_USERNAME")
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    stars_provider_token: str = Field(default="", alias="STARS_PROVIDER_TOKEN")
    webhook_url: str = Field(default="", alias="WEBHOOK_URL")
    webhook_path: str = Field(default="/webhook", alias="WEBHOOK_PATH")
    webhook_secret: str = Field(default="", alias="WEBHOOK_SECRET")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    secret_key: str = Field(alias="SECRET_KEY")
    admin_ids: List[int] = Field(default_factory=list, alias="ADMIN_IDS")
    admin_api_key: str = Field(default="", alias="ADMIN_API_KEY")
    jwt_secret: str = Field(default="", alias="JWT_SECRET")
    jk_token_contract: str = Field(
        default="EQAK3lkmVshzYJeypOCtPBnE_kOJ4Nb9hwyRvQJeRDDW6HPM",
        alias="JK_TOKEN_CONTRACT",
    )
    free_daily_likes: int = Field(default=20, alias="FREE_DAILY_LIKES")
    new_user_likes: int = Field(default=5, alias="NEW_USER_LIKES")
    new_user_limit_hours: int = Field(default=24, alias="NEW_USER_LIMIT_HOURS")
    premium_price_stars: int = Field(default=250, alias="PREMIUM_PRICE_STARS")
    premium_duration_days: int = Field(default=30, alias="PREMIUM_DURATION_DAYS")
    referral_bonus_days: int = Field(default=7, alias="REFERRAL_BONUS_DAYS")
    bot_mode: str = Field(default="polling", alias="BOT_MODE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: object) -> List[int]:
        if isinstance(value, list):
            return [int(item) for item in value]
        if isinstance(value, int):
            return [value]
        if isinstance(value, str):
            if not value.strip():
                return []
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return []


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
