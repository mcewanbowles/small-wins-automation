#!/usr/bin/env python3
"""
Freebie Generator for Small Wins Studio TPT Products
Generates a freebie PDF with 1 sample page from each level,
cutouts, and color-coded storage labels.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import os

# Level colors
LEVEL_COLORS = {
    1: HexColor('#90EE90'),  # Light Green - Errorless
    2: HexColor('#ADD8E6'),  # Light Blue - Easy
    3: HexColor('#FFD580'),  # Light Orange - Medium
    4: HexColor('#FFB6C1'),  # Light Pink - Challenge
    5: HexColor('#DDA0DD'),  # Light Purple - Real Photos
}

LEVEL_NAMES = {
    1: 'Errorless',
    2: 'Easy',
    3: 'Medium',
    4: 'Challenge',
    5: 'Real Photos',
}

TEAL = HexColor('#008B8B')
NAVY = HexColor('#1E3A5F')
WHITE = HexColor('#FFFFFF')
LIGHT_GRAY = HexColor('#999999')


def generate_freebie_cover(c, width, height, product_title):
    """Generate the freebie cover page."""
    
    # Teal header
    c.setFillColor(TEAL)
    c.rect(0, height - 100, width, 100, fill=True, stroke=False)
    
    # FREEBIE badge
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 36)
    c.drawCentredString(width/2, height - 60, "FREE SAMPLER")
    
    c.setFont('Helvetica', 18)
    c.drawCentredString(width/2, height - 85, "Try Before You Buy!")
    
    # Title
    y = height - 150
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 28)
    c.drawCentredString(width/2, y, product_title)
    
    # Subtitle
    y -= 30
    c.setFont('Helvetica', 16)
    c.drawCentredString(width/2, y, "1 Sample Activity from Each Level")
    
    # What's included box
    y -= 60
    box_height = 200
    c.setFillColor(HexColor('#F0F8FF'))
    c.setStrokeColor(TEAL)
    c.setLineWidth(2)
    c.roundRect(50, y - box_height, width - 100, box_height, 10, fill=True, stroke=True)
    
    # What's included title
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(width/2, y - 25, "What's Included:")
    
    # List items
    items = [
        "✓ 1 sample activity page from EACH level (5 pages)",
        "✓ Matching cutouts for each activity",
        "✓ Color-coded storage labels",
        "✓ Quick Start guide",
        "✓ Terms of Use"
    ]
    
    c.setFont('Helvetica', 12)
    item_y = y - 55
    for item in items:
        c.drawCentredString(width/2, item_y, item)
        item_y -= 22
    
    # Levels preview
    y = y - box_height - 40
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(width/2, y, "Preview All 5 Levels:")
    
    # Level color boxes
    y -= 30
    box_width = 90
    box_height = 60
    start_x = (width - (box_width * 5 + 40)) / 2
    
    for level in range(1, 6):
        x = start_x + (level - 1) * (box_width + 10)
        color = LEVEL_COLORS[level]
        
        c.setFillColor(color)
        c.setStrokeColor(NAVY)
        c.setLineWidth(1)
        c.roundRect(x, y - box_height, box_width, box_height, 5, fill=True, stroke=True)
        
        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 11)
        c.drawCentredString(x + box_width/2, y - 25, f"Level {level}")
        c.setFont('Helvetica', 9)
        c.drawCentredString(x + box_width/2, y - 40, LEVEL_NAMES[level])
    
    # CTA section
    y = y - box_height - 50
    c.setFillColor(TEAL)
    c.roundRect(width/2 - 150, y - 10, 300, 35, 8, fill=True, stroke=False)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(width/2, y + 3, "Love it? Get the Full Bundle!")
    
    # Footer
    footer_y = 50
    c.setFillColor(LIGHT_GRAY)
    c.setFont('Helvetica', 10)
    c.drawCentredString(width/2, footer_y + 15, "Visit: teacherspayteachers.com/Store/Small-Wins-Studio")
    c.setFont('Helvetica', 9)
    c.drawCentredString(width/2, footer_y, "⭐ Small Wins Studio  © 2025 All rights reserved.")
    
    c.showPage()


def generate_sample_activity_page(c, width, height, level, product_type='Matching'):
    """Generate a sample activity page for a level."""
    
    level_color = LEVEL_COLORS[level]
    level_name = LEVEL_NAMES[level]
    
    # Header with level color
    c.setFillColor(level_color)
    c.rect(0, height - 60, width, 60, fill=True, stroke=False)
    
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 20)
    c.drawCentredString(width/2, height - 35, f"Level {level}: {level_name}")
    
    c.setFont('Helvetica', 12)
    c.drawCentredString(width/2, height - 52, f"Sample {product_type} Activity")
    
    # Main content area placeholder
    content_y = height - 100
    content_height = 500
    
    c.setFillColor(HexColor('#FAFAFA'))
    c.setStrokeColor(level_color)
    c.setLineWidth(2)
    c.rect(50, content_y - content_height, width - 100, content_height, fill=True, stroke=True)
    
    # Placeholder text
    c.setFillColor(LIGHT_GRAY)
    c.setFont('Helvetica', 14)
    c.drawCentredString(width/2, content_y - content_height/2, f"[Sample {product_type} Activity Page]")
    c.setFont('Helvetica', 11)
    c.drawCentredString(width/2, content_y - content_height/2 - 20, f"Level {level}: {level_name}")
    
    # Footer
    footer_y = 50
    c.setFillColor(level_color)
    c.rect(0, footer_y - 10, width, 35, fill=True, stroke=False)
    
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(width/2, footer_y + 8, f"Brown Bear {product_type} - Level {level} | FREE SAMPLE")
    
    c.setFillColor(LIGHT_GRAY)
    c.setFont('Helvetica', 8)
    c.drawCentredString(width/2, footer_y - 8, "⭐ Small Wins Studio  © 2025")
    
    c.showPage()


def generate_cutouts_page(c, width, height, level, product_type='Matching'):
    """Generate a cutouts page for a level."""
    
    level_color = LEVEL_COLORS[level]
    level_name = LEVEL_NAMES[level]
    
    # Header
    c.setFillColor(level_color)
    c.rect(0, height - 50, width, 50, fill=True, stroke=False)
    
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(width/2, height - 30, f"Level {level} Cutouts")
    
    # Cutout placeholders
    y = height - 100
    cutout_size = 100
    cols = 4
    rows = 5
    
    margin_x = (width - (cols * cutout_size + (cols-1) * 20)) / 2
    
    for row in range(rows):
        for col in range(cols):
            x = margin_x + col * (cutout_size + 20)
            cy = y - row * (cutout_size + 20)
            
            c.setFillColor(WHITE)
            c.setStrokeColor(level_color)
            c.setLineWidth(1)
            c.setDash([3, 3])
            c.rect(x, cy - cutout_size, cutout_size, cutout_size, fill=True, stroke=True)
            c.setDash([])
            
            c.setFillColor(LIGHT_GRAY)
            c.setFont('Helvetica', 8)
            c.drawCentredString(x + cutout_size/2, cy - cutout_size/2, "[Cutout]")
    
    # Footer
    footer_y = 30
    c.setFillColor(LIGHT_GRAY)
    c.setFont('Helvetica', 8)
    c.drawCentredString(width/2, footer_y, "⭐ Small Wins Studio  © 2025 - FREE SAMPLE")
    
    c.showPage()


def generate_storage_labels_page(c, width, height):
    """Generate color-coded storage labels page."""
    
    # Header
    c.setFillColor(TEAL)
    c.rect(0, height - 50, width, 50, fill=True, stroke=False)
    
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 18)
    c.drawCentredString(width/2, height - 32, "Storage Labels")
    
    # Labels for each level
    y = height - 100
    label_height = 80
    label_width = width - 100
    
    for level in range(1, 6):
        level_color = LEVEL_COLORS[level]
        level_name = LEVEL_NAMES[level]
        
        # Label background
        c.setFillColor(level_color)
        c.setStrokeColor(NAVY)
        c.setLineWidth(2)
        c.roundRect(50, y - label_height, label_width, label_height, 10, fill=True, stroke=True)
        
        # Label text
        c.setFillColor(NAVY)
        c.setFont('Helvetica-Bold', 18)
        c.drawCentredString(width/2, y - 35, f"Level {level}: {level_name}")
        
        c.setFont('Helvetica', 12)
        c.drawCentredString(width/2, y - 55, "Brown Bear Matching")
        
        y -= label_height + 20
    
    # Footer
    footer_y = 30
    c.setFillColor(LIGHT_GRAY)
    c.setFont('Helvetica', 8)
    c.drawCentredString(width/2, footer_y, "⭐ Small Wins Studio  © 2025 - FREE SAMPLE - Print on cardstock for durability")
    
    c.showPage()


def generate_freebie(output_path, product_title, product_type='Matching'):
    """Generate a complete freebie PDF."""
    
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Page 1: Cover
    generate_freebie_cover(c, width, height, product_title)
    
    # Pages 2-6: Sample activity from each level
    for level in range(1, 6):
        generate_sample_activity_page(c, width, height, level, product_type)
    
    # Pages 7-11: Cutouts for each level
    for level in range(1, 6):
        generate_cutouts_page(c, width, height, level, product_type)
    
    # Page 12: Storage labels
    generate_storage_labels_page(c, width, height)
    
    c.save()
    return output_path


if __name__ == '__main__':
    output_dir = 'review_pdfs'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate Brown Bear Matching Freebie
    output_path = os.path.join(output_dir, 'brown_bear_matching_freebie.pdf')
    generate_freebie(output_path, 'Brown Bear Matching', 'Matching')
    
    print(f"✅ Generated freebie: {output_path}")
