#!/usr/bin/env python3
"""S6-006 — Generate one complete Cocoa Talk video from the editorial pipeline."""

import json
import sys
from pathlib import Path

import httpx

# Allow running from the project root without installing the package.
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ai_content_studio.assets.concept_extractor import SceneConceptExtractor
from ai_content_studio.assets.providers.pexels import PexelsProvider
from ai_content_studio.assets.query_builder import SearchQueryBuilder
from ai_content_studio.assets.ranking import AssetRanker
from ai_content_studio.assets.service import AssetService
from ai_content_studio.brain.parser import StoryParser
from ai_content_studio.brain.prompt_builder import PromptBuilder
from ai_content_studio.brain.providers.anthropic import AnthropicProvider
from ai_content_studio.brands.brand_context import BrandContext
from ai_content_studio.shared.models import Asset, CreativeBrief
from ai_content_studio.shared.models.editorial import ContentType, EditorialPillar
from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.video.renderer import FFmpegRenderer
from ai_content_studio.video.service import RenderService
from ai_content_studio.video.subtitles import SubtitleGenerator
from ai_content_studio.video.timeline_builder import TimelineBuilder

OUTPUT_DIR = Path(__file__).parents[1] / "output"
ASSETS_DIR = OUTPUT_DIR / "assets"
STORY_PATH = OUTPUT_DIR / "story.json"
VIDEO_PATH = OUTPUT_DIR / "video.mp4"

_IDEA = "El primer llanto que nunca dejamos salir"


def _download(asset: Asset, dest: Path) -> Asset:
    resp = httpx.get(asset.url, follow_redirects=True, timeout=30.0)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return asset.model_copy(update={"path": str(dest)})


def _ext(url: str) -> str:
    tail = url.rsplit(".", 1)[-1].split("?")[0]
    return tail if tail in {"mp4", "jpg", "jpeg", "png", "webm"} else "mp4"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)

    # ── CreativeBrief ────────────────────────────────────────────────────────
    brief = CreativeBrief(
        idea=_IDEA,
        primary_emotion=Emotion.GRIEF,
        theme="Las heridas que callamos en la infancia",
        narrative_arc="recognition-wound-reflection-acceptance",
        target_duration_seconds=60,
        pillar=EditorialPillar.SHADOW_WORK,
        content_type=ContentType.VIDEO,
        language="es",
    )

    print(f"Pillar:       {brief.pillar.value}")
    print(f"Content type: {brief.content_type.value}")
    print(f"Language:     {brief.language}")
    print(f"Idea:         {brief.idea}\n")

    # ── Brain ────────────────────────────────────────────────────────────────
    brand_context = BrandContext.load()
    prompt_builder = PromptBuilder(brand_context=brand_context)
    prompt = prompt_builder.build_story_prompt(brief)

    print("Generating story via Anthropic …")
    llm = AnthropicProvider()
    raw = llm.generate(prompt)
    story = StoryParser().parse(raw)

    print(f"Story title:  {story.title}")
    print(f"Scenes:       {len(story.scenes)}")
    STORY_PATH.write_text(story.model_dump_json(indent=2), encoding="utf-8")
    print(f"Saved:        {STORY_PATH}\n")

    # ── Assets ───────────────────────────────────────────────────────────────
    query_builder = SearchQueryBuilder()
    asset_service = AssetService(
        query_builder=query_builder,
        concept_extractor=SceneConceptExtractor(),
        providers=[PexelsProvider()],
        ranker=AssetRanker(),
    )

    assets_by_scene: dict[str, list[Asset]] = {}
    for scene in story.scenes:
        query = query_builder.build(scene)
        print(f"Scene {scene.order:>2} query:  {query!r}")

        try:
            found = asset_service.find_assets(scene, limit=8)
        except Exception as exc:
            print(f"  Asset search failed: {exc}")
            continue

        if not found:
            print("  No assets found — skipping scene")
            continue

        best = found[0]
        dest = ASSETS_DIR / f"scene_{scene.order:02d}.{_ext(best.url)}"
        print(f"  Selected:    {best.source}/{best.provider_id} ({best.asset_type})")

        try:
            best = _download(best, dest)
            print(f"  Downloaded:  {dest}")
        except Exception as exc:
            print(f"  Download failed: {exc} — skipping")
            continue

        assets_by_scene[scene.id] = [best]

    if not assets_by_scene:
        print("\nNo assets downloaded — cannot render.")
        sys.exit(1)

    # ── Render ───────────────────────────────────────────────────────────────
    print("\nRendering video …")
    render_service = RenderService(
        timeline_builder=TimelineBuilder(),
        voice_provider=None,  # silent — voice engine dormant
        subtitle_generator=SubtitleGenerator(),
        renderer=FFmpegRenderer(),
    )

    rendered = render_service.render(story, assets_by_scene, VIDEO_PATH)

    total_duration = sum(s.duration_seconds for s in story.scenes)
    print(f"Video duration: {total_duration:.1f}s")
    print(f"Output path:    {rendered}")


if __name__ == "__main__":
    main()
