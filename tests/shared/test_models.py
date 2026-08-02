"""Tests for shared domain models."""

from datetime import UTC, datetime

from ai_content_studio.shared.models import Asset, Publication, Scene, Story


def _make_scene(**kwargs: object) -> Scene:
    defaults = {
        "order": 1,
        "narration": "Welcome to Cocoa Talk.",
        "visual_prompt": "A warm coffee shop at sunrise.",
        "emotion": "calm",
        "duration_seconds": 5.0,
    }
    defaults.update(kwargs)  # type: ignore[arg-type]
    return Scene(**defaults)  # type: ignore[arg-type]


def _make_story(**kwargs: object) -> Story:
    defaults = {
        "title": "The Origin of Cocoa",
        "hook": "Did you know chocolate has a 3,000-year history?",
        "caption": "Explore the rich world of cocoa.",
        "hashtags": ["#CocoaTalk", "#Chocolate"],
        "scenes": [_make_scene(order=1), _make_scene(order=2)],
    }
    defaults.update(kwargs)  # type: ignore[arg-type]
    return Story(**defaults)  # type: ignore[arg-type]


# --- Scene ---

def test_scene_creation() -> None:
    scene = _make_scene()
    assert scene.order == 1
    assert scene.narration == "Welcome to Cocoa Talk."
    assert scene.duration_seconds == 5.0


def test_scene_id_auto_generated() -> None:
    s1 = _make_scene()
    s2 = _make_scene()
    assert s1.id != s2.id


def test_scene_model_dump() -> None:
    scene = _make_scene()
    data = scene.model_dump()
    assert "id" in data
    assert data["order"] == 1


# --- Story ---

def test_story_creation() -> None:
    story = _make_story()
    assert story.title == "The Origin of Cocoa"
    assert len(story.scenes) == 2


def test_story_id_auto_generated() -> None:
    s1 = _make_story()
    s2 = _make_story()
    assert s1.id != s2.id


def test_story_nested_scenes() -> None:
    story = _make_story()
    for i, scene in enumerate(story.scenes, start=1):
        assert isinstance(scene, Scene)
        assert scene.order == i


def test_story_model_dump_includes_scenes() -> None:
    story = _make_story()
    data = story.model_dump()
    assert isinstance(data["scenes"], list)
    assert "narration" in data["scenes"][0]


# --- Asset ---

def test_asset_creation() -> None:
    asset = Asset(scene_id="abc", source="pexels", path="/tmp/clip.mp4", asset_type="video")
    assert asset.source == "pexels"
    assert asset.asset_type == "video"


def test_asset_id_auto_generated() -> None:
    a1 = Asset(scene_id="x", source="local", path="/a", asset_type="image")
    a2 = Asset(scene_id="x", source="local", path="/a", asset_type="image")
    assert a1.id != a2.id


def test_asset_model_dump() -> None:
    asset = Asset(scene_id="abc", source="mixkit", path="/tmp/a.mp4", asset_type="video")
    data = asset.model_dump()
    assert data["source"] == "mixkit"


# --- Publication ---

def test_publication_creation() -> None:
    pub = Publication(platform="tiktok", caption="Watch this!", hashtags=["#cocoa"])
    assert pub.platform == "tiktok"
    assert pub.scheduled_at is None


def test_publication_scheduled_at_default_none() -> None:
    pub = Publication(platform="tiktok", caption="Hi", hashtags=[])
    assert pub.scheduled_at is None


def test_publication_with_scheduled_at() -> None:
    dt = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)
    pub = Publication(platform="tiktok", caption="Hi", hashtags=[], scheduled_at=dt)
    assert pub.scheduled_at == dt


def test_publication_model_dump() -> None:
    pub = Publication(platform="tiktok", caption="Hi", hashtags=["#a"])
    data = pub.model_dump()
    assert data["platform"] == "tiktok"
    assert data["hashtags"] == ["#a"]
