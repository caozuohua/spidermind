"""
M3: Plugin Registry System
===========================

SpiderMind uses a registry-based plugin system. All extensible components
(downloaders, extractors, pipelines, storage, middleware) follow the
same BasePlugin interface and register via decorators.

Architecture:
    @registry.register_downloader
    class MyDownloader(BaseDownloader):
        name = "my_downloader"
        async def setup(self): ...
        async def download(self, request) -> CrawlResponse: ...
"""

from __future__ import annotations

import abc
import importlib
import logging
from typing import Any, TypeVar

from spidermind.core.config import SpiderMindConfig
from spidermind.core.models import CrawlRequest, CrawlResponse, CrawlResult

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ─── Base Plugin ───────────────────────────────────────────────────


class BasePlugin(abc.ABC):
    """Base class for all plugins."""

    name: str = "base"
    version: str = "0.1.0"
    description: str = ""
    author: str = ""

    def __init__(self, config: SpiderMindConfig, **kwargs: Any) -> None:
        self.config = config
        self._enabled = True

    @abc.abstractmethod
    async def setup(self) -> None:
        ...

    async def teardown(self) -> None:
        pass

    @property
    def enabled(self) -> bool:
        return self._enabled

    def disable(self) -> None:
        self._enabled = False

    def enable(self) -> None:
        self._enabled = True


# ─── Plugin Interfaces ─────────────────────────────────────────────


class BaseDownloader(BasePlugin):
    name = "base_downloader"

    @abc.abstractmethod
    async def download(self, request: CrawlRequest) -> CrawlResponse:
        ...


class BaseExtractor(BasePlugin):
    name = "base_extractor"

    @abc.abstractmethod
    async def extract(self, response: CrawlResponse, rules: dict[str, Any] | None = None) -> dict[str, Any]:
        ...


class BaseAIExtractor(BasePlugin):
    name = "base_ai_extractor"

    @abc.abstractmethod
    async def extract(self, response: CrawlResponse, schema: dict[str, Any] | None = None) -> dict[str, Any]:
        ...

    @abc.abstractmethod
    async def classify(self, response: CrawlResponse) -> str:
        ...

    @abc.abstractmethod
    async def summarize(self, response: CrawlResponse, max_length: int = 500) -> str:
        ...


class BasePipeline(BasePlugin):
    name = "base_pipeline"

    @abc.abstractmethod
    async def process(self, result: CrawlResult) -> CrawlResult:
        ...


class BaseStorage(BasePlugin):
    name = "base_storage"

    @abc.abstractmethod
    async def save(self, result: CrawlResult) -> None:
        ...

    @abc.abstractmethod
    async def exists(self, url: str) -> bool:
        ...

    async def close(self) -> None:
        pass


class BaseMiddleware(BasePlugin):
    name = "base_middleware"

    async def process_request(self, request: CrawlRequest) -> CrawlRequest:
        return request

    async def process_response(self, response: CrawlResponse) -> CrawlResponse:
        return response

    async def process_result(self, result: CrawlResult) -> CrawlResult:
        return result


# ─── Registry ──────────────────────────────────────────────────────


class PluginRegistry:
    """Central registry for all plugin types."""

    def __init__(self) -> None:
        self._downloaders: dict[str, type[BaseDownloader]] = {}
        self._extractors: dict[str, type[BaseExtractor]] = {}
        self._ai_extractors: dict[str, type[BaseAIExtractor]] = {}
        self._pipelines: dict[str, type[BasePipeline]] = {}
        self._storage: dict[str, type[BaseStorage]] = {}
        self._middleware: dict[str, type[BaseMiddleware]] = {}

    def register_downloader(self, cls: type[BaseDownloader]) -> type[BaseDownloader]:
        self._downloaders[cls.name] = cls
        return cls

    def register_extractor(self, cls: type[BaseExtractor]) -> type[BaseExtractor]:
        self._extractors[cls.name] = cls
        return cls

    def register_ai_extractor(self, cls: type[BaseAIExtractor]) -> type[BaseAIExtractor]:
        self._ai_extractors[cls.name] = cls
        return cls

    def register_pipeline(self, cls: type[BasePipeline]) -> type[BasePipeline]:
        self._pipelines[cls.name] = cls
        return cls

    def register_storage(self, cls: type[BaseStorage]) -> type[BaseStorage]:
        self._storage[cls.name] = cls
        return cls

    def register_middleware(self, cls: type[BaseMiddleware]) -> type[BaseMiddleware]:
        self._middleware[cls.name] = cls
        return cls

    # ── Lookup ──

    def get_downloader(self, name: str) -> type[BaseDownloader] | None:
        return self._downloaders.get(name)

    def get_extractor(self, name: str) -> type[BaseExtractor] | None:
        return self._extractors.get(name)

    def get_ai_extractor(self, name: str) -> type[BaseAIExtractor] | None:
        return self._ai_extractors.get(name)

    def get_pipeline(self, name: str) -> type[BasePipeline] | None:
        return self._pipelines.get(name)

    def get_storage(self, name: str) -> type[BaseStorage] | None:
        return self._storage.get(name)

    def get_middleware(self, name: str) -> type[BaseMiddleware] | None:
        return self._middleware.get(name)

    def load_plugin_module(self, module_path: str) -> None:
        importlib.import_module(module_path)

    def list_plugins(self) -> dict[str, list[str]]:
        return {
            "downloaders": list(self._downloaders.keys()),
            "extractors": list(self._extractors.keys()),
            "ai_extractors": list(self._ai_extractors.keys()),
            "pipelines": list(self._pipelines.keys()),
            "storage": list(self._storage.keys()),
            "middleware": list(self._middleware.keys()),
        }


# Global singleton
registry = PluginRegistry()
