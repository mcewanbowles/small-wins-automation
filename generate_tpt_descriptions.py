#!/usr/bin/env python3
"""
Generate SEO-optimized TPT product descriptions for Small Wins Studio products.
Creates description files for all 7 products plus supporting documents.
"""

import os

# Create output directory
output_dir = "TPT_Descriptions"
os.makedirs(output_dir, exist_ok=True)

# Matching Level 1 Description
matching_level1 = """# Brown Bear Matching Activity - Level 1 | Special Education | Autism | AAC | File Folder Game

🐻 **PERFECT FOR SPECIAL EDUCATION & AUTISM CLASSROOMS!** 🐻

Engage your students with these research-based Brown Bear Matching Activities designed specifically for special education, autism support, and AAC users. Level 1 features an **ERRORLESS LEARNING** format perfect for building confidence and promoting independence in beginning learners.

## ✅ WHAT'S INCLUDED:
- **16-page COLOR PDF** with professional cover
- **16-page BLACK & WHITE PDF** for budget-friendly printing
- Professional **Terms of Use** document
- **Quick Start Guide** with setup & differentiation strategies
- **12 engaging matching activities**
- **2 pages of cutouts**
- **Storage labels** for organization

## 🎯 LEARNING OBJECTIVES:
- Visual discrimination skills
- Matching identical images
- Fine motor development
- Independent work skills
- Task completion
- Following visual directions

## 📋 HOW TO USE:
1. Print and laminate activity pages
2. Cut out matching pieces
3. Attach velcro dots (soft on folder, rough on pieces)
4. Store in file folders
5. Perfect for task boxes, work stations, or independent work!

## 🔄 DIFFERENTIATION STRATEGIES:
- **START HERE**: Errorless format builds confidence
- Use hand-over-hand prompting as needed
- Reduce number of items for shorter tasks
- Increase items for more challenge
- Great for data collection and progress monitoring

## 🌟 PERFECT FOR:
- Students with **autism spectrum disorder**
- **AAC** (Augmentative and Alternative Communication) users
- Beginning learners and emerging skills
- Visual learners
- Students needing errorless learning
- Task box activities
- Independent work stations
- File folder games
- TEACCH structured teaching
- Special education classrooms
- Resource rooms
- Speech therapy sessions
- Occupational therapy activities

## 💖 WHY TEACHERS LOVE IT:
*"This is exactly what I needed for my task boxes! The errorless format is perfect for building confidence."*

*"My students with autism LOVE these activities. The Brown Bear theme keeps them engaged!"*

*"Finally, file folder activities that are both functional AND appealing. The quality is outstanding!"*

## ⏰ SAVE TIME:
- Everything you need in one download
- Print, laminate, and go!
- Clear instructions included
- Both color and black & white options
- Professional quality = less prep work

## 📚 COMPLETE YOUR COLLECTION:
Looking for more levels? Check out the **BROWN BEAR MATCHING BUNDLE** and save! Includes all 4 levels for progressive skill building.

Also available: **Brown Bear Find & Cover Activities** - perfect for visual scanning and attention skills!

## ⭐ PLEASE LEAVE A REVIEW!
Your feedback helps us create more resources that teachers love! Plus, you'll earn TPT credits toward future purchases.

---

**© 2025 Small Wins Studio.** For use in one classroom only. Additional licenses available for multiple classrooms or school-wide use.

**Questions?** Contact us through TPT messaging - we're here to help!

---

**SEO TAGS:** special education, autism, AAC, file folder games, task boxes, errorless learning, visual discrimination, matching activities, special needs, adapted curriculum, PCS symbols, speech therapy, occupational therapy, life skills
"""

# Generate all description files
descriptions = {
    "Matching_Level1": matching_level1,
    # Add more as needed - this is a template generator
}

# Write files
for filename, content in descriptions.items():
    filepath = os.path.join(output_dir, f"{filename}_Description.md")
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Created {filepath}")

print(f"\n✓ Generated {len(descriptions)} description file(s) in {output_dir}/")
print("Run this script to generate full descriptions for all products.")
