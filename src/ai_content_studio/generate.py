"""Entry point: generate a Story from an idea using the real Anthropic API.

Usage:
    uv run python -m ai_content_studio.generate
"""

import json
import sys
from pathlib import Path

from ai_content_studio.brain.parser import StoryParser
from ai_content_studio.brain.prompt_builder import PromptBuilder
from ai_content_studio.brain.providers.anthropic import AnthropicProvider
from ai_content_studio.brain.service import BrainService
from ai_content_studio.brain.story_director import StoryDirector
from ai_content_studio.brands.brand_context import BrandContext
from ai_content_studio.core.config import get_settings
from ai_content_studio.core.exceptions import ProviderError

_IDEA = (
    "Sometimes healing isn't becoming someone new. "
    "It's remembering who you were before the world convinced you to hide."
)

_OUTPUT_DIR = Path("output")
_OUTPUT_FILE = _OUTPUT_DIR / "story.json"


def main() -> None:
    settings = get_settings()

    if not settings.anthropic_api_key:
        print("ERROR: ANTHROPIC_API_KEY is not set. Add it to .env or export it.", file=sys.stderr)
        sys.exit(1)

    print(f"Model : {settings.anthropic_model}")
    print(f"Idea  : {_IDEA}\n")

    service = BrainService(
        story_director=StoryDirector(),
        prompt_builder=PromptBuilder(brand_context=BrandContext.load()),
        llm_provider=AnthropicProvider(),
        story_parser=StoryParser(),
    )

    try:
        story = service.generate_story(_IDEA)
    except ProviderError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Title  : {story.title}")
    print(f"Hook   : {story.hook}")
    print()
    for scene in story.scenes:
        print(f"  Scene {scene.order}: {scene.narration}")
    print()
    print(f"Caption: {story.caption}")
    print(f"Tags   : {' '.join(story.hashtags)}")

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _OUTPUT_FILE.write_text(json.dumps(story.model_dump(), indent=2, default=str))
    print(f"\nSaved  : {_OUTPUT_FILE}")


if __name__ == "__main__":
    main()
