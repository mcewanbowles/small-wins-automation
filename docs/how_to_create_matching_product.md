# How to Create a New Matching Product

This guide explains how to duplicate the Matching Activity product for a new theme.

## Quick Start

To create a new matching product (e.g., "Polar Bear Matching"):

1. **Prepare 12 icons** for your theme
2. **Copy the theme configuration** template
3. **Run the generator** with your theme settings
4. **Review and adjust** as needed

---

## Step-by-Step Guide

### Step 1: Prepare Your Icons

You need **12 high-quality icons** related to your theme.

#### Icon Requirements:
- **Format:** PNG with transparent background
- **Size:** Minimum 500×500 pixels (larger is better)
- **Style:** Consistent across all icons
- **Content:** Clear, recognizable images suitable for special education students
- **Naming:** Use descriptive filenames (e.g., `polar_bear.png`, `seal.png`)

#### Create Icon Directory:
```bash
mkdir -p /assets/themes/[your_theme]/icons/
```

Place all 12 icon PNG files in this directory.

---

### Step 2: Create Theme Configuration

1. **Copy the template:**
```bash
cp /config/theme_template.json /config/[your_theme]_theme.json
```

2. **Edit the configuration:**

Open `/config/[your_theme]_theme.json` and update:

```json
{
  "theme": {
    "name": "Your Theme Name",
    "code": "YT01",           # Unique 4-character code
    "description": "Description of your theme"
  },
  "icons": [
    {
      "filename": "icon1.png",
      "display_name": "Icon 1 Name",
      "description": "Description"
    },
    // ... repeat for all 12 icons
  ],
  "paths": {
    "icons_dir": "/assets/themes/your_theme/icons/",
    "output_dir": "/samples/your_theme/matching/"
  },
  "output": {
    "color_filename": "your_theme_matching_color.pdf",
    "bw_filename": "your_theme_matching_bw.pdf"
  }
}
```

#### Pack Code Guidelines:
- Use 4 characters (2 letters + 2 numbers)
- First letters represent theme (e.g., BB = Brown Bear, PB = Polar Bear)
- Numbers represent product type (e.g., 03 = Matching)
- Examples: BB03, PB03, PA03

---

### Step 3: Update the Generator Script

The current generator (`generate_matching_constitution.py`) is hardcoded for Brown Bear. To make it work for your theme:

#### Option A: Quick Modification (for one-off use)

Edit `generate_matching_constitution.py`:

1. **Line ~24-26:** Update theme name and paths:
```python
THEME_NAME = "Your Theme Name"
PACK_CODE = "YT03"
ICONS_DIR = "/assets/themes/your_theme/icons/"
OUTPUT_DIR = "/samples/your_theme/matching/"
```

2. **Line ~29-41:** Update icon list:
```python
ICON_FILES = {
    "Icon 1 Name": "icon1.png",
    "Icon 2 Name": "icon2.png",
    # ... all 12 icons
}
```

#### Option B: Config-Driven Approach (recommended for multiple themes)

Create a new generator that reads from the JSON config:

```python
import json

# Load theme configuration
with open('/config/your_theme_theme.json', 'r') as f:
    config = json.load(f)

THEME_NAME = config['theme']['name']
PACK_CODE = config['theme']['code']
ICONS_DIR = config['paths']['icons_dir']
OUTPUT_DIR = config['paths']['output_dir']

# Build icon dictionary from config
ICON_FILES = {
    icon['display_name']: icon['filename']
    for icon in config['icons']
}
```

---

### Step 4: Create Output Directory

```bash
mkdir -p /samples/[your_theme]/matching/
```

---

### Step 5: Run the Generator

```bash
python generate_matching_constitution.py
```

Or if you created a config-driven version:

```bash
python generate_matching_from_config.py --config /config/your_theme_theme.json
```

This will generate:
- `your_theme_matching_color.pdf` (full color, 60 pages)
- `your_theme_matching_bw.pdf` (grayscale, 60 pages)

---

### Step 6: Review the Output

Check the generated PDFs:

