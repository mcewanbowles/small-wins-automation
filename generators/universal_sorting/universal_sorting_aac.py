#!/usr/bin/env python3
"""
UNIVERSAL SORTING MAT WITH AAC CORE WORDS
Interactive Velcro Sorting Activity with Communication Support

DESIGN (Design Constitution Compliant):
- PORTRAIT orientation (8.5" × 11") per Design Constitution
- US Letter size with 0.5" margins on all sides
- Rounded border (2-3px, 0.12" corner radius) containing all content
- Header area ABOVE border with pack code, page numbers, "Small Wins Studio"
- Accent stripe INSIDE border (0.55"-0.6" height, rounded corners)
- Title in Comic Sans MS font, centered in accent stripe
- Two-line footer INSIDE border with pack code, theme, copyright
- Small Wins Studio star logo (28px) in footer

AAC CORE WORDS:
- 16 AAC core word buttons positioned on LEFT and RIGHT sides (portrait)
- Buttons: PUT, DIFFERENT, FINISHED, AGAIN, WAIT, I THINK, SAME, HELP
           STOP, LIKE, DON'T LIKE, FUNNY, UH-OH, WHOOPS, MORE, YES
- Load AAC icons from assets/global/aac_core/
- AAC button size: ~50px icons with text labels
- Positioned to avoid overlap with sorting areas

SORTING AREAS:
- Center area contains 2-way, 3-way, and Yes/No sorting configurations
- Navy blue boxes (#2B4C7E) for sorting areas
- Orange accent stripe (#F4B400)
- Instructions: "Cut out picture cards and sort them into the correct boxes."

OUTPUT: Color and B&W versions of sorting mat

Author: Small Wins Studio
License: MIT
"""

from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io
import argparse
from typing import Optional, List, Tuple

# PORTRAIT orientation per Design Constitution (8.5" × 11")
PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = 300

# Brand Colors - Small Wins Studio
BRAND_NAVY = "#2B4C7E"      # Navy blue for borders and sorting boxes
BRAND_ORANGE = "#F4B400"    # Orange for accent stripe
BRAND_TEAL = "#2AAEAE"      # Small Wins brand color
BRAND_GOLD = "#E8C547"      # Small Wins brand color

# Supporting colors
LIGHT_BLUE = "#EEF4FB"
STEEL_BLUE = "#5B7AA0"
FOOTER_GREY = "#999999"

# AAC core words mapped to image filenames (16 buttons)
AAC_WORDS = [
    ("PUT", "put.png"),
    ("DIFFERENT", "different.png"),
    ("FINISHED", "finished.png"),
    ("AGAIN", "more.png"),  # Using "more" for "again"
    ("WAIT", "wait.png"),
    ("I THINK", "think.png"),
    ("SAME", "same.png"),
    ("HELP", "help.png"),
    ("STOP", "stop.png"),
    ("LIKE", "like.png"),
    ("DON'T LIKE", "dont_like.png"),
    ("FUNNY", "favorite.png"),  # Using "favorite" for "funny"
    ("UH-OH", "uh_oh.png"),
    ("WHOOPS", "uh_oh.png"),  # Reuse uh-oh
    ("MORE", "more.png"),
    ("YES", "yes.png"),
]


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def load_fonts():
    """Load fonts with fallback for different operating systems"""
    scale = DPI / 72
    fonts = {}
    try:
        # Windows fonts
        fonts['title'] = ImageFont.truetype("C:/Windows/Fonts/comic.ttf", int(24 * scale))
        fonts['subtitle'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(16 * scale))
        fonts['instruction'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(12 * scale))
        fonts['aac_label'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(9 * scale))
        fonts['sorting_label'] = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(14 * scale))
        fonts['header'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(10 * scale))
        fonts['footer'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(9 * scale))
    except (OSError, IOError):
        # Linux fonts (fallback)
        fonts['title'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(24 * scale))
        fonts['subtitle'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(16 * scale))
        fonts['instruction'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(12 * scale))
        fonts['aac_label'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(9 * scale))
        fonts['sorting_label'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(14 * scale))
        fonts['header'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(10 * scale))
        fonts['footer'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(11 * scale))
        fonts['copyright'] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(9 * scale))
    return fonts


