"""Editorial profiles — writing guidance per Cocoa Talk editorial pillar."""

from dataclasses import dataclass

from ai_content_studio.shared.models.editorial import EditorialPillar

_HEADER = "## Editorial Profile"


@dataclass(frozen=True)
class EditorialProfile:
    """Structured writing guidance for one editorial pillar."""

    pillar: EditorialPillar
    focus_areas: tuple[str, ...]
    constraints: tuple[str, ...]

    def to_prompt_section(self) -> str:
        focus = ", ".join(self.focus_areas)
        constraints = ", ".join(self.constraints) if self.constraints else "none"
        return (
            f"{_HEADER}: {self.pillar.value}\n\n"
            f"**Focus:** {focus}\n"
            f"**Constraints:** {constraints}"
        )


_PROFILES: dict[EditorialPillar, EditorialProfile] = {
    EditorialPillar.SHADOW_WORK: EditorialProfile(
        pillar=EditorialPillar.SHADOW_WORK,
        focus_areas=(
            "self-awareness",
            "inner child",
            "emotional wounds",
            "boundaries",
            "acceptance",
        ),
        constraints=("reflection instead of advice",),
    ),
    EditorialPillar.POETIC_WRITING: EditorialProfile(
        pillar=EditorialPillar.POETIC_WRITING,
        focus_areas=(
            "original writing only",
            "minimal language",
            "sensory imagery",
            "emotional rhythm",
        ),
        constraints=("no rhyme requirement", "no imitation of existing authors"),
    ),
    EditorialPillar.INTRAPERSONAL: EditorialProfile(
        pillar=EditorialPillar.INTRAPERSONAL,
        focus_areas=(
            "relationship with oneself",
            "identity",
            "loneliness",
            "self-talk",
            "forgiveness",
            "personal growth",
        ),
        constraints=(),
    ),
    EditorialPillar.MENTAL_HEALTH: EditorialProfile(
        pillar=EditorialPillar.MENTAL_HEALTH,
        focus_areas=("empathy", "calm tone", "emotional validation without clinical claims"),
        constraints=("no diagnosis", "no therapy", "no medical advice"),
    ),
}

# Exhaustiveness check: every pillar must have a profile.
assert set(_PROFILES) == set(EditorialPillar), (
    f"Missing profiles for: {set(EditorialPillar) - set(_PROFILES)}"
)


def get_profile(pillar: EditorialPillar) -> EditorialProfile:
    """Return the EditorialProfile for the given pillar."""
    return _PROFILES[pillar]
