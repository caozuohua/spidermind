"""
M1 Test: Data Models
====================
验证所有数据模型的创建、序列化、计算字段、边界条件。
"""

import json
import pytest
from spidermind.core.models import (
    CrawlRequest, CrawlResponse, CrawlResult, CrawlStatus,
    CrawlStats, ContentType, ExtractionField, ExtractionMethod,
    ExtractionResult,
)


# ─── CrawlRequest ──────────────────────────────────────────────────

class TestCrawlRequest:

    def test_basic_creation(self):
        req = CrawlRequest(url="https://example.com")
        assert req.url == "https://example.com"
        assert req.method == "GET"
        assert req.depth == 0
        assert req.priority == 0
        assert len(req.id) == 12

    def test_custom_fields(self):
        req = CrawlRequest(
            url="https://a.com",
            method="POST",
            priority=10,
            depth=2,
            headers={"X-Token": "abc"},
            meta={"category": "test"},
        )
        assert req.method == "POST"
        assert req.priority == 10
        assert req.depth == 2
        assert req.headers["X-Token"] == "abc"
        assert req.meta["category"] == "test"

    def test_serialization_roundtrip(self):
        req = CrawlRequest(url="https://a.com", priority=5)
        data = req.model_dump()
        restored = CrawlRequest.model_validate(data)
        assert restored.url == req.url
        assert restored.priority == req.priority
        assert restored.id == req.id

    def test_unique_ids(self):
        ids = {CrawlRequest(url="https://a.com").id for _ in range(100)}
        assert len(ids) == 100  # All unique


# ─── CrawlResponse ────────────────────────────────────────────────

class TestCrawlResponse:

    def test_success_response(self):
        resp = CrawlResponse(
            request_id="abc",
            url="https://a.com",
            status_code=200,
            body="<html>OK</html>",
            content_type=ContentType.HTML,
            elapsed_ms=150.5,
        )
        assert resp.status_code == 200
        assert resp.content_type == ContentType.HTML
        assert "OK" in resp.body
        assert resp.error is None

    def test_error_response(self):
        resp = CrawlResponse(
            request_id="abc",
            url="https://a.com",
            error="Connection timeout",
        )
        assert resp.status_code == 0
        assert resp.error == "Connection timeout"

    def test_redirect_tracking(self):
        resp = CrawlResponse(
            request_id="abc",
            url="https://a.com/final",
            redirect_urls=["https://a.com/old", "https://a.com/new"],
        )
        assert len(resp.redirect_urls) == 2


# ─── ExtractionResult ─────────────────────────────────────────────

class TestExtractionResult:

    def test_field_get(self):
        ext = ExtractionResult(
            request_id="t",
            url="https://a.com",
            fields=[
                ExtractionField(name="title", value="Hello"),
                ExtractionField(name="price", value=9.99),
            ],
        )
        assert ext.get("title") == "Hello"
        assert ext.get("price") == 9.99
        assert ext.get("missing") is None
        assert ext.get("missing", "N/A") == "N/A"

    def test_to_dict(self):
        ext = ExtractionResult(
            request_id="t",
            url="https://a.com",
            fields=[ExtractionField(name="x", value="y")],
            links=["https://a.com/1"],
            ai_summary="A page",
        )
        d = ext.to_dict()
        assert d["x"] == "y"
        assert d["_url"] == "https://a.com"
        assert d["_links"] == ["https://a.com/1"]
        assert d["_ai_summary"] == "A page"

    def test_to_dict_no_ai(self):
        ext = ExtractionResult(request_id="t", url="https://a.com")
        d = ext.to_dict()
        assert "_ai_summary" not in d
        assert "_ai_classification" not in d


# ─── CrawlResult ──────────────────────────────────────────────────

class TestCrawlResult:

    def _make_result(self, body="test content"):
        req = CrawlRequest(url="https://a.com")
        resp = CrawlResponse(request_id=req.id, url=req.url, body=body)
        return CrawlResult(request=req, response=resp)

    def test_fingerprint_deterministic(self):
        r1 = self._make_result("same content")
        r2 = self._make_result("same content")
        assert r1.fingerprint == r2.fingerprint
        assert len(r1.fingerprint) == 16

    def test_fingerprint_differs(self):
        r1 = self._make_result("content A")
        r2 = self._make_result("content B")
        assert r1.fingerprint != r2.fingerprint

    def test_to_storage_dict(self):
        r = self._make_result()
        r.status = CrawlStatus.COMPLETED
        data = r.to_storage_dict()
        assert data["url"] == "https://a.com"
        assert data["status"] == "completed"
        assert data["fingerprint"] is not None
        assert "created_at" in data

    def test_to_storage_with_extraction(self):
        req = CrawlRequest(url="https://a.com")
        ext = ExtractionResult(
            request_id=req.id,
            url=req.url,
            fields=[ExtractionField(name="title", value="Test")],
        )
        r = CrawlResult(request=req, extraction=ext, status=CrawlStatus.COMPLETED)
        data = r.to_storage_dict()
        assert data["extracted"]["title"] == "Test"

    def test_status_enum(self):
        req = CrawlRequest(url="https://a.com")
        r = CrawlResult(request=req, status=CrawlStatus.FAILED)
        assert r.status == CrawlStatus.FAILED
        assert r.status.value == "failed"


# ─── CrawlStats ───────────────────────────────────────────────────

class TestCrawlStats:

    def test_success_rate(self):
        s = CrawlStats(completed=80, failed=20)
        assert s.success_rate == 80.0

    def test_success_rate_zero(self):
        s = CrawlStats()
        assert s.success_rate == 0.0

    def test_elapsed(self):
        s = CrawlStats()
        assert s.elapsed_seconds >= 0


# ─── Enums ────────────────────────────────────────────────────────

class TestEnums:

    def test_crawl_status_values(self):
        assert CrawlStatus.PENDING.value == "pending"
        assert CrawlStatus.COMPLETED.value == "completed"

    def test_content_type_values(self):
        assert ContentType.HTML.value == "html"
        assert ContentType.JSON.value == "json"

    def test_extraction_method_values(self):
        assert ExtractionMethod.CSS.value == "css"
        assert ExtractionMethod.AI.value == "ai"
