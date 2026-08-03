"""Tests for shared domain models."""

from datetime import UTC, datetime

from ai_content_studio.shared.models import Asset, Publication, Scene, Story


def _make_scene(**kwargs: object) -> Scene:
    defaults = {
        "order": 1,
        "narration": "Welcome to Cocoa Talk.",
        "visual_prompt": "A warm coffee shop at sunrise.",
        "emotion": "acceptance",
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

def _make_asset(**kwargs: object) -> Asset:
    defaults: dict[str, object] = {
        "scene_id": "scene-1",
        "source": "pexels",
        "provider_id": "1448735",
        "asset_type": "video",
        "url": "https://player.vimeo.com/external/example.mp4",
        "thumbnail_url": "https://images.pexels.com/videos/1448735/preview.jpg",
    }
    defaults.update(kwargs)
    return Asset(**defaults)  # type: ignore[arg-type]


def test_asset_creation() -> None:
    asset = _make_asset()
    assert asset.source == "pexels"
    assert asset.asset_type == "video"
    assert asset.provider_id == "1448735"


def test_asset_id_auto_generated() -> None:
    a1 = _make_asset()
    a2 = _make_asset()
    assert a1.id != a2.id


def test_asset_model_dump() -> None:
    asset = _make_asset(source="pixabay")
    data = asset.model_dump()
    assert data["source"] == "pixabay"
    assert data["provider_id"] == "1448735"
    assert data["url"] is not None
    assert data["thumbnail_url"] is not None


def test_asset_optional_fields_default_none() -> None:
    asset = _make_asset()
    assert asset.width is None
    assert asset.height is None
    assert asset.duration is None
    assert asset.author is None
    assert asset.license is None
    assert asset.path is None


def test_asset_optional_fields_accepted() -> None:
    asset = _make_asset(
        width=1920,
        height=1080,
        duration=37.0,
        author="Jane Doe",
        license="Pexels License",
        path="/tmp/clip.mp4",
    )
    assert asset.width == 1920
    assert asset.height == 1080
    assert asset.duration == 37.0
    assert asset.author == "Jane Doe"
    assert asset.license == "Pexels License"
    assert asset.path == "/tmp/clip.mp4"


def test_asset_path_none_before_download() -> None:
    asset = _make_asset()
    assert asset.path is None


def test_asset_path_set_after_download() -> None:
    asset = _make_asset(path="/data/assets/clip.mp4")
    assert asset.path == "/data/assets/clip.mp4"


def test_asset_model_dump_includes_all_fields() -> None:
    asset = _make_asset(width=1280, height=720, duration=15.5, author="Photographer", license="Free")
    data = asset.model_dump()
    for field in ("id", "scene_id", "source", "provider_id", "asset_type", "url",
                  "thumbnail_url", "width", "height", "duration", "author", "license", "path"):
        assert field in data


def test_asset_scene_id_stored() -> None:
    scene = _make_scene()
    asset = _make_asset(scene_id=scene.id)
    assert asset.scene_id == scene.id


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
