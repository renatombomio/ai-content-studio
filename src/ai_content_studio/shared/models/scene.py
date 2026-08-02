"""Scene domain model."""

import uuid

from pydantic import BaseModel, Field


class Scene(BaseModel):
    """A single scene in a story."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order: int
    narration: str
    visual_prompt: str
    emotion: str
    duration_seconds: float
