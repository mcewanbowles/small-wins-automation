# Architecture Documentation

## System Overview

The Small Wins Automation system is a modular Python-based automation framework for generating 14 different types of printable SPED (Special Education) resources. The system follows strict accessibility guidelines and produces high-quality, 300 DPI PDF files ready for classroom use.

## Core Design Principles

### 1. SPED Compliance
All generators adhere to special education design principles:
- **High Contrast**: Black text on white backgrounds for readability
- **Large Images**: Appropriately scaled for visibility
- **Minimal Clutter**: Clean, uncluttered layouts to reduce cognitive load
- **Predictable Layouts**: Consistent structure for easier navigation
- **Consistent Borders**: Clear visual boundaries
- **Consistent Footers**: Attribution and copyright information

### 2. Modularity
The system is built with a clear separation of concerns:
- **Shared Utilities**: Common functionality used across all generators
- **Independent Generators**: Each resource type is self-contained
- **Theme Agnostic**: Generators work with any theme by swapping images/text

### 3. Differentiation Support
Three levels of scaffolding:
- **Level 1**: Maximum support with visual cues and labels
- **Level 2**: Reduced support for independent practice
- **Level 3**: Increased complexity for advanced learners

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  (Python Scripts, Examples, Direct Function Calls)          │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Generator Layer                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Counting  │ │Matching  │ │  Bingo   │ │Sequencing│ ...  │
│  │  Mats    │ │  Cards   │ │          │ │          │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│                   (14 Generator Modules)                     │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Utility Layer                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │   Config   │ │Image Loader│ │Image Utils │              │
│  └────────────┘ └────────────┘ └────────────┘              │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │   Layout   │ │   Fonts    │ │PDF Export  │              │
│  └────────────┘ └────────────┘ └────────────┘              │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │   images/  │ │Colour_     │ │aac_images/ │              │
│  │            │ │images/     │ │            │              │
│  └────────────┘ └────────────┘ └────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### Utility Layer (`utils/`)

#### 1. `config.py`
Central configuration for all SPED design rules:
- **Constants**: DPI (300), page dimensions (8.5" x 11")
- **Design Rules**: Margins, spacing, colors
- **Card Sizes**: Predefined sizes for consistency
- **Differentiation Levels**: Level definitions and settings

#### 2. `image_loader.py`
Manages image loading with caching:
- **Three Folder Support**: color, bw_outline, aac
- **Transparency Preservation**: Automatic RGBA conversion
- **Caching**: Reduces file I/O for repeated use
- **Error Handling**: Graceful handling of missing files

#### 3. `image_utils.py`
Image manipulation functions:
- **Proportional Scaling**: Maintains aspect ratios
- **Centering**: Centers images in containers
- **Border Addition**: Adds consistent borders
- **Grid Layouts**: Creates multi-image layouts
- **Transparency Support**: Alpha channel handling

#### 4. `layout.py`
Page layout and composition:
- **Page Canvas**: Creates blank pages
- **Borders**: Consistent page borders
- **Footers**: Attribution footers
- **Card Backgrounds**: Bordered card templates
- **Grid Positioning**: Calculates positions for grids

#### 5. `fonts.py`
Font management:
- **Font Selection**: Accessible, readable fonts
- **Size Consistency**: Predefined sizes for different uses
- **Fallback Support**: Defaults when custom fonts unavailable

#### 6. `pdf_export.py`
PDF generation at 300 DPI:
- **Single Page**: Export one image to PDF
- **Multi-Page**: Export multiple images to PDF
- **RGBA to RGB**: Converts with white background
- **High Quality**: 300 DPI output for printing

### Generator Layer (`generators/`)

Each generator is self-contained and follows a consistent pattern:

#### Generator Structure
```python
def generate_single_item(...):
    """Generate one instance of the resource."""
    # 1. Create canvas
    # 2. Load images
    # 3. Apply layout
    # 4. Add differentiation elements
    # 5. Add borders/footer
    # 6. Return PIL Image

def generate_set(...):
    """Generate complete set of resources."""
    # 1. Generate multiple items
    # 2. Arrange on pages
    # 3. Export to PDF
    # 4. Return pages
```

#### The 14 Generators

1. **Counting Mats** (`counting_mats.py`)
   - Visual counting with images
   - Numbers 1-10+ support
   - Grid layout based on number

