# AAC (Augmentative & Alternative Communication) Generator

This folder contains the **AAC** resources generator for Small Wins Studio TpT resources.

## Status
**ACTIVE** — This is an approved, maintained generator.

## Overview
The AAC generator creates communication support resources using core vocabulary and symbols:
- Core word boards
- Communication strips
- Visual supports
- Color and B&W versions

## Configuration
Theme-specific settings are loaded from `/themes/<theme>.json`. Global AAC core vocabulary is stored in:
- `/assets/global/aac_core/` — Core AAC symbols
- `/assets/global/aac_core_text/` — Text-based core resources

## Output Structure
Generated files are exported to:
```
exports/<date>_<theme>/aac/
├── <theme>_aac_core_board_color.pdf
├── <theme>_aac_core_board_bw.pdf
├── <theme>_aac_strips_color.pdf
├── <theme>_aac_strips_bw.pdf
└── <theme>_aac_storage_labels.pdf
```

## Usage
```bash
python -m generators.aac --theme brown_bear --output exports/
```

## See Also
- `/docs/exports-workflow.md` — Export folder conventions
- `/docs/product-type-standards.md` — Standards for all generators
