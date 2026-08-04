"""ReflectionParser — validates LLM JSON responses into Reflection models."""

import json
import re

from pydantic import ValidationError as PydanticValidationError

from ai_content_studio.core.exceptions import ValidationError
from ai_content_studio.shared.models.editorial import EditorialPillar
from ai_content_studio.shared.models.reflection import Reflection


class ReflectionParser:
    """Parses a raw JSON string from an LLM into a validated Reflection instance."""

    def parse(
        self,
        response: str,
        pillar: EditorialPillar = EditorialPillar.SHADOW_WORK,
        language: str = "es",
    ) -> Reflection:
        """Parse and validate a JSON string into a Reflection."""
        try:
            data = json.loads(_strip_fences(response))
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Malformed JSON: {exc}") from exc

        data["pillar"] = pillar
        data["language"] = language

        try:
            return Reflection.model_validate(data)
        except PydanticValidationError as exc:
            raise ValidationError(f"Reflection validation failed: {exc}") from exc


def _strip_fences(text: str) -> str:
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    return match.group(1) if match else text.strip()
