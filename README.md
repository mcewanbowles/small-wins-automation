# Small Wins Automation - SPED Resource Generator

Automated TpT (Teachers Pay Teachers) resource generators for Small Wins Studio. This Python automation system generates 14 different printable resources for special education (SPED) following strict accessibility and design guidelines.

## Features

- **14 Different Resource Types**: Counting Mats, Matching Cards, Bingo, Sequencing, Coloring Strips, Coloring Sheets, Find & Cover, Sorting Cards, Sentence Strips (AAC), Yes/No Questions, WH Questions, Story Maps, Color Questions, Word Search, and Storage Labels
- **SPED Design Compliance**: Large images, high contrast, minimal clutter, predictable layouts, consistent borders and footers
- **300 DPI Output**: High-quality PDF files ready for printing
- **Differentiation Levels**: Support for multiple difficulty levels (visual cues, progressive complexity)
- **Theme-Agnostic**: Reusable generators that work with any theme by swapping images and text
- **Modular Architecture**: Shared utilities for borders, fonts, scaling, centering, image loading, and PDF export

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
├── utils/              # Shared utilities
│   ├── config.py       # SPED design rules and constants
│   ├── fonts.py        # Font management
│   ├── image_loader.py # Image loading from 3 folders
│   ├── image_utils.py  # Scaling, centering, transparency
│   ├── layout.py       # Borders, footers, spacing
│   └── pdf_export.py   # 300 DPI PDF generation
├── images/             # Full-color theme images
├── Colour_images/      # Black-and-white outline images
├── aac_images/         # AAC/PCS-style symbols
├── examples/           # Example usage scripts
└── output/             # Generated PDF files

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

### Example 2: Generate Matching Cards (4 Differentiation Levels)

The matching card generator now supports 4 SPED-friendly differentiation levels:

```python
from generators import generate_matching_cards_set

# Define your items
items = [
    {'image': 'bear', 'label': 'Brown Bear'},
    {'image': 'duck', 'label': 'Yellow Duck'},
    {'image': 'frog', 'label': 'Green Frog'},
]

# Level 1: Identical errorless matching (same color image on both cards)
pages_l1 = generate_matching_cards_set(
    items=items,
    level=1,
    card_size='large',
    cards_per_page=6,
    output_dir='output',
    theme_name='Brown_Bear'
)

# Level 2: Outline-to-color matching (outline image matches color image)
pages_l2 = generate_matching_cards_set(items=items, level=2, theme_name='Brown_Bear')

# Level 3: AAC symbol to real image matching
pages_l3 = generate_matching_cards_set(items=items, level=3, theme_name='Brown_Bear')

# Level 4: AAC symbol to text matching
pages_l4 = generate_matching_cards_set(items=items, level=4, theme_name='Brown_Bear')
```

**Matching Card Levels Explained:**
- **Level 1**: Identical errorless matching - Perfect for beginners, both cards show the same color image
- **Level 2**: Outline-to-color matching - Match black-and-white outline to color image
- **Level 3**: AAC symbol to real image - Match AAC/PCS symbol to real photograph/illustration
- **Level 4**: AAC symbol to text - Match AAC/PCS symbol to written word

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

### 7. Find & Cover
Generate "find and cover" activity sheets.
```python
from generators import generate_find_cover_set
```

### 8. Sorting Cards
Create sorting cards for categorization activities.
```python
from generators import generate_sorting_cards_set
```

### 9. Sentence Strips (AAC)
Generate sentence strips with AAC symbols.
```python
from generators import generate_sentence_strips_set
```

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
