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
| Sprint 3 | Asset Engine — search, providers, ranking, service, scene → asset resolution | 🔄 Active |

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

### Phase 4 — Asset Engine 🔄 Sprint 3

**Goal:** Source every visual and audio asset required by the production plan.

**Priority order:**
1. Local library (previously downloaded or curated assets)
2. Freepik
3. Mixkit
4. Pexels
5. Pixabay
6. AI generation — only when no suitable asset exists in the above sources

**Deliverables:**
- Asset resolver: selects the best source per scene
- Downloaders per source with rate-limit and error handling
- Local asset cache
- AI generation fallback (image and short video clip)
- Asset manifest attached to the production plan

**Definition of Done:** Every scene in a production plan has at least one resolved, downloaded asset ready for editing.

**Sprint 3 Tasks:**

| Task | Description | Status |
|------|-------------|--------|
| S3-001 | Search Query Builder | ⬜ Pending |
| S3-002 | Freepik Provider | ⬜ Pending |
| S3-003 | Mixkit Provider | ⬜ Pending |
| S3-004 | Pexels Provider | ⬜ Pending |
| S3-005 | Asset Ranking | ⬜ Pending |
| S3-006 | Asset Service | ⬜ Pending |
| S3-007 | Scene → Assets | ⬜ Pending |
| S3-008 | End-to-End Asset Pipeline | ⬜ Pending |

---

### Phase 5 — Video Engine

**Goal:** Assemble all assets into a finished, ready-to-upload TikTok video.

**Deliverables:**
- Timeline builder — maps scenes, assets, and captions to a timeline
- FFmpeg pipeline — handles cuts, overlays, and compositing
- Subtitle renderer — burns in captions with brand typography
- Music layer — selects and mixes background audio
- Transitions — scene-to-scene transitions consistent with brand style
- Renderer — exports final video in TikTok-compatible format (9:16, ≤ 10 min)

**Definition of Done:** Given a production plan with resolved assets, the engine renders a single `.mp4` file ready for publishing.

---

### Phase 6 — Publisher

**Goal:** Upload the finished video to TikTok automatically.

**Deliverables:**
- Playwright-based browser automation
- Persistent authenticated browser session
- TikTok upload flow (file, caption, hashtags, cover frame)
- Scheduling support (publish now or at a future time)
- Post-publish confirmation and URL capture

**Definition of Done:** The Publisher uploads a video to TikTok unattended, confirms the post is live, and stores the published URL.

---

### Phase 7 — Automation

**Goal:** The Studio operates weekly without manual triggering.

**Deliverables:**
- Weekly scheduler — triggers the full pipeline twice per week
- Automatic recovery — retries failed stages with backoff
- Notifications — alerts on success, failure, or human approval requests

**Definition of Done:** The Studio autonomously publishes two high-quality TikTok videos every week. Failures are recovered or escalated without human initiation.

---

## Future Ideas

- Analytics dashboard tracking views, retention, and follower growth per video
- A/B testing for thumbnails and captions
- Audience feedback loop feeding into idea generation
- Support for TikTok Series or multi-part narratives
- Voice cloning for a consistent Cocoa Talk narrator persona
