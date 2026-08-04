"""ReflectionDirector — prepares creative intent for short editorial reflection generation."""

from ai_content_studio.shared.models.creative_brief import CreativeBrief
from ai_content_studio.shared.models.editorial import ContentType, EditorialPillar
from ai_content_studio.shared.models.emotion import Emotion

_DEFAULT_PILLAR = EditorialPillar.SHADOW_WORK
_DEFAULT_EMOTION = Emotion.VULNERABILITY
_DEFAULT_DURATION_SECONDS = 12


class ReflectionDirector:
    """Assembles a CreativeBrief suited for reflection content generation."""

    def direct(
        self,
        idea: str,
        pillar: EditorialPillar = _DEFAULT_PILLAR,
        emotion: Emotion = _DEFAULT_EMOTION,
        language: str = "es",
    ) -> CreativeBrief:
        """Return a CreativeBrief for a short editorial reflection."""
        return CreativeBrief(
            idea=idea,
            primary_emotion=emotion,
            theme=idea,
            narrative_arc="single-reflection",
            target_duration_seconds=_DEFAULT_DURATION_SECONDS,
            pillar=pillar,
            content_type=ContentType.VIDEO,
            language=language,
        )
