"""Asset ranking engine — scores and orders assets for a given scene."""

from ai_content_studio.shared.models import Asset, Scene
from ai_content_studio.shared.models.emotion import Emotion

# Emotions with high video affinity: motion amplifies the feeling.
# Emotions with low affinity: stillness (photos) serve them better.
_EMOTION_VIDEO_AFFINITY: dict[Emotion, float] = {
    Emotion.GRIEF: 1.0,
    Emotion.LONELINESS: 1.0,
    Emotion.LONGING: 0.9,
    Emotion.INNER_CONFLICT: 0.9,
    Emotion.VULNERABILITY: 0.8,
    Emotion.MELANCHOLY: 0.8,
    Emotion.REGRET: 0.7,
    Emotion.DISAPPOINTMENT: 0.7,
    Emotion.WONDER: 0.6,
    Emotion.HOPE: 0.6,
    Emotion.SELF_DISCOVERY: 0.5,
    Emotion.RELIEF: 0.5,
    Emotion.ACCEPTANCE: 0.4,
    Emotion.NOSTALGIA: 0.3,
}

_TYPE_SCORES: dict[str, float] = {
    "video": 20.0,
    "photo": 10.0,
    "illustration": 8.0,
    "vector": 5.0,
}

# HD 1080p used as reference ceiling for resolution scoring.
_RESOLUTION_CEILING = 1920 * 1080


class AssetRanker:
    """Scores and sorts assets for a scene using deterministic weighted criteria."""

    def rank(self, scene: Scene, assets: list[Asset]) -> list[Asset]:
        """Return assets ordered from best to worst for the given scene."""
        if not assets:
            return []
        scored = [(asset, _total_score(scene, asset)) for asset in assets]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [asset for asset, _ in scored]


def _total_score(scene: Scene, asset: Asset) -> float:
    return (
        _score_orientation(asset)
        + _score_asset_type(asset)
        + _score_resolution(asset)
        + _score_duration(scene, asset)
        + _score_emotion(scene, asset)
    )


def _score_orientation(asset: Asset) -> float:
    """Portrait (9:16) preferred → 30. Square → 15. Landscape → 5. Unknown → 0."""
    if asset.width is None or asset.height is None or asset.height == 0:
        return 0.0
    ratio = asset.width / asset.height
    if ratio < 0.75:
        return 30.0
    if ratio <= 1.33:
        return 15.0
    return 5.0


def _score_asset_type(asset: Asset) -> float:
    """Video preferred → 20. Photo → 10. Illustration → 8. Vector/other → 5."""
    return _TYPE_SCORES.get(asset.asset_type, 5.0)


def _score_resolution(asset: Asset) -> float:
    """Higher pixel count scores higher; capped at 1080p reference → max 20."""
    if asset.width is None or asset.height is None:
        return 0.0
    pixels = asset.width * asset.height
    return min(pixels / _RESOLUTION_CEILING, 1.0) * 20.0


def _score_duration(scene: Scene, asset: Asset) -> float:
    """Closer to scene duration → higher score (max 20). Images score 0."""
    if asset.duration is None:
        return 0.0
    ideal = scene.duration_seconds
    if ideal <= 0:
        return 0.0
    diff = abs(asset.duration - ideal)
    return max(0.0, 20.0 * (1.0 - diff / ideal))


def _score_emotion(scene: Scene, asset: Asset) -> float:
    """Video/photo affinity determined by emotion. Max 10."""
    affinity = _EMOTION_VIDEO_AFFINITY.get(scene.emotion, 0.5)
    if asset.asset_type == "video":
        return affinity * 10.0
    return (1.0 - affinity) * 10.0
