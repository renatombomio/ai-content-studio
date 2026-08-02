"""Tests for the CreativeBrief domain model."""

from ai_content_studio.shared.models import CreativeBrief, Emotion


def _make_brief(**kwargs: object) -> CreativeBrief:
    defaults: dict[str, object] = {
        "idea": "A farmer who plants cocoa for a future he will not see.",
        "primary_emotion": Emotion.LONGING,
        "theme": "Legacy and sacrifice",
        "narrative_arc": "recognition → grief → acceptance → wonder",
        "target_duration_seconds": 50,
    }
    defaults.update(kwargs)
    return CreativeBrief(**defaults)  # type: ignore[arg-type]


def test_creative_brief_creation() -> None:
    brief = _make_brief()
    assert brief.idea == "A farmer who plants cocoa for a future he will not see."
    assert brief.primary_emotion == Emotion.LONGING
    assert brief.target_duration_seconds == 50


def test_creative_brief_emotion_integration() -> None:
    for emotion in Emotion:
        brief = _make_brief(primary_emotion=emotion)
        assert brief.primary_emotion == emotion


def test_creative_brief_model_dump() -> None:
    brief = _make_brief()
    data = brief.model_dump()
    assert data["idea"] == "A farmer who plants cocoa for a future he will not see."
    assert data["primary_emotion"] == "longing"
    assert data["target_duration_seconds"] == 50


def test_creative_brief_json_round_trip() -> None:
    brief = _make_brief()
    restored = CreativeBrief.model_validate_json(brief.model_dump_json())
    assert restored.idea == brief.idea
    assert restored.primary_emotion == brief.primary_emotion
    assert restored.theme == brief.theme
    assert restored.narrative_arc == brief.narrative_arc
    assert restored.target_duration_seconds == brief.target_duration_seconds
