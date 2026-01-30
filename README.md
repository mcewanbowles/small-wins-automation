# Small Wins Automation - SPED Resource Generator

Automated TpT (Teachers Pay Teachers) resource generators for Small Wins Studio. This Python automation system generates 14 different printable resources for special education (SPED) following strict accessibility and design guidelines.

## Features

- **14 Different Resource Types**: Counting Mats, Matching Cards, Bingo, Sequencing, Coloring Strips, Coloring Sheets, Find & Cover, Sorting Cards, Sentence Strips (AAC), Yes/No Questions, WH Questions, Story Maps, Color Questions, Word Search, and Storage Labels
- **SPED Design Compliance**: Large images, high contrast, minimal clutter, predictable layouts, consistent borders and footers
- **Enhanced Layout Engine**: Precise grid positioning, consistent spacing, and optional visual effects (drop shadows)
- **300 DPI Output**: High-quality PDF files ready for printing
- **Differentiation Levels**: Support for multiple difficulty levels (visual cues, progressive complexity)
- **Theme-Agnostic**: Reusable generators that work with any theme by swapping images and text
- **Modular Architecture**: Shared utilities for borders, fonts, scaling, centering, image loading, and PDF export
- **Storage Label Support**: All generators can create companion organization labels

## Installation

1. Clone this repository:
```bash
git clone https://github.com/mcewanbowles/small-wins-automation.git
cd small-wins-automation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
small-wins-automation/
├── generators/          # 14 resource generators
│   ├── counting_mats.py
│   ├── matching_cards.py
│   ├── bingo.py
│   ├── sequencing.py
│   ├── coloring_strips.py
│   ├── coloring_sheets.py
│   ├── find_cover.py
│   ├── sorting_cards.py
│   ├── sentence_strips.py
│   ├── yes_no_questions.py
│   ├── wh_questions.py
│   ├── story_maps.py
│   ├── color_questions.py
│   ├── word_search.py
│   └── storage_labels.py
├── utils/              # Shared utilities (16 modules)
│   ├── config.py       # SPED design rules and constants
│   ├── fonts.py        # Font management
│   ├── image_loader.py # Image loading from 3 folders
│   ├── image_utils.py  # Scaling, centering, transparency
│   ├── layout.py       # Borders, footers, spacing
│   ├── pdf_export.py   # 300 DPI PDF generation
│   ├── draw_helpers.py # Modular drawing functions (NEW)
│   ├── grid_layout.py  # Grid calculations
│   ├── pdf_builder.py  # High-level PDF building
│   ├── text_renderer.py# Accessible text rendering
│   ├── file_naming.py  # Standardized naming
│   ├── theme_loader.py # Theme configuration
│   ├── differentiation.py # Level management
│   └── storage_label_helper.py # Label generation
├── images/             # Full-color theme images
├── Colour_images/      # Black-and-white outline images
├── aac_images/         # AAC/PCS-style symbols
├── examples/           # Example usage scripts
└── output/             # Generated PDF files

```

## Modular Helper Architecture

The matching cards generator (and future generators) use a modular helper system from `utils/draw_helpers.py` for clean, maintainable code:

### Helper Functions

- **`calculate_cell_rect()`** - Calculate grid cell bounding boxes with consistent spacing
- **`scale_image_to_fit()`** - Scale images proportionally with minimal padding (5-10px)
- **`draw_card_background()`** - Draw styled card backgrounds with borders, corner radius, and optional shadows
- **`fit_text_to_width()`** - Auto-shrink font size to fit text within width limits
- **`draw_page_number()`** - Add page numbers (bottom-right, inside border)
- **`draw_copyright_footer()`** - Add copyright and branding line (bottom-center)
- **`draw_text_centered_in_rect()`** - Center and auto-size text within rectangles
- **`create_placeholder_image()`** - Generate consistent placeholders for missing images

### Benefits

