# Brown Bear Matching Output Directory

This directory contains generated PDF files for the Brown Bear matching activities.

## Generated Files

When you run `./generate_all.sh` or `python3 generate_matching_constitution.py`, the following files will be created here:

### Main PDFs (60 pages each)
- `brown_bear_matching_color.pdf` - Full color version
- `brown_bear_matching_bw.pdf` - Black & white version

### Individual Level PDFs (15 pages each)
- `brown_bear_matching_level1_color.pdf`
- `brown_bear_matching_level1_bw.pdf`
- `brown_bear_matching_level1_preview.pdf` (with watermark)
- `brown_bear_matching_level2_color.pdf`
- `brown_bear_matching_level2_bw.pdf`
- `brown_bear_matching_level2_preview.pdf` (with watermark)
- `brown_bear_matching_level3_color.pdf`
- `brown_bear_matching_level3_bw.pdf`
- `brown_bear_matching_level3_preview.pdf` (with watermark)
- `brown_bear_matching_level4_color.pdf`
- `brown_bear_matching_level4_bw.pdf`
- `brown_bear_matching_level4_preview.pdf` (with watermark)

### Supporting Materials
- `brown_bear_matching_quick_start.pdf`
- `small_wins_tpt_documentation.pdf`

## Note

**PDFs are not committed to Git** (excluded by `.gitignore`).

To generate the PDFs, run:
```bash
./generate_all.sh
```

Or generate just the matching activities:
```bash
python3 generate_matching_constitution.py
```
