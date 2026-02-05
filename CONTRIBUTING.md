# Contributing to SPED TpT Activity Generator

Thank you for your interest in contributing to the SPED TpT Activity Generator! This document provides guidelines for contributing to the project.

## Code Structure

The project follows a modular architecture:

```
src/
├── utils/              # Core utilities
│   ├── image_utils.py  # Image processing helpers
│   └── layout.py       # SPED layout base class
└── generators/         # Activity generators
    ├── counting_mats.py
    ├── bingo.py
    ├── matching.py
    ├── sequencing.py
    ├── coloring.py
    ├── aac_boards.py
    └── labels.py
```

## Development Guidelines

### SPED Accessibility Standards

All contributions must maintain SPED (Special Education) accessibility standards:

1. **High Contrast**: Use black text/borders on white backgrounds
2. **Large Fonts**: Minimum 36pt for body text, 48-72pt for titles
3. **Clear Borders**: Consistent border widths (typically 0.1 inches)
4. **Predictable Structure**: Grid-based, symmetrical layouts
5. **Simple Design**: Avoid clutter, use clear visual hierarchy
6. **Professional Quality**: Always output at 300 DPI

### Code Standards

#### Type Hints

Use type hints for all function parameters and return values:

```python
from typing import List, Tuple, Optional
from PIL import Image

def generate_activity(items: List[str], 
                     output_path: Optional[str] = None) -> Image.Image:
    """Generate an activity."""
    pass
```

#### Docstrings

All functions should have clear docstrings:

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
    """
    pass
```

#### Constants

Define constants at the module level:

```python
# Good
DEFAULT_MARGIN = inches_to_pixels(0.5)
GRID_LINE_WIDTH = 5

# Avoid magic numbers
layout.draw.line(..., width=GRID_LINE_WIDTH)  # Good
layout.draw.line(..., width=5)  # Avoid
```

### Adding New Generators

To add a new activity generator:

1. Create a new file in `src/generators/`
2. Import required utilities from `src.utils`
3. Implement the main generator function
4. Implement a batch/set generator function
5. Add to `src/generators/__init__.py`
6. Add examples to `demo.py`
7. Update documentation

#### Template for New Generator

```python
"""
New Activity Generator
Brief description of what this generates.
"""

from PIL import Image
from typing import List, Optional
from ..utils import (
    SPEDLayout, get_font, load_image, 
    BLACK, WHITE, LARGE_FONT_SIZE
)


def generate_my_activity(param1: str,
                        param2: int = 10,
                        output_path: Optional[str] = None) -> Image.Image:
    """
    Generate a new type of activity.
    
    Args:
        param1: Description
        param2: Description with default
        output_path: Path to save (optional)
        
    Returns:
        PIL Image of the activity
    """
    # Create layout
    layout = SPEDLayout()
    
    # Add standard elements
    layout.add_border()
    layout.add_title("My Activity")
    
    # Add custom content
    # ... your code here ...
    
    # Add footer
    layout.add_footer("© Small Wins Studio")
    
    # Save if requested
    if output_path:
        layout.save(output_path)
    
    return layout.get_canvas()


def generate_my_activity_set(items: List[str],
                             output_dir: str = 'outputs') -> List[str]:
    """
    Generate a set of activities.
    
    Args:
        items: List of items for activities
        output_dir: Directory to save files
        
    Returns:
        List of generated file paths
    """
    from ..utils import get_project_root
    
    output_files = []
    output_path = get_project_root() / output_dir
    output_path.mkdir(exist_ok=True)
    
    for i, item in enumerate(items):
        filename = f"my_activity_{i+1}.png"
        filepath = output_path / filename
        
        generate_my_activity(
            item,
            output_path=str(filepath)
        )
        
        output_files.append(str(filepath))
    
    return output_files
```

### Adding New Utilities

To add new utility functions:

1. Decide if it belongs in `image_utils.py` or `layout.py`
2. Add the function with proper type hints and docstrings
3. Export from `src/utils/__init__.py`
4. Add tests/examples

### Testing

Before submitting:

1. Run the demo script: `python demo.py`
2. Verify all generators work
3. Check output files for quality
4. Ensure 300 DPI output
5. Verify SPED compliance (contrast, fonts, borders)

### Code Review Checklist

- [ ] Follows SPED accessibility standards
- [ ] Uses type hints
- [ ] Has clear docstrings
- [ ] Uses constants instead of magic numbers
- [ ] Outputs at 300 DPI
- [ ] Includes footer with copyright
- [ ] Works with and without images
- [ ] Handles edge cases (missing images, etc.)
- [ ] No hardcoded paths
- [ ] Follows existing code style

## Specific Areas for Contribution

### High Priority

1. **PDF Generation**: Add ReportLab-based PDF export
2. **Additional Generators**: 
   - Word search puzzles
   - Flashcards
   - Task cards
   - Social stories
3. **Image Effects**: More edge detection/outline algorithms
4. **Batch Processing**: CLI tools for bulk generation

### Medium Priority

1. **Templates**: Pre-designed templates for common themes
2. **Custom Fonts**: Better font handling and custom font support
3. **Color Schemes**: Theme-based color palettes
4. **Accessibility**: Additional accessibility features (braille, audio cues)

### Nice to Have

1. **GUI**: Simple GUI for non-programmers
2. **Web Interface**: Browser-based generator
3. **Templates Library**: Downloadable template packs
4. **Printing Guides**: Print settings documentation

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push to your fork
7. Create a Pull Request with:
   - Clear description of changes
   - Screenshots of generated outputs
   - Any breaking changes noted

## Code Style

- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Follow PEP 8 guidelines
- Use meaningful variable names
- Keep functions focused and small

## Questions?

Open an issue with the `question` label.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
