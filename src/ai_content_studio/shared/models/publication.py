"""Publication domain model."""

from datetime import datetime

from pydantic import BaseModel


class Publication(BaseModel):
    """Publishing metadata for a rendered video."""

    platform: str
    caption: str
    hashtags: list[str]
    scheduled_at: datetime | None = None
