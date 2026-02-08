# 🚀 Quick Start Guide

Get your first TpT product generated in **5 minutes**!

## Step 1: Install Dependencies (30 seconds)

```bash
pip install -r requirements.txt
```

This installs:
- **Pillow** - Image processing
- **reportlab** - PDF generation

## Step 2: Verify Setup (30 seconds)

```bash
python3 test_system.py
```

You should see:
```
✓ Global config loaded
✓ Brown Bear theme loaded
✓ Icon folder found: 12 PNG icons
✓ Test PDF created
✓ All Tests Complete
```

## Step 3: Generate Your First Product (1 minute)

```bash
python3 generators/matching_cards.py
```

**Output**: `output/matching/brown_bear_matching_level1_color.pdf`

This creates a matching activity with:
- 5 vocabulary words (Brown bear, Blue horse, Red bird, etc.)
- Professional rounded borders
- Level 1 color coding (Orange)
- Print-ready 300 DPI quality

## What You Get

The generated PDF includes:
- **Target boxes** (left column) - Navy borders, 1.0" × 1.5"
- **Matching boxes** (right column) - Orange borders, 1.5" square
- **Brown Bear icons** - Automatically loaded and centered
- **Professional styling** - Rounded corners, proper spacing

## Next Steps

### Customize Vocabulary
Edit `generators/matching_cards.py`:

```python
# Change this line:
vocab = ["Brown bear", "Blue horse", "Red bird", "Yellow duck", "Green frog"]

# To your own words:
vocab = ["cat", "dog", "fish", "bird", "mouse"]
```

### Generate Different Levels

```python
# Generate Level 2 (with distractors)
output_path = generator.generate_level_page(2, vocab, "color")

# Generate Level 3
output_path = generator.generate_level_page(3, vocab, "color")

# Generate Level 4
output_path = generator.generate_level_page(4, vocab, "color")
```

### Create Black & White Version

```python
# Generate B&W version
output_path = generator.generate_level_page(1, vocab, "bw")
```

## Troubleshooting

### "Icon not found" warnings
Make sure icon names match exactly with files in:
`assets/themes/brown_bear/icons/`

Available icons:
- `Brown bear`, `Blue horse`, `Red bird`, `Yellow duck`, `Green frog`
- `Black sheep`, `White dog`, `Purple cat`
- `goldfish`, `children`, `teacher`, `see`

### "Config not found" errors
Ensure you're running from the project root:
```bash
cd /path/to/small-wins-automation
python3 generators/matching_cards.py
```

### PDF won't open
Check file size: `ls -lh output/matching/*.pdf`

Should be ~10-20 KB. If 0 KB, check error messages in terminal.

## File Locations

- **Generated PDFs**: `output/matching/`
- **Icons**: `assets/themes/brown_bear/icons/`
- **Configuration**: `themes/brown_bear.json`
- **Global settings**: `themes/global_config.json`

## Need Help?

1. Check the main [README.md](README.md) for full documentation
2. Review design specs in `/design/product_specs/matching.md`
3. Run test suite: `python3 test_system.py`
4. Create an issue in GitHub

---

**You're ready to generate TpT resources!** 🎉

Next: Explore other generators in the `/generators` directory or customize the matching generator for your specific needs.
