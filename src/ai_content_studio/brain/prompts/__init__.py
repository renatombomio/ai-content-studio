"""Brain prompts — story and reflection generation instructions."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

STORY_PROMPT_PATH = PROMPTS_DIR / "story_prompt.md"
REFLECTION_PROMPT_PATH = PROMPTS_DIR / "reflection_prompt.md"


def load_story_prompt() -> str:
    """Return the story generation prompt."""
    return STORY_PROMPT_PATH.read_text(encoding="utf-8")


def load_reflection_prompt() -> str:
    """Return the reflection generation prompt."""
    return REFLECTION_PROMPT_PATH.read_text(encoding="utf-8")


__all__ = [
    "REFLECTION_PROMPT_PATH",
    "STORY_PROMPT_PATH",
    "load_reflection_prompt",
    "load_story_prompt",
]
