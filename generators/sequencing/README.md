# Sequencing Generator

This generator creates Brown Bear sequencing activities with TPT brand colors and Small Wins Studio branding.

## Features

- **3 difficulty levels** with consistent color coding:
  - Level 1 (Orange #F4B400): Image hints for errorless learning
  - Level 2 (Blue #4285F4): Numbers only for moderate challenge
  - Level 3 (Green #34A853): Text labels for advanced learners
  
- **Cutout sheet** with all 11 story characters
- **Storage labels** using brand level colors
- **Professional branding** aligned with Small Wins Studio standards

## Brand Colors

The generator uses the official TPT brand colors as defined in `themes/global_config.json`:

- **Navy (#1E3A5F)**: Borders and main text
- **Teal (#2AAEAE)**: Brand accent color
- **Orange (#F4B400)**: Level 1 (Errorless)
- **Blue (#4285F4)**: Level 2 (Distractors)
- **Green (#34A853)**: Level 3 (Picture + Text)

## Usage

```bash
python generators/sequencing/SEQUENCING.py <images_folder> [pack_code] [theme_name]
```

### Example

```bash
python generators/sequencing/SEQUENCING.py brown_bear_images BB0ALL "Brown Bear"
```

## Required Images

The generator expects 11 character images in PNG format:

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

## Output

The generator creates:
- 4-page PDF with 3 activity levels + 1 cutout sheet
- Storage labels page with level color coding
- All pages include proper copyright: "© 2025 Small Wins Studio. All rights reserved."
- PCS licensing notice included

## Design Compliance

This generator follows the Small Wins Studio Design Constitution:
- US Letter page size (8.5" × 11")
- Rounded border with 0.12" corner radius
- Accent stripes using level colors
- Consistent footer and copyright placement
- High-contrast design for accessibility

## Future Enhancements

This generator can be delivered to a different repository later as requested. The code is modular and follows standard Python practices for easy integration into other projects.
