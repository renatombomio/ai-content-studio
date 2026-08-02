"""Tests for the Emotion domain model."""


from ai_content_studio.shared.models import Emotion, Scene, Story


def test_emotion_values_are_valid_strings() -> None:
    for emotion in Emotion:
        assert isinstance(emotion.value, str)
        assert len(emotion.value) > 0


def test_all_expected_emotions_exist() -> None:
    expected = {
        "NOSTALGIA", "LONGING", "LONELINESS", "MELANCHOLY", "REGRET",
        "GRIEF", "HOPE", "ACCEPTANCE", "VULNERABILITY", "DISAPPOINTMENT",
        "RELIEF", "WONDER", "INNER_CONFLICT", "SELF_DISCOVERY",
    }
    assert {e.name for e in Emotion} == expected


def test_scene_accepts_emotion_enum() -> None:
    scene = Scene(
        order=1,
        narration="The light fades slowly.",
        visual_prompt="Golden hour through dusty blinds.",
        emotion=Emotion.LONGING,
        duration_seconds=5.0,
    )
    assert scene.emotion == Emotion.LONGING


def test_scene_accepts_emotion_string() -> None:
    scene = Scene(
        order=1,
        narration="She stood at the door.",
        visual_prompt="A silhouette in a doorway.",
        emotion="grief",
        duration_seconds=4.0,
    )
    assert scene.emotion == Emotion.GRIEF


def test_story_serialization_preserves_emotion() -> None:
    scene = Scene(
        order=1,
        narration="He watched the last train leave.",
        visual_prompt="Empty platform, single overhead light.",
        emotion=Emotion.REGRET,
        duration_seconds=6.0,
    )
    story = Story(
        title="The Last Train",
        hook="He always said he would leave. He never did.",
        caption="Some goodbyes happen without moving.",
        hashtags=["#CocoaTalk"],
        scenes=[scene],
    )
    data = story.model_dump()
    assert data["scenes"][0]["emotion"] == "regret"


def test_story_json_round_trip_preserves_emotion() -> None:
    scene = Scene(
        order=1,
        narration="A child holds a letter she cannot read yet.",
        visual_prompt="Small hands holding an old envelope, afternoon light.",
        emotion=Emotion.NOSTALGIA,
        duration_seconds=5.0,
    )
    story = Story(
        title="Letters",
        hook="She kept them for thirty years before she understood them.",
        caption="Some things wait until we're ready.",
        hashtags=["#CocoaTalk"],
        scenes=[scene],
    )
    raw = story.model_dump_json()
    restored = Story.model_validate_json(raw)
    assert restored.scenes[0].emotion == Emotion.NOSTALGIA
