"""Brain prompts — story generation instructions."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

STORY_PROMPT_PATH = PROMPTS_DIR / "story_prompt.md"


def load_story_prompt() -> str:
    """Return the story generation prompt."""
    return STORY_PROMPT_PATH.read_text(encoding="utf-8")


__all__ = [
    "STORY_PROMPT_PATH",
    "load_story_prompt",
]
