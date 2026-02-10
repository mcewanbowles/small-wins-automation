# PRODUCT REQUIREMENTS REFERENCE

## Complete Product Specification

**For every product (e.g., Matching), you need exactly 9 items:**

---

## 📋 The 9 Required Items

### 1. Final PDF Colour (with cover)
- **What:** 16-page PDF including cover, activities, and How to Use guide
- **Generator:** `production/generators/generate_complete_products_final.py`
- **Status:** ✅ WORKING
- **Output:** `final_products/brown_bear/matching/brown_bear_matching_levelX_color_FINAL.pdf`

### 2. Final PDF B&W (with cover)
- **What:** 16-page B&W PDF including cover, activities, and How to Use guide
- **Generator:** `production/generators/generate_complete_products_final.py`
- **Status:** ✅ WORKING
- **Output:** `final_products/brown_bear/matching/brown_bear_matching_levelX_bw_FINAL.pdf`

### 3. Terms of Use
- **What:** Official legal document for product use
- **Source:** `Draft General Docs/TOU_etc/Terms_of_Use_Credits.pdf`
- **Status:** ✅ READY (when file is added to repository)
- **Usage:** Automatically included in TpT ZIPs

### 4. Quick Start (product-specific)
- **What:** 1-page guide with setup instructions, customized per level
- **Generator:** Auto-generated in `production/generators/create_tpt_packages_updated.py`
- **Status:** ✅ WORKING
- **Features:** Auto-updates level number and name

### 5. Freebie
- **What:** Free sample product for customer acquisition (cover + samples + cutouts)
- **Generator:** `generate_freebie_new.py` (root directory, 14 KB)
- **Status:** ✅ AVAILABLE (fully functional, ready to use)
- **Output:** Freebie PDF with cover, page 1 from each level, all cutout pages
- **Action:** Move to production/generators/ for organization

### 6. Description
- **What:** TpT listing description text
- **Generator:** ❌ NOT CREATED YET
- **Status:** ❌ MISSING
- **Workaround:** Create manually
- **Action needed:** Build description generator

### 7. Preview
- **What:** Watermarked PDF for TpT product preview
- **Generator 1:** `production/generators/generate_matching_constitution.py` (creates watermarked previews)
- **Generator 2:** `generate_level_covers_with_preview.py` (root directory, 11 KB, creates covers with preview)
- **Status:** ✅ WORKING (two generators available)
- **Output:** `samples/brown_bear/matching/brown_bear_matching_levelX_preview.pdf`

### 8. Thumbnails
- **What:** 280×280 and 500×500 PNG images for TpT listing
- **Utility:** `utils/image_utils.py` has `create_thumbnail()` function
- **Generator:** ⚠️ Utility exists, need wrapper generator
- **Status:** ⚠️ PARTIAL (thumbnail function available, need generator script)
- **Workaround:** Screenshot covers manually OR use utility directly
- **Action needed:** Create simple generator wrapper using image_utils.py

### 9. TpT Full Product ZIP File
- **What:** ZIP containing items 1, 2, 3, 4 (Color PDF, B&W PDF, TOU, Quick Start)
- **Generator:** `production/generators/create_tpt_packages_updated.py`
- **Status:** ✅ WORKING
- **Output:** `production/generators/tpt_packages/brown_bear_matching_levelX_TpT.zip`

---

## 📍 Generator Locations

### Active Generators (in production/generators/)

**1. `generate_matching_constitution.py`**
- Creates 14 core PDFs (all levels, color, B&W, previews)
- Generates watermarked preview PDFs
- Output: samples/brown_bear/matching/

**2. `generate_complete_products_final.py`**
- Adds covers to each level
- Adds page numbers
- Creates FINAL 16-page PDFs
- Output: final_products/brown_bear/matching/

