"""
Roll & Cover Game Generator
Generates dice-based numeracy games in task-box sizing format.
Supports dual-mode output (color and black-and-white).
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import os


def hex_to_grayscale_reportlab(hex_color):
    """Convert hex color to grayscale using luminosity method"""
    if isinstance(hex_color, str):
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
    else:
        # Already a HexColor object
        r, g, b = hex_color.red, hex_color.green, hex_color.blue
    
    # Luminosity method: 0.299R + 0.587G + 0.114B
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    return HexColor(int(gray * 255) << 16 | int(gray * 255) << 8 | int(gray * 255))


def create_roll_cover_games(theme_data, output_dir, mode='color'):
    """
    Generate Roll & Cover game boards with task-box sizing.
    
    Args:
        theme_data: Dictionary containing theme information
        output_dir: Directory to save generated PDFs
        mode: 'color' or 'bw' for black-and-white output
    
    Game Types:
    1. Roll & Cover (numbers 1-6)
    2. Roll & Cover (numbers 1-12, using two dice)
    3. Roll, Count & Cover (with icon counting)
    4. Color Roll & Cover (color-coded)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    theme_name = theme_data.get('name', 'Theme')
    primary_color = HexColor(theme_data.get('primary_colour', '#4A90E2'))
    
    # Convert to grayscale if in BW mode
    if mode == 'bw':
        primary_color = hex_to_grayscale_reportlab(primary_color)
    
    # Task-box dimensions (4 per page, 2x2 grid)
    card_width = 5.25 * inch
    card_height = 4 * inch
    
    # Generate different game types
    _create_basic_roll_cover(output_dir, theme_name, primary_color, card_width, card_height, mode)
    _create_double_dice_roll_cover(output_dir, theme_name, primary_color, card_width, card_height, mode)
    _create_icon_roll_cover(output_dir, theme_name, primary_color, card_width, card_height, theme_data, mode)
    _create_storage_labels(output_dir, theme_name, primary_color, mode)
    
    print(f"Roll & Cover games ({mode}) generated in {output_dir}")


def _create_basic_roll_cover(output_dir, theme_name, primary_color, card_width, card_height, mode='color'):
    """Create Roll & Cover boards for numbers 1-6"""
    mode_suffix = f"_{mode}" if mode else ""
    pdf_path = os.path.join(output_dir, f"{theme_name}_Roll_Cover_1-6{mode_suffix}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    page_width, page_height = letter
    
    # 4 boards per page (2x2 grid)
    boards_per_page = 4
    positions = [
        (0, page_height - card_height),  # Top-left
        (card_width, page_height - card_height),  # Top-right
        (0, page_height - 2 * card_height),  # Bottom-left
        (card_width, page_height - 2 * card_height)  # Bottom-right
    ]
    
    board_count = 0
    for board_num in range(4):  # Create 4 different boards
        pos_index = board_count % boards_per_page
        x, y = positions[pos_index]
        
        # Draw card border
        c.setStrokeColor(primary_color)
        c.setLineWidth(2)
        c.rect(x, y, card_width, card_height)
        
        # Title
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(primary_color)
        c.drawCentredString(x + card_width/2, y + card_height - 40, "Roll & Cover")
        
        # Subtitle
        c.setFont("Helvetica", 14)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x + card_width/2, y + card_height - 65, "Numbers 1-6")
        
        # Create 6 boxes for numbers 1-6 (2 rows of 3)
        box_width = card_width / 3.5
        box_height = card_height / 3.5
        start_x = x + (card_width - 3 * box_width) / 2
        start_y = y + card_height - 150
        
        for row in range(2):
            for col in range(3):
                num = row * 3 + col + 1
                box_x = start_x + col * box_width
                box_y = start_y - row * box_height
                
                # Draw box
                c.setStrokeColor(primary_color)
                c.setLineWidth(1.5)
                c.rect(box_x, box_y, box_width, box_height)
                
                # Draw number
                c.setFont("Helvetica-Bold", 36)
                c.setFillColor(primary_color)
                c.drawCentredString(box_x + box_width/2, box_y + box_height/2 - 15, str(num))
                
                # Draw dots (dice pattern)
                _draw_dice_dots(c, box_x + box_width/2, box_y + 15, num, 6)
        
        board_count += 1
        
        # Add footer
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        footer_text = f"© 2026 Small Wins Studio • {theme_name} • Roll & Cover 1-6"
        c.drawCentredString(x + card_width/2, y + 15, footer_text)
        
        if pos_index == boards_per_page - 1:
            c.showPage()
    
    c.save()


