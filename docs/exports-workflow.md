# Exports Workflow

This document describes the standard workflow for generating and exporting TpT resources.

## Key Principle: Generated Files Are NOT Committed

All generated outputs (PDFs, PNGs, ZIPs) are stored locally in the `exports/` folder and are **excluded from Git** via `.gitignore`. This keeps the repository clean and focused on source code and assets.

## Export Folder Structure

When running a generator, outputs are organized as follows:

```
exports/
└── <date>_<theme>/
    ├── matching/
    │   ├── <theme>_matching_level1_color.pdf
    │   ├── <theme>_matching_level1_bw.pdf
    │   └── ...
    ├── find_cover/
    │   ├── <theme>_find_cover_level1_color.pdf
    │   └── ...
    ├── aac/
    │   ├── <theme>_aac_core_board_color.pdf
    │   └── ...
    └── TpT_Listings/
        ├── <theme>_matching.zip
        ├── <theme>_find_cover.zip
        └── <theme>_aac.zip
```

## Running an Export

### Example: Brown Bear Matching Export

```bash
# Generate matching activity for Brown Bear theme
python -m generators.matching --theme brown_bear --output exports/

# Or run all generators for a theme
python -m generators.generate_all --theme brown_bear --output exports/
```

### Output Location

After running, find your generated files in:
```
exports/20260205_brown_bear/matching/
```

## TpT Listing Package

Each TpT listing should be packaged as a single ZIP containing:
- All PDF files (color + B&W versions)
- Terms of Use (TOU) document
- Credits page
- Optional: Thumbnail preview images

The ZIP files are created in `exports/<date>_<theme>/TpT_Listings/`.

## Verification Checklist

Before uploading to TpT, verify:
- [ ] All levels generated (1-4 for differentiated products)
- [ ] Color AND B&W versions present
- [ ] Storage labels included
- [ ] TOU and Credits in ZIP
- [ ] No corrupted or blank pages
- [ ] File sizes are reasonable (< 50MB per ZIP)

## Important Notes

1. **Do NOT commit exports/** — This folder is in `.gitignore`
2. **Do NOT commit generated outputs** — Keep the repo clean
3. **Back up exports locally** before clearing the folder
4. **Use date-prefixed folders** to track export versions

## Excluded Directories

The following directories are excluded from Git (see `.gitignore`):
- `exports/` — Primary export folder
- `TPT_Products/` — Legacy output folder
- `Covers/` — Generated cover images
- `Thumbnails/` — Generated thumbnail images
- `outputs/` — Alternative output folder
- `dist/` — Distribution builds
