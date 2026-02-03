# CSV-Based Theme Loader

## Overview

The new CSV-based theme loader (`themes/theme_loader.py`) serves as the **single source of truth** for all theme metadata in the SPED Resource Automation System.

## Features

- **CSV-based configuration**: All themes defined in `themes.csv`
- **Structured Theme objects**: Clean API for accessing theme data
- **Color/BW mode support**: Automatic conversion to grayscale for black-and-white printing
- **Path resolution**: Automatic resolution of icon folders, image folders, etc.
- **Validation**: Built-in validation of theme data and folder paths
- **Caching**: Performance optimization through intelligent caching

## Quick Start

```python
from themes.theme_loader import load_theme

# Load a theme in color mode
theme = load_theme('brown_bear', mode='color')

# Access theme data
print(theme.name)           # "Brown Bear Brown Bear What Do You See?"
print(theme.vocab)          # ['bear', 'duck', 'frog', ...]
print(theme.colours)        # ['#8B4513', '#FFD700', ...]
print(theme.icons)          # List of icon filenames
print(theme.fonts)          # {'heading': 'Arial-Bold', 'body': 'Arial'}

# Load in black-and-white mode
bw_theme = load_theme('brown_bear', mode='bw')
print(bw_theme.colours)     # Grayscale versions of colors
```

## CSV Format

The `themes.csv` file should have the following columns:

| Column | Required | Description | Example |
|--------|----------|-------------|---------|
| `theme_id` | Yes | Unique identifier for the theme | `brown_bear` |
| `theme_name` | Yes | Display name of the theme | `Brown Bear Brown Bear What Do You See?` |
| `icon_folder` | Optional | Relative path to icon folder | `icons/brown_bear` |
| `real_images_folder` | Optional | Relative path to real images | `images/brown_bear` |
| `colour_palette` | Optional | Comma-separated hex colors | `#8B4513,#FFD700,#32CD32` |
| `fonts` | Optional | JSON or comma-separated fonts | `Arial,Arial` or `{"heading":"Arial-Bold","body":"Arial"}` |
| `key_vocab` | Optional | Comma-separated vocabulary words | `bear,duck,frog,cat` |
| `sequencing_steps` | Optional | JSON or pipe-separated sequences | `["look","see"] \| ["walk","sit"]` |
| `adapted_book_sentences` | Optional | Pipe-separated sentences | `I see a bear. \| I see a duck.` |
| `storage_label_images` | Optional | Path to storage label images | `labels/brown_bear` |

### Data Format Details

**Sequencing Steps**: Can be formatted as:
- JSON array of arrays: `[["step1","step2"],["step3","step4"]]`
- Pipe-separated with double-pipe between sequences: `step1|step2 || step3|step4`

**Adapted Book Sentences**: Can be formatted as:
- JSON array: `["I see a bear.","I see a duck."]`
- Pipe-separated: `I see a bear. | I see a duck.`

**Fonts**: Can be formatted as:
- JSON object: `{"heading":"Arial-Bold","body":"Arial"}`
- Comma-separated: `Arial,Arial` (will add -Bold to first for heading)

## Theme Object API

The `Theme` class provides the following attributes:

- `name` (str): Display name
- `theme_id` (str): Unique identifier
- `icons` (List[str]): List of icon filenames
- `real_images` (List[str]): List of real image filenames
- `colours` (List[str]): List of hex color codes
- `fonts` (Dict): `{'heading': str, 'body': str}`
- `vocab` (List[str]): Vocabulary words
- `sequencing` (List[List[str]]): Sequencing step sequences
- `adapted_book` (List[str]): Adapted book sentences
- `storage_label_images` (List[str]): Storage label filenames
- `paths` (Dict): Resolved file paths
- `metadata` (Dict): Raw CSV row data
- `mode` (str): 'color' or 'bw'

### Helper Methods

- `get_icon_path(icon_name)`: Get full path to an icon file
- `get_real_image_path(image_name)`: Get full path to a real image
- `get_storage_label_path(label_name)`: Get full path to a storage label
- `to_dict()`: Convert theme to dictionary

## Color vs Black-and-White Mode

When loading a theme with `mode='bw'`:

1. **Colors**: Converted to grayscale using standard luminance formula
2. **Contrast**: Automatically adjusted to ensure high contrast for printing
3. **Icons/Images**: Metadata points to same files (conversion happens at render time)

```python
# Color mode
color_theme = load_theme('brown_bear', mode='color')
print(color_theme.colours)  # ['#8B4513', '#FFD700', ...]

# Black-and-white mode
bw_theme = load_theme('brown_bear', mode='bw')
print(bw_theme.colours)  # ['#6b6b6b', '#a8a8a8', ...]  (grayscale)
```

## Advanced Usage

### Load All Themes

```python
from themes.theme_loader import load_all_themes

themes = load_all_themes(mode='color')
for theme_id, theme in themes.items():
    print(f"{theme_id}: {theme.name}")
```

### List Available Themes

```python
from themes.theme_loader import list_themes

theme_ids = list_themes()
print(theme_ids)  # ['brown_bear', 'polar_bear', ...]
```

### Custom CSV Path

```python
theme = load_theme('my_theme', csv_path='custom/path/themes.csv')
```

## Migration from JSON

To migrate from the old JSON-based system:

1. Create a row in `themes.csv` for each JSON theme
2. Set `theme_id` to the JSON filename (without .json)
3. Populate columns with data from the JSON file
4. Update generator code to use `load_theme()` instead of direct JSON loading

## Error Handling

The loader validates themes and provides helpful error messages:

```python
try:
    theme = load_theme('invalid_theme')
except ValueError as e:
    print(f"Error: {e}")  # "Theme not found: invalid_theme"

try:
    theme = load_theme('brown_bear', mode='invalid')
except ValueError as e:
    print(f"Error: {e}")  # "Invalid mode: invalid. Must be 'color' or 'bw'"
```

## Integration with Generators

All generators should eventually migrate to use this loader:

```python
# Old way (JSON-based)
with open('themes/brown_bear.json') as f:
    theme_data = json.load(f)

# New way (CSV-based)
from themes.theme_loader import load_theme
theme = load_theme('brown_bear', mode='color')
```

## Performance

- **Caching**: Themes are cached after first load
- **Lazy loading**: CSV file only loaded when first theme is requested
- **Efficient**: Validated once, used many times

## Future Enhancements

Potential future additions:
- Image preprocessing for BW mode (actual image conversion)
- Theme inheritance (base themes extended by child themes)
- Dynamic theme generation from templates
- Theme validation CLI tool
- Automatic migration tool from JSON to CSV
