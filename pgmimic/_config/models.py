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


class DataConfig(BaseModel):
    location: str
    version: str
    schemas: list[str]
    tables: TableMap


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
