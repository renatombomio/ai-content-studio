"""Tests for the visual language layer."""

from ai_content_studio.assets.query_builder import SearchQueryBuilder
from ai_content_studio.assets.visual_language import get_cinematic_terms
from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.shared.models.scene_concept import SceneConcept


def _make_concept(emotion: Emotion, concepts: list[str] | None = None) -> SceneConcept:
    return SceneConcept(emotion=emotion, concepts=concepts or [])


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
    result = builder.build(_make_concept(Emotion.NOSTALGIA))
    cinematic = get_cinematic_terms(Emotion.NOSTALGIA)
    assert any(term in result for term in cinematic)


def test_query_is_richer_than_emotion_word_alone() -> None:
    builder = SearchQueryBuilder()
    result = builder.build(_make_concept(Emotion.LONELINESS))
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
    concept = _make_concept(Emotion.LONGING, ["river", "road"])
    assert builder.build(concept) == builder.build(concept)


# --- multiple pillars (emotions from different editorial contexts) ---

def test_shadow_work_emotions_enriched() -> None:
    """Shadow Work pillar uses GRIEF, REGRET, INNER_CONFLICT."""
    builder = SearchQueryBuilder()
    for emotion in (Emotion.GRIEF, Emotion.REGRET, Emotion.INNER_CONFLICT):
        result = builder.build(_make_concept(emotion))
        cinematic = get_cinematic_terms(emotion)
        assert any(term in result for term in cinematic)


def test_mental_health_emotions_enriched() -> None:
    """Mental Health pillar uses RELIEF, HOPE, ACCEPTANCE."""
    builder = SearchQueryBuilder()
    for emotion in (Emotion.RELIEF, Emotion.HOPE, Emotion.ACCEPTANCE):
        result = builder.build(_make_concept(emotion))
        cinematic = get_cinematic_terms(emotion)
        assert any(term in result for term in cinematic)


def test_poetic_emotions_enriched() -> None:
    """Poetic Writing pillar uses NOSTALGIA, WONDER, LONGING."""
    builder = SearchQueryBuilder()
    for emotion in (Emotion.NOSTALGIA, Emotion.WONDER, Emotion.LONGING):
        result = builder.build(_make_concept(emotion))
        cinematic = get_cinematic_terms(emotion)
        assert any(term in result for term in cinematic)