- **Clean Code**: Generators focus on data preparation, not drawing details
- **Reusable**: Same helpers work across all generators
- **Consistent**: Same visual style across all resources
- **Maintainable**: Changes to layout logic in one place
- **Testable**: Helper functions can be tested independently

### Example Usage

```python
from utils.draw_helpers import calculate_cell_rect, scale_image_to_fit

# Calculate grid positions
cells = calculate_cell_rect(
    page_width=2550, page_height=3300,
    rows=2, cols=3, padding=20, margin=50
)

# Scale and position image
scaled_img, x, y = scale_image_to_fit(
    image, cells[0], padding=5
)
```

## Image Folders

The system uses three dedicated image folders:

1. **`images/`** - Full-color theme images for most activities
2. **`Colour_images/`** - Black-and-white outline images for coloring activities
3. **`aac_images/`** - AAC/PCS-style symbols for communication activities

## Quick Start

### Example 1: Generate Counting Mats

```python
from generators import generate_counting_mats_set

# Generate counting mats for numbers 1-10
pages = generate_counting_mats_set(
    image_filenames=['dog.png', 'cat.png', 'bird.png'],
    theme_name='Farm Animals',
    number_range=(1, 10),
    level=1,  # Level 1 includes visual cues
    folder_type='color',
    output_dir='output'
)
```

### Example 2: Generate Matching Cards (4 Differentiation Levels with Enhanced Layout)

The matching card generator now supports 4 SPED-friendly differentiation levels with precise grid layout control:

```python
from generators import generate_matching_cards_set

# Define your items
items = [
    {'image': 'bear', 'label': 'Brown Bear'},
    {'image': 'duck', 'label': 'Yellow Duck'},
    {'image': 'frog', 'label': 'Green Frog'},
]

# Level 1: Identical errorless matching with enhanced layout
pages_l1 = generate_matching_cards_set(
    items=items,
    level=1,
    card_size='large',
    cards_per_page=6,  # 2×3 grid
    output_dir='output',
    theme_name='Brown_Bear',
    add_drop_shadow=False,  # Optional: add subtle drop shadow
    custom_spacing=30  # Optional: customize spacing between cards
)

# Level 2: Outline-to-color matching
pages_l2 = generate_matching_cards_set(items=items, level=2, theme_name='Brown_Bear')

# Level 3: AAC symbol to real image matching
pages_l3 = generate_matching_cards_set(items=items, level=3, theme_name='Brown_Bear')

# Level 4: AAC symbol to text matching with consistent font sizing
pages_l4 = generate_matching_cards_set(items=items, level=4, theme_name='Brown_Bear')

# Generate 3×3 grid with smaller cards
pages_grid = generate_matching_cards_set(
    items=items,
    level=1,
    card_size='standard',  # Smaller cards for denser layout
    cards_per_page=9,  # 3×3 grid
    theme_name='Brown_Bear'
)
```

**Matching Card Levels Explained:**
- **Level 1**: Identical errorless matching - Perfect for beginners, both cards show the same color image
- **Level 2**: Outline-to-color matching - Match black-and-white outline to color image
- **Level 3**: AAC symbol to real image - Match AAC/PCS symbol to real photograph/illustration
- **Level 4**: AAC symbol to text - Match AAC/PCS symbol to written word

**Enhanced Layout Features:**
- ✓ Precise grid positioning using `utils/grid_layout.py` utility
- ✓ Consistent spacing between cards (configurable)
- ✓ Predictable margins around the page
- ✓ Proportional image scaling and centering within cards
- ✓ Minimal padding - images maximized within card boundaries
- ✓ Optional drop shadow effects for visual polish
- ✓ Consistent font sizes across all levels
- ✓ Clean grid alignment (2×3, 3×3, or custom layouts)
- ✓ Copyright and branding footer on every page

### Example 3: Generate Bingo

