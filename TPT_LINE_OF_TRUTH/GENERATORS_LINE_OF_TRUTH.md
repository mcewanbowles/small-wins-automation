---
# Line of Truth — Generators (Provisional)

Legend:
- 🟩 Canonical (use this)
- 🟧 Alternate (valid but not canonical)
- 🟥 Deprecated/Do not use
- 🟨 Under review (awaiting your confirmation)

Notes:
- This registry exists to eliminate confusion from duplicate/legacy files. Always start here when running builds.
- When a Canonical is chosen, all listings, batch scripts, and QA should point to these exact paths.
- Evidence refers to raster/manifest proof generated on 2026-07-28 unless otherwise noted.

| Product | Status | Canonical Path | Alternates / Duplicates | Evidence & Rationale |
|---|---|---|---|---|
| Matching | 🟩 Canonical | Studioforge/_CANONICAL_LOCKED/MATCHING_GENERATOR__LLRP_STANDARD__LOCKED_2026-08-22.py | 🟧 Generators/ARCHIVE generators/MATCHING_GENERATOR (2).py; 🟧 Generators/ARCHIVE generators/MATCHING_GENERATOR (3).py | Locked to LLRP standard. Outputs teacher cover, 4-level pages for each selected icon, plus cut‑outs and storage labels (COLOR & B&W) and PREVIEW thumbnails; universal frame + two-line footer; hero resolution via assets/themes/<slug>/hero.png. Reference build used for Llama Llama Red Pajama; target for all themes (e.g., Stellaluna). |
| Find & Cover | 🟩 Canonical | Generators/FIND_AND_COVER_GENERATOR (2).py | 🟧 Generators/FIND_AND_COVER_GENERATOR.py, FIND_AND_COVER_IMPROVED.py | Verified build with cover + manifest; 3 levels confirmed. Brand teal locked. Placeholder-output guardrail implemented — routes to `OUTPUT/test_placeholder` when placeholders used. |
| Sentence Strips AAC | 🟩 Canonical | Generators/SENTENCE_STRIPS_AAC (2).py | 🟧 Generators/SENTENCE_STRIPS_AAC.py, (3).py | Manifest-thumbnails ordering bug fixed; cover integrated; 11 pages; AAC symbols robust with env override. Placeholder-output guardrail implemented. |
| Sorting Cards | 🟩 Canonical | Generators/SORTING_CARDS.py | 🟧 Generators/SORTING_CARDS (2).py, *_IMPROVED.py | Brand compliance; thumbnails and description generated. Placeholder-output guardrail implemented — routes to `OUTPUT/test_placeholder/` when placeholder images are used. |
| Story Elements Mat | 🟩 Canonical | Generators/STORY_ELEMENTS_MAT.py |  | Standards-compliant with cover + thumbnails + BuildResult. Placeholder-output guardrail supported via routing flag. |
| I Spy & Count (Brown Bear) | 🟩 Canonical | production/generators/i_spy_count/generate_i_spy_count_brown_bear.py |  | Counting logic hand-verified; blocked only on Brown Bear `activity_images` top-up + hero.png. |

## Matching — layout standard (locked 2026-08-21)
- title/reference icon must not overlap
- page border must be fully continuous with no clipping from footer or content
- content grid sits high enough that the footer has clearance
- title wording uses 'Match the [X]'.

This is the reference for QA on every future Matching page across all books.
Action items to finalize this LoT:
- Off-brand color audit: ensure no `#006379` remains in generators. Fixed in Adapted Book (2); Matching (2) uses on-brand teal `#31A8A0`.
- Identify the 5th fine-tuned generator definitively and add it here (brief suggests Story Elements Mat; please confirm).
- Placeholder-output guardrail: implemented in Matching (2), Sorting Cards, Story Elements Mat, Find & Cover (2), and Sentence Strips AAC (2) — placeholder builds route to `OUTPUT/test_placeholder/`.

Version: 2026-07-29


