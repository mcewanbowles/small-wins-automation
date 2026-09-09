# Teen SpEd Icon Research + Design Pack (Max Build)

## What was researched

### Icon pool counts
(From `Pipeline Products/teen_sped_icon_pool_summary.csv`)

- `assets/global/icons/ask_for_help_master/selected`: **99 PNGs**
- `assets/social_stories/body hygiene/png_raw`: **384 PNGs**
- `assets/global/icons/ask_for_help_master/cyber-security/png_raw`: **206 PNGs**
- `assets/global/aac_core`: **35 PNGs**

### Body-hygiene inventory created
- Full filename inventory generated at:
  - `assets/social_stories/body hygiene/body_hygiene_png_inventory.csv`

### Coverage check created
- Body-hygiene community product icon coverage report:
  - `Pipeline Products/community_body_hygiene_icon_coverage.csv`
- Result: **all referenced icons now ready in selected/**.

## Design outputs now implemented

### 1) New build-ready community product content file
- `production/generators/ask_for_help/community_series/content_community_body_hygiene.py`
- Includes:
  - Story pages
  - Choice cards
  - Routine strips
  - AAC board items
  - Cutout theme
  - Cover hero mappings

### 2) Registered in community series generator
- `production/generators/ask_for_help/community_series/series_registry.py`
- Added key: `community_body_hygiene`

### 3) Icon staging to selected folder completed
To maximize use of existing icon assets without waiting on manual curation, staged **32 required icons** into:
- `assets/global/icons/ask_for_help_master/selected`

Staged sources included:
- `assets/social_stories/body hygiene/png_raw`
- `assets/social_stories/pad_change/Boardmaker_icons`
- `assets/global/aac_core`

## QA + generation status

### Generation
- Ran:
  - `python production/generators/ask_for_help/community_series/generate_community_series.py --only community_body_hygiene`
- Output folder:
  - `production/generators/ask_for_help/output_series/community_body_hygiene`

### QA
- Ran with explicit content file + selected icons:
  - PASS (no errors)
- Notes:
  - Duplicate-use warnings are expected for routine/choice overlap and are acceptable for reinforcement.

## Product design blueprint using current icon library

### A) Cyber Safety Pack (already configured)
Use icon sets for: message, block, report/tell, screenshot/video evidence, no-reply overlay, trusted adult, phone.

- Core sequence: **Notice -> Stop -> No reply -> Save evidence -> Block -> Tell trusted adult**
- Formats:
  - PDF: explicit teaching + role-play cards
  - Slides: editable scenarios by grade/reading level
  - Easel: action sorting + sequencing practice

### B) Body Hygiene + Self-Advocacy Pack (newly built)
Use icon sets for: brush sequence, deodorant, check self, clean/wash, private room, trusted adult, need help.

- Core sequence: **Notice -> Private space -> Hygiene steps -> Check self -> Ask for help if needed**
- Formats:
  - PDF: routines and scripts
  - Slides: custom routines by student profile
  - Easel: sequencing and public/private decision checks

### C) Cross-pack reusable icon routines
To scale faster, reuse these high-utility routines:
1. **Help-seeking strip**: stop, need help, trusted adult, call home
2. **Regulation strip**: breathe, calm, quiet place, ask again
3. **Repair strip**: problem, tell someone, get support, safe now

## Immediate next production order
1. Finalize body-hygiene lesson script pages (10/20/30 min variants).
2. Export Google Slides editable version for Cyber and Body Hygiene.
3. Create Easel subset from highest-frequency routines only.
4. Curate unlabeled `image_*.png` body-hygiene assets into named sets for phase 2 expansion.

## Constraints handled
- Preserved distinct `I_need_help.png` usage for "Need help" (kept separate from `help.png`).
- Avoided semantically weak substitutions for helper roles.
- Kept build in existing Ask-for-Help automation structure for repeatable scaling.
