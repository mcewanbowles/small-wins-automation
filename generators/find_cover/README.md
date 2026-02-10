# Find + Cover Activity Generator

This folder contains the **Find + Cover** activity generator for Small Wins Studio TpT resources.

## Status
**ACTIVE** — This is the canonical folder for all Find + Cover products.

## Overview
The Find + Cover generator creates differentiated visual discrimination activities with:
- 4 levels (L1-L4) based on distractor load and grid density
- Grid-based layouts (typically 4x4)
- Color and B&W versions
- Storage labels

## Level Definitions (SPED Differentiation)

| Level | Name | Image Type | Description |
|-------|------|------------|-------------|
| **L1** | Errorless | Boardmaker Icons | Fewer items, easy visual search |
| **L2** | Distractors | Boardmaker Icons | More items, still fairly distinct |
| **L3** | Dense Grid | Boardmaker Icons | Tighter layout, items more similar |
| **L4** | Expert | Boardmaker Icons | Densest layout, highest challenge |

> **IMPORTANT:** Always refer to levels as "Level 1", "Level 2", etc. — NOT "Easy", "Medium", "Hard"

## Configuration
Theme-specific settings are loaded from `/themes/<theme>.json` under the `"find_cover"` key.

Example configuration:
```json
{
  "find_cover": {
    "grid_size": "4x4",
    "levels": {
      "L1": { "name": "Errorless", "distractors": "lowest" },
      "L2": { "name": "Distractors", "distractors": "some" },
      "L3": { "name": "Dense Grid", "distractors": "more" },
      "L4": { "name": "Expert", "distractors": "most" }
    },
    "see_icon": "eye.png"
  }
}
```

## Output Structure
Generated files are exported to:
```
exports/<date>_<theme>/find_cover/
├── <theme>_find_cover_level1_color.pdf
├── <theme>_find_cover_level1_bw.pdf
├── <theme>_find_cover_level2_color.pdf
├── <theme>_find_cover_level2_bw.pdf
├── <theme>_find_cover_level3_color.pdf
├── <theme>_find_cover_level3_bw.pdf
├── <theme>_find_cover_level4_color.pdf
├── <theme>_find_cover_level4_bw.pdf
└── <theme>_find_cover_storage_labels.pdf
```

## Usage
```bash
python -m generators.find_cover --theme brown_bear --output exports/
```

## See Also
- `/docs/exports-workflow.md` — Export folder conventions
- `/docs/product-type-standards.md` — Standards for all generators
