# Production - TpT Release Packages

This folder contains complete, production-ready TpT packages organized by theme and product.

## Structure

```
production/final_products/{theme}/{product}/
├── uploads/                    # TpT ZIP files ready for upload
│   ├── {theme}_{product}_level1_TpT.zip
│   ├── {theme}_{product}_level2_TpT.zip
│   ├── {theme}_{product}_level3_TpT.zip
│   └── {theme}_{product}_level4_TpT.zip
├── previews/                   # Preview PDFs for TpT listing
│   ├── {theme}_{product}_level1_PREVIEW.pdf
│   ├── {theme}_{product}_level2_PREVIEW.pdf
│   ├── {theme}_{product}_level3_PREVIEW.pdf
│   └── {theme}_{product}_level4_PREVIEW.pdf
├── thumbnails/                 # Thumbnail images (280×280, 500×500)
│   └── (PNG files)
├── descriptions/               # TpT listing descriptions
│   ├── {theme}_{product}_level1_description.txt
│   ├── {theme}_{product}_level2_description.txt
│   ├── {theme}_{product}_level3_description.txt
│   ├── {theme}_{product}_level4_description.txt
│   └── {theme}_{product}_freebie_description.txt
├── freebie/                    # Freebie PDF
│   └── {theme}_{product}_freebie.pdf
└── manifest.txt                # Complete file listing with sizes/dates
```

## Generating Release Packages

Run from repository root:

```bash
python create_release_package.py --theme brown_bear --product matching
```

This will:
1. Create TpT ZIP files (containing activity PDF + Quick Start + Terms of Use)
2. Generate preview PDFs
3. Copy thumbnails from marketing folder
4. Copy description files
5. Copy freebie
6. Create manifest

## TpT ZIP Contents

Each `{theme}_{product}_level{N}_TpT.zip` contains exactly 3-4 files:
1. **Activity PDF** - The main product file (color version)
2. **Quick Start Guide** - Level-specific instructions
3. **Terms of Use** - Standard TOU
4. **Terms of Use Credits** - Combined TOU+Credits (optional)

## Support Documents

Support documents are stored in:
- `production/support_docs/Terms_of_Use.pdf`
- `production/support_docs/Terms_of_Use_Credits.pdf`
- `production/support_docs/Quick_Start_Guide_Matching_Level1.pdf` ... Level4.pdf

## Marketing Materials

Marketing materials are sourced from:
- `production/marketing/{theme}/{product}/thumbnails/`
- `production/marketing/{theme}/{product}/{theme}_{product}_L{N}_description.txt`

## Freebies

Freebies are sourced from:
- `production/freebies/{theme}/{product}/{theme}_{product}_freebie.pdf`

## Manifest

The `manifest.txt` file lists:
- All generated files
- File sizes
- Last modified dates
- Generation summary
- Any errors encountered

## Workflow

1. **Generate base PDFs**: Run matching generator to create activity pages
2. **Create release package**: Run `create_release_package.py`
3. **Review outputs**: Check `production/final_products/{theme}/{product}/`
4. **Upload to TpT**: Use files from `uploads/` folder
5. **Add previews**: Use files from `previews/` folder
6. **Add descriptions**: Use text from `descriptions/` folder

## Current Status

### Brown Bear Matching ✅
- 4 levels generated (L1-L4)
- 4 TpT ZIPs ready for upload
- 4 preview PDFs
- 5 description files
- 1 freebie
- Total: 295 KB in uploads/
