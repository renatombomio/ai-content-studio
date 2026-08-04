"""Tests for EditorialProfile registry and profile content."""

import pytest

from ai_content_studio.brands.editorial_profiles import EditorialProfile, get_profile
from ai_content_studio.shared.models.editorial import EditorialPillar


def test_every_pillar_resolves_to_a_profile() -> None:
    for pillar in EditorialPillar:
        profile = get_profile(pillar)
        assert isinstance(profile, EditorialProfile)
        assert profile.pillar == pillar


def test_shadow_work_profile() -> None:
    profile = get_profile(EditorialPillar.SHADOW_WORK)
    assert "self-awareness" in profile.focus_areas
    assert "inner child" in profile.focus_areas
    assert "emotional wounds" in profile.focus_areas
    assert "boundaries" in profile.focus_areas
    assert "acceptance" in profile.focus_areas
    assert any("reflection" in c for c in profile.constraints)


def test_poetic_writing_profile() -> None:
    profile = get_profile(EditorialPillar.POETIC_WRITING)
    assert "sensory imagery" in profile.focus_areas
    assert "minimal language" in profile.focus_areas
    assert "emotional rhythm" in profile.focus_areas
    assert any("rhyme" in c for c in profile.constraints)
    assert any("imitation" in c for c in profile.constraints)


def test_intrapersonal_profile() -> None:
    profile = get_profile(EditorialPillar.INTRAPERSONAL)
    assert "identity" in profile.focus_areas
    assert "loneliness" in profile.focus_areas
    assert "self-talk" in profile.focus_areas
    assert "forgiveness" in profile.focus_areas
    assert "personal growth" in profile.focus_areas


def test_mental_health_profile() -> None:
    profile = get_profile(EditorialPillar.MENTAL_HEALTH)
    assert "empathy" in profile.focus_areas
    assert "calm tone" in profile.focus_areas
    assert any("diagnosis" in c for c in profile.constraints)
    assert any("therapy" in c for c in profile.constraints)
    assert any("medical" in c for c in profile.constraints)


def test_profile_pillar_identity() -> None:
    for pillar in EditorialPillar:
        assert get_profile(pillar).pillar is pillar


def test_to_prompt_section_contains_pillar_value() -> None:
    for pillar in EditorialPillar:
        section = get_profile(pillar).to_prompt_section()
        assert pillar.value in section


def test_to_prompt_section_contains_focus_areas() -> None:
    profile = get_profile(EditorialPillar.SHADOW_WORK)
    section = profile.to_prompt_section()
    for area in profile.focus_areas:
        assert area in section


def test_profiles_are_immutable() -> None:
    profile = get_profile(EditorialPillar.INTRAPERSONAL)
    with pytest.raises((AttributeError, TypeError)):
        profile.pillar = EditorialPillar.SHADOW_WORK  # type: ignore[misc]
