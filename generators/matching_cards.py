"""
Matching Cards Generator for TpT Automation System

Generates matching activities following the specifications in:
/design/product_specs/matching.md

Layout: 5×2 grid
- Left column: Target boxes (navy border, rounded, shadow)
- Right column: Matching boxes (cards to match)
- Optional velcro placeholder boxes

Levels:
- Level 1: Errorless (watermarks, no distractors)
- Level 2: 4 targets + 1 distractor
- Level 3: 3 targets + 2 distractors  
- Level 4: 1 target + 4 distractors
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
from reportlab.lib.units import inch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    load_theme_config,
    load_global_config,
    get_level_color,
    load_theme_image,
    PDFBuilder,
    hex_to_rgb,
    inches_to_points,
    resize_image_proportional,
    get_image_center_position
)


class MatchingGenerator:
    """
    Generates matching activity pages following SPED design rules.
    """
    
    # Layout constants from matching.md specs
    GRID_ROWS = 5
    GRID_COLS = 2
    
    # Target box (left column) - per specs
    TARGET_BOX_WIDTH = 1.0 * inch  # Approximately
    TARGET_BOX_HEIGHT = 1.5 * inch
    
    # Matching box (right column) - 1.4-1.6" square per specs
    MATCH_BOX_SIZE = 1.5 * inch
    
    # Spacing
    ROW_SPACING = 0.3 * inch
    COL_SPACING = 0.5 * inch
    
    # Border styling per Design Constitution
    BORDER_COLOR = "#1E3A5F"  # Navy
    BORDER_THICKNESS = 2.0
    CORNER_RADIUS = 0.12 * inch
    
    def __init__(self, theme_name: str, output_dir: Path):
        """
        Initialize the matching generator.
        
        Args:
            theme_name: Name of the theme (e.g., "brown_bear")
            output_dir: Directory for output files
        """
        self.theme_name = theme_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configs
        self.theme_config = load_theme_config(theme_name)
        self.global_config = load_global_config()
        
        print(f"Matching Generator initialized for theme: {theme_name}")
    
    def generate_level_page(self, level: int, vocabulary_words: List[str], 
                           color_mode: str = "color") -> Path:
        """
        Generate a matching page for a specific level.
        
        Args:
            level: Level number (1-4)
            vocabulary_words: List of vocabulary words to use
            color_mode: "color" or "bw" (black and white)
            
        Returns:
            Path to the generated PDF
        """
        # Determine filename
        filename = f"{self.theme_name}_matching_level{level}_{color_mode}.pdf"
        output_path = self.output_dir / filename
        
        # Get level color
        level_color_hex = get_level_color(level, self.global_config)
        level_color_rgb = hex_to_rgb(level_color_hex)
        
        # Create PDF
        pdf = PDFBuilder(output_path, title=f"Matching Level {level}")
        pdf.add_page()
        
        # Add title
        pdf.draw_text(
            f"Brown Bear Matching - Level {level}",
            inches_to_points(1),
            inches_to_points(10),
            font_size=18,
            color=(0, 0, 0)
        )
        
        # Calculate grid starting position
        start_x = 1.0 * inch
        start_y = 8.5 * inch
        
        # Draw matching grid (simplified version)
        for row in range(min(5, len(vocabulary_words))):
            word = vocabulary_words[row]
            
            # Calculate positions
            y = start_y - (row * (self.TARGET_BOX_HEIGHT + self.ROW_SPACING))
            
            # LEFT: Target box (navy border)
            target_x = start_x
            border_rgb = hex_to_rgb(self.BORDER_COLOR)
            pdf.draw_border(
                target_x, y,
                self.TARGET_BOX_WIDTH, self.TARGET_BOX_HEIGHT,
                color=border_rgb,
                thickness=self.BORDER_THICKNESS,
                rounded=True,
                corner_radius=self.CORNER_RADIUS
            )
            
            # Try to load and draw icon in target box
            img = load_theme_image(self.theme_name, word, "icons")
            if img:
                # Resize to fit in target box (leaving margins)
                max_img_width = self.TARGET_BOX_WIDTH - (0.2 * inch)
                max_img_height = self.TARGET_BOX_HEIGHT - (0.2 * inch)
                
                img_resized = resize_image_proportional(
                    img,
                    int(max_img_width),
                    int(max_img_height)
                )
                
                # Save temporarily and draw
                temp_img_path = Path(f"/tmp/temp_{word}.png")
                img_resized.save(temp_img_path)
                
                # Center in box
                img_w, img_h = img_resized.size
                img_x = target_x + (self.TARGET_BOX_WIDTH - (img_w / 72)) / 2
                img_y = y + (self.TARGET_BOX_HEIGHT - (img_h / 72)) / 2
                
                pdf.draw_image(temp_img_path, img_x, img_y,
                              width=img_w / 72 * inch,
                              height=img_h / 72 * inch)
            
            # RIGHT: Matching box (with level color accent)
            match_x = start_x + self.TARGET_BOX_WIDTH + self.COL_SPACING
            
            # Draw matching box border (level color)
            pdf.draw_border(
                match_x, y,
                self.MATCH_BOX_SIZE, self.MATCH_BOX_SIZE,
                color=level_color_rgb,
                thickness=self.BORDER_THICKNESS,
                rounded=True,
                corner_radius=self.CORNER_RADIUS
            )
            
            # Draw icon in matching box too
            if img:
                img_x = match_x + (self.MATCH_BOX_SIZE - (img_w / 72)) / 2
                img_y = y + (self.MATCH_BOX_SIZE - (img_h / 72)) / 2
                
                pdf.draw_image(temp_img_path, img_x, img_y,
                              width=img_w / 72 * inch,
                              height=img_h / 72 * inch)
        
        pdf.save()
        return output_path


def main():
    """Test the matching generator."""
    print("\n" + "=" * 60)
    print("Matching Generator Test")
    print("=" * 60 + "\n")
    
    # Create generator
    generator = MatchingGenerator("brown_bear", Path("output/matching"))
    
    # Test vocabulary
    vocab = ["Brown bear", "Blue horse", "Red bird", "Yellow duck", "Green frog"]
    
    # Generate Level 1 page
    print(f"\nGenerating Level 1 page with {len(vocab)} words...")
    output_path = generator.generate_level_page(1, vocab, "color")
    print(f"✓ Generated: {output_path}")
    
    print("\n" + "=" * 60)
    print("Generation Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
