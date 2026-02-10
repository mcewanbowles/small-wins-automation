# Review PDFs Output Directory

This directory contains generated cover pages, freebie samples, and marketing materials.

## Generated Files

When you run `./generate_all.sh`, the following files will be created here:

### Cover Pages
- `brown_bear_matching_level1_cover.pdf`
- `brown_bear_matching_level2_cover.pdf`
- `brown_bear_matching_level3_cover.pdf`
- `brown_bear_matching_level4_cover.pdf`
- `brown_bear_matching_level5_cover.pdf`

### Marketing Materials
- `brown_bear_matching_freebie.pdf` - Sample for TpT preview

### Quick Start Guides
- `brown_bear_matching_quick_start.pdf`
- `brown_bear_find_cover_quick_start.pdf`

### Documentation
- `small_wins_tpt_documentation.pdf` - Terms of Use & Credits

## Note

**PDFs are not committed to Git** (excluded by `.gitignore`).

To generate all review materials, run:
```bash
./generate_all.sh
```

Or generate specific components:
```bash
python3 generate_cover_page.py
python3 generate_freebie.py
python3 generate_quick_start_professional.py
python3 generate_tpt_documentation.py
```
