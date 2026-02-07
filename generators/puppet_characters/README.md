# Puppet Characters Generator

Generate 5 types of Brown Bear puppet resources from Boardmaker icons with dual-mode output (color + B&W).

## Features

### 5 Puppet Resource Types

1. **Stick Puppets** - Cut and tape handle strips (2×3 grid per page)
2. **Finger Puppets** - Fold tabs for finger insertion (3×2 grid per page)
3. **Velcro Character Cards** - Bold outlines for durability (3×3 grid per page)
4. **Story Mat** - WH prompts (WHO/WHAT/WHERE/WHEN/WHY/HOW) with character strip
5. **Lanyard Characters** - Hole-punch indicators for lanyards (3×2 grid per page)

### Dual-Mode Output

- **Color PDFs** - Full color for lamination
- **B&W PDFs** - Black & white for coloring activities or cost-effective printing

### Professional Features

- ✅ Layout Utilities: `create_page_canvas()` and `add_footer()` for consistent formatting
- ✅ Image Utilities: `scale_image_proportional()` and `center_image_in_box()` for professional image handling
- ✅ Dual-Mode Support: Automatic grayscale conversion for B&W versions
- ✅ Bold Outlines: Added to velcro cards for durability
- ✅ Consistent Branding: Small Wins Studio branding on all pages
- ✅ SPED-Friendly: All resources designed for special education use

## Usage

### Basic Usage

```bash
python generators/puppet_characters/puppet_characters.py \
    --icons_dir "assets/themes/brown_bear/icons" \
    --out_dir "OUTPUT/puppets" \
    --theme "Brown Bear" \
    --brand "Small Wins Studio"
```

### Command Line Arguments

- `--icons_dir` (required): Folder containing character icons (PNG recommended)
- `--out_dir` (required): Output folder for generated PDFs
- `--theme` (required): Theme name (used in titles and filenames)
- `--brand` (optional): Brand name for footer (default: "Small Wins Studio")

### Example with Different Theme

```bash
python generators/puppet_characters/puppet_characters.py \
    --icons_dir "assets/themes/my_theme/icons" \
    --out_dir "OUTPUT/my_theme_puppets" \
    --theme "My Custom Theme"
```

## Output Files

For each mode (color and bw), the generator creates:

```
OUTPUT/puppets/
├── brown_bear_stick_puppets_color.pdf
├── brown_bear_stick_puppets_bw.pdf
├── brown_bear_finger_puppets_color.pdf
├── brown_bear_finger_puppets_bw.pdf
├── brown_bear_velcro_cards_color.pdf
├── brown_bear_velcro_cards_bw.pdf
├── brown_bear_story_mat_color.pdf
├── brown_bear_story_mat_bw.pdf
├── brown_bear_lanyard_characters_color.pdf
└── brown_bear_lanyard_characters_bw.pdf
```

**Total**: 10 PDF files (5 resource types × 2 modes)

## Dependencies

Install required Python packages:

```bash
pip install reportlab pillow
```

## Icon Requirements

- **Format**: PNG files with transparent backgrounds recommended
- **Location**: Organized in a single folder (e.g., `assets/themes/brown_bear/icons/`)
- **Naming**: Filenames become character labels (e.g., `brown_bear.png` → "brown_bear")
- **Supported formats**: .png, .jpg, .jpeg, .webp

## Design Specifications

### Page Layout

- **Page Size**: A4 (210 × 297 mm)
- **Margins**: 12mm on all sides
- **Gutter**: 6mm between cells
- **Font**: Helvetica (system font)

### Resource-Specific Layouts

| Resource Type | Grid Layout | Special Features |
|--------------|-------------|------------------|
| Stick Puppets | 2×3 (6 per page) | Handle strip with dashed tape line |
| Finger Puppets | 3×2 (6 per page) | Left/right fold tabs with dashed line |
| Velcro Cards | 3×3 (9 per page) | Bold border (3pt), character outline (8px) |
| Story Mat | 3×2 prompts + strip | 6 WH question boxes + character strip |
| Lanyard Cards | 3×2 (6 per page) | Hole-punch indicator at top |

### Footer Format

All pages include:
- **Left**: `{Brand} | {Theme} | {MODE} | Print & Go`
- **Right**: `Page {number}`

## Examples

### Stick Puppets
- Character image fills most of cell
- Handle strip (60% width) at bottom
- Dashed line indicates where to tape handle
- Character name label at top

### Finger Puppets
- Character image in upper portion
- Fold tabs on left and right (25% width each)
- Dashed fold line separates image from tabs
- Perfect for interactive storytelling

### Velcro Cards
- 3pt bold border for durability
- 8px black outline added to character images
- Ideal for magnetic boards or velcro surfaces
- Suitable for matching and sequencing activities

### Story Mat
- 6 WH prompt boxes (WHO? WHAT? WHERE? WHEN? WHY? HOW?)
- Character strip shows up to 10 mini icons
- One mat per mode (color/bw)
- Great for comprehension activities

### Lanyard Characters
- Rounded corners for safety
- Hole-punch indicator (4mm radius circle)
- Perfect for character identification
- Wearable for role-play activities

## Educational Uses

### SPED Applications

- **Visual Schedules**: Use lanyard characters for daily routines
- **Story Retelling**: Stick and finger puppets for narrative skills
- **Sequencing**: Velcro cards for ordering events
- **Comprehension**: Story mat for answering WH questions
- **Social Skills**: Puppet play for communication practice

### Classroom Activities

- Reading centers
- Small group instruction
- Independent practice stations
- Literacy centers
- Drama and role-play

## Customization

The generator automatically:
- Loads all images from the specified folder
- Sorts alphabetically by filename
- Scales images proportionally to fit cells
- Centers images within allocated space
- Converts to grayscale for B&W mode
- Adds outlines where specified (velcro cards)

## Troubleshooting

### Common Issues

**"No module named 'PIL'"**
- Solution: Install Pillow with `pip install pillow`

**"icons_dir not found"**
- Solution: Check the path to your icons folder
- Ensure it exists and contains image files

**"No image files found"**
- Solution: Ensure folder contains .png, .jpg, .jpeg, or .webp files
- Check file extensions are lowercase

**Images too small/large**
- The generator automatically scales images proportionally
- Original aspect ratio is preserved
- Images are centered in their cells

## Contributing

To add new puppet resource types:

1. Add a new generation function (e.g., `generate_new_type()`)
2. Follow the existing pattern with canvas, assets, theme, brand, mode
3. Use utility functions: `scale_image_proportional()`, `center_image_in_box()`
4. Add the new type to `generate_puppet_characters_for_mode()`

## License

Part of the Small Wins Studio TPT resource automation suite.

## Support

For issues or questions about this generator, please refer to the main repository documentation.
