# Quick Start Guide

Get started with the Small Wins Automation system in 5 minutes!

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mcewanbowles/small-wins-automation.git
   cd small-wins-automation
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**
   ```bash
   python demo.py
   ```
   
   You should see a PDF created at `output/Demo_Word_Search.pdf`

## Your First Resource

Let's create a simple matching cards activity.

### Step 1: Add Images

Place 3 images in the `images/` folder:
- `apple.png`
- `banana.png`
- `orange.png`

### Step 2: Create a Script

Create a file called `my_first_resource.py`:

```python
from generators import generate_matching_cards_sheet

# Define your cards (image filename, label text)
cards = [
    ('apple.png', 'Apple'),
    ('banana.png', 'Banana'),
    ('orange.png', 'Orange'),
]

# Generate the resource
pages = generate_matching_cards_sheet(
    image_label_pairs=cards,
    cards_per_page=6,       # 6 cards per page (each card appears twice)
    card_size='standard',   # Can be 'standard', 'large', 'rectangle', 'wide'
    folder_type='color',    # Use color images
    level=1,                # Level 1 includes text labels
    output_dir='output',
    theme_name='Fruits'
)

print("✓ Matching cards created!")
print(f"  Output: output/Fruits_Matching_Cards_Level1.pdf")
print(f"  Pages: {len(pages)}")
```

### Step 3: Run Your Script

```bash
python my_first_resource.py
```

You'll find your PDF at `output/Fruits_Matching_Cards_Level1.pdf`!

## Common Recipes

### Recipe 1: Counting Mats (1-10)

```python
from generators import generate_counting_mats_set

pages = generate_counting_mats_set(
    image_filenames=['star.png'],  # One image, repeated
    theme_name='Stars',
    number_range=(1, 10),
    level=1,
    folder_type='color',
    output_dir='output'
)
```

### Recipe 2: Bingo Game

```python
from generators import generate_bingo_set

# You need at least 9 images for a 3x3 bingo
images = ['img1.png', 'img2.png', 'img3.png', 'img4.png', 'img5.png',
          'img6.png', 'img7.png', 'img8.png', 'img9.png']

pages = generate_bingo_set(
    image_filenames=images,
    num_cards=6,         # Generate 6 different bingo cards
    grid_size=3,         # 3x3 grid
    folder_type='color',
    theme_name='Animals',
    output_dir='output'
)
```

### Recipe 3: Coloring Pages

```python
from generators import generate_coloring_sheets_set

# Use outline images from Colour_images folder
sheets = [
    ('apple_outline.png', 'Color the Apple'),
    ('dog_outline.png', 'Color the Dog'),
    ('house_outline.png', 'Color the House'),
]

pages = generate_coloring_sheets_set(
    image_title_pairs=sheets,
    folder_type='bw_outline',  # Use outline images
    theme_name='Coloring Fun',
    output_dir='output'
)
```

### Recipe 4: Yes/No Questions

```python
from generators import generate_yes_no_questions_set

questions = [
    {'image': 'dog.png', 'question': 'Is this a dog?', 'answer': True},
    {'image': 'cat.png', 'question': 'Is this a dog?', 'answer': False},
    {'image': 'apple.png', 'question': 'Is this a fruit?', 'answer': True},
]

pages = generate_yes_no_questions_set(
    question_data=questions,
    folder_type='color',
    level=1,  # Level 1 highlights the correct answer
    theme_name='Animals and Foods',
    output_dir='output'
)
```

### Recipe 5: Word Search (No Images Needed!)

```python
from generators import generate_word_search

# Word search doesn't need images
page = generate_word_search(
    words=['DOG', 'CAT', 'BIRD', 'FISH', 'HAMSTER'],
    theme_name='Pets',
    grid_size=10,
    show_answers=False
)

# Save it
from utils.pdf_export import save_image_as_pdf
save_image_as_pdf(page, 'output/Pets_Word_Search.pdf', title='Pets Word Search')
```

## Understanding Differentiation Levels

Change the `level` parameter to create different versions:

```python
# Level 1: Maximum support (visual cues, labels, highlighted answers)
generate_matching_cards_sheet(..., level=1)

# Level 2: Moderate support (no labels, no highlighting)
generate_matching_cards_sheet(..., level=2)

# Level 3: Minimal support (increased difficulty)
generate_matching_cards_sheet(..., level=3)
```

