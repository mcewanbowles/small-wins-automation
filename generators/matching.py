"""Matching Activity Generator for Small Wins Studio

Generates matching activities with 4 difficulty levels according to
the Design Constitution and Master Product Specification.
"""
import argparse
from datetime import datetime
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
import os

from generators.base import BaseGenerator
from generators.pdf_utils import PageLayout


class MatchingGenerator(BaseGenerator):
    """Generator for matching activities"""
    
    def __init__(self, theme: str, output_dir: str):
        super().__init__(theme, output_dir)
        
        # Get matching configuration from theme
        self.matching_config = self.theme_config.get('matching', {})
        self.levels_config = self.matching_config.get('levels', {})
        
        # Get icons for matching (from fringe_icons or real_image_icons)
        self.icons = self.theme_config.get('fringe_icons', {})
        
        # Matching box constants
        self.BOX_SIZE = 1.1 * 72  # 1.1 inches
        self.BOX_CORNER_RADIUS = 0.12 * 72
        self.VERTICAL_SPACING = 0.3 * 72
        self.HORIZONTAL_SPACING = 1.0 * 72
        
        # Target box constants  
        self.TARGET_SIZE = 1.4 * 72  # Larger than matching boxes
        
    def generate_all_levels(self):
        """Generate all 4 levels of matching activities"""
        print(f"Generating matching activities for theme: {self.theme}")
        
        # Create output directory
        output_path = self.ensure_output_dir('matching')
        
        # Generate each level
        for level_num in range(1, 5):
            level_id = f'L{level_num}'
            if level_id in self.levels_config:
                print(f"  Generating Level {level_num}...")
                self.generate_level(level_num, output_path)
        
        # Generate cutouts and storage labels
        print("  Generating cutouts...")
        self.generate_cutouts(output_path)
        
        print("  Generating storage labels...")
        self.generate_storage_labels(output_path)
        
        print(f"✓ Matching activities generated in {output_path}")
    
    def generate_level(self, level_num: int, output_dir: Path):
        """Generate a single level in both color and B&W"""
        level_id = f'L{level_num}'
        level_config = self.levels_config.get(level_id, {})
        level_name = level_config.get('name', f'Level {level_num}')
        level_color = self.LEVEL_COLORS[level_id]
        
        # Generate color version
        color_filename = f'{self.theme}_matching_level{level_num}_color.pdf'
        self._generate_level_pdf(
            level_num,
            level_name,
            level_color,
            level_config,
            output_dir / color_filename,
            is_color=True
        )
        
        # Generate B&W version
        bw_filename = f'{self.theme}_matching_level{level_num}_bw.pdf'
        self._generate_level_pdf(
            level_num,
            level_name,
            level_color,
            level_config,
            output_dir / bw_filename,
            is_color=False
        )
    
    def _generate_level_pdf(self, level_num: int, level_name: str, level_color: str,
                           level_config: dict, output_path: Path, is_color: bool):
        """Generate a single PDF for a level"""
        c = canvas.Canvas(str(output_path), pagesize=letter)
        
        # Get icons for this level
        icon_list = list(self.icons.items())[:6]  # Use first 6 icons for demo
        
        # Determine number of pages needed (2 icons per page for demo)
        icons_per_page = 2
        total_pages = (len(icon_list) + icons_per_page - 1) // icons_per_page
        
        for page_num in range(1, total_pages + 1):
            # Get icons for this page
            start_idx = (page_num - 1) * icons_per_page
            end_idx = min(start_idx + icons_per_page, len(icon_list))
            page_icons = icon_list[start_idx:end_idx]
            
            # Create page layout
            layout = PageLayout(c, self.PAGE_WIDTH, self.PAGE_HEIGHT, 
                              self.MARGIN, self.BORDER_RADIUS)
            
            # Draw page border
            layout.draw_page_border()
            
            # Draw header
            pack_code = f"BB-M-L{level_num}"
            layout.draw_header(pack_code, page_num, total_pages)
            
            # Draw footer
            layout.draw_footer(year=self.theme_config.get('year', 2025))
            
            # Draw accent stripe
            theme_name = self.theme_config.get('theme_name', self.theme.replace('_', ' ').title())
            title = "Matching Activity"
            subtitle = theme_name
            layout.draw_accent_stripe(title, subtitle, level_color, 
                                    self.STRIPE_HEIGHT, self.STRIPE_PADDING)
            
            # Draw matching content based on level
            content_top = self.PAGE_HEIGHT - self.MARGIN - self.STRIPE_PADDING - self.STRIPE_HEIGHT - 40
            self._draw_matching_content(
                layout, page_icons, level_num, level_config, 
                content_top, is_color
            )
            
            c.showPage()
        
        c.save()
    
    def _draw_matching_content(self, layout: PageLayout, icons: list, level_num: int,
                              level_config: dict, content_top: float, is_color: bool):
        """Draw the matching activity content for a page"""
        # For Level 1 (Errorless): single column of target boxes
        # For Level 2 (Distractors): target + matching boxes
        # For demo, we'll implement Level 1 layout
        
        # Calculate layout
        start_y = content_top - 40
        
        for idx, (icon_name, icon_file) in enumerate(icons):
            # Draw target box
            box_x = self.MARGIN + 100
            box_y = start_y - (idx * (self.TARGET_SIZE + self.VERTICAL_SPACING))
            
            # Draw the box
            layout.draw_rounded_box(
                box_x, box_y,
                self.TARGET_SIZE, self.TARGET_SIZE,
                self.BOX_CORNER_RADIUS,
                stroke_width=3
            )
            
            # Draw the icon
            try:
                icon_path = self.get_icon_path(icon_file)
                layout.draw_image(
                    icon_path,
                    box_x, box_y,
                    self.TARGET_SIZE, self.TARGET_SIZE,
                    preserve_aspect=True,
                    center=True
                )
            except FileNotFoundError:
                # If icon not found, just draw the box
                pass
            
            # Draw velcro dot
            velcro_x = box_x + self.TARGET_SIZE / 2
            velcro_y = box_y + self.TARGET_SIZE / 2
            
            if level_num == 1:
                # Level 1: Add watermark
                try:
                    icon_path = self.get_icon_path(icon_file)
                    # Draw watermark behind velcro dot (lower opacity would need PIL)
                    layout.canvas.saveState()
                    layout.canvas.setFillAlpha(0.25)
                    watermark_size = self.TARGET_SIZE * 0.75
                    watermark_x = box_x + (self.TARGET_SIZE - watermark_size) / 2
                    watermark_y = box_y + (self.TARGET_SIZE - watermark_size) / 2
                    layout.draw_image(
                        icon_path,
                        watermark_x, watermark_y,
                        watermark_size, watermark_size,
                        preserve_aspect=True,
                        center=False
                    )
                    layout.canvas.restoreState()
                except FileNotFoundError:
                    pass
            
            layout.draw_velcro_dot(velcro_x, velcro_y)
            
            # Draw matching box (to the right)
            match_box_x = box_x + self.TARGET_SIZE + self.HORIZONTAL_SPACING
            match_box_y = box_y + (self.TARGET_SIZE - self.BOX_SIZE) / 2
            
            layout.draw_rounded_box(
                match_box_x, match_box_y,
                self.BOX_SIZE, self.BOX_SIZE,
                self.BOX_CORNER_RADIUS,
                stroke_width=2
            )
            
            # Draw icon in matching box (for errorless/level 1)
            if level_num == 1:
                try:
                    icon_path = self.get_icon_path(icon_file)
                    layout.draw_image(
                        icon_path,
                        match_box_x, match_box_y,
                        self.BOX_SIZE, self.BOX_SIZE,
                        preserve_aspect=True,
                        center=True
                    )
                except FileNotFoundError:
                    pass
    
    def generate_cutouts(self, output_dir: Path):
        """Generate cutout pieces page"""
        output_path = output_dir / f'{self.theme}_matching_cutouts.pdf'
        c = canvas.Canvas(str(output_path), pagesize=letter)
        
        layout = PageLayout(c, self.PAGE_WIDTH, self.PAGE_HEIGHT,
                          self.MARGIN, self.BORDER_RADIUS)
        
        # Draw page elements
        layout.draw_page_border()
        layout.draw_header("BB-M-CUT", 1, 1)
        layout.draw_footer(year=self.theme_config.get('year', 2025))
        
        # Draw title
        theme_name = self.theme_config.get('theme_name', self.theme.replace('_', ' ').title())
        title = "Cutout Matching Pieces"
        subtitle = theme_name
        layout.draw_accent_stripe(title, subtitle, self.LEVEL_COLORS['L1'],
                                self.STRIPE_HEIGHT, self.STRIPE_PADDING)
        
        # Draw 5 icons per strip
        icon_list = list(self.icons.items())[:10]  # First 10 icons
        strip_y = self.PAGE_HEIGHT - self.MARGIN - self.STRIPE_HEIGHT - 100
        strip_height = self.BOX_SIZE
        
        for strip_idx in range(2):  # 2 strips
            strip_icons = icon_list[strip_idx * 5:(strip_idx + 1) * 5]
            current_y = strip_y - (strip_idx * (strip_height + 40))
            
            for idx, (icon_name, icon_file) in enumerate(strip_icons):
                box_x = self.MARGIN + 20 + (idx * (self.BOX_SIZE + 10))
                box_y = current_y
                
                # Draw box
                layout.draw_rounded_box(
                    box_x, box_y,
                    self.BOX_SIZE, self.BOX_SIZE,
                    self.BOX_CORNER_RADIUS
                )
                
                # Draw icon
                try:
                    icon_path = self.get_icon_path(icon_file)
                    layout.draw_image(
                        icon_path,
                        box_x, box_y,
                        self.BOX_SIZE, self.BOX_SIZE,
                        preserve_aspect=True,
                        center=True
                    )
                except FileNotFoundError:
                    pass
        
        c.showPage()
        c.save()
    
    def generate_storage_labels(self, output_dir: Path):
        """Generate storage labels page"""
        output_path = output_dir / f'{self.theme}_matching_storage_labels.pdf'
        c = canvas.Canvas(str(output_path), pagesize=letter)
        
        layout = PageLayout(c, self.PAGE_WIDTH, self.PAGE_HEIGHT,
                          self.MARGIN, self.BORDER_RADIUS)
        
        # Draw page elements
        layout.draw_page_border()
        layout.draw_header("BB-M-STOR", 1, 1)
        layout.draw_footer(year=self.theme_config.get('year', 2025))
        
        # Draw title
        theme_name = self.theme_config.get('theme_name', self.theme.replace('_', ' ').title())
        title = f"{theme_name} Matching Cards"
        subtitle = "Storage Labels"
        layout.draw_accent_stripe(title, subtitle, self.LEVEL_COLORS['L1'],
                                self.STRIPE_HEIGHT, self.STRIPE_PADDING)
        
        # Draw vocabulary table (3 columns)
        table_top = self.PAGE_HEIGHT - self.MARGIN - self.STRIPE_HEIGHT - 100
        col_width = (self.PAGE_WIDTH - 2 * self.MARGIN - 100) / 3
        row_height = 60
        
        icon_list = list(self.icons.items())
        for idx, (icon_name, icon_file) in enumerate(icon_list[:9]):  # 3x3 grid
            row = idx // 3
            col = idx % 3
            
            cell_x = self.MARGIN + 50 + (col * col_width)
            cell_y = table_top - (row * row_height)
            
            # Draw icon (small)
            icon_size = 40
            try:
                icon_path = self.get_icon_path(icon_file)
                layout.draw_image(
                    icon_path,
                    cell_x, cell_y,
                    icon_size, icon_size,
                    preserve_aspect=True,
                    center=False
                )
            except FileNotFoundError:
                pass
            
            # Draw label text
            c.setFillColor(HexColor('#000000'))
            c.setFont('Helvetica', 10)
            label = icon_name.replace('_', ' ').title()
            c.drawString(cell_x + icon_size + 10, cell_y + 15, label)
        
        c.showPage()
        c.save()


def main():
    """Main entry point for the matching generator"""
    parser = argparse.ArgumentParser(description='Generate matching activities')
    parser.add_argument('--theme', required=True, help='Theme name (e.g., brown_bear)')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--level', type=int, choices=[1, 2, 3, 4],
                       help='Generate only a specific level (default: all)')
    
    args = parser.parse_args()
    
    generator = MatchingGenerator(args.theme, args.output)
    
    if args.level:
        output_path = generator.ensure_output_dir('matching')
        generator.generate_level(args.level, output_path)
        generator.generate_cutouts(output_path)
        generator.generate_storage_labels(output_path)
    else:
        generator.generate_all_levels()


if __name__ == '__main__':
    main()