```python
from generators import generate_bingo_set

# Generate bingo cards with calling cards
pages = generate_bingo_set(
    image_filenames=['img1.png', 'img2.png', 'img3.png', 'img4.png', 'img5.png'],
    num_cards=6,
    grid_size=3,  # 3x3 grid
    folder_type='color',
    theme_name='Animals',
    output_dir='output'
)
```

## Differentiation Levels

All generators support differentiation levels for inclusive teaching:

- **Level 1**: Includes visual cues, labels, and supports (easiest)
- **Level 2**: Removes visual cues and supports (moderate)
- **Level 3**: Increased difficulty with more complex layouts (challenging)

Example:
```python
# Generate with Level 1 (visual cues)
generate_counting_mats_set(..., level=1)

# Generate with Level 2 (no cues)
generate_counting_mats_set(..., level=2)
```

## Storage Labels

Automatically generate companion storage labels for organizing resources. Storage labels feature:
- High-contrast borders for visibility
- Large, clear text for theme and activity names
- Level indicators for differentiation
- Optional icon from the first image

### Quick Example

```python
from generators import generate_matching_cards_set

# Generate matching cards WITH storage label
pages = generate_matching_cards_set(
    items=items,
    level=1,
    theme_name='Brown_Bear',
    output_dir='output',
    include_storage_label=True  # Creates X_LABEL.pdf automatically
)
```

### Manual Label Generation

```python
from utils import generate_storage_label

# Create a standalone storage label
label_path = generate_storage_label(
    theme_name='Brown Bear',
    activity_name='Matching Cards',
    level=1,
    output_path='output/My_Label.pdf',
    label_size='standard'  # 'small', 'standard', or 'large'
)
```

**Naming Convention**: If the main PDF is `Theme_Activity.pdf`, the label will be `Theme_Activity_LABEL.pdf`

**Supported Generators**: All generators can create storage labels by setting `include_storage_label=True`:
- `generate_matching_cards_set(..., include_storage_label=True)`
- `generate_counting_mats_set(..., include_storage_label=True)`
- `generate_bingo_set(..., include_storage_label=True)`

## Build Pipeline - Generate Complete Theme Packs

The `build_theme_pack.py` script generates a complete theme pack with ALL generators from a single theme JSON file.

### Quick Start

```bash
# Generate all resources for brown_bear theme
python build_theme_pack.py brown_bear

# Generate specific generators only
python build_theme_pack.py brown_bear --generators matching,counting,bingo

# Generate without storage labels
python build_theme_pack.py brown_bear --no-labels

# Custom output directory
python build_theme_pack.py brown_bear --output my_output
```

### Available Generators

List all available generators:
```bash
python build_theme_pack.py --list-generators
```

Generators include: `matching`, `counting`, `bingo`, `sequencing`, `find_cover`, `sorting`, `sentence_strips`, `yes_no`, `wh_questions`, `story_maps`, `color_questions`, `coloring_sheets`, `coloring_strips`, `word_search`

### Theme JSON Format

Create custom themes in `/themes/your_theme.json`:

```json
{
  "name": "Your Theme Name",
  "description": "Theme description",
  "items": [
    {
      "image": "item1",
      "label": "Item 1 Label",
      "color": "red"
    },
    {
      "image": "item2",
      "label": "Item 2 Label",
      "color": "blue"
    }
  ]
}
```

Then build the complete pack:
```bash
python build_theme_pack.py your_theme
```

### Build Output

The build pipeline creates organized output:
```
output/
└── brown_bear/
    ├── brown_bear_Matching_Level1_Identical_Errorless.pdf
    ├── brown_bear_Matching_Level1_Identical_Errorless_LABEL.pdf
    ├── brown_bear_Counting_Mats_Level1.pdf
    ├── brown_bear_Counting_Mats_Level1_LABEL.pdf
    ├── brown_bear_Bingo.pdf
    ├── brown_bear_Bingo_LABEL.pdf
    └── ... (all other generators)
```

