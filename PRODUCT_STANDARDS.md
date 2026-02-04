# PRODUCT STANDARDS - SMALL WINS STUDIO
## Standard Requirements for ALL Future Activities and Products

**Version:** 2.0  
**Last Updated:** February 3, 2026  
**Status:** ACTIVE - Use for all future products

---

## 1. LEVEL DESCRIPTION FORMAT ✅

### STANDARD: Simplified Level Naming

**Use:**
- ✅ "Level 1"
- ✅ "Level 2"
- ✅ "Level 3"
- ✅ "Level 4"

**Do NOT Use:**
- ❌ "Level 1 - Beginner"
- ❌ "Level 2 - Easy"
- ❌ "Level 3 - Intermediate"
- ❌ "Level 4 - Hard"
- ❌ "Advanced", "Medium", etc.

**Rationale:** Clean, simple, professional appearance. Less cluttered design.

**Implementation:**
- Covers: Show "LEVEL 1", "LEVEL 2", etc. in level badge
- Documentation: Reference as "Level 1", "Level 2", etc.
- File names: Use "level1", "level2", etc.
- Code: `get_level_description()` returns "Level X"

---

## 2. ERRORLESS LEARNING TERMINOLOGY ✅

### STANDARD: Limited Use

**Where to Use:**
- ✅ Level 1 Matching ONLY: "Errorless Learning Format"
- ✅ In specific context of Level 1 Matching activities

**Where NOT to Use:**
- ❌ General product descriptions
- ❌ Cover feature bullets (except Level 1 Matching)
- ❌ Other levels
- ❌ Other activity types

**Alternative Selling Points:**
Use instead:
- ✅ "Research-Based Visual Discrimination"
- ✅ "Progressive Difficulty Levels"
- ✅ "Differentiated Instruction Ready"
- ✅ "Data Collection Friendly"

**Rationale:** Errorless is specific to Level 1 Matching. Other products use different pedagogical approaches.

---

## 3. PRODUCT COVER GENERATION ✅

### STANDARD: Required for ALL Products

**Generate covers for:**
- ✅ Every product level (Matching: 1-4, Find & Cover: 1-3)
- ✅ Each activity type
- ✅ Each theme

**Cover Elements:**
1. Small Wins Studio branding
2. Product title
3. Level badge (simplified: "LEVEL X")
4. Preview image from actual PDF
5. Feature highlights (3-4 bullets)
6. Professional typography
7. Level-appropriate colors

