# 📁 File Locations Guide
## Small Wins Studio - Complete Repository Map

**Last Updated:** February 4, 2026  
**Purpose:** Explain where TOU, documentation, and final product files are stored

---

## 🎯 Quick Answer to Your Question

**Q: "Where are the TOU and related docs and final zipped pdfs committed and stored?"**

**A: Short Answer:**
- ✅ **Product PDFs** ARE committed → `samples/brown_bear/`
- ✅ **Documentation** IS committed → Root directory and `/docs`
- ✅ **Thumbnails** ARE committed → `Thumbnails/`
- ❌ **Final ZIP packages** are NOT committed (not created yet)
- ❌ **TOU PDFs** are NOT committed (not created yet)

---

## ✅ WHAT EXISTS (Committed to Repository)

### 1. Product PDFs with Covers (14 files)

**Location:** `samples/brown_bear/matching/` and `samples/brown_bear/find_cover/`

**Matching Products (8 files):**
```
samples/brown_bear/matching/
├── brown_bear_matching_level1_color.pdf  ✅ (16 pages, cover included)
├── brown_bear_matching_level1_bw.pdf     ✅ (16 pages, cover included)
├── brown_bear_matching_level2_color.pdf  ✅ (16 pages, cover included)
├── brown_bear_matching_level2_bw.pdf     ✅ (16 pages, cover included)
├── brown_bear_matching_level3_color.pdf  ✅ (16 pages, cover included)
├── brown_bear_matching_level3_bw.pdf     ✅ (16 pages, cover included)
├── brown_bear_matching_level4_color.pdf  ✅ (16 pages, cover included)
└── brown_bear_matching_level4_bw.pdf     ✅ (16 pages, cover included)
```

**Find & Cover Products (6 files):**
```
samples/brown_bear/find_cover/
├── brown_bear_find_cover_level1_color.pdf  ✅ (14 pages, cover included)
├── brown_bear_find_cover_level1_bw.pdf     ✅ (14 pages, cover included)
├── brown_bear_find_cover_level2_color.pdf  ✅ (14 pages, cover included)
├── brown_bear_find_cover_level2_bw.pdf     ✅ (14 pages, cover included)
├── brown_bear_find_cover_level3_color.pdf  ✅ (14 pages, cover included)
└── brown_bear_find_cover_level3_bw.pdf     ✅ (14 pages, cover included)
```

**Status:** All PDFs include professional covers as page 1 (merged on Feb 3, 2026)

---

### 2. Individual Cover PDFs (7 files)

**Location:** `Covers/`

```
Covers/
├── brown_bear_matching_level1_cover.pdf   ✅
├── brown_bear_matching_level2_cover.pdf   ✅
├── brown_bear_matching_level3_cover.pdf   ✅
├── brown_bear_matching_level4_cover.pdf   ✅
├── brown_bear_find_cover_level1_cover.pdf ✅
├── brown_bear_find_cover_level2_cover.pdf ✅
└── brown_bear_find_cover_level3_cover.pdf ✅
```

**Purpose:** Individual cover files (also merged into product PDFs as page 1)

---

### 3. PNG Thumbnails (~198 files)

**Location:** `Thumbnails/`

```
Thumbnails/
├── brown_bear_matching_level1_color/    (15 PNG files) ✅
├── brown_bear_matching_level1_bw/       (15 PNG files) ✅
├── brown_bear_matching_level2_color/    (15 PNG files) ✅
├── brown_bear_matching_level2_bw/       (15 PNG files) ✅
├── brown_bear_matching_level3_color/    (15 PNG files) ✅
├── brown_bear_matching_level3_bw/       (15 PNG files) ✅
├── brown_bear_matching_level4_color/    (15 PNG files) ✅
├── brown_bear_matching_level4_bw/       (15 PNG files) ✅
├── brown_bear_find_cover_level1_color/  (13 PNG files) ✅
├── brown_bear_find_cover_level1_bw/     (13 PNG files) ✅
├── brown_bear_find_cover_level2_color/  (13 PNG files) ✅
├── brown_bear_find_cover_level2_bw/     (13 PNG files) ✅
├── brown_bear_find_cover_level3_color/  (13 PNG files) ✅
└── brown_bear_find_cover_level3_bw/     (13 PNG files) ✅
```

**Purpose:** Marketing images for TPT previews, social media, blog posts

---

### 4. Documentation Files (12+ files)

**Location:** Root directory and `/docs`

