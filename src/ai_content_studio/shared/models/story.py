"""Story domain model."""

import uuid

from pydantic import BaseModel, Field

from ai_content_studio.shared.models.scene import Scene


class Story(BaseModel):
    """A complete structured story ready for production."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    hook: str
    caption: str
    hashtags: list[str]
    scenes: list[Scene]
