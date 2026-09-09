#!/usr/bin/env python3
"""
TPT Pack Builder - Single Pack Version
Simple script to create one pack at a time
"""

import os
import shutil
from pathlib import Path
from PyPDF2 import PdfMerger
from PIL import Image
import pdf2image
import img2pdf

# Get Desktop path (works on all Windows systems)
DESKTOP = Path.home() / "Desktop"

def convert_to_bw(pdf_path, output_path):
    """Convert PDF to black and white"""
    print(f"Converting to B&W: {pdf_path.name}")
    
    # Convert to images
    images = pdf2image.convert_from_path(str(pdf_path), dpi=300)
    
    # Convert each to grayscale
    bw_images = []
    temp_dir = Path("temp_bw")
    temp_dir.mkdir(exist_ok=True)
    
    for i, img in enumerate(images):
        print(f"  Processing page {i+1}/{len(images)}")
        bw_img = img.convert('L')  # Grayscale
        temp_file = temp_dir / f"page_{i:03d}.png"
        bw_img.save(temp_file, dpi=(300, 300))
        bw_images.append(str(temp_file))
    
    # Convert back to PDF
    with open(output_path, "wb") as f:
        f.write(img2pdf.convert(bw_images))
    
    # Cleanup
    shutil.rmtree(temp_dir)
    print(f"✓ B&W version saved!")

def create_instructions_pdf(master_folder, output_folder):
    """Create the master instructions PDF"""
    print("\n📄 Creating Instructions Guide...")
    
    master_path = Path(master_folder)
    output_path = Path(output_folder)
    
    # Create output folder if it doesn't exist
    try:
        output_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Output folder ready: {output_path}")
    except Exception as e:
        print(f"⚠️  Could not create output folder: {e}")
        print(f"   Trying current directory instead...")
        output_path = Path("TPT_Output")
        output_path.mkdir(parents=True, exist_ok=True)
    
    merger = PdfMerger()
    
    # Files in order - these match your ACTUAL files with spaces
    instruction_files = [
        'Terms_of_Use.pdf',  # This one has underscore
        'Data_Collection.pdf',  # This one has underscore
        'Data_tracking.pdf',  # This one has underscore
        'How_to_Use.pdf',  # This one has underscore
        'Levels_Differentiation.pdf',  # This one has underscore
        'More Packs.pdf',  # This one has SPACE
        'Progress_Exensions.pdf',  # This one has underscore
        'Storage_Organization.pdf',  # This one has underscore
        'Student_Directions.pdf'  # This one has underscore
    ]
    
    for filename in instruction_files:
        file_path = master_path / filename
        if file_path.exists():
            print(f"  ✓ Adding: {filename}")
            merger.append(str(file_path))
        else:
            print(f"  ⚠️  Not found: {filename}")
    
    output_file = output_path / "Instructions_Guide.pdf"
    merger.write(str(output_file))
    merger.close()
    
    print(f"✓ Instructions Guide created!")
    return output_file

def create_pack(pack_code, pack_folder, output_folder):
    """Create a pack with color and B&W versions"""
    print(f"\n{'='*60}")
    print(f"🎨 Creating Pack: {pack_code}")
    print(f"{'='*60}")
    
    pack_path = Path(pack_folder)
    output_path = Path(output_folder)
    
    # Create output folder if it doesn't exist
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"⚠️  Output folder issue: {e}")
        output_path = Path("TPT_Output")
        output_path.mkdir(parents=True, exist_ok=True)
    
    # Look for the pack PDF file in current directory
    # Look for a file named with the pack code
    pack_pdf = pack_path / f"{pack_code}.pdf"
    
    print(f"\n🔍 Looking for: {pack_pdf}")
    
    if not pack_pdf.exists():
        # Try finding any PDF with the pack code in the name
        pdf_files = list(pack_path.glob(f"*{pack_code}*.pdf"))
        print(f"   Found {len(pdf_files)} PDF file(s) matching *{pack_code}*.pdf")
        
        if not pdf_files:
            # List what files ARE in the current directory
            print(f"\n   PDF files in current directory:")
            all_pdfs = list(pack_path.glob("*.pdf"))
            for f in all_pdfs:
                print(f"     - {f.name}")
            raise Exception(f"No PDF file found matching {pack_code}")
        
        pack_pdf = pdf_files[0]
    
    print(f"✓ Found pack PDF: {pack_pdf.name}")
    
    # Copy to output with standard name
    color_output = output_path / f"{pack_code}_Activities.pdf"
    shutil.copy(pack_pdf, color_output)
    print(f"✓ COLOR PDF created: {pack_code}_Activities.pdf")
    
    # Create B&W version
    print(f"\n📗 Creating B&W version...")
    bw_output = output_path / f"{pack_code}_Activities_BW.pdf"
    convert_to_bw(color_output, bw_output)
    print(f"✓ B&W PDF created: {pack_code}_Activities_BW.pdf")
    
    return color_output, bw_output