2. **Matching Cards** (`matching_cards.py`)
   - Memory/matching pairs
   - Optional text labels
   - Multiple card sizes

3. **Bingo** (`bingo.py`)
   - Customizable grid size (3x3, 4x4, 5x5)
   - Randomized placement
   - Calling cards included

4. **Sequencing** (`sequencing.py`)
   - Step-by-step sequences
   - Numbered cards (Level 1)
   - Unnumbered (Level 2+)

5. **Coloring Strips** (`coloring_strips.py`)
   - Narrow 2" x 8.5" strips
   - Uses outline images
   - Optional labels

6. **Coloring Sheets** (`coloring_sheets.py`)
   - Full-page coloring
   - Large outline images
   - Title support

7. **Find & Cover** (`find_cover.py`)
   - Search and find activities
   - Target images + grid
   - Randomized placement

8. **Sorting Cards** (`sorting_cards.py`)
   - Category sorting
   - Header cards for categories
   - Optional category labels

9. **Sentence Strips** (`sentence_strips.py`)
   - AAC symbol sequences
   - Sentence starters
   - Visual + text support

10. **Yes/No Questions** (`yes_no_questions.py`)
    - Binary choice questions
    - Image + question
    - Answer highlighting (Level 1)

11. **WH Questions** (`wh_questions.py`)
    - Multiple choice questions
    - Who, What, Where, When, Why
    - Up to 4 choices

12. **Story Maps** (`story_maps.py`)
    - 4-section organizer
    - Characters, Setting, Problem, Solution
    - Optional image support

13. **Color Questions** (`color_questions.py`)
    - Color identification
    - Visual color swatches
    - Answer highlighting

14. **Word Search** (`word_search.py`)
    - Customizable grid size
    - Horizontal/vertical words
    - Answer key generation

15. **Storage Labels** (`storage_labels.py`)
    - Multiple sizes (small, medium, large)
    - Image + text labels
    - Organization tools

## Image Management

### Folder Structure
```
images/          # Full-color theme images
├── dog.png
├── cat.png
└── ...

Colour_images/   # Black-and-white outlines
├── apple_outline.png
├── dog_outline.png
└── ...

aac_images/      # AAC/PCS symbols
├── eat.png
├── drink.png
└── ...
```

### Image Requirements
- **Format**: PNG (transparency), JPEG, GIF
- **Resolution**: 1000x1000+ pixels recommended
- **Naming**: Descriptive, lowercase with underscores
- **Transparency**: PNG with alpha channel supported

## Workflow Example

### Creating Counting Mats

```python
from generators import generate_counting_mats_set

# 1. Prepare image files in images/ folder
#    farm_cow.png, farm_pig.png, farm_chicken.png

# 2. Generate Level 1 (with visual cues)
pages = generate_counting_mats_set(
    image_filenames=['farm_cow.png', 'farm_pig.png', 'farm_chicken.png'],
    theme_name='Farm Animals',
    number_range=(1, 10),
    level=1,
    folder_type='color',
    output_dir='output'
)

# 3. PDF automatically saved to:
#    output/Farm_Animals_Counting_Mats_Level1.pdf

# 4. Generate Level 2 (without visual cues)
pages = generate_counting_mats_set(..., level=2)
```

## Extension Points

### Adding New Generators
1. Create new file in `generators/`
2. Import utilities from `utils`
3. Follow generator pattern (single item + set)
4. Add to `generators/__init__.py`

### Custom Layouts
Modify layout functions in `utils/layout.py` or create new ones in generators.

### Custom Fonts
Register new fonts in `utils/fonts.py` using ReportLab's font registration.

### New Image Folders
Add new folder types in `utils/config.py` and `utils/image_loader.py`.

## Testing

Run the demo to verify installation:
```bash
python demo.py
```

Check examples:
```bash
python examples/usage_examples.py
```

## Performance Considerations

- **Image Caching**: Loaded images are cached to reduce I/O
- **Batch Generation**: Generate multiple pages in one call
- **Memory Management**: Clear cache when processing large sets

## Error Handling

- **Missing Images**: Graceful fallback or clear error messages
- **Invalid Parameters**: Validation at generator entry points
- **File I/O**: Directory creation, permission checks

## Future Enhancements

Potential additions:
- Web interface for non-technical users
- Template system for recurring themes
- Batch processing from CSV/JSON
- Cloud storage integration
- Print-ready packaging (crop marks, bleed)
