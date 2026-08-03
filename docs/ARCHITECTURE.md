# Cocoa Talk Studio — Technical Architecture

---

## Pipeline Overview

```
Brand Context (Cocoa Talk identity)
 ↓
Brain Engine    →  Structured Story (Spanish)
 ↓
Asset Engine    →  Cinematic Footage (vertical, warm)
 ↓
Video Engine    →  Typography-first MP4 (silent)
 ↓
Publisher       →  Live TikTok Post
```

The Brand Context is not a runtime module. It is the identity embedded in prompts, defaults, and editorial decisions. Every generation begins with the Cocoa Talk identity.

Each stage consumes the output of the previous one. No stage reaches backward or sideways into another stage's internals.

---

## Brand Layer

The Brand Layer is not a software module. It is the editorial foundation that every module serves.

**It lives in:**
- `docs/BRAND.md` — the editorial bible
- `docs/COCO.md` — the mascot reference
- `brands/cocoa-talk/` — brand assets and configuration
- `src/ai_content_studio/brain/prompts/` — identity embedded into every LLM prompt

**Every generation starts here.** The `system_prompt.md` is the Cocoa Talk identity, loaded before any LLM call. The `story_prompt.md` enforces the writing philosophy, the language (Spanish), and the editorial pillar.

If a feature violates the brand identity, it does not get built.

---

## Modules

---

### Core

The technical foundation. Every other module depends on Core; Core depends on nothing.

**Responsibilities:**
- Application configuration and environment loading
- Typed settings with validation
- Structured logging
- Dependency injection
- Shared infrastructure (HTTP client, database session)

**Boundaries:** No business logic. No editorial decisions.

---

### Brain

The creative engine. Transforms a topic or editorial pillar into a complete, structured production plan — entirely in Spanish.

**Responsibilities:**
- Accept a `CreativeBrief` with an `EditorialPillar` and optional `ContentType`
- Generate original Cocoa Talk writing aligned with the brand voice
- Plan scenes with visual direction and on-screen text
- Generate caption and curated hashtags
- Parse and validate LLM output into a `Story` object

**Components:**
- `StoryDirector` — orchestrates the full Brain pipeline
- `PromptBuilder` — constructs LLM prompts from identity + brief
- `AnthropicProvider` — LLM backend (Claude)
- `StoryParser` — parses and validates LLM output into `Story`
- `BrainService` — public interface

**Language:** All generated content is in Spanish by default.

**Editorial pillars:** `SHADOW_WORK`, `POETIC`, `INTRAPERSONAL`, `MENTAL_HEALTH`

**Output:** A validated `Story` object — structured JSON consumed by downstream stages.

**Boundaries:** Generates text and structure only. Never downloads assets, edits video, or publishes.

---

### Asset Engine

The footage resolver. Sources vertical, cinematic footage for every scene.

**Responsibilities:**
- Derive a visual search query from each scene (emotion + narration → search terms)
- Search all configured providers (vertical orientation, Spanish context)
- Merge, deduplicate, and rank results by relevance to the scene
- Return a ranked asset list per scene

**Components:**
- `SearchQueryBuilder` — visual search query from a Scene; biased toward warm, cinematic aesthetics
- `AssetProvider` — abstract interface
- `PexelsProvider` — primary provider
- `PixabayProvider` — secondary provider (vertical, Spanish)
- `FreepikProvider` — optional (requires API key)
- `AssetRanker` — scores by orientation (portrait preferred), type, resolution, duration, emotion
- `AssetService` — orchestrates, merges, deduplicates, ranks

**Output:** Ranked `Asset` list per `Scene`.

**Boundaries:** Selects and retrieves media only. Never edits video or publishes.

---

### Video Engine

The production suite. Assembles footage and typography into a finished silent video.

**Architecture note — Typography-first:**
There is no voice-over in the default pipeline. The written narration appears as animated subtitles over cinematic footage. Typography is the primary storytelling element.

Voice synthesis (`VoiceProvider`) is **dormant** — present in the codebase but not called by default. `voice_provider` is optional in `RenderService`. When it is `None`, the pipeline produces a silent video. This is the current production mode.

