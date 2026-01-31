"""
Grid Layout Builder

Provides utilities for creating grid-based layouts for SPED resources.
Complements layout.py with specialized grid functionality.
"""

from PIL import Image
from utils.config import MARGINS


def calculate_grid_dimensions(num_items, max_cols=3, max_rows=None):
    """
    Calculate optimal grid dimensions for a number of items.
    
    Args:
        num_items: Number of items to arrange
        max_cols: Maximum number of columns
        max_rows: Maximum number of rows (None for auto)
        
    Returns:
        tuple: (cols, rows)
    """
    if max_rows:
        cols = min(max_cols, (num_items + max_rows - 1) // max_rows)
        rows = (num_items + cols - 1) // cols
    else:
        cols = min(max_cols, num_items)
        rows = (num_items + cols - 1) // cols
    
    return (cols, rows)


def create_grid_positions(cols, rows, cell_width, cell_height, spacing, 
                          container_width=None, container_height=None):
    """
    Calculate positions for grid cells.
    
    Args:
        cols: Number of columns
        rows: Number of rows
        cell_width: Width of each cell
        cell_height: Height of each cell
        spacing: Space between cells
        container_width: Width of container (for centering)
        container_height: Height of container (for centering)
        
    Returns:
        list: List of (x, y) tuples for each cell position
    """
    total_width = (cell_width * cols) + (spacing * (cols - 1))
    total_height = (cell_height * rows) + (spacing * (rows - 1))
    
    # Calculate offset for centering
    offset_x = ((container_width - total_width) // 2) if container_width else 0
    offset_y = ((container_height - total_height) // 2) if container_height else 0
    
    positions = []
    for row in range(rows):
        for col in range(cols):
            x = offset_x + (col * (cell_width + spacing))
            y = offset_y + (row * (cell_height + spacing))
            positions.append((x, y))
    
    return positions


def create_grid_canvas(cols, rows, cell_width, cell_height, spacing, background_color=(255, 255, 255, 255)):
    """
    Create a blank canvas sized for a grid layout.
    
    Args:
        cols: Number of columns
        rows: Number of rows
        cell_width: Width of each cell
        cell_height: Height of each cell
        spacing: Space between cells
        background_color: RGBA background color
        
    Returns:
        PIL.Image: Blank canvas
    """
    width = (cell_width * cols) + (spacing * (cols - 1)) + (MARGINS['page'] * 2)
    height = (cell_height * rows) + (spacing * (rows - 1)) + (MARGINS['page'] * 2)
    
    return Image.new('RGBA', (int(width), int(height)), background_color)


def arrange_items_in_grid(items, cols, rows, cell_width, cell_height, spacing,
                          canvas=None, container_width=None, container_height=None):
    """
    Arrange items (images or objects) in a grid layout.
    
    Args:
        items: List of PIL Images or objects to arrange
        cols: Number of columns
        rows: Number of rows
        cell_width: Width of each cell
        cell_height: Height of each cell
        spacing: Space between cells
        canvas: Existing canvas to draw on (creates new if None)
        container_width: Container width for centering
        container_height: Container height for centering
        
    Returns:
        PIL.Image: Canvas with items arranged in grid
    """
    if canvas is None:
        canvas = create_grid_canvas(cols, rows, cell_width, cell_height, spacing)
    
    positions = create_grid_positions(cols, rows, cell_width, cell_height, spacing,
                                     container_width, container_height)
    
    for idx, item in enumerate(items[:cols * rows]):
        if idx < len(positions):
            x, y = positions[idx]
            if isinstance(item, Image.Image):
                # Center item within cell
                item_x = x + (cell_width - item.width) // 2
                item_y = y + (cell_height - item.height) // 2
                canvas.paste(item, (int(item_x), int(item_y)), item if item.mode == 'RGBA' else None)
    
    return canvas


def create_responsive_grid(items, max_width, max_height, min_cell_size=100, spacing=20):
    """
    Create a responsive grid that fits within maximum dimensions.
    
    Args:
        items: List of items to arrange
        max_width: Maximum width of grid
        max_height: Maximum height of grid
        min_cell_size: Minimum size for cells
        spacing: Space between cells
        
    Returns:
        tuple: (canvas, cols, rows, cell_size)
    """
    num_items = len(items)
    
    # Try different column counts to find best fit
    best_layout = None
    for cols in range(1, num_items + 1):
        rows = (num_items + cols - 1) // cols
        
        # Calculate cell size for this layout
        available_width = max_width - (spacing * (cols - 1))
        available_height = max_height - (spacing * (rows - 1))
        
        max_cell_width = available_width // cols
        max_cell_height = available_height // rows
        cell_size = min(max_cell_width, max_cell_height)
        
        if cell_size >= min_cell_size:
            if best_layout is None or cell_size > best_layout[3]:
                best_layout = (cols, rows, cell_size)
    
    if best_layout is None:
        # Fallback: use minimum cell size
        best_layout = calculate_grid_dimensions(num_items, max_cols=3)
        cols, rows = best_layout
        cell_size = min_cell_size
    else:
        cols, rows, cell_size = best_layout
    
    canvas = arrange_items_in_grid(items, cols, rows, cell_size, cell_size, spacing,
                                   container_width=max_width, container_height=max_height)
    
    return (canvas, cols, rows, cell_size)
