#!/usr/bin/env python3
"""
STORAGE LABELS - Matching Original Design
Small Wins Studio - TPT Automation System

Save at THEME level (e.g., Winter_Animals/STORAGE_LABELS.py)
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

# =============================================================================
# CONFIGURATION - Matching Original Design
# =============================================================================

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.4 * inch

# Colors from original design
TAN_BACKGROUND = HexColor('#C9C085')      # Olive-tan background
BORDER_COLOR = HexColor('#5C5C3D')        # Olive-gray border
LABEL_FILL = HexColor('#E8ECF0')          # Light gray-blue fill
TITLE_COLOR = HexColor('#4A5568')         # Dark gray-blue for title
TEXT_DARK = HexColor('#2D3748')           # Dark text
TEXT_GRAY = HexColor('#718096')           # Gray text

BORDER_WIDTH = 1.5
CORNER_RADIUS = 8

# =============================================================================
# PRODUCT DEFINITIONS
# =============================================================================

PRODUCTS = {
    'matching_l1': {
        'name': 'Matching Level 1',
        'skill': 'Errorless Visual Matching',
        'pieces_name': 'Matching Pieces',
        'has_pieces': True,
        'folder_type': 'animal',
    },
    'matching_l2': {
        'name': 'Matching Level 2',
        'skill': '4-Choice Visual Discrimination',
        'pieces_name': 'Answer Cards',
        'has_pieces': True,
        'folder_type': 'animal',
    },
    'find_cover_l1': {
        'name': 'Find & Cover Level 1',
        'skill': '2-Choice Visual Scanning (1 vs 1)',
        'pieces_name': None,
        'has_pieces': False,
        'folder_type': 'animal',
    },
    'find_cover_l2': {
        'name': 'Find & Cover Level 2',
        'skill': '3-Choice Visual Scanning (1 vs 2)',
        'pieces_name': None,
        'has_pieces': False,
        'folder_type': 'animal',
    },
    'find_cover_l3': {
        'name': 'Find & Cover Level 3',
        'skill': '4-Choice Visual Scanning (1 vs 3)',
        'pieces_name': None,
        'has_pieces': False,
        'folder_type': 'animal',
    },
    'aac_strips': {
        'name': 'AAC Sentence Strips',
        'skill': 'Core Word Sentence Building',
        'pieces_name': 'Picture Cards',
        'has_pieces': True,
        'folder_type': 'sentence',
        'folder_labels': ['I See', 'I Want', 'I Like', "I Don't Like"],
    },
    'word_search': {
        'name': 'Word Search',
        'skill': 'Visual Scanning & Letter Recognition',
        'pieces_name': 'Answer Keys',
        'has_pieces': True,
        'folder_type': 'level',
        'folder_labels': [
            ('Level 1', 'Symbols Only'),
            ('Level 2', 'H/V Letters'),
            ('Level 3', 'With Diagonals'),
            ('Level 4', 'Challenge'),
        ],
    },
    'sorting_cards': {
        'name': 'Sorting Cards',
        'skill': 'Category Classification',
        'pieces_name': 'Picture Cards',
        'has_pieces': True,
        'folder_type': 'sorting',
        'folder_labels': ['Sort Activity 1', 'Sort Activity 2', 'Category Headers', 'Answer Keys'],
    },
}

# =============================================================================
# FONT SETUP
# =============================================================================

_fonts_registered = False

def setup_fonts():
    global _fonts_registered
    if _fonts_registered:
        return
    
    font_configs = [
        ('ScriptFont', [
            '/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf',
            'C:/Windows/Fonts/georgiaz.ttf',
        ]),
        ('SerifBold', [
            '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',
            'C:/Windows/Fonts/georgiab.ttf',
        ]),
        ('SansRegular', [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            'C:/Windows/Fonts/arial.ttf',
        ]),
        ('SansBold', [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            'C:/Windows/Fonts/arialbd.ttf',
        ]),
    ]
    
    for font_name, paths in font_configs:
        for path in paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, path))
                    break
                except:
                    pass
    
    _fonts_registered = True

def set_font(c, font_name, size, fallback='Helvetica'):
    try:
        c.setFont(font_name, size)
    except:
        c.setFont(fallback, size)

# =============================================================================
# DRAWING UTILITIES
# =============================================================================

def draw_rounded_rect(c, x, y, width, height, radius=8, fill=None, stroke=None, stroke_width=1.5):
    """Draw a rounded rectangle."""
    path = c.beginPath()
    path.moveTo(x + radius, y)
    path.lineTo(x + width - radius, y)
    path.arcTo(x + width - radius, y, x + width, y + radius, radius)
    path.lineTo(x + width, y + height - radius)
    path.arcTo(x + width, y + height - radius, x + width - radius, y + height, radius)
    path.lineTo(x + radius, y + height)
    path.arcTo(x + radius, y + height, x, y + height - radius, radius)
    path.lineTo(x, y + radius)
    path.arcTo(x, y + radius, x + radius, y, radius)
    path.close()
    
    if fill:
        c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(stroke_width)
    
    if fill and stroke:
        c.drawPath(path, fill=1, stroke=1)
    elif fill:
        c.drawPath(path, fill=1, stroke=0)
    elif stroke:
        c.drawPath(path, fill=0, stroke=1)

def draw_image(c, img_path, x, y, width, height):
    """Draw image scaled to fit, centered in the given area."""
    if not os.path.exists(img_path):
        return False
    try:
        with Image.open(img_path) as img:
            img_w, img_h = img.size
            scale = min(width / img_w, height / img_h)
            new_w, new_h = img_w * scale, img_h * scale
            draw_x = x + (width - new_w) / 2
            draw_y = y + (height - new_h) / 2
            c.drawImage(img_path, draw_x, draw_y, new_w, new_h,
                       preserveAspectRatio=True, mask='auto')
        return True
    except:
        return False

def get_pack_images(pack_folder):
    """Get images from pack's images folder."""
    images_folder = os.path.join(pack_folder, 'images')
    if not os.path.exists(images_folder):
        return []
    
    images = []
    for f in sorted(os.listdir(images_folder)):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
            images.append({
                'path': os.path.join(images_folder, f),
                'name': os.path.splitext(f)[0].replace('_', ' ').title(),
            })
    return images[:4]

