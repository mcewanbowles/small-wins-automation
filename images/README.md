# Color Images Folder

This folder contains full-color theme images used by the resource generators.

## Guidelines

- **File Format**: PNG or JPEG recommended
- **Resolution**: At least 1000x1000 pixels for best quality
- **Transparency**: PNG files with transparency are supported
- **Naming**: Use descriptive names (e.g., `dog.png`, `apple.png`, `farm_barn.png`)

## Usage

These images are loaded using:
```python
folder_type='color'
```

## Examples

Place your theme images here:
- Animal themes: `dog.png`, `cat.png`, `bird.png`, etc.
- Food themes: `apple.png`, `banana.png`, `orange.png`, etc.
- Transportation: `car.png`, `bus.png`, `airplane.png`, etc.
- Seasons: `snowflake.png`, `sun.png`, `leaf.png`, etc.

The generators will automatically load and scale these images while preserving transparency and aspect ratios.
