# 🗑️ FILE CLEANUP PLAN

**Purpose:** Identify obsolete/duplicate files for deletion or archiving  
**Date:** February 9, 2026

---

## 📊 GENERATOR SCRIPTS ANALYSIS

### ✅ KEEP (Current/Active - 7 scripts)

**Core Generators:**
1. `generate_matching_constitution.py` - Main matching product generator
2. `generate_complete_products_final.py` - Final complete products with covers
3. `generate_covers_final.py` - Final cover generator
4. `generate_freebie_new.py` - Current freebie generator
5. `create_tpt_packages.py` - TpT package creator
6. `generate_quick_start_professional.py` - Professional Quick Start
7. `generate_tpt_documentation.py` - TpT documentation

### 🗄️ ARCHIVE (Obsolete/Superseded - 10 scripts)

**Move to `archive/generators/` folder:**

1. `generate_cover_page.py` → Superseded by generate_covers_final.py
2. `generate_cover_page_new.py` → Intermediate version, superseded
3. `generate_covers_amended.py` → Superseded by generate_covers_final.py
4. `generate_level_covers_with_preview.py` → Alternative approach, not used
5. `generate_product_covers_windows.py` → Windows-specific, integrated into final
6. `generate_product_covers_marketing.py` → Marketing version, integrated into final
7. `generate_products_amended.py` → Superseded by generate_complete_products_final.py
8. `generate_final_products_complete.py` → Similar to generate_complete_products_final.py
9. `generate_freebie.py` → Old version, superseded by generate_freebie_new.py
10. `generate_quick_start_instructions.py` → Superseded by generate_quick_start_professional.py

**Rationale:** These were development iterations. Keep in archive for reference but remove from active use.

---

## 📄 PDF FILES ANALYSIS

### samples/brown_bear/matching/ - CLEANUP NEEDED

#### ✅ KEEP (Final Versions)

**Full Products:**
- `brown_bear_matching_color.pdf` - Full 60-page color product
- `brown_bear_matching_bw.pdf` - Full 60-page B&W product

**Level Products (if these are most recent):**
- `brown_bear_matching_level1_color.pdf`
- `brown_bear_matching_level1_bw.pdf`
- `brown_bear_matching_level2_color.pdf`
- `brown_bear_matching_level2_bw.pdf`
- `brown_bear_matching_level3_color.pdf`
- `brown_bear_matching_level3_bw.pdf`
- `brown_bear_matching_level4_color.pdf`
- `brown_bear_matching_level4_bw.pdf`

**Support Files:**
- `brown_bear_matching_quick_start.pdf`
- `small_wins_tpt_documentation.pdf`

**Preview Files (for TpT):**
- `brown_bear_matching_level1_preview.pdf`
- `brown_bear_matching_level2_preview.pdf`
- `brown_bear_matching_level3_preview.pdf`
- `brown_bear_matching_level4_preview.pdf`

#### 🗑️ DELETE (Duplicates/Intermediate Versions)

**Duplicate Covers:**
- `cover_level1_marketing.pdf` → Intermediate version
- `cover_level1_windows.pdf` → Intermediate version
- `cover_level2_marketing.pdf` → Intermediate version
- `cover_level2_windows.pdf` → Intermediate version
- `cover_level3_marketing.pdf` → Intermediate version
- `cover_level3_windows.pdf` → Intermediate version
- `cover_level4_marketing.pdf` → Intermediate version
- `cover_level4_windows.pdf` → Intermediate version

**Duplicate Products (with covers already merged):**
- `brown_bear_matching_level1_color_with_cover.pdf` → Superseded by FINAL version
- `brown_bear_matching_level1_color_with_cover_windows.pdf` → Superseded
- `brown_bear_matching_level2_color_with_cover.pdf` → Superseded
- `brown_bear_matching_level2_color_with_cover_windows.pdf` → Superseded
- `brown_bear_matching_level3_color_with_cover.pdf` → Superseded
- `brown_bear_matching_level3_color_with_cover_windows.pdf` → Superseded
- `brown_bear_matching_level4_color_with_cover.pdf` → Superseded
- `brown_bear_matching_level4_color_with_cover_windows.pdf` → Superseded

**Total to Delete:** 16 files (~60 MB)

### review_pdfs/ - KEEP ALL

