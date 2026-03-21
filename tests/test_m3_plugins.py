"""
M3 Test: Plugin System
======================
"""

import pytest
from spidermind.core.config import SpiderMindConfig
from spidermind.core.models import CrawlRequest, CrawlResponse, CrawlResult, CrawlStatus
from spidermind.plugins import (
    registry, BasePlugin, BaseDownloader, BaseExtractor,
    BasePipeline, BaseStorage, BaseMiddleware, BaseAIExtractor,
)


# ─── Mock plugins for testing ──────────────────────────────────────

@registry.register_downloader
class MockDownloader(BaseDownloader):
    name = "mock_dl"
    version = "1.0.0"
    async def setup(self): pass
    async def download(self, request):
        return CrawlResponse(request_id=request.id, url=request.url, status_code=200, body="ok")

@registry.register_extractor
class MockExtractor(BaseExtractor):
    name = "mock_ext"
    async def setup(self): pass
    async def extract(self, response, rules=None):
        return {"title": "Mock Title"}

@registry.register_pipeline
class MockPipeline(BasePipeline):
    name = "mock_pipe"
    async def setup(self): pass
    async def process(self, result):
        result.pipeline_data["mock"] = True
        return result

@registry.register_storage
class MockStorage(BaseStorage):
    name = "mock_store"
    _saved: list
    async def setup(self):
        self._saved = []
    async def save(self, result):
        self._saved.append(result)
    async def exists(self, url):
        return any(r.request.url == url for r in self._saved)

@registry.register_middleware
class MockMiddleware(BaseMiddleware):
    name = "mock_mw"
    async def setup(self): pass
    async def process_request(self, request):
        request.headers["X-Mock"] = "1"
        return request

@registry.register_ai_extractor
class MockAIExtractor(BaseAIExtractor):
    name = "mock_ai"
    async def setup(self): pass
    async def extract(self, response, schema=None):
        return {"ai_field": "ai_value"}
    async def classify(self, response):
        return "article"
    async def summarize(self, response, max_length=500):
        return "A summary"


# ─── Tests ─────────────────────────────────────────────────────────

class TestRegistration:

    def test_all_registered(self):
        plugins = registry.list_plugins()
        assert "mock_dl" in plugins["downloaders"]
        assert "mock_ext" in plugins["extractors"]
        assert "mock_pipe" in plugins["pipelines"]
        assert "mock_store" in plugins["storage"]
        assert "mock_mw" in plugins["middleware"]
        assert "mock_ai" in plugins["ai_extractors"]

    def test_get_downloader(self):
        cls = registry.get_downloader("mock_dl")
        assert cls is MockDownloader

    def test_get_nonexistent(self):
        assert registry.get_downloader("nonexistent") is None
        assert registry.get_pipeline("nonexistent") is None


class TestPluginLifecycle:

    @pytest.mark.asyncio
    async def test_setup_teardown(self):
        config = SpiderMindConfig()
        dl = MockDownloader(config)
        await dl.setup()
        assert dl.enabled is True
        dl.disable()
        assert dl.enabled is False
        dl.enable()
        assert dl.enabled is True
        await dl.teardown()


class TestDownloaderPlugin:

    @pytest.mark.asyncio
    async def test_download(self):
        config = SpiderMindConfig()
        dl = MockDownloader(config)
        await dl.setup()
        req = CrawlRequest(url="https://test.com")
        resp = await dl.download(req)
        assert resp.status_code == 200
        assert resp.body == "ok"
        await dl.teardown()


class TestExtractorPlugin:

    @pytest.mark.asyncio
    async def test_extract(self):
        config = SpiderMindConfig()
        ext = MockExtractor(config)
        await ext.setup()
        resp = CrawlResponse(request_id="t", url="https://a.com", body="<html>")
        result = await ext.extract(resp)
        assert result["title"] == "Mock Title"


class TestPipelinePlugin:

    @pytest.mark.asyncio
    async def test_process(self):
        config = SpiderMindConfig()
        pipe = MockPipeline(config)
        await pipe.setup()
        req = CrawlRequest(url="https://a.com")
        result = CrawlResult(request=req)
        result = await pipe.process(result)
        assert result.pipeline_data["mock"] is True


class TestStoragePlugin:

    @pytest.mark.asyncio
    async def test_save_and_exists(self):
        config = SpiderMindConfig()
        store = MockStorage(config)
        await store.setup()
        req = CrawlRequest(url="https://a.com")
        result = CrawlResult(request=req, status=CrawlStatus.COMPLETED)
        await store.save(result)
        assert await store.exists("https://a.com")
        assert not await store.exists("https://b.com")


class TestMiddlewarePlugin:

    @pytest.mark.asyncio
    async def test_process_request(self):
        config = SpiderMindConfig()
        mw = MockMiddleware(config)
        await mw.setup()
        req = CrawlRequest(url="https://a.com")
        req = await mw.process_request(req)
        assert req.headers["X-Mock"] == "1"


class TestAIExtractorPlugin:

    @pytest.mark.asyncio
    async def test_full_ai_pipeline(self):
        config = SpiderMindConfig()
        ai = MockAIExtractor(config)
        await ai.setup()
        resp = CrawlResponse(request_id="t", url="https://a.com", body="content")

        extracted = await ai.extract(resp)
        assert extracted["ai_field"] == "ai_value"

        cls = await ai.classify(resp)
        assert cls == "article"

        summary = await ai.summarize(resp)
        assert summary == "A summary"
