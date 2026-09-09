# StudioForge Canonical Generator Truth Folder

This folder (`Studioforge/_TRUTH/`) holds the current, working versions of the 15 production activity generators.

## Purpose

- A single place for the canonical generator source.
- Prevents confusion between old/archive copies in `Generators/`, `production/generators/`, `Studioforge/Accurate generators/`, and `Studioforge/_CANONICAL_LOCKED/`.
- Future books should use these files (or wrappers that load from here).

## Products and canonical files

| # | Product | Truth file | Notes |
|---|---------|------------|-------|
| 1 | Book Participation Pieces | `BOOK_PARTICIPATION.py` | Requires `config/book_participation_pieces.json` |
| 2 | Matching | `MATCHING.py` + `_MATCHING_LOCKED.py` | `MATCHING.py` is the wrapper that loads `_MATCHING_LOCKED.py` |
| 3 | Word Search | `WORD_SEARCH.py` | Outputs `{pack_code}_WordSearch_COLOR.pdf` |
| 4 | AAC Sentence Building | `SENTENCE_BUILDING.py` + `_SENTENCE_STRIPS_AAC_LOCKED.py` | `SENTENCE_BUILDING.py` is the wrapper |
| 5 | Sequencing | `SEQUENCING.py` | |
| 6 | Sorting Cards | `SORTING.py` | |
| 7 | Bingo | `BINGO.py` | |
| 8 | Yes/No Questions | `YES_NO.py` | Filters icons to those with reviewed questions |
| 9 | Inferencing Cards | `INFERENCING.py` | |
| 10 | Vocabulary Snap | `VOCABULARY_SNAP.py` + `_VOCAB_WORD_WALL.py` | `VOCABULARY_SNAP.py` is the wrapper |
| 11 | Syllable Awareness | `SYLLABLE_AWARENESS.py` + `_SYLLABLE_CARDS.py` | `SYLLABLE_AWARENESS.py` is the wrapper |
| 12 | Print Detective | `PRINT_DETECTIVE.py` | Wrapper normalises pack code |
| 13 | ~~CVC Decode & Build~~ | `DECODING.py` | **RETIRED** — removed from Generate All pipeline |
| 14 | Story Elements Mat | `STORY_ELEMENTS.py` | Renamed from "Story Grammar & Retell" |
| 15 | AAC Board | `AAC_BOARD.py` | BoardReady wrapper, moves outputs to book `OUTPUT/` and removes cover |

## Important rules

1. **Only edit the file in `_TRUTH/` once it is adopted as the active source.**
2. All paths should derive from the passed `images_folder`, `pack_code`, and `theme_name`.
3. No hardcoded book slugs, pack codes, or theme names.
4. Teacher/instruction covers have been removed from activity PDFs.
5. Outputs must be written to the book's own `OUTPUT/` folder.

## Adopting these as the active source

To make the app use these truth copies, update `studioforge_app.py` `PRODUCT_SPECS` `module` and `func` entries to the `Studioforge._TRUTH.XXX` import path, and update wrapper files (or point them to `_TRUTH/`) as needed.
