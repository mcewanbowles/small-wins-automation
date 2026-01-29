# SPED TpT Activity Generator System

Automated TpT (Teachers Pay Teachers) resource generators for Small Wins Studio, specifically designed for Special Education (SPED) materials.

## Features

- **High-Quality Output**: All materials generated at 300 DPI for professional printing
- **SPED-Compliant Layouts**: High contrast, large fonts, predictable structure
- **Accessibility-Focused**: Clear borders, consistent footers, and simple designs
- **Multiple Activity Types**:
  - Counting Mats
  - Bingo Boards
  - Matching Activities
  - Sequencing Activities
  - Coloring Pages
  - AAC (Augmentative and Alternative Communication) Boards
  - Labels

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mcewanbowles/small-wins-automation.git
cd small-wins-automation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

Run the demo script to see examples of all generators:

```bash
python demo.py
```

This will create sample activities in the `outputs/` folder.

## Directory Structure

```
small-wins-automation/
├── src/
│   ├── utils/           # Helper utilities
│   │   ├── image_utils.py    # Image processing helpers
│   │   └── layout.py         # SPED layout utilities
│   └── generators/      # Activity generators
│       ├── counting_mats.py
│       ├── bingo.py
│       ├── matching.py
│       ├── sequencing.py
│       ├── coloring.py
│       ├── aac_boards.py
│       └── labels.py
├── images/              # General images
├── Colour_images/       # Color images for activities
├── aac_images/          # AAC symbols and icons
├── outputs/             # Generated materials (git-ignored)
├── demo.py             # Example/demo script
└── requirements.txt    # Python dependencies
```

## Usage

### Counting Mats

Generate counting mats for number practice:

```python
from src.generators import generate_counting_mat_set

# Generate mats for numbers 1-10
files = generate_counting_mat_set(
    start=1,
    end=10,
    image_filename='apple.png',  # Optional
    image_folder='Colour_images',
    output_dir='outputs'
)
```

### Bingo Boards

Create bingo boards with images or text:

```python
from src.generators import generate_bingo_board

items = ['apple.png', 'banana.png', 'cat.png', ...]  # Or text labels

generate_bingo_board(
    items,
    image_folder='images',
    use_images=True,  # Or False for text
    title="Animal Bingo",
    output_path='outputs/bingo.png'
)
```

### Matching Activities

Create matching activities with pairs:

```python
from src.generators import generate_matching_activity

pairs = [
    ('apple.png', 'red.png'),
    ('banana.png', 'yellow.png'),
    # ...
]

generate_matching_activity(
    pairs,
    left_folder='images',
    right_folder='Colour_images',
    use_images=True,
    output_path='outputs/matching.png'
)
```

### Sequencing Activities

Create step-by-step sequencing activities:

```python
from src.generators import generate_sequencing_activity

steps = ['step1.png', 'step2.png', 'step3.png', 'step4.png']

generate_sequencing_activity(
    steps,
    image_folder='images',
    use_images=True,
    title="Washing Hands",
    output_path='outputs/sequencing.png'
)
```

### Coloring Pages

Convert images to coloring pages:

```python
from src.generators import generate_coloring_page

generate_coloring_page(
    'butterfly.png',
    image_folder='images',
    title="Color the Butterfly",
    output_path='outputs/coloring.png'
)
```

### AAC Communication Boards

Create communication boards:

```python
from src.generators import generate_aac_board

items = [
    ('yes.png', 'YES'),
    ('no.png', 'NO'),
    ('help.png', 'HELP'),
    # ... up to 12 items for 3x4 grid
]

generate_aac_board(
    items,
    image_folder='aac_images',
    title="My Communication Board",
    grid_size=(3, 4),  # rows, cols
    output_path='outputs/aac_board.png'
)
```

### Labels

Create classroom labels:

```python
from src.generators import generate_label_sheet

labels = ['Pencils', 'Crayons', 'Scissors', 'Glue', 'Paper', 'Books']
images = ['pencil.png', 'crayon.png', ...]  # Optional

generate_label_sheet(
    labels,
    images=images,
    image_folder='images',
    labels_per_page=6,
    output_path='outputs/labels.png'
)
```

## SPED Design Principles

All generated materials follow SPED best practices:

1. **High Contrast**: Black borders and text on white backgrounds
2. **Large, Clear Fonts**: Minimum 36pt fonts, bold options available
3. **Predictable Structure**: Consistent layout patterns
4. **Visual Clarity**: Simple, uncluttered designs
5. **Professional Quality**: 300 DPI for crisp printing
6. **Consistent Branding**: Footer with studio credit

## Customization

### Image Utilities

The `src/utils/image_utils.py` module provides helpers:

- `get_font(size, bold)` - Get SPED-appropriate fonts
- `scale_image_to_fit(image, max_width, max_height)` - Scale images
- `center_image(canvas_width, canvas_height, image_width, image_height)` - Calculate centered positions
- `add_transparency(image, alpha)` - Add transparency
- `load_image(filename, folder)` - Load from standard folders
- `create_placeholder_image(width, height, text)` - Create placeholders
- `inches_to_pixels(inches)` / `pixels_to_inches(pixels)` - Convert units

### Layout Utilities

The `src/utils/layout.py` module provides the `SPEDLayout` class:

```python
from src.utils import SPEDLayout

# Create custom layout
layout = SPEDLayout(width=2550, height=3300)  # Letter size at 300 DPI
layout.add_border()
layout.add_title("My Activity")
layout.add_footer("© Small Wins Studio")

# Add content...
layout.paste_image(my_image, x, y)

# Save
layout.save('output.png')
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Maintain SPED accessibility standards
2. Keep code modular and well-documented
3. Use type hints where applicable
4. Test with various image sizes and content

## License

Copyright © Small Wins Studio. All rights reserved.

## Support

For questions or issues, please open an issue on GitHub.
