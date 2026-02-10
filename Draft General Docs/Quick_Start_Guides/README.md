# Quick Start Guides

## Overview

This directory contains **Quick Start Guides** for Small Wins Studio products. These one-page guides help teachers quickly understand how to prep and use each resource.

## Template Placeholders

The Quick Start Guide template uses placeholders for product-specific information. Replace these when creating guides for specific products:

### Available Placeholders

| Placeholder | Description | Example Values |
|------------|-------------|----------------|
| `{{LEVEL}}` | Level number | "1", "2", "3", "4", "5" |
| `{{DESCRIPTION}}` | Level description | "Errorless matching to boards", "Match with 2 choices", "Match with 3-4 choices" |
| `{{LEVEL_FULL}}` | Full level title for header | "Level 1 (Errorless)", "Level 2 (2 Choices)", "Level 3 (3-4 Choices)" |
| `{{NUM_BOARDS}}` | Number of activity boards | "15", "20", "25" |

### Example Customization

**For Level 1 (Errorless):**
```
{{LEVEL}} → "1"
{{DESCRIPTION}} → "Errorless matching to boards"
{{LEVEL_FULL}} → "Level 1 (Errorless)"
{{NUM_BOARDS}} → "15"
```

**For Level 2:**
```
{{LEVEL}} → "2"
{{DESCRIPTION}} → "Match with 2 choices"
{{LEVEL_FULL}} → "Level 2 (2 Choices)"
{{NUM_BOARDS}} → "20"
```

**For Level 3:**
```
{{LEVEL}} → "3"
{{DESCRIPTION}} → "Match with 3-4 choices"
{{LEVEL_FULL}} → "Level 3 (3-4 Choices)"
{{NUM_BOARDS}} → "20"
```

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

### Matching to Boards — Template
- **HTML**: `Quick_Start_Guide_Matching_Level1.html` (Template with placeholders)
- **PDF**: `Quick_Start_Guide_Matching_Level1.pdf` (Example with placeholders visible)
- **Size**: ~88 KB
- **Format**: Single page, US Letter (8.5" × 11")

## Creating New Quick Start Guides

### Option 1: Using Template Placeholders (Recommended)

1. **Copy the Template**
   ```bash
   cp Quick_Start_Guide_Matching_Level1.html Quick_Start_Guide_Matching_Level2.html
   ```

2. **Replace Placeholders**
   Use find-replace in your editor:
   - Find: `{{LEVEL}}` → Replace: `2`
   - Find: `{{DESCRIPTION}}` → Replace: `Match with 2 choices`
   - Find: `{{LEVEL_FULL}}` → Replace: `Level 2 (2 Choices)`
   - Find: `{{NUM_BOARDS}}` → Replace: `20`

3. **Generate PDF**
   ```bash
   python3 generate_pdf.py
   ```

4. **Rename PDF**
   ```bash
   mv Quick_Start_Guide_Matching_Level1.pdf Quick_Start_Guide_Matching_Level2.pdf
   ```

### Option 2: Manual Customization

1. **Copy the Template**
   ```bash
   cp Quick_Start_Guide_Matching_Level1.html Quick_Start_Guide_YourProduct.html
   ```

2. **Edit the Content**
   - Update the title and subtitle in the header
   - Modify section content as needed for your product
   - Keep the same visual structure and styling
   - Maintain single-page format

3. **Generate PDF**
   ```bash
   python3 generate_pdf.py
   ```

## Section Structure

Each Quick Start Guide includes these sections (customize as needed):

1. **What this resource is** - Brief description (uses {{LEVEL}} and {{DESCRIPTION}})
2. **Part of a Differentiated Series** - Series promotion
3. **What's included** - List of materials (uses {{NUM_BOARDS}})
4. **Prep** - Materials needed and optional items
5. **Set-up steps** - Numbered preparation instructions
6. **Student routine** - How students use the resource
7. **Teaching support** - Prompting strategies
8. **Communication + AAC** - AAC vocabulary suggestions
9. **Ways to use this set** - Classroom implementation ideas
10. **Troubleshooting** - Common issues and solutions
11. **Next steps** - When student is ready to advance
12. **Quick games** - Engagement variations

## Distribution

**Include the PDF** in product ZIP files alongside the activity materials. This helps teachers get started quickly without reading lengthy documentation.

## Maintenance

- Keep guides to **single page** for maximum usability
- Update branding if Small Wins Studio design standards change
- Ensure all guides maintain visual consistency
- Test PDF generation after any HTML changes
- **Keep template file** with placeholders intact for future products

## Technical Notes

- **Font**: Comic Sans MS (system font, should be available on most systems)
- **Page Size**: 8.5" × 11" (US Letter)
- **PDF Generation**: WeasyPrint (install with `pip install weasyprint`)
- **Logo**: Links to `../../assets/branding/logos/small_wins_logo_with_text.png`
- **Placeholders**: Clearly marked with `{{}}` brackets for easy find-replace

---

*Last Updated: February 2026*
