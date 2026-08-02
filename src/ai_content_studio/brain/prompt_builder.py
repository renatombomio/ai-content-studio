"""Prompt builder — assembles the final prompt for story generation."""

from ai_content_studio.brain.prompts import load_story_prompt, load_system_prompt

_IDEA_HEADER = "## Idea\n\n"


class PromptBuilder:
    """Constructs the complete story generation prompt from identity, instructions, and idea."""

    def __init__(self) -> None:
        self._system_prompt = load_system_prompt()
        self._story_prompt = load_story_prompt()

    def build_story_prompt(self, idea: str) -> str:
        """Return the full prompt: Cocoa Talk identity + story instructions + user idea."""
        return f"{self._system_prompt}\n\n---\n\n{self._story_prompt}\n\n---\n\n{_IDEA_HEADER}{idea}"
