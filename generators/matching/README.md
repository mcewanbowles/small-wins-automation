# Matching Activity Generator

This folder contains the **Matching** activity generator for Small Wins Studio TpT resources.

## Status
**ACTIVE** — This is an approved, maintained generator.

## Overview
The Matching generator creates differentiated matching activities with:
- 5 levels (L1-L5) based on image types and cognitive demand
- Color and B&W versions
- Cutout pieces page
- Storage labels

## Level Definitions (SPED Differentiation)

| Level | Name | Image Type | Description |
|-------|------|------------|-------------|
| **L1** | Errorless | Boardmaker Icons | Identical matching, no distractors, builds confidence |
| **L2** | Distractors | Boardmaker Icons | Same image type with increasing distractors |
| **L3** | Picture + Text | Boardmaker + Text | Match pictures to written words (both directions) |
| **L4** | Generalisation | Icon ↔ Real Photo | Match Boardmaker icons to real photographs |
| **L5** | Advanced | B&W ↔ Colour | Match B&W outlines to coloured icons |

### Image Types Available
1. **Boardmaker Icons** - Licenced signature style (colour)
2. **Real Images** - Actual photographs
3. **B&W Boardmaker** - Black & white outlines (for colouring/advanced matching)
4. **Text Labels** - Written word names

> **IMPORTANT:** Always refer to levels as "Level 1", "Level 2", etc. — NOT "Easy", "Medium", "Hard"

## Configuration
Theme-specific settings are loaded from `/themes/<theme>.json` under the `"matching"` key.

## Output Structure
Generated files are exported to:
```
exports/<date>_<theme>/matching/
├── <theme>_matching_level1_color.pdf
├── <theme>_matching_level1_bw.pdf
├── <theme>_matching_level2_color.pdf
├── <theme>_matching_level2_bw.pdf
├── <theme>_matching_level3_color.pdf
├── <theme>_matching_level3_bw.pdf
├── <theme>_matching_level4_color.pdf
├── <theme>_matching_level4_bw.pdf
├── <theme>_matching_cutouts.pdf
└── <theme>_matching_storage_labels.pdf
```

## Usage
```bash
python -m generators.matching --theme brown_bear --output exports/
```

## See Also
- `/design/product_specs/matching.md` — Full product specification
- `/docs/exports-workflow.md` — Export folder conventions
- `/docs/product-type-standards.md` — Standards for all generators
