"""End-to-end integration test for the full Cocoa Talk Studio pipeline.

Mocks: Anthropic LLM, asset providers, Kokoro voice, FFmpeg, TikTok HTTP.
Real:  StoryDirector, PromptBuilder, StoryParser, SearchQueryBuilder,
       AssetRanker, TimelineBuilder, SubtitleGenerator, all service classes.
"""

import json
import struct
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_content_studio.assets.interface import AssetProvider
from ai_content_studio.assets.query_builder import SearchQueryBuilder
from ai_content_studio.assets.ranking import AssetRanker
from ai_content_studio.assets.service import AssetService
from ai_content_studio.brain.parser import StoryParser
from ai_content_studio.brain.prompt_builder import PromptBuilder
from ai_content_studio.brain.providers.base import LLMProvider
from ai_content_studio.brain.service import BrainService
from ai_content_studio.brain.story_director import StoryDirector
from ai_content_studio.publisher.service import PublicationService
from ai_content_studio.publisher.tiktok import TikTokPublisher
from ai_content_studio.publisher.tiktok_oauth import TikTokOAuth
from ai_content_studio.shared.models import Asset, Publication, PublicationStatus, Story
from ai_content_studio.video.renderer import FFmpegRenderer
from ai_content_studio.video.service import RenderService
from ai_content_studio.video.subtitles import SubtitleGenerator
from ai_content_studio.video.timeline_builder import TimelineBuilder
from ai_content_studio.video.voice.interface import VoiceProvider

# ---------------------------------------------------------------------------
# Fake data
# ---------------------------------------------------------------------------

_STORY_JSON = json.dumps({
    "title": "The Origin of Cocoa",
    "hook": "Did you know chocolate has a 3,000-year history?",
    "caption": "Explore the rich world of cocoa.",
    "hashtags": ["#CocoaTalk", "#Chocolate"],
    "scenes": [
        {
            "order": 1,
            "narration": "The ancient Maya were the first to cultivate cocoa.",
            "visual_prompt": "Ancient jungle with cocoa trees at sunrise.",
            "emotion": "wonder",
            "duration_seconds": 8.0,
        }
    ],
})

_TOKEN_BODY = {
    "access_token": "act-integration",
    "refresh_token": "rft-integration",
    "expires_in": 86400,
    "open_id": "uid-cocoa",
}

_CREATOR_INFO_BODY = {
    "data": {
        "privacy_level_options": ["PUBLIC_TO_EVERYONE"],
        "comment_disabled": False,
        "duet_disabled": False,
        "stitch_disabled": False,
        "max_video_post_duration_sec": 600,
    },
    "error": {"code": "ok", "message": "", "log_id": "x"},
}

_INIT_BODY = {
    "data": {
        "publish_id": "pub-cocoa-001",
        "upload_url": "https://upload.tiktok.com/v1/cocoa?key=abc",
    },
    "error": {"code": "ok", "message": "", "log_id": "x"},
}

