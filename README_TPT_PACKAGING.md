# TPT Product Packaging Automation

Complete automation system for Teachers Pay Teachers product packaging.

## Overview

This script automates the entire TPT product packaging workflow, saving hours of manual work and ensuring consistent, professional results across all products.

## What It Does

For EACH product PDF, the script automatically creates:

### 1. Preview Images (JPG, 150 DPI)
- Converts pages 1-4 to high-quality JPG images
- Perfect for TPT product listings
- Names: `ProductName_Preview1.jpg`, `Preview2.jpg`, etc.

### 2. Square Thumbnail (PNG, 500×500px)
- Takes page 1 of PDF
- Crops to center square
- Resizes to 500×500 pixels
- High-quality PNG format
- Names: `ProductName_Thumbnail.png`

### 3. Professional Cover PDF
- Turquoise header (#5DBECD) - 2 inches tall
- Cream body background (#FFF8E1)
- White product title (42pt, bold)
- Centered product thumbnail (300×300px)
- Navy subtitle (#1F4E78): "Errorless File Folder Activities"
- Gold footer (#FFB84D): "© 2025 Small Wins Studio ⭐"
- Names: `ProductName_Cover.pdf`

### 4. Complete Folder Structure
```
ProductName/
├── ProductName.pdf              # Main product
├── ProductName_Cover.pdf        # Professional cover
├── Quick_Start_Guide.pdf        # Usage instructions
└── Terms_of_Use/
    └── Terms_of_Use.pdf        # License terms
```

### 5. ZIP Package
- Everything packaged into one ZIP file
- Ready for immediate TPT upload
- Names: `ProductName.zip`

## Quick Start

### Installation

```bash
# Install required packages
pip install Pillow PyMuPDF reportlab
```

### Usage

```bash
# Run the script
python package_for_tpt.py
```

That's it! The script will:
1. Find all product PDFs in `samples/brown_bear/`
2. Process each one automatically
3. Create all required files
4. Generate a complete summary report

## Output Structure

All files are organized in the `TPT_Packages` directory:

```
TPT_Packages/
├── Previews/
│   ├── Product1_Preview1.jpg
│   ├── Product1_Preview2.jpg
│   ├── Product1_Preview3.jpg
│   ├── Product1_Preview4.jpg
│   └── ...
├── Thumbnails/
│   ├── Product1_Thumbnail.png
│   └── ...
├── Covers/
│   ├── Product1_Cover.pdf
│   └── ...
└── Zips/
    ├── Product1.zip           # Ready for TPT upload!
    └── ...
```

## Example Output

```
============================================================
TPT PRODUCT PACKAGING AUTOMATION
Small Wins Studio
============================================================

✓ Created output directories in TPT_Packages

Scanning for products...
✓ Found 2 product(s)

============================================================
Processing: brown_bear_find_cover_color
============================================================
1. Creating preview images...
  ✓ Created 4 preview images
2. Creating thumbnail...
  ✓ Created thumbnail (500x500px)
3. Creating cover PDF...
  ✓ Created cover PDF
4. Creating folder structure and ZIP...
  ✓ Created ZIP package

✓ brown_bear_find_cover_color - Ready for TPT upload!

============================================================
PACKAGING COMPLETE!
============================================================

📦 ZIP FILES CREATED:
  ✓ brown_bear_find_cover_color.zip
  ✓ brown_bear_matching_color.zip

🖼️  PREVIEW IMAGES CREATED:
  ✓ brown_bear_find_cover_color_Preview1.jpg
  ✓ brown_bear_find_cover_color_Preview2.jpg
  ✓ brown_bear_find_cover_color_Preview3.jpg
  ✓ brown_bear_find_cover_color_Preview4.jpg
  ✓ brown_bear_matching_color_Preview1.jpg
  ✓ brown_bear_matching_color_Preview2.jpg
  ✓ brown_bear_matching_color_Preview3.jpg
  ✓ brown_bear_matching_color_Preview4.jpg

📊 SUMMARY:
  • 2 products ready for TPT!
  • 8 preview images
  • 2 thumbnails
  • 2 covers
  • 2 ZIP packages

✓ All files in: TPT_Packages

🎉 Ready for TPT upload!
```

## Customization

### Modify Colors

Edit the `COLORS` dictionary in `package_for_tpt.py`:

```python
COLORS = {
    'turquoise': (0.365, 0.745, 0.804),  # Header
    'cream': (1.0, 0.973, 0.882),         # Body
    'navy': (0.122, 0.306, 0.471),        # Subtitle
    'gold': (1.0, 0.722, 0.302),          # Footer
    'white': (1.0, 1.0, 1.0)
}
```

### Modify Design Specs

Edit the `COVER_SPECS` dictionary:

```python
COVER_SPECS = {
    'header_height': 2 * inch,
    'title_fontsize': 42,
    'subtitle_fontsize': 18,
    'footer_fontsize': 14,
    'thumbnail_size': (300, 300)
}
```

### Change Output Directories

Edit the directory paths at the top:

```python
OUTPUT_DIR = Path("TPT_Packages")
PREVIEWS_DIR = OUTPUT_DIR / "Previews"
THUMBNAILS_DIR = OUTPUT_DIR / "Thumbnails"
COVERS_DIR = OUTPUT_DIR / "Covers"
ZIPS_DIR = OUTPUT_DIR / "Zips"
```

## Technical Details

### Image Quality
- **Preview JPGs:** 150 DPI (optimal for web display)
- **Thumbnail PNG:** 500×500 pixels (TPT standard)
- **Source rendering:** 300 DPI (high quality conversion)

### PDF Generation
- **ReportLab:** Professional PDF creation
- **Letter size:** 8.5" × 11"
- **Embedded images:** High quality thumbnails
- **Vector graphics:** Crisp text and colors

### File Processing
- **PyMuPDF (fitz):** PDF to image conversion
- **PIL/Pillow:** Image manipulation and cropping
- **zipfile:** Package creation
- **pathlib:** Modern file handling

## Benefits

✅ **Time Saving**
- Automates hours of manual work
- Process multiple products in minutes
- Eliminates repetitive tasks

✅ **Consistency**
- Same design across all products
- Professional branding
- No human errors

✅ **Quality**
- High-resolution images
- Professional cover design
- Optimized for TPT

✅ **Complete**
- Everything TPT requires
- All files properly organized
- Ready to upload

✅ **Reusable**
- Works for any product
- Easy to customize
- Scales to any number of products

## Workflow Integration

### For New Products

1. **Generate your PDF** (using existing generators)
2. **Run the packaging script**
   ```bash
   python package_for_tpt.py
   ```
3. **Upload the ZIP to TPT** - Done!

### For Product Updates

1. **Regenerate your PDF** (after making changes)
2. **Run the packaging script again**
3. **Upload updated ZIP to TPT**

### For Batch Processing

The script automatically processes all products it finds:
- Place all product PDFs in the correct directory
- Run once
- Get packages for all products

## Troubleshooting

### "No product PDFs found"
- Check that PDFs are in `samples/brown_bear/find_cover/` or `samples/brown_bear/matching/`
- Verify file names match expected patterns

### "Module not found" errors
- Install dependencies: `pip install Pillow PyMuPDF reportlab`

### Preview images look pixelated
- Check the DPI setting (currently 150 DPI)
- Increase zoom factor for higher quality

### Cover design issues
- Verify thumbnail was created successfully
- Check color definitions in COLORS dictionary

## Future Enhancements

Potential features to add:
- [ ] Command-line arguments for custom directories
- [ ] Configuration file support
- [ ] Multiple cover design templates
- [ ] Custom Quick Start Guide content
- [ ] Batch rename functionality
- [ ] Preview image watermarking
- [ ] Level-specific packaging (separate L1, L2, L3)

## Credits

**Created by:** Small Wins Studio  
**Date:** February 2026  
**Purpose:** TPT Product Packaging Automation  

## License

© 2025 Small Wins Studio. All rights reserved.

---

**Questions or issues?** Check the script comments for detailed documentation of each function.