# =============================================================================
# MAIN DRAWING FUNCTION
# =============================================================================

def draw_storage_labels_page(c, pack_code, theme_name, product_type, images):
    """Draw storage labels page matching original design."""
    
    product = PRODUCTS.get(product_type)
    if not product:
        return
    
    # === BACKGROUND ===
    c.setFillColor(TAN_BACKGROUND)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    
    # === TITLE: "Storage Labels" in script font ===
    set_font(c, 'ScriptFont', 44, 'Times-BoldItalic')
    c.setFillColor(TITLE_COLOR)
    c.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 52, "Storage Labels")
    
    # === HEADER BOX ===
    header_width = PAGE_WIDTH - 2 * MARGIN
    header_height = 1.75 * inch
    header_x = MARGIN
    header_y = PAGE_HEIGHT - 75 - header_height
    
    draw_rounded_rect(c, header_x, header_y, header_width, header_height,
                     CORNER_RADIUS, LABEL_FILL, BORDER_COLOR, BORDER_WIDTH)
    
    # Pack title at top of header
    set_font(c, 'SansBold', 13, 'Helvetica-Bold')
    c.setFillColor(TEXT_DARK)
    pack_title = f"{theme_name} Pack {pack_code[-1]} ({pack_code})"
    c.drawCentredString(PAGE_WIDTH / 2, header_y + header_height - 20, pack_title)
    
    # Product name below pack title
    set_font(c, 'SansBold', 12, 'Helvetica-Bold')
    c.setFillColor(TITLE_COLOR)
    c.drawCentredString(PAGE_WIDTH / 2, header_y + header_height - 38, product['name'])
    
    # Skill description
    set_font(c, 'SansRegular', 9, 'Helvetica')
    c.setFillColor(TEXT_GRAY)
    c.drawCentredString(PAGE_WIDTH / 2, header_y + header_height - 52, product.get('skill', ''))
    
    # Row of 4 large images
    if images:
        img_size = 0.8 * inch
        total_width = 4 * img_size + 3 * 15
        start_x = (PAGE_WIDTH - total_width) / 2
        img_y = header_y + 15
        
        for i, img in enumerate(images):
            img_x = start_x + i * (img_size + 15)
            draw_image(c, img['path'], img_x, img_y, img_size, img_size)
    
    # Instruction text at bottom of header
    set_font(c, 'SansRegular', 8, 'Helvetica')
    c.setFillColor(TEXT_GRAY)
    c.drawCentredString(PAGE_WIDTH / 2, header_y + 5,
                       "Cut, laminate, and attach to folders for organized storage")
    
    # === FOLDER LABELS (2x2 Grid) ===
    grid_top = header_y - 12
    grid_width = PAGE_WIDTH - 2 * MARGIN
    label_width = (grid_width - 15) / 2
    label_height = 1.4 * inch
    gap_x = 15
    gap_y = 10
    
    folder_type = product.get('folder_type', 'animal')
    custom_labels = product.get('folder_labels', [])
    
    for i in range(4):
        row = i // 2
        col = i % 2
        
        x = MARGIN + col * (label_width + gap_x)
        y = grid_top - (row + 1) * label_height - row * gap_y
        
        # Draw label box
        draw_rounded_rect(c, x, y, label_width, label_height,
                         CORNER_RADIUS, LABEL_FILL, BORDER_COLOR, BORDER_WIDTH)
        
        # Folder identifier at top
        set_font(c, 'SansRegular', 9, 'Helvetica')
        c.setFillColor(TEXT_GRAY)
        c.drawCentredString(x + label_width/2, y + label_height - 14,
                           f"Folder {i+1} - {pack_code}")
        
        if folder_type == 'animal' and i < len(images):
            # Large animal image - centered in label
            img_size = 0.72 * inch
            img_x = x + (label_width - img_size) / 2
            img_y = y + 26
            draw_image(c, images[i]['path'], img_x, img_y, img_size, img_size)
            
            # Animal name below image
            set_font(c, 'SerifBold', 14, 'Times-Bold')
            c.setFillColor(TEXT_DARK)
            c.drawCentredString(x + label_width/2, y + 10, images[i]['name'])
        
        elif folder_type == 'level' and i < len(custom_labels):
            # Word search level with description
            level_info = custom_labels[i]
            if isinstance(level_info, tuple):
                level_name, level_desc = level_info
            else:
                level_name, level_desc = level_info, ''
            
            # Level name
            set_font(c, 'SerifBold', 18, 'Times-Bold')
            c.setFillColor(TEXT_DARK)
            c.drawCentredString(x + label_width/2, y + label_height/2 + 5, level_name)
            
            # Level description below
            if level_desc:
                set_font(c, 'SansRegular', 10, 'Helvetica')
                c.setFillColor(TEXT_GRAY)
                c.drawCentredString(x + label_width/2, y + label_height/2 - 15, level_desc)
        
        elif folder_type in ('sentence', 'sorting') and i < len(custom_labels):
            # Text label centered
            set_font(c, 'SerifBold', 16, 'Times-Bold')
            c.setFillColor(TEXT_DARK)
            c.drawCentredString(x + label_width/2, y + label_height/2 - 5, custom_labels[i])
    
    # Calculate bottom of folder grid
    folders_bottom = grid_top - 2 * label_height - gap_y
    
    # === PIECES LABEL (if applicable) ===
    if product.get('has_pieces', False) and product.get('pieces_name'):
        pieces_height = 1.25 * inch
        pieces_y = MARGIN + 35
        
        draw_rounded_rect(c, MARGIN, pieces_y, grid_width, pieces_height,
                         CORNER_RADIUS, LABEL_FILL, BORDER_COLOR, BORDER_WIDTH)
        
        # Pieces name - large serif font
        set_font(c, 'SerifBold', 22, 'Times-Bold')
        c.setFillColor(TEXT_DARK)
        c.drawCentredString(PAGE_WIDTH / 2, pieces_y + pieces_height - 28, product['pieces_name'])
        
        # Pack info below
        set_font(c, 'SansRegular', 10, 'Helvetica')
        c.setFillColor(TEXT_GRAY)
        c.drawCentredString(PAGE_WIDTH / 2, pieces_y + pieces_height - 45, pack_title)
        
        # Row of images
        if images:
            img_size = 0.52 * inch
            total_width = 4 * img_size + 3 * 12
            start_x = (PAGE_WIDTH - total_width) / 2
            img_y = pieces_y + 6
            
            for i, img in enumerate(images):
                img_x = start_x + i * (img_size + 12)
                draw_image(c, img['path'], img_x, img_y, img_size, img_size)
    
    # === FOOTER ===
    set_font(c, 'SansRegular', 7, 'Helvetica')
    c.setFillColor(TEXT_GRAY)
    c.drawCentredString(PAGE_WIDTH / 2, 18,
                       "© 2026 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License.")