**These are for review/marketing purposes:**
- brown_bear_matching_level1_cover.pdf ✓
- brown_bear_matching_level2_cover.pdf ✓
- brown_bear_matching_level3_cover.pdf ✓
- brown_bear_matching_level4_cover.pdf ✓
- brown_bear_matching_level5_cover.pdf ✓
- brown_bear_matching_freebie.pdf ✓
- brown_bear_matching_quick_start.pdf ✓
- brown_bear_find_cover_quick_start.pdf ✓
- small_wins_tpt_documentation.pdf ✓

### final_products/brown_bear/matching/ - ORGANIZE

**Check if this directory has the actual final versions:**
- If yes, these are the MASTER copies
- If duplicates of samples/, consolidate
- Move to outputs/ structure

---

## 📋 CLEANUP ACTIONS

### Step 1: Create Archive Directories
```bash
mkdir -p archive/generators
mkdir -p archive/pdfs/intermediate_versions
```

### Step 2: Archive Obsolete Generators
```bash
# Move to archive
mv generate_cover_page.py archive/generators/
mv generate_cover_page_new.py archive/generators/
mv generate_covers_amended.py archive/generators/
mv generate_level_covers_with_preview.py archive/generators/
mv generate_product_covers_windows.py archive/generators/
mv generate_product_covers_marketing.py archive/generators/
mv generate_products_amended.py archive/generators/
mv generate_final_products_complete.py archive/generators/
mv generate_freebie.py archive/generators/
mv generate_quick_start_instructions.py archive/generators/
```

### Step 3: Archive Intermediate PDFs
```bash
cd samples/brown_bear/matching/

# Archive intermediate covers
mv cover_level*_marketing.pdf ../../../archive/pdfs/intermediate_versions/
mv cover_level*_windows.pdf ../../../archive/pdfs/intermediate_versions/

# Archive intermediate products with covers
mv *_with_cover.pdf ../../../archive/pdfs/intermediate_versions/
mv *_with_cover_windows.pdf ../../../archive/pdfs/intermediate_versions/
```

### Step 4: Organize Final Products
```bash
# Create outputs structure
mkdir -p outputs/brown_bear/matching/{level1,level2,level3,level4,freebie}

# Move final products to outputs (after confirming which are final)
# This step requires manual verification
```

### Step 5: Update .gitignore
```bash
# Add to .gitignore:
archive/
outputs/
*.pyc
__pycache__/
```

---

## ⚠️ SAFETY MEASURES

### Before Deletion:
1. ✅ Create full backup of repository
2. ✅ Commit all current work
3. ✅ Test that archived generators still work (if needed)
4. ✅ Verify final products are correct
5. ✅ Get user approval

### During Cleanup:
1. Move to archive/ first (don't delete immediately)
2. Test complete workflow with remaining files
3. Verify TpT packages still build correctly
4. Check that all 4 levels can be generated

### After Cleanup:
1. Run master generator end-to-end
2. Verify all outputs
3. Update documentation
4. Create WORKFLOW.md guide

---

## 📊 EXPECTED RESULTS

### Space Savings:
- Archived generators: ~200 KB
- Archived PDFs: ~60 MB
- Total cleanup: ~60 MB

### Organization Improvement:
- 7 active generators (down from 17) - 59% reduction
- Clear naming (no more "new", "amended", "final" confusion)
- Organized outputs/ structure
- Clean samples/ directory

### Maintainability:
- Clear which scripts to use
- Easy to find final products
- Documented workflow
- Reduced confusion

---

## 🎯 SUCCESS CRITERIA

After cleanup:
- ✅ Only 7 active generators in root
- ✅ 10 obsolete generators in archive/
- ✅ No duplicate PDFs in samples/
- ✅ All final products in outputs/
- ✅ TpT packages still build correctly
- ✅ Documentation updated
- ✅ Workflow guide created

---

## 📝 NEXT STEPS

1. **Get user approval** for cleanup plan
2. **Create backup** of current state
3. **Execute cleanup** steps 1-4
4. **Test thoroughly** after cleanup
5. **Update documentation** and workflow guide

**Estimated Time:** 2-3 hours  
**Risk Level:** Low (using archive, not delete)  
**Benefits:** High (clarity, organization, maintainability)
