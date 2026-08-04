"""Visual language layer — maps emotions to cinematic visual concepts."""

from ai_content_studio.shared.models.emotion import Emotion

_CINEMATIC_TERMS: dict[Emotion, tuple[str, ...]] = {
    Emotion.NOSTALGIA: ("window", "warm light", "golden hour", "film grain"),
    Emotion.LONGING: ("horizon", "fading light", "road", "distance"),
    Emotion.LONELINESS: ("empty street", "fog", "silhouette", "night"),
    Emotion.MELANCHOLY: ("rain", "grey", "autumn leaves", "overcast"),
    Emotion.REGRET: ("empty room", "shadow", "closed door", "letters"),
    Emotion.GRIEF: ("rain", "candle", "dark room", "black and white"),
    Emotion.HOPE: ("sunrise", "sunlight", "open sky", "seeds"),
    Emotion.ACCEPTANCE: ("mountains", "ocean", "forest", "walking path"),
    Emotion.VULNERABILITY: ("soft light", "close-up portrait", "hands", "tears"),
    Emotion.DISAPPOINTMENT: ("empty chair", "grey sky", "still life", "closed window"),
    Emotion.RELIEF: ("open window", "sunlight", "green nature", "gentle"),
    Emotion.WONDER: ("vast landscape", "stars", "light rays", "aerial"),
    Emotion.INNER_CONFLICT: ("mirror", "split light", "shadow", "dark room"),
    Emotion.SELF_DISCOVERY: ("forest path", "journal", "light through trees", "solitude"),
}

# Exhaustiveness check: every emotion must have cinematic terms.
assert set(_CINEMATIC_TERMS) == set(Emotion), (
    f"Missing cinematic terms for: {set(Emotion) - set(_CINEMATIC_TERMS)}"
)

_MAX_CINEMATIC_TERMS = 2


def get_cinematic_terms(emotion: Emotion) -> tuple[str, ...]:
    """Return cinematic visual concepts for the given emotion."""
    return _CINEMATIC_TERMS[emotion][:_MAX_CINEMATIC_TERMS]
