# Quick Start Guides - Support Documentation

## Overview

This directory contains **official Quick Start Guides** for all Small Wins Studio products. These professionally designed one-page guides help teachers quickly understand how to prep and use each resource.

## Current Files

### Quick Start Guides (Matching - Brown Bear)
All 5 level-specific Quick Start Guides for the Brown Bear Matching product:

| File | Level | Size | Description |
|------|-------|------|-------------|
| `Quick_Start_Guide_Matching_Level1.pdf` | L1 - Errorless | ~89KB | Identical matching, builds confidence |
| `Quick_Start_Guide_Matching_Level2.pdf` | L2 - Distractors | ~89KB | Visual discrimination with distractors |
| `Quick_Start_Guide_Matching_Level3.pdf` | L3 - Picture+Text | ~89KB | Literacy connections with labels |
| `Quick_Start_Guide_Matching_Level4.pdf` | L4 - Generalisation | ~89KB | Icon to photo matching |
| `Quick_Start_Guide_Matching_Level5.pdf` | L5 - Advanced | ~89KB | B&W to colour matching |

### Terms of Use
- `Terms_of_Use_Credits.pdf` - Official TOU for all products

## Design Features

All Quick Start Guides feature:
- ✅ **Professional design** with Small Wins Studio branding
- ✅ **Teal accent colors** (#20B2AA) with rounded corners
- ✅ **Comic Sans MS font** for accessibility
- ✅ **Single-page format** for easy printing
- ✅ **Two-column layout** for space efficiency
- ✅ **Color-coded sections** with emoji icons
- ✅ **Level-specific content** while maintaining consistent design

## How They're Generated

### Generator Script
Location: `production/generators/generate_quick_start_from_template.py`

### Template Source
The HTML template is located at:
`Draft General Docs/Quick_Start_Guides/Quick_Start_Guide_Matching_Level1.html`

### Generation Process
1. The generator reads the HTML template with placeholders
2. Replaces placeholders with level-specific content:
   - `{{LEVEL}}` - Level number (1-5)
   - `{{LEVEL_FULL}}` - Full level name (e.g., "Level 1 (Errorless)")
   - `{{NUM_BOARDS}}` - Number of boards ("6 matching boards")
   - `{{NUM_LEVELS}}` - Total levels available ("5")
   - `{{DESCRIPTION_FULL}}` - Full description paragraph
   - `{{STUDENT_ROUTINE}}` - Step-by-step instructions (HTML)
   - `{{TROUBLESHOOTING}}` - Common issues and solutions (HTML)
   - `{{NEXT_STEPS}}` - Progression guidance (HTML)
   - `{{QUICK_GAMES}}` - Engagement activities (HTML)
3. Converts HTML to PDF using WeasyPrint
4. Outputs to `production/support_docs/`

### To Regenerate All Quick Start Guides
```bash
cd /home/runner/work/small-wins-automation/small-wins-automation
python3 production/generators/generate_quick_start_from_template.py
```

## Usage in TpT Packages

The TpT packaging system (`production/generators/create_tpt_packages_updated.py`) automatically includes the appropriate Quick Start Guide for each level:

- Brown Bear Matching L1 Color.zip → includes `Quick_Start_Guide_Matching_Level1.pdf`
- Brown Bear Matching L2 Color.zip → includes `Quick_Start_Guide_Matching_Level2.pdf`
- And so on...

Each TpT package contains:
1. Final Color PDF (with cover)
2. Final B&W PDF (with cover)
3. Terms of Use PDF
4. **Quick Start Guide (level-specific)** ← This file!

## Maintenance

### Adding New Levels
If adding Level 6 or beyond:
1. Add content to `LEVEL_CONTENT` dictionary in the generator
2. Update `NUM_LEVELS` placeholder value
3. Run the generator to create new PDFs

### Updating Content
To update content for existing levels:
1. Edit the `LEVEL_CONTENT` dictionary in `generate_quick_start_from_template.py`
2. Run the generator to regenerate all PDFs
3. Commit the updated PDFs

### Updating Design
To update the design:
1. Edit the HTML template: `Draft General Docs/Quick_Start_Guides/Quick_Start_Guide_Matching_Level1.html`
2. Run the generator to apply new design to all levels
3. Commit the updated PDFs

## File Sizes

All Quick Start PDFs should be approximately **88-90 KB** in size. If a PDF is significantly smaller (~3-4 KB), it was likely generated with the old reportlab-based generator and should be regenerated using the template-based generator.

## Dependencies

The generator requires:
- Python 3.x
- WeasyPrint (`pip install weasyprint`)
- See `requirements.txt` for all dependencies

---

*Last Updated: February 2026*
*Generated with: generate_quick_start_from_template.py*
