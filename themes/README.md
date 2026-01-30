# Themes Folder

This folder contains theme configuration files for SPED resource generation.

## Theme File Format

Each theme is defined in a JSON file with the following structure:

```json
{
  "name": "Theme Name",
  "description": "Description of the theme",
  "author": "Author name",
  "version": "1.0",
  "items": [
    {
      "image": "image_basename",
      "label": "Display Label",
      "color": "optional_color"
    }
  ]
}
```

## Required Fields

- **name**: Display name for the theme
- **items**: Array of item objects, each with:
  - **image**: Base filename (without extension or folder path)
  - **label**: Human-readable label for the item

## Optional Fields

- **description**: Theme description
- **author**: Theme creator
- **version**: Theme version number
- **color**: Color associated with the item (for color-based activities)

## Using Themes

```python
from utils import get_theme_loader

# Load a theme
loader = get_theme_loader()
theme_data = loader.load_theme('brown_bear')

# Get items
items = loader.get_theme_items('brown_bear')

# List all themes
themes = loader.list_available_themes()
```

## Image Organization

For each item, place images in the appropriate folders:
- **images/**: Full-color images (e.g., `images/bear.png`)
- **Colour_images/**: Black-and-white outlines (e.g., `Colour_images/bear.png`)
- **aac_images/**: AAC/PCS symbols (e.g., `aac_images/bear.png`)

## Example Themes

- **brown_bear.json**: Brown Bear, Brown Bear, What Do You See? theme
