# TpT Package Creation Guide

## Overview

This guide explains how to create complete, TpT-ready ZIP packages for your educational products. Each package includes all necessary files for a professional TpT listing.

## Quick Start

### Generate All Packages

```bash
python3 create_tpt_packages.py
```

This creates 4 ZIP files in the `tpt_packages/` directory, ready for immediate TpT upload.

---

## Package Contents

### What's Included in Each ZIP

Every TpT package contains **6 essential files**:

1. **Color PDF** (3.4-3.9 MB)
   - Full product with marketing cover
   - Professional cover with benefits
   - 15-16 activity pages
   - Level-specific color coding

2. **Black & White PDF** (1.4-1.8 MB)
   - Printer-friendly version
   - Same content, optimized for B&W printing
   - Cost-effective for teachers

3. **Terms of Use** (396 KB)
   - Legal licensing information
   - Usage rights and restrictions
   - Copyright protection
   - Professional compliance

4. **How to Use** (330 KB)
   - Teacher instructions
   - Setup guidelines
   - Implementation tips
   - Best practices

5. **Levels of Differentiation** (313 KB)
   - Explanation of 4 levels
   - Errorless, Easy, Medium, Challenge
   - When to use each level
   - Differentiation strategies

6. **More Packs** (301 KB)
   - Promotional material
   - Related products
   - Bundle information
   - Encourages additional purchases

---

## Generated Packages

### Brown Bear Matching Products

| Level | Package Name | Size | Description |
|-------|-------------|------|-------------|
| 1 | `brown_bear_matching_level1_TpT.zip` | 5.4 MB | Errorless level |
| 2 | `brown_bear_matching_level2_TpT.zip` | 4.8 MB | Easy level |
| 3 | `brown_bear_matching_level3_TpT.zip` | 4.8 MB | Medium level |
| 4 | `brown_bear_matching_level4_TpT.zip` | 4.9 MB | Challenge level |

**Total:** 4 complete products ready for TpT upload (19.9 MB combined)

---

## Package Structure

### Example: Level 1 Package

```
brown_bear_matching_level1_TpT.zip (5.4 MB)
├── Brown_Bear_Matching_Level1_Errorless_Color.pdf (3.9 MB)
│   ├── Page 1: Marketing cover with product preview
│   ├── Pages 2-16: Activity pages, cutouts, storage labels
│   └── Footer: Pack code, copyright, PCS® license
│
├── Brown_Bear_Matching_Level1_Errorless_BW.pdf (1.8 MB)
│   └── Same content, black & white for printing
│
├── Terms of Use.pdf (396 KB)
│   ├── License agreement
│   ├── Usage rights
│   └── Copyright information
│
├── How to Use.pdf (330 KB)
│   ├── Setup instructions
│   ├── Implementation guide
│   └── Teaching tips
│
├── Levels of Differentiation.pdf (313 KB)
│   ├── Level descriptions
│   ├── When to use each
│   └── Differentiation strategies
│
└── More Packs.pdf (301 KB)
    ├── Related products
    ├── Bundle information
    └── Promotional content
```

---

## Technical Details

### Script Features

**`create_tpt_packages.py`** provides:

- ✅ **Automatic PDF selection** - Uses covers when available
- ✅ **Batch processing** - All levels in one run
- ✅ **Professional naming** - Level names in filenames
- ✅ **ZIP compression** - Smaller file sizes
- ✅ **Verification** - Checks package contents
- ✅ **Error handling** - Graceful failures with clear messages

### PDF Selection Logic

The script intelligently selects the best available PDFs:

1. **First choice:** PDFs with marketing covers
   - `{theme}_{product}_level{X}_color_with_cover.pdf`
   
2. **Second choice:** Windows-compatible covers
   - `{theme}_{product}_level{X}_color_with_cover_windows.pdf`
   
3. **Fallback:** Basic color PDFs
   - `{theme}_{product}_level{X}_color.pdf`

### File Naming Convention

**Format:** `{Theme}_{Product}_Level{X}_{LevelName}_{Version}.pdf`

**Examples:**
- `Brown_Bear_Matching_Level1_Errorless_Color.pdf`
- `Brown_Bear_Matching_Level2_Easy_BW.pdf`
- `Space_Adventure_Bingo_Level3_Medium_Color.pdf`

**Level Names:**
- Level 1: Errorless
- Level 2: Easy
- Level 3: Medium
- Level 4: Challenge

---

## Customization

### For Different Themes

Edit `create_tpt_packages.py`:

```python
THEME = "space_adventure"  # Change theme name
PRODUCT = "matching"        # Product type
LEVELS = [1, 2, 3, 4]      # Levels to package
```

### For Different Products

```python
THEME = "brown_bear"
PRODUCT = "bingo"          # Change product type
LEVELS = [1, 2, 3]         # Adjust number of levels
```

### Adding More Documents

Add to `REQUIRED_DOCS` dictionary:

```python
REQUIRED_DOCS = {
    "Terms_of_Use.pdf": "Terms of Use.pdf",
    "How_to_Use.pdf": "How to Use.pdf",
    "Levels_Differentiation.pdf": "Levels of Differentiation.pdf",
    "More Packs.pdf": "More Packs.pdf",
    "New_Document.pdf": "New Document.pdf"  # Add here
}
```

---

## TpT Upload Checklist

### Before Upload

