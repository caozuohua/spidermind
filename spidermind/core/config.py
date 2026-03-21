"""
M2: Configuration System
========================

Centralized configuration with YAML + env var support.
All settings have sensible defaults via Pydantic v2.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class DownloaderType(str, Enum):
    HTTP = "http"
    BROWSER = "browser"


class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    CUSTOM = "custom"


class StorageBackend(str, Enum):
    JSONL = "jsonl"
    CSV = "csv"
    SQLITE = "sqlite"
    MONGO = "mongo"
    REDIS = "redis"
    MYSQL = "mysql"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class DownloaderConfig(BaseModel):
    type: DownloaderType = DownloaderType.HTTP
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    follow_redirects: bool = True
    max_redirects: int = 10
    verify_ssl: bool = True
    user_agent: str = "SpiderMind/0.1.0"
    headers: dict[str, str] = Field(default_factory=dict)
    cookies: dict[str, str] = Field(default_factory=dict)
    proxy: str | None = None
    headless: bool = True
    browser_type: str = "chromium"


class AIConfig(BaseModel):
    provider: AIProvider = AIProvider.OPENAI
    model: str = "gpt-4o-mini"
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout: float = 60.0


class StorageConfig(BaseModel):
    backend: StorageBackend = StorageBackend.JSONL
    path: str = "./data"
    host: str = "localhost"
    port: int = 27017
    database: str = "spidermind"
    collection: str = "results"
    username: str | None = None
    password: str | None = None


class PipelineConfig(BaseModel):
    dedup: bool = True
    dedup_field: str = "url"
    filter_empty: bool = True
    clean_html: bool = True
    extract_metadata: bool = True
    custom_processors: list[str] = Field(default_factory=list)


class SchedulerConfig(BaseModel):
    concurrency: int = 5
    rate_limit: float = 1.0
    delay_range: tuple[float, float] = (0.5, 2.0)
    respect_robots: bool = True
    max_depth: int = 3
    max_pages: int = 0
    crawl_delay: float = 0.0


class SpiderMindConfig(BaseModel):
    """Root configuration."""
    name: str = "default-spider"
    version: str = "0.1.0"
    log_level: LogLevel = LogLevel.INFO
    log_file: str | None = None

    downloader: DownloaderConfig = Field(default_factory=DownloaderConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)

    plugins: list[str] = Field(default_factory=list)
    middleware: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> SpiderMindConfig:
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    @classmethod
    def load(cls, path: str | Path | None = None) -> SpiderMindConfig:
        if path and Path(path).exists():
            config = cls.from_yaml(path)
        else:
            config = cls()
        # Env overrides
        for key, value in os.environ.items():
            if key.startswith("SPIDERMIND_"):
                field = key[len("SPIDERMIND_"):].lower()
                if hasattr(config, field):
                    setattr(config, field, value)
        return config