**Main Documentation:**
```
Root Directory:
├── PRODUCT_STANDARDS.md                 ✅ Product generation standards
├── FILE_LOCATIONS_GUIDE.md              ✅ This file!
├── TOU_AND_DOCS_LOCATION_GUIDE.md       ✅ Doc location reference
├── LOGO_INTEGRATION_GUIDE.md            ✅ Logo integration guide
├── CHANGELOG_2026-02-03.md              ✅ Recent changes
├── README_THUMBNAILS.md                 ✅ Thumbnail generation
├── README_TPT_PACKAGING.md              ✅ TPT packaging guide
├── README_LEVEL_PDFS.md                 ✅ Level PDF structure
├── README_FIND_COVER.md                 ✅ Find & Cover guide
├── README_MATCHING_SYSTEM.md            ✅ Matching guide
└── COVER_DESIGN_RECOMMENDATION.md       ✅ Cover design options
```

**Design Documentation:**
```
docs/
├── design_system.md                     ✅ Design system specs
└── find_cover_design_spec.md           ✅ Find & Cover specs
```

---

### 5. Generation Scripts (10+ files)

**Location:** Root directory

**Key Scripts:**
```
Root Directory:
├── generate_matching_constitution.py     ✅ Generate matching products
├── generate_find_cover_constitution.py   ✅ Generate find & cover products
├── generate_product_covers.py            ✅ Generate cover PDFs
├── generate_page_thumbnails.py           ✅ Generate PNG thumbnails
├── merge_covers_to_products.py           ✅ Merge covers into PDFs
├── package_for_tpt.py                    ✅ TPT packaging (basic)
└── ... (additional utility scripts)
```

---

## ❌ WHAT DOES NOT EXIST (Not in Repository)

### 1. Final TPT Product Packages

**Expected Location:** `TPT_Products/` ❌ **DOES NOT EXIST**

**Missing Files:**
```
TPT_Products/                                    ❌ Directory not created
├── Brown_Bear_Matching_Level1.zip              ❌ Not created
├── Brown_Bear_Matching_Level2.zip              ❌ Not created
├── Brown_Bear_Matching_Level3.zip              ❌ Not created
├── Brown_Bear_Matching_Level4.zip              ❌ Not created
├── Brown_Bear_Find_Cover_Level1.zip            ❌ Not created
├── Brown_Bear_Find_Cover_Level2.zip            ❌ Not created
└── Brown_Bear_Find_Cover_Level3.zip            ❌ Not created
```

**Each ZIP should contain:**
- Color PDF (with cover)
- Black & White PDF (with cover)
- Terms of Use PDF
- Quick Start Guide PDF

**Why Missing:** Discussed in conversation but not actually created/committed

---

### 2. Terms of Use Documents

**Expected Locations:** Various ❌ **DO NOT EXIST**

**Missing Files:**
```
templates/ or TPT_Products/
├── Terms_of_Use.pdf                            ❌ Not created

docs/
├── TOU_Universal.md                            ❌ Not created
├── TOU_FindAndCover.md                         ❌ Not created
└── TOU_Matching.md                             ❌ Not created
```

**Why Missing:** TOU system was planned but not implemented

---

### 3. Quick Start Guides

**Expected Location:** `TPT_Products/` ❌ **DO NOT EXIST**

**Missing Files:**
```
TPT_Products/
├── Quick_Start_Guide_Matching.pdf              ❌ Not created
└── Quick_Start_Guide_FindCover.pdf             ❌ Not created
```

**Should Include:**
- Materials needed
- Setup instructions
- How to use
- Differentiation tips

**Why Missing:** Not yet created

---

### 4. Complete TPT Packaging Script

**Expected Location:** Root directory ❌ **DOES NOT EXIST**

**Missing File:**
```
create_tpt_packages.py                          ❌ Not in repository
```

**Should Do:**
- Generate Terms of Use PDF
- Generate Quick Start Guides
- Package products into ZIP files
- Include all documentation

**Why Missing:** Script was designed in conversation but not implemented

---

## 🤔 Why the Confusion?

During our previous conversation, we:
1. ✅ **Discussed** creating complete TPT packages
2. ✅ **Designed** the packaging system in detail
3. ✅ **Planned** TOU and documentation structure
4. ❌ **Did NOT** actually create/commit those files

The conversation was very detailed and comprehensive, which may have made it seem like the files were created. However, the final implementation step (actually creating the scripts, running them, and committing the output) was not completed.

---

## 📊 Current Repository Status

