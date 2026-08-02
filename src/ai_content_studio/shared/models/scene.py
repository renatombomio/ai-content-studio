"""Scene domain model."""

import uuid

from pydantic import BaseModel, Field

from ai_content_studio.shared.models.emotion import Emotion


class Scene(BaseModel):
    """A single scene in a story."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order: int
    narration: str
    visual_prompt: str
    emotion: Emotion
    duration_seconds: float
