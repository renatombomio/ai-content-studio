"""SceneConceptExtractor — derives semantic visual concepts from a Scene."""

import re

from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.shared.models.scene import Scene
from ai_content_studio.shared.models.scene_concept import SceneConcept

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
    "rest", "rest of",
})

# Camera and direction terms that describe production intent, not visual subjects.
_CAMERA_TERMS: frozenset[str] = frozenset({
    "shot", "camera", "frame", "depth", "field", "angle", "view",
    "extreme", "slightly", "slowly", "barely", "gently", "softly",
    "clearly", "directly", "visible", "footage", "image", "video",
    "photo", "lens", "aperture", "exposure", "centered", "framed",
    "curled", "resting", "cast", "filter", "motion", "movement",
    "panning", "tilting", "zoom", "cut", "transition", "static",
    "focus", "blur", "bokeh", "wide", "medium", "close", "closeup",
    "overhead", "aerial", "handheld", "tripod", "tracking", "dolly",
})

_NON_ALPHA = re.compile(r"[^a-zA-Z\s-]")
_MULTI_SPACE = re.compile(r"\s+")

_FOCUS_PATTERNS = [
    (re.compile(r"extreme close.?up", re.IGNORECASE), "close-up"),
    (re.compile(r"close.?up", re.IGNORECASE), "close-up"),
    (re.compile(r"wide shot", re.IGNORECASE), "wide"),
    (re.compile(r"medium shot", re.IGNORECASE), "portrait"),
    (re.compile(r"aerial", re.IGNORECASE), "aerial"),
    (re.compile(r"overhead", re.IGNORECASE), "overhead"),
]

_MAX_CONCEPTS = 3


class SceneConceptExtractor:
    """Extracts semantic visual concepts from a Scene's visual prompt."""

    def extract(self, scene: Scene) -> SceneConcept:
        """Return a SceneConcept derived from scene.visual_prompt and scene.emotion."""
        return self.extract_from_prompt(scene.visual_prompt, scene.emotion)

    def extract_from_prompt(self, visual_prompt: str, emotion: Emotion) -> SceneConcept:
        """Return a SceneConcept derived from a visual prompt string and emotion."""
        return SceneConcept(
            emotion=emotion,
            concepts=_extract_concepts(visual_prompt),
            visual_focus=_detect_focus(visual_prompt),
        )


def _extract_concepts(visual_prompt: str) -> list[str]:
    if not visual_prompt:
        return []
    cleaned = _NON_ALPHA.sub(" ", visual_prompt)
    cleaned = _MULTI_SPACE.sub(" ", cleaned).lower().strip()
    words = cleaned.split()
    return [
        w for w in words
        if w not in _STOP_WORDS and w not in _CAMERA_TERMS and len(w) > 2
    ][:_MAX_CONCEPTS]


def _detect_focus(visual_prompt: str) -> str | None:
    for pattern, label in _FOCUS_PATTERNS:
        if pattern.search(visual_prompt):
            return label
    return None
