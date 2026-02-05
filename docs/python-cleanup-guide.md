# Python Generator Cleanup Guide

This document provides guidance for consolidating the many Python files across branches into a streamlined structure.

## Problem Summary

Multiple branches contain numerous Python generator files, many of which are:
- Duplicates (e.g., `find_cover.py` + `find_cover_old.py`)
- Backups (e.g., `matching_cards.py.backup`)
- Test scripts (e.g., `test_brown_bear_generators.py`)
- One-off generation scripts (e.g., `generate_brown_bear_samples.py`)

This causes confusion about which generators are current/active.

## Target Structure

After cleanup, the repository should have:

```
generators/
├── matching/           # ACTIVE - Matching activity generator
│   └── __init__.py
├── find_cover/         # ACTIVE - Find + Cover generator
│   └── __init__.py
├── aac/                # ACTIVE - AAC resources generator
│   └── __init__.py
└── __init__.py         # Package init

deprecated_generators/  # Quarantine for old/unused generators
├── README.md
└── (all other generators moved here)
```

## Active Generators (KEEP)

Only these three product types should have active generators:

| Generator | Purpose | Source File |
|-----------|---------|-------------|
| `matching` | Matching activity pages | `matching_cards.py` → `generators/matching/` |
| `find_cover` | Find + Cover activities | `find_cover.py` → `generators/find_cover/` |
| `aac` | AAC book boards | `aac_book_board.py` → `generators/aac/` |

## Files to Quarantine (MOVE to deprecated_generators/)

These generators should be preserved but moved out of the active path:

### From `generators/` folder:
- `bingo.py`, `bingo_game.py`
- `clip_cards.py`
- `color_questions.py`, `coloring_sheets.py`, `coloring_strips.py`
- `counting_mats.py`
- `i_spy.py`
- `label_the_picture.py`
- `puppet_characters.py`
- `roll_cover.py`
- `sentence_strips.py`
- `sequencing.py`, `sequencing_strips.py`
- `social_stories.py`
- `sorting_cards.py`
- `storage_labels.py`
- `story_maps.py`, `story_sequencing.py`
- `trace_write.py`
- `uno_memory_game.py`
- `vocab_cards.py`
- `wh_questions.py`, `word_search.py`
- `yes_no_cards.py`, `yes_no_questions.py`

## Files to Delete (REMOVE - duplicates/backups)

These are clearly duplicate/backup files that should be removed:
- `find_cover_old.py` (duplicate of `find_cover.py`)
- `matching_cards.py.backup` (backup copy)
- `sentence_strips_old.py` (duplicate)
- `sequencing_strips_old_backup.py` (duplicate)
- `sorting_cards_old.py` (duplicate)

## Root-Level Scripts (CONSOLIDATE)

The following scripts at the repository root should be evaluated:

### Keep/Refactor:
- `build_theme_pack.py` → Could be main entry point

### Move to `scripts/` or remove:
- `demo.py`, `demo_matching.py` → Example/demo scripts
- `generate_brown_bear_samples.py` → One-off script
- `generate_matching_constitution.py` → Specialized script
- `generate_matching_full.py`, `generate_matching_velcro.py` → Duplicates
- `generate_priority_samples.py`, `generate_samples.py`, `generate_simple_samples.py` → Variations
- `run_brown_bear_test.py`, `run_brown_bear_tests.py` → Test runners

### Move to `tests/`:
- `test_brown_bear_generators.py`
- `test_brown_bear_simple.py`
- `test_single_generator.py`

## Cleanup Steps

1. **Create the target folder structure**
   - The `copilot/backup-snapshot-pr7` branch has the clean folder structure already created
   - Folders: `generators/matching/`, `generators/find_cover/`, `generators/aac/`, `deprecated_generators/`

2. **Copy active generators** from `copilot/build-python-automation-system` branch:
   - `generators/matching_cards.py` → `generators/matching/__init__.py`
   - `generators/find_cover.py` → `generators/find_cover/__init__.py`
   - `generators/aac_book_board.py` → `generators/aac/__init__.py`
   
   **Note:** Verify these files exist on the source branch before copying. If file names differ, check for similar files (e.g., `matching.py` instead of `matching_cards.py`).

3. **Move quarantined generators** to `deprecated_generators/`
4. **Delete duplicate/backup files**
5. **Consolidate entry points** into a single `cli.py` or `main.py`
6. **Update imports** in remaining code

## Verification

After cleanup:
- [ ] Only 3 generators in `generators/` (matching, find_cover, aac)
- [ ] All other generators in `deprecated_generators/`
- [ ] No `*_old.py` or `*.backup` files
- [ ] One clear entry point for running generators
- [ ] Tests organized in `tests/` folder
