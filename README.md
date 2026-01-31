# Small Wins Automation - SPED Resource Generator

Automated TpT (Teachers Pay Teachers) resource generators for Small Wins Studio. This Python automation system generates 20 different printable resources for special education (SPED) following strict accessibility and design guidelines.

## Features

- **20 Different Resource Types**: Counting Mats, Matching Cards, Bingo, Sequencing, Coloring Strips, Coloring Sheets, Find & Cover, Sorting Cards, Sentence Strips (AAC), Yes/No Questions, WH Questions, Story Maps, Color Questions, Word Search, Storage Labels, AAC Book Board, Sequencing Strips, Story Sequencing, Vocabulary Cards, and Puppet Characters
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
```

### 15. AAC Book Board
Generate AAC (Augmentative and Alternative Communication) book boards with core vocabulary and theme-specific fringe vocabulary.

**Features:**
- Fixed set of 15 core vocabulary icons (I, you, want, like, see, go, put, yes, no, more, all done, big, little, happy, sad)
- Theme-specific fringe vocabulary integration
- Optional color coding by part of speech:
  - Pronouns: Light blue
  - Verbs: Light green
  - Social words: Light pink
  - Adjectives: Light yellow
  - Emotions: Peach
  - Nouns: Light purple
- Configurable grid layouts (5×6 or 6×6)
- Optional cut-out icon pages
- Uses modular helper architecture

**Usage:**
```python
from generators import generate_aac_board_set

# Define theme-specific fringe vocabulary
fringe_vocab = [
    {'image': 'bear.png', 'label': 'bear', 'category': 'noun'},
    {'image': 'duck.png', 'label': 'duck', 'category': 'noun'},
    {'image': 'frog.png', 'label': 'frog', 'category': 'noun'},
    {'image': 'cat.png', 'label': 'cat', 'category': 'noun'},
    {'image': 'dog.png', 'label': 'dog', 'category': 'noun'},
]

# Generate AAC board with core + fringe vocabulary
output_files = generate_aac_board_set(
    fringe_vocab=fringe_vocab,
    theme_name='Brown_Bear',
    grid_size=(5, 6),  # 5 rows × 6 columns = 30 icons total
    use_color_coding=True,  # Enable part-of-speech colors
    with_cutout_icons=True,  # Generate separate cut-out pages
    folder_type='aac',  # Use AAC/PCS symbols
    include_storage_label=True
)

# Output includes:
# - Brown_Bear_AAC_Board.pdf (complete communication board)
# - Brown_Bear_AAC_Icons_Cutouts.pdf (cut-out icons, 6 per page)
# - Storage labels for both
```

**Grid Sizes:**
- `(5, 6)`: 30 total icons (15 core + 15 fringe)
- `(6, 6)`: 36 total icons (15 core + 21 fringe)

**Supported Image Types:**
- `folder_type='aac'`: AAC/PCS symbols from aac_images/
- `folder_type='images'`: Real images from images/
- `folder_type='Colour_images'`: Boardmaker-style colored images

**Color Coding:**
When `use_color_coding=True`, icons are colored by part of speech to aid language learning and organization.

### 16. Sequencing Strips
Generate sequencing strips for teaching order and temporal sequences with lanyard-friendly design.

**Features:**
- Horizontal strips with 3 or 4 icon slots
- Icons match exact size of matching cards (750×750px at 300 DPI)
- Lanyard-friendly design with hole-punch indicator and reinforced border
- Optional text labels under icons
- 4 differentiation levels:
  - Level 1: Errorless (correct order)
  - Level 2: Mixed (scrambled order)
  - Level 3: Cut-and-paste version
  - Level 4: WH-version ("What happens next?")
- Separate cut-out icon pages with optional bold outline and grab tabs
- Storage label support

**Usage:**
```python
from generators import generate_sequencing_strips_set

sequences = [
    {
        'steps': [
            {'image': 'step1.png', 'label': 'First'},
            {'image': 'step2.png', 'label': 'Then'},
            {'image': 'step3.png', 'label': 'Finally'}
        ],
        'title': 'Make a Sandwich'
    }
]

