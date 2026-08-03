"""Brain service — orchestrates the complete story generation pipeline."""

from ai_content_studio.brain.parser import StoryParser
from ai_content_studio.brain.prompt_builder import PromptBuilder
from ai_content_studio.brain.providers.base import LLMProvider
from ai_content_studio.brain.story_director import StoryDirector
from ai_content_studio.shared.models import Story


class BrainService:
    """Orchestrates the full pipeline: idea → CreativeBrief → prompt → LLM → Story."""

    def __init__(
        self,
        story_director: StoryDirector,
        prompt_builder: PromptBuilder,
        llm_provider: LLMProvider,
        story_parser: StoryParser,
    ) -> None:
        self._story_director = story_director
        self._prompt_builder = prompt_builder
        self._llm_provider = llm_provider
        self._story_parser = story_parser

    def generate_story(self, idea: str) -> Story:
        """Generate a Story from an idea by running the full Brain pipeline."""
        brief = self._story_director.direct(idea)
        prompt = self._prompt_builder.build_story_prompt(brief)
        response = self._llm_provider.generate(prompt)
        return self._story_parser.parse(response)
