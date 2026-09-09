# StudioForge — Protected Generators Manifest

**DO NOT MODIFY, DELETE, OR MOVE THESE FILES.**
These are the verified working generators that produce the complete
activity suite for all 20 September books. They are wired into
`studioforge_app.py` via `PRODUCT_SPECS` and produce validated output.

Last verified: 2026-09-07
Branch: fix/llrp-readiness-20260819

---

## PRIMARY GENERATORS (Studioforge/_TRUTH/) — DO NOT TOUCH

These are the canonical, locked generators used by the app:

| File | Product | Function | Status |
|------|---------|----------|--------|
| `Studioforge/_TRUTH/__init__.py` | Package init | — | active |
| `Studioforge/_TRUTH/MATCHING.py` | Matching Cards | `generate_matching_pack` | active |
| `Studioforge/_TRUTH/_MATCHING_LOCKED.py` | Matching (locked impl) | internal | active |
| `Studioforge/_TRUTH/BINGO.py` | Differentiated Bingo | `generate_bingo_pack` | pilot_review |
| `Studioforge/_TRUTH/BOOK_PARTICIPATION.py` | Book Participation Pieces | `generate_book_participation_pack` | pilot_review |
| `Studioforge/_TRUTH/DECODING.py` | CVC Decode & Build | `generate_decoding_pack` | pilot_review |
| `Studioforge/_TRUTH/INFERENCING.py` | Inferencing Cards | `generate_inferencing_reasoning_pack` | pilot_review |
| `Studioforge/_TRUTH/PRINT_DETECTIVE.py` | Print Detective | `generate_print_detective_pack_wrapper` | pilot_review |
| `Studioforge/_TRUTH/SEQUENCING.py` | Story Sequencing | `generate_grounded_sequence_pack` | pilot_review |
| `Studioforge/_TRUTH/SORTING.py` | Sorting Cards | `generate_grounded_sorting_pack` | pilot_review |
| `Studioforge/_TRUTH/STORY_ELEMENTS.py` | Story Grammar & Retell | `generate_story_elements_mat_pack` | pilot_review |
| `Studioforge/_TRUTH/SYLLABLE_AWARENESS.py` | Syllable Awareness | `generate_syllable_awareness_pack` | pilot_review |
| `Studioforge/_TRUTH/_SYLLABLE_CARDS.py` | Syllable Cards (impl) | internal | active |
| `Studioforge/_TRUTH/VOCABULARY_SNAP.py` | Vocabulary Snap | `generate_vocabulary_snap_pack` | pilot_review |
| `Studioforge/_TRUTH/_VOCAB_WORD_WALL.py` | Word Wall + Snap (impl) | internal | active |
| `Studioforge/_TRUTH/WORD_SEARCH.py` | Word Search | `generate_word_search` | pilot_review |
| `Studioforge/_TRUTH/YES_NO.py` | Yes/No Questions | `generate_yes_no_pack` | pilot_review |
| `Studioforge/_TRUTH/AAC_BOARD.py` | AAC Board | `generate_aac_board_pack` | pilot_review |
| `Studioforge/_TRUTH/SENTENCE_BUILDING.py` | AAC Sentence Building | `generate_sentence_building_pack` | pilot_review |
| `Studioforge/_TRUTH/_SENTENCE_STRIPS_AAC_LOCKED.py` | Sentence Strips (impl) | internal | active |

## SECONDARY GENERATORS (wired via PRODUCT_SPECS)

| File | Product | Function | Status |
|------|---------|----------|--------|
| `production/generators/generators/FIND_AND_COVER_GENERATOR.py` | Find & Cover | `generate_find_and_cover_pack` | pilot_review |
| `production/generators/generators/SPIN_COVER_GENERATOR.py` | Spin & Cover | `generate_spin_cover_pack` | review |
| `production/generators/generators/PDF_MERGER.py` | PDF merging (packaging) | `merge_pdfs` | active |

## SUPPORT MODULES — DO NOT TOUCH

