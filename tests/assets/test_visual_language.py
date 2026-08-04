"""Tests for the visual language layer."""

from ai_content_studio.assets.query_builder import SearchQueryBuilder
from ai_content_studio.assets.visual_language import get_cinematic_terms
from ai_content_studio.shared.models import Scene
from ai_content_studio.shared.models.emotion import Emotion


def _make_scene(narration: str = "", emotion: Emotion = Emotion.NOSTALGIA) -> Scene:
    return Scene(
        order=1,
        narration=narration,
        visual_prompt="placeholder",
        emotion=emotion,
        duration_seconds=5.0,
    )


# --- emotional mapping ---

def test_every_emotion_has_cinematic_terms() -> None:
    for emotion in Emotion:
        terms = get_cinematic_terms(emotion)
        assert len(terms) > 0


def test_nostalgia_contains_expected_concepts() -> None:
    terms = get_cinematic_terms(Emotion.NOSTALGIA)
    assert "window" in terms or "warm light" in terms or "golden hour" in terms


def test_loneliness_contains_expected_concepts() -> None:
    terms = get_cinematic_terms(Emotion.LONELINESS)
    assert "fog" in terms or "silhouette" in terms or "empty street" in terms


def test_hope_contains_expected_concepts() -> None:
    terms = get_cinematic_terms(Emotion.HOPE)
    assert "sunrise" in terms or "sunlight" in terms or "open sky" in terms


def test_acceptance_contains_expected_concepts() -> None:
    terms = get_cinematic_terms(Emotion.ACCEPTANCE)
    assert "mountains" in terms or "ocean" in terms or "forest" in terms


def test_mental_health_adjacent_emotions_have_calm_terms() -> None:
    relief_terms = get_cinematic_terms(Emotion.RELIEF)
    assert any(w in " ".join(relief_terms) for w in ("sunlight", "window", "nature", "gentle"))


# --- cinematic enrichment in query ---

def test_cinematic_terms_appear_in_query() -> None:
    builder = SearchQueryBuilder()
    scene = _make_scene("She stood at the window.", Emotion.NOSTALGIA)
    result = builder.build(scene)
    cinematic = get_cinematic_terms(Emotion.NOSTALGIA)
    assert any(term in result for term in cinematic)


def test_query_is_richer_than_emotion_word_alone() -> None:
    builder = SearchQueryBuilder()
    scene = _make_scene("", Emotion.LONELINESS)
    result = builder.build(scene)
    assert len(result.split()) > 1


def test_cinematic_terms_differ_across_emotions() -> None:
    grief_terms = get_cinematic_terms(Emotion.GRIEF)
    wonder_terms = get_cinematic_terms(Emotion.WONDER)
    assert set(grief_terms) != set(wonder_terms)


# --- deterministic output ---

def test_cinematic_terms_are_deterministic() -> None:
    assert get_cinematic_terms(Emotion.MELANCHOLY) == get_cinematic_terms(Emotion.MELANCHOLY)


def test_query_is_deterministic_with_cinematic_enrichment() -> None:
    builder = SearchQueryBuilder()
    scene = _make_scene("I sat alone by the river.", Emotion.LONGING)
    assert builder.build(scene) == builder.build(scene)


# --- multiple pillars (emotions from different editorial contexts) ---

def test_shadow_work_emotions_enriched() -> None:
    """Shadow Work pillar uses GRIEF, REGRET, INNER_CONFLICT."""
    builder = SearchQueryBuilder()
    for emotion in (Emotion.GRIEF, Emotion.REGRET, Emotion.INNER_CONFLICT):
        result = builder.build(_make_scene(emotion=emotion))
        cinematic = get_cinematic_terms(emotion)
        assert any(term in result for term in cinematic)


def test_mental_health_emotions_enriched() -> None:
    """Mental Health pillar uses RELIEF, HOPE, ACCEPTANCE."""
    builder = SearchQueryBuilder()
    for emotion in (Emotion.RELIEF, Emotion.HOPE, Emotion.ACCEPTANCE):
        result = builder.build(_make_scene(emotion=emotion))
        cinematic = get_cinematic_terms(emotion)
        assert any(term in result for term in cinematic)


def test_poetic_emotions_enriched() -> None:
    """Poetic Writing pillar uses NOSTALGIA, WONDER, LONGING."""
    builder = SearchQueryBuilder()
    for emotion in (Emotion.NOSTALGIA, Emotion.WONDER, Emotion.LONGING):
        result = builder.build(_make_scene(emotion=emotion))
        cinematic = get_cinematic_terms(emotion)
        assert any(term in result for term in cinematic)
