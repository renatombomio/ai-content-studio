"""Content profiles — format guidance per Cocoa Talk ContentType."""

from dataclasses import dataclass

from ai_content_studio.shared.models.editorial import ContentType

_HEADER = "## Content Profile"


@dataclass(frozen=True)
class ContentProfile:
    """Structured format guidance for one content type."""

    content_type: ContentType
    characteristics: tuple[str, ...]

    def to_prompt_section(self) -> str:
        chars = ", ".join(self.characteristics)
        return f"{_HEADER}: {self.content_type.value}\n\n**Characteristics:** {chars}"


_PROFILES: dict[ContentType, ContentProfile] = {
    ContentType.VIDEO: ContentProfile(
        content_type=ContentType.VIDEO,
        characteristics=(
            "strong opening hook",
            "short paragraphs",
            "continuous emotional progression",
            "cinematic pacing",
            "ending reflection",
            "suitable for subtitle-driven vertical video",
        ),
    ),
    ContentType.CAROUSEL: ContentProfile(
        content_type=ContentType.CAROUSEL,
        characteristics=(
            "slide-based thinking",
            "first slide captures attention",
            "second slide delivers one powerful reflection or question",
            "minimal text",
            "visual balance",
            "encourages contemplation",
        ),
    ),
    ContentType.IMAGE: ContentProfile(
        content_type=ContentType.IMAGE,
        characteristics=(
            "one single complete idea",
            "concise",
            "memorable",
            "suitable for static visual content",
            "no storytelling required",
        ),
    ),
}

# Exhaustiveness check: every content type must have a profile.
assert set(_PROFILES) == set(ContentType), (
    f"Missing profiles for: {set(ContentType) - set(_PROFILES)}"
)


def get_content_profile(content_type: ContentType) -> ContentProfile:
    """Return the ContentProfile for the given content type."""
    return _PROFILES[content_type]
