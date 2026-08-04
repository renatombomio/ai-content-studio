"""Search query builder — assembles a visual search query from a SceneConcept."""

from ai_content_studio.assets.visual_language import get_cinematic_terms
from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.shared.models.scene_concept import SceneConcept

_EMOTION_VISUAL: dict[Emotion, str] = {
    Emotion.NOSTALGIA: "nostalgic",
    Emotion.LONGING: "longing",
    Emotion.LONELINESS: "lonely",
    Emotion.MELANCHOLY: "melancholic",
    Emotion.REGRET: "regretful",
    Emotion.GRIEF: "grieving",
    Emotion.HOPE: "hopeful",
    Emotion.ACCEPTANCE: "peaceful",
    Emotion.VULNERABILITY: "vulnerable",
    Emotion.DISAPPOINTMENT: "disappointed",
    Emotion.RELIEF: "relieved",
    Emotion.WONDER: "breathtaking",
    Emotion.INNER_CONFLICT: "conflicted",
    Emotion.SELF_DISCOVERY: "contemplative",
}

_MAX_CONCEPTS = 3


class SearchQueryBuilder:
    """Assembles a visual search query from a SceneConcept and cinematic visual language."""

    def build(self, concept: SceneConcept) -> str:
        """Return a visual search query from semantic concepts and emotional atmosphere."""
        parts: list[str] = []

        emotion_word = _EMOTION_VISUAL.get(concept.emotion)
        if emotion_word:
            parts.append(emotion_word)

        parts.extend(concept.concepts[:_MAX_CONCEPTS])
        parts.extend(get_cinematic_terms(concept.emotion))

        if concept.visual_focus:
            parts.append(concept.visual_focus)

        return " ".join(parts)
