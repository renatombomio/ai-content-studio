"""Tests for SearchQueryBuilder."""

from ai_content_studio.assets.query_builder import SearchQueryBuilder
from ai_content_studio.assets.visual_language import get_cinematic_terms
from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.shared.models.scene_concept import SceneConcept


def _make_concept(
    emotion: Emotion = Emotion.LONELINESS,
    concepts: list[str] | None = None,
    visual_focus: str | None = None,
) -> SceneConcept:
    return SceneConcept(
        emotion=emotion,
        concepts=concepts if concepts is not None else ["child", "window", "rain"],
    )


def test_build_returns_string() -> None:
    builder = SearchQueryBuilder()
    result = builder.build(_make_concept())
    assert isinstance(result, str)


def test_build_is_not_empty() -> None:
    builder = SearchQueryBuilder()
    result = builder.build(_make_concept())
    assert result.strip() != ""


def test_output_is_deterministic() -> None:
    builder = SearchQueryBuilder()
    concept = _make_concept(Emotion.LONGING, ["road", "horizon"])
    assert builder.build(concept) == builder.build(concept)


def test_different_emotions_produce_different_queries() -> None:
    builder = SearchQueryBuilder()
    concept_hope = _make_concept(Emotion.HOPE, ["field", "light"])
    concept_grief = _make_concept(Emotion.GRIEF, ["field", "light"])
    assert builder.build(concept_hope) != builder.build(concept_grief)


def test_different_concepts_produce_different_queries() -> None:
    builder = SearchQueryBuilder()
    c1 = _make_concept(Emotion.NOSTALGIA, ["window", "rain"])
    c2 = _make_concept(Emotion.NOSTALGIA, ["forest", "river"])
    assert builder.build(c1) != builder.build(c2)


def test_emotion_word_appears_in_query() -> None:
    builder = SearchQueryBuilder()
    result = builder.build(_make_concept(Emotion.HOPE, ["seed", "soil"]))
    assert "hopeful" in result


def test_concepts_appear_in_query() -> None:
    builder = SearchQueryBuilder()
    result = builder.build(_make_concept(Emotion.GRIEF, ["candle", "dark"]))
    assert "candle" in result
    assert "dark" in result


def test_cinematic_terms_appear_in_query() -> None:
    builder = SearchQueryBuilder()
    result = builder.build(_make_concept(Emotion.NOSTALGIA, ["table"]))
    cinematic = get_cinematic_terms(Emotion.NOSTALGIA)
    assert any(term in result for term in cinematic)


def test_visual_focus_appears_in_query() -> None:
    builder = SearchQueryBuilder()
    concept = SceneConcept(
        emotion=Emotion.VULNERABILITY,
        concepts=["hands"],
        visual_focus="close-up",
    )
    result = builder.build(concept)
    assert "close-up" in result


def test_no_visual_focus_omits_it() -> None:
    builder = SearchQueryBuilder()
    concept = SceneConcept(emotion=Emotion.HOPE, concepts=["sunrise"])
    result = builder.build(concept)
    assert "close-up" not in result
    assert "wide" not in result


def test_empty_concepts_still_produces_query() -> None:
    builder = SearchQueryBuilder()
    result = builder.build(SceneConcept(emotion=Emotion.WONDER, concepts=[]))
    assert "breathtaking" in result


# --- Narration exclusion ---

def test_narration_words_do_not_appear() -> None:
    """SceneConcept carries no narration — narration words cannot leak into queries."""
    builder = SearchQueryBuilder()
    spanish_narration_words = ["hubo", "aprendiste", "alguien", "guardarlo", "tragarlo"]
    concept = _make_concept(Emotion.GRIEF, ["rain", "candle"])
    result = builder.build(concept)
    for word in spanish_narration_words:
        assert word not in result


def test_query_contains_only_semantic_visual_concepts() -> None:
    builder = SearchQueryBuilder()
    concept = _make_concept(Emotion.LONELINESS, ["empty street", "fog"])
    result = builder.build(concept)
    # Must contain concept terms and emotion word, never narration fragments
    assert "empty street" in result or "fog" in result
    assert "lonely" in result