## Storage Labels for Organization

Keep your resources organized with automatic storage labels!

### Quick Example

```python
from generators import generate_matching_cards_set

# Add include_storage_label=True to any generator
pages = generate_matching_cards_set(
    items=[
        {'image': 'bear', 'label': 'Brown Bear'},
        {'image': 'duck', 'label': 'Yellow Duck'},
    ],
    level=1,
    theme_name='Brown_Bear',
    output_dir='output',
    include_storage_label=True  # Creates companion label PDF
)
```

This creates TWO files:
- `Brown_Bear_Matching_Level1_Identical_Errorless.pdf` (main activity)
- `Brown_Bear_Matching_Level1_Identical_Errorless_LABEL.pdf` (storage label)

### Manual Storage Label

```python
from utils import generate_storage_label

# Create a standalone label
generate_storage_label(
    theme_name='Farm Animals',
    activity_name='Counting Mats',
    level=2,
    label_size='standard',  # 'small', 'standard', or 'large'
    output_path='output/Farm_Animals_Counting_LABEL.pdf'
)
```

**Label Features:**
- High-contrast black border
- Large text for theme and activity
- Level indicator (when applicable)
- Perfect for zip bags, envelopes, or storage boxes
- 3 sizes: small (3x2"), standard (4x3"), large (5x4")

## Image Folder Guide

| Folder | Purpose | Example Files |
|--------|---------|---------------|
| `images/` | Full-color theme images | `dog.png`, `apple.png` |
| `Colour_images/` | Black-and-white outlines for coloring | `dog_outline.png`, `apple_outline.png` |
| `aac_images/` | AAC/PCS communication symbols | `eat.png`, `drink.png`, `happy.png` |

## Tips for Success

1. **Start Simple**: Begin with word search or matching cards (easy to test)
2. **Use Good Images**: 1000x1000 pixels or larger, PNG format recommended
3. **Consistent Naming**: Use lowercase, descriptive names with underscores
4. **Test Differentiation**: Try all 3 levels to see the differences
5. **Check Output**: Always review the PDF before printing

## Troubleshooting

### "FileNotFoundError: Image not found"
- Check that your image file is in the correct folder
- Verify the filename matches exactly (including extension)
- Make sure you're using the right `folder_type` parameter

### "No module named 'reportlab'"
- Run: `pip install -r requirements.txt`

### PDF looks wrong
- Check your image resolution (should be 1000x1000+)
- Verify images have transparent backgrounds (PNG format)
- Review the generated page size (should be 2550x3300 pixels at 300 DPI)

## Next Steps

1. **Explore Examples**: Check `examples/usage_examples.py` for more code samples
2. **Read Architecture**: See `ARCHITECTURE.md` for system design details
3. **Customize**: Modify `utils/config.py` to adjust margins, colors, fonts
4. **Create Themes**: Build complete theme packages with matching images
5. **Share**: Generate resources for your classroom or TpT store!

## Quick Reference

### All 14 Generators

```python
from generators import (
    generate_counting_mats_set,
    generate_matching_cards_sheet,
    generate_bingo_set,
    generate_sequencing_set,
    generate_coloring_strips_page,
    generate_coloring_sheets_set,
    generate_find_cover_set,
    generate_sorting_cards_set,
    generate_sentence_strips_set,
    generate_yes_no_questions_set,
    generate_wh_questions_set,
    generate_story_maps_set,
    generate_color_questions_set,
    generate_word_search_set,
    generate_storage_labels_sheet,
)
```

### Common Parameters

Most generators accept these parameters:
- `theme_name`: Name for your theme (used in filename)
- `folder_type`: `'color'`, `'bw_outline'`, or `'aac'`
- `level`: `1`, `2`, or `3` (differentiation level)
- `output_dir`: Where to save PDFs (default: `'output'`)

## Get Help

- **Issues**: https://github.com/mcewanbowles/small-wins-automation/issues
- **Discussions**: Start a discussion on GitHub
- **TpT Store**: https://www.teacherspayteachers.com/Store/Small-Wins-Studio

Happy creating! 🎉
