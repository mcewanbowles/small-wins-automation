# Small Wins Studio - Matching Activity System

A comprehensive system for creating themed matching activities for special education students.

## What This System Produces

Each matching product includes:
- **60-page PDF** with 4 difficulty levels
- **240 matching pieces** (60 per level)
- **Professional storage labels** for classroom organization
- **Color and black & white versions**
- **Level-specific color coding** for easy teacher identification

## System Components

### 📋 Templates
- `/templates/matching_product_spec.md` - Complete product specification
- `/config/theme_template.json` - Theme configuration template

### 📚 Documentation
- `/docs/how_to_create_matching_product.md` - Step-by-step creation guide
- `/docs/design_system.md` - Visual design standards and specifications

### 🎨 Example Configuration
- `/config/brown_bear_theme.json` - Working Brown Bear example

### 🛠️ Generator
- `generate_matching_constitution.py` - Python generator script

## Quick Start

### To Create a New Theme:

1. **Prepare 12 high-quality PNG icons** for your theme
2. **Copy the theme template:**
   ```bash
   cp config/theme_template.json config/your_theme.json
   ```
3. **Edit configuration** with your theme details
4. **Update generator** or create config-driven version
5. **Run generator** to create PDFs

See `/docs/how_to_create_matching_product.md` for detailed instructions.

## Product Structure

### Each Level Package (15 pages):
- **12 Activity Pages:** One per icon with appropriate difficulty
- **2 Cutout Pages:** 60 matching pieces (5 copies of each icon)
- **1 Storage Labels Page:** Professional organization labels

### Level Difficulty System:
- **Level 1 (Orange):** Errorless - 5 targets, 0 distractors, watermarks
- **Level 2 (Blue):** Easy - 4 targets, 1 distractor
- **Level 3 (Green):** Medium - 3 targets, 2 distractors
- **Level 4 (Purple):** Hard - 1 target, 4 distractors

## Design Features

✅ **SPED-Friendly:** High contrast, clear layouts, friendly fonts  
✅ **Color-Coded Levels:** Quick visual identification for teachers  
✅ **Professional:** Consistent design across all themes  
✅ **Classroom-Ready:** Guillotine-friendly cutouts, storage labels  
✅ **Flexible:** Can sell levels separately or as package  
✅ **Print-Optimized:** Color and grayscale versions included  

## File Structure

```
├── config/
│   ├── theme_template.json          # Template for new themes
│   └── brown_bear_theme.json        # Example configuration
├── docs/
│   ├── how_to_create_matching_product.md
│   └── design_system.md
├── templates/
│   └── matching_product_spec.md     # Complete specification
├── generate_matching_constitution.py # Generator script
├── assets/
│   └── themes/
│       └── [theme_name]/
│           └── icons/               # Theme-specific icons
└── samples/
    └── [theme_name]/
        └── matching/                # Generated PDFs
```

## Technologies

- **Python 3.x**
- **ReportLab** - PDF generation
- **PIL/Pillow** - Image processing

## Getting Started

```bash
# Install dependencies
pip install reportlab Pillow

# Generate Brown Bear example
python generate_matching_constitution.py

# Find output in samples/brown_bear/matching/
```

## Creating Your First Product

1. Read: `/docs/how_to_create_matching_product.md`
2. Review: `/templates/matching_product_spec.md`
3. Study: `/config/brown_bear_theme.json` example
4. Create: Your theme configuration
5. Generate: Your matching product

## Theme Ideas

- Polar Bear, Polar Bear
- Panda Bear, Panda Bear
- Zoo Animals
- Farm Animals
- Ocean Creatures
- Dinosaurs
- Vehicles
- Seasons
- Emotions
- Colors and Shapes

## Customization

All visual aspects can be customized:
- Colors (level-based and standard)
- Fonts and sizes
- Spacing and layout
- Box dimensions
- Border styles

See `/docs/design_system.md` for specifications.

## Support Files

### For Teachers:
- Storage labels with images
- Level-coded pages (Orange/Blue/Green/Purple)
- Both color and BW printing options

### For Developers:
- Complete design system documentation
- JSON configuration format
- Python generator with utilities
- Template files for duplication

## License

© 2025 Small Wins Studio  
PCS® symbols used with active PCS Maker Personal License

## Contributing

To add new themes or improve the system:
1. Follow the design system specifications
2. Test with actual icons and generation
3. Ensure both color and BW modes work
4. Update documentation as needed

## Version

Current: v1.0 (February 2026)
- Initial system based on Brown Bear Matching
- Level-based color coding
- Professional storage labels
- Complete documentation suite