- [ ] Verify all 4 ZIP files created
- [ ] Check package contents (at least 6 files each)
- [ ] Confirm file sizes are reasonable (4-6 MB)
- [ ] Test by unzipping one package
- [ ] Review PDFs for quality

### TpT Listing Requirements

Each package should have:
- [ ] Clear product title with level
- [ ] Professional cover image (use preview from PDF)
- [ ] Complete description with benefits
- [ ] Appropriate grade level tags
- [ ] Subject category (Special Education)
- [ ] Resource type (Activities, Printables)
- [ ] File type listed (ZIP with PDFs)

### Upload Process

1. **Create TpT Listing** for each level
2. **Upload ZIP file** as the product
3. **Add cover image** (screenshot of PDF cover)
4. **Write description** highlighting:
   - Page count
   - Differentiation level
   - Bundle availability
   - Bonus storage labels
   - Print-ready quality
5. **Set price** (consider bundle discounts)
6. **Add tags** (Special Ed, Autism, AAC, etc.)
7. **Preview** before publishing
8. **Publish** and share!

---

## Troubleshooting

### Missing PDFs

**Error:** "No color PDF found for Level X"

**Solution:** 
- Verify PDFs exist in `samples/{theme}/{product}/`
- Check filename format matches expected pattern
- Run product generator first if PDFs missing

### Missing Documents

**Warning:** "Missing: Terms of Use.pdf"

**Solution:**
- Check `Draft General Docs/TOU_etc/` exists
- Verify document files are present
- Update `DOCS_DIR` path if different location

### ZIP Creation Failed

**Error:** "Error creating ZIP for Level X"

**Solution:**
- Check write permissions in output directory
- Verify disk space available
- Check for file locks on source PDFs

---

## Best Practices

### File Organization

```
your-repo/
├── samples/              # Generated products
│   └── {theme}/
│       └── {product}/
│           ├── level1_color.pdf
│           ├── level1_bw.pdf
│           └── ...
├── Draft General Docs/   # Supporting documents
│   └── TOU_etc/
│       ├── Terms_of_Use.pdf
│       ├── How_to_Use.pdf
│       └── ...
└── tpt_packages/        # Generated ZIP files (output)
    ├── level1_TpT.zip
    └── ...
```

### Version Control

**What to commit:**
- ✅ Generator script (`create_tpt_packages.py`)
- ✅ Supporting documents (Terms of Use, etc.)
- ✅ Source PDFs (product files)

**What NOT to commit:**
- ❌ ZIP packages (large, generated)
- ❌ Temporary files
- ❌ Build artifacts

**Add to `.gitignore`:**
```
tpt_packages/*.zip
```

### Quality Control

Before final upload:

1. **Test unzip** on different systems (Windows, Mac)
2. **Open all PDFs** to verify rendering
3. **Check file sizes** are appropriate
4. **Verify page counts** match description
5. **Review legal documents** are current
6. **Test print quality** on sample pages

---

## Maintenance

### Updating Packages

When product PDFs are updated:

1. Regenerate product PDFs
2. Run `python3 create_tpt_packages.py`
3. Replace old ZIP files on TpT
4. Update version number in listing

### Updating Documents

When Terms of Use or other docs change:

1. Update files in `Draft General Docs/TOU_etc/`
2. Regenerate all packages
3. Replace on TpT
4. Notify customers if significant changes

### Adding New Levels

If adding Level 5:

1. Update `LEVELS = [1, 2, 3, 4, 5]` in script
2. Ensure Level 5 PDFs exist
3. Run script to generate new package
4. Create new TpT listing

---

## Support Documents

### Required Documents Location

All supporting documents are in: `Draft General Docs/TOU_etc/`

**Available documents:**
- Terms_of_Use.pdf (405 KB)
- How_to_Use.pdf (337 KB)
- Levels_Differentiation.pdf (320 KB)
- More Packs.pdf (308 KB)
- Storage_Organization.pdf (278 KB)
- Student_Directions.pdf (295 KB)
- Progress_Extensions.pdf (243 KB)

**Currently included:** First 4 documents (Terms, How to Use, Levels, More Packs)

**To add more:** Edit `REQUIRED_DOCS` in script

---

## Summary

### What This Automates

- ✅ Finding best available product PDFs
- ✅ Copying supporting documents
- ✅ Professional file naming
- ✅ ZIP package creation
- ✅ Batch processing all levels
- ✅ Quality verification

### What You Still Do

- Create TpT listings
- Write product descriptions
- Set prices
- Add tags and categories
- Upload ZIP files
- Market your products

### Time Savings

**Before automation:**
- Manual file selection: 5 min/level
- Copying documents: 2 min/level
- Renaming files: 3 min/level
- Creating ZIPs: 2 min/level
- **Total: ~48 minutes for 4 levels**

**With automation:**
- Run script: 5 seconds
- **Total: 5 seconds** ⚡

**Savings: 99.8% faster!**

---

## Resources

### Scripts
- `create_tpt_packages.py` - Main package creator

### Documentation
- This guide (TPT_PACKAGES_GUIDE.md)
- WINDOWS_SOLUTION_GUIDE.md
- MARKETING_COVERS_GUIDE.md

### Support
- Check script output for errors
- Review verification section
- Inspect package contents before upload

---

**Created:** February 8, 2026  
**Version:** 1.0  
**Status:** Production Ready ✅
