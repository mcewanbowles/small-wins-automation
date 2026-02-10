# Marketing Product Covers Guide

## Overview

This guide documents the new marketing-focused product covers that highlight benefits and value proposition while maintaining Design Constitution compliance.

---

## What Changed

### Previous Design
- **Header**: Level number in colored box (e.g., "Level 1")
- **Description**: Generic text ("This level provides errorless practice")
- **Footer**: Basic pack code format
- **Focus**: Educational/technical information

### New Marketing Design ✅
- **Accent Strip**: Product title in teal (e.g., "Brown Bear Matching")
- **Subtitle**: Level info (e.g., "Level 1 • Errorless")
- **Benefits Section**: 5 key product benefits highlighted
- **Footer**: Matches product specification (matching.md)
- **Focus**: Marketing value proposition

---

## Cover Structure

### 1. Accent Strip (Teal Background)
- **Color**: Teal (#2AAEAE)
- **Height**: 1.0"
- **Content**:
  - Product Title: "{Theme} {Product}" (32pt bold, white)
    - Example: "Brown Bear Matching"
  - Level Subtitle: "Level {X} • {Name}" (16pt, white)
    - Example: "Level 1 • Errorless"
- **Position**: Top of page, inside border with 15px margin
- **Rounded corners**: 0.12" radius

### 2. Product Preview Image
- **Size**: 5" × 5"
- **Border**: Level-specific color (Orange/Blue/Green/Purple)
- **Border width**: 3px
- **Rounded corners**: 0.12" radius
- **Content**: First page of product PDF
- **Fallback**: Placeholder with page count

### 3. Product Benefits Section
- **Title**: "✨ Product Benefits ✨" (14pt bold, navy)
- **Benefits** (11pt, centered):
  1. **Page count**: "{X} Differentiated Activity Pages"
  2. **Level type**: "{Level Name} Level for Special Education"
  3. **Bundle**: "Part of Discounted Bundle (Save 25%!)" (in level color, bold)
  4. **Bonus**: "Bonus: Storage Labels Included"
  5. **Contents**: "Print-Ready Cutout Pages"

### 4. Footer (Two-Line Format per matching.md)
- **Line 1** (9pt, navy):
  - Format: "{Product} – Level {X} | {PACK_CODE}{level}"
  - Example: "Matching – Level 1 | SWS-MTCH-BB1"
- **Line 2** (9pt, light gray #999999):
  - "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License."
- **Position**: 0.3" from bottom, inside border

---

## Design Specifications

### Colors
- **Accent Strip**: Teal (#2AAEAE)
- **Main Text**: Navy (#1E3A5F)
- **Background**: White
- **Footer Line 2**: Light Gray (#999999)
- **Level-Specific Colors**:
  - Level 1: Orange (#F4B400)
  - Level 2: Blue (#4285F4)
  - Level 3: Green (#34A853)
  - Level 4: Purple (#8C06F2)

### Typography
- **Primary Font**: Comic Sans MS
- **Fallback 1**: Arial Rounded MT Bold
- **Fallback 2**: Helvetica
- **Font Sizes**:
  - Product title: 32pt bold
  - Level subtitle: 16pt regular
  - Benefits title: 14pt bold
  - Benefits text: 11pt regular
  - Footer: 9pt regular

### Layout
- **Page Size**: US Letter (8.5" × 11")
- **Margins**: 0.5" all sides
- **Border**: 3px navy, rounded corners (0.12" radius)
- **Accent strip margin**: 15px from border
- **Preview image**: Centered on page
- **Benefits**: Centered, 18px line spacing

---

## Marketing Benefits

### What's Highlighted

1. **Page Count**
   - Shows value (e.g., "15 Differentiated Activity Pages")
   - Transparent about content quantity
   
2. **Level Type**
   - Explains differentiation (Errorless/Easy/Medium/Challenge)
   - Targets special education teachers
   
3. **Bundle Savings** ⭐
   - Highlights discount opportunity
   - "Part of Discounted Bundle (Save 25%!)"
   - Shown in level-specific color for emphasis
   
4. **Bonus Content**
   - "Bonus: Storage Labels Included"
   - Adds perceived value
   - Practical classroom resource
   
5. **Print-Ready**
   - "Print-Ready Cutout Pages"
   - Emphasizes convenience
   - Ready to use immediately

### Marketing Psychology

- **Value Proposition**: Clear benefits upfront
- **Bundle Mention**: Encourages upsell
- **Bonus Content**: Increases perceived value
- **Professional Design**: Builds trust
- **Clear Level Info**: Helps customer selection

---

## Technical Implementation

### File: `generate_product_covers_marketing.py`

**Key Functions:**

1. `setup_fonts()`
   - Tries Comic Sans MS
   - Falls back to Arial Rounded MT Bold
   - Final fallback: Helvetica

2. `extract_first_page_as_image()`
   - Uses pdf2image to convert first page
   - 300 DPI for quality
   - Handles poppler not installed gracefully

3. `create_marketing_cover()`
   - Creates cover with all marketing elements
   - Extracts product preview
   - Applies level-specific colors
   - Generates two-line footer

4. `merge_cover_into_pdf()`
   - Merges cover as page 1
   - Preserves all original pages
   - Creates new merged PDF

5. `process_all_levels()`
   - Batch processes all 4 levels
   - Consistent naming
   - Progress reporting

### Dependencies

- **PyPDF2**: PDF reading and writing
- **reportlab**: PDF generation
- **pdf2image**: PDF to image conversion (requires poppler)
- **Pillow (PIL)**: Image manipulation

### Installation

```bash
pip install PyPDF2 reportlab pdf2image Pillow
```

**Note**: pdf2image requires poppler system package:
- Ubuntu/Debian: `sudo apt-get install poppler-utils`
- macOS: `brew install poppler`
- Windows: Download from poppler releases

---

## Usage

### Basic Usage

```bash
python3 generate_product_covers_marketing.py
```

This generates covers for Brown Bear Matching, all 4 levels.

### Custom Theme/Product

```python
from generate_product_covers_marketing import process_all_levels

process_all_levels(
    theme_name="Space Adventure",
    product_type="Matching",
    pack_code_base="SWS-MTCH-SA"
)
```

### Single Level

```python
from generate_product_covers_marketing import create_marketing_cover, merge_cover_into_pdf

# Generate cover
create_marketing_cover(
    level=1,
    theme_name="Brown Bear",
    product_type="Matching",
    level_pdf_path="samples/brown_bear/matching/brown_bear_matching_level1_color.pdf",
    output_path="cover_level1.pdf",
    pack_code="SWS-MTCH-BB"
)

# Merge into product
merge_cover_into_pdf(
    cover_pdf_path="cover_level1.pdf",
    original_pdf_path="samples/brown_bear/matching/brown_bear_matching_level1_color.pdf",
    output_pdf_path="brown_bear_matching_level1_with_cover.pdf"
)
```

---

## File Outputs

### Individual Covers
- `cover_level1_marketing.pdf` (~2.6 KB)
- `cover_level2_marketing.pdf` (~2.6 KB)
- `cover_level3_marketing.pdf` (~2.6 KB)
- `cover_level4_marketing.pdf` (~2.6 KB)

### Merged Products
- `{theme}_{product}_level1_color_with_cover.pdf` (original + 1 page)
- `{theme}_{product}_level2_color_with_cover.pdf` (original + 1 page)
- `{theme}_{product}_level3_color_with_cover.pdf` (original + 1 page)
- `{theme}_{product}_level4_color_with_cover.pdf` (original + 1 page)

**Location**: `samples/{theme}/matching/`

---

## Design Compliance

### Design Constitution
- ✅ Page size: US Letter
- ✅ Margins: 0.5" all sides
- ✅ Rounded borders: 0.12" radius
- ✅ Navy borders: #1E3A5F
- ✅ Comic Sans MS fonts
- ✅ 300 DPI quality

### Product Specification (matching.md)
- ✅ Two-line footer format
- ✅ Line 1: "{Product} – Level {X} | {CODE}"
- ✅ Line 2: Copyright and PCS® license
- ✅ Footer positioned 0.3" from bottom
- ✅ Footer inside border
- ✅ 9pt font size
- ✅ Light gray for line 2

### Brand Guidelines
- ✅ Small Wins Studio branding
- ✅ Teal accent color
- ✅ Level-specific color coding
- ✅ Professional typography
- ✅ Consistent spacing

---

## Benefits vs. Previous Version

### Marketing Impact
| Aspect | Previous | New Marketing |
|--------|----------|---------------|
| **Header** | Level number | Product name |
| **Focus** | Educational info | Value proposition |
| **Benefits** | Not shown | 5 key benefits |
| **Bundle** | Not mentioned | Highlighted with savings |
| **Bonus** | Not emphasized | "Bonus: Storage Labels" |
| **Professionalism** | Good | Excellent |
| **Sales Appeal** | Moderate | High |

### Customer Experience
- **Clarity**: Immediately see product name and level
- **Value**: Benefits clearly listed upfront
- **Decision**: Bundle savings encourage larger purchase
- **Trust**: Professional design builds credibility
- **Practical**: Page count and contents help planning

---

## Customization

### Changing Bundle Discount
Edit line 219 in `generate_product_covers_marketing.py`:
```python
c.drawCentredString(width/2, benefits_y, "• Part of Discounted Bundle (Save 25%!)")
```

Change "25%" to desired discount.

### Adding More Benefits
Add after line 235:
```python
benefits_y -= 18
c.drawCentredString(width/2, benefits_y, "• Your New Benefit Here")
```

### Changing Accent Color
Edit line 26:
```python
TEAL = HexColor('#2AAEAE')  # Change to desired color
```

---

## Future Enhancements

**Potential Improvements:**
1. Add product thumbnail images in corners
2. Include QR code to bundle page
3. Add "Best Seller" badge for popular products
4. Include sample activity screenshot
5. Add teacher testimonial quote
6. Show differentiation visual diagram
7. Include page count pie chart
8. Add "Includes X vocabulary words" benefit

---

## Troubleshooting

### Preview Image Not Showing
**Symptom**: "[Product Preview]" placeholder shown instead of actual preview

**Cause**: Poppler not installed

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

Then re-run generator.

### Font Not Comic Sans
**Symptom**: Covers use Helvetica instead of Comic Sans

**Cause**: Comic Sans font files not found

**Solution**: Ensure `comic.ttf` and `comicbd.ttf` are in the directory, or install Comic Sans system-wide.

### Footer Too Long
**Symptom**: Footer text wraps or gets cut off

**Solution**: Shorten pack code or abbreviate theme name. Footer is designed for standard pack codes (e.g., "SWS-MTCH-BB1").

---

## Maintenance

### Updating for New Products

1. **Update product name** in accent strip
2. **Adjust benefits** for product type
3. **Modify footer** format if needed
4. **Test with sample theme**

### Version Control

- Keep old generator as backup: `generate_level_covers_with_preview.py`
- New marketing version: `generate_product_covers_marketing.py`
- Document changes in commit messages

---

## Summary

**Key Achievement**: Transformed educational cover into marketing tool

**Marketing Focus**:
- Product name prominently displayed
- Benefits clearly highlighted
- Bundle savings emphasized
- Bonus content mentioned
- Professional appearance

**Technical Quality**:
- Design Constitution compliant
- Product specification footer
- Level-specific branding
- Print-ready 300 DPI
- Proper file structure

**Result**: Professional marketing materials that sell the product value while maintaining educational quality and brand consistency.

---

**Date**: February 8, 2026
**Version**: 1.0
**Status**: Production Ready ✅