# =============================================================================
# PUBLIC API FUNCTIONS
# =============================================================================

def add_storage_labels_page(canvas_obj, pack_code, theme_name, product_type, pack_folder):
    """Add a single storage labels page to PDF."""
    setup_fonts()
    images = get_pack_images(pack_folder)
    canvas_obj.showPage()
    draw_storage_labels_page(canvas_obj, pack_code, theme_name, product_type, images)

def add_matching_storage_labels(canvas_obj, pack_code, theme_name, pack_folder):
    """Add storage labels for Matching (L1 + L2 = 2 pages)."""
    setup_fonts()
    images = get_pack_images(pack_folder)
    canvas_obj.showPage()
    draw_storage_labels_page(canvas_obj, pack_code, theme_name, 'matching_l1', images)
    canvas_obj.showPage()
    draw_storage_labels_page(canvas_obj, pack_code, theme_name, 'matching_l2', images)

def add_find_cover_storage_labels(canvas_obj, pack_code, theme_name, pack_folder):
    """Add storage labels for Find & Cover (L1 + L2 + L3 = 3 pages)."""
    setup_fonts()
    images = get_pack_images(pack_folder)
    canvas_obj.showPage()
    draw_storage_labels_page(canvas_obj, pack_code, theme_name, 'find_cover_l1', images)
    canvas_obj.showPage()
    draw_storage_labels_page(canvas_obj, pack_code, theme_name, 'find_cover_l2', images)
    canvas_obj.showPage()
    draw_storage_labels_page(canvas_obj, pack_code, theme_name, 'find_cover_l3', images)

