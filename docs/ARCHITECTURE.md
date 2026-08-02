# Cocoa Talk Studio — Technical Architecture

---

## Pipeline Overview

```
Idea
 ↓
Brain          →  Structured Story
 ↓
Asset Engine   →  Resolved Assets
 ↓
Video Engine   →  TikTok-ready MP4
 ↓
Publisher      →  Live TikTok Post
```

Each stage consumes the output of the previous one. No stage reaches backward or sideways into another stage's internals.

---

## Modules

---

### Core

The technical foundation. Every other module depends on Core; Core depends on nothing.

**Responsibilities:**
- Application configuration and environment loading
- Typed settings with validation
- Structured logging
- Dependency injection container
- Shared infrastructure services (HTTP client, database session, etc.)

**Boundaries:** Core contains no business logic. It provides capabilities; it makes no decisions about content, assets, or publishing.

---

### Brain

The creative engine. The Brain transforms a topic or idea into a complete, structured production plan.

**Responsibilities:**
- Generate ranked video ideas aligned with the Cocoa Talk brand
- Write a narrated script for a selected idea
- Plan scenes: visual direction, timing, and on-screen text
- Generate captions per scene
- Generate a curated TikTok hashtag set

**Output:** A single Structured Story object — a validated, machine-readable production plan consumed by downstream stages.

**Boundaries:** The Brain generates text and structure only. It never downloads assets, edits video, or publishes content.

---

### Asset Engine

The resource resolver. The Asset Engine takes a Structured Story and finds the best visual and audio assets for every scene.

**Responsibilities:**
- Search the local asset library first
- Search external sources in priority order: Freepik → Mixkit → Pexels → Pixabay
- Fall back to AI generation only when no suitable asset is found elsewhere
- Download and cache resolved assets
- Attach an asset manifest to the production plan

**Output:** The Structured Story enriched with resolved, downloaded assets for every scene.

**Boundaries:** The Asset Engine selects and retrieves media. It never edits video or publishes content.

---

### Video Engine

The production suite. The Video Engine assembles assets and story structure into a finished video.

**Responsibilities:**
- Build a scene timeline from the production plan
- Composite video clips, images, and overlays via FFmpeg
- Burn in subtitles and captions with brand typography
- Layer background music
- Apply scene transitions consistent with brand style
- Render and export a TikTok-compatible MP4 (9:16 aspect ratio)

**Input:** Structured Story + resolved asset manifest.

**Output:** A single rendered `.mp4` file ready for upload.

**Boundaries:** The Video Engine renders only. It never generates content or publishes.

---

### Publisher

The delivery layer. The Publisher handles the final step: getting the rendered video onto TikTok.

**Responsibilities:**
- Maintain a persistent, authenticated browser session via Playwright
- Upload the rendered video file
- Set caption and hashtags
- Select or set the publish time (immediate or scheduled)
- Confirm the post is live and capture the published URL

**Boundaries:** The Publisher uploads and confirms. It never generates content, selects assets, or edits video.

---

### Scheduler

The automation controller. The Scheduler owns the weekly production cadence and job lifecycle.

**Responsibilities:**
- Determine when to trigger a new production run (twice per week)
- Invoke the pipeline in sequence
- Retry failed stages with backoff
- Escalate unrecoverable failures via notification
- Log job history and outcomes

**Boundaries:** The Scheduler coordinates timing and recovery. It contains no content or media logic.

---

### Storage

The persistence layer. Storage provides a consistent interface to all durable data.

**Responsibilities:**
- Local asset library (downloaded media files)
- Asset and render cache
- Project records (ideas, scripts, production plans)
- Published post metadata
- General key-value and binary storage

**Boundaries:** Storage contains no business logic. It persists and retrieves; it makes no decisions.

---

### Shared

The common vocabulary. Shared provides types, contracts, and utilities used across modules.

**Responsibilities:**
- Domain types and data models (e.g., `StructuredStory`, `Scene`, `Asset`)
- Interfaces and protocols that decouple modules from concrete implementations
- Project-wide constants
- Pure utility functions with no side effects

**Boundaries:** Shared contains no module-specific logic and no side effects. No module other than Shared defines cross-cutting types.

---

## Architectural Principles

- **Single Responsibility.** Each module owns one concern. A module that generates content does not touch the filesystem. A module that edits video does not call external APIs.

- **Loose Coupling.** Modules communicate through well-defined data contracts (e.g., `StructuredStory`). No module imports the internals of another.

- **High Cohesion.** Everything inside a module belongs there. Unrelated logic is moved to the appropriate module or to Shared.

- **Modular Design.** Any module can be replaced or upgraded independently without affecting the others, provided its interface contract is preserved.

- **Small Public Interfaces.** Each module exposes the minimum surface needed by its consumers. Implementation details remain private.

- **Testability.** Modules are designed to be tested in isolation. Dependencies are injected, not hardcoded.

- **Automation First.** The default execution path requires no human input. Human checkpoints are explicit, optional, and narrow in scope.

- **Simplicity.** No abstraction is introduced without a concrete need. The system is extended only when the product requires it.
