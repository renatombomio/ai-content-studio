"""Asset domain model."""

import uuid

from pydantic import BaseModel, Field


class Asset(BaseModel):
    """A resolved media asset assigned to a scene."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scene_id: str
    source: str
    path: str
    asset_type: str
