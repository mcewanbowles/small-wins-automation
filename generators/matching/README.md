# Matching Activity Generator

This folder contains the **Matching** activity generator for Small Wins Studio TpT resources.

## Status
**ACTIVE** — This is an approved, maintained generator.

## Overview
The Matching generator creates differentiated matching activities with:
- 4 difficulty levels (Errorless, Easy, Medium, Hard)
- Color and B&W versions
- Cutout pieces page
- Storage labels

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
