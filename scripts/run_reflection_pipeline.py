#!/usr/bin/env python3
"""Default Cocoa Talk TikTok pipeline — generates a short editorial reflection video.

One thought. One visual. One feeling. 10–15 seconds.
"""

import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ai_content_studio.assets.concept_extractor import SceneConceptExtractor
from ai_content_studio.assets.providers.pexels import PexelsProvider
from ai_content_studio.assets.query_builder import SearchQueryBuilder
from ai_content_studio.assets.ranking import AssetRanker
from ai_content_studio.assets.service import AssetService
from ai_content_studio.brain.prompt_builder import PromptBuilder
from ai_content_studio.brain.providers.anthropic import AnthropicProvider
from ai_content_studio.brain.reflection_director import ReflectionDirector
from ai_content_studio.brain.reflection_parser import ReflectionParser
from ai_content_studio.brands.brand_context import BrandContext
from ai_content_studio.shared.models.editorial import EditorialPillar
from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.video.reflection_renderer import ReflectionRenderer

OUTPUT_DIR = Path(__file__).parents[1] / "output"
ASSETS_DIR = OUTPUT_DIR / "assets"
REFLECTION_PATH = OUTPUT_DIR / "reflection.json"
VIDEO_PATH = OUTPUT_DIR / "reflection.mp4"

_IDEA = "La primera vez que callaste algo que querías decir"
_PILLAR = EditorialPillar.SHADOW_WORK
_EMOTION = Emotion.GRIEF
_LANGUAGE = "es"


def _ext(url: str) -> str:
    tail = url.rsplit(".", 1)[-1].split("?")[0]
    return tail if tail in {"mp4", "jpg", "jpeg", "png", "webm"} else "mp4"


def _download(url: str, dest: Path) -> None:
    resp = httpx.get(url, follow_redirects=True, timeout=30.0)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)

    # ── Brief ─────────────────────────────────────────────────────────────────
    director = ReflectionDirector()
    brief = director.direct(idea=_IDEA, pillar=_PILLAR, emotion=_EMOTION, language=_LANGUAGE)

    print(f"Idea:         {brief.idea}")
    print(f"Pillar:       {brief.pillar.value}")
    print(f"Emotion:      {brief.primary_emotion.value}")
    print(f"Language:     {brief.language}\n")

    # ── Brain ─────────────────────────────────────────────────────────────────
    brand_context = BrandContext.load()
    prompt_builder = PromptBuilder(brand_context=brand_context)
    prompt = prompt_builder.build_reflection_prompt(brief)

    print("Generating reflection via Anthropic …")
    raw = AnthropicProvider().generate(prompt)
    reflection = ReflectionParser().parse(raw, pillar=_PILLAR, language=_LANGUAGE)

    print(f'Reflection:   "{reflection.reflection_text}"')
    print(f"Title:        {reflection.title}")
    REFLECTION_PATH.write_text(reflection.model_dump_json(indent=2), encoding="utf-8")
    print(f"Saved:        {REFLECTION_PATH}\n")

    # ── Asset ─────────────────────────────────────────────────────────────────
    extractor = SceneConceptExtractor()
    query_builder = SearchQueryBuilder()
    asset_service = AssetService(
        query_builder=query_builder,
        concept_extractor=extractor,
        providers=[PexelsProvider()],
        ranker=AssetRanker(),
    )

    concept = extractor.extract_from_prompt(reflection.visual_prompt, _EMOTION)
    query = query_builder.build(concept)
    print(f"Asset query:  {query!r}")

    from ai_content_studio.shared.models import Scene
    proxy = Scene(
        order=1,
        narration="",
        visual_prompt=reflection.visual_prompt,
        emotion=_EMOTION,
        duration_seconds=brief.target_duration_seconds,
    )
    assets = asset_service.find_assets(proxy, limit=8)

    if not assets:
        print("No assets found — cannot render.")
        sys.exit(1)

    best = assets[0]
    ext = _ext(best.url)
    asset_dest = ASSETS_DIR / f"reflection.{ext}"

    print(f"Selected:     {best.source}/{best.provider_id} ({best.asset_type})")
    _download(best.url, asset_dest)
    print(f"Downloaded:   {asset_dest}\n")

    # ── Render ────────────────────────────────────────────────────────────────
    print("Rendering reflection video …")
    renderer = ReflectionRenderer()
    rendered = renderer.render(
        asset_path=asset_dest,
        reflection_text=reflection.reflection_text,
        output_path=VIDEO_PATH,
        duration=float(brief.target_duration_seconds),
        asset_type=best.asset_type,
    )

    print(f"Duration:     {brief.target_duration_seconds}s")
    print(f"Output:       {rendered}")


if __name__ == "__main__":
    main()