def create_zip(pack_code, color_pdf, bw_pdf, instructions_pdf, output_folder):
    """Create ZIP bundle"""
    print(f"\n📦 Creating ZIP bundle...")
    
    output_path = Path(output_folder)
    zip_name = f"{pack_code}_Complete_Pack"
    zip_folder = output_path / zip_name
    zip_folder.mkdir(exist_ok=True)
    
    # Copy files with clear names
    shutil.copy(color_pdf, zip_folder / f"{pack_code}_Activities_COLOR.pdf")
    shutil.copy(bw_pdf, zip_folder / f"{pack_code}_Activities_BW.pdf")
    shutil.copy(instructions_pdf, zip_folder / "Instructions_Guide.pdf")
    
    # Create README
    readme_path = zip_folder / "README.txt"
    with open(readme_path, 'w') as f:
        f.write(f"""{pack_code} - Errorless Winter Matching

WHAT'S INCLUDED:
1. {pack_code}_Activities_COLOR.pdf - Print for color folders (8 pages)
2. {pack_code}_Activities_BW.pdf - Print for black & white (8 pages)
3. Instructions_Guide.pdf - How to use, data sheets, tips

QUICK START:
1. Print activities (color OR B&W - your choice)
2. Read Instructions_Guide.pdf
3. Laminate, cut, add Velcro, done!

© 2025 Small Wins Studio
""")
    
    # Create ZIP
    shutil.make_archive(str(zip_folder), 'zip', zip_folder)
    shutil.rmtree(zip_folder)
    
    print(f"✓ ZIP created: {zip_name}.zip")
    print(f"\n{'='*60}")
    print(f"✨ ALL DONE! Files ready in 'output' folder!")
    print(f"{'='*60}")

# ==== MAIN SCRIPT - EDIT THIS SECTION ====

# Set your pack code here
PACK_CODE = "WA1A"  # Removed hyphen to avoid file matching issues

# Set your folder paths
MASTER_FOLDER = "master pages"  # Same level as script
PACK_FOLDER = "."  # Current folder (look for WA1-A.pdf here)
OUTPUT_FOLDER = DESKTOP / "TPT_Output"  # Save to Desktop instead!

# Run the script
if __name__ == "__main__":
    print("\n" + "="*60)
    print("TPT PACK BUILDER")
    print("="*60)
    
    try:
        # Step 1: Create instructions
        instructions_pdf = create_instructions_pdf(MASTER_FOLDER, OUTPUT_FOLDER)
        
        # Step 2: Create pack
        color_pdf, bw_pdf = create_pack(PACK_CODE, PACK_FOLDER, OUTPUT_FOLDER)
        
        # Step 3: Create ZIP
        create_zip(PACK_CODE, color_pdf, bw_pdf, instructions_pdf, OUTPUT_FOLDER)
        
        print("\n🎉 SUCCESS! Check the 'output' folder for your files!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nPlease check:")
        print("1. Folder paths are correct")
        print("2. All PDF files are in the right folders")
        print("3. PDF files are named correctly")
    
    # Keep window open so you can see the results
    input("\nPress ENTER to close...")
