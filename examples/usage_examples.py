"""
Example usage of the SPED Resource Automation System.

This script demonstrates how to use each of the 14 generators.
Before running, ensure you have images in the appropriate folders:
- images/ for color images
- Colour_images/ for black-and-white outline images
- aac_images/ for AAC/PCS symbols
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators import *
from utils.pdf_export import create_output_directory
from utils.storage_label_helper import generate_storage_label


def example_storage_labels():
    """Example: Generate storage labels for organizing resources."""
    print("=" * 60)
    print("Generating Storage Labels...")
    print("=" * 60)
    
    output_dir = create_output_directory()
    
    # Example 1: Basic storage label with theme and activity
    label_path = generate_storage_label(
        theme_name="Brown Bear",
        activity_name="Matching Cards",
        level=1,
        output_path=f"{output_dir}/Brown_Bear_Matching_LABEL.pdf"
    )
    print(f"✓ Generated basic label: {label_path}")
    
    # Example 2: Label with custom size
    label_path = generate_storage_label(
        theme_name="Farm Animals",
        activity_name="Counting Mats",
        level=2,
        label_size='large',
        output_path=f"{output_dir}/Farm_Animals_Counting_LABEL.pdf"
    )
    print(f"✓ Generated large label: {label_path}")
    
    # Example 3: Label without level (for activities without differentiation)
    label_path = generate_storage_label(
        theme_name="Ocean Theme",
        activity_name="Bingo",
        level=None,
        output_path=f"{output_dir}/Ocean_Bingo_LABEL.pdf"
    )
    print(f"✓ Generated label without level: {label_path}")
    
    print()


def example_counting_mats():
    """Example: Generate counting mats for numbers 1-10."""
    print("Generating Counting Mats...")
    
    # Create output directory
    output_dir = create_output_directory()
    
    # Example with placeholder images (you would use actual image files)
    image_files = ['image1.png', 'image2.png', 'image3.png']
    
    # Generate counting mats for numbers 1-5
    # pages = generate_counting_mats_set(
    #     image_filenames=image_files,
    #     theme_name='Farm Animals',
    #     number_range=(1, 5),
    #     level=1,
    #     folder_type='color',
    #     output_dir=output_dir,
    #     include_storage_label=True  # Generate companion storage label
    # )
    
    print("Example: Uncomment code and add actual image files")


def example_matching_cards():
    """Example: Generate matching cards with storage labels."""
    print("Generating Matching Cards...")
    
    output_dir = create_output_directory()
    
    # Example data with storage labels
    items = [
        {'image': 'bear', 'label': 'Brown Bear'},
        {'image': 'duck', 'label': 'Yellow Duck'},
        {'image': 'frog', 'label': 'Green Frog'},
    ]
    
    # Generate matching cards with automatic storage label
    # pages = generate_matching_cards_set(
    #     items=items,
    #     level=1,
    #     card_size='large',
    #     cards_per_page=6,
    #     output_dir=output_dir,
    #     theme_name='Brown_Bear',
    #     include_storage_label=True  # Automatically generates X_LABEL.pdf
    # )
    
    print("Example: Uncomment code and add actual image files")


def example_bingo():
    """Example: Generate bingo cards with storage labels."""
    print("Generating Bingo...")
    
    output_dir = create_output_directory()
    
    # Example with storage labels
    # image_files = ['img1.png', 'img2.png', 'img3.png', 'img4.png', 'img5.png']
    
    # pages = generate_bingo_set(
    #     image_filenames=image_files,
    #     num_cards=6,
    #     grid_size=3,
    #     folder_type='color',
    #     theme_name='Animals',
    #     output_dir=output_dir,
    #     include_storage_label=True  # Generate companion label for organization
    # )
    
    print("Example: Uncomment code and add actual image files")
    image_label_pairs = [
        ('dog.png', 'Dog'),
        ('cat.png', 'Cat'),
        ('bird.png', 'Bird'),
    ]
    
    # pages = generate_matching_cards_sheet(
    #     image_label_pairs=image_label_pairs,
    #     cards_per_page=6,
    #     card_size='standard',
    #     folder_type='color',
    #     level=1,
    #     output_dir=output_dir,
    #     theme_name='Pets'
    # )
    
    print("Example: Uncomment code and add actual image files")


def example_bingo():
    """Example: Generate bingo cards."""
    print("Generating Bingo...")
    
    output_dir = create_output_directory()
    
    # Example data
    image_files = ['img1.png', 'img2.png', 'img3.png', 'img4.png', 'img5.png']
    
    # pages = generate_bingo_set(
    #     image_filenames=image_files,
    #     num_cards=4,
    #     grid_size=3,
    #     folder_type='color',
    #     theme_name='Animals',
    #     output_dir=output_dir
    # )
    
    print("Example: Uncomment code and add actual image files")


def example_sequencing():
    """Example: Generate sequencing cards."""
    print("Generating Sequencing Cards...")
    
    output_dir = create_output_directory()
    
    # Example: Steps for brushing teeth
    sequence_images = ['step1.png', 'step2.png', 'step3.png', 'step4.png']
    
    # pages = generate_sequencing_set(
    #     image_sequence=sequence_images,
    #     theme_name='Brushing Teeth',
    #     card_size='large',
    #     folder_type='color',
    #     level=1,
    #     output_dir=output_dir
    # )
    
    print("Example: Uncomment code and add actual image files")


def example_coloring_strips():
    """Example: Generate coloring strips."""
    print("Generating Coloring Strips...")
    
    output_dir = create_output_directory()
    
    # Example data (should use outline images)
    strips_data = [
        ('apple_outline.png', 'Apple'),
        ('banana_outline.png', 'Banana'),
        ('orange_outline.png', 'Orange'),
    ]
    
    # pages = generate_coloring_strips_page(
    #     image_label_pairs=strips_data,
    #     folder_type='bw_outline',
    #     theme_name='Fruits',
    #     output_dir=output_dir
    # )
    
    print("Example: Uncomment code and add actual outline image files")


def example_yes_no_questions():
    """Example: Generate yes/no questions."""
    print("Generating Yes/No Questions...")
    
    output_dir = create_output_directory()
    
    # Example questions
    questions = [
        {'image': 'dog.png', 'question': 'Is this a dog?', 'answer': True},
        {'image': 'cat.png', 'question': 'Is this a dog?', 'answer': False},
    ]
    
    # pages = generate_yes_no_questions_set(
    #     question_data=questions,
    #     folder_type='color',
    #     level=1,
    #     theme_name='Animals',
    #     output_dir=output_dir
    # )
    
    print("Example: Uncomment code and add actual image files")


def example_wh_questions():
    """Example: Generate WH questions."""
    print("Generating WH Questions...")
    
    output_dir = create_output_directory()
    
    # Example questions
    questions = [
        {
            'image': 'apple.png',
            'question': 'What is this?',
            'choices': ['Apple', 'Banana', 'Orange', 'Grape'],
            'answer': 0  # Index of correct answer
        },
    ]
    
    # pages = generate_wh_questions_set(
    #     question_data=questions,
    #     folder_type='color',
    #     level=1,
    #     theme_name='Fruits',
    #     output_dir=output_dir
    # )
    
    print("Example: Uncomment code and add actual image files")


def example_word_search():
    """Example: Generate word search."""
    print("Generating Word Search...")
    
    output_dir = create_output_directory()
    
    # Example word lists
    word_lists = [
        ['DOG', 'CAT', 'BIRD', 'FISH', 'HAMSTER'],
        ['APPLE', 'BANANA', 'ORANGE', 'GRAPE', 'PEAR'],
    ]
    
    # pages = generate_word_search_set(
    #     word_lists=word_lists,
    #     theme_name='Pets and Fruits',
    #     grid_size=10,
    #     output_dir=output_dir
    # )
    
    print("Example: Word search doesn't require images")


def example_storage_labels():
    """Example: Generate storage labels."""
    print("Generating Storage Labels...")
    
    output_dir = create_output_directory()
    
    # Example labels
    labels = [
        ('pencils.png', 'Pencils'),
        ('crayons.png', 'Crayons'),
        ('scissors.png', 'Scissors'),
    ]
    
    # pages = generate_storage_labels_sheet(
    #     label_data=labels,
    #     label_size='medium',
    #     folder_type='color',
    #     theme_name='Classroom',
    #     output_dir=output_dir
    # )
    
    print("Example: Uncomment code and add actual image files")


def main():
    """Run all examples."""
    print("=" * 60)
    print("SPED Resource Automation System - Examples")
    print("=" * 60)
    print()
    
    print("NOTE: These are code examples showing how to use each generator.")
    print("To actually generate PDFs, you need to:")
    print("1. Add image files to the appropriate folders (images/, Colour_images/, aac_images/)")
    print("2. Uncomment the function calls in each example")
    print("3. Update the image filenames to match your actual files")
    print()
    
    example_counting_mats()
    example_matching_cards()
    example_bingo()
    example_sequencing()
    example_coloring_strips()
    example_yes_no_questions()
    example_wh_questions()
    example_word_search()
    example_storage_labels()
    
    print()
    print("=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
