"""Tests for Brain module interfaces and service."""

import inspect

import pytest

from ai_content_studio.brain.interfaces import Brain
from ai_content_studio.brain.service import BrainService
from ai_content_studio.shared.models import Scene, Story


def test_brain_is_abstract() -> None:
    assert inspect.isabstract(Brain)


def test_brain_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        Brain()  # type: ignore[abstract]


def test_brain_has_generate_story_method() -> None:
    assert hasattr(Brain, "generate_story")
    assert getattr(Brain.generate_story, "__isabstractmethod__", False)


def test_brain_service_accepts_brain_implementation() -> None:
    class StubBrain(Brain):
        def generate_story(self, idea: str) -> Story:
            return Story(
                title="Test",
                hook="Hook",
                caption="Caption",
                hashtags=[],
                scenes=[
                    Scene(
                        order=1,
                        narration="n",
                        visual_prompt="v",
                        emotion="calm",
                        duration_seconds=3.0,
                    )
                ],
            )

    service = BrainService(StubBrain())
    assert isinstance(service, BrainService)


def test_brain_service_delegates_to_implementation() -> None:
    class StubBrain(Brain):
        def generate_story(self, idea: str) -> Story:
            return Story(
                title=f"Story about {idea}",
                hook="Hook",
                caption="Caption",
                hashtags=["#test"],
                scenes=[
                    Scene(
                        order=1,
                        narration="n",
                        visual_prompt="v",
                        emotion="joy",
                        duration_seconds=4.0,
                    )
                ],
            )

    service = BrainService(StubBrain())
    story = service.generate_story("cocoa")
    assert isinstance(story, Story)
    assert story.title == "Story about cocoa"


def test_no_concrete_brain_in_production_module() -> None:
    import ai_content_studio.brain as brain_module
    members = inspect.getmembers(brain_module, inspect.isclass)
    concrete = [
        cls for _, cls in members
        if issubclass(cls, Brain) and cls is not Brain and not inspect.isabstract(cls)
    ]
    assert concrete == [], f"Unexpected concrete Brain implementations: {concrete}"