### What You HAVE:
✅ **14 product PDFs** (color + BW, with covers merged)  
✅ **7 individual cover PDFs**  
✅ **~198 PNG thumbnails** for marketing  
✅ **12+ documentation files**  
✅ **10+ generation scripts**  

**Status:** Products are 95% ready for TPT upload

### What You DON'T HAVE:
❌ **7 ZIP packages** with complete documentation  
❌ **Terms of Use PDFs**  
❌ **Quick Start Guide PDFs**  
❌ **Packaging automation script**  

**Status:** Need to add legal/instruction documents

---

## 🚀 What You Can Do RIGHT NOW

### Option 1: Use Products As-Is (Quickest)

**Steps:**
1. Go to `samples/brown_bear/matching/` or `find_cover/`
2. Take the color and BW PDFs
3. Upload directly to Teachers Pay Teachers
4. Add your own Terms of Use in TPT's interface
5. Add product instructions in TPT description

**Pros:** 
- Fastest option
- Products are complete and professional
- Covers already included
- Ready to upload

**Cons:**
- No packaged ZIP files
- No separate TOU PDF
- Manual TOU entry on TPT

---

### Option 2: Create Complete TPT Packages (Most Professional)

**Steps:**

**1. Create Terms of Use PDF**
```python
# Use ReportLab to create a professional TOU PDF
# Include:
# - Copyright notice
# - License types (single/multi classroom)
# - Permitted uses
# - Prohibited uses
# - Contact information
```

**2. Create Quick Start Guides**
```python
# Create instruction PDFs for each product type
# Include:
# - Materials needed
# - Setup instructions
# - How to use
# - Differentiation strategies
```

**3. Create Packaging Script**
```python
# create_tpt_packages.py
# - Find all product PDFs
# - Include TOU and guides
# - Create ZIP files
# - Save to TPT_Products/
```

**4. Generate Packages**
```bash
python create_tpt_packages.py
# Creates 7 complete ZIP files
```

**5. Upload to TPT**
- Upload each ZIP file as a product
- TPT will automatically extract and preview contents
- Everything included in one package

**Pros:**
- Most professional
- Complete packages
- Legal documentation included
- User instructions included

**Cons:**
- More work upfront
- Need to create TOU and guides

---

## 📝 How to Create Missing Pieces

### Creating Terms of Use PDF

**Recommended Content:**
```
TERMS OF USE

© 2025 Small Wins Studio
All rights reserved.

LICENSE TYPES:
- Single Classroom License (included with purchase)
- Multiple Classroom License (requires additional purchase)

PERMITTED USES:
✓ Use in your classroom
✓ Print for your students
✓ Display digitally in your classroom
✓ Store in your personal cloud storage

PROHIBITED USES:
✗ Sharing on internet (personal websites, blogs, etc.)
✗ Redistribution to other teachers
✗ Modification for resale
✗ Commercial use outside of classroom
✗ File sharing services

MULTI-CLASSROOM LICENSING:
If you wish to share with other teachers in your school,
please purchase additional licenses or school-wide license.

PCS SYMBOLS:
This product uses PCS® symbols. Used with active 
PCS Maker Personal License. © 2025 Tobii Dynavox LLC.

CONTACT:
For questions: [your email]
TPT Store: [your TPT store URL]
```

**Create Using:**
- ReportLab (Python library)
- Microsoft Word → Export to PDF
- Google Docs → Download as PDF
- Canva → Download as PDF

---

### Creating Quick Start Guides

**For Matching:**
```
QUICK START GUIDE
Brown Bear Matching Activities

ABOUT THIS ACTIVITY:
File folder matching activities with velcro pieces.
Perfect for special education and early learners.

MATERIALS NEEDED:
- Laminator and laminating pouches
- Scissors
- Small velcro dots (soft and hook sides)
- File folders for storage

SETUP INSTRUCTIONS:
1. Laminate all activity pages
2. Laminate all cutout pages
3. Cut out matching pieces
4. Attach velcro dots to designated circles
5. Place soft side on folder, hook side on pieces

LEVELS:
Level 1 (Orange): 5 targets, 0 distractors - Beginner
Level 2 (Blue): 4 targets, 1 distractor - Easy
Level 3 (Green): 3 targets, 2 distractors - Medium
Level 4 (Purple): 1 target, 4 distractors - Hard

HOW TO USE:
1. Start with Level 1 for errorless learning
2. Present folder to student
3. Student matches pieces to images
4. Provide support as needed
5. Progress to higher levels

DIFFERENTIATION:
- Use hand-over-hand prompting for emerging learners
- Reduce choices for students needing more support
- Add time limits for advanced students
- Use for assessment data collection

DATA COLLECTION:
Track: Accuracy, Time to complete, Level of prompting

STORAGE:
Use included storage labels to organize activities.
```

