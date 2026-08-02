"""Tests for Brain module interfaces and service."""

import inspect

import pytest

from ai_content_studio.brain.interfaces import Brain


def test_brain_is_abstract() -> None:
    assert inspect.isabstract(Brain)


def test_brain_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        Brain()  # type: ignore[abstract]


def test_brain_has_generate_story_method() -> None:
    assert hasattr(Brain, "generate_story")
    assert getattr(Brain.generate_story, "__isabstractmethod__", False)


def test_brain_interface_has_generate_story() -> None:
    assert hasattr(Brain, "generate_story")


def test_no_concrete_brain_in_production_module() -> None:
    import ai_content_studio.brain as brain_module
    members = inspect.getmembers(brain_module, inspect.isclass)
    concrete = [
        cls for _, cls in members
        if issubclass(cls, Brain) and cls is not Brain and not inspect.isabstract(cls)
    ]
    assert concrete == [], f"Unexpected concrete Brain implementations: {concrete}"
