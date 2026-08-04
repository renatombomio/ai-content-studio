"""Reflection domain model — the short editorial format for Cocoa Talk."""

import uuid

from pydantic import BaseModel, Field

from ai_content_studio.shared.models.editorial import EditorialPillar


class Reflection(BaseModel):
    """A single short editorial reflection: one thought, one visual, one feeling."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reflection_text: str
    visual_prompt: str
    title: str
    hashtags: list[str] = []
    pillar: EditorialPillar
    language: str = "es"
