# Cocoa Talk Studio — Product Roadmap

---

## Vision

The Cocoa Talk Studio is a purpose-built automation system for producing and publishing cinematic short-form videos on TikTok — exclusively for the Cocoa Talk brand.

It is not a generic content platform. Every design decision serves one goal: publish two high-quality TikTok videos per week, autonomously, with minimal human intervention.

---

## Principles

- **TikTok first.** The only supported platform. No feature exists to serve another.
- **Cinematic storytelling.** Every video follows a deliberate narrative structure.
- **Quality over quantity.** Two excellent videos beat ten mediocre ones.
- **Automation first.** The system handles the full pipeline end-to-end by default.
- **Human approval when needed.** Creative checkpoints exist; they are the exception, not the rule.
- **Modular architecture.** Each stage of the pipeline is independently replaceable.
- **Simplicity over unnecessary features.** Nothing is built speculatively.

---

## Sprint Status

| Sprint | Scope | Status |
|--------|-------|--------|
| Sprint 1 | Core infrastructure, Cocoa Talk identity, shared domain models | ✅ Completed |
| Sprint 2 | Brain pipeline — StoryDirector, PromptBuilder, AnthropicProvider, StoryParser, AssetProvider interface | ✅ Completed |
| Sprint 3 | Asset Engine — SearchQueryBuilder, FreepikProvider, PexelsProvider, PixabayProvider, AssetRanker, AssetService | ✅ Completed |
| Sprint 4 | Video Engine — Timeline, Voice, Subtitles, FFmpeg Renderer | 🔄 Active |

---

## Product Phases

---

### Phase 0 — Foundation ✅

**Goal:** Establish a working, production-quality repository baseline.

**Deliverables:**
- Python 3.12 project with `uv`
- FastAPI skeleton with `/health` endpoint
- Ruff, MyPy, pytest configured and passing
- Docker setup
- Module structure: `brain`, `assets`, `editor`, `voice`, `publisher`, `analytics`, `shared`, `brands`
- `brands/cocoa-talk/` placeholder
- `CLAUDE.md`, `README.md`

**Definition of Done:** All checks pass. Repository is committed and pushed.

---

### Phase 1 — Core

**Goal:** Establish the technical foundation every subsequent module depends on.

**Deliverables:**
- Configuration management (environment-based, typed)
- Application settings with validation
- Structured logging
- Database setup and migration baseline
- Dependency injection container

**Definition of Done:** Application starts cleanly, loads config from environment, logs structured output, connects to the database. All tests pass.

---

### Phase 2 — Cocoa Talk Identity

**Goal:** Define the Cocoa Talk brand so the system can produce content that is consistent and recognizable.

**Deliverables:**
- Brand profile (name, tone, audience, mission)
- Writing style guide (vocabulary, sentence structure, forbidden patterns)
- Voice profile (TTS persona, pacing, energy)
- Visual identity (color palette, typography, overlay style)
- Publishing schedule (days, times, cadence)

**Definition of Done:** Brand configuration is fully loaded at runtime and accessible to every module. Identity is documented and version-controlled.

---

### Phase 3 — Brain ✅

**Goal:** Automate ideation, scripting, and scene planning using an LLM.

**Deliverables:**
- Idea generation — produces ranked video concepts aligned with the brand
- Script writing — transforms an idea into a narrated script
- Scene planning — breaks the script into visual scenes with direction notes
- Captions — generates on-screen text per scene
- Hashtag generation — produces a curated TikTok hashtag set per video

**Output format:** All Brain outputs are structured JSON. No free text passed between modules.

**Definition of Done:** Given a topic, the Brain produces a complete, validated JSON production plan ready for the Asset Engine.

---

### Phase 4 — Asset Engine ✅

**Goal:** Source every visual asset required by the production plan.

**Providers (searched in parallel, ranked by score):**
1. Freepik (Magnific API)
2. Pexels
3. Pixabay

**Deliverables:**
- SearchQueryBuilder — derives a visual search query from a Scene
- AssetProvider interface — common contract for all providers
- FreepikProvider — Freepik image and vector search via Magnific API
- PexelsProvider — Pexels photo and video search
- PixabayProvider — Pixabay image and video search
- AssetRanker — scores assets by orientation, type, resolution, duration, and emotion
- AssetService — orchestrates providers, merges results, deduplicates, ranks

**Definition of Done:** Given a Scene, the Asset Engine returns a ranked, deduplicated list of assets from all available providers.

**Sprint 3 Tasks:**

| Task | Description | Status |
|------|-------------|--------|
| S3-001 | Search Query Builder | ✅ Completed |
| S3-002 | API Research & Provider Contract | ✅ Completed |
| S3-003 | Asset Domain Model Revision | ✅ Completed |
| S3-004 | FreepikProvider | ✅ Completed |
| S3-005 | PexelsProvider | ✅ Completed |
| S3-006 | AssetRanker | ✅ Completed |
| S3-007 | AssetService | ✅ Completed |
| S3-008 | PixabayProvider | ✅ Completed |
| S3-009 | End-to-End Asset Pipeline | ✅ Completed |

---

### Phase 5 — Video Engine 🔄 Sprint 4

**Goal:** Assemble all assets into a finished, ready-to-upload TikTok video.

**Deliverables:**
- Timeline builder — maps scenes, assets, and captions to a timeline
- FFmpeg pipeline — handles cuts, overlays, and compositing
- Subtitle renderer — burns in captions with brand typography
- Music layer — selects and mixes background audio
- Transitions — scene-to-scene transitions consistent with brand style
- Renderer — exports final video in TikTok-compatible format (9:16, ≤ 10 min)

**Definition of Done:** Given a production plan with resolved assets, the engine renders a single `.mp4` file ready for publishing.

**Sprint 4 Tasks:**

| Task | Description | Status |
|------|-------------|--------|
| S4-001 | Timeline Domain | ⬜ Pending |
| S4-002 | Timeline Builder | ⬜ Pending |
| S4-003 | Voice Engine (TTS) | ⬜ Pending |
| S4-004 | Subtitle Generator | ⬜ Pending |
| S4-005 | FFmpeg Renderer | ⬜ Pending |
| S4-006 | Render Service | ⬜ Pending |
| S4-007 | End-to-End Render Pipeline | ⬜ Pending |

---

### Phase 6 — Publisher

**Goal:** Upload the finished video to TikTok automatically.

**Deliverables:**
- TikTok Publisher
- Instagram Publisher
- Upload Service
- Publication Pipeline

**Definition of Done:** The Publisher uploads a video to TikTok unattended, confirms the post is live, and stores the published URL.

---

### Phase 7 — Automation

**Goal:** The Studio operates weekly without manual triggering.

**Deliverables:**
- Scheduler
- Content Calendar
- Retry System
- Monitoring
- Analytics

**Definition of Done:** The Studio autonomously publishes two high-quality TikTok videos every week. Failures are recovered or escalated without human initiation.

---

## Future Ideas

- Analytics dashboard tracking views, retention, and follower growth per video
- A/B testing for thumbnails and captions
- Audience feedback loop feeding into idea generation
- Support for TikTok Series or multi-part narratives
- Voice cloning for a consistent Cocoa Talk narrator persona
