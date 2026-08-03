"""Story parser — validates LLM JSON responses into Story models."""

import json
import re

from pydantic import ValidationError as PydanticValidationError

from ai_content_studio.core.exceptions import ValidationError
from ai_content_studio.shared.models import Story


class StoryParser:
    """Parses a raw JSON string from an LLM into a validated Story instance."""

    def parse(self, response: str) -> Story:
        """Parse and validate a JSON string into a Story.

        Raises ValidationError if the JSON is malformed or fails model validation.
        """
        try:
            data = json.loads(_strip_fences(response))
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Malformed JSON: {exc}") from exc

        try:
            return Story.model_validate(data)
        except PydanticValidationError as exc:
            raise ValidationError(f"Story validation failed: {exc}") from exc


def _strip_fences(text: str) -> str:
    """Remove markdown code fences if the LLM wrapped its JSON output."""
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    return match.group(1) if match else text.strip()
