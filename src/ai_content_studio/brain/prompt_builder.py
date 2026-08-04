"""Prompt builder — assembles the final prompt for story generation."""

from ai_content_studio.brain.prompts import load_story_prompt
from ai_content_studio.brands.brand_context import BrandContext
from ai_content_studio.brands.content_profiles import get_content_profile
from ai_content_studio.brands.editorial_profiles import get_profile
from ai_content_studio.shared.models import CreativeBrief

_BRIEF_HEADER = "## Creative Brief\n\n"


class PromptBuilder:
    """Constructs the complete story generation prompt from brand identity, instructions, and brief."""

    def __init__(self, brand_context: BrandContext | None = None) -> None:
        self._brand_context = brand_context or BrandContext.load()
        self._story_prompt = load_story_prompt()

    def build_story_prompt(self, brief: CreativeBrief) -> str:
        """Return the full prompt: brand → editorial → content → brief → story template."""
        editorial_section = get_profile(brief.pillar).to_prompt_section()
        content_section = get_content_profile(brief.content_type).to_prompt_section()
        brief_section = (
            f"{_BRIEF_HEADER}"
            f"**Pillar:** {brief.pillar.value}\n"
            f"**Content Type:** {brief.content_type.value}\n"
            f"**Language:** {brief.language}\n"
            f"**Idea:** {brief.idea}\n"
            f"**Primary Emotion:** {brief.primary_emotion.value}\n"
            f"**Theme:** {brief.theme}\n"
            f"**Narrative Arc:** {brief.narrative_arc}\n"
            f"**Target Duration:** {brief.target_duration_seconds} seconds"
        )
        return (
            f"{self._brand_context.system_prompt}\n\n---\n\n"
            f"{editorial_section}\n\n---\n\n"
            f"{content_section}\n\n---\n\n"
            f"{self._story_prompt}\n\n---\n\n"
            f"{brief_section}"
        )
