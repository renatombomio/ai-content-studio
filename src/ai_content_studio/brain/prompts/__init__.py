"""Brain prompts — system identity and story generation instructions."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system_prompt.md"
STORY_PROMPT_PATH = PROMPTS_DIR / "story_prompt.md"


def load_system_prompt() -> str:
    """Return the Cocoa Talk system prompt."""
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def load_story_prompt() -> str:
    """Return the story generation prompt."""
    return STORY_PROMPT_PATH.read_text(encoding="utf-8")


__all__ = [
    "SYSTEM_PROMPT_PATH",
    "STORY_PROMPT_PATH",
    "load_system_prompt",
    "load_story_prompt",
]
