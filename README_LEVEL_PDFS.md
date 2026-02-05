# Level PDFs and Preview Watermarks

## Overview

Both the Matching and Find & Cover generators now create:
1. **Full PDFs** - Complete product with all levels
2. **Level-specific PDFs** - Individual PDFs for each level
3. **Preview PDFs** - Watermarked versions for marketing

## File Structure

### Matching Product (4 Levels)
- `brown_bear_matching_color.pdf` - Full color (60 pages)
- `brown_bear_matching_bw.pdf` - Full BW (60 pages)
- `brown_bear_matching_level1_color.pdf` - Level 1 color (15 pages)
- `brown_bear_matching_level1_bw.pdf` - Level 1 BW (15 pages)
- `brown_bear_matching_level1_preview.pdf` - Level 1 preview with watermark
- (Same pattern for levels 2, 3, 4)

### Find & Cover Product (3 Levels)
- `brown_bear_find_cover_color.pdf` - Full color (39 pages)
- `brown_bear_find_cover_bw.pdf` - Full BW (39 pages)
- `brown_bear_find_cover_level1_color.pdf` - Level 1 color (13 pages)
- `brown_bear_find_cover_level1_bw.pdf` - Level 1 BW (13 pages)
- `brown_bear_find_cover_level1_preview.pdf` - Level 1 preview with watermark
- (Same pattern for levels 2, 3)

## Level Contents

### Matching (15 pages per level)
- 12 activity pages (one per icon)
- 2 cutout pages (5 icons per strip × 2)
- 1 storage labels page

### Find & Cover (13 pages per level)
- 12 activity pages (one per icon)
- 1 storage labels page

## Preview Watermark

The preview PDFs include:
- Diagonal "PREVIEW" text at 45° angle
- Helvetica Bold, 140pt font
- Gray color with 30% opacity
- Centered on every page
- Prevents unauthorized printing while showing content

## Generating Files

### Matching Product
```bash
python generate_matching_constitution.py
```

### Find & Cover Product
```bash
python generate_find_cover_constitution.py
```

Both generators will automatically create:
1. Full PDFs (color and BW)
2. Split them into level-specific PDFs
3. Add watermarks to create preview versions

## Sales Options

### Option 1: Individual Levels
Sell each level separately:
- Matching Level 1 (Beginner)
- Matching Level 2 (Easy)
- Matching Level 3 (Medium)
- Matching Level 4 (Hard)

### Option 2: Complete Sets
Sell all levels together at a discount

### Option 3: Custom Bundles
Any combination of levels

## Use Cases

### For Teachers Pay Teachers Listings
- Use **preview PDFs** in product images
- Offer **color and BW** options
- Sell **individual levels** or **complete sets**

### For Marketing
- Share preview PDFs on social media
- Include in email campaigns
- Display on website
- Watermark prevents unauthorized use

### For Classroom Use
- Print **BW versions** for budget-friendly copies
- Use **color versions** for laminated materials
- Choose appropriate **level** for student ability

## Technical Notes

### Dependencies
- Python 3.6+
- ReportLab (PDF generation)
- PyPDF2 (PDF manipulation)
- Pillow (Image processing)

### Code Functions

**`add_preview_watermark(input_pdf, output_pdf)`**
- Adds watermark to all pages
- Uses ReportLab for watermark creation
- PyPDF2 for merging

**`split_pdf_by_level(full_pdf, output_dir, mode)`**
- Splits full PDF into level PDFs
- Calculates page ranges automatically
- Maintains page quality

## Color Coding

Levels are color-coded for easy identification:
- **Level 1:** Orange (Beginner)
- **Level 2:** Blue (Easy/Intermediate)
- **Level 3:** Green (Medium/Advanced)
- **Level 4:** Purple (Hard) - Matching only

This makes it easy for teachers to organize and select appropriate materials.
