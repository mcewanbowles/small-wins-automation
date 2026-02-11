"""
Utils package for TpT Automation System

Provides shared utilities for:
- Configuration loading (config.py)
- Image loading and processing (image_loader.py)
- PDF generation (pdf_builder.py)
- Layout calculations (layout_utils.py)
- Font management (fonts.py)
- Border/styling utilities (border_utils.py)
"""

from .config import (
    load_theme_config,
    load_global_config,
    get_level_color,
    get_branding_config,
    get_asset_path
)

from .image_loader import (
    load_image,
    load_theme_image,
    find_theme_image,
    resize_image_proportional,
    get_image_center_position
)

from .pdf_builder import (
    PDFBuilder,
    hex_to_rgb,
    inches_to_points,
    points_to_inches,
    PAGE_WIDTH,
    PAGE_HEIGHT,
    MARGIN,
    USABLE_WIDTH,
    USABLE_HEIGHT
)

__all__ = [
    # Config
    'load_theme_config',
    'load_global_config',
    'get_level_color',
    'get_branding_config',
    'get_asset_path',
    
    # Image loading
    'load_image',
    'load_theme_image',
    'find_theme_image',
    'resize_image_proportional',
    'get_image_center_position',
    
    # PDF building
    'PDFBuilder',
    'hex_to_rgb',
    'inches_to_points',
    'points_to_inches',
    'PAGE_WIDTH',
    'PAGE_HEIGHT',
    'MARGIN',
    'USABLE_WIDTH',
    'USABLE_HEIGHT',
]
