# StudioForge — Master Phase Index
**Small Wins Studio · Product Automation Centre**
Version: 1.0 (April 2026)

---

## Overview

StudioForge is a three-screen internal tool (Today / Build / Tools) that manages the full lifecycle of TPT product production for Small Wins Studio. This index is the source of truth for all phases.

**Architecture summary:**
- Today screen — active book status, next action, seasonal picks
- Build screen — 5 tabs: Icons → QA → Build → Listing → AAC Board
- Tools drawer — Symbol Library, PDF Extractor, Pipeline, Settings

---

## Phase Status

| Phase | Title | Status | Brief file |
|---|---|---|---|
| 1 | Foundation (shell, tokens, slug decode, toasts) | ✅ Complete | `PHASE_1_FOUNDATION.md` |
| 2 | Today screen | ✅ Complete | `STUDIOFORGE_PHASES_2_4_UPDATE.md` |
| 3 | Build screen + Icons tab | ✅ Complete | `STUDIOFORGE_PHASES_2_4_UPDATE.md` |
| 4 | QA tab | ✅ Complete | `STUDIOFORGE_PHASES_2_4_UPDATE.md` |
| 5 | Build tab + state persistence | ✅ Complete | `PHASE_5_BUILD_TAB.md` |
| 6 | Listing tab (AI-assisted copy) | ✅ Complete* | `PHASE_6_LISTING_TAB.md` |
| 7 | Tools drawer | ⬜ Not started | `PHASE_7_TOOLS_DRAWER.md` |
| 8 | AAC Board Editor | ⬜ Not started | `PHASE_8_AAC_BOARD_EDITOR.md` |
| 9 | Covers (Canva CSV + merge) + Listing Images | ⏳ In progress | `STUDIOFORGE_MASTER_STRATEGIC_BRIEF.md` (Phase 9) |
| 10 | AI Listing integration + Pinterest CSV | ⬜ Planned | `STUDIOFORGE_MASTER_STRATEGIC_BRIEF.md` (Phase 10) |
| 11 | Freebie generator | ⬜ Planned | `STUDIOFORGE_MASTER_STRATEGIC_BRIEF.md` (Phase 11) |

*Phase 6 note: Delivered with template-based draft available. AI draft via Anthropic API (as specced in brief) is gated by `.env` and may be deferred depending on API cost. The brief remains the spec for full AI integration.

*Phases 9–11 note: Detailed specs live in the Master Strategic Brief. Phase 9 (Covers + Listing Images) is being wired in UI; Phases 10–11 are planned next in this branch.

---

## Key Architectural Decisions (locked)

These decisions were made and confirmed across phases. Do not revisit without explicit discussion.

| Decision | Resolution |
|---|---|
| UI framework | Streamlit (Python). Retained from legacy app. |
| State persistence | `assets/themes/<slug>/config/book_state.json` per book |
| AAC board config | `assets/themes/<slug>/config/aac_board.json` per book (Phase 8) |
| Listing backup | `assets/themes/<slug>/config/listing.md` (human-readable) |
| Slug decoding | `theme_titles.json` overrides + auto-decode fallback |
| Book discovery | Scan `assets/themes/` subfolders. Override via `SF_THEMES_ROOT` env var |
| Generator calls | Subprocess only. Never modify generator `.py` files from StudioForge. |
| Built product token list | Matching, Find & Cover, Word Search, AAC Sentence Strips, Sorting Cards — exactly these 5. No others. |
| AAC Board grid default | 6×6. Core rows: 0 (pronouns), 1 (core verbs), 5 (navigation). Locked by default. |
| Brand primary colour | `#006379` teal throughout. Navy `#1E3A5F` for top bar. Gold `#F5C518` accent only. |
| AI listing draft | Anthropic API (`claude-sonnet-4-6`), deferred to when cost is acceptable. Template fallback in place. |

---

## File Map

```
project root/
├── studioforge_app.py          ← main app (all phases touch this)
├── aac_migrate_configs.py      ← Phase 8 migration script (run once)
├── theme_titles.json           ← slug → display name overrides
├── .streamlit/
│   └── config.toml             ← Phase 9 brand theme
├── .env                        ← ANTHROPIC_API_KEY (not committed)
├── requirements.txt            ← anthropic, python-dotenv added Phase 6
├── assets/
│   ├── themes/
│   │   └── <slug>/
│   │       ├── activity_images/    ← source icons for Icons tab
│   │       ├── OUTPUT/
│   │       │   └── thumbnails/     ← generator thumbnail PNGs
│   │       └── config/
│   │           ├── book_state.json ← icons, QA, build, listing state
│   │           ├── listing.md      ← human-readable listing copy
│   │           ├── aac_board.json  ← AAC board cell config (Phase 8)
│   │           └── aac_board_preview.png ← exported board PNG (Phase 8)
│   └── symbols/                ← extracted PCS symbol PNGs (Phase 7)
└── phase_briefs/
    ├── PHASE_1_FOUNDATION.md
    ├── PHASE_5_BUILD_TAB.md
    ├── PHASE_6_LISTING_TAB.md
    ├── PHASE_7_TOOLS_DRAWER.md
    ├── PHASE_8_AAC_BOARD_EDITOR.md
    ├── PHASE_9_DESIGN_POLISH.md
    └── STUDIOFORGE_MASTER_INDEX.md  ← this file
```

---

## Open Items (to resolve before or during remaining phases)

| Item | Phase | Notes |
|---|---|---|
| AI listing draft via Anthropic API | 6 (deferred) | Template fallback in place. Revisit when API cost is acceptable. |
| Streamlit drag-and-drop for AAC Board | 8 | May need click-to-place fallback if true drag-drop not achievable in Streamlit. Flag early. |
| Streamlit drawer overlay (vs sidebar push) | 7 | Flag to Fi if overlay behaviour cannot be achieved without a component library. |
| Regenerate listing confirmation dialog | 6 | Windsurf noted this as not yet added. Add before Phase 6 is fully signed off. |
| Phase 5 phantom chips (I Spy, Bingo, QR Hunt) | 5 | Confirm these are removed from Today screen before Phase 7 begins. |

---

## Design Pass Reminder (Phase 9)

Phase 9 is cosmetic only. The rule is simple: **if a change in Phase 9 breaks any functional behaviour, revert it.** Run the full Phase 1–8 functional QA checklist after Phase 9 is complete before calling StudioForge done.

---

## What Comes After StudioForge

Once Phase 9 is complete, the next major system is **ListingLift** — the TPT market intelligence tool for discovering which books/niches to build next. StudioForge points the production pipeline at validated demand from ListingLift. These are two separate local tools that work together.
