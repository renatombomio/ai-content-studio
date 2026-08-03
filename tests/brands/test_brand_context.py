"""Tests for BrandContext."""

from ai_content_studio.brands.brand_context import BrandContext


def test_load_returns_brand_context() -> None:
    ctx = BrandContext.load()
    assert isinstance(ctx, BrandContext)


def test_brand_document_is_non_empty() -> None:
    ctx = BrandContext.load()
    assert len(ctx.brand_document.strip()) > 0


def test_mascot_document_is_non_empty() -> None:
    ctx = BrandContext.load()
    assert len(ctx.mascot_document.strip()) > 0


def test_brand_document_contains_cocoa_talk() -> None:
    ctx = BrandContext.load()
    assert "Cocoa Talk" in ctx.brand_document


def test_mascot_document_contains_coco() -> None:
    ctx = BrandContext.load()
    assert "Coco" in ctx.mascot_document


def test_system_prompt_returns_brand_document() -> None:
    ctx = BrandContext.load()
    assert ctx.system_prompt == ctx.brand_document


def test_brand_context_is_immutable() -> None:
    ctx = BrandContext.load()
    try:
        ctx.brand_document = "mutated"  # type: ignore[misc]
        raise AssertionError("Should have raised on mutation")
    except (AttributeError, TypeError):
        pass


def test_stub_brand_context_works() -> None:
    ctx = BrandContext(brand_document="test brand", mascot_document="test mascot")
    assert ctx.brand_document == "test brand"
    assert ctx.mascot_document == "test mascot"
    assert ctx.system_prompt == "test brand"


def test_two_loads_are_equal() -> None:
    assert BrandContext.load() == BrandContext.load()