output_files = generate_sequencing_strips_set(
    sequences=sequences,
    theme_name='Life_Skills',
    level=1,  # Errorless
    with_lanyard=True,
    with_cutout_icons=True,
    include_storage_label=True
)
# Returns: {'strips': '...pdf', 'cutouts': '...pdf', 'strips_label': '...pdf', 'cutouts_label': '...pdf'}
```

**Output files:**
- `Theme_Sequencing_Strips_Errorless.pdf` - Strip pages with icons in order
- `Theme_Sequencing_Icons_Cutouts.pdf` - Cut-out icon pages
- Storage labels for organization

### 17. Story Sequencing
Generate comprehensive story sequencing resources for comprehension and retelling.

**Features:**
- **First → Next → Last** (3-box layout):
  - Level 1: Errorless (correct order)
  - Level 2: Mixed (scrambled order)
  - Level 3: Cut-and-paste (empty boxes with cutouts)
- **Story Map**: One-page graphic organizer with Characters, Setting, Problem, Events, Solution
- **Event Ordering**: 3-step and 4-step sequences with WH prompts ("What happened first/next/last")
- **Retell Strip**: Horizontal strip with 3-4 icon slots, lanyard-friendly design
- **Story Summary**: Page with sentence starters ("The story is about...", "First...", "Then...", "Last...")
- **Cut-out Icons**: Matching card-sized icons (750×750px) with optional grab tabs
- Icons match exact size of matching cards for interchangeability
- Storage label support

**Usage:**
```python
from generators import generate_story_sequencing_set

story_data = {
    'events': [
        {'image': 'bear.png', 'label': 'Brown Bear'},
        {'image': 'duck.png', 'label': 'Yellow Duck'},
        {'image': 'frog.png', 'label': 'Green Frog'}
    ],
    'characters': ['Brown Bear', 'Friends'],
    'setting': 'Forest',
    'problem': 'Looking for friends',
    'solution': 'Found colorful friends'
}

output_files = generate_story_sequencing_set(
    story_data=story_data,
    theme_name='Brown_Bear',
    include_storage_label=True
)
# Returns: {'story_sequencing': '...pdf', 'cutouts': '...pdf', 'labels': '...'}
```

**Output files:**
- `Theme_Story_Sequencing.pdf` - All sequencing pages (First/Next/Last, Story Map, Event Ordering, Retell Strip, Story Summary)
- `Theme_Story_Icons_Cutouts.pdf` - Cut-out icon pages with grab tabs
- Storage labels for organization

### 18. Vocabulary Cards
Generate comprehensive vocabulary card sets with 5 different versions.

**Features:**
- **Standard Vocabulary Cards**: AAC/PCS symbols with labels in grid layout (2×2, 3×3, or 4×4)
- **Real Image Vocabulary Cards**: Real photographs with labels (if available)
- **Boardmaker Vocabulary Cards**: Boardmaker symbols with labels (if available)
- **Cut-and-Paste Version**: Matching card-sized icons (750×750px) with bold outlines and grab tabs
- **Lanyard-Friendly Version**: Smaller cards with hole-punch indicators for portable communication
- Consistent spacing and padding across all card types
- Icons maintain exact sizing for interchangeability
- Storage label support for all versions

**Usage:**
```python
from generators import generate_vocab_cards_set

fringe_vocab = [
    {'image': 'bear.png', 'label': 'bear'},
    {'image': 'duck.png', 'label': 'duck'},
    {'image': 'frog.png', 'label': 'frog'},
    {'image': 'cat.png', 'label': 'cat'},
    {'image': 'dog.png', 'label': 'dog'},
]

