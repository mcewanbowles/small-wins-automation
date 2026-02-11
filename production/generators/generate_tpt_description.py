#!/usr/bin/env python3
"""
TpT Description Generator
Creates SEO-optimized TpT listing text for each product level.
Reads from theme JSON and generates formatted description files.
"""

import json
from pathlib import Path
from datetime import datetime

# Constants
BASE_DIR = Path(__file__).parent.parent.parent
THEMES_DIR = BASE_DIR / "themes"
OUTPUT_DIR = BASE_DIR / "production" / "marketing"


def load_theme(theme_id: str) -> dict:
    """Load theme configuration from JSON."""
    theme_path = THEMES_DIR / f"{theme_id}.json"
    with open(theme_path, 'r') as f:
        return json.load(f)


def generate_matching_description(theme: dict, level: str, level_config: dict) -> str:
    """Generate TpT description for a matching product."""
    theme_name = theme.get("theme_name", "")
    level_name = level_config.get("name", "")
    description = level_config.get("description", "")
    image_type = level_config.get("image_type", "")
    
    # SEO Keywords
    seo_keywords = [
        "special education", "SPED", "autism", "ASD", "early childhood",
        "matching activity", "file folder game", "adapted book", 
        "task box", "work task", "visual learning", "hands-on learning",
        theme_name, level_name, "differentiated instruction"
    ]
    
    description_text = f"""
📚 {theme_name} - Matching Activity {level}: {level_name}

✨ WHAT'S INCLUDED:
• Complete matching activity pages
• Ready-to-cut picture cutouts
• Colour-coded storage labels
• Quick Start Guide
• Terms of Use

🎯 LEVEL DESCRIPTION:
{level}: {level_name}
{description}
Image Type: {image_type}

👩‍🏫 PERFECT FOR:
• Special Education (SPED) classrooms
• Autism (ASD) support
• Early childhood intervention
• Occupational therapy
• Speech therapy
• Home learning

📋 HOW TO USE:
1. Print and laminate for durability
2. Cut out the matching pieces
3. Add velcro dots (hook on pieces, loop on board)
4. Store in labelled bags or containers

💡 TEACHING TIPS:
• Start with errorless matching to build confidence
• Use hand-over-hand prompting as needed
• Praise all attempts and correct responses
• Progress through levels as skills develop

🌟 PART OF A DIFFERENTIATED SERIES:
This product is part of our {theme_name} collection with 5 complete levels of difficulty. Perfect for classrooms with diverse learners!

📦 SAVE WITH BUNDLES:
Check out our complete {theme_name} bundle for the best value!

❤️ SUPPORT A NEW BUSINESS:
Thank you for supporting Small Wins Studio! We're a new teacher-author dedicated to creating high-quality, practical resources. Your review means the world to us!

---
© {datetime.now().year} Small Wins Studio
Terms of Use: For personal classroom use only. Please purchase additional licenses for other teachers.

---
SEO KEYWORDS:
{', '.join(seo_keywords)}
"""
    return description_text


def generate_all_descriptions(theme_id: str, product_type: str = "matching") -> None:
    """Generate descriptions for all levels of a product."""
    theme = load_theme(theme_id)
    theme_name = theme.get("theme_name", theme_id)
    
    # Create output directory
    output_dir = OUTPUT_DIR / theme_id / product_type
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if product_type == "matching":
        levels = theme.get("matching", {}).get("levels", {})
        
        for level, level_config in levels.items():
            description = generate_matching_description(theme, level, level_config)
            
            # Save description
            filename = f"{theme_id}_{product_type}_{level}_description.txt"
            output_path = output_dir / filename
            
            with open(output_path, 'w') as f:
                f.write(description)
            
            print(f"✅ Generated: {output_path}")
        
        # Also generate freebie description
        freebie_desc = generate_freebie_description(theme, product_type)
        freebie_path = output_dir / f"{theme_id}_{product_type}_freebie_description.txt"
        with open(freebie_path, 'w') as f:
            f.write(freebie_desc)
        print(f"✅ Generated: {freebie_path}")
    
    print(f"\n📁 All descriptions saved to: {output_dir}")


def generate_freebie_description(theme: dict, product_type: str) -> str:
    """Generate description for freebie product."""
    theme_name = theme.get("theme_name", "")
    
    return f"""
🎁 FREE SAMPLE: {theme_name} - Matching Activity Freebie

✨ TRY BEFORE YOU BUY!
Get a taste of our popular {theme_name} matching activities with this FREE sample!

📦 WHAT'S INCLUDED:
• 1 sample page from each of 5 levels
• Ready-to-cut picture cutouts
• Colour-coded storage labels
• Quick Start Guide
• Terms of Use

🎯 5 LEVELS OF DIFFERENTIATION:
• Level 1: Errorless (identical matching)
• Level 2: Distractors (increasing challenge)
• Level 3: Picture + Text (match to words)
• Level 4: Generalisation (icon to photo)
• Level 5: Advanced (B&W to colour)

👩‍🏫 PERFECT FOR:
• Special Education (SPED) classrooms
• Autism (ASD) support
• Early childhood intervention
• Trying before buying the full set!

💡 LOVE IT? GET THE FULL SET:
Check out our complete {theme_name} Matching bundle with all 5 levels!

❤️ FOLLOW FOR UPDATES:
Follow our store for new products and freebies!

---
© {datetime.now().year} Small Wins Studio
"""


if __name__ == "__main__":
    print("=" * 60)
    print("TpT Description Generator")
    print("=" * 60)
    
    # Generate for Brown Bear Matching
    generate_all_descriptions("brown_bear", "matching")
    
    print("\n✅ All descriptions generated successfully!")
