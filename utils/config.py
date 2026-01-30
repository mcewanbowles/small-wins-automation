"""
Configuration settings for SPED-compliant resource generation.

This module defines all the design rules, constants, and settings
required for creating accessible, high-quality special education resources.
"""

# DPI Settings
DPI = 300  # High-quality print resolution

# Page dimensions (US Letter at 300 DPI)
PAGE_WIDTH = 8.5 * DPI  # 2550 pixels
PAGE_HEIGHT = 11 * DPI  # 3300 pixels

# SPED Design Rules
SPED_RULES = {
    'high_contrast': True,
    'large_images': True,
    'minimal_clutter': True,
    'predictable_layouts': True,
    'consistent_borders': True,
    'consistent_footers': True,
}

# Margins and spacing (in pixels at 300 DPI)
MARGINS = {
    'page': 50,  # Outer page margin
    'content': 30,  # Space between content elements
    'card': 20,  # Margin inside cards
    'border': 5,  # Border thickness
}

# Font sizes (in points)
FONT_SIZES = {
    'title': 36,
    'heading': 28,
    'body': 24,
    'small': 18,
    'footer': 14,
}

# Colors (SPED-friendly high contrast)
COLORS = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'dark_gray': (64, 64, 64),
    'light_gray': (200, 200, 200),
    'border': (0, 0, 0),
    'background': (255, 255, 255),
}

# Image folders
IMAGE_FOLDERS = {
    'color': 'images',  # Full-color theme images
    'bw_outline': 'Colour_images',  # Black-and-white outline images
    'aac': 'aac_images',  # AAC/PCS-style symbols
}

# Differentiation levels
DIFFERENTIATION_LEVELS = {
    1: {'visual_cues': True, 'description': 'Level 1 with visual cues'},
    2: {'visual_cues': False, 'description': 'Level 2 without cues'},
    3: {'visual_cues': False, 'increased_difficulty': True, 'description': 'Level 3 with increased difficulty'},
}

# Card sizes (common dimensions for various activities)
CARD_SIZES = {
    'standard': (750, 750),  # 2.5" x 2.5" at 300 DPI
    'large': (900, 900),  # 3" x 3" at 300 DPI
    'rectangle': (900, 600),  # 3" x 2" at 300 DPI
    'wide': (1200, 600),  # 4" x 2" at 300 DPI
}

# Footer settings
FOOTER_HEIGHT = 80  # Height of footer area in pixels
FOOTER_TEXT = "© 2026 Small Wins Studio • PCS® symbols used with active PCS Maker Personal Licence — For classroom use only"
