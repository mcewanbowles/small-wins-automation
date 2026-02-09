# Terms of Use & Quick Start Requirements

## User Requirements

**From user:** "Please update all records past and future - the Terms of Use to use is the following versions - all others can be deleted. Draft General Docs/TOU_etc/Terms_of_Use_Credits.pdf This is the document that should be included in TPT Final ZIP. The Quick Start guide will change for each product and level - it will need to be updated - can you ensure that the generator updates the Quick Start guide before including it in the Zip folder - ensure correct level each time. Draft General Docs/Quick_Start_Guides/Quick_Start_Guide_Matching_Level 1 - there should be a version updated for each level and then merged into final ZIP."

---

## Terms of Use (TOU)

### Standard File
**File:** `Draft General Docs/TOU_etc/Terms_of_Use_Credits.pdf`

**Requirements:**
- This is THE standard TOU for all products, past and future
- Must be included in all TpT Final ZIP packages
- All other TOU versions should be deleted/archived

### Current Status
**Current location:** `assets/global/tpt_support_docs/Terms of Use.pdf`

**Target location:** `assets/global/tpt_support_docs/Terms_of_Use_Credits.pdf`

**Action needed:**
1. Obtain Terms_of_Use_Credits.pdf from Draft General Docs/TOU_etc/
2. Place at target location
3. Update all generators to use this file
4. Archive old versions

---

## Quick Start Guides

### Requirements
**Template:** `Draft General Docs/Quick_Start_Guides/Quick_Start_Guide_Matching_Level 1`

**Key requirements:**
- **Level-specific:** Each level (1-4) gets its own Quick Start guide
- **Dynamic generation:** Generator must update Quick Start before including in ZIP
- **Correct level:** Each guide must have correct level number and name
- **In ZIP:** Level-specific Quick Start included in each TpT package

### File Naming
- Level 1: `Quick_Start_Guide_Matching_Level1.pdf` (Errorless)
- Level 2: `Quick_Start_Guide_Matching_Level2.pdf` (Easy)
- Level 3: `Quick_Start_Guide_Matching_Level3.pdf` (Medium)
- Level 4: `Quick_Start_Guide_Matching_Level4.pdf` (Challenge)

### Generator Requirements
**Must:**
1. Accept level parameter (1, 2, 3, or 4)
2. Update level number in PDF content
3. Update level name (Errorless/Easy/Medium/Challenge)
4. Generate fresh PDF for each level
5. Run BEFORE packaging in ZIP

---

## TpT Package Structure

### Each ZIP Contains (4 files):
1. Color FINAL PDF (17 pages with cover)
2. B&W FINAL PDF (17 pages with cover)
3. **Terms_of_Use_Credits.pdf** (standard for all)
4. **Quick_Start_Guide_Matching_LevelX.pdf** (level-specific)

### Example:
```
brown_bear_matching_level1_TpT.zip
├── Brown_Bear_Matching_Level1_Errorless_Color.pdf
├── Brown_Bear_Matching_Level1_Errorless_BW.pdf
├── Terms_of_Use_Credits.pdf
└── Quick_Start_Guide_Matching_Level1.pdf (← Level 1 specific)
```

---

## Implementation Status

### Completed
- [x] Documentation of requirements
- [x] System design
- [x] File naming conventions

### In Progress
- [ ] Quick Start generator creation
- [ ] TpT packager updates
- [ ] Testing

### Pending (Need files)
- [ ] Obtain Terms_of_Use_Credits.pdf
- [ ] Obtain Quick Start template
- [ ] Replace placeholder files

---

## Next Steps

1. **Create Quick Start generator** - generates level-specific PDFs
2. **Update TpT packager** - includes dynamic Quick Start generation
3. **Test with current files** - use existing TOU as placeholder
4. **Await source files** - replace when Terms_of_Use_Credits.pdf available
5. **Final generation** - regenerate all packages with correct files
6. **Cleanup** - archive old TOU versions

---

## Questions for User

1. Can you provide Terms_of_Use_Credits.pdf file?
2. Can you provide Quick Start template or example?
3. Should old TOU versions be deleted or archived?
4. Are there other products (besides Matching) that need Quick Start guides?

---

**Status:** Requirements documented, implementation in progress
**Updated:** 2026-02-09
