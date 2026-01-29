# SPED TpT Activity Generator - Usage Guide

This guide provides detailed examples and best practices for using the SPED TpT activity generator system.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Core Utilities](#core-utilities)
3. [Generator Examples](#generator-examples)
4. [Best Practices](#best-practices)
5. [Customization](#customization)

## Getting Started

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Quick Test

```bash
# Run the demo to test all generators
python demo.py
```

## Core Utilities

### Image Utilities

Located in `src/utils/image_utils.py`:

```python
from src.utils import (
    get_font,           # Get SPED-appropriate fonts
    scale_image_to_fit, # Scale images maintaining aspect ratio
    center_image,       # Calculate centered position
    load_image,         # Load from standard folders
    inches_to_pixels,   # Convert measurements
)

# Example: Load and scale an image
from PIL import Image
from src.utils import load_image, scale_image_to_fit, inches_to_pixels

image = load_image('apple.png', folder='Colour_images')
if image:
    scaled = scale_image_to_fit(image, 
                               inches_to_pixels(2),  # max width
                               inches_to_pixels(2))  # max height
```

### Layout Utilities

Located in `src/utils/layout.py`:

```python
from src.utils import SPEDLayout, inches_to_pixels

# Create a custom layout
layout = SPEDLayout(
    width=inches_to_pixels(8.5),   # Letter width
    height=inches_to_pixels(11),    # Letter height
)

# Add standard elements
layout.add_border()
layout.add_title("My Custom Activity")
layout.add_footer("© Small Wins Studio")

# Add a grid
cells = layout.add_grid(rows=3, cols=4)

# Add images to cells
for i, (x, y, width, height) in enumerate(cells):
    # Add content to each cell
    pass

# Save
layout.save('output/my_activity.png')
```

## Generator Examples

### 1. Counting Mats

**Simple counting mat (no images):**
```python
from src.generators import generate_counting_mat

generate_counting_mat(
    number=5,
    title="Count to 5",
    output_path='outputs/count_5.png'
)
```

**With object images:**
```python
generate_counting_mat(
    number=7,
    image_filename='star.png',
    image_folder='Colour_images',
    title="Count the Stars",
    output_path='outputs/count_stars.png'
)
```

**Generate a complete set:**
```python
from src.generators import generate_counting_mat_set

files = generate_counting_mat_set(
    start=1,
    end=20,
    image_filename='apple.png',
    image_folder='Colour_images',
    output_dir='outputs/counting'
)
print(f"Generated {len(files)} counting mats")
```

### 2. Bingo Boards

**Text-based bingo:**
```python
from src.generators import generate_bingo_board

words = [
    "cat", "dog", "bird", "fish", "mouse",
    "lion", "tiger", "bear", "fox", "wolf",
    "frog", "duck", "pig", "cow", "horse",
    "sheep", "goat", "hen", "rooster", "chick",
    "bee", "ant", "spider", "fly", "worm",
]

generate_bingo_board(
    words,
    use_images=False,
    title="Animal Bingo",
    free_space=True,
    output_path='outputs/animal_bingo.png'
)
```

**Image-based bingo:**
```python
image_files = [
    'apple.png', 'banana.png', 'orange.png', 'grape.png',
    'strawberry.png', 'watermelon.png', 'pineapple.png',
    # ... add more image files
]

generate_bingo_board(
    image_files,
    image_folder='images',
    use_images=True,
    title="Fruit Bingo",
    output_path='outputs/fruit_bingo.png'
)
```

**Generate multiple unique boards:**
```python
from src.generators import generate_bingo_set

files = generate_bingo_set(
    items=words,
    num_boards=10,
    use_images=False,
    output_dir='outputs/bingo_set'
)
```

### 3. Matching Activities

**Text matching:**
```python
from src.generators import generate_matching_activity

color_pairs = [
    ("Red", "Apple"),
    ("Yellow", "Banana"),
    ("Orange", "Carrot"),
    ("Green", "Grass"),
    ("Blue", "Sky"),
]

generate_matching_activity(
    color_pairs,
    use_images=False,
    title="Match Colors to Objects",
    output_path='outputs/color_matching.png'
)
```

**Image matching:**
```python
shape_pairs = [
    ('circle.png', 'ball.png'),
    ('square.png', 'box.png'),
    ('triangle.png', 'pyramid.png'),
    ('rectangle.png', 'door.png'),
]

generate_matching_activity(
    shape_pairs,
    left_folder='images',
    right_folder='Colour_images',
    use_images=True,
    title="Match Shapes",
    output_path='outputs/shape_matching.png'
)
```

### 4. Sequencing Activities

**Daily routine sequencing:**
```python
from src.generators import generate_sequencing_activity

morning_routine = [
    "Wake up",
    "Brush teeth",
    "Get dressed",
    "Eat breakfast",
]

generate_sequencing_activity(
    morning_routine,
    use_images=False,
    title="Morning Routine",
    output_path='outputs/morning_routine.png'
)
```

**With images:**
```python
plant_growth = [
    'seed.png',
    'sprout.png',
    'small_plant.png',
    'flowering_plant.png',
]

generate_sequencing_activity(
    plant_growth,
    image_folder='images',
    use_images=True,
    title="How Plants Grow",
    output_path='outputs/plant_growth.png'
)
```

### 5. Coloring Pages

**Basic coloring page:**
```python
from src.generators import generate_coloring_page

generate_coloring_page(
    'butterfly.png',
    image_folder='images',
    title="Color the Butterfly",
    edge_width=3,
    output_path='outputs/butterfly_coloring.png'
)
```

**Generate multiple coloring pages:**
```python
from src.generators import generate_coloring_set

animals = ['cat.png', 'dog.png', 'bird.png', 'fish.png']
titles = ['Color the Cat', 'Color the Dog', 'Color the Bird', 'Color the Fish']

files = generate_coloring_set(
    animals,
    image_folder='images',
    titles=titles,
    output_dir='outputs/coloring'
)
```

### 6. AAC Communication Boards

**Basic communication board:**
```python
from src.generators import generate_aac_board

basic_needs = [
    ('yes.png', 'YES'),
    ('no.png', 'NO'),
    ('help.png', 'HELP'),
    ('more.png', 'MORE'),
    ('done.png', 'DONE'),
    ('please.png', 'PLEASE'),
    ('thank_you.png', 'THANK YOU'),
    ('bathroom.png', 'BATHROOM'),
    ('drink.png', 'DRINK'),
    ('eat.png', 'EAT'),
    ('play.png', 'PLAY'),
    ('stop.png', 'STOP'),
]

generate_aac_board(
    basic_needs,
    image_folder='aac_images',
    title="My Communication Board",
    grid_size=(3, 4),  # 3 rows, 4 columns
    output_path='outputs/aac_basic.png'
)
```

**Feelings board:**
```python
feelings = [
    ('happy.png', 'HAPPY'),
    ('sad.png', 'SAD'),
    ('angry.png', 'ANGRY'),
    ('scared.png', 'SCARED'),
    ('excited.png', 'EXCITED'),
    ('tired.png', 'TIRED'),
]

generate_aac_board(
    feelings,
    image_folder='aac_images',
    title="How I Feel",
    grid_size=(2, 3),  # 2 rows, 3 columns
    output_path='outputs/aac_feelings.png'
)
```

### 7. Labels

**Simple text labels:**
```python
from src.generators import generate_label

generate_label(
    "Pencils",
    size=(1200, 600),  # 4" x 2" at 300 DPI
    output_path='outputs/label_pencils.png'
)
```

**Label with image:**
```python
generate_label(
    "Crayons",
    image_filename='crayon.png',
    image_folder='images',
    output_path='outputs/label_crayons.png'
)
```

**Label sheet:**
```python
from src.generators import generate_label_sheet

classroom_items = [
    "Pencils",
    "Crayons",
    "Scissors",
    "Glue",
    "Paper",
    "Books",
]

# Optional: matching images
item_images = [
    'pencil.png',
    'crayon.png',
    'scissors.png',
    'glue.png',
    'paper.png',
    'book.png',
]

generate_label_sheet(
    classroom_items,
    images=item_images,
    labels_per_page=6,  # 4, 6, or 8
    output_path='outputs/classroom_labels.png'
)
```

## Best Practices

### Image Preparation

1. **Resolution**: Use high-resolution images (at least 300 DPI) for best print quality
2. **Format**: PNG or JPEG formats work best
3. **Size**: Images don't need to be exact size - the system scales them automatically
4. **Transparency**: PNG files with transparency are supported

### File Organization

```
project/
├── images/          # General purpose images
├── Colour_images/   # Colorful images for activities
├── aac_images/      # AAC symbols (simple, high contrast)
└── outputs/         # Generated materials (git-ignored)
```

### Naming Conventions

- Use descriptive filenames: `apple.png`, not `img001.png`
- Use lowercase with underscores: `morning_routine.png`
- Keep names short but meaningful

### SPED Compliance

All generators follow these principles:
- **High Contrast**: Black on white for maximum visibility
- **Large Fonts**: Minimum 36pt, up to 72pt for titles
- **Clear Borders**: Consistent border width (0.1 inches)
- **Predictable Layout**: Grid-based, symmetrical designs
- **Simple Graphics**: Uncluttered, easy to understand

## Customization

### Custom Colors

```python
from src.utils import SPEDLayout, BLUE, RED, GREEN

layout = SPEDLayout(background_color=(255, 255, 220))  # Light yellow
layout.add_border(color=BLUE, width=10)
```

### Custom Fonts

```python
from src.utils import get_font

# Get different font sizes
title_font = get_font(72, bold=True)
body_font = get_font(48, bold=False)
small_font = get_font(36, bold=False)
```

### Custom Page Sizes

```python
from src.utils import SPEDLayout, inches_to_pixels

# Half-letter size (5.5" x 8.5")
layout = SPEDLayout(
    width=inches_to_pixels(8.5),
    height=inches_to_pixels(5.5)
)
```

## Troubleshooting

### Issue: Images not loading
**Solution**: Check that images are in the correct folder and the filename is correct (case-sensitive)

### Issue: Fonts look different
**Solution**: The system uses system fonts. Install Arial or DejaVu Sans for consistent results

### Issue: Generated files are large
**Solution**: This is normal for 300 DPI images. They're optimized for printing, not web display

### Issue: Need different grid sizes
**Solution**: Use the `grid_size` parameter in AAC boards or `labels_per_page` for labels

## Advanced Usage

### Batch Processing

```python
from src.generators import generate_counting_mat_set, generate_bingo_set
from pathlib import Path

# Create organized output structure
output_base = Path('outputs')
(output_base / 'counting').mkdir(parents=True, exist_ok=True)
(output_base / 'bingo').mkdir(parents=True, exist_ok=True)

# Generate multiple sets
generate_counting_mat_set(1, 20, output_dir='outputs/counting')
generate_bingo_set(['word1', 'word2', ...], num_boards=10, output_dir='outputs/bingo')
```

### Custom Layout Example

```python
from src.utils import SPEDLayout, get_font, BLACK, BLUE
from PIL import Image

# Create custom activity
layout = SPEDLayout()
layout.add_border()
layout.add_title("Custom Activity", color=BLUE)

# Add custom content
font = get_font(48, bold=True)
layout.draw.text((300, 500), "Custom Text Here", fill=BLACK, font=font)

# Add shapes
layout.draw.rectangle([100, 600, 500, 900], outline=BLACK, width=5)
layout.draw.ellipse([600, 600, 900, 900], outline=BLUE, width=5)

layout.add_footer("© Small Wins Studio")
layout.save('outputs/custom_activity.png')
```

## Support

For issues or questions:
1. Check this usage guide
2. Review the demo.py file for examples
3. Open an issue on GitHub