output_files = generate_vocab_cards_set(
    fringe_vocab=fringe_vocab,
    theme_name='Brown_Bear',
    include_real_images=False,  # Set True if real images available
    include_boardmaker=False,   # Set True if Boardmaker icons available
    include_cutouts=True,
    include_lanyard=True,
    include_storage_label=True
)
# Returns: {'standard': '...pdf', 'cutouts': '...pdf', 'lanyard': '...pdf', 'labels': '...'}
```

**Output files:**
- `Theme_Vocabulary_Cards.pdf` - Standard AAC/PCS vocabulary cards
- `Theme_Vocabulary_Cards_Real_Images.pdf` - Real image version (optional)
- `Theme_Vocabulary_Cards_Boardmaker.pdf` - Boardmaker version (optional)
- `Theme_Vocabulary_Cards_Cutouts.pdf` - Cut-out cards with grab tabs
- `Theme_Vocabulary_Cards_Lanyard.pdf` - Lanyard-friendly cards with hole-punch indicators
- Storage labels for all versions

### 19. Puppet Characters

Generate various puppet resources for dramatic play and story retelling.

**Features:**
- **Stick Puppets**: Large character images (12-15cm tall) with optional grab tabs, handle strips for gluing to craft sticks, and "I am the ___" sentence strips
- **Finger Puppets**: Small character images (5-6cm tall) with fold-over tabs, 2-3 characters per row
- **Velcro Character Cards**: Matching card-sized characters with optional bold outlines and grab tabs, perfect for story mats and adapted books
- **Story Mat**: Simple background page with 3-6 placement zones and optional WH prompts ("Who is here?", "Where is the ___?", "What happens next?")
- **Lanyard Version**: Small character icons sized for lanyard use with hole-punch indicators

```python
from generators import generate_puppet_characters_set

characters = [
    {'image': 'bear.png', 'label': 'Brown Bear'},
    {'image': 'duck.png', 'label': 'Yellow Duck'},
    {'image': 'frog.png', 'label': 'Green Frog'}
]

output_files = generate_puppet_characters_set(
    characters=characters,
    theme_name='Brown_Bear',
    include_stick_puppets=True,
    include_finger_puppets=True,
    include_velcro_cards=True,
    include_story_mat=True,
    include_lanyard=True,
    include_storage_label=True,
    folder_type='images'
)
# Returns: {
#     'stick_puppets': '...pdf', 
#     'finger_puppets': '...pdf', 
#     'velcro_cards': '...pdf',
#     'story_mat': '...pdf',
#     'lanyard': '...pdf',
#     'labels': '...'
# }
```

**Output files:**
- `Theme_Stick_Puppets.pdf` - Large stick puppets (1 per page) with handle strips
- `Theme_Finger_Puppets.pdf` - Small finger puppets (3 per page) with fold tabs
- `Theme_Velcro_Character_Cards.pdf` - Matching card-sized character cards (6 per page)
- `Theme_Story_Mat.pdf` - Story mat with placement zones and WH prompts
- `Theme_Lanyard_Characters.pdf` - Lanyard-friendly character cards (3 per page)
- Storage labels for all versions



### 20. Yes/No Cards

Generate Yes/No question cards for receptive language and categorization tasks.

**Features:**
- **Task-Box Friendly**: 4 cards per page in 2×2 grid with shared borders for guillotine cutting (5.25" × 4" per card)
- **Standard Yes/No Cards**: Question with icon and YES/NO response circles
- **Real Image Version**: Same layout using real photographs (if available)
- **Errorless Version**: Pre-highlighted correct answer (YES or NO)
- **Cut-and-Paste Version**: Students cut and glue YES/NO icons onto cards
- Large icons and clear YES/NO response areas
- SPED-compliant high contrast design
- Storage label support for all versions

**Usage:**
```python
from generators import generate_yes_no_cards_set

items = [
    {'image': 'bear.png', 'label': 'bear'},
    {'image': 'duck.png', 'label': 'duck'},
    {'image': 'frog.png', 'label': 'frog'},
    {'image': 'cat.png', 'label': 'cat'}
]