**Color Coding:**
- Level 1: Orange (#F4A259)
- Level 2: Blue (#4A90E2)
- Level 3: Green (#7BC47F)
- Level 4: Purple (#B88DD9)

**Script:** `generate_product_covers.py`

**Output Location:** `Covers/`

---

## 4. PNG THUMBNAIL GENERATION ✅

### STANDARD: Required for ALL Products

**Generate thumbnails for:**
- ✅ Every product level PDF
- ✅ Both color and BW versions
- ✅ All pages of each PDF

**Thumbnail Specifications:**
- Format: PNG (optimized)
- Quality: 150 DPI
- Max Width: 800 pixels
- Aspect Ratio: Maintained (not stretched)
- Sequential Naming: page_01.png, page_02.png, etc.

**Organization:**
```
Thumbnails/
├── [product]_[activity]_level[N]_color/
│   ├── page_01.png
│   ├── page_02.png
│   └── ...
└── [product]_[activity]_level[N]_bw/
    └── ...
```

**Script:** `generate_page_thumbnails.py`

**Output Location:** `Thumbnails/`

**Use Cases:**
- TPT product previews (pages 1-4)
- Social media marketing
- Blog posts and tutorials
- Email newsletters
- Website product pages

---

## 5. COMPLETE PRODUCT GENERATION WORKFLOW ✅

### STANDARD: Follow this sequence

```bash
# Step 1: Generate base products
python3 generate_matching_constitution.py
python3 generate_find_cover_constitution.py
# (or other activity generators)

# Step 2: Generate product covers
python3 generate_product_covers.py

# Step 3: Generate PNG thumbnails
python3 generate_page_thumbnails.py

# Step 4: Package for TPT (optional)
python3 package_for_tpt.py
```

**Result:**
- Product PDFs (color, BW, preview versions)
- Level-specific PDFs
- Professional covers
- Complete thumbnail library
- Ready for TPT upload

---

## 6. FILE ORGANIZATION STANDARDS ✅

### STANDARD: Consistent structure

```
samples/[theme]/[activity]/
├── [theme]_[activity]_color.pdf           # Full product (all levels)
├── [theme]_[activity]_bw.pdf              # Full product BW
├── [theme]_[activity]_level1_color.pdf    # Individual levels
├── [theme]_[activity]_level1_bw.pdf
├── [theme]_[activity]_level1_preview.pdf  # Watermarked
└── ... (all levels)

Covers/
├── [theme]_[activity]_level1_cover.pdf
├── [theme]_[activity]_level2_cover.pdf
└── ...

Thumbnails/
├── [theme]_[activity]_level1_color/
│   └── page_*.png
├── [theme]_[activity]_level1_bw/
│   └── page_*.png
└── ...
```

---

## 7. QUALITY STANDARDS ✅

### STANDARD: Professional quality across all products

**PDFs:**
- High resolution (300 DPI minimum)
- Clean borders and spacing
- Consistent fonts and colors
- Professional typography
- Print-ready quality

**Covers:**
- Eye-catching design
- Clear product information
- Level-appropriate branding
- Preview from actual product
- TPT-optimized

**Thumbnails:**
- Web-optimized (150 DPI)
- Fast loading
- Clear visibility
- Professional appearance
- Marketing-ready

---

## 8. DOCUMENTATION STANDARDS ✅

### STANDARD: Complete documentation for each product

**Required Documentation:**
1. Product README (usage, levels, features)
2. Design specifications
3. Generation instructions
4. Changelog (when updated)

**Documentation Location:**
- Product-specific: `README_[PRODUCT].md`
- Design specs: `docs/`
- General guides: Root directory

---

## 9. VERSION CONTROL ✅

### STANDARD: Track all changes

**Commit Standards:**
- Clear commit messages
- Logical grouping of changes
- Document major updates in CHANGELOG
- Tag major versions

**Branching:**
- Use feature branches for major changes
- Test before merging to main
- Document breaking changes

---

## 10. TESTING & VERIFICATION ✅

### STANDARD: Verify before release

**Before Release:**
- ✅ Generate all product versions
- ✅ Generate all covers
- ✅ Generate all thumbnails
- ✅ Verify file sizes reasonable
- ✅ Check PDF quality
- ✅ Verify level naming correct
- ✅ Check color coding accurate
- ✅ Test on sample device/viewer

**Quality Checklist:**
- [ ] Product PDFs generated
- [ ] Covers created
- [ ] Thumbnails generated
- [ ] Documentation updated
- [ ] Level descriptions simplified
- [ ] Errorless used appropriately
- [ ] File organization correct
- [ ] Ready for TPT

---

## VERIFIED IMPLEMENTATION STATUS:

### Current Products (as of Feb 3, 2026):

**Brown Bear Matching:**
- ✅ 4 levels generated
- ✅ Covers created with simplified levels
- ✅ Thumbnails generated (15 pages × 4 levels × 2 versions = 120 thumbnails)
- ✅ Errorless ONLY on Level 1
- ✅ All standards applied

**Brown Bear Find & Cover:**
- ✅ 3 levels generated
- ✅ Covers created with simplified levels
- ✅ Thumbnails generated (13 pages × 3 levels × 2 versions = 78 thumbnails)
- ✅ Research-based selling point
- ✅ All standards applied

**Total Output:**
- 7 covers
- 198 PNG thumbnails
- 100% compliance with standards

---

## FUTURE ACTIVITIES:

When creating new activities (Word Search, Sentence Strips, Sorting, etc.):

1. ✅ Follow this PRODUCT_STANDARDS.md document
2. ✅ Use simplified level naming
3. ✅ Generate covers for all levels
4. ✅ Generate PNG thumbnails
5. ✅ Apply errorless terminology correctly
6. ✅ Maintain file organization structure
7. ✅ Create activity-specific documentation
8. ✅ Update this document if new standards emerge

---

## BENEFITS OF THESE STANDARDS:

**Consistency:**
- Same quality across all products
- Professional appearance
- Brand recognition

**Efficiency:**
- Automated generation
- No manual work
- Faster production

**Marketing:**
- Ready-to-use thumbnails
- Professional covers
- TPT-optimized

**Maintenance:**
- Easy to update
- Clear documentation
- Version controlled

---

## CONTACT & UPDATES:

**Questions:** Refer to this document first
**Updates:** Document all changes in CHANGELOG
**Issues:** Report inconsistencies to update standards

---

**🎉 USE THESE STANDARDS FOR ALL FUTURE PRODUCTS!**

This document ensures:
- Professional quality
- Consistent branding
- Efficient production
- Marketing readiness
- TPT success

**Last Verified:** February 3, 2026  
**Products Verified:** Brown Bear Matching, Brown Bear Find & Cover  
**Status:** ✅ ACTIVE - READY FOR USE
