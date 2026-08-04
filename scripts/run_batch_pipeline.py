#!/usr/bin/env python3
"""Cocoa Talk batch editorial production pipeline.

Usage:
    uv run python scripts/run_batch_pipeline.py --count 30

Generated batches are immutable. Each run creates a new numbered batch directory.
Existing batches are never overwritten.
"""

import argparse
import json
import random
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from ai_content_studio.assets.concept_extractor import SceneConceptExtractor
from ai_content_studio.assets.providers.pexels import PexelsProvider
from ai_content_studio.assets.query_builder import SearchQueryBuilder
from ai_content_studio.assets.ranking import AssetRanker
from ai_content_studio.assets.service import AssetService
from ai_content_studio.brain import BRAIN_VERSION
from ai_content_studio.brain.prompt_builder import PromptBuilder
from ai_content_studio.brain.providers.anthropic import AnthropicProvider
from ai_content_studio.brain.question_parser import QuestionParser
from ai_content_studio.brain.reflection_director import ReflectionDirector
from ai_content_studio.brain.reflection_parser import ReflectionParser
from ai_content_studio.brands.brand_context import BrandContext
from ai_content_studio.shared.models import Scene
from ai_content_studio.shared.models.editorial import EditorialPillar
from ai_content_studio.shared.models.emotion import Emotion
from ai_content_studio.video.reflection_renderer import RENDERER_VERSION, ReflectionRenderer

_OUTPUT_ROOT = Path(__file__).parents[1] / "output" / "batch"

_REFLECTION_DISTRIBUTION = [
    (EditorialPillar.SHADOW_WORK, 0.35),
    (EditorialPillar.INTRAPERSONAL, 0.25),
    (EditorialPillar.MENTAL_HEALTH, 0.25),
    (EditorialPillar.POETIC_WRITING, 0.15),
]

_QUESTION_PILLARS = [
    EditorialPillar.SHADOW_WORK,
    EditorialPillar.SHADOW_WORK,
    EditorialPillar.SHADOW_WORK,
    EditorialPillar.INTRAPERSONAL,
    EditorialPillar.INTRAPERSONAL,
    EditorialPillar.MENTAL_HEALTH,
    EditorialPillar.MENTAL_HEALTH,
    EditorialPillar.POETIC_WRITING,
]

_IDEAS: dict[EditorialPillar, list[tuple[str, Emotion]]] = {
    EditorialPillar.SHADOW_WORK: [
        ("Lo que dejaste de pedir", Emotion.VULNERABILITY),
        ("La primera vez que callaste algo que querías decir", Emotion.GRIEF),
        ("Lo que te enseñaron a esconder", Emotion.REGRET),
        ("El enojo que convertiste en silencio", Emotion.INNER_CONFLICT),
        ("Las cosas que hiciste para ser amado", Emotion.VULNERABILITY),
        ("El día que aprendiste a no necesitar", Emotion.GRIEF),
        ("Lo que normalizaste sin darte cuenta", Emotion.REGRET),
        ("La versión de ti que nadie conoció", Emotion.LONELINESS),
        ("Lo que cargaste para que otros no tuvieran que hacerlo", Emotion.GRIEF),
        ("El límite que nunca pusiste", Emotion.INNER_CONFLICT),
        ("Lo que sacrificaste para encajar", Emotion.REGRET),
        ("El miedo que disfrazaste de indiferencia", Emotion.VULNERABILITY),
    ],
    EditorialPillar.INTRAPERSONAL: [
        ("Quien fuiste antes de aprender a adaptarte", Emotion.NOSTALGIA),
        ("La persona que eras antes de las expectativas", Emotion.SELF_DISCOVERY),
        ("Lo que perdiste cuando dejaste de escucharte", Emotion.REGRET),
        ("El momento en que empezaste a dudar de ti", Emotion.INNER_CONFLICT),
        ("La voz que aprendiste a ignorar", Emotion.SELF_DISCOVERY),
        ("Quién eres cuando nadie te observa", Emotion.SELF_DISCOVERY),
        ("Lo que defines como tuyo y lo que copiaste", Emotion.INNER_CONFLICT),
        ("La diferencia entre quien eres y quien crees ser", Emotion.SELF_DISCOVERY),
        ("Lo que necesitas y lo que dices que necesitas", Emotion.VULNERABILITY),
        ("El diálogo interno que nunca te ayudó", Emotion.INNER_CONFLICT),
    ],
    EditorialPillar.MENTAL_HEALTH: [
        ("El cuerpo que guarda lo que la mente olvida", Emotion.GRIEF),
        ("Los días en que nada está mal y todo duele", Emotion.MELANCHOLY),
        ("El agotamiento que no tiene nombre", Emotion.GRIEF),
        ("Lo que llamas fortaleza y lo que realmente es", Emotion.VULNERABILITY),
        ("La diferencia entre estar bien y parecer bien", Emotion.INNER_CONFLICT),
        ("El descanso que nunca tomaste", Emotion.ACCEPTANCE),
        ("La ansiedad que convertiste en productividad", Emotion.INNER_CONFLICT),
        ("Sanar sin saber de qué exactamente", Emotion.ACCEPTANCE),
        ("El peso invisible que cargas cada mañana", Emotion.GRIEF),
        ("Lo que significa pedir ayuda cuando no sabes qué pedir", Emotion.VULNERABILITY),
    ],
    EditorialPillar.POETIC_WRITING: [
        ("La soledad que elegiste sin saber", Emotion.LONELINESS),
        ("Los inviernos que ocurren adentro", Emotion.MELANCHOLY),
        ("Lo que el tiempo no borró", Emotion.NOSTALGIA),
        ("El silencio que tiene forma", Emotion.LONELINESS),
        ("Las memorias que inventó el olvido", Emotion.NOSTALGIA),
        ("Lo que queda cuando ya no queda nada", Emotion.MELANCHOLY),
        ("El espacio entre lo que sientes y lo que dices", Emotion.LONGING),
    ],
}


