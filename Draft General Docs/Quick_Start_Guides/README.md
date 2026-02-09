# Quick Start Guides

## Overview

This directory contains **Quick Start Guides** for Small Wins Studio products. These one-page guides help teachers quickly understand how to prep and use each resource.

## Design Standards

All Quick Start Guides follow the **Small Wins Studio branding**:
- **Teal accent strips** (#20B2AA) with 0.12" rounded corners
- **Comic Sans MS** font throughout
- **Teal page border** (3px) with rounded corners
- **Single-page format** for easy printing and reference
- **Two-column layout** for efficient space usage
- **Color-coded sections** for visual organization
- **Clear section headers** with emoji icons

## Current Guides

### Matching to Boards — Level 1 (Errorless)
- **HTML**: `Quick_Start_Guide_Matching_Level1.html`
- **PDF**: `Quick_Start_Guide_Matching_Level1.pdf`
- **Size**: ~77 KB
- **Format**: Single page, US Letter (8.5" × 11")

## Creating New Quick Start Guides

1. **Copy the Template**
   ```bash
   cp Quick_Start_Guide_Matching_Level1.html Quick_Start_Guide_YourProduct.html
   ```

2. **Edit the Content**
   - Update the title and subtitle in the header
   - Modify section content as needed for your product
   - Keep the same visual structure and styling
   - Maintain single-page format

3. **Update the PDF Script** (if creating multiple guides)
   - Edit `generate_pdf.py` to include your new file
   - Or create a product-specific script

4. **Generate PDF**
   ```bash
   python3 generate_pdf.py
   ```

## Section Structure

Each Quick Start Guide includes these sections (customize as needed):

1. **What this resource is** - Brief description
2. **What's included** - List of materials
3. **Prep** - Materials needed and optional items
4. **Set-up steps** - Numbered preparation instructions
5. **Student routine** - How students use the resource
6. **Teaching support** - Prompting strategies
7. **Communication + AAC** - AAC vocabulary suggestions
8. **Ways to use this set** - Classroom implementation ideas
9. **Quick games** - Engagement variations
10. **Troubleshooting** - Common issues and solutions
11. **Next steps** - When student is ready to advance

## Distribution

**Include the PDF** in product ZIP files alongside the activity materials. This helps teachers get started quickly without reading lengthy documentation.

## Maintenance

- Keep guides to **single page** for maximum usability
- Update branding if Small Wins Studio design standards change
- Ensure all guides maintain visual consistency
- Test PDF generation after any HTML changes

## Technical Notes

- **Font**: Comic Sans MS (system font, should be available on most systems)
- **Page Size**: 8.5" × 11" (US Letter)
- **PDF Generation**: WeasyPrint (install with `pip install weasyprint`)
- **Logo**: Links to `../../assets/branding/logos/small_wins_logo_with_text.png`

---

*Last Updated: February 2026*