| File | Purpose |
|------|---------|
| `utils/UNIVERSAL_STANDARDS.py` | Brand tokens, colours, copyright, border rules |
| `utils/sws_design.py` | Header/footer/cover drawing, font loading, design system |
| `Studioforge/boardready/modules/qa_logic.py` | Icon QA logic |
| `Studioforge/boardready/modules/qa_reviewer.py` | QA reviewer |
| `BoardReady/boardready/AAC_BOARD_GENERATOR.py` | AAC board generation |
| `Generators/aac_book_board.py` | AAC book board adapter |
| `Studioforge/Accurate generators/IEP_MONITORING_FORM.py` | IEP monitoring form |
| `Studioforge/Accurate generators/ADAPTED_BOOK_GENERATOR.py` | Adapted book generator |
| `Studioforge/Accurate generators/PARTICIPATION_PIECES.py` | Participation pieces (legacy) |
| `Studioforge/Accurate generators/MATCHING_GENERATOR.py` | Matching (legacy reference) |
| `Studioforge/Accurate generators/VOCAB_WORD_WALL.py` | Vocab word wall (legacy reference) |
| `Studioforge/Accurate generators/FIND_AND_COVER_GENERATOR.py` | Find & Cover (legacy reference) |
| `Studioforge/Accurate generators/WORD_SEARCH_GENERATOR.py` | Word Search (legacy reference) |
| `Studioforge/Accurate generators/SYLLABLE_CARDS.py` | Syllable Cards (legacy reference) |
| `Studioforge/Accurate generators/YES_NO_GENERATOR.py` | Yes/No (legacy reference) |
| `Studioforge/Accurate generators/INFERENCING_CARDS.py` | Inferencing (legacy reference) |
| `Studioforge/Accurate generators/SNAP_CARD_GAME.py` | Snap cards (legacy reference) |
| `Studioforge/Accurate generators/SPIN_COVER_GENERATOR.py` | Spin & Cover (legacy reference) |
| `Studioforge/Accurate generators/SENTENCE_STRIPS_AAC.py` | Sentence Strips (legacy reference) |

## MARKETING & PACKAGING — DO NOT TOUCH

| File | Purpose |
|------|---------|
| `production/generators/marketing_thumbnail_generator.py` | Canva-style TPT marketing thumbnails |
| `production/generators/generate_pinterest_pins.py` | Pinterest pin generation |
| `Studioforge/tpt_packager.py` | TPT packager |
| `Studioforge/_build_book_dashboard.py` | Review dashboard builder |

## APP ENTRY POINTS — DO NOT TOUCH

| File | Purpose |
|------|---------|
| `studioforge_app.py` | Main Streamlit application |
| `run_studioforge.bat` | Windows launcher (batch) |
| `run_studioforge.ps1` | Windows launcher (PowerShell) |
| `sf_shared.py` | Shared utilities for app |

## CONFIG & THEME DATA — DO NOT TOUCH

| Path | Purpose |
|------|---------|
| `assets/config/september_2026_sped_book_focus.json` | 20-book September manifest |
| `assets/themes/<slug>/book_vocab.json` | Per-book reviewed vocabulary |
| `assets/themes/<slug>/config/*.json` | Per-book activity configs (12 files each) |
| `assets/branding/logos/small_wins_logo_with_text.png` | SWS logo |
| `assets/branding/logos/studioforge.ico` | SWS icon (shortcuts) |
| `assets/branding/rope/realistic/*.png` | Scarborough Reading Rope diagrams |
| `assets/covers/cover_templates/*.png` | Canva cover templates |

---

## CLEANUP POLICY

When cleaning up the generator database:

1. **NEVER delete files listed above** — they are the verified working set
2. Files in `Generators/ARCHIVE generators/` are safe to remove
3. Files in `Studioforge/_REVIEW/GENERATOR_ARCHIVE_*` are safe to remove
4. Files in `Studioforge/_CANONICAL_LOCKED/` are reference snapshots — keep but do not modify
5. Files in `_ARCHIVE/` are safe to remove
6. Files in `_TLOT_ARCHIVED_DUPLICATE/` are safe to remove
7. Always run `python _qa_audit.py` after any cleanup to verify nothing broke
8. Always commit before AND after cleanup so changes are reversible

## VERIFICATION COMMAND

After any cleanup, verify the build still works:

```bash
# 1. Run QA audit (should show 0 blockers)
python _qa_audit.py

# 2. Test build llama_llama_back_to_school (should produce 21 PDFs)
python -c "from Studioforge._TRUTH.MATCHING import generate_matching_pack; generate_matching_pack('assets/themes/llama_llama_back_to_school/activity_images', 'LLB01', 'Llama Llama Back To School')"

# 3. Test marketing thumbnails
python production/generators/marketing_thumbnail_generator.py "assets/themes/llama_llama_back_to_school/activity_images" "LLB01" "Llama Llama Back To School"
```
