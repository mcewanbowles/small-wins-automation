# Universal Sorting Mat Generator (with AAC Core Words)

**Design Constitution Compliant** sorting mat generator with integrated AAC communication support.

## Overview

Generates interactive sorting mats in **PORTRAIT orientation** (US Letter 8.5" × 11") with AAC core word buttons positioned on the left and right sides. Perfect for special education, speech therapy, and AAC users.

## Features

### Design Constitution Compliance
- ✅ **US Letter PORTRAIT** orientation (8.5" × 11")
- ✅ **0.5" margins** on all sides
- ✅ **Rounded border** (2-3px, 0.12" corner radius) containing all content
- ✅ **Header area ABOVE border** with pack code, page numbers, and "Small Wins Studio"
- ✅ **Accent stripe INSIDE border** (0.55"-0.6" height, rounded corners, orange #F4B400)
- ✅ **Title in Comic Sans MS** font, centered in accent stripe
- ✅ **Two-line footer INSIDE border**:
  - Line 1: Pack code | Theme | Page X/Y
  - Line 2: © 2025 Small Wins Studio copyright with PCS® symbols attribution
- ✅ **Small Wins Studio star logo** (28px) in footer

### AAC Integration (16 Core Words)
**LEFT SIDE (8 buttons):**
- PUT, DIFFERENT, FINISHED, AGAIN, WAIT, I THINK, SAME, HELP

**RIGHT SIDE (8 buttons):**
- STOP, LIKE, DON'T LIKE, FUNNY, UH-OH, WHOOPS, MORE, YES

Each AAC button includes:
- Icon from `assets/global/aac_core/` (50px size)
- Text label below icon
- Rounded border with navy blue outline
- White/light gray background (color/B&W versions)

### Sorting Areas

**Center area contains THREE sorting configurations:**

1. **2-Way Sort**: Two categories side-by-side
2. **3-Way Sort**: Three categories across
3. **Yes/No Sort**: Binary decision sorting

All boxes have navy blue borders (#2B4C7E) with labels.

## Usage

### Command Line

```bash
python generators/universal_sorting/universal_sorting_aac.py \
  --pack_code SORT01 \
  --theme "Universal Sorting" \
  --output_dir OUTPUT/sorting_mats \
  --aac_dir assets/global/aac_core
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--pack_code` | `SORT01` | Product code for branding |
| `--theme` | `Universal Sorting` | Theme name in title |
| `--output_dir` | `OUTPUT` | Output folder for PDFs |
| `--aac_dir` | `assets/global/aac_core` | AAC icon directory |

## Output

- `{pack_code}_sorting_mat_color.pdf` - Full color version (~450-500 KB)
- `{pack_code}_sorting_mat_bw.pdf` - Black & white version (~400-450 KB)

## Changelog

### v2.0 (February 2025) - Complete Rewrite
- **BREAKING CHANGE**: Changed from A4 landscape to US Letter portrait
- Implemented full Design Constitution compliance
- Added proper borders, margins, and branding
- Repositioned AAC buttons from top/bottom to left/right sides
- Fixed text overlap issues
- Switched from reportlab canvas to PIL-based rendering
- 536 lines (complete rewrite from 401 lines)

## License

MIT License - Small Wins Studio © 2025
