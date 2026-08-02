# Cocoa Talk Studio — Execution Pipeline

---

## Overview

```
Idea
 ↓
Brain          →  Structured Story
 ↓
Asset Engine   →  Story + Selected Assets
 ↓
Video Engine   →  Rendered MP4
 ↓
Publisher      →  Published TikTok Post
 ↑
Scheduler      →  Triggers Publisher on schedule
```

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

### 2. Brain

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

**Purpose:** Resolve the best visual and audio asset for every scene in the Structured Story.

**Input:** Structured Story

**Output:** Structured Story with an asset manifest — each scene has at least one resolved, downloaded asset attached.

**Search priority:**
1. Local Library
2. Freepik
3. Mixkit
4. Pexels
5. Pixabay
6. AI Generation — only when no suitable asset is found in any of the above

**Responsible Module:** Asset Engine

**Failure Handling:** If a source is unavailable, the engine falls through to the next source in priority order. If all sources fail for a scene, AI generation is attempted. If AI generation also fails, the pipeline stops and the failure is reported.

---

### 4. Video Engine

**Purpose:** Assemble the Structured Story and its assets into a finished, cinematic vertical video.

**Input:** Structured Story + asset manifest

**Output:** Rendered MP4 — a single TikTok-compatible video file (9:16 aspect ratio) with subtitles, music, and transitions applied.

**Responsibilities:**
- Build the scene timeline
- Composite video clips and images
- Burn in subtitles and captions
- Layer background music
- Apply brand-consistent transitions
- Export the final render

**Responsible Module:** Video Engine

**Failure Handling:** Rendering errors stop the pipeline immediately. The failed render is discarded. The Scheduler is notified and may retry the full pipeline or escalate to the operator.

---

### 5. Publisher

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

### 6. Scheduler

**Purpose:** Determine when the pipeline runs and manage the job lifecycle.

**Input:** Publishing schedule (days, times, cadence)

**Output:** Publishing job — a triggered pipeline execution at the configured time.

**Responsibilities:**
- Trigger a full pipeline run twice per week
- Monitor job progress
- Retry failed jobs with backoff
- Notify the operator on unrecoverable failures
- Record job history and outcomes

**Responsible Module:** Scheduler

**Failure Handling:** Failed jobs are retried automatically. If a job cannot complete after all retries, the Scheduler notifies the operator and skips to the next scheduled run rather than blocking future executions.

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
