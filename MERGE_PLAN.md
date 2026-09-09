# Tool Launcher + StudioForge Merge Plan

## Why merge

Two apps currently compete for the same job:

1. **Tool Launcher** (`Studioforge/WINDSURF_TOOL_LAUNCHER.py`) — a Tkinter desktop app, 285 KB, ~6 500 lines.
2. **StudioForge** (`studioforge_app.py`) — a Streamlit web app, 602 KB, ~12 000 lines.

Fiona ends up using both, which is exactly the confusion the Tool Launcher was built to eliminate. We are merging them into **one** app: StudioForge (Streamlit), taking the best UX from the Tool Launcher and the correct generator wiring from StudioForge.

## Comparison

| Dimension | Tool Launcher (Tkinter) | StudioForge (Streamlit) | Winner / decision |
|---|---|---|---|
| **Generators wired** | `Accurate generators/GENERATE_ALL.py` (legacy), `AAC_BOARD_GENERATOR.py` (legacy, hardcoded `H:\` paths + old brand colors per brief), `LISTING_GENERATOR.py`, separate `CODE_WORDS` script | `Studioforge/_TRUTH/` — 20+ canonical locked generators + `DIGNITY/` line | **StudioForge** (canonical `_TRUTH/` is the source of truth) |
| **Activity coverage** | 4 generators: Matching, Code Words, Book Insert Strips, Board Ready | 20+ generators: Matching, Find & Cover, Word Search, AAC Board, Sequencing, Sorting, Bingo, Yes/No, Inferencing, Vocab Snap, Syllable, Print Detective, CVC Decode, Story Grammar, Adapted Book, IEP Monitoring, Word Wall, Book Participation, Sentence Building + Dignity line | **StudioForge** |
| **Workflow model** | Flat tool tabs + left nav groups + "Guided Start" stepper | 9-stage gated workflow: Setup → Content → Icons → BoardReady → QA → Activities → Dignity → Listing → Promote | **StudioForge** (gated workflow is correct for production safety) |
| **UX shell** | Left sidebar with grouped nav (Start / Set up / Build assets / Generate activities / Review and track / Finish and publish), "New" badges, tooltips, flow stepper, pill status colors, last-used timestamps | Top bar + tab strip + tools drawer; functional but denser | **Tool Launcher** (the grouped sidebar + flow stepper are genuinely better wayfinding) |
| **Icon Labeler** | Launches `ICON_LABELER.py` Flask on port 5052, opens browser, single-instance reuse | Same `ICON_LABELER.py` via subprocess | Tie — same underlying tool |
| **AI Pre-Populate / Topic Builder** | Dedicated tabs calling `TOPIC_CONTENT_BUILDER.py` | `render_new_topic_panel()` + Content review stage | StudioForge already covers this in the workflow |
| **Pack Ready** | Disabled with "Awaiting confirmation" tooltip (per brief) | Not present as a tab; packaging handled via `FINAL_ZIP_PACKAGER.py` / `tpt_packager.py` scripts | Needs a home in StudioForge |
| **QA Review** | Tab embedding `boardready/modules/qa_reviewer.py` | `render_qa_tab()` — full visual QA | StudioForge already covers this |
| **Entry point** | `Small Wins Tool Launcher.lnk` → `Launch_Tool_Launcher.bat` → `WINDSURF_TOOL_LAUNCHER.py` | `run_studioforge.ps1` / `run_studioforge.bat` → `studioforge_app.py` | Consolidate to one |
| **Architecture quality** | Clean tab-per-tool structure, but wrong generators | Monolithic 602 KB single file, but correct generators + gated workflow | Merge: StudioForge's wiring + Tool Launcher's nav structure |

## Merge principle

> **Keep StudioForge's generator wiring and gated workflow. Borrow Tool Launcher's wayfinding (grouped sidebar, flow stepper, status pills, last-used timestamps). Retire the Tool Launcher entirely.**

## Phased plan

### Phase 1 — Retire the Tool Launcher (single entry point)
Goal: one app, one shortcut, zero confusion.

- [ ] Repoint `Small Wins Tool Launcher.lnk` → `run_studioforge.bat` (or a renamed `Small Wins Studio.lnk`).
- [ ] Move `WINDSURF_TOOL_LAUNCHER.py` + its `.bak` + `Launch_Tool_Launcher.bat` + `Launch_Tool_Launcher_DEBUG.bat` + `create_tool_launcher_shortcuts*.ps1` + `remove_tool_launcher_*.ps1` into `Studioforge/_ARCHIVED_TOOL_LAUNCHER/`.
- [ ] Keep `_tool_launcher_log.json` (last-used data) — we may mine it for the new sidebar.
- [ ] Confirm `run_studioforge.ps1` / `run_studioforge.bat` is the single launch path.
- [ ] Smoke-test: StudioForge starts, book selector works, one generator runs.

### Phase 2 — Port Tool Launcher UX into StudioForge
Goal: StudioForge gets the grouped sidebar + flow stepper.

- [ ] Add a left sidebar nav with the same groups: Start / Set up / Build assets / Generate activities / Review and track / Finish and publish.
- [ ] Add "New" badges for recently added capabilities (driven by a date map).
- [ ] Add last-used timestamps per tool (seed from `_tool_launcher_log.json`).
- [ ] Add the flow stepper (Setup → Content → Icons → … → Promote) at the top of the Build screen, clickable.
- [ ] Keep the existing 9-stage gated workflow underneath — the stepper is just a nav affordance for the same stages.

### Phase 3 — Consolidate generator entry points
Goal: every generator call goes through `Studioforge/_TRUTH/`.

- [ ] Audit `studioforge_app.py` for any subprocess call that does NOT point at `_TRUTH/` and repoint it.
- [ ] Remove references to `Accurate generators/GENERATE_ALL.py`, legacy `AAC_BOARD_GENERATOR.py`, and standalone `CODE_WORDS` / `BOOK_INSERT` scripts from any active code path.
- [ ] Confirm Code Words, Book Insert Strips, and Pack Ready either (a) have a `_TRUTH/` generator or (b) are explicitly marked "not yet wired" in the UI.

### Phase 4 — Verify all 12 Tool Launcher capabilities have a home
Goal: nothing the Tool Launcher did is lost.

Tool Launcher tab → StudioForge home:
| Tool Launcher tab | StudioForge home | Status |
|---|---|---|
| Board Ready | Build screen → BoardReady stage → `run_boardready_generator` → `Studioforge._TRUTH.AAC_BOARD` | ✅ Wired (Phase 3 repointed from legacy `Generators.aac_book_board`) |
| Matching | Build screen → Activities stage → `Studioforge._TRUTH.MATCHING` | ✅ Wired |
| Guided Start | Today screen + Build screen flow stepper (9-stage progress bar + "→ Next" button) | ✅ Wired |
| Code Words | Not in `PRODUCT_SPECS`; generator lives at `production/generators/generate_code_words_constitution.py` | ⚠️ Gap — see below |
| Book Insert Strips | Not in `PRODUCT_SPECS`; generator lives at `production/generators/generate_book_insert_strips_constitution.py` | ⚠️ Gap — see below |
| AI Pre-Populate | Build screen → Setup/Content stage → `AAC_VOCAB_BUILDER.py` subprocess | ✅ Wired |
| Topic Builder | Today screen → New Topic panel → `TOPIC_CONTENT_BUILDER.py` subprocess | ✅ Wired |
| Icon Labeler | Build screen → Icons stage → `ICON_LABELER.py` Flask on port 5052 | ✅ Wired |
| Review and track | Today screen / Tracker view (`render_tracker_screen`) | ✅ Wired |
| Listing Generator | Build screen → Listing stage (`render_listing_tab`) — in-app form with AI draft | ✅ Wired (better than old CLI script) |
| Pack Ready | Build screen → Activities stage → "Finalize & Package for TPT" button → `finalize_and_package_book` | ✅ Wired (lives in Activities, not Promote) |
| QA Review | Build screen → QA stage (`render_qa_tab`) | ✅ Wired |

### Gaps: Code Words and Book Insert Strips

Both generators exist and work but have **not been promoted into `_TRUTH/`** or wired into `PRODUCT_SPECS`. Per the architecture rule ("Do not integrate unfinished engines directly into the main StudioForge UI"), they are intentionally left unwired until reviewed.

- **Code Words** (`production/generators/generate_code_words_constitution.py`): signature is `generate_code_words_pack(slug, theme_name, images_folder, pack_code)` — does NOT match the `_TRUTH/` dispatch contract `(images_folder, pack_code, theme_name)`. Would need a wrapper or signature change before promotion.
- **Book Insert Strips** (`production/generators/generate_book_insert_strips_constitution.py`): signature `generate_book_insert_strips_pack(images_folder, pack_code, theme_name)` — DOES match the contract. Could be promoted by moving into `_TRUTH/` and adding to `PRODUCT_SPECS`, pending review.

**Decision deferred to Fiona:** promote these into `_TRUTH/` and wire them, or leave them as standalone scripts run from the command line. Not force-wired during this merge.

### Pack Ready location note

Packaging ("Finalize & Package for TPT") lives at the bottom of the **Activities** stage (`render_build_tab`), not the Promote stage. The Promote stage handles Pinterest/Tailwind marketing. This is acceptable — packaging logically follows building — but worth noting for wayfinding.

- [x] Walk each row, confirm the capability exists and is reachable.
- [x] For Pack Ready: confirmed it lives in Activities stage as "Finalize & Package for TPT".
- [x] Code Words + Book Insert Strips: documented as gaps, deferred to Fiona.

## Out of scope for this merge

- Rewriting `studioforge_app.py` into modules (separate refactor task).
- Adding new product types or generators.
- Changing the `_TRUTH/` generator logic itself.
- AI listing / ListingLift integration (separate roadmap).
- Promoting Code Words / Book Insert Strips into `_TRUTH/` (deferred to Fiona).