**For Find & Cover:**
```
QUICK START GUIDE
Brown Bear Find & Cover Activities

ABOUT THIS ACTIVITY:
Visual scanning activities with dry erase markers or daubers.
Perfect for special education and early learners.

MATERIALS NEEDED:
- Laminator and laminating pouches
- Dry erase markers OR bingo daubers
- Optional: velcro coins for reusable covering

SETUP INSTRUCTIONS:
1. Laminate all activity pages
2. Ready to use with dry erase markers!

LEVELS:
Level 1 (Orange): 2-choice - Beginner
Level 2 (Blue): 3-choice - Intermediate
Level 3 (Green): 4-choice - Advanced

HOW TO USE:
1. Give student a marker or dauber
2. Call out or point to target image
3. Student finds and covers all matching images
4. Wipe clean and repeat

DIFFERENTIATION:
- Use larger grid spaces for motor challenges
- Reduce distractors for visual processing needs
- Add verbal prompts as needed
- Use for turn-taking in small groups

DATA COLLECTION:
Track: Accuracy, Time to complete, Independence level

STORAGE:
Store flat or in page protectors.
```

---

### Creating the Packaging Script

**Basic Structure:**
```python
#!/usr/bin/env python3
"""
TPT Product Packaging Script
Creates complete ZIP packages for Teachers Pay Teachers upload
"""

import os
import zipfile
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_terms_of_use():
    """Generate Terms of Use PDF"""
    # Create TOU PDF using ReportLab
    pass

def create_quick_start_guide(product_type):
    """Generate Quick Start Guide PDF"""
    # Create guide PDF using ReportLab
    pass

def package_product(product_name, color_pdf, bw_pdf, tou_pdf, guide_pdf):
    """Create ZIP package with all files"""
    zip_path = f"TPT_Products/{product_name}.zip"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(color_pdf)
        zipf.write(bw_pdf)
        zipf.write(tou_pdf)
        zipf.write(guide_pdf)

def main():
    # Create output directory
    os.makedirs("TPT_Products", exist_ok=True)
    
    # Generate documentation
    tou_pdf = create_terms_of_use()
    matching_guide = create_quick_start_guide("matching")
    findcover_guide = create_quick_start_guide("find_cover")
    
    # Package all products
    # ... package each level ...
    
if __name__ == "__main__":
    main()
```

---

## 🎯 Recommended Next Steps

### Immediate (Use What You Have):
1. Navigate to `samples/brown_bear/matching/` and `find_cover/`
2. Review the product PDFs (already include covers)
3. Upload to TPT with manual TOU
4. Use PNG thumbnails from `Thumbnails/` for previews

### Short Term (Add Documentation):
1. Create simple Terms of Use PDF
2. Create basic Quick Start Guides
3. Upload as separate files or add to ZIP manually

### Long Term (Full Automation):
1. Create complete packaging script
2. Generate all documentation automatically
3. Create ZIP packages
4. Maintain consistent workflow for future products

---

## 📚 Additional Resources

**Documentation in Repository:**
- `PRODUCT_STANDARDS.md` - Product generation workflow
- `README_TPT_PACKAGING.md` - TPT packaging guide (conceptual)
- `TOU_AND_DOCS_LOCATION_GUIDE.md` - Documentation index

**External Resources:**
- Teachers Pay Teachers Seller Handbook
- ReportLab Documentation (for PDF creation)
- Python zipfile module documentation

---

## ✅ Summary

**WHAT'S COMMITTED:**
- ✅ 14 complete product PDFs (in samples/brown_bear/)
- ✅ 7 individual covers (in Covers/)
- ✅ ~198 marketing thumbnails (in Thumbnails/)
- ✅ Complete documentation (in root and /docs)
- ✅ All generation scripts (in root)

**WHAT'S NOT COMMITTED:**
- ❌ Final ZIP packages
- ❌ Terms of Use PDFs
- ❌ Quick Start Guides
- ❌ Packaging automation script

**NEXT STEP:**
Choose Option 1 (use as-is) or Option 2 (create packages) based on your needs!

---

**Questions?** Review the documentation files or create the missing pieces using the templates above!