## All 14 Generators

### 1. Counting Mats
Generate counting mats with visual representations for numbers.
```python
from generators import generate_counting_mats_set
```

### 2. Matching Cards
Create matching card pairs for memory games.
```python
from generators import generate_matching_cards_sheet
```

### 3. Bingo
Generate bingo cards and calling cards.
```python
from generators import generate_bingo_set
```

### 4. Sequencing
Create sequencing cards for teaching order.
```python
from generators import generate_sequencing_set
```

### 5. Coloring Strips
Generate narrow coloring strips for fine motor practice.
```python
from generators import generate_coloring_strips_page
```

### 6. Coloring Sheets
Create full-page coloring sheets.
```python
from generators import generate_coloring_sheets_set
```

### 7. Find & Cover (Enhanced with Modular Helpers)
Generate differentiated "Find and Cover" activity worksheets where students find and cover matching icons.

**Features:**
- Target icon display at top with instructions
- Grid layout (default 4×4) with differentiated content
- Uses modular helpers from `utils/draw_helpers.py`
- Maximum image size with minimal padding (5px)
- Page numbering and copyright footer on every page
- Storage label support

**Differentiation Levels:**
- Level 1: **Errorless** - All icons match the target (perfect for beginners)
- Level 2: **Mixed** - 50% match, 50% distractors (medium difficulty)
- Level 3: **Challenging** - Field of 6 distractors with fewer matches (higher difficulty)
- Level 4: **Cut-and-Paste** - Empty grid with circles for pasting (fine motor practice)

```python
from generators import generate_find_cover_set

# Define target items and all available items
target_items = [
    {'image': 'bear', 'label': 'Brown Bear'},
    {'image': 'duck', 'label': 'Yellow Duck'}
]

all_items = [
    {'image': 'bear', 'label': 'Brown Bear'},
    {'image': 'duck', 'label': 'Yellow Duck'},
    {'image': 'frog', 'label': 'Green Frog'},
    {'image': 'cat', 'label': 'Cat'},
    {'image': 'dog', 'label': 'Dog'}
]

# Generate all 4 levels
for level in range(1, 5):
    pages = generate_find_cover_set(
        target_items=target_items,
        all_items=all_items,
        theme_name='Brown_Bear',
        level=level,
        grid_size=(4, 4),  # 4×4 grid
        folder_type='color',
        sheets_per_target=1,
        include_storage_label=True,
        card_style={'border_width': 2, 'corner_radius': 0, 'shadow': False}
    )
# → Brown_Bear_Find_Cover_Level1_Errorless.pdf
# → Brown_Bear_Find_Cover_Level2_Mixed.pdf
# → Brown_Bear_Find_Cover_Level3_Challenging.pdf
# → Brown_Bear_Find_Cover_Level4_Cut_Paste.pdf
```

### 8. Sorting Cards (Enhanced with Modular Helpers)
Create sorting mats and cut-out sorting cards for categorization activities.

**Features:**
- Sorting mats with category headers and drop zones
- Watermarked answer keys
- Cut-out sorting cards with 3 differentiation levels
- Uses modular helpers from `utils/draw_helpers.py`
- Page numbering and copyright footer

**Differentiation Levels:**
- Level 1: Real images with text labels (most support)
- Level 2: Real images only (less visual support)
- Level 3: Text only or AAC symbols (highest difficulty)

```python
from generators import generate_sorting_cards_set

# Define categories with items
categories = {
    'Animals': [
        {'image': 'bear', 'label': 'Bear'},
        {'image': 'duck', 'label': 'Duck'},
        {'image': 'cat', 'label': 'Cat'}
    ],
    'Colors': [
        {'image': 'bird', 'label': 'Red Bird'},
        {'image': 'frog', 'label': 'Green Frog'}
    ]
}

# Generate sorting mats and cards
generate_sorting_cards_set(
    categories=categories,
    theme_name='Animals',
    level=1,  # Level 1-3
    card_size='standard',
    cards_per_page=6,
    include_storage_label=True
)
# Output:
# - Sorting mat for each category (Animals, Colors)
# - Pages of cut-out sorting cards
# - Storage label PDF
```

