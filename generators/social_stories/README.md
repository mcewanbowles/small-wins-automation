# Social Stories Generator

This generator creates beautiful, accessible social story PDFs for SPED students covering sensitive topics.

## Status
**ACTIVE** — This is an approved, maintained generator.

## Overview
The Social Stories generator creates professionally designed social story PDFs with:
- Small Wins Studio branding (colors, fonts, footers)
- Large image placeholders for Boardmaker icons
- Clear, accessible layout (1 phrase per page design)
- Automatic page numbering and copyright footers
- US Letter size pages with rounded borders

## Features
- ✓ Parses text files from `assets/social_stories/`
- ✓ Generates professional PDFs with branding
- ✓ Large image placeholders for icons (to be added)
- ✓ Comic Sans MS typography (accessible for learners)
- ✓ Brand colors: Navy, Teal, Gold
- ✓ Rounded borders and accent stripes
- ✓ Automatic footers with copyright info

## Input Format
Stories are stored as `.txt` files in subdirectories under `assets/social_stories/`.

Each story should follow this format:
```
# SOCIAL STORY: [Title]
## [Subtitle/Age Range]

## PAGE 1: [Page Title]

**TEXT:**
```
[Page content text]
```

**IMAGE:**
- [Image description for reference]
```

## Output Structure
Generated PDFs are exported to:
```
exports/social_stories/
├── SOCIAL_STORY_Good_Touch_Bad_Touch.pdf
├── SOCIAL_STORY_Erections_Wet_Dreams.pdf
├── SOCIAL_STORY_Bras_Body_Changes.pdf
├── SOCIAL_STORY_Body_Odor_Deodorant.pdf
└── SOCIAL_STORY_Masturbation_Private.pdf
```

## Usage

### Generate all social stories:
```bash
python generators/social_stories/generator.py
```

### Generate a specific story:
```bash
python generators/social_stories/generator.py --story assets/social_stories/good_touch_bad_touch/SOCIAL_STORY_Good_Touch_Bad_Touch.txt
```

### Custom output directory:
```bash
python generators/social_stories/generator.py --output-dir my_exports
```

## Design Standards
The generator follows the Small Wins Studio Design Constitution:
- **Page size:** US Letter (8.5" × 11")
- **Margins:** 0.5" on all sides
- **Border:** 2px rounded rectangle
- **Typography:** Helvetica (Comic Sans MS when available)
- **Colors:** 
  - Navy (#1E3A5F) - titles
  - Teal (#2AAEAE) - accent stripes
  - Gold (#E8C547) - branding
- **Footer:** Copyright and PCS license notice

## Image Placeholders
Each page includes a large placeholder box for Boardmaker icons:
- Dotted border for easy identification
- Centered text: "[ Image Placeholder ]"
- Subtitle: "Add Boardmaker icon here"
- Size: 5" × 4" (prominent on page)

User will add actual icons tomorrow.

## Dependencies
- Python 3.7+
- reportlab

Install with:
```bash
pip install reportlab
```

## Topics Covered
Current social stories:
1. Good Touch, Bad Touch (Safety)
2. Erections & Wet Dreams (Boys Puberty)
3. Bras & Body Changes (Girls Puberty)
4. Body Odor & Deodorant (Hygiene)
5. Masturbation is Private (Privacy)

## See Also
- `/design/Design-Constitution.md` — Visual standards
- `/themes/global_config.json` — Branding configuration
- `/assets/social_stories/` — Source content files