Voice will be re-enabled when a premium provider (e.g. ElevenLabs) is integrated.

**Responsibilities:**
- Build a scene timeline from the production plan
- Generate animated subtitle cues from scene narration
- Composite vertical footage clips via FFmpeg
- Render and export a silent TikTok-compatible MP4 (9:16)

**Components:**
- `Timeline` — domain model for the timed clip sequence
- `TimelineBuilder` — constructs `Timeline` from `Story` + assets
- `SubtitleGenerator` — derives timed subtitle cues from narration; primary storytelling layer
- `VoiceProvider` / `KokoroProvider` — dormant; interface preserved for future ElevenLabs integration
- `FFmpegRenderer` — video assembly and export
- `RenderService` — orchestrates Timeline → subtitles → render

**Input:** `Story` + resolved asset manifest.
**Output:** Silent `.mp4` ready for upload. Music is selected inside TikTok.

**Boundaries:** Renders only. Never generates content or publishes.

---

### Publisher

The delivery layer. Uploads the finished video to TikTok.

**Responsibilities:**
- OAuth token exchange and refresh (TikTok)
- Upload the rendered video file via TikTok Content Posting API
- Set caption and hashtags
- Poll publication status until confirmed live or failed
- Store publication record

**Components:**
- `TikTokOAuth` — token exchange and refresh
- `TikTokPublisher` — video upload and status polling
- `PublicationService` — orchestrates OAuth → upload → polling
- `Publisher` (ABC) — abstract interface
- `OAuthProvider` (ABC) — abstract OAuth contract

**Boundaries:** Uploads and confirms. Never generates content or edits video.

---

### Scheduler

The automation controller. Manages the weekly production cadence.

**Responsibilities:**
- Trigger pipeline runs on schedule (2× video per week, 1× carousel per week)
- Retry failed stages with backoff
- Escalate unrecoverable failures
- Log job history

**Boundaries:** Coordinates timing and recovery. No content or media logic.

---

### Storage

The persistence layer.

**Responsibilities:**
- Local asset library (downloaded footage)
- Asset and render cache
- Project records (ideas, scripts, production plans)
- Published post metadata

**Boundaries:** Persists and retrieves. No business logic.

---

### Shared

The common vocabulary. Types, contracts, and utilities used across modules.

**Responsibilities:**
- Domain models: `Story`, `Scene`, `Asset`, `Emotion`, `CreativeBrief`, `Publication`, `Timeline`
- Enums: `Emotion`, `PublicationStatus`, `EditorialPillar`, `ContentType`
- Abstract interfaces decoupling modules from concrete implementations
- Pure utility functions

**Boundaries:** No module-specific logic. No side effects.

---

## Architectural Principles

- **Brand first.** Every feature serves the Cocoa Talk editorial identity.
- **Single Responsibility.** Each module owns one concern.
- **Loose Coupling.** Modules communicate through well-defined data contracts.
- **High Cohesion.** Unrelated logic belongs in the appropriate module or Shared.
- **Modular Design.** Any module can be replaced independently, provided its contract is preserved.
- **Small Public Interfaces.** Implementation details stay private.
- **Testability.** Dependencies are injected, not hardcoded.
- **Automation First.** The default path requires no human input.
- **Simplicity.** No abstraction is introduced without a concrete need.

---

## Content Type Architecture

The pipeline supports two output types:

### Video (current)

```
CreativeBrief(pillar, content_type=VIDEO)
 ↓ Brain
Story (Spanish narration + scenes)
 ↓ Asset Engine
Assets (vertical footage)
 ↓ Video Engine
Silent MP4 (typography over footage)
 ↓ Publisher
TikTok post
```

### Carousel (planned — Sprint 6)

```
CreativeBrief(pillar, content_type=CAROUSEL)
 ↓ Brain (CarouselGenerator)
Carousel (slides with question + brand identity)
 ↓ CarouselRenderer
Image set (2 slides)
 ↓ Publisher
TikTok carousel post
```
