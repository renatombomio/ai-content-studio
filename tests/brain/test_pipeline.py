"""End-to-end Brain pipeline test using a fake LLM provider."""

import json

from ai_content_studio.brain.parser import StoryParser
from ai_content_studio.brain.prompt_builder import PromptBuilder
from ai_content_studio.brain.providers import LLMProvider
from ai_content_studio.shared.models import Scene, Story

_FAKE_STORY = {
    "title": "The Last Harvest",
    "hook": "He planted the tree the year his daughter was born. He never saw it fruit.",
    "caption": "Some things we grow for others.",
    "hashtags": ["#CocoaTalk", "#Patience"],
    "scenes": [
        {
            "order": 1,
            "narration": "A man kneels in red soil, pressing a seed into the ground.",
            "visual_prompt": "Extreme close-up of weathered hands pressing a seed into dark earth, golden afternoon light.",
            "emotion": "hope",
            "duration_seconds": 5.0,
        },
        {
            "order": 2,
            "narration": "Years pass. The tree grows taller than the house.",
            "visual_prompt": "Time-lapse silhouette of a cacao tree growing against a pale sky.",
            "emotion": "wonder",
            "duration_seconds": 4.0,
        },
        {
            "order": 3,
            "narration": "A young woman picks the first pod. She does not know the story yet.",
            "visual_prompt": "A woman's hand reaching for a ripe cacao pod, sun filtering through leaves.",
            "emotion": "melancholy",
            "duration_seconds": 6.0,
        },
    ],
}


class FakeLLMProvider(LLMProvider):
    """Returns a fixed valid Story JSON regardless of prompt input."""

    def __init__(self) -> None:
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return json.dumps(_FAKE_STORY)


def test_pipeline_generates_prompt() -> None:
    builder = PromptBuilder()
    provider = FakeLLMProvider()

    prompt = builder.build_story_prompt("cocoa origin")
    provider.generate(prompt)

    assert provider.last_prompt is not None
    assert "cocoa origin" in provider.last_prompt


def test_pipeline_prompt_contains_identity() -> None:
    from ai_content_studio.brain.prompts import load_system_prompt

    builder = PromptBuilder()
    provider = FakeLLMProvider()

    prompt = builder.build_story_prompt("the first harvest")
    provider.generate(prompt)

    assert load_system_prompt() in provider.last_prompt  # type: ignore[operator]


def test_pipeline_parser_returns_story() -> None:
    builder = PromptBuilder()
    provider = FakeLLMProvider()
    parser = StoryParser()

    prompt = builder.build_story_prompt("the first harvest")
    response = provider.generate(prompt)
    story = parser.parse(response)

    assert isinstance(story, Story)


def test_pipeline_story_has_expected_title() -> None:
    builder = PromptBuilder()
    provider = FakeLLMProvider()
    parser = StoryParser()

    prompt = builder.build_story_prompt("the first harvest")
    story = parser.parse(provider.generate(prompt))

    assert story.title == "The Last Harvest"


def test_pipeline_story_has_expected_scenes() -> None:
    builder = PromptBuilder()
    provider = FakeLLMProvider()
    parser = StoryParser()

    prompt = builder.build_story_prompt("the first harvest")
    story = parser.parse(provider.generate(prompt))

    assert len(story.scenes) == 3
    for i, scene in enumerate(story.scenes, start=1):
        assert isinstance(scene, Scene)
        assert scene.order == i


def test_pipeline_is_end_to_end() -> None:
    """Full pipeline: idea → prompt → LLM → parse → Story."""
    idea = "a farmer who plants cocoa for a future he will not see"

    builder = PromptBuilder()
    provider = FakeLLMProvider()
    parser = StoryParser()

    story = parser.parse(provider.generate(builder.build_story_prompt(idea)))

    assert isinstance(story, Story)
    assert story.hook
    assert story.caption
    assert len(story.scenes) > 0