def _create_double_dice_roll_cover(output_dir, theme_name, primary_color, card_width, card_height, mode='color'):
    """Create Roll & Cover boards for numbers 2-12 (using two dice)"""
    mode_suffix = f"_{mode}" if mode else ""
    pdf_path = os.path.join(output_dir, f"{theme_name}_Roll_Cover_2-12{mode_suffix}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    page_width, page_height = letter
    
    boards_per_page = 4
    positions = [
        (0, page_height - card_height),
        (card_width, page_height - card_height),
        (0, page_height - 2 * card_height),
        (card_width, page_height - 2 * card_height)
    ]
    
    board_count = 0
    for board_num in range(4):
        pos_index = board_count % boards_per_page
        x, y = positions[pos_index]
        
        # Draw card border
        c.setStrokeColor(primary_color)
        c.setLineWidth(2)
        c.rect(x, y, card_width, card_height)
        
        # Title
        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(primary_color)
        c.drawCentredString(x + card_width/2, y + card_height - 35, "Roll & Cover")
        
        # Subtitle
        c.setFont("Helvetica", 12)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x + card_width/2, y + card_height - 55, "Numbers 2-12 (Roll 2 Dice)")
        
        # Create 11 boxes for numbers 2-12 (arranged nicely)
        box_width = card_width / 4.2
        box_height = card_height / 4.5
        
        # Row 1: 2, 3, 4, 5
        start_y = y + card_height - 110
        for i in range(4):
            num = i + 2
            box_x = x + 20 + i * box_width
            box_y = start_y
            
            c.setStrokeColor(primary_color)
            c.setLineWidth(1.5)
            c.rect(box_x, box_y, box_width, box_height)
            
            c.setFont("Helvetica-Bold", 28)
            c.setFillColor(primary_color)
            c.drawCentredString(box_x + box_width/2, box_y + box_height/2 - 10, str(num))
        
        # Row 2: 6, 7, 8, 9
        for i in range(4):
            num = i + 6
            box_x = x + 20 + i * box_width
            box_y = start_y - box_height - 10
            
            c.setStrokeColor(primary_color)
            c.setLineWidth(1.5)
            c.rect(box_x, box_y, box_width, box_height)
            
            c.setFont("Helvetica-Bold", 28)
            c.setFillColor(primary_color)
            c.drawCentredString(box_x + box_width/2, box_y + box_height/2 - 10, str(num))
        
        # Row 3: 10, 11, 12 (centered)
        for i in range(3):
            num = i + 10
            box_x = x + 20 + (i + 0.5) * box_width
            box_y = start_y - 2 * (box_height + 10)
            
            c.setStrokeColor(primary_color)
            c.setLineWidth(1.5)
            c.rect(box_x, box_y, box_width, box_height)
            
            c.setFont("Helvetica-Bold", 28)
            c.setFillColor(primary_color)
            c.drawCentredString(box_x + box_width/2, box_y + box_height/2 - 10, str(num))
        
        board_count += 1
        
        # Add footer
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        footer_text = f"© 2026 Small Wins Studio • {theme_name} • Roll & Cover 2-12"
        c.drawCentredString(x + card_width/2, y + 15, footer_text)
        
        if pos_index == boards_per_page - 1:
            c.showPage()
    
    c.save()


def _create_icon_roll_cover(output_dir, theme_name, primary_color, card_width, card_height, theme_data, mode='color'):
    """Create Roll & Cover with icon counting"""
    mode_suffix = f"_{mode}" if mode else ""
    pdf_path = os.path.join(output_dir, f"{theme_name}_Roll_Count_Cover{mode_suffix}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    page_width, page_height = letter
    
    boards_per_page = 4
    positions = [
        (0, page_height - card_height),
        (card_width, page_height - card_height),
        (0, page_height - 2 * card_height),
        (card_width, page_height - 2 * card_height)
    ]
    
    board_count = 0
    for board_num in range(4):
        pos_index = board_count % boards_per_page
        x, y = positions[pos_index]
        
        # Draw card border
        c.setStrokeColor(primary_color)
        c.setLineWidth(2)
        c.rect(x, y, card_width, card_height)
        
        # Title
        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(primary_color)
        c.drawCentredString(x + card_width/2, y + card_height - 35, "Roll, Count & Cover")
        
        # Subtitle
        c.setFont("Helvetica", 11)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x + card_width/2, y + card_height - 55, "Roll the die, count the dots, cover the number")
        
        # Create 6 boxes for numbers 1-6
        box_width = card_width / 3.5
        box_height = card_height / 3.5
        start_x = x + (card_width - 3 * box_width) / 2
        start_y = y + card_height - 140
        
        for row in range(2):
            for col in range(3):
                num = row * 3 + col + 1
                box_x = start_x + col * box_width
                box_y = start_y - row * box_height
                
                # Draw box
                c.setStrokeColor(primary_color)
                c.setLineWidth(1.5)
                c.rect(box_x, box_y, box_width, box_height)
                
                # Draw number at top
                c.setFont("Helvetica-Bold", 32)
                c.setFillColor(primary_color)
                c.drawCentredString(box_x + box_width/2, box_y + box_height - 35, str(num))
                
                # Draw icon placeholders (circles) for counting
                icon_size = 12
                spacing = 15
                if num <= 3:
                    # Single row
                    start_icon_x = box_x + (box_width - num * spacing) / 2
                    for i in range(num):
                        c.circle(start_icon_x + i * spacing + icon_size/2, box_y + 25, icon_size/2)
                else:
                    # Two rows
                    icons_row1 = (num + 1) // 2
                    icons_row2 = num - icons_row1
                    start_icon_x1 = box_x + (box_width - icons_row1 * spacing) / 2
                    start_icon_x2 = box_x + (box_width - icons_row2 * spacing) / 2
                    for i in range(icons_row1):
                        c.circle(start_icon_x1 + i * spacing + icon_size/2, box_y + 35, icon_size/2)
                    for i in range(icons_row2):
                        c.circle(start_icon_x2 + i * spacing + icon_size/2, box_y + 20, icon_size/2)
        
        board_count += 1
        
        # Add footer
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        footer_text = f"© 2026 Small Wins Studio • {theme_name} • Roll Count & Cover"
        c.drawCentredString(x + card_width/2, y + 15, footer_text)
        
        if pos_index == boards_per_page - 1:
            c.showPage()
    
    c.save()


