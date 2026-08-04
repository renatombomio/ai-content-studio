"""QuestionParser — parses Anthropic JSON response into a CocoaQuestion."""

import json
import re

from ai_content_studio.core.exceptions import ValidationError
from ai_content_studio.shared.models.editorial import EditorialPillar
from ai_content_studio.shared.models.question import CocoaQuestion

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


def _strip_fences(text: str) -> str:
    match = _FENCE_RE.search(text)
    return match.group(1) if match else text.strip()


class QuestionParser:
    """Parses an LLM JSON response into a CocoaQuestion."""

    def parse(
        self,
        response: str,
        pillar: EditorialPillar = EditorialPillar.SHADOW_WORK,
    ) -> CocoaQuestion:
        raw = _strip_fences(response)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Malformed JSON from brain: {exc}") from exc

        data["pillar"] = pillar
        try:
            return CocoaQuestion.model_validate(data)
        except Exception as exc:
            raise ValidationError(f"CocoaQuestion validation failed: {exc}") from exc
