# Matching Activity Generator

This folder contains the **Matching** activity generator for Small Wins Studio TpT resources.

## Status
**ACTIVE** — Generator complete and ready for review.

## Features

- **4 difficulty levels** with consistent TPT brand color coding:
  - Level 1 (Orange #F4B400): Errorless - 5 targets, 0 distractors, watermark hints
  - Level 2 (Blue #4285F4): Easy - 4 targets, 1 distractor
  - Level 3 (Green #34A853): Medium - 3 targets, 2 distractors
  - Level 4 (Purple #8C06F2): Hard - 1 target, 4 distractors

- **Professional Layout**:
  - 5 rows × 2 columns (matching boxes + velcro boxes)
  - Target reference box at top
  - Navy borders and proper spacing
  - Velcro dots centered in velcro boxes

- **Complete Output**:
  - Color and B&W versions of all 4 levels
  - Cutout pieces page
  - Storage labels with level color coding
  - Proper copyright and branding

## Brand Colors

The generator uses the official TPT brand colors as defined in `themes/global_config.json`:

- **Navy (#1E3A5F)**: Borders and main text
- **Teal (#2AAEAE)**: Cutout page accent
- **Orange (#F4B400)**: Level 1 (Errorless)
- **Blue (#4285F4)**: Level 2 (Easy)
- **Green (#34A853)**: Level 3 (Medium)
- **Purple (#8C06F2)**: Level 4 (Hard)
- **Purple Border (#6B5BE2)**: Velcro boxes
- **Light Grey (#E8E8E8)**: Velcro box fill

## Configuration
Theme-specific settings are loaded from `/themes/<theme>.json` under the `"matching"` key.

## Output Structure
Generated files are saved to:
```
OUTPUT/
├── BB03_Matching_Color.pdf    # All 4 levels + cutouts + storage labels
└── BB03_Matching_BW.pdf       # B&W version of all content
```

## Usage

```bash
python generators/matching/MATCHING.py <images_folder> [pack_code] [theme_name]
```

### Example

```bash
python generators/matching/MATCHING.py brown_bear_images BB03 "Brown Bear"
```

## Required Images

The generator expects 12 icon images in PNG format:

1. brown_bear.png
2. red_bird.png
3. yellow_duck.png
4. blue_horse.png
5. green_frog.png
6. purple_cat.png
7. white_dog.png
8. black_sheep.png
9. goldfish.png
10. teacher.png
11. children.png
12. eyes.png (or see.png - "see" renamed to "eyes")

## Design Compliance

This generator follows the Small Wins Studio Design Constitution and Matching Product Specification:
- US Letter page size (8.5" × 11")
- 5 rows × 2 columns layout
- Rounded borders with 0.12" corner radius
- Accent stripes using level colors (tall enough for title + subtitle)
- Target box with reference image
- Matching boxes (95-100% icon fill)
- Velcro boxes with centered dots
- Watermark hints for Level 1 only (20-30% opacity)
- Proper footer with copyright
- B&W version converts cleanly to grayscale

## See Also
- `/design/product_specs/matching.md` — Full product specification
- `/design/Design-Constitution.md` — Universal design standards
- `/themes/global_config.json` — Brand color definitions
