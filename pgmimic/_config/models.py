"""Typed config model. Raw config.json is validated into a Config instance."""

from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    host: str
    port: int
    database: str
    schema_: str = Field(alias="schema")
    username: str | None = None
    password: str | None = None


TableMap = dict[str, "list[str] | dict[str, list[str]]"]


class VersionedAssets(BaseModel):
    schemas: list[str]
    tables: TableMap


class DataConfig(BaseModel):
    location: str
    version: str
    schemas: list[str]
    tables: TableMap
    versions: dict[str, VersionedAssets] | None = None

    @model_validator(mode="after")
    def _resolve_versioned_assets(self) -> DataConfig:
        """If `versions[version]` exists, its schemas/tables override the
        top-level legacy keys. Otherwise the legacy top-level keys win.

        This keeps `config.data.schemas` and `config.data.tables` as the
        single accessors for downstream callers — they don't need to know
        whether the config is in legacy or versioned shape.
        """
        if self.versions is None:
            return self
        assets = self.versions.get(self.version)
        if assets is None:
            return self
        self.schemas = assets.schemas
        self.tables = assets.tables
        return self


class Config(BaseModel):
    database: DatabaseConfig
    data: DataConfig

    @model_validator(mode="after")
    def _populate_credentials_from_env(self) -> Config:
        env_user = os.getenv("DB_USER")
        env_password = os.getenv("DB_PASSWORD")
        if env_user is not None:
            self.database.username = env_user
        if env_password is not None:
            self.database.password = env_password
        return self