### 9. Enhanced Sentence Strips (AAC)

**NEW**: Lanyard-friendly sentence strips with interchangeable cut-out icons

Generate sentence strips with AAC symbols designed for practical classroom use:

**Features:**
- **Lanyard-Friendly Design**: Left margin strip with hole-punch indicator and reinforced border
- **Interchangeable Icons**: Cut-out icons match exact size of matching cards (750px/2.5" at 300 DPI)
- **Horizontal Strip Layout**: 2-4 icon slots with predictable left-to-right spacing
- **Cut-Out Icon Pages**: Separate pages with bold outlines and optional grab tabs for fine motor support
- **Same Card Style**: Uses matching card styling for visual consistency across products
- **Page Elements**: Copyright footer and page numbering on all pages

```python
from generators import generate_sentence_strips_set

# Define sentence data
sentence_data = [
    {
        'symbols': [
            {'image': 'bear.png', 'label': 'bear', 'folder_type': 'aac'},
            {'image': 'brown.png', 'label': 'brown', 'folder_type': 'aac'},
            {'image': 'see.png', 'label': 'I see', 'folder_type': 'aac'}
        ],
        'slots': 4  # Number of icon slots in strip
    }
]

# Generate sentence strips with cut-out icons
output_files = generate_sentence_strips_set(
    sentence_data=sentence_data,
    theme_name='Brown_Bear',
    with_lanyard=True,  # Add lanyard strip
    with_cutout_icons=True,  # Generate cut-out icon pages
    include_storage_label=True
)

# Output includes:
# - Brown_Bear_Sentence_Strips.pdf (lanyard-ready strips)
# - Brown_Bear_Sentence_Icons_Cutouts.pdf (interchangeable icons)
# - Storage labels for both
```

**Icon Interchangeability:**
Icons are the exact same size (750px) as matching card icons, allowing:
- Mix-and-match across activities
- Reusable icon sets for multiple sentence patterns
- Consistent visual experience for students

### 10. Yes/No Questions
Create yes/no question cards with images.
```python
from generators import generate_yes_no_questions_set
```

### 11. WH Questions
Generate WH question cards (Who, What, Where, When, Why).
```python
from generators import generate_wh_questions_set
```

### 12. Story Maps
Create story map organizers for comprehension.
```python
from generators import generate_story_maps_set
```

### 13. Color Questions
Generate color identification questions.
```python
from generators import generate_color_questions_set
```

### 14. Word Search
Create word search puzzles with theme words.
```python
from generators import generate_word_search_set
```

### 15. Storage Labels
Generate labels for organizing materials.
```python
from generators import generate_storage_labels_sheet
```

## SPED Design Principles

All generators follow these accessibility guidelines:

- **High Contrast**: Black text on white backgrounds
- **Large Images**: Scaled appropriately for visibility
- **Minimal Clutter**: Clean, uncluttered layouts
- **Predictable Layouts**: Consistent placement and structure
- **Consistent Borders**: Clear visual boundaries
- **Consistent Footers**: Copyright and attribution
- **300 DPI**: Print-ready quality

## Customization

### Changing Page Settings

Edit `utils/config.py` to customize:
- Page dimensions
- Margins and spacing
- Font sizes
- Colors
- Card sizes

### Adding Custom Fonts

Edit `utils/fonts.py` to register and use custom TTF fonts.

### Modifying Layouts

Each generator in `generators/` can be customized for specific layout needs.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

Copyright © Small Wins Studio. All rights reserved.

## Support

For questions or support, visit [Small Wins Studio on Teachers Pay Teachers](https://www.teacherspayteachers.com/Store/Small-Wins-Studio)
