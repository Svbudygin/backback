import base64
import os
import json
from functools import cached_property

from dotenv import load_dotenv
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings
from typing_extensions import Any

load_dotenv()


def parse_ro_uri_list(s: str) -> list[str]:
    fields = s.split('|')
    uri_arr = []
    for i in range(0, len(fields), 5):
        uri_arr.append(str(
            PostgresDsn.build(  # type: ignore
                scheme="postgresql+asyncpg",
                username=fields[i + 0],
                password=fields[i + 1],
                host=fields[i + 2],
                port=int(fields[i + 3]),
                path=fields[i + 4],
            )
        ))
    return uri_arr


class Settings(BaseSettings):
    PROJECT_NAME: str = "1spin API BEST6"
    VERSION: str = "1"
    DESCRIPTION: str | None = ""

    DOCS_PASSWORD: str | None = os.environ.get("DOCS_PASSWORD")

    # CORE SETTINGS
    SECRET_KEY: str = os.environ["SECRET_KEY"]
    SECRET_HASH_KEY: str = os.environ["SECRET_HASH_KEY"]

    X_RAPIDAPI_KEY: str = os.environ["X_RAPIDAPI_KEY"]

    SECURITY_BCRYPT_ROUNDS: int = 4
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 40320  # 28 days

    PAYER_ACCESS_TOKEN_EXPIRE_S: int = 60 * 60  # 60 min
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    ALLOWED_HOSTS: list[str] = ["*"]

    # POSTGRESQL DEFAULT DATABASE
    DATABASE_HOSTNAME: str = os.environ["DATABASE_HOSTNAME"]
    DATABASE_USER: str = os.environ["DATABASE_USER"]
    DATABASE_PASSWORD: str = os.environ["DATABASE_PASSWORD"]
    DATABASE_PORT: int = os.environ["DATABASE_PORT"]
    DATABASE_DB: str = os.environ["DATABASE_DB"]

    CACHE_USER: str = os.environ["CACHE_USER"]
    CACHE_PASSWORD: str = os.environ["CACHE_PASSWORD"]
    CACHE_PORT: int = os.environ["CACHE_PORT"]
    CACHE_HOST: str = os.environ["CACHE_HOST"]
    CACHE_DB: str = os.environ["CACHE_DB"]

    REDIS_USER: str = os.environ["REDIS_USER"]
    REDIS_PASSWORD: str = os.environ["REDIS_PASSWORD"]
    REDIS_PORT: int = os.environ["REDIS_PORT"]
    REDIS_HOST: str = os.environ["REDIS_HOST"]
    REDIS_PING_DB: str = os.environ["REDIS_PING_DB"]
    REDIS_CELERY_DB: str = os.environ["REDIS_CELERY_DB"]

    FILE_STORAGE_KEY: str = os.environ["FILE_STORAGE_KEY"]
    FILE_STORAGE_SECRET: str = os.environ["FILE_STORAGE_SECRET"]
    FILE_STORAGE_LOCATION: str = os.environ["FILE_STORAGE_LOCATION"]
    FILE_STORAGE_BUCKET: str = os.environ["FILE_STORAGE_BUCKET"]
    FILE_STORAGE_PATH: str = os.environ.get("FILE_STORAGE_PATH", "")
    FILE_STORAGE_PUBLIC_BUCKET: str = os.environ["FILE_STORAGE_PUBLIC_BUCKET"]
    #ALLOWED_DOMAINS: dict[str, list[str]] = json.loads(base64.b64decode(os.environ['DOMAINS']))

    REDIS_NOTIFICATIONS_CHANNEL: str = os.environ["REDIS_NOTIFICATIONS_CHANNEL"]

    FRONTEND_APPEALS_URL: str = os.environ["FRONTEND_APPEALS_URL"]

    ANALIZATOR_TENANT_ID: str = os.environ["ANALIZATOR_TENANT_ID"]
    ANALIZATOR_CLIENT_ID: str = os.environ["ANALIZATOR_CLIENT_ID"]
    ANALIZATOR_CLIENT_SECRET: str = os.environ["ANALIZATOR_CLIENT_SECRET"]
    ANALIZATOR_REPORT_ID: str = os.environ["ANALIZATOR_REPORT_ID"]
    ANALIZATOR_GROUP_ID: str = os.environ["ANALIZATOR_GROUP_ID"]

    POOL_SIZE: int = 1000
    MAX_OVERFLOW: int = 0
    POOL_TIMEOUT: int = 60 * 10
    ro_database_uris: list[str] = parse_ro_uri_list(s=os.environ["RO_DB_LIST"])  # type: ignore

    @computed_field
    @cached_property
    def database_uri(self) -> str:
        return str(
            PostgresDsn.build(  # type: ignore
                scheme="postgresql+asyncpg",
                username=self.DATABASE_USER,
                password=self.DATABASE_PASSWORD,
                host=self.DATABASE_HOSTNAME,
                port=self.DATABASE_PORT,
                path=self.DATABASE_DB,
            )
        )

    @computed_field
    @cached_property
    def redis_url(self) -> str:
        return f"rediss://{self.REDIS_USER}:" \
               f"{self.REDIS_PASSWORD}@" \
               f"{self.REDIS_HOST}:" \
               f"{self.REDIS_PORT}"


settings: Settings = Settings()  # type: ignore
