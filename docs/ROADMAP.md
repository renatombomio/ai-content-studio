# Cocoa Talk Studio — Product Roadmap

---

## Vision

Cocoa Talk Studio is a purpose-built content automation system for the Cocoa Talk editorial brand.

It is not a generic AI video platform. Every design decision serves one goal: publish consistent, high-quality introspective content on TikTok — autonomously, twice per week.

Cocoa Talk is an introspective content brand. Technology serves the brand. The brand drives every technical decision.

---

## Principles

- **Brand first.** Every feature exists to serve the Cocoa Talk editorial identity. If it does not serve the brand, it does not get built.
- **Typography-first video.** The writing is the story. Footage is the atmosphere. There is no voice-over.
- **TikTok first.** The only publishing platform. No feature exists to serve another.
- **Quality over quantity.** Two excellent videos per week beat ten mediocre ones.
- **Automation first.** The system handles the full pipeline end-to-end by default.
- **Human approval when needed.** Creative checkpoints are the exception, not the rule.
- **Modular architecture.** Each pipeline stage is independently replaceable.
- **Simplicity.** Nothing is built speculatively.

---

## Sprint Status

| Sprint | Scope | Status |
|--------|-------|--------|
| Sprint 1 | Core infrastructure, Cocoa Talk identity, shared domain models | ✅ Completed |
| Sprint 2 | Brain pipeline — StoryDirector, PromptBuilder, AnthropicProvider, StoryParser | ✅ Completed |
| Sprint 3 | Asset Engine — providers, AssetRanker, AssetService | ✅ Completed |
| Sprint 4 | Video Engine — Timeline, Voice (dormant), Subtitles, FFmpeg Renderer | ✅ Completed |
| Sprint 5 | Publisher — TikTok OAuth, TikTokPublisher, PublicationService | ✅ Completed |
| Sprint 6 | Cocoa Brain — editorial pillars, Spanish content, typography-first pipeline | 🔄 Planned |

---

## Product Phases

---

### Phase 0 — Foundation ✅

**Goal:** Establish a working, production-quality repository baseline.

**Definition of Done:** All checks pass. Repository is committed and pushed.

---

### Phase 1 — Core ✅

**Goal:** Establish the technical foundation every module depends on.

**Deliverables:**
- Typed settings, structured logging, database baseline, dependency injection

**Definition of Done:** Application starts cleanly, loads config from environment, connects to the database.

---

### Phase 2 — Cocoa Talk Identity ✅

**Goal:** Define the Cocoa Talk brand so the system produces recognisable content.

**Deliverables:**
- Brand profile, writing style, visual identity, content pillars
- `docs/BRAND.md` — editorial bible
- `docs/COCO.md` — mascot reference

**Definition of Done:** Brand identity is fully documented and version-controlled.

---

### Phase 3 — Brain ✅

**Goal:** Automate ideation and scripting using an LLM.

**Deliverables:**
- `StoryDirector`, `PromptBuilder`, `AnthropicProvider`, `StoryParser`, `BrainService`
- Stories generated natively in Spanish
- Editorial pillars embedded in prompt generation

**Output:** Validated `Story` object — structured JSON consumed by downstream stages.

---

### Phase 4 — Asset Engine ✅

**Goal:** Source cinematic footage for every scene.

**Providers:** Pexels (primary), Pixabay (secondary), Freepik (optional)

**Deliverables:**
- `SearchQueryBuilder`, `AssetProvider`, `PexelsProvider`, `PixabayProvider`, `FreepikProvider`, `AssetRanker`, `AssetService`
- Search parameters: vertical orientation, Spanish language context, cinematic visual language

**Definition of Done:** Given a Scene, the Asset Engine returns a ranked list of vertical footage candidates.

---

### Phase 5 — Video Engine ✅

**Goal:** Assemble footage and typography into a finished TikTok video.

**Architecture change from original plan:**
- Voice synthesis is **dormant**, not removed. `VoiceProvider` remains in the codebase. `voice_track` on `Timeline` is optional.
- Typography (subtitles) is now the **primary storytelling element**, not a secondary overlay.
- Music is selected inside TikTok. The pipeline produces no audio track.

**Deliverables:**
- `Timeline`, `TimelineBuilder`, `SubtitleGenerator`, `FFmpegRenderer`, `RenderService`
- Renderer produces silent video with animated typography

**Definition of Done:** Given a Story and assets, the engine renders a 9:16 MP4 ready for upload.

---

### Phase 6 — Cocoa Brain ✅ Planned

**Goal:** Full editorial automation aligned with the Cocoa Talk brand identity.

**Deliverables:**

| Task | Description |
|------|-------------|
| S6-001 | Make `voice_provider` optional in `RenderService`. Remove from default pipeline path. |
| S6-002 | Add `EditorialPillar` enum to `CreativeBrief`. Update `StoryDirector` to use it. |
| S6-003 | Update `story_prompt.md` with editorial pillars and Spanish-first writing. |
| S6-004 | Update `SearchQueryBuilder` visual mappings for cinematic, warm, autumn aesthetics. |
| S6-005 | End-to-end pipeline bring-up: typography-first silent video with real assets. |
| S6-006 | `Carousel` model + `CarouselGenerator` in Brain. |
| S6-007 | `CarouselRenderer` — produce two-slide carousel image set. |
| S6-008 | Cocoa Question of the Week — weekly carousel automation. |

---

### Phase 7 — Publisher ✅ Completed (Sprint 5)

TikTok OAuth, upload, status polling, `PublicationService` — fully implemented.

---

### Phase 8 — Automation

**Goal:** The Studio operates weekly without manual triggering.

**Deliverables:**
- Scheduler, Content Calendar, Retry System, Monitoring

**Definition of Done:** The Studio autonomously publishes two videos and one carousel per week.

---

## Content Output Target

| Format | Frequency | Pipeline |
|---|---|---|
| Vertical video (9:16) | 2× per week | Brain → Assets → Typography → FFmpeg → TikTok |
| Cocoa Question carousel | 1× per week | Brain → Carousel generator → Canva/image render → TikTok |

---

## Future Ideas

- ElevenLabs integration when premium voice is needed
- Analytics dashboard (views, retention, follower growth)
- Audience feedback loop into idea generation
- Mascot-led video format featuring Coco
- Multi-slide carousel for longer reflective pieces
- Voice cloning for a consistent Cocoa Talk narrator
