#!/usr/bin/env python3
"""
Generate Brown Bear samples for the 5 prioritized generators:
1. Matching Cards (all levels)
2. WH Questions  
3. Yes/No Cards
4. AAC Board
5. Cut-and-Paste Activity (Label the Picture)
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from themes.theme_loader import load_theme
from generators.matching_cards import generate_matching_cards_dual_mode
from generators.wh_questions import generate_wh_questions_dual_mode
from generators.yes_no_cards import generate_yes_no_cards_dual_mode
from generators.aac_book_board import generate_aac_board_set_dual_mode
# Note: label_the_picture has compatibility issues - skipping for now
# from generators.label_the_picture import generate_label_cards_dual_mode


def create_output_dir():
    """Create samples/brown_bear directory"""
    output_dir = Path('samples/brown_bear')
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir)


def generate_matching_cards_samples(theme, output_dir):
    """Generate Matching Cards samples at all differentiation levels"""
    print("\n" + "="*60)
    print("GENERATING: Matching Cards (All Levels)")
    print("="*60)
    
    # Prepare items from Brown Bear vocab
    items = []
    for word in theme.vocab[:6]:  # Use first 6 words
        # Try to find matching icon
        icon_path = theme.get_icon_path(f'{word}.png')
        if not icon_path:
            # Try with capital letter
            icon_path = theme.get_icon_path(f'{word.capitalize()}.png')
        if not icon_path:
            # Try variations
            for icon_file in theme.icons:
                if word.lower() in icon_file.lower():
                    icon_path = theme.get_icon_path(icon_file)
                    break
        
        if icon_path:
            items.append({
                'image': os.path.basename(icon_path),
                'label': word.capitalize()
            })
    
    print(f"Using {len(items)} items for matching cards")
    
    # Generate all 4 levels
    results = {}
    for level in [1, 2, 3, 4]:
        print(f"\n--- Level {level} ---")
        try:
            paths = generate_matching_cards_dual_mode(
                items=items,
                level=level,
                card_size='large',
                cards_per_page=6,
                output_dir=output_dir,
                theme_name='Brown_Bear_Matching',
                include_storage_label=True
            )
            results[f'level_{level}'] = paths
            print(f"✓ Level {level} complete: {paths}")
        except Exception as e:
            print(f"✗ Level {level} failed: {e}")
            import traceback
            traceback.print_exc()
    
    return results


def generate_wh_questions_samples(theme, output_dir):
    """Generate WH Questions samples"""
    print("\n" + "="*60)
    print("GENERATING: WH Questions")
    print("="*60)
    
    # Create question data using Brown Bear theme
    question_data = [
        {
            'image': 'Brown bear.png',
            'question': 'What do you see?',
            'choices': ['bear', 'duck', 'frog', 'cat'],
            'answer': 'bear'
        },
        {
            'image': 'Blue horse.png',
            'question': 'What color is the horse?',
            'choices': ['red', 'blue', 'green', 'yellow'],
            'answer': 'blue'
        },
        {
            'image': 'Black sheep.png',
            'question': 'What animal is this?',
            'choices': ['bear', 'sheep', 'duck', 'dog'],
            'answer': 'sheep'
        }
    ]
    
    try:
        paths = generate_wh_questions_dual_mode(
            question_data=question_data,
            folder_type='color',
            level=1,
            theme_name='Brown_Bear_WH',
            output_dir=output_dir,
            include_storage_label=True
        )
        print(f"✓ WH Questions complete: {paths}")
        return paths
    except Exception as e:
        print(f"✗ WH Questions failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_yes_no_cards_samples(theme, output_dir):
    """Generate Yes/No Cards samples"""
    print("\n" + "="*60)
    print("GENERATING: Yes/No Cards")
    print("="*60)
    
    # Prepare items from Brown Bear vocab
    items = []
    for word in theme.vocab[:8]:  # Use first 8 words
        icon_path = theme.get_icon_path(f'{word}.png')
        if not icon_path:
            icon_path = theme.get_icon_path(f'{word.capitalize()}.png')
        if not icon_path:
            for icon_file in theme.icons:
                if word.lower() in icon_file.lower():
                    icon_path = theme.get_icon_path(icon_file)
                    break
        
        if icon_path:
            items.append({
                'image': os.path.basename(icon_path),
                'label': word.capitalize()
            })
    
    print(f"Using {len(items)} items for Yes/No cards")
    
    try:
        paths = generate_yes_no_cards_dual_mode(
            items=items,
            theme_name='Brown_Bear_YesNo',
            output_dir=output_dir,
            include_standard=True,
            include_real_images=False,
            include_errorless=True,
            include_cut_paste=True,
            include_storage_label=True,
            folder_type='images'
        )
        print(f"✓ Yes/No Cards complete: {paths}")
        return paths
    except Exception as e:
        print(f"✗ Yes/No Cards failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_aac_board_samples(theme, output_dir):
    """Generate AAC Board samples"""
    print("\n" + "="*60)
    print("GENERATING: AAC Board")
    print("="*60)
    
    # Create fringe vocabulary from Brown Bear theme
    fringe_vocab = []
    for word in theme.vocab:
        icon_path = theme.get_icon_path(f'{word}.png')
        if not icon_path:
            icon_path = theme.get_icon_path(f'{word.capitalize()}.png')
        if not icon_path:
            for icon_file in theme.icons:
                if word.lower() in icon_file.lower():
                    icon_path = theme.get_icon_path(icon_file)
                    break
        
        if icon_path:
            fringe_vocab.append({
                'word': word.capitalize(),
                'icon': os.path.basename(icon_path),
                'part_of_speech': 'noun'  # Default for animals
            })
    
    print(f"Using {len(fringe_vocab)} items for AAC board")
    
    try:
        paths = generate_aac_board_set_dual_mode(
            fringe_vocab=fringe_vocab,
            theme_name='Brown_Bear_AAC',
            output_dir=output_dir,
            grid_size=(5, 6),  # 5x6 grid
            use_color_coding=True,
            with_cutout_icons=True,
            folder_type='aac',
            include_storage_label=True
        )
        print(f"✓ AAC Board complete: {paths}")
        return paths
    except Exception as e:
        print(f"✗ AAC Board failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_cut_paste_samples(theme, output_dir):
    """Generate Cut-and-Paste Activity (Label the Picture) samples"""
    print("\n" + "="*60)
    print("GENERATING: Cut-and-Paste Activity (Label the Picture)")
    print("="*60)
    
    # Prepare theme data for label_the_picture generator
    theme_data = {
        'name': 'Brown Bear',
        'fringe_icons': []
    }
    
    # Add fringe icons from theme
    for word in theme.vocab[:6]:  # Use first 6 words
        icon_path = theme.get_icon_path(f'{word}.png')
        if not icon_path:
            icon_path = theme.get_icon_path(f'{word.capitalize()}.png')
        if not icon_path:
            for icon_file in theme.icons:
                if word.lower() in icon_file.lower():
                    icon_path = theme.get_icon_path(icon_file)
                    break
        
        if icon_path:
            theme_data['fringe_icons'].append({
                'word': word.capitalize(),
                'icon_path': icon_path
            })
    
    print(f"Using {len(theme_data['fringe_icons'])} items for cut-and-paste")
    
    try:
        paths = generate_label_cards_dual_mode(
            theme_data=theme_data,
            output_dir=output_dir
        )
        print(f"✓ Cut-and-Paste complete: {paths}")
        return paths
    except Exception as e:
        print(f"✗ Cut-and-Paste failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function to generate all priority samples"""
    print("="*60)
    print("BROWN BEAR PRIORITY SAMPLE GENERATION")
    print("="*60)
    print("\nGenerating samples for 4 prioritized generators:")
    print("1. Matching Cards (all levels)")
    print("2. WH Questions")
    print("3. Yes/No Cards")
    print("4. AAC Board")
    print("Note: Cut-and-Paste has compatibility issues - will be addressed separately")
    print()
    
    # Load Brown Bear theme
    print("Loading Brown Bear theme...")
    theme = load_theme('brown_bear', mode='color')
    print(f"✓ Theme loaded: {theme.name}")
    print(f"  - {len(theme.vocab)} vocabulary words")
    print(f"  - {len(theme.icons)} icon files")
    
    # Create output directory
    output_dir = create_output_dir()
    print(f"✓ Output directory: {output_dir}")
    
    # Generate samples for each generator
    results = {}
    
    try:
        results['matching_cards'] = generate_matching_cards_samples(theme, output_dir)
    except Exception as e:
        print(f"CRITICAL ERROR in Matching Cards: {e}")
    
    try:
        results['wh_questions'] = generate_wh_questions_samples(theme, output_dir)
    except Exception as e:
        print(f"CRITICAL ERROR in WH Questions: {e}")
    
    try:
        results['yes_no_cards'] = generate_yes_no_cards_samples(theme, output_dir)
    except Exception as e:
        print(f"CRITICAL ERROR in Yes/No Cards: {e}")
    
    try:
        results['aac_board'] = generate_aac_board_samples(theme, output_dir)
    except Exception as e:
        print(f"CRITICAL ERROR in AAC Board: {e}")
    
    # Note: Skipping cut_paste due to compatibility issues
    # try:
    #     results['cut_paste'] = generate_cut_paste_samples(theme, output_dir)
    # except Exception as e:
    #     print(f"CRITICAL ERROR in Cut-and-Paste: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("GENERATION COMPLETE - SUMMARY")
    print("="*60)
    
    for generator_name, result in results.items():
        if result:
            print(f"✓ {generator_name}: SUCCESS")
        else:
            print(f"✗ {generator_name}: FAILED")
    
    print(f"\n✓ All outputs saved to: {output_dir}")
    print("\nCheck the samples/brown_bear/ folder for generated PDFs")


if __name__ == '__main__':
    main()