_STATUS_BODY = {
    "data": {
        "status": "PUBLISH_COMPLETE",
        "publicaly_available_post_id": "8880000000001",
    },
    "error": {"code": "ok", "message": "", "log_id": "x"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_wav() -> bytes:
    """Minimal valid WAV bytes readable by RenderService._parse_wav_* helpers."""
    data = bytearray(44 + 200)
    struct.pack_into("<H", data, 22, 1)       # num_channels = 1
    struct.pack_into("<I", data, 24, 22050)   # sample_rate = 22050
    struct.pack_into("<H", data, 34, 16)      # bits_per_sample = 16
    return bytes(data)


def _make_asset() -> Asset:
    return Asset(
        scene_id="",
        source="pexels",
        provider_id="99999",
        asset_type="video",
        url="https://videos.pexels.com/cocoa.mp4",
        thumbnail_url="https://images.pexels.com/cocoa.jpg",
    )


def _ok(body: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = body
    resp.raise_for_status = MagicMock()
    return resp


def _upload_ok() -> MagicMock:
    resp = MagicMock()
    resp.status_code = 201
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    path = tmp_path / "cocoa.mp4"
    path.write_bytes(b"x" * 100)
    return path


@pytest.fixture
def mock_llm() -> MagicMock:
    provider = MagicMock(spec=LLMProvider)
    provider.generate.return_value = _STORY_JSON
    return provider


@pytest.fixture
def mock_asset_provider() -> MagicMock:
    provider = MagicMock(spec=AssetProvider)
    provider.search.return_value = [_make_asset()]
    return provider


@pytest.fixture
def mock_voice() -> MagicMock:
    provider = MagicMock(spec=VoiceProvider)
    provider.generate.return_value = _make_fake_wav()
    return provider


@pytest.fixture
def mock_renderer(output_path: Path) -> MagicMock:
    renderer = MagicMock(spec=FFmpegRenderer)
    renderer.render.return_value = output_path
    return renderer


@pytest.fixture
def brain(mock_llm: MagicMock) -> BrainService:
    return BrainService(
        story_director=StoryDirector(),
        prompt_builder=PromptBuilder(),
        llm_provider=mock_llm,
        story_parser=StoryParser(),
    )


@pytest.fixture
def asset_service(mock_asset_provider: MagicMock) -> AssetService:
    return AssetService(
        query_builder=SearchQueryBuilder(),
        providers=[mock_asset_provider],
        ranker=AssetRanker(),
    )


@pytest.fixture
def render_service(mock_voice: MagicMock, mock_renderer: MagicMock) -> RenderService:
    return RenderService(
        timeline_builder=TimelineBuilder(),
        voice_provider=mock_voice,
        subtitle_generator=SubtitleGenerator(),
        renderer=mock_renderer,
    )


@pytest.fixture
def pub_service() -> PublicationService:
    oauth = TikTokOAuth()
    publisher = TikTokPublisher(oauth=oauth)
    return PublicationService(
        oauth=oauth,
        publisher=publisher,
        poll_interval=0.0,
        poll_timeout=30.0,
    )


# ---------------------------------------------------------------------------
# Full pipeline test
# ---------------------------------------------------------------------------

def test_full_cocoa_pipeline(
    brain: BrainService,
    asset_service: AssetService,
    render_service: RenderService,
    pub_service: PublicationService,
    output_path: Path,
    mock_llm: MagicMock,
    mock_asset_provider: MagicMock,
    mock_voice: MagicMock,
    mock_renderer: MagicMock,
) -> None:
    # 1. Brain — generate story
    story = brain.generate_story("The origin of cocoa")

    assert isinstance(story, Story)
    assert story.title
    assert len(story.scenes) >= 1
    mock_llm.generate.assert_called_once()

    # 2. Assets — find assets for each scene
    assets_by_scene: dict[str, list[Asset]] = {
        scene.id: asset_service.find_assets(scene, limit=1)
        for scene in story.scenes
    }

    assert len(assets_by_scene) == len(story.scenes)
    assert mock_asset_provider.search.call_count == len(story.scenes)
    for scene_assets in assets_by_scene.values():
        assert len(scene_assets) >= 1

    # 3. Video — build timeline, synthesize voice, generate subtitles, render
    rendered_path = render_service.render(story, assets_by_scene, output_path)

    assert rendered_path == output_path
    mock_voice.generate.assert_called_once()
    mock_renderer.render.assert_called_once()

    # 4. Publication — publish to TikTok
    publication = Publication(
        platform="tiktok",
        video_path=rendered_path,
        title=story.title,
        caption=story.caption,
        hashtags=story.hashtags,
    )

    post_effects = [
        _ok(_TOKEN_BODY),
        _ok(_CREATOR_INFO_BODY),
        _ok(_INIT_BODY),
        _ok(_STATUS_BODY),
    ]

    with patch("httpx.post", side_effect=post_effects), \
         patch("httpx.put", return_value=_upload_ok()), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        result = pub_service.publish(publication, "authcode-cocoa")

    assert isinstance(result, Publication)
    assert result.status == PublicationStatus.PUBLISHED
    assert result.publish_id == "pub-cocoa-001"
    assert result.external_id == "8880000000001"
    assert result.published_at is not None


# ---------------------------------------------------------------------------
# Stage-level orchestration checks
# ---------------------------------------------------------------------------

def test_story_generation(brain: BrainService, mock_llm: MagicMock) -> None:
    story = brain.generate_story("The origin of cocoa")
    assert isinstance(story, Story)
    mock_llm.generate.assert_called_once()


def test_asset_generation(asset_service: AssetService, mock_asset_provider: MagicMock) -> None:
    from ai_content_studio.shared.models import Scene

    scene = Scene(
        order=1,
        narration="A cocoa farmer harvests pods.",
        visual_prompt="Cocoa farm at golden hour.",
        emotion="wonder",
        duration_seconds=5.0,
    )
    assets = asset_service.find_assets(scene, limit=1)
    assert len(assets) >= 1
    mock_asset_provider.search.assert_called_once()


def test_timeline_creation_and_rendering(
    render_service: RenderService,
    mock_voice: MagicMock,
    mock_renderer: MagicMock,
    output_path: Path,
) -> None:
    from ai_content_studio.shared.models import Scene
    from ai_content_studio.shared.models import Story as StoryModel

    scene = Scene(
        order=1,
        narration="A cocoa farmer harvests pods.",
        visual_prompt="Cocoa farm at golden hour.",
        emotion="wonder",
        duration_seconds=5.0,
    )
    story = StoryModel(
        title="T",
        hook="H",
        caption="C",
        hashtags=[],
        scenes=[scene],
    )
    assets_by_scene: dict[str, list[Asset]] = {scene.id: [_make_asset()]}
    path = render_service.render(story, assets_by_scene, output_path)

    assert path == output_path
    mock_voice.generate.assert_called_once()
    mock_renderer.render.assert_called_once()


def test_publication(pub_service: PublicationService, output_path: Path) -> None:
    publication = Publication(
        platform="tiktok",
        video_path=output_path,
        title="The Origin of Cocoa",
        caption="Explore cocoa.",
        hashtags=["#CocoaTalk"],
    )
    post_effects = [
        _ok(_TOKEN_BODY),
        _ok(_CREATOR_INFO_BODY),
        _ok(_INIT_BODY),
        _ok(_STATUS_BODY),
    ]
    with patch("httpx.post", side_effect=post_effects), \
         patch("httpx.put", return_value=_upload_ok()), \
         patch("ai_content_studio.publisher.service.time.sleep"):
        result = pub_service.publish(publication, "authcode-cocoa")

    assert result.status == PublicationStatus.PUBLISHED