@dataclass
class _Services:
    director: ReflectionDirector
    prompt_builder: PromptBuilder
    provider: AnthropicProvider
    reflection_parser: ReflectionParser
    question_parser: QuestionParser
    asset_service: AssetService
    extractor: SceneConceptExtractor
    query_builder: SearchQueryBuilder
    renderer: ReflectionRenderer


def _next_batch_number() -> int:
    if not _OUTPUT_ROOT.exists():
        return 1
    existing = sorted(
        int(p.name) for p in _OUTPUT_ROOT.iterdir()
        if p.is_dir() and p.name.isdigit()
    )
    return (existing[-1] + 1) if existing else 1


def _plan_reflections(count: int) -> list[tuple[EditorialPillar, str, Emotion]]:
    pillar_counts: dict[EditorialPillar, int] = {}
    for pillar, ratio in _REFLECTION_DISTRIBUTION:
        pillar_counts[pillar] = round(count * ratio)

    total = sum(pillar_counts.values())
    diff = count - total
    if diff != 0:
        pillar_counts[EditorialPillar.SHADOW_WORK] += diff

    posts: list[tuple[EditorialPillar, str, Emotion]] = []
    for pillar, n in pillar_counts.items():
        pool = list(_IDEAS[pillar])
        random.shuffle(pool)
        extended = (pool * (n // len(pool) + 1))[:n]
        posts.extend((pillar, idea, emotion) for idea, emotion in extended)

    random.shuffle(posts)
    return posts


def _ext(url: str) -> str:
    tail = url.rsplit(".", 1)[-1].split("?")[0]
    return tail if tail in {"mp4", "jpg", "jpeg", "png", "webm"} else "mp4"


def _download(url: str, dest: Path) -> None:
    resp = httpx.get(url, follow_redirects=True, timeout=60.0)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


def _generate_reflection(
    index: int,
    total: int,
    pillar: EditorialPillar,
    idea: str,
    emotion: Emotion,
    post_dir: Path,
    svc: _Services,
) -> bool:
    print(f"  [post_{index:03d}] {pillar.value} — {idea}")

    brief = svc.director.direct(idea=idea, pillar=pillar, emotion=emotion)
    prompt = svc.prompt_builder.build_reflection_prompt(brief)
    raw = svc.provider.generate(prompt)
    reflection = svc.reflection_parser.parse(raw, pillar=pillar)

    preview = reflection.reflection_text
    if len(preview) > 80:
        preview = preview[:77] + "..."
    print(f"            \"{preview}\"")

    concept = svc.extractor.extract_from_prompt(reflection.visual_prompt, emotion)
    proxy = Scene(
        order=1,
        narration="",
        visual_prompt=reflection.visual_prompt,
        emotion=emotion,
        duration_seconds=brief.target_duration_seconds,
    )
    assets = svc.asset_service.find_assets(proxy, limit=8)
    if not assets:
        print("            No assets found — skipping.")
        return False

    best = assets[0]
    ext = _ext(best.url)
    asset_path = post_dir / f"_asset.{ext}"
    _download(best.url, asset_path)

    svc.renderer.render(
        asset_path=asset_path,
        reflection_text=reflection.reflection_text,
        output_path=post_dir / "reflection.mp4",
        duration=float(brief.target_duration_seconds),
        asset_type=best.asset_type,
    )
    asset_path.unlink(missing_ok=True)

    (post_dir / "caption.txt").write_text(reflection.caption, encoding="utf-8")
    (post_dir / "hashtags.txt").write_text("\n".join(reflection.hashtags), encoding="utf-8")
    (post_dir / "metadata.json").write_text(
        json.dumps({
            "pillar": pillar.value,
            "title": reflection.title,
            "reflection": reflection.reflection_text,
            "visual_prompt": reflection.visual_prompt,
            "generation_date": date.today().isoformat(),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return True


def _generate_question(
    index: int,
    pillar: EditorialPillar,
    question_dir: Path,
    svc: _Services,
) -> bool:
    print(f"  [question_{index:03d}] {pillar.value}")

    prompt = svc.prompt_builder.build_question_prompt(pillar)
    raw = svc.provider.generate(prompt)
    question = svc.question_parser.parse(raw, pillar=pillar)

    print(f"            \"{question.question_text}\"")

    (question_dir / "question.json").write_text(
        json.dumps({
            "pillar": pillar.value,
            "question_text": question.question_text,
            "context": question.context,
            "caption": question.caption,
            "hashtags": question.hashtags,
            "generation_date": date.today().isoformat(),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return True


def _write_manifest(
    batch_dir: Path,
    batch_number: int,
    reflections: int,
    questions: int,
    status: str = "active",
    deprecation_reason: str | None = None,
) -> None:
    total = reflections + questions
    manifest = {
        "batch": batch_number,
        "brain_version": BRAIN_VERSION,
        "renderer_version": RENDERER_VERSION,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "status": status,
        "remaining": total,
        "reflections": reflections,
        "questions": questions,
        "deprecation_reason": deprecation_reason,
    }
    (batch_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    arg_parser = argparse.ArgumentParser(description="Cocoa Talk batch editorial pipeline.")
    arg_parser.add_argument("--count", type=int, required=True, help="Number of reflections to generate.")
    args = arg_parser.parse_args()
    reflection_count: int = args.count
    question_count = len(_QUESTION_PILLARS)

    batch_number = _next_batch_number()
    batch_dir = _OUTPUT_ROOT / f"{batch_number:03d}"
    batch_dir.mkdir(parents=True, exist_ok=True)

    brand_context = BrandContext.load()
    extractor = SceneConceptExtractor()
    query_builder = SearchQueryBuilder()
    svc = _Services(
        director=ReflectionDirector(),
        prompt_builder=PromptBuilder(brand_context=brand_context),
        provider=AnthropicProvider(),
        reflection_parser=ReflectionParser(),
        question_parser=QuestionParser(),
        asset_service=AssetService(
            query_builder=query_builder,
            concept_extractor=extractor,
            providers=[PexelsProvider()],
            ranker=AssetRanker(),
        ),
        extractor=extractor,
        query_builder=query_builder,
        renderer=ReflectionRenderer(),
    )

    print(f"Cocoa Talk — Batch {batch_number:03d}")
    print(f"Brain: {BRAIN_VERSION}  Renderer: {RENDERER_VERSION}")
    print(f"Reflections: {reflection_count}  Questions: {question_count}")
    print(f"Output: {batch_dir}\n")

    plan = _plan_reflections(reflection_count)

    reflection_ok = 0
    reflection_fail = 0
    question_ok = 0
    question_fail = 0

    print("── Reflections ─────────────────────────────────────────────")
    for i, (pillar, idea, emotion) in enumerate(plan, 1):
        post_dir = batch_dir / f"post_{i:03d}"
        post_dir.mkdir(parents=True, exist_ok=True)
        try:
            ok = _generate_reflection(i, reflection_count, pillar, idea, emotion, post_dir, svc)
            reflection_ok += 1 if ok else 0
            reflection_fail += 0 if ok else 1
        except Exception as exc:
            print(f"            ERROR: {exc}")
            reflection_fail += 1

    print("\n── Questions ───────────────────────────────────────────────")
    for i, pillar in enumerate(_QUESTION_PILLARS, 1):
        question_dir = batch_dir / f"question_{i:03d}"
        question_dir.mkdir(parents=True, exist_ok=True)
        try:
            ok = _generate_question(i, pillar, question_dir, svc)
            question_ok += 1 if ok else 0
            question_fail += 0 if ok else 1
        except Exception as exc:
            print(f"            ERROR: {exc}")
            question_fail += 1

    _write_manifest(
        batch_dir,
        batch_number=batch_number,
        reflections=reflection_ok,
        questions=question_ok,
    )

    print(f"\n{'─' * 60}")
    print(f"Batch {batch_number:03d} complete")
    print(f"  Reflections: {reflection_ok}/{reflection_count} succeeded")
    print(f"  Questions:   {question_ok}/{question_count} succeeded")
    print(f"  Output:      {batch_dir}")


if __name__ == "__main__":
    main()
