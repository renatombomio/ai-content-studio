"""CocoaQuestion — weekly introspective question carousel format for Cocoa Talk."""

import uuid

from pydantic import BaseModel, Field

from ai_content_studio.shared.models.editorial import EditorialPillar


class CocoaQuestion(BaseModel):
    """A single Cocoa Talk introspective question for the weekly carousel."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_text: str
    context: str
    caption: str = ""
    hashtags: list[str] = []
    pillar: EditorialPillar
