# Cocoa Talk Studio — Execution Pipeline

---

## Overview

```
Idea
 ↓
Brain Engine
 ↓
Story
 ↓
Asset Engine
 ↓
Timeline Builder
 ↓
Timeline
 ↓
Voice Engine
 ↓
Rendered Video
 ↓
TikTok Publisher
```

---

## Implementation Status

| Stage | Module | Status |
|-------|--------|--------|
| Idea / Brief | Brain — StoryDirector | ✅ Sprint 2 |
| Brain | Brain — PromptBuilder, AnthropicProvider, StoryParser | ✅ Sprint 2 |
| Asset Engine | assets — SearchQueryBuilder, providers, AssetRanker, AssetService | ✅ Sprint 3 |
| Video Engine | video — Timeline, VoiceEngine, Renderer | 🔄 Sprint 4 |
| Publisher | publisher | ⬜ Planned |
| Scheduler | scheduler | ⬜ Planned |

---

## Stages

---

### 1. Idea

**Purpose:** Start the creative process by defining what the video is about.

**Input:** A topic, prompt, or signal from the Scheduler.

**Output:** Creative Brief — a minimal structured object describing the video concept, target audience, and tone.

**Responsible Module:** Brain (intake) / Scheduler (trigger)

**Failure Handling:** If no valid idea can be formed, the pipeline does not start. The Scheduler logs the failure and retries on the next scheduled run.

---

### 2. Brain Engine

**Purpose:** Transform the Creative Brief into a complete, machine-readable production plan.

**Input:** Creative Brief

**Output:** Structured Story containing:
- `title` — video title
- `hook` — opening line designed to retain viewers
- `scenes` — ordered list of scenes, each with narration, visual direction, and caption text
- `caption` — full TikTok post caption
- `hashtags` — curated hashtag set

**Responsible Module:** Brain

**Failure Handling:** If the LLM returns an invalid or incomplete response, the Brain retries up to a configured limit. Persistent failure stops the pipeline and notifies the operator. The Brain never proceeds with a partially valid story.

---

### 3. Asset Engine

**Purpose:** Resolve the best visual asset for every scene in the Structured Story.

**Input:** Structured Story (list of Scenes)

**Output:** Ranked, deduplicated list of Assets per Scene.

**Internal flow:**

```
Scene
 ↓
SearchQueryBuilder
 ↓
Freepik
Pexels
Pixabay
 ↓
AssetRanker
 ↓
Assets
```

**Responsible Module:** Asset Engine

**Failure Handling:** If a provider is unavailable, the engine continues with the remaining providers. If all providers fail for a scene, AssetError is raised and the pipeline stops.

---

### 4. Timeline Builder

**Purpose:** Map scenes, assets, narration, and captions to a time-coded timeline.

**Input:** Structured Story + resolved assets per scene.

**Output:** Timeline — an ordered sequence of timed clips ready for rendering.

**Responsible Module:** Video Engine

**Failure Handling:** Invalid or incomplete input stops the builder. No partial timelines are produced.

---

### 5. Voice Engine

**Purpose:** Generate narration audio for each scene using text-to-speech.

**Input:** Scene narration text.

**Output:** Audio file per scene, attached to the timeline.

**Responsible Module:** Video Engine

**Failure Handling:** TTS failures stop the pipeline. The rendered audio is discarded and the error is surfaced.

---

### 6. Rendered Video

**Purpose:** Assemble the timeline, assets, audio, and captions into a finished video.

**Input:** Timeline + audio files + caption text.

**Output:** Rendered MP4 — a single TikTok-compatible video file (9:16 aspect ratio) with subtitles and transitions applied.

**Responsible Module:** Video Engine (FFmpeg Renderer)

**Failure Handling:** Rendering errors stop the pipeline immediately. The failed render is discarded. The Scheduler is notified and may retry the full pipeline or escalate to the operator.

---

### 7. TikTok Publisher

**Purpose:** Upload the rendered video to TikTok and confirm the post is live.

**Input:** Rendered MP4 + caption + hashtags

**Output:** Published TikTok post — confirmation that the video is live, including the post URL.

**Responsibilities:**
- Open and maintain a persistent authenticated browser session
- Upload the video file
- Set caption, hashtags, and publish time
- Confirm the post is publicly visible
- Store the published URL in Storage

**Responsible Module:** Publisher

**Failure Handling:** If the upload fails, the Publisher retries up to a configured limit before surfacing the failure to the Scheduler. The rendered MP4 is preserved so the upload can be retried without re-rendering.

---

## Pipeline Principles

- Every stage has one responsibility.
- Every stage has a clearly defined input.
- Every stage has a clearly defined output.
- Data always flows forward.
- No module may skip another module.
- Modules communicate only through structured objects.
- Every stage must be independently testable.
- Failures must stop the pipeline gracefully.
