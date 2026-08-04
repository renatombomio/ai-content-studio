"""Search query builder — transforms a Scene into a visual search query."""

import re

from ai_content_studio.assets.visual_language import get_cinematic_terms
from ai_content_studio.shared.models import Scene
from ai_content_studio.shared.models.emotion import Emotion

_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "so", "yet", "for", "nor",
    "i", "me", "my", "we", "us", "our", "you", "your",
    "he", "she", "it", "they", "them", "their", "his", "her", "its",
    "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "shall", "may", "might", "must", "can",
    "in", "on", "at", "by", "with", "about", "from", "to", "of", "up",
    "out", "as", "into", "through", "during", "before", "after",
    "above", "below", "between",
    "that", "which", "who", "whom", "whose",
    "when", "where", "why", "how", "if", "while", "although", "because",
    "since", "until", "unless",
    "not", "no", "never", "always", "still", "just", "very", "really",
    "ever", "also", "too", "then", "than",
    "this", "these", "those", "what", "there", "here",
    "kept", "came", "got", "went", "said", "made", "knew", "thought",
})

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

_FIRST_PERSON = re.compile(r"\b(i|we|me|us|my|our)\b", re.IGNORECASE)
_NON_ALPHA = re.compile(r"[^a-zA-Z\s]")
_MAX_KEYWORDS = 3


class SearchQueryBuilder:
    """Transforms a Scene into a concise visual search query for asset providers."""

    def build(self, scene: Scene) -> str:
        """Return a cinematic visual search query derived from scene narration and emotion."""
        parts: list[str] = []

        emotion_word = _EMOTION_VISUAL.get(scene.emotion)
        if emotion_word:
            parts.append(emotion_word)

        if scene.narration and _FIRST_PERSON.search(scene.narration):
            parts.append("person")

        parts.extend(_extract_keywords(scene.narration)[:_MAX_KEYWORDS])
        parts.extend(get_cinematic_terms(scene.emotion))

        return " ".join(parts)


def _extract_keywords(narration: str) -> list[str]:
    if not narration:
        return []
    words = _NON_ALPHA.sub("", narration).lower().split()
    return [w for w in words if w not in _STOP_WORDS]