def _draw_dice_dots(c, center_x, center_y, number, dot_size=4):
    """Draw dice dot patterns"""
    spacing = 8
    
    # Dot patterns for dice faces
    patterns = {
        1: [(0, 0)],
        2: [(-spacing, spacing), (spacing, -spacing)],
        3: [(-spacing, spacing), (0, 0), (spacing, -spacing)],
        4: [(-spacing, spacing), (spacing, spacing), (-spacing, -spacing), (spacing, -spacing)],
        5: [(-spacing, spacing), (spacing, spacing), (0, 0), (-spacing, -spacing), (spacing, -spacing)],
        6: [(-spacing, spacing), (spacing, spacing), (-spacing, 0), (spacing, 0), (-spacing, -spacing), (spacing, -spacing)]
    }
    
    if number in patterns:
        c.setFillColorRGB(0.3, 0.3, 0.3)
        for dx, dy in patterns[number]:
            c.circle(center_x + dx, center_y + dy, dot_size/2, fill=1)


def _create_storage_labels(output_dir, theme_name, primary_color, mode='color'):
    """Create storage labels for Roll & Cover games"""
    mode_suffix = f"_{mode}" if mode else ""
    pdf_path = os.path.join(output_dir, f"{theme_name}_Roll_Cover_Storage_Labels{mode_suffix}.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    page_width, page_height = letter
    
    # Label dimensions (4 per page)
    label_width = 5.25 * inch
    label_height = 1.5 * inch
    
    labels = [
        "Roll & Cover 1-6",
        "Roll & Cover 2-12",
        "Roll, Count & Cover",
        "Roll & Cover Games"
    ]
    
    positions = [
        (0, page_height - label_height),
        (label_width, page_height - label_height),
        (0, page_height - 2 * label_height),
        (label_width, page_height - 2 * label_height)
    ]
    
    for i, label_text in enumerate(labels):
        x, y = positions[i]
        
        # Draw border
        c.setStrokeColor(primary_color)
        c.setLineWidth(2)
        c.rect(x, y, label_width, label_height)
        
        # Draw title
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(primary_color)
        c.drawCentredString(x + label_width/2, y + label_height/2 + 5, label_text)
        
        # Draw theme name
        c.setFont("Helvetica", 14)
        c.setFillColorRGB(0, 0, 0)
        c.drawCentredString(x + label_width/2, y + label_height/2 - 20, theme_name)
    
    c.save()


def generate_roll_cover_dual_mode(theme_data, output_dir):
    """
    Generate Roll & Cover games in both color and black-and-white modes.
    
    Args:
        theme_data: Dictionary containing theme information
        output_dir: Directory to save generated PDFs
    
    Returns:
        Dictionary with paths to generated PDFs:
        {
            'color': [list of color PDF paths],
            'bw': [list of BW PDF paths]
        }
    """
    paths = {'color': [], 'bw': []}
    
    # Generate color version
    create_roll_cover_games(theme_data, output_dir, mode='color')
    theme_name = theme_data.get('name', 'Theme')
    paths['color'] = [
        os.path.join(output_dir, f"{theme_name}_Roll_Cover_1-6_color.pdf"),
        os.path.join(output_dir, f"{theme_name}_Roll_Cover_2-12_color.pdf"),
        os.path.join(output_dir, f"{theme_name}_Roll_Count_Cover_color.pdf"),
        os.path.join(output_dir, f"{theme_name}_Roll_Cover_Storage_Labels_color.pdf")
    ]
    
    # Generate black-and-white version
    create_roll_cover_games(theme_data, output_dir, mode='bw')
    paths['bw'] = [
        os.path.join(output_dir, f"{theme_name}_Roll_Cover_1-6_bw.pdf"),
        os.path.join(output_dir, f"{theme_name}_Roll_Cover_2-12_bw.pdf"),
        os.path.join(output_dir, f"{theme_name}_Roll_Count_Cover_bw.pdf"),
        os.path.join(output_dir, f"{theme_name}_Roll_Cover_Storage_Labels_bw.pdf")
    ]
    
    return paths


# Example usage
if __name__ == "__main__":
    # Test with sample theme data
    sample_theme = {
        'name': 'Brown Bear',
        'primary_colour': '#8B4513',
        'fringe_icons': ['bear', 'duck', 'cat']
    }
    
    create_roll_cover_games(sample_theme, 'output/roll_cover')
