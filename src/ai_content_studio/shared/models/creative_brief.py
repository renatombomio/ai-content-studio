"""Creative brief domain model."""

from pydantic import BaseModel

from ai_content_studio.shared.models.editorial import ContentType, EditorialPillar
from ai_content_studio.shared.models.emotion import Emotion


class CreativeBrief(BaseModel):
    """The creative intent of a Story before it is generated."""

    idea: str
    primary_emotion: Emotion
    theme: str
    narrative_arc: str
    target_duration_seconds: int
    pillar: EditorialPillar
    content_type: ContentType
    language: str = "es"
