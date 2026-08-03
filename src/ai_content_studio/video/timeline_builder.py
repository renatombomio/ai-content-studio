"""Timeline builder — assembles a Story and assets into a Timeline."""

from ai_content_studio.shared.models.asset import Asset
from ai_content_studio.shared.models.scene import Scene
from ai_content_studio.shared.models.story import Story
from ai_content_studio.shared.models.timeline import Timeline, TimelineAsset, TimelineScene

_MIN_SCENE_DURATION = 2.0


class TimelineBuilder:
    """Transforms a Story and resolved assets into a Timeline."""

    def build(self, story: Story, assets_by_scene: dict[str, list[Asset]]) -> Timeline:
        """Build a Timeline from a Story and a mapping of scene id → assets."""
        durations = [_scene_duration(s) for s in story.scenes]
        scenes: list[TimelineScene] = []
        cursor = 0.0

        for scene, duration in zip(story.scenes, durations, strict=True):
            scene_end = cursor + duration
            assets = assets_by_scene.get(scene.id, [])
            timeline_assets = [
                TimelineAsset(asset=a, start_time=cursor, end_time=scene_end)
                for a in assets
            ]
            scenes.append(TimelineScene(scene=scene, assets=timeline_assets))
            cursor = scene_end

        return Timeline(story=story, scenes=scenes, duration=cursor)


def _scene_duration(scene: Scene) -> float:
    word_count = len(scene.narration.split())
    duration = max(word_count * 0.4, _MIN_SCENE_DURATION)
    return round(duration, 4)
