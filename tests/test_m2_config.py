"""
M2 Test: Configuration
======================
"""

import tempfile
import os
import pytest
from pathlib import Path
from spidermind.core.config import (
    SpiderMindConfig, DownloaderConfig, AIConfig, StorageConfig,
    SchedulerConfig, PipelineConfig,
    DownloaderType, AIProvider, StorageBackend, LogLevel,
)


class TestDefaultConfig:

    def test_defaults(self):
        c = SpiderMindConfig()
        assert c.name == "default-spider"
        assert c.log_level == LogLevel.INFO
        assert c.downloader.type == DownloaderType.HTTP
        assert c.downloader.timeout == 30.0
        assert c.scheduler.concurrency == 5
        assert c.storage.backend == StorageBackend.JSONL

    def test_nested_defaults(self):
        c = SpiderMindConfig()
        assert c.ai.provider == AIProvider.OPENAI
        assert c.ai.model == "gpt-4o-mini"
        assert c.ai.temperature == 0.0
        assert c.pipeline.dedup is True


class TestDictConfig:

    def test_top_level(self):
        c = SpiderMindConfig(name="test", log_level="WARNING")
        assert c.name == "test"
        assert c.log_level == LogLevel.WARNING

    def test_nested_dict(self):
        c = SpiderMindConfig(
            downloader={"timeout": 60, "user_agent": "TestBot/1.0"},
            scheduler={"concurrency": 10, "rate_limit": 5.0},
        )
        assert c.downloader.timeout == 60.0
        assert c.downloader.user_agent == "TestBot/1.0"
        assert c.scheduler.concurrency == 10
        assert c.scheduler.rate_limit == 5.0

    def test_storage_config(self):
        c = SpiderMindConfig(storage={"backend": "sqlite", "path": "/tmp/db"})
        assert c.storage.backend == StorageBackend.SQLITE
        assert c.storage.path == "/tmp/db"


class TestYamlConfig:

    def test_load_yaml(self, tmp_path):
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("""
name: yaml-spider
downloader:
  timeout: 45
  user_agent: "YamlBot/1.0"
scheduler:
  concurrency: 10
  max_pages: 500
ai:
  provider: anthropic
  model: claude-3
storage:
  backend: mongo
  path: /data/crawl
pipeline:
  dedup: true
  clean_html: false
""")
        c = SpiderMindConfig.from_yaml(yaml_file)
        assert c.name == "yaml-spider"
        assert c.downloader.timeout == 45.0
        assert c.downloader.user_agent == "YamlBot/1.0"
        assert c.scheduler.concurrency == 10
        assert c.scheduler.max_pages == 500
        assert c.ai.provider == AIProvider.ANTHROPIC
        assert c.ai.model == "claude-3"
        assert c.storage.backend == StorageBackend.MONGO
        assert c.pipeline.clean_html is False

    def test_empty_yaml(self, tmp_path):
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")
        c = SpiderMindConfig.from_yaml(yaml_file)
        assert c.name == "default-spider"

    def test_missing_yaml(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            SpiderMindConfig.from_yaml(tmp_path / "nonexistent.yaml")


class TestValidation:

    def test_invalid_timeout_type(self):
        with pytest.raises(Exception):
            DownloaderConfig(timeout="not-a-number")

    def test_invalid_enum(self):
        with pytest.raises(Exception):
            SpiderMindConfig(downloader={"type": "ftp"})


class TestEnums:

    def test_downloader_types(self):
        assert DownloaderType.HTTP.value == "http"
        assert DownloaderType.BROWSER.value == "browser"

    def test_ai_providers(self):
        assert AIProvider.OPENAI.value == "openai"
        assert AIProvider.ANTHROPIC.value == "anthropic"

    def test_storage_backends(self):
        assert StorageBackend.JSONL.value == "jsonl"
        assert StorageBackend.MONGO.value == "mongo"

    def test_log_levels(self):
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.ERROR.value == "ERROR"


class TestSerialization:

    def test_roundtrip(self):
        c = SpiderMindConfig(name="rt", downloader={"timeout": 99})
        data = c.model_dump()
        restored = SpiderMindConfig.model_validate(data)
        assert restored.name == "rt"
        assert restored.downloader.timeout == 99.0
