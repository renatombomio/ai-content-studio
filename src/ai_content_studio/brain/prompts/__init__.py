"""Brain prompts — story, reflection, and question generation instructions."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

STORY_PROMPT_PATH = PROMPTS_DIR / "story_prompt.md"
REFLECTION_PROMPT_PATH = PROMPTS_DIR / "reflection_prompt.md"
QUESTION_PROMPT_PATH = PROMPTS_DIR / "question_prompt.md"


def load_story_prompt() -> str:
    return STORY_PROMPT_PATH.read_text(encoding="utf-8")


def load_reflection_prompt() -> str:
    return REFLECTION_PROMPT_PATH.read_text(encoding="utf-8")


def load_question_prompt() -> str:
    return QUESTION_PROMPT_PATH.read_text(encoding="utf-8")


__all__ = [
    "QUESTION_PROMPT_PATH",
    "REFLECTION_PROMPT_PATH",
    "STORY_PROMPT_PATH",
    "load_question_prompt",
    "load_reflection_prompt",
    "load_story_prompt",
]
