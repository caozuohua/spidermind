"""
M1: Standardized Data Models
=============================

All SpiderMind data flows through these Pydantic v2 models.
They serve as the universal contract between components.

Design decisions:
- Use enums for fixed value sets (status, content type)
- Computed fields for derived values (fingerprint, duration)
- to_storage_dict() for serialization to storage backends
- model_dump() for full Pydantic serialization
"""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field


# ─── Enums ──────────────────────────────────────────────────────────


class CrawlStatus(str, Enum):
    """Lifecycle status of a crawl result."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ContentType(str, Enum):
    """Detected content type of a response."""
    HTML = "html"
    JSON = "json"
    XML = "xml"
    TEXT = "text"
    BINARY = "binary"
    RSS = "rss"
    SITEMAP = "sitemap"
    UNKNOWN = "unknown"


class ExtractionMethod(str, Enum):
    """Method used to extract a field."""
    CSS = "css"
    XPATH = "xpath"
    REGEX = "regex"
    AI = "ai"
    JSON_PATH = "jsonpath"
    CUSTOM = "custom"


# ─── Request / Response ─────────────────────────────────────────────


class CrawlRequest(BaseModel):
    """A single crawl request. Immutable once created."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    url: str
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    cookies: dict[str, str] = Field(default_factory=dict)
    body: str | bytes | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    depth: int = 0
    parent_url: str | None = None
    dont_filter: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CrawlResponse(BaseModel):
    """Raw HTTP response from the downloader."""
    request_id: str
    url: str
    status_code: int = 0
    headers: dict[str, str] = Field(default_factory=dict)
    body: str | bytes = ""
    content_type: ContentType = ContentType.UNKNOWN
    encoding: str = "utf-8"
    elapsed_ms: float = 0.0
    redirect_urls: list[str] = Field(default_factory=list)
    error: str | None = None


# ─── Extraction ─────────────────────────────────────────────────────


class ExtractionField(BaseModel):
    """A single extracted field with provenance."""
    name: str
    value: Any
    method: ExtractionMethod = ExtractionMethod.CSS
    selector: str | None = None
    confidence: float = 1.0
    raw: str | None = None


class ExtractionResult(BaseModel):
    """Complete extraction result for a single page."""
    request_id: str
    url: str
    fields: list[ExtractionField] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    ai_summary: str | None = None
    ai_classification: str | None = None
    ai_tags: list[str] = Field(default_factory=list)
    raw_data: dict[str, Any] = Field(default_factory=dict)

    def get(self, name: str, default: Any = None) -> Any:
        """Get field value by name, with optional default."""
        for field in self.fields:
            if field.name == name:
                return field.value
        return default

    def to_dict(self) -> dict[str, Any]:
        """Flatten fields to a plain dict for storage."""
        result: dict[str, Any] = {}
        for field in self.fields:
            result[field.name] = field.value
        result["_url"] = self.url
        result["_links"] = self.links
        result["_metadata"] = self.metadata
        if self.ai_summary:
            result["_ai_summary"] = self.ai_summary
        if self.ai_classification:
            result["_ai_classification"] = self.ai_classification
        if self.ai_tags:
            result["_ai_tags"] = self.ai_tags
        return result


# ─── Final Result ───────────────────────────────────────────────────


class CrawlResult(BaseModel):
    """Final crawl result combining all processing stages."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    request: CrawlRequest
    response: CrawlResponse | None = None
    extraction: ExtractionResult | None = None
    status: CrawlStatus = CrawlStatus.PENDING
    error: str | None = None
    retry_count: int = 0
    pipeline_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    @computed_field
    @property
    def fingerprint(self) -> str:
        """SHA256-based content fingerprint for dedup."""
        content = ""
        if self.response:
            body = self.response.body
            if isinstance(body, bytes):
                body = body.decode("utf-8", errors="replace")
            content = body[:4096]
        elif self.extraction:
            content = str(self.extraction.to_dict())
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @computed_field
    @property
    def duration_ms(self) -> float:
        """Processing duration in milliseconds."""
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds() * 1000
        return 0.0

    def to_storage_dict(self) -> dict[str, Any]:
        """Serialize for storage backends."""
        data: dict[str, Any] = {
            "id": self.id,
            "url": self.request.url,
            "status": self.status.value,
            "fingerprint": self.fingerprint,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
        }
        if self.response:
            data["status_code"] = self.response.status_code
            data["content_type"] = self.response.content_type.value
        if self.extraction:
            data["extracted"] = self.extraction.to_dict()
        if self.error:
            data["error"] = self.error
        if self.pipeline_data:
            data["pipeline"] = self.pipeline_data
        return data


# ─── Statistics ─────────────────────────────────────────────────────


class CrawlStats(BaseModel):
    """Session statistics."""
    session_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    total_requests: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    bytes_downloaded: int = 0
    start_time: float = Field(default_factory=time.time)
    end_time: float | None = None

    @computed_field
    @property
    def elapsed_seconds(self) -> float:
        end = self.end_time or time.time()
        return round(end - self.start_time, 2)

    @computed_field
    @property
    def success_rate(self) -> float:
        total = self.completed + self.failed
        return round(self.completed / total * 100, 2) if total > 0 else 0.0

    @computed_field
    @property
    def pages_per_second(self) -> float:
        elapsed = self.elapsed_seconds
        return round(self.completed / elapsed, 2) if elapsed > 0 else 0.0
