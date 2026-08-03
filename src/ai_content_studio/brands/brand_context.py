"""BrandContext — loads and exposes the Cocoa Talk brand identity from docs/."""

from dataclasses import dataclass
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parents[3]
_BRAND_PATH = _PROJECT_ROOT / "docs" / "BRAND.md"
_COCO_PATH = _PROJECT_ROOT / "docs" / "COCO.md"


@dataclass(frozen=True)
class BrandContext:
    """Immutable container for the Cocoa Talk brand identity documents.

    Injected into every generator so all content starts from the same identity.
    """

    brand_document: str
    mascot_document: str

    @classmethod
    def load(cls) -> "BrandContext":
        """Load brand identity from docs/BRAND.md and docs/COCO.md."""
        return cls(
            brand_document=_BRAND_PATH.read_text(encoding="utf-8"),
            mascot_document=_COCO_PATH.read_text(encoding="utf-8"),
        )

    @property
    def system_prompt(self) -> str:
        """Return the brand document as the LLM system context."""
        return self.brand_document