def image_to_grayscale(img: Image.Image) -> Image.Image:
    """Convert image to grayscale while preserving alpha"""
    if img.mode not in ("RGBA", "LA"):
        img = img.convert("RGBA")
    rgba = img.convert("RGBA")
    r, g, b, a = rgba.split()
    from PIL import ImageOps
    gray = ImageOps.grayscale(Image.merge("RGB", (r, g, b)))
    gray_rgb = Image.merge("RGB", (gray, gray, gray))
    return Image.merge("RGBA", (*gray_rgb.split(), a))


def load_aac_icon(icon_filename: str, mode: str, aac_dir: Path) -> Optional[Image.Image]:
    """Load an AAC icon from the aac_core directory"""
    icon_path = aac_dir / icon_filename
    if not icon_path.exists():
        print(f"⚠️  AAC icon not found: {icon_path}")
        return None
    
    img = Image.open(icon_path).convert("RGBA")
    if mode == "bw":
        img = image_to_grayscale(img)
    return img


def draw_aac_button(page, draw, x, y, width, height, icon_img, label_text, fonts, mode="color"):
    """Draw a single AAC button with icon and label
    
    Args:
        page: PIL Image object to paste icon onto
        draw: ImageDraw object for drawing shapes and text
        x, y: Top-left position of button
        width, height: Button dimensions
        icon_img: AAC icon image (PIL Image)
        label_text: Text label for button
        fonts: Dictionary of loaded fonts
        mode: "color" or "bw"
    """
    scale = DPI / 72
    
    # Button background - rounded rectangle
    button_color = (255, 255, 255) if mode == "color" else (245, 245, 245)
    draw.rounded_rectangle(
        [x, y, x + width, y + height],
        radius=int(6 * scale),
        fill=button_color,
        outline=hex_to_rgb(BRAND_NAVY),
        width=int(2 * scale)
    )
    
    # Icon - paste onto page
    if icon_img:
        icon_size = int(40 * scale)  # ~40px icon
        icon_img_resized = icon_img.copy()
        icon_img_resized.thumbnail((icon_size, icon_size), Image.Resampling.LANCZOS)
        icon_x = x + (width - icon_img_resized.width) // 2
        icon_y = y + int(8 * scale)
        
        # Paste icon onto page
        page.paste(icon_img_resized, (icon_x, icon_y), 
                  icon_img_resized if icon_img_resized.mode == 'RGBA' else None)
    
    # Label text below icon
    label_y = y + int(52 * scale)
    label_bbox = draw.textbbox((0, 0), label_text, font=fonts['aac_label'])
    label_w = label_bbox[2] - label_bbox[0]
    label_x = x + (width - label_w) // 2
    
    text_color = hex_to_rgb(BRAND_NAVY) if mode == "color" else (60, 60, 60)
    draw.text((label_x, label_y), label_text, fill=text_color, font=fonts['aac_label'])


def draw_sorting_box(draw, x, y, width, height, label_text, fonts, mode="color"):
    """Draw a sorting area box with label"""
    scale = DPI / 72
    
    # Box background - navy blue
    box_color = hex_to_rgb(BRAND_NAVY) if mode == "color" else (100, 100, 100)
    draw.rounded_rectangle(
        [x, y, x + width, y + height],
        radius=int(8 * scale),
        fill=None,
        outline=box_color,
        width=int(4 * scale)
    )
    
    # Label centered at top of box
    if label_text:
        label_bbox = draw.textbbox((0, 0), label_text, font=fonts['sorting_label'])
        label_w = label_bbox[2] - label_bbox[0]
        label_h = label_bbox[3] - label_bbox[1]
        label_x = x + (width - label_w) // 2
        label_y = y + int(12 * scale)
        
        # White background for label
        label_bg_padding = int(8 * scale)
        draw.rounded_rectangle(
            [label_x - label_bg_padding, label_y - int(4 * scale),
             label_x + label_w + label_bg_padding, label_y + label_h + int(4 * scale)],
            radius=int(4 * scale),
            fill=(255, 255, 255),
            outline=box_color,
            width=int(2 * scale)
        )
        
        text_color = box_color
        draw.text((label_x, label_y), label_text, fill=text_color, font=fonts['sorting_label'])