def add_aac_storage_labels(canvas_obj, pack_code, theme_name, pack_folder):
    """Add storage labels for AAC Sentence Strips (1 page)."""
    setup_fonts()
    images = get_pack_images(pack_folder)
    canvas_obj.showPage()
    draw_storage_labels_page(canvas_obj, pack_code, theme_name, 'aac_strips', images)

def add_word_search_storage_labels(canvas_obj, pack_code, theme_name, pack_folder):
    """Add storage labels for Word Search (1 page)."""
    setup_fonts()
    images = get_pack_images(pack_folder)
    canvas_obj.showPage()
    draw_storage_labels_page(canvas_obj, pack_code, theme_name, 'word_search', images)

def add_sorting_storage_labels(canvas_obj, pack_code, theme_name, pack_folder):
    """Add storage labels for Sorting Cards (1 page)."""
    setup_fonts()
    images = get_pack_images(pack_folder)
    canvas_obj.showPage()
    draw_storage_labels_page(canvas_obj, pack_code, theme_name, 'sorting_cards', images)

# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python STORAGE_LABELS.py PACK_CODE \"Theme Name\" product_type")
        print("Types:", ', '.join(PRODUCTS.keys()))
        sys.exit(1)
    
    pack_code = sys.argv[1]
    theme_name = sys.argv[2]
    product_type = sys.argv[3]
    
    setup_fonts()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pack_folder = os.path.join(script_dir, pack_code)
    images = get_pack_images(pack_folder)
    
    output_folder = os.path.join(pack_folder, 'OUTPUT')
    os.makedirs(output_folder, exist_ok=True)
    
    output_path = os.path.join(output_folder, f'{pack_code}_{product_type}_StorageLabels.pdf')
    c = canvas.Canvas(output_path, pagesize=letter)
    draw_storage_labels_page(c, pack_code, theme_name, product_type, images)
    c.save()
    
    print(f"Created: {output_path}")
