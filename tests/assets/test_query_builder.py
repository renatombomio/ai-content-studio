"""Tests for SearchQueryBuilder."""

from ai_content_studio.assets.query_builder import SearchQueryBuilder
from ai_content_studio.shared.models import Scene
from ai_content_studio.shared.models.emotion import Emotion


def _make_scene(
    narration: str = "A man walks alone at dusk.",
    emotion: Emotion = Emotion.LONELINESS,
    order: int = 1,
) -> Scene:
    return Scene(
        order=order,
        narration=narration,
        visual_prompt="close-up of a face",
        emotion=emotion,
        duration_seconds=5.0,
    )


def test_build_returns_string() -> None:
    builder = SearchQueryBuilder()
    result = builder.build(_make_scene())
    assert isinstance(result, str)


def test_build_is_not_empty() -> None:
    builder = SearchQueryBuilder()
    result = builder.build(_make_scene())
    assert result.strip() != ""


def test_output_is_deterministic() -> None:
    builder = SearchQueryBuilder()
    scene = _make_scene("I waited by the door every evening.", Emotion.LONGING)
    assert builder.build(scene) == builder.build(scene)


def test_different_scenes_produce_different_queries() -> None:
    builder = SearchQueryBuilder()
    scene_a = _make_scene("She planted a seed in the rain.", Emotion.HOPE)
    scene_b = _make_scene("He sat alone in a dark room.", Emotion.GRIEF)
    assert builder.build(scene_a) != builder.build(scene_b)


def test_emotion_influences_query() -> None:
    builder = SearchQueryBuilder()
    scene_hope = _make_scene("A child runs through a field.", Emotion.HOPE)
    scene_grief = _make_scene("A child runs through a field.", Emotion.GRIEF)
    assert builder.build(scene_hope) != builder.build(scene_grief)


def test_emotion_word_appears_in_query() -> None:
    builder = SearchQueryBuilder()
    result = builder.build(_make_scene("Hands reach for the light.", Emotion.HOPE))
    assert "hopeful" in result


def test_first_person_narration_adds_person() -> None:
    builder = SearchQueryBuilder()
    result = builder.build(_make_scene("I looked out at the empty street.", Emotion.LONELINESS))
    assert "person" in result


def test_third_person_narration_omits_person() -> None:
    builder = SearchQueryBuilder()
    result = builder.build(_make_scene("The old man sat under a tree.", Emotion.NOSTALGIA))
    assert "person" not in result


def test_empty_narration_returns_emotion_word_and_cinematic_terms() -> None:
    builder = SearchQueryBuilder()
    result = builder.build(_make_scene(narration="", emotion=Emotion.WONDER))
    assert "breathtaking" in result
    assert len(result.split()) > 1


def test_query_contains_no_stop_words() -> None:
    stop_words = {"a", "an", "the", "and", "or", "for", "in", "of", "to", "that"}
    builder = SearchQueryBuilder()
    result = builder.build(_make_scene("I kept waiting for a message that never came.", Emotion.LONELINESS))
    query_words = set(result.lower().split())
    assert query_words.isdisjoint(stop_words)


def test_query_length_is_bounded() -> None:
    builder = SearchQueryBuilder()
    scene = _make_scene(
        "She walked slowly through the long empty corridor at midnight thinking of home.",
        Emotion.MELANCHOLY,
    )
    result = builder.build(scene)
    assert len(result.split()) <= 10
