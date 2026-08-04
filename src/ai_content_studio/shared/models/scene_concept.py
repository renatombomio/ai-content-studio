"""SceneConcept — semantic visual representation of a Scene."""

from pydantic import BaseModel

from ai_content_studio.shared.models.emotion import Emotion


class SceneConcept(BaseModel):
    """Semantic visual intent derived from a Scene, used to build asset search queries."""

    emotion: Emotion
    concepts: list[str]
    visual_focus: str | None = None
    avoid_terms: list[str] = []
