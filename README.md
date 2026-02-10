
# small-wins-automation
Automated TpT resource generators for Small Wins Studio

## Template Placeholders

The Quick Start Guide templates use the following placeholders that should be replaced when generating specific products:

### Basic Placeholders
- `{{LEVEL}}` - Level number (e.g., "1", "2", "3")
- `{{DESCRIPTION}}` - Level description (e.g., "Errorless matching to boards", "Match with 2 choices")
- `{{LEVEL_FULL}}` - Full level for subtitle (e.g., "Level 1 (Errorless)", "Level 2 (2 Choices)")
- `{{NUM_BOARDS}}` - Number of boards (e.g., "15", "20", "25")
- `{{NUM_LEVELS}}` - Number of levels in the series (e.g., "5", "6")

### Content Block Placeholders
- `{{DESCRIPTION_FULL}}` - Complete description content for "What this resource is" section
- `{{STUDENT_ROUTINE}}` - Complete student routine steps (typically an ordered list)
- `{{TROUBLESHOOTING}}` - Complete troubleshooting tips (typically a bulleted list)
- `{{NEXT_STEPS}}` - Complete next steps content (typically wrapped in a content-box)
- `{{QUICK_GAMES}}` - Complete quick games list (typically a bulleted list)
=======
# Small Wins Automation

Automated TpT (Teachers Pay Teachers) resource generator for Small Wins Studio. This Python automation system generates 14 different printable SPED (Special Education) resources following strict design rules for accessibility and consistency.

## 🎯 Current Status

### ✅ Working Features
- **Matching Generator** - Creates differentiated matching activities (Levels 1-4)
- **Theme Support** - Brown Bear theme fully configured with icons
- **PDF Generation** - 300 DPI print-quality output
- **Design System** - Rounded borders, proper colors, consistent branding

### 📋 What's Generated
Each activity includes:
1. Color PDF with activity pages
2. Black & White PDF variant
3. Thumbnails (1000×1000px)
4. Preview watermarked PDFs
5. Cover page
6. Quick Start instructions
7. Terms of Use and Credits
8. ZIP file ready for TpT upload

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/mcewanbowles/small-wins-automation.git
cd small-wins-automation
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

### Running the Generators

#### Test the System
```bash
python3 test_system.py
```

This validates:
- Config files load correctly
- Images are accessible
- PDF generation works

#### Generate Matching Activities
```bash
python3 generators/matching_cards.py
```

Output will be in: `output/matching/brown_bear_matching_level1_color.pdf`

## 📁 Project Structure

```
small-wins-automation/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── test_system.py              # System validation tests
│
├── assets/                     # All assets and resources
│   ├── branding/              # Small Wins Studio logos
│   ├── global/                # Shared templates (TOU, Credits)
│   └── themes/                # Theme-specific assets
│       └── brown_bear/        # Brown Bear theme
│           └── icons/         # Full-color theme images (12 PNG files)
│
├── design/                     # Design specifications
│   ├── Design-Constitution.md # Universal design standards
│   ├── Master-Product-Specification.md
│   └── product_specs/
│       └── matching.md        # Matching generator specs
│
├── docs/                      # Additional documentation
│
├── generators/                # Generator modules
│   ├── __init__.py
│   ├── matching_cards.py     # ✅ WORKING - Matching activities
│   ├── find_cover.py         # 🚧 Planned
│   └── aac_book_board.py     # 🚧 Planned
│
├── themes/                    # Theme configurations (JSON)
│   ├── brown_bear.json       # Brown Bear theme config
│   └── global_config.json    # Global settings (colors, branding)
│
└── utils/                     # Shared utilities
    ├── __init__.py
    ├── config.py             # Config loading
    ├── image_loader.py       # Image processing
    └── pdf_builder.py        # PDF generation
```

## 🎨 Design Philosophy

### SPED Design Rules
All generators follow strict SPED accessibility guidelines:

1. **High Contrast** - Navy borders (#1E3A5F), white backgrounds
2. **Large Images** - Icons 0.8-1.6 inches, easy to see
3. **Minimal Clutter** - Clean layouts, predictable structure
4. **Consistent Branding** - Small Wins Studio colors and logos
5. **300 DPI Output** - Print-quality PDFs
6. **Rounded Borders** - 0.12" radius for softer appearance

### Level Color Coding
- **Level 1** (Errorless): Orange (#F4B400)
- **Level 2** (Easy): Blue (#4285F4)
- **Level 3** (Medium): Green (#34A853)
- **Level 4** (Hard): Purple (#8C06F2)

## 📚 Available Generators

### ✅ Matching Cards (WORKING)
- **Location**: `generators/matching_cards.py`
- **Spec**: `design/product_specs/matching.md`
- **Layout**: 5×2 grid (target boxes + matching boxes)
- **Levels**: 1-4 with differentiation
- **Output**: Color PDFs with proper branding

### 🚧 Planned Generators
1. Find & Cover (4×4 grids)
2. AAC Boards/Strips
3. Bingo
4. Sequencing
5. Coloring Strips
6. Coloring Sheets (Full Page)
7. Sorting Cards
8. Sentence Strips
9. Yes/No Questions
10. WH Questions
11. Story Maps
12. Color Questions
13. Word Search

## 🔧 Configuration

### Theme Configuration
Themes are defined in JSON files in `/themes/`:

```json
{
  "name": "Brown Bear, Brown Bear, What Do You See?",
  "colors": {
    "primary": "#F28CC8",
    "secondary": "#8C06F2",
    "accent": "#F4B400"
  },
  "fonts": {
    "primary": "Arial Rounded MT Bold",
    "fallback": "Arial"
  }
}
```

### Global Configuration
Global settings in `/themes/global_config.json`:

- Level colors
- Small Wins Studio branding
- Typography standards
- Page layout specifications

## 🧪 Testing

Run the test suite:
```bash
python3 test_system.py
```

Expected output:
```
✓ Global config loaded
✓ Brown Bear theme loaded
✓ Icon folder found: 12 PNG icons
✓ Test PDF created: 1.7 KB
✓ All Tests Complete
```

## 📖 Documentation

Comprehensive specifications in `/design/`:

- **Design-Constitution.md** - Universal design standards (10 sections)
- **Master-Product-Specification.md** - Overall product requirements
- **product_specs/matching.md** - Matching generator detailed specs

## 🤝 Contributing

This is a private automation system for Small Wins Studio. For questions or improvements, contact the repository owner.

## 📄 License

Copyright © 2024 Small Wins Studio. All rights reserved.

## 🔮 Roadmap

### Short Term
- [ ] Add watermark support for Level 1
- [ ] Implement distractor logic for Levels 2-4
- [ ] Create cutout page generator (4×5 grid)
- [ ] Build storage labels generator

### Medium Term
- [ ] Cover page generator
- [ ] Preview/thumbnail generators
- [ ] B&W (black and white) mode
- [ ] ZIP packaging for TpT upload

### Long Term
- [ ] Complete all 14 generator types
- [ ] Multi-theme support
- [ ] Automated testing suite
- [ ] Batch generation workflows

## 📞 Support

For issues or questions about this automation system, please create an issue in the GitHub repository or contact Small Wins Studio directly.

---

**Made with ❤️ by Small Wins Studio**
