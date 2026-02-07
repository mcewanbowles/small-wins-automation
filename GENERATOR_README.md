# Small Wins Studio — Generator System

Python-based automation system for generating TpT (Teachers Pay Teachers) educational resources.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run a Generator

```bash
# Generate all matching levels for Brown Bear theme
python -m generators.matching --theme brown_bear --output exports/

# Generate only Level 1
python -m generators.matching --theme brown_bear --output exports/ --level 1
```

### 3. View Generated Files

Generated PDFs will be in `exports/matching/`:
- `brown_bear_matching_level1_color.pdf` - Level 1 color version
- `brown_bear_matching_level1_bw.pdf` - Level 1 black & white version
- `brown_bear_matching_level2_color.pdf` - Level 2 color version
- (continues for all 4 levels)
- `brown_bear_matching_cutouts.pdf` - Cutout pieces
- `brown_bear_matching_storage_labels.pdf` - Storage labels

## 📁 Project Structure

```
small-wins-automation/
├── generators/              # Generator scripts
│   ├── __init__.py
│   ├── base.py             # Base generator class
│   ├── pdf_utils.py        # PDF layout utilities
│   ├── matching.py         # Matching activity generator
│   ├── find_cover.py       # (TODO) Find & Cover generator
│   └── aac.py              # (TODO) AAC generator
├── design/                  # Design specifications
│   ├── Design-Constitution.md
│   ├── Master-Fix-File.md
│   └── Master-Product-Specification.md
├── themes/                  # Theme configurations
│   ├── brown_bear.json
│   └── global_config.json
├── assets/                  # Images and icons
│   ├── themes/
│   │   └── brown_bear/
│   │       ├── icons/      # Colored icons
│   │       ├── real_images/# Real photos
│   │       └── colouring/  # B&W outlines
│   ├── branding/           # Logos
│   └── global/             # Templates
├── exports/                 # Generated outputs (gitignored)
└── requirements.txt         # Python dependencies
```

## 🎨 Available Generators

### Matching Activities (`generators.matching`)
Generates differentiated matching activities with 4 levels:

- **Level 1 (Errorless)** - Orange accent stripe
  - Identical picture-to-picture matching
  - No distractors (errorless learning)
  - Watermarks in target boxes

- **Level 2 (Distractors)** - Blue accent stripe
  - Picture-to-picture with distractors
  - Increasing difficulty

- **Level 3 (Picture + Text)** - Green accent stripe
  - Bidirectional matching (picture→word and word→picture)
  - Multiple orientations

- **Level 4 (Generalisation)** - Purple accent stripe
  - Cross-representation (icon↔photo)
  - Hardest distractors

**Usage:**
```bash
python -m generators.matching --theme brown_bear --output exports/
```

### Find & Cover (TODO)
_Coming soon_

### AAC Book & Board (TODO)
_Coming soon_

## 🎯 Product Specifications

All generators follow the **Design Constitution** and **Master Product Specification**:

- **Page Size:** US Letter (8.5" × 11")
- **Margins:** 0.5" on all sides
- **Border:** Rounded rectangle (0.12" radius)
- **Header:** Pack code, page numbers, "Small Wins Studio" branding
- **Footer:** Copyright notice and PCS license
- **Accent Stripe:** Level-coded color with title/subtitle

### Level Color System (Universal)

| Level | Color | Hex | Name |
|-------|-------|-----|------|
| L1 | 🟠 Orange | #F4B400 | Errorless |
| L2 | 🔵 Blue | #4285F4 | Distractors |
| L3 | 🟢 Green | #34A853 | Picture + Text |
| L4 | 🟣 Purple | #8C06F2 | Generalisation |

## 🛠️ Development

### Adding a New Theme

1. Create theme config: `themes/your_theme.json`
2. Add icons to `assets/themes/your_theme/icons/`
3. Run generator: `python -m generators.matching --theme your_theme --output exports/`

### Theme Configuration Format

```json
{
  "theme_id": "brown_bear",
  "theme_name": "Brown Bear, Brown Bear",
  "year": 2026,
  "fonts": {
    "primary": "Arial Rounded MT Bold",
    "secondary": "Arial"
  },
  "colours": {
    "primary": "#F28CC8",
    "secondary": "#8C06F2",
    "accent": "#F4B400"
  },
  "fringe_icons": {
    "bear": "bear.png",
    "bird": "bird.png"
  }
}
```

### Creating a New Generator

1. Extend `BaseGenerator` from `generators/base.py`
2. Implement product-specific layout logic
3. Follow Design Constitution standards
4. Add command-line interface with `argparse`

Example:
```python
from generators.base import BaseGenerator

class MyGenerator(BaseGenerator):
    def generate(self):
        # Your generation logic here
        pass
```

## 📋 Design Standards

### Page Layout
- All content inside rounded border
- Pack code and page numbers above border
- Copyright footer inside border
- Accent stripe at top with rounded corners

### Icon Standards
- Target images: 1.4" box
- Matching boxes: 1.0"–1.15" box
- Icons centered with minimal padding
- Velcro dots centered in boxes

### Watermarks (Level 1 Only)
- 20–30% opacity
- 70–80% of box size
- Centered behind velcro dot

### File Naming
- Pattern: `{theme}_{product}_level{X}_{variant}.pdf`
- Example: `brown_bear_matching_level1_color.pdf`

## 📦 Output Files

Each product generates:
1. Activity pages (Color + B&W) for each level
2. Cutout pieces page
3. Storage labels page

Future outputs (per Master Product Specification):
- Cover page
- Quick Start instructions
- Support tips
- TOU + Credits
- Thumbnails and preview images

## 🔍 Troubleshooting

### Icons Not Found
Ensure icons exist in `assets/themes/{theme}/icons/` and are referenced correctly in the theme JSON.

### PDF Generation Errors
Check that reportlab and Pillow are installed:
```bash
pip install -r requirements.txt
```

### Output Directory Issues
The generator creates the output directory automatically. Ensure you have write permissions.

## 📚 Documentation

- [Design Constitution](design/Design-Constitution.md) - Visual and structural standards
- [Master Fix File](design/Master-Fix-File.md) - Universal corrections
- [Master Product Specification](design/Master-Product-Specification.md) - Complete product requirements
- [Getting Started](docs/GETTING_STARTED.md) - Workflow and next steps

## 🎉 Next Steps

1. ✅ Matching generator is working
2. ⏳ Add Find & Cover generator
3. ⏳ Add AAC generator
4. ⏳ Implement cover page generation
5. ⏳ Add Quick Start instructions
6. ⏳ Generate thumbnails and previews
7. ⏳ Create ZIP packaging

## 📄 License

© 2025 Small Wins Studio. All rights reserved.
PCS® symbols used with active PCS Maker Personal License.
