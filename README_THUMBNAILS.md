# PDF Page Thumbnails Generator

## Overview

The `generate_page_thumbnails.py` script automatically creates PNG thumbnails for every page of your product PDFs. This is useful for:

- **Marketing Materials**: Preview images for social media, blog posts, etc.
- **Product Listings**: Show multiple pages on Teachers Pay Teachers
- **Documentation**: Visual examples in guides and tutorials
- **Quality Control**: Quick visual check of all pages

## Quick Start

```bash
python3 generate_page_thumbnails.py
```

That's it! The script will:
1. Find all product level PDFs (both color and BW)
2. Convert each page to a PNG thumbnail
3. Organize them in separate folders
4. Show you a complete summary

## Output Structure

```
Thumbnails/
├── brown_bear_matching_level1_color/
│   ├── page_01.png
│   ├── page_02.png
│   ├── page_03.png
│   └── ... (15 pages)
├── brown_bear_matching_level1_bw/
│   ├── page_01.png
│   └── ... (15 pages)
├── brown_bear_matching_level2_color/
│   └── ... (15 pages)
├── brown_bear_matching_level3_color/
│   └── ... (15 pages)
├── brown_bear_matching_level4_color/
│   └── ... (15 pages)
├── brown_bear_find_cover_level1_color/
│   ├── page_01.png
│   └── ... (13 pages)
├── brown_bear_find_cover_level2_color/
│   └── ... (13 pages)
├── brown_bear_find_cover_level3_color/
│   └── ... (13 pages)
└── ... (BW versions too)
```

## Thumbnail Specifications

- **Format**: PNG (optimized)
- **DPI**: 150 (good quality for web/preview)
- **Max Width**: 800 pixels (maintains aspect ratio)
- **Quality**: High (suitable for marketing)

## Use Cases

### 1. Social Media Posts
```bash
# Use thumbnails from Thumbnails/brown_bear_matching_level1_color/
# Perfect for Instagram, Facebook, Pinterest posts
```

### 2. TPT Product Previews
- Upload first 4-6 thumbnails to show product pages
- Gives buyers a clear idea of what they're getting
- Professional preview images

### 3. Blog Posts & Tutorials
- Include thumbnail images in blog posts
- Show examples of activities
- Create how-to guides with visuals

### 4. Email Newsletters
- Feature product pages in newsletters
- Visual promotions
- Engaging marketing content

## Configuration

You can modify the settings in `generate_page_thumbnails.py`:

```python
# Thumbnail settings
THUMBNAIL_DPI = 150      # Change to 300 for higher quality
THUMBNAIL_WIDTH = 800    # Change to 1200 for larger images
```

## Example Output

```
======================================================================
PDF PAGE THUMBNAIL GENERATOR
Small Wins Studio
======================================================================

✓ Output directory: Thumbnails

Scanning for product PDFs...
✓ Found 14 product PDF(s)

======================================================================
GENERATING THUMBNAILS
======================================================================

  Processing: brown_bear_matching_level1_color
  Pages: 15
    ✓ 5/15 pages converted
    ✓ 10/15 pages converted
    ✓ 15/15 pages converted
  ✓ Completed: 15/15 pages

  Processing: brown_bear_find_cover_level1_color
  Pages: 13
    ✓ 5/13 pages converted
    ✓ 10/13 pages converted
    ✓ 13/13 pages converted
  ✓ Completed: 13/13 pages

...

======================================================================
SUMMARY
======================================================================

📊 Statistics:
  • Products processed: 14
  • Total pages: 196
  • Thumbnails created: 196
  • Success rate: 100.0%

📁 Products:
  ✓ brown_bear_matching_level1_color (15 thumbnails)
  ✓ brown_bear_matching_level1_bw (15 thumbnails)
  ✓ brown_bear_matching_level2_color (15 thumbnails)
  ✓ brown_bear_matching_level2_bw (15 thumbnails)
  ... (and more)

📂 All thumbnails saved to: Thumbnails/

✅ Thumbnail generation complete!
```

## File Naming

Thumbnails are named sequentially:
- `page_01.png` - First page
- `page_02.png` - Second page
- `page_03.png` - Third page
- etc.

This makes it easy to:
- Sort files in order
- Reference specific pages
- Batch process images

## Integration with Other Tools

### Use with TPT Packager

The thumbnails can be used alongside the TPT packaging workflow:

```bash
# 1. Generate products
python3 generate_matching_constitution.py
python3 generate_find_cover_constitution.py

# 2. Generate covers
python3 generate_product_covers.py

# 3. Generate thumbnails
python3 generate_page_thumbnails.py

# 4. Package for TPT
python3 package_for_tpt.py
```

### Batch Image Processing

All thumbnails are in PNG format and can be:
- Batch resized with ImageMagick
- Watermarked with scripts
- Converted to other formats
- Optimized for web

## Benefits

✅ **Automated**: No manual screenshot taking  
✅ **Consistent**: Same quality for all pages  
✅ **Organized**: Separate folders by product  
✅ **Fast**: Processes all PDFs in seconds  
✅ **High Quality**: Professional-grade output  
✅ **Flexible**: Easy to customize settings  

## Requirements

- Python 3.6+
- PyMuPDF (fitz)
- Pillow (PIL)

Install with:
```bash
pip install PyMuPDF Pillow
```

## Troubleshooting

### No PDFs Found
**Issue**: Script says "No product PDFs found!"

**Solution**: Make sure you have generated the level PDFs:
```bash
python3 generate_matching_constitution.py
python3 generate_find_cover_constitution.py
```

### Low Quality Thumbnails
**Issue**: Thumbnails look blurry

**Solution**: Increase the DPI in the script:
```python
THUMBNAIL_DPI = 300  # Higher quality
```

### Large File Sizes
**Issue**: PNG files are too large

**Solution**: Reduce the max width:
```python
THUMBNAIL_WIDTH = 600  # Smaller files
```

## Tips

1. **Generate thumbnails after finalizing PDFs** - Any PDF changes require regenerating thumbnails

2. **Use color versions for marketing** - More visually appealing for previews

3. **BW thumbnails for printing** - Show customers what printed version looks like

4. **First 4-6 pages are key** - Most important for product previews on TPT

5. **Update thumbnails when updating products** - Keep marketing materials current

## License

© 2025 Small Wins Studio - All Rights Reserved
