# Exports Directory

This directory is used by `generate_all.sh` for organizing exported products.

## Purpose

When running `./generate_all.sh`, this directory is used as a staging area for complete product packages.

## Structure

```
exports/
└── {theme}_matching_complete/
    └── (organized output files)
```

For example:
```
exports/
└── brown_bear_matching_complete/
```

## Note

This directory is in `.gitignore` and its contents are not committed to Git.

The actual PDF outputs are in:
- `samples/brown_bear/matching/` - Main product PDFs
- `review_pdfs/` - Marketing and review materials
