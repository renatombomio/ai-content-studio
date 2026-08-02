"""Story parser — validates LLM JSON responses into Story models."""

import json

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
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Malformed JSON: {exc}") from exc

        try:
            return Story.model_validate(data)
        except PydanticValidationError as exc:
            raise ValidationError(f"Story validation failed: {exc}") from exc
