#!/usr/bin/env python3
"""
TPT Product Packaging System
Small Wins Studio

Creates complete TPT product packages with:
- Color PDF (with cover)
- Black & White PDF (with cover)
- Terms of Use PDF
- Quick Start Guide PDF

Each product is packaged as a ZIP file ready for Teachers Pay Teachers upload.
"""

import os
import zipfile
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Directories
BASE_DIR = Path(__file__).parent
MATCHING_DIR = BASE_DIR / "samples" / "brown_bear" / "matching"
FIND_COVER_DIR = BASE_DIR / "samples" / "brown_bear" / "find_cover"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "TPT_Products"

# Product configurations
MATCHING_LEVELS = [1, 2, 3, 4]
FIND_COVER_LEVELS = [1, 2, 3]

def create_terms_of_use():
    """Create Terms of Use PDF"""
    print("\nCreating Terms of Use...")
    
    TEMPLATES_DIR.mkdir(exist_ok=True)
    filename = TEMPLATES_DIR / "Terms_of_Use.pdf"
    
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=letter,
        leftMargin=1*inch,
        rightMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )
    
    story = []
    
    # Title
    story.append(Paragraph("TERMS OF USE", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Copyright
    story.append(Paragraph("© 2025 Small Wins Studio. All rights reserved.", body_style))
    story.append(Spacer(1, 0.3*inch))
    
    # License Information
    story.append(Paragraph("LICENSE INFORMATION", heading_style))
    story.append(Paragraph(
        "This product includes a <b>single classroom license</b>. This means you may use this "
        "product for your own classroom or therapy room. You may make copies for your own students.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))
    
    # Multiple Classroom License
    story.append(Paragraph("MULTIPLE CLASSROOM LICENSE", heading_style))
    story.append(Paragraph(
        "If you wish to share this product with colleagues or use it in multiple classrooms, "
        "you must purchase additional licenses through Teachers Pay Teachers. School-wide licenses "
        "are also available - please contact Small Wins Studio for pricing.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))
    
    # Permitted Uses
    story.append(Paragraph("PERMITTED USES", heading_style))
    story.append(Paragraph("You MAY:", body_style))
    story.append(Paragraph("• Use this product in your own classroom or therapy room", body_style))
    story.append(Paragraph("• Print copies for your own students", body_style))
    story.append(Paragraph("• Display the materials digitally in your classroom", body_style))
    story.append(Paragraph("• Store files on your personal computer or cloud storage for your own use", body_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Prohibited Uses
    story.append(Paragraph("PROHIBITED USES", heading_style))
    story.append(Paragraph("You may NOT:", body_style))
    story.append(Paragraph("• Share this product with other teachers without purchasing additional licenses", body_style))
    story.append(Paragraph("• Post this product online in any form (websites, blogs, social media, etc.)", body_style))
    story.append(Paragraph("• Sell or redistribute this product in any way", body_style))
    story.append(Paragraph("• Claim this product as your own", body_style))
    story.append(Paragraph("• Modify and sell or distribute modified versions", body_style))
    story.append(Paragraph("• Share files through file sharing services", body_style))
    story.append(Spacer(1, 0.1*inch))
    
    # PCS Symbols
    story.append(Paragraph("PCS SYMBOLS", heading_style))
    story.append(Paragraph(
        "This product contains PCS symbols used with permission from Tobii Dynavox. "
        "PCS symbols © 2025 Tobii Dynavox. All rights reserved. Used with an active "
        "PCS Maker Personal License.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))
    
    # Special Education
    story.append(Paragraph("SPECIAL EDUCATION FOCUS", heading_style))
    story.append(Paragraph(
        "These materials are specifically designed for special education settings and students "
        "with diverse learning needs. The activities support skill development through evidence-based "
        "visual discrimination and errorless learning approaches.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))
    
    # Feedback
    story.append(Paragraph("FEEDBACK & REVIEWS", heading_style))
    story.append(Paragraph(
        "If you enjoy this product, please consider leaving a review on Teachers Pay Teachers! "
        "Your feedback helps other educators find quality resources and supports Small Wins Studio "
        "in creating more helpful materials.",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))
    
    # Contact
    story.append(Paragraph("QUESTIONS OR CONCERNS?", heading_style))
    story.append(Paragraph(
        "If you have any questions about this product or need support, please contact Small Wins Studio "
        "through Teachers Pay Teachers. We're here to help!",
        body_style
    ))
    
    # Build PDF
    doc.build(story)
    print(f"  ✓ Terms of Use created: {filename}")
    return filename

def create_quick_start_guide_matching():
    """Create Quick Start Guide for Matching activities"""
    print("\nCreating Quick Start Guide (Matching)...")
    
    TEMPLATES_DIR.mkdir(exist_ok=True)
    filename = TEMPLATES_DIR / "Quick_Start_Guide_Matching.pdf"
    
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=letter,
        leftMargin=1*inch,
        rightMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_LEFT,
        spaceAfter=10
    )
    
    story = []
    
    # Title
    story.append(Paragraph("QUICK START GUIDE", title_style))
    story.append(Paragraph("Brown Bear Matching Activities", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    # About
    story.append(Paragraph("ABOUT THIS ACTIVITY", heading_style))
    story.append(Paragraph(
        "These matching file folder activities are designed for special education students to develop "
        "visual discrimination skills through hands-on practice. Each level provides scaffolded support "
        "with varying difficulty levels.",
        body_style
    ))
    
    # Materials
    story.append(Paragraph("MATERIALS NEEDED", heading_style))
    story.append(Paragraph("• Laminator and laminating pouches", body_style))
    story.append(Paragraph("• File folders (one per level)", body_style))
    story.append(Paragraph("• Velcro dots (hook and loop)", body_style))
    story.append(Paragraph("• Scissors", body_style))
    story.append(Paragraph("• Optional: Label maker for storage organization", body_style))
    
    # Setup
    story.append(Paragraph("SETUP INSTRUCTIONS", heading_style))
    story.append(Paragraph("1. Print the activity pages (color or black & white)", body_style))
    story.append(Paragraph("2. Laminate all pages for durability", body_style))
    story.append(Paragraph("3. Cut out the matching pieces from the cutout pages", body_style))
    story.append(Paragraph("4. Attach soft velcro dots to the file folder at designated spots", body_style))
    story.append(Paragraph("5. Attach hook velcro dots to the back of each cutout piece", body_style))
    story.append(Paragraph("6. Store pieces in a labeled envelope or bag attached to the folder", body_style))
    
    # Levels
    story.append(Paragraph("DIFFICULTY LEVELS", heading_style))
    story.append(Paragraph(
        "<b>Level 1 (Orange):</b> 5 targets, 0 distractors - Errorless learning format for beginners",
        body_style
    ))
    story.append(Paragraph(
        "<b>Level 2 (Blue):</b> 4 targets, 1 distractor - Easy difficulty with minimal challenge",
        body_style
    ))
    story.append(Paragraph(
        "<b>Level 3 (Green):</b> 3 targets, 2 distractors - Medium difficulty",
        body_style
    ))
    story.append(Paragraph(
        "<b>Level 4 (Purple):</b> 1 target, 4 distractors - Hard difficulty requiring discrimination",
        body_style
    ))
    
    # Usage
    story.append(Paragraph("HOW TO USE", heading_style))
    story.append(Paragraph(
        "Present the file folder to the student with the matching pieces available. Have the student "
        "match each piece to its corresponding spot on the folder. Provide immediate feedback and support "
        "as needed. Start with Level 1 for errorless learning, then progress through levels as student "
        "demonstrates mastery.",
        body_style
    ))
    
    # Differentiation
    story.append(Paragraph("DIFFERENTIATION TIPS", heading_style))
    story.append(Paragraph("• Start with hand-over-hand guidance for students new to the task", body_style))
    story.append(Paragraph("• Reduce the number of choices for students who need more support", body_style))
    story.append(Paragraph("• Add a timer for students ready for a challenge", body_style))
    story.append(Paragraph("• Use as an independent work station or small group activity", body_style))
    
    # Data Collection
    story.append(Paragraph("DATA COLLECTION", heading_style))
    story.append(Paragraph(
        "Track student progress by recording: number of correct matches, level of prompting needed, "
        "time to complete, and independence level. Use this data to determine when to move to the next level.",
        body_style
    ))
    
    # Storage
    story.append(Paragraph("STORAGE RECOMMENDATIONS", heading_style))
    story.append(Paragraph(
        "Keep file folders in a labeled bin or filing system. Attach storage labels (included) to help "
        "with organization and inventory management.",
        body_style
    ))
    
    # Build PDF
    doc.build(story)
    print(f"  ✓ Quick Start Guide (Matching) created: {filename}")
    return filename

def create_quick_start_guide_find_cover():
    """Create Quick Start Guide for Find & Cover activities"""
    print("\nCreating Quick Start Guide (Find & Cover)...")
    
    TEMPLATES_DIR.mkdir(exist_ok=True)
    filename = TEMPLATES_DIR / "Quick_Start_Guide_FindCover.pdf"
    
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=letter,
        leftMargin=1*inch,
        rightMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_LEFT,
        spaceAfter=10
    )
    
    story = []
    
    # Title
    story.append(Paragraph("QUICK START GUIDE", title_style))
    story.append(Paragraph("Brown Bear Find & Cover Activities", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    # About
    story.append(Paragraph("ABOUT THIS ACTIVITY", heading_style))
    story.append(Paragraph(
        "Find & Cover activities are designed to build visual scanning and discrimination skills "
        "through engaging, hands-on practice. Students locate target images in a 4×4 grid and mark "
        "them using various methods.",
        body_style
    ))
    
    # Materials
    story.append(Paragraph("MATERIALS NEEDED", heading_style))
    story.append(Paragraph("• Laminator and laminating pouches", body_style))
    story.append(Paragraph("• Dry erase markers OR bingo daubers", body_style))
    story.append(Paragraph("• Optional: Velcro coins for reusable covering", body_style))
    story.append(Paragraph("• Optional: Small manipulatives as markers", body_style))
    
    # Setup
    story.append(Paragraph("SETUP INSTRUCTIONS", heading_style))
    story.append(Paragraph("1. Print the activity pages (color or black & white)", body_style))
    story.append(Paragraph("2. Laminate all pages for durability and reusability", body_style))
    story.append(Paragraph("3. If using dry erase markers, have erasers or tissues ready", body_style))
    story.append(Paragraph("4. If using bingo daubers, ensure they're washable for laminated surfaces", body_style))
    story.append(Paragraph("5. Store in a labeled binder or folder for easy access", body_style))
    
    # Levels
    story.append(Paragraph("DIFFICULTY LEVELS", heading_style))
    story.append(Paragraph(
        "<b>Level 1 (Orange):</b> 2-choice discrimination - Beginner level with errorless design",
        body_style
    ))
    story.append(Paragraph(
        "<b>Level 2 (Blue):</b> 3-choice discrimination - Intermediate difficulty",
        body_style
    ))
    story.append(Paragraph(
        "<b>Level 3 (Green):</b> 4-choice discrimination - Advanced level requiring careful scanning",
        body_style
    ))
    
    # Usage
    story.append(Paragraph("HOW TO USE", heading_style))
    story.append(Paragraph(
        "Show the student the target image at the top of the page. Have them scan the 4×4 grid to find "
        "all matching images. Student marks each match with a dry erase marker, bingo dauber, or by "
        "covering with velcro coins. Provide support as needed based on student skill level.",
        body_style
    ))
    
    # Differentiation
    story.append(Paragraph("DIFFERENTIATION TIPS", heading_style))
    story.append(Paragraph("• Use hand-over-hand prompting for students learning the task", body_style))
    story.append(Paragraph("• Point to each box to support systematic scanning", body_style))
    story.append(Paragraph("• Start with Level 1 for errorless learning approach", body_style))
    story.append(Paragraph("• Add a timer for students ready for additional challenge", body_style))
    story.append(Paragraph("• Use in small groups or as independent work", body_style))
    
    # Data Collection
    story.append(Paragraph("DATA COLLECTION", heading_style))
    story.append(Paragraph(
        "Record: accuracy (number correct/total), time to complete, level of prompting needed, and "
        "scanning strategy used. This data helps determine readiness for the next level.",
        body_style
    ))
    
    # Storage
    story.append(Paragraph("STORAGE RECOMMENDATIONS", heading_style))
    story.append(Paragraph(
        "Store laminated pages in a 3-ring binder or folder with dividers for each level. Use the "
        "included storage labels for organization. Keep markers/daubers in a attached pencil pouch.",
        body_style
    ))
    
    # Build PDF
    doc.build(story)
    print(f"  ✓ Quick Start Guide (Find & Cover) created: {filename}")
    return filename

def create_product_package(product_name, product_type, level, color_pdf, bw_pdf, tou_pdf, guide_pdf):
    """Create a ZIP package for a single product"""
    
    # Create friendly names
    friendly_name = f"Brown_Bear_{product_type.replace('_', '')}_Level{level}"
    zip_filename = OUTPUT_DIR / f"{friendly_name}.zip"
    
    print(f"\nPackaging: {friendly_name}")
    
    # Create ZIP file
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add color PDF
        if color_pdf.exists():
            zipf.write(color_pdf, f"{friendly_name}_Color.pdf")
            print(f"  ✓ Added: {friendly_name}_Color.pdf")
        
        # Add BW PDF
        if bw_pdf.exists():
            zipf.write(bw_pdf, f"{friendly_name}_BW.pdf")
            print(f"  ✓ Added: {friendly_name}_BW.pdf")
        
        # Add TOU
        if tou_pdf.exists():
            zipf.write(tou_pdf, "Terms_of_Use.pdf")
            print(f"  ✓ Added: Terms_of_Use.pdf")
        
        # Add Quick Start Guide
        if guide_pdf.exists():
            zipf.write(guide_pdf, "Quick_Start_Guide.pdf")
            print(f"  ✓ Added: Quick_Start_Guide.pdf")
    
    # Get file size
    size_mb = zip_filename.stat().st_size / (1024 * 1024)
    print(f"✓ Created: {zip_filename.name} ({size_mb:.1f} MB)")
    
    return zip_filename

def main():
    """Main packaging function"""
    print("=" * 60)
    print("TPT PRODUCT PACKAGING")
    print("Small Wins Studio")
    print("=" * 60)
    
    # Create output directory
    print("\nCreating output directory...")
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"✓ Output directory: {OUTPUT_DIR}")
    
    # Generate documentation
    print("\n" + "=" * 60)
    print("GENERATING DOCUMENTATION")
    print("=" * 60)
    
    tou_pdf = create_terms_of_use()
    matching_guide_pdf = create_quick_start_guide_matching()
    find_cover_guide_pdf = create_quick_start_guide_find_cover()
    
    # Package products
    print("\n" + "=" * 60)
    print("PACKAGING PRODUCTS")
    print("=" * 60)
    
    packages_created = []
    
    # Package Matching products
    for level in MATCHING_LEVELS:
        color_pdf = MATCHING_DIR / f"brown_bear_matching_level{level}_color.pdf"
        bw_pdf = MATCHING_DIR / f"brown_bear_matching_level{level}_bw.pdf"
        
        if color_pdf.exists() and bw_pdf.exists():
            zip_file = create_product_package(
                f"brown_bear_matching_level{level}",
                "Matching",
                level,
                color_pdf,
                bw_pdf,
                tou_pdf,
                matching_guide_pdf
            )
            packages_created.append(zip_file)
        else:
            print(f"\n⚠ Warning: Missing PDFs for Matching Level {level}")
    
    # Package Find & Cover products
    for level in FIND_COVER_LEVELS:
        color_pdf = FIND_COVER_DIR / f"brown_bear_find_cover_level{level}_color.pdf"
        bw_pdf = FIND_COVER_DIR / f"brown_bear_find_cover_level{level}_bw.pdf"
        
        if color_pdf.exists() and bw_pdf.exists():
            zip_file = create_product_package(
                f"brown_bear_find_cover_level{level}",
                "Find_Cover",
                level,
                color_pdf,
                bw_pdf,
                tou_pdf,
                find_cover_guide_pdf
            )
            packages_created.append(zip_file)
        else:
            print(f"\n⚠ Warning: Missing PDFs for Find & Cover Level {level}")
    
    # Summary
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    
    print(f"\n✓ Created {len(packages_created)} complete TPT packages")
    print(f"✓ All packages saved to: {OUTPUT_DIR}")
    print("\n✓ Ready to upload to Teachers Pay Teachers!")
    
    print("\n📦 Packages Created:")
    for package in packages_created:
        size_mb = package.stat().st_size / (1024 * 1024)
        print(f"  • {package.name} ({size_mb:.1f} MB)")
    
    print("\n🎉 All products ready for TPT upload!")

if __name__ == "__main__":
    main()
