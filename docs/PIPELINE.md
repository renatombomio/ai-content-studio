# Cocoa Talk Studio — Execution Pipeline

---

## Overview

```
Brand Context
 ↓
Idea / Editorial Pillar
 ↓
Brain Engine
 ↓
Story (Spanish)
 ↓
Asset Engine
 ↓
Timeline Builder
 ↓
Subtitle Generator
 ↓
FFmpeg Renderer (silent)
 ↓
TikTok Publisher
(music selected inside TikTok)
```

The pipeline produces a **silent vertical video**. Typography is the primary storytelling element. Music is added by the creator inside TikTok after upload.

---

## Output Types

The pipeline supports two distinct output formats:

| Type | Trigger | Output |
|---|---|---|
| **Video** | `ContentType.VIDEO` | Silent 9:16 MP4 with animated subtitles |
| **Carousel** | `ContentType.CAROUSEL` | Two-slide image set |

Both begin with a `CreativeBrief` and the Brain Engine. They diverge after story generation.

---

## Implementation Status

| Stage | Module | Status |
|-------|--------|--------|
| Brand Context | `brain/prompts/` | ✅ Sprint 2 |
| Brain | Brain — PromptBuilder, AnthropicProvider, StoryParser | ✅ Sprint 2 |
| Asset Engine | assets — SearchQueryBuilder, providers, AssetRanker | ✅ Sprint 3 |
| Video Engine | video — Timeline, SubtitleGenerator, FFmpegRenderer | ✅ Sprint 4 |
| Voice Engine | video/voice — KokoroProvider | ✅ Completed / Dormant |
| Publisher | publisher — TikTokOAuth, TikTokPublisher, PublicationService | ✅ Sprint 5 |
| Carousel Engine | video/carousel — CarouselGenerator, CarouselRenderer | ⬜ Sprint 6 |
| Scheduler | scheduler | ⬜ Phase 8 |

---

## Pipeline A — Vertical Video

---

### Stage 1: Brand Context

**Purpose:** Establish the Cocoa Talk identity before any generation begins.

**How:** The `system_prompt.md` is loaded and passed as the system message to every LLM call. It encodes the brand voice, writing philosophy, and visual thinking principles.

This stage is not a runtime call. It is a design constraint embedded in the Brain module.

---

### Stage 2: Brief

**Purpose:** Define what the video is about.

**Input:** A topic or idea. An `EditorialPillar` (`SHADOW_WORK`, `POETIC`, `INTRAPERSONAL`, `MENTAL_HEALTH`).

**Output:** `CreativeBrief` — structured object with idea, primary emotion, theme, pillar, and target duration.

**Responsible Module:** Brain (intake) / Scheduler (trigger)

---

### Stage 3: Brain Engine

**Purpose:** Transform the brief into a complete, structured production plan in Spanish.

**Input:** `CreativeBrief`

**Output:** `Story` containing:
- `title` — Spanish video title
- `hook` — opening line (specific, close, earns the next ten seconds)
- `scenes` — ordered list, each with `narration`, `visual_prompt`, `emotion`, `duration_seconds`
- `caption` — TikTok post caption in Spanish
- `hashtags` — curated set (3–7, relevant, never generic)

**Language:** Always Spanish. The LLM is instructed to think and write in Spanish from the first word.

**Responsible Module:** Brain

**Failure Handling:** Invalid LLM output triggers a retry (up to configured limit). The pipeline never proceeds with a partially valid story.

---

### Stage 4: Asset Engine

**Purpose:** Resolve cinematic vertical footage for every scene.

**Input:** `Story` (list of `Scene` objects)

**Output:** Ranked `Asset` list per `Scene`.

**Internal flow:**
```
Scene
 ↓
SearchQueryBuilder (emotion + narration → visual query, warm/cinematic bias)
 ↓
PexelsProvider (primary)
PixabayProvider (vertical, Spanish, secondary)
FreepikProvider (optional)
 ↓
AssetRanker (portrait preferred, video preferred, duration match)
 ↓
Assets
```

**Responsible Module:** Asset Engine

**Failure Handling:** If one provider fails, the engine continues with the remaining. If all fail for a scene, `AssetError` is raised and the pipeline stops.

---

### Stage 5: Timeline Builder

**Purpose:** Map scenes, assets, and narration to a time-coded sequence.

**Input:** `Story` + resolved assets per scene.

**Output:** `Timeline` — ordered, timed clips.

**Responsible Module:** Video Engine

---

### Stage 6: Subtitle Generator

**Purpose:** Derive animated subtitle cues from scene narration.

This is the **primary storytelling layer** of the video. There is no voice-over. The written narration appears on screen as animated typography over the footage.

**Input:** `Timeline`

**Output:** List of `SubtitleCue` objects — timed text segments.

**Responsible Module:** Video Engine

---

### Stage 7: Voice Engine (Dormant)

Voice synthesis is **disabled in the current production pipeline**.

`VoiceProvider` and `KokoroProvider` remain in the codebase. `voice_track` on `Timeline` is optional. `RenderService` accepts `voice_provider: VoiceProvider | None = None`.

When `voice_provider` is `None`, the renderer produces a silent video.

Voice will be re-enabled when a premium provider (e.g. ElevenLabs) is integrated and the brand determines voice quality meets its standard.

---

### Stage 8: FFmpeg Renderer

**Purpose:** Composite footage, animated subtitles, and produce the final silent MP4.

**Input:** `Timeline` (with subtitle cues, without voice track).

**Output:** Silent 9:16 MP4, TikTok-compatible.

**Responsible Module:** Video Engine (FFmpegRenderer)

**Failure Handling:** Rendering errors stop the pipeline. The failed file is discarded.

---

### Stage 9: TikTok Publisher

**Purpose:** Upload the video and confirm the post is live.

**Input:** Rendered MP4 + caption + hashtags.

**Output:** Published TikTok post URL.

**Responsibilities:**
- OAuth token exchange / refresh
- Upload via TikTok Content Posting API (Direct Post)
- Poll status until `PUBLISH_COMPLETE` or `FAILED`
- Store publication record

**Post-upload:** Music is selected by the creator inside TikTok. The pipeline does not produce or select music.

**Responsible Module:** Publisher

---

## Pipeline B — Carousel (Planned, Sprint 6)

```
CreativeBrief(content_type=CAROUSEL)
 ↓
CarouselGenerator (Brain)
 ↓
Carousel (2 slides)
 ↓
CarouselRenderer
 ↓
Image files (slide_01.png, slide_02.png)
 ↓
TikTok Publisher (carousel upload)
```

**Slide 1:** Brand identity card — Coco mascot, "Cocoa Question of the Week" typography.
**Slide 2:** One reflective question — minimal, large typography, no distractions.

Published once per week.

---

## Pipeline Principles

- Every stage has one responsibility.
- Every stage has a clearly defined input and output.
- Data always flows forward.
- No module may skip another module.
- Modules communicate only through structured objects.
- Every stage must be independently testable.
- Failures must stop the pipeline gracefully.
- The brand identity is embedded at Stage 1 and never overridden.
