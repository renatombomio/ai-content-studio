"""Timeline domain model."""

from pydantic import BaseModel

from ai_content_studio.shared.models.asset import Asset
from ai_content_studio.shared.models.scene import Scene
from ai_content_studio.shared.models.story import Story


class TimelineAsset(BaseModel):
    """An asset placed at a specific time interval on the timeline."""

    asset: Asset
    start_time: float
    end_time: float


class TimelineScene(BaseModel):
    """A scene with its assigned assets."""

    scene: Scene
    assets: list[TimelineAsset]


class VoiceTrack(BaseModel):
    """Synthesized narration audio for the full timeline."""

    audio: bytes
    sample_rate: int
    duration: float


class SubtitleCue(BaseModel):
    """A single timed subtitle entry."""

    text: str
    start_time: float
    end_time: float


class Timeline(BaseModel):
    """Canonical video representation consumed by the renderer."""

    story: Story
    scenes: list[TimelineScene]
    duration: float
    voice_track: VoiceTrack | None = None
    subtitles: list[SubtitleCue] = []
