"""Asset domain model."""

import uuid

from pydantic import BaseModel, Field


class Asset(BaseModel):
    """A resolved media asset assigned to a scene."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scene_id: str
    source: str
    provider_id: str
    asset_type: str
    url: str
    thumbnail_url: str
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    author: str | None = None
    license: str | None = None
    path: str | None = None
