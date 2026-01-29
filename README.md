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

### Example 2: Generate Matching Cards

```python
from generators import generate_matching_cards_sheet

# Generate matching card pairs
image_label_pairs = [
    ('apple.png', 'Apple'),
    ('banana.png', 'Banana'),
    ('orange.png', 'Orange'),
]

pages = generate_matching_cards_sheet(
    image_label_pairs=image_label_pairs,
    cards_per_page=6,
    card_size='standard',
    folder_type='color',
    level=1,
    output_dir='output',
    theme_name='Fruits'
)
```

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
