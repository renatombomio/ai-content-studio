"""Tests for core path constants."""

from pathlib import Path

from ai_content_studio.core.paths import (
    ASSETS,
    BRANDS,
    CACHE,
    DATA,
    DOCS,
    OUTPUT,
    PROJECTS,
    RENDERS,
    ROOT,
    SRC,
    TEMP,
)

ALL_PATHS = [ROOT, SRC, DOCS, BRANDS, DATA, CACHE, ASSETS, PROJECTS, RENDERS, OUTPUT, TEMP]


def test_all_exports_are_paths() -> None:
    for p in ALL_PATHS:
        assert isinstance(p, Path), f"{p} is not a Path"


def test_all_paths_relative_to_root() -> None:
    for p in ALL_PATHS:
        assert str(p).startswith(str(ROOT)), f"{p} is not under ROOT"


def test_path_names() -> None:
    assert SRC == ROOT / "src"
    assert DOCS == ROOT / "docs"
    assert BRANDS == ROOT / "brands"
    assert DATA == ROOT / "data"
    assert CACHE == DATA / "cache"
    assert ASSETS == DATA / "assets"
    assert PROJECTS == DATA / "projects"
    assert RENDERS == DATA / "renders"
    assert OUTPUT == DATA / "output"
    assert TEMP == DATA / "temp"


def test_root_is_absolute() -> None:
    assert ROOT.is_absolute()


def test_no_directories_created() -> None:
    # DATA itself may exist (e.g. cover_history.json), but sub-dirs that the
    # project hasn't written to yet must not be auto-created by paths.py.
    auto_created_subdirs = [CACHE, ASSETS, PROJECTS, RENDERS, OUTPUT, TEMP]
    for p in auto_created_subdirs:
        assert not p.exists(), f"{p} should not be created by paths.py"
