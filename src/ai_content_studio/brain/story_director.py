"""StoryDirector — prepares creative intent before LLM generation."""

from ai_content_studio.shared.models.creative_brief import CreativeBrief
from ai_content_studio.shared.models.emotion import Emotion

_DEFAULT_EMOTION = Emotion.SELF_DISCOVERY
_DEFAULT_NARRATIVE_ARC = "recognition-conflict-reflection-resonance"
_DEFAULT_DURATION_SECONDS = 60


class StoryDirector:
    """Assembles a CreativeBrief from a raw idea."""

    def direct(self, idea: str) -> CreativeBrief:
        """Return a CreativeBrief derived from the given idea."""
        return CreativeBrief(
            idea=idea,
            primary_emotion=_DEFAULT_EMOTION,
            theme=idea,
            narrative_arc=_DEFAULT_NARRATIVE_ARC,
            target_duration_seconds=_DEFAULT_DURATION_SECONDS,
        )
