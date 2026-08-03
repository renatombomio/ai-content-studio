"""Prompt builder — assembles the final prompt for story generation."""

from ai_content_studio.brain.prompts import load_story_prompt
from ai_content_studio.brands.brand_context import BrandContext
from ai_content_studio.shared.models import CreativeBrief

_BRIEF_HEADER = "## Creative Brief\n\n"


class PromptBuilder:
    """Constructs the complete story generation prompt from brand identity, instructions, and brief."""

    def __init__(self, brand_context: BrandContext | None = None) -> None:
        self._brand_context = brand_context or BrandContext.load()
        self._story_prompt = load_story_prompt()

    def build_story_prompt(self, brief: CreativeBrief) -> str:
        """Return the full prompt: Cocoa Talk identity + story instructions + creative brief."""
        brief_section = (
            f"{_BRIEF_HEADER}"
            f"**Idea:** {brief.idea}\n"
            f"**Primary Emotion:** {brief.primary_emotion.value}\n"
            f"**Theme:** {brief.theme}\n"
            f"**Narrative Arc:** {brief.narrative_arc}\n"
            f"**Target Duration:** {brief.target_duration_seconds} seconds"
        )
        return f"{self._brand_context.system_prompt}\n\n---\n\n{self._story_prompt}\n\n---\n\n{brief_section}"