def create_sorting_mat_page(pack_code: str, theme_name: str, page_num: int, total_pages: int, 
                            mode: str = "color", aac_dir: Optional[Path] = None):
    """Create universal sorting mat page with AAC buttons - PORTRAIT LAYOUT
    
    Args:
        pack_code: Product code (e.g., "SORT01")
        theme_name: Theme name (e.g., "Universal Sorting")
        page_num: Current page number
        total_pages: Total pages in PDF
        mode: "color" or "bw"
        aac_dir: Path to AAC core word icons directory
    """
    
    img_width = int(PAGE_WIDTH * DPI / 72)
    img_height = int(PAGE_HEIGHT * DPI / 72)
    page = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(page)
    
    scale = DPI / 72
    fonts = load_fonts()
    
    # Margins: 0.5" per Design Constitution
    margin = int(0.5 * 72 * scale)  # 0.5 inch = 36 points at 72 DPI
    
    # Header ABOVE border - pack code, page numbers, branding
    header_y = margin - int(20 * scale)
    header_text = f"{pack_code} • Page {page_num}/{total_pages} • Small Wins Studio"
    header_bbox = draw.textbbox((0, 0), header_text, font=fonts['header'])
    header_w = header_bbox[2] - header_bbox[0]
    draw.text(((img_width - header_w) // 2, header_y), header_text,
              fill=hex_to_rgb(STEEL_BLUE), font=fonts['header'])
    
    # Border: 2-3px rounded rectangle, 0.12" corner radius
    border_radius = int(0.12 * 72 * scale)  # 0.12 inch
    draw.rounded_rectangle(
        [margin, margin, img_width - margin, img_height - margin],
        radius=border_radius,
        outline=hex_to_rgb(BRAND_NAVY),
        width=int(3 * scale)
    )
    
    # Accent stripe INSIDE border
    accent_color = hex_to_rgb(BRAND_ORANGE) if mode == "color" else (180, 180, 180)
    accent_height = int(0.6 * 72 * scale)  # 0.6 inch
    accent_padding = int(0.12 * 72 * scale)  # 0.12 inch padding from border
    draw.rounded_rectangle(
        [margin + accent_padding, margin + accent_padding, 
         img_width - margin - accent_padding, margin + accent_padding + accent_height],
        radius=int(0.12 * 72 * scale),
        fill=accent_color,
        outline=None
    )
    
    # Title - centered in accent stripe
    title_text = "Universal Sorting Mat"
    title_bbox = draw.textbbox((0, 0), title_text, font=fonts['title'])
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    title_y = margin + accent_padding + (accent_height - title_h) // 2
    draw.text(((img_width - title_w) // 2, title_y), title_text,
              fill='white', font=fonts['title'])
    
    # Instructions below accent stripe
    instr_y = margin + accent_padding + accent_height + int(15 * scale)
    instr_text = "Cut out picture cards and sort them into the correct boxes."
    instr_bbox = draw.textbbox((0, 0), instr_text, font=fonts['instruction'])
    instr_w = instr_bbox[2] - instr_bbox[0]
    draw.text(((img_width - instr_w) // 2, instr_y), instr_text,
              fill=hex_to_rgb(STEEL_BLUE), font=fonts['instruction'])
    
    # Load AAC icons
    aac_icons = []
    if aac_dir and aac_dir.exists():
        for word, filename in AAC_WORDS:
            icon = load_aac_icon(filename, mode, aac_dir)
            aac_icons.append((word, icon))
    else:
        print(f"⚠️  AAC directory not found: {aac_dir}, creating buttons without icons")
        aac_icons = [(word, None) for word, _ in AAC_WORDS]
    
    # AAC Button dimensions
    aac_button_width = int(65 * scale)  # ~65px wide
    aac_button_height = int(70 * scale)  # ~70px tall
    aac_spacing = int(12 * scale)  # Spacing between buttons
    
    # Position AAC buttons on LEFT and RIGHT sides (8 buttons each)
    # Left side: buttons 0-7, Right side: buttons 8-15
    aac_start_y = instr_y + int(50 * scale)
    aac_left_x = margin + int(15 * scale)  # 15px from border
    aac_right_x = img_width - margin - int(15 * scale) - aac_button_width
    
    # Draw LEFT side AAC buttons (8 buttons)
    for i in range(8):
        word, icon = aac_icons[i]
        button_y = aac_start_y + i * (aac_button_height + aac_spacing)
        draw_aac_button(page, draw, aac_left_x, button_y, aac_button_width, aac_button_height,
                       icon, word, fonts, mode)
    
    # Draw RIGHT side AAC buttons (8 buttons)
    for i in range(8):
        word, icon = aac_icons[i + 8]
        button_y = aac_start_y + i * (aac_button_height + aac_spacing)
        draw_aac_button(page, draw, aac_right_x, button_y, aac_button_width, aac_button_height,
                       icon, word, fonts, mode)
    
    # SORTING AREAS in center
    # Calculate center area between AAC buttons
    center_left = aac_left_x + aac_button_width + int(20 * scale)
    center_right = aac_right_x - int(20 * scale)
    center_width = center_right - center_left
    center_y = aac_start_y
    
    # 2-way sorting (two boxes side by side)
    box_2way_width = (center_width - int(15 * scale)) // 2
    box_2way_height = int(140 * scale)
    
    draw.text((center_left, center_y - int(20 * scale)), "2-Way Sort:",
              fill=hex_to_rgb(BRAND_NAVY), font=fonts['subtitle'])
    
    draw_sorting_box(draw, center_left, center_y, box_2way_width, box_2way_height, 
                    "Category 1", fonts, mode)
    draw_sorting_box(draw, center_left + box_2way_width + int(15 * scale), center_y, 
                    box_2way_width, box_2way_height, "Category 2", fonts, mode)
    
    # 3-way sorting (three boxes)
    three_way_y = center_y + box_2way_height + int(50 * scale)
    box_3way_width = (center_width - 2 * int(10 * scale)) // 3
    box_3way_height = int(120 * scale)
    
    draw.text((center_left, three_way_y - int(20 * scale)), "3-Way Sort:",
              fill=hex_to_rgb(BRAND_NAVY), font=fonts['subtitle'])
    
    for i in range(3):
        box_x = center_left + i * (box_3way_width + int(10 * scale))
        draw_sorting_box(draw, box_x, three_way_y, box_3way_width, box_3way_height,
                        f"Category {i+1}", fonts, mode)
    
    # Yes/No sorting (two boxes)
    yesno_y = three_way_y + box_3way_height + int(50 * scale)
    box_yesno_width = (center_width - int(15 * scale)) // 2
    box_yesno_height = int(100 * scale)
    
    draw.text((center_left, yesno_y - int(20 * scale)), "Yes/No Sort:",
              fill=hex_to_rgb(BRAND_NAVY), font=fonts['subtitle'])
    
    draw_sorting_box(draw, center_left, yesno_y, box_yesno_width, box_yesno_height,
                    "YES", fonts, mode)
    draw_sorting_box(draw, center_left + box_yesno_width + int(15 * scale), yesno_y,
                    box_yesno_width, box_yesno_height, "NO", fonts, mode)
    
    # Footer - Two lines inside border
    # Line 1: Pack code | Theme | Page X/Y
    footer_y = img_height - margin - int(45 * scale)  # Inside border
    footer_line1 = f"{pack_code} | {theme_name} | Page {page_num}/{total_pages}"
    footer1_bbox = draw.textbbox((0, 0), footer_line1, font=fonts['footer'])
    footer1_w = footer1_bbox[2] - footer1_bbox[0]
    draw.text(((img_width - footer1_w) // 2, footer_y), footer_line1,
              fill=hex_to_rgb(BRAND_NAVY), font=fonts['footer'])
    
    # Line 2: Copyright with star logo
    copyright_y = img_height - margin - int(25 * scale)
    copyright_text = "© 2025 Small Wins Studio. All rights reserved. • PCS® symbols used with active PCS Maker Personal License."
    
    # Calculate text position
    copyright_bbox = draw.textbbox((0, 0), copyright_text, font=fonts['copyright'])
    copyright_w = copyright_bbox[2] - copyright_bbox[0]
    text_start_x = (img_width - copyright_w) // 2
    
    # Try to load and add Small Wins Studio star logo
    try:
        star_path = Path("assets/branding/small_wins_logo.png/star.png")
        if star_path.exists():
            star_img = Image.open(star_path).convert('RGBA')
            star_height = int(28 * scale)
            star_aspect = star_img.width / star_img.height
            star_width = int(star_height * star_aspect)
            star_img = star_img.resize((star_width, star_height), Image.Resampling.LANCZOS)
            
            # Position star before text
            star_logo_x = text_start_x - star_width - int(8 * scale)
            star_y = copyright_y - int(6 * scale)
            page.paste(star_img, (star_logo_x, star_y), 
                      star_img if star_img.mode == 'RGBA' else None)
    except Exception as e:
        print(f"⚠️  Could not load star logo: {e}")
    
    # Draw copyright text
    draw.text((text_start_x, copyright_y), copyright_text,
              fill=FOOTER_GREY, font=fonts['copyright'])
    
    return page


def pil_to_imagereader(img: Image.Image) -> ImageReader:
    """Convert PIL Image to ReportLab ImageReader"""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def generate_sorting_mats(pack_code: str = "SORT01", theme_name: str = "Universal Sorting",
                         output_dir: Optional[Path] = None, aac_dir: Optional[Path] = None):
    """Generate complete sorting mat pack - color and B&W versions
    
    Args:
        pack_code: Product code (e.g., "SORT01")
        theme_name: Theme name for the sorting mats
        output_dir: Output directory for PDFs (default: OUTPUT)
        aac_dir: Path to AAC core word icons (default: assets/global/aac_core)
    """
    
    print(f"\n{'='*70}")
    print(f"  📊 GENERATING UNIVERSAL SORTING MAT: {pack_code}")
    print(f"  Theme: {theme_name}")
    print(f"  Design Constitution Compliant - Small Wins Studio")
    print(f"{'='*70}\n")
    
    # Set defaults
    if output_dir is None:
        output_dir = Path("OUTPUT")
    if aac_dir is None:
        aac_dir = Path("assets/global/aac_core")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check AAC directory
    if not aac_dir.exists():
        print(f"⚠️  AAC directory not found: {aac_dir}")
        print(f"   Creating sorting mat without AAC icons\n")
    else:
        print(f"✅ AAC icons directory found: {aac_dir}\n")
    
    print(f"📝 Pack Details:")
    print(f"   Code: {pack_code}")
    print(f"   Theme: {theme_name}")
    print(f"   AAC Buttons: {len(AAC_WORDS)} core words\n")
    
    print(f"📄 Creating pages...\n")
    
    saved_pages = []
    total_pages = 2  # 1 color + 1 B&W
    
    # Create COLOR version
    print(f"   Creating COLOR sorting mat...")
    color_page = create_sorting_mat_page(pack_code, theme_name, 1, total_pages, 
                                         mode="color", aac_dir=aac_dir)
    saved_pages.append(("color", color_page))
    
    # Create B&W version
    print(f"   Creating B&W sorting mat...")
    bw_page = create_sorting_mat_page(pack_code, theme_name, 2, total_pages,
                                      mode="bw", aac_dir=aac_dir)
    saved_pages.append(("bw", bw_page))
    
    print(f"\n💾 Saving PDFs...\n")
    
    # Save PDFs
    for mode, page_img in saved_pages:
        pdf_path = output_dir / f"{pack_code}_sorting_mat_{mode}.pdf"
        
        # Create PDF using reportlab
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.setTitle(f"Universal Sorting Mat ({mode.upper()})")
        
        # Convert PIL image to ImageReader and add to PDF
        img_reader = pil_to_imagereader(page_img)
        c.drawImage(img_reader, 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
        
        c.save()
        print(f"   ✅ {mode.upper()}: {pdf_path}")
    
    print(f"\n{'='*70}")
    print(f"  ✅ SUCCESS! Generated {len(saved_pages)} sorting mat PDFs")
    print(f"  📁 Location: {output_dir}")
    print(f"  © 2025 Small Wins Studio")
    print(f"{'='*70}\n")
    
    return True


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    p = argparse.ArgumentParser(
        description="Generate Universal Sorting Mat with AAC core words (Design Constitution compliant)"
    )
    p.add_argument("--pack_code", default="SORT01", type=str, 
                   help="Product code (default: SORT01)")
    p.add_argument("--theme", default="Universal Sorting", type=str,
                   help="Theme name (default: Universal Sorting)")
    p.add_argument("--output_dir", default="OUTPUT", type=str,
                   help="Output folder for PDFs (default: OUTPUT)")
    p.add_argument("--aac_dir", default="assets/global/aac_core", type=str,
                   help="Directory containing AAC core word images (default: assets/global/aac_core)")
    return p.parse_args()


def main() -> None:
    """Main entry point"""
    args = parse_args()
    
    output_dir = Path(args.output_dir).expanduser().resolve()
    aac_dir = Path(args.aac_dir).expanduser().resolve()
    
    generate_sorting_mats(
        pack_code=args.pack_code,
        theme_name=args.theme,
        output_dir=output_dir,
        aac_dir=aac_dir
    )


if __name__ == "__main__":
    main()
