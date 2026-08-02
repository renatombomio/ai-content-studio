"""Integration tests for BrainService pipeline."""

import json
from unittest.mock import MagicMock

from ai_content_studio.brain.parser import StoryParser
from ai_content_studio.brain.prompt_builder import PromptBuilder
from ai_content_studio.brain.providers.base import LLMProvider
from ai_content_studio.brain.service import BrainService
from ai_content_studio.brain.story_director import StoryDirector
from ai_content_studio.shared.models import Story

_VALID_STORY_JSON = json.dumps({
    "title": "The Last Harvest",
    "hook": "He planted the tree the year his daughter was born.",
    "caption": "Some things we grow for others.",
    "hashtags": ["#CocoaTalk"],
    "scenes": [
        {
            "order": 1,
            "narration": "A man kneels in red soil.",
            "visual_prompt": "Close-up of hands pressing a seed into earth.",
            "emotion": "hope",
            "duration_seconds": 5.0,
        }
    ],
})


def _make_service(llm_response: str = _VALID_STORY_JSON) -> tuple[BrainService, MagicMock]:
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate.return_value = llm_response
    service = BrainService(
        story_director=StoryDirector(),
        prompt_builder=PromptBuilder(),
        llm_provider=mock_provider,
        story_parser=StoryParser(),
    )
    return service, mock_provider


def test_generate_story_returns_story() -> None:
    service, _ = _make_service()
    story = service.generate_story("a farmer planting cocoa")
    assert isinstance(story, Story)


def test_story_director_is_invoked() -> None:
    director = MagicMock(spec=StoryDirector, wraps=StoryDirector())
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate.return_value = _VALID_STORY_JSON

    service = BrainService(
        story_director=director,
        prompt_builder=PromptBuilder(),
        llm_provider=mock_provider,
        story_parser=StoryParser(),
    )
    service.generate_story("an idea")
    director.direct.assert_called_once_with("an idea")


def test_llm_provider_receives_prompt() -> None:
    service, mock_provider = _make_service()
    service.generate_story("an idea")
    mock_provider.generate.assert_called_once()
    prompt_sent = mock_provider.generate.call_args.args[0]
    assert isinstance(prompt_sent, str)
    assert len(prompt_sent) > 0


def test_prompt_contains_idea() -> None:
    service, mock_provider = _make_service()
    service.generate_story("the weight of small decisions")
    prompt_sent = mock_provider.generate.call_args.args[0]
    assert "the weight of small decisions" in prompt_sent


def test_story_parser_receives_llm_response() -> None:
    parser = MagicMock(spec=StoryParser, wraps=StoryParser())
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.generate.return_value = _VALID_STORY_JSON

    service = BrainService(
        story_director=StoryDirector(),
        prompt_builder=PromptBuilder(),
        llm_provider=mock_provider,
        story_parser=parser,
    )
    service.generate_story("an idea")
    parser.parse.assert_called_once_with(_VALID_STORY_JSON)


def test_pipeline_execution_order() -> None:
    calls: list[str] = []

    class TrackingDirector(StoryDirector):
        def direct(self, idea: str):  # type: ignore[override]
            calls.append("director")
            return super().direct(idea)

    class TrackingProvider(LLMProvider):
        def generate(self, prompt: str) -> str:
            calls.append("provider")
            return _VALID_STORY_JSON

    class TrackingParser(StoryParser):
        def parse(self, response: str) -> Story:
            calls.append("parser")
            return super().parse(response)

    service = BrainService(
        story_director=TrackingDirector(),
        prompt_builder=PromptBuilder(),
        llm_provider=TrackingProvider(),
        story_parser=TrackingParser(),
    )
    service.generate_story("an idea")
    assert calls == ["director", "provider", "parser"]
