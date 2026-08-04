"""Editorial taxonomy for Cocoa Talk content."""

from enum import StrEnum


class EditorialPillar(StrEnum):
    """Cocoa Talk editorial pillars — content thematic classification."""

    SHADOW_WORK = "shadow_work"
    POETIC_WRITING = "poetic_writing"
    INTRAPERSONAL = "intrapersonal"
    MENTAL_HEALTH = "mental_health"


class ContentType(StrEnum):
    """Output format for a piece of Cocoa Talk content."""

    VIDEO = "video"
    CAROUSEL = "carousel"
    IMAGE = "image"
