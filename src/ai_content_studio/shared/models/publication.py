"""Publication domain model."""

import uuid
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class PublicationStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"


class Publication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform: str
    video_path: Path
    title: str
    caption: str
    hashtags: list[str]

    status: PublicationStatus = PublicationStatus.PENDING

    publish_id: str | None = None
    external_id: str | None = None

    url: str | None = None
    published_at: datetime | None = None