1. **Pages 1-15:** Level 1 (Orange stripe)
   - 12 activity pages with watermarks
   - 2 cutout pages (60 pieces)
   - 1 storage labels page

2. **Pages 16-30:** Level 2 (Blue stripe)
3. **Pages 31-45:** Level 3 (Green stripe)
4. **Pages 46-60:** Level 4 (Purple stripe)

**What to check:**
- ✅ All icons load correctly
- ✅ Icon names display properly
- ✅ Level colors are correct (Orange, Blue, Green, Purple)
- ✅ Title shows your theme name
- ✅ Pack code is correct
- ✅ Cutouts have 5 copies of each icon
- ✅ Storage labels show all 12 icons
- ✅ BW version is fully grayscale

---

## Customization Options

### Adjust Colors

To use different level colors, edit the `get_level_color()` function:

```python
LEVEL_COLORS = {
    1: '#F4A259',  # Orange
    2: '#4A90E2',  # Blue
    3: '#7BC47F',  # Green
    4: '#9B59B6'   # Purple
}
```

### Adjust Sizing

Key size variables in the generator:

```python
# Activity boxes
BOX_SIZE = 1.28 * inch

# Target box
TARGET_SIZE = 0.72 * inch

# Column spacing
COLUMN_GAP = 1.45 * inch

# Row spacing
ROW_SPACING = 0.16 * inch
```

### Adjust Fonts

```python
# Title font
title_font = 'Comic-Sans-MS-Bold'
title_size = 36

# Subtitle font
subtitle_font = 'Comic-Sans-MS'
subtitle_size = 28
```

---

## Troubleshooting

### Icons Don't Load
- Check icon filenames match exactly (case-sensitive)
- Verify icons are in the correct directory
- Ensure icons are PNG format

### Wrong Theme Name Appears
- Update `THEME_NAME` variable in generator
- Check theme configuration JSON

### Colors Don't Match
- Verify hex color codes in `LEVEL_COLORS`
- Check BW mode conversion is working

### PDF Generation Fails
- Ensure reportlab is installed: `pip install reportlab`
- Check PIL/Pillow is installed: `pip install Pillow`
- Verify all paths exist and are writable

---

## Example: Creating "Polar Bear" Matching

Here's a complete example:

```bash
# 1. Create directories
mkdir -p /assets/themes/polar_bear/icons/
mkdir -p /samples/polar_bear/matching/

# 2. Add 12 polar bear-themed PNG icons to /assets/themes/polar_bear/icons/

# 3. Create config
cp /config/theme_template.json /config/polar_bear_theme.json

# 4. Edit config with polar bear icons:
#    - arctic_fox.png
#    - beluga_whale.png
#    - harp_seal.png
#    - narwhal.png
#    - penguin.png
#    - polar_bear.png
#    - reindeer.png
#    - snowy_owl.png
#    - walrus.png
#    - arctic_hare.png
#    - orca.png
#    - igloo.png

# 5. Update generator or create config-driven version

# 6. Run generator
python generate_matching_constitution.py

# 7. Find output PDFs in /samples/polar_bear/matching/
```

---

## Best Practices

1. **Consistent Icon Style:** Use icons from the same artist or style
2. **High Resolution:** Start with larger icons (they'll be scaled down)
3. **Clear Images:** Icons should be easily recognizable
4. **Test Print:** Print a few pages to check quality
5. **Version Control:** Keep theme configs in git
6. **Naming Convention:** Use consistent, descriptive names
7. **Documentation:** Note any theme-specific customizations

---

## Next Steps

- Create additional themes (Panda, Zoo Animals, Farm Animals, etc.)
- Consider automating with a command-line tool
- Build a web interface for theme configuration
- Create a template gallery with examples
- Share templates with other educators

---

## Support

For questions or issues:
1. Review the Product Specification: `/templates/matching_product_spec.md`
2. Check the Design System: `/docs/design_system.md`
3. Examine the Brown Bear example: `/config/brown_bear_theme.json`
4. Open an issue in the repository

---

## License

© 2025 Small Wins Studio  
PCS® symbols used with active PCS Maker Personal License
