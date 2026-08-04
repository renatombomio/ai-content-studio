"""Tests for ContentProfile registry and profile content."""

import pytest

from ai_content_studio.brands.content_profiles import ContentProfile, get_content_profile
from ai_content_studio.shared.models.editorial import ContentType


def test_every_content_type_resolves_to_a_profile() -> None:
    for ct in ContentType:
        profile = get_content_profile(ct)
        assert isinstance(profile, ContentProfile)
        assert profile.content_type == ct


def test_video_profile() -> None:
    profile = get_content_profile(ContentType.VIDEO)
    assert "strong opening hook" in profile.characteristics
    assert "cinematic pacing" in profile.characteristics
    assert "ending reflection" in profile.characteristics
    assert any("vertical video" in c for c in profile.characteristics)


def test_carousel_profile() -> None:
    profile = get_content_profile(ContentType.CAROUSEL)
    assert "slide-based thinking" in profile.characteristics
    assert any("first slide" in c for c in profile.characteristics)
    assert any("second slide" in c for c in profile.characteristics)
    assert "minimal text" in profile.characteristics


def test_image_profile() -> None:
    profile = get_content_profile(ContentType.IMAGE)
    assert any("single" in c for c in profile.characteristics)
    assert "concise" in profile.characteristics
    assert "memorable" in profile.characteristics
    assert any("static" in c for c in profile.characteristics)


def test_profile_content_type_identity() -> None:
    for ct in ContentType:
        assert get_content_profile(ct).content_type is ct


def test_to_prompt_section_contains_content_type_value() -> None:
    for ct in ContentType:
        section = get_content_profile(ct).to_prompt_section()
        assert ct.value in section


def test_to_prompt_section_contains_characteristics() -> None:
    profile = get_content_profile(ContentType.VIDEO)
    section = profile.to_prompt_section()
    for char in profile.characteristics:
        assert char in section


def test_profiles_are_immutable() -> None:
    profile = get_content_profile(ContentType.CAROUSEL)
    with pytest.raises((AttributeError, TypeError)):
        profile.content_type = ContentType.VIDEO  # type: ignore[misc]