output_files = generate_yes_no_cards_set(
    items=items,
    theme_name='Brown_Bear',
    include_standard=True,
    include_real_images=False,  # Set True if real images available
    include_errorless=True,
    include_cut_paste=True,
    include_storage_label=True,
    folder_type='images'
)
# Returns: {
#     'standard': '...pdf',
#     'errorless_yes': '...pdf',
#     'errorless_no': '...pdf',
#     'cut_paste': '...pdf',
#     'cutouts': '...pdf',
#     'labels': '...'
# }
```

**Output files:**
- `Theme_Yes_No_Cards.pdf` - Standard Yes/No question cards (4 per page)
- `Theme_Yes_No_Cards_Real_Images.pdf` - Real image version (optional)
- `Theme_Yes_No_Cards_Errorless_Yes.pdf` - Errorless with YES pre-highlighted
- `Theme_Yes_No_Cards_Errorless_No.pdf` - Errorless with NO pre-highlighted
- `Theme_Yes_No_Cards_Cut_Paste.pdf` - Cut-and-paste version with empty boxes
- `Theme_Yes_No_Cutouts.pdf` - YES/NO icons for cutting (12 icons per page)
- Storage labels for all versions

### 21. Bingo Game

Generate bingo boards and calling cards for vocabulary and receptive language practice.

**Features:**
- **Multiple Board Sizes**: 3×3 (early learners), 4×4 (standard), 5×5 (advanced)
- **Errorless Bingo**: All icons identical for beginners
- **Real Image Bingo**: Real photographs instead of symbols (if available)
- **Boardmaker Bingo**: Boardmaker symbols (if available)
- **Task-Box Calling Cards**: 4 cards per page in 2×2 grid with shared borders (5.25" × 4")
- **Multiple Calling Card Types**: Icon only, icon + word, real images
- FREE space in center (except errorless)
- 6 unique boards per type for classroom variety
- SPED-compliant high contrast design
- Storage label support for all versions

**Usage:**
```python
from generators import generate_bingo_game_set

items = [
    {'image': 'bear.png', 'label': 'bear'},
    {'image': 'duck.png', 'label': 'duck'},
    {'image': 'frog.png', 'label': 'frog'},
    {'image': 'cat.png', 'label': 'cat'},
    {'image': 'dog.png', 'label': 'dog'},
    {'image': 'fish.png', 'label': 'fish'},
]

output_files = generate_bingo_game_set(
    items=items,
    theme_name='Brown_Bear',
    include_3x3=True,
    include_4x4=True,
    include_5x5=True,
    include_errorless=True,
    include_real_images=False,  # Set True if real images available
    include_boardmaker=False,   # Set True if Boardmaker icons available
    num_boards=6,  # Number of unique boards per type
    include_calling_cards=True,
    include_storage_label=True,
    folder_type='images'
)
# Returns: {
#     'bingo_3x3': '...pdf',
#     'bingo_4x4': '...pdf',
#     'bingo_5x5': '...pdf',
#     'calling_cards_icons': '...pdf',
#     'calling_cards_words': '...pdf',
#     'labels': '...'
# }
```

**Output files:**
- `Theme_Bingo_3x3.pdf` - 3×3 bingo boards (6 unique boards)
- `Theme_Bingo_4x4.pdf` - 4×4 bingo boards (6 unique boards)
- `Theme_Bingo_5x5.pdf` - 5×5 bingo boards (6 unique boards)
- `Theme_Bingo_3x3_Errorless.pdf` - 3×3 errorless boards (6 unique boards)
- `Theme_Bingo_4x4_Errorless.pdf` - 4×4 errorless boards (6 unique boards)
- `Theme_Bingo_5x5_Errorless.pdf` - 5×5 errorless boards (6 unique boards)
- `Theme_Bingo_3x3_Real_Images.pdf` - 3×3 real image boards (optional)
- `Theme_Bingo_4x4_Real_Images.pdf` - 4×4 real image boards (optional)
- `Theme_Bingo_5x5_Real_Images.pdf` - 5×5 real image boards (optional)
- `Theme_Bingo_Calling_Cards_Icons.pdf` - Task-box sized calling cards with icons only
- `Theme_Bingo_Calling_Cards_Words.pdf` - Task-box sized calling cards with icons + words
- `Theme_Bingo_Calling_Cards_Real_Images.pdf` - Task-box sized calling cards with real images (optional)
- Storage labels for all versions

## Task Box Sizing Standard

The following generators use the **Task Box Sizing Standard** for easy classroom organization:

- **Yes/No Cards**: 4 cards per page (2×2 grid), 5.25" × 4" per card
- **Bingo Calling Cards**: 4 cards per page (2×2 grid), 5.25" × 4" per card

All task-box sized cards share borders for fast guillotine cutting, making them perfect for task boxes, file folder games, and independent work systems.