**3. `create_tpt_packages_updated.py`**
- Auto-generates level-specific Quick Starts
- Creates TpT ZIP packages
- Includes: Color PDF, B&W PDF, TOU, Quick Start
- Output: production/generators/tpt_packages/

### Available Generators (not in production/)

**4. `generate_freebie_new.py` (root directory)**
- Creates freebie products
- Status: Exists but needs integration

**5. `generate_level_covers_with_preview.py` (root directory)**
- Alternative preview generator
- Status: Exists but not primary

### Missing Generators (need to create)

**6. Description Generator**
- Purpose: Generate TpT listing description text
- Status: Does not exist yet
- Priority: Medium (can do manually)

**7. Thumbnail Generator (Wrapper)**
- Purpose: Create 280×280 and 500×500 PNG images from covers
- Status: Utility function exists (`utils/image_utils.py`), need wrapper script
- Priority: Low (can use utility directly or screenshot manually)

---

## 🚀 Complete Workflow

### To Generate Everything for a Product:

```bash
# Step 1: Core products (14 PDFs including previews)
cd /home/runner/work/small-wins-automation/small-wins-automation
python3 production/generators/generate_matching_constitution.py

# Step 2: Add covers and create FINAL PDFs (8 PDFs)
python3 production/generators/generate_complete_products_final.py

# Step 3: Create TpT packages with Quick Starts (4 ZIPs)
python3 production/generators/create_tpt_packages_updated.py

# Step 4: Create freebie
python3 generate_freebie_new.py

# Step 5: Create level covers with preview (optional)
python3 generate_level_covers_with_preview.py

# Step 6: Create description (manual for now)
# TODO: Build description generator

# Step 7: Create thumbnails (can use utility directly)
# Available: utils/image_utils.py create_thumbnail()
# TODO: Build simple wrapper generator
```

### Quick Run (all automated steps):
```bash
cd production/generators
./run_automation.sh
```

---

## 📊 Automation Status

### ✅ Working (7/9 items) - 78%
1. Final PDF Colour ✅
2. Final PDF B&W ✅
3. Terms of Use ✅
4. Quick Start ✅
5. Freebie ✅ (generator available in root)
7. Preview ✅ (two generators available)
9. TpT ZIP ✅

### ⚠️ Partial (1/9 items) - 11%
8. Thumbnails ⚠️ (utility function exists, need wrapper)

### ❌ Missing (1/9 items) - 11%
6. Description ❌ (need to create generator)

---

## 💡 To Complete Automation (100%)

### Immediate Actions (5 minutes)
1. Move `generate_freebie_new.py` to `production/generators/`
2. Test freebie generation
3. Integrate into workflow

### Soon (2-3 hours)
4. Create description generator
   - Template-based system
   - Product-specific details
   - Auto-generate for each level

5. Create thumbnail generator
   - Convert cover to PNG
   - Resize to 280×280 and 500×500
   - Auto-generate from FINAL PDFs

### Result
- 100% automation! 🎉
- One command generates everything
- No manual work needed

---

## 🎯 Current Branch

**Working on:** `copilot/enhance-automation-system`

**All generators located in:**
- `production/generators/` (active, organized)
- Root directory (available, needs integration)

---

## 📚 Related Documentation

**Quick references:**
- `RUN_AUTOMATION.md` - How to run automation
- `QUICK_REFERENCE.md` - Find files fast
- `AUTOMATION_STATUS.md` - What's automated
- `TPT_PACKAGE_UPDATE.md` - TpT package structure

**Detailed guides:**
- `production/README.md` - Production folder guide
- `LINE_OF_TRUTH_PLAN.md` - Organization strategy

---

## ✅ Summary

**Question:** "Where are these generators?"

**Answer:** 
- **Active:** production/generators/ (3 scripts)
- **Available:** Root directory (2 scripts)
- **Missing:** Need to create (2 generators)

**Status:** 67% automated, ready to use!

**Next steps:** Build description and thumbnail generators for 100% automation.
