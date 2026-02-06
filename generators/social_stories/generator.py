#!/usr/bin/env python3
"""
Social Stories Generator for Small Wins Studio
Generates beautiful, accessible social stories PDFs from text content
"""

import json
import os
import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class SocialStoryGenerator:
    """Generator for social stories following Small Wins Studio branding"""
    
    def __init__(self, story_path, output_dir="exports/social_stories"):
        """
        Initialize the generator
        
        Args:
            story_path: Path to the story text file
            output_dir: Directory for output PDFs
        """
        self.story_path = Path(story_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load global config
        config_path = Path(__file__).parent.parent.parent / "themes" / "global_config.json"
        with open(config_path) as f:
            self.config = json.load(f)
        
        # Extract story data
        self.story_data = self._parse_story_file()
        
        # Page dimensions (US Letter)
        self.page_width = 8.5 * inch
        self.page_height = 11 * inch
        self.margin = 0.5 * inch
        
        # Colors from config
        self.navy = HexColor(self.config['branding']['brand_colours']['navy'])
        self.teal = HexColor(self.config['branding']['brand_colours']['teal'])
        self.gold = HexColor(self.config['branding']['brand_colours']['gold'])
        self.border_color = HexColor(self.config['page_layout']['border_colour'])
        
        # Try to register Comic Sans font (accessible font for learners)
        self._register_fonts()
        
    def _register_fonts(self):
        """Try to register Comic Sans MS font if available"""
        try:
            # Try common Comic Sans MS paths
            possible_paths = [
                "/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS.ttf",
                "/usr/share/fonts/truetype/msttcorefonts/comic.ttf",
                "C:\\Windows\\Fonts\\comic.ttf",
                "C:\\Windows\\Fonts\\comicbd.ttf",
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pdfmetrics.registerFont(TTFont('ComicSans', path))
                    self.primary_font = 'ComicSans'
                    self.primary_font_bold = 'ComicSans'
                    print(f"✓ Comic Sans MS font registered from {path}")
                    return
            
            # Fallback to Helvetica
            self.primary_font = 'Helvetica'
            self.primary_font_bold = 'Helvetica-Bold'
            print("ℹ Using Helvetica (Comic Sans not found)")
            
        except Exception as e:
            # Fallback to Helvetica on any error
            self.primary_font = 'Helvetica'
            self.primary_font_bold = 'Helvetica-Bold'
            print(f"ℹ Using Helvetica (Comic Sans registration failed: {e})")
    
    def _parse_story_file(self):
        """Parse the story text file to extract metadata and pages"""
        with open(self.story_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract title
        title_match = re.search(r'^# SOCIAL STORY: (.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Untitled Story"
        
        # Extract subtitle
        subtitle_match = re.search(r'^## (.+)$', content, re.MULTILINE)
        subtitle = subtitle_match.group(1).strip() if subtitle_match else ""
        
        # Extract all pages
        pages = []
        page_pattern = r'## (PAGE \d+): (.+?)\n\n\*\*TEXT:\*\*\n```\n(.+?)\n```'
        
        for match in re.finditer(page_pattern, content, re.DOTALL):
            page_num = match.group(1)
            page_title = match.group(2).strip()
            page_text = match.group(3).strip()
            
            pages.append({
                'number': page_num,
                'title': page_title,
                'text': page_text
            })
        
        return {
            'title': title,
            'subtitle': subtitle,
            'pages': pages
        }
    
    def _draw_border(self, c):
        """Draw the rounded rectangle border"""
        border_radius = self.config['page_layout']['border_corner_radius_inches'] * inch
        c.setStrokeColor(self.border_color)
        c.setLineWidth(self.config['page_layout']['border_stroke_px'])
        c.roundRect(
            self.margin,
            self.margin,
            self.page_width - 2 * self.margin,
            self.page_height - 2 * self.margin,
            border_radius
        )
    
    def _draw_footer(self, c, page_num, total_pages):
        """Draw the footer with copyright info"""
        footer_text = f"{self.story_data['title']} | Page {page_num}/{total_pages} © {self.config['branding']['copyright_year']} Small Wins Studio. {self.config['branding']['pcs_notice']}"
        
        c.setFont(self.primary_font, 8)
        c.setFillColor(HexColor(self.config['typography']['footer_colour']))
        
        footer_y = self.margin + 0.2 * inch
        c.drawString(self.margin + 0.2 * inch, footer_y, footer_text)
    
    def _draw_title_stripe(self, c, title, subtitle=None):
        """Draw the colored title stripe at top of page"""
        stripe_height = self.config['page_layout']['accent_stripe_height_inches'] * inch
        stripe_padding = self.config['page_layout']['accent_stripe_padding_inches'] * inch
        border_radius = self.config['page_layout']['border_corner_radius_inches'] * inch
        
        stripe_y = self.page_height - self.margin - stripe_padding - stripe_height
        
        # Draw stripe background
        c.setFillColor(self.teal)
        c.roundRect(
            self.margin + stripe_padding,
            stripe_y,
            self.page_width - 2 * self.margin - 2 * stripe_padding,
            stripe_height,
            border_radius,
            fill=1,
            stroke=0
        )
        
        # Draw title text
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont(self.primary_font_bold, 18)
        text_y = stripe_y + stripe_height / 2 - 6
        c.drawCentredString(self.page_width / 2, text_y, title)
        
        if subtitle:
            c.setFont(self.primary_font, 12)
            c.drawCentredString(self.page_width / 2, text_y - 18, subtitle)
    
    def _draw_image_placeholder(self, c, x, y, width, height):
        """Draw a placeholder box for images"""
        # Draw dotted border box
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.setLineWidth(2)
        c.setDash(6, 3)
        c.rect(x, y, width, height)
        c.setDash()  # Reset to solid
        
        # Add centered text
        c.setFillColor(HexColor("#999999"))
        c.setFont(self.primary_font, 14)
        c.drawCentredString(x + width/2, y + height/2 + 10, "[ Image Placeholder ]")
        c.setFont(self.primary_font, 10)
        c.drawCentredString(x + width/2, y + height/2 - 10, "Add Boardmaker icon here")
    
    def _wrap_text(self, text, max_width, font_name, font_size):
        """Wrap text to fit within max_width"""
        from reportlab.pdfbase.pdfmetrics import stringWidth
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            width = stringWidth(test_line, font_name, font_size)
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _draw_page_content(self, c, page_data, page_num, total_pages):
        """Draw content for a story page"""
        # Draw border
        self._draw_border(c)
        
        # Draw footer
        self._draw_footer(c, page_num, total_pages)
        
        # Draw title stripe with page title
        self._draw_title_stripe(c, page_data['title'])
        
        # Content area dimensions
        content_top = self.page_height - self.margin - 1 * inch
        content_bottom = self.margin + 0.6 * inch
        content_left = self.margin + 0.3 * inch
        content_right = self.page_width - self.margin - 0.3 * inch
        content_width = content_right - content_left
        
        # Large image placeholder (top 60% of content area)
        image_height = 4 * inch
        image_width = 5 * inch
        image_x = (self.page_width - image_width) / 2
        image_y = content_top - image_height - 0.3 * inch
        
        self._draw_image_placeholder(c, image_x, image_y, image_width, image_height)
        
        # Text content (bottom 40% of content area)
        text_y = image_y - 0.5 * inch
        
        # Split text into lines, keeping ALL content including bullets
        lines = [line.strip() for line in page_data['text'].split('\n') if line.strip()]
        
        c.setFillColor(self.navy)
        c.setFont(self.primary_font, 14)  # Slightly smaller for more content
        
        current_y = text_y
        for line in lines:  # Use ALL lines, not just first 3
            if not line.startswith('#'):  # Skip markdown headers
                # Wrap text to fit width
                wrapped_lines = self._wrap_text(line, content_width, self.primary_font, 14)
                
                for wrapped_line in wrapped_lines:
                    if current_y > content_bottom:
                        c.drawString(content_left, current_y, wrapped_line)
                        current_y -= 20  # Tighter spacing to fit more
                    else:
                        # Text overflow - stop rendering
                        break
                
                # Small gap between logical lines
                current_y -= 4
    
    def generate_pdf(self):
        """Generate the complete social story PDF"""
        story_name = self.story_path.stem
        output_path = self.output_dir / f"{story_name}.pdf"
        
        c = canvas.Canvas(str(output_path), pagesize=letter)
        
        # Generate cover page
        self._draw_border(c)
        self._draw_footer(c, 1, len(self.story_data['pages']) + 1)
        
        # Cover title
        c.setFillColor(self.navy)
        c.setFont(self.primary_font_bold, 32)
        c.drawCentredString(self.page_width / 2, self.page_height - 2 * inch, self.story_data['title'])
        
        # Subtitle
        c.setFont(self.primary_font, 18)
        c.setFillColor(self.teal)
        c.drawCentredString(self.page_width / 2, self.page_height - 2.5 * inch, self.story_data['subtitle'])
        
        # Cover image placeholder
        cover_img_width = 5 * inch
        cover_img_height = 5 * inch
        cover_img_x = (self.page_width - cover_img_width) / 2
        cover_img_y = self.page_height / 2 - cover_img_height / 2
        
        self._draw_image_placeholder(c, cover_img_x, cover_img_y, cover_img_width, cover_img_height)
        
        # Branding
        c.setFont(self.primary_font, 14)
        c.setFillColor(self.gold)
        c.drawCentredString(self.page_width / 2, 2 * inch, "A Social Story")
        c.drawCentredString(self.page_width / 2, 1.7 * inch, "by Small Wins Studio")
        
        c.showPage()
        
        # Generate story pages
        for idx, page in enumerate(self.story_data['pages'], start=2):
            self._draw_page_content(c, page, idx, len(self.story_data['pages']) + 1)
            c.showPage()
        
        c.save()
        print(f"✓ Generated: {output_path}")
        return output_path


def generate_all_stories(input_dir="assets/social_stories", output_dir="exports/social_stories"):
    """Generate PDFs for all social stories in the input directory"""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' not found")
        return
    
    # Find all story text files
    story_files = []
    for item in input_path.iterdir():
        if item.is_dir():
            txt_files = list(item.glob("*.txt"))
            story_files.extend(txt_files)
    
    if not story_files:
        print(f"No story files found in {input_dir}")
        return
    
    print(f"Found {len(story_files)} social stories to generate:")
    for story in story_files:
        print(f"  - {story.name}")
    
    print("\nGenerating PDFs...")
    for story_file in story_files:
        try:
            generator = SocialStoryGenerator(story_file, output_dir)
            generator.generate_pdf()
        except Exception as e:
            print(f"✗ Error generating {story_file.name}: {e}")
    
    print(f"\n✓ All stories generated in: {output_dir}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate social story PDFs")
    parser.add_argument(
        "--story",
        help="Path to a specific story file (generates single story)"
    )
    parser.add_argument(
        "--input-dir",
        default="assets/social_stories",
        help="Directory containing story folders (default: assets/social_stories)"
    )
    parser.add_argument(
        "--output-dir",
        default="exports/social_stories",
        help="Output directory for PDFs (default: exports/social_stories)"
    )
    
    args = parser.parse_args()
    
    if args.story:
        generator = SocialStoryGenerator(args.story, args.output_dir)
        generator.generate_pdf()
    else:
        generate_all_stories(args.input_dir, args.output_dir)
