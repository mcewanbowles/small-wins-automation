# 📍 Where to Review Generated PDFs

## Current Branch
**Branch:** `copilot/enhance-automation-system`

This is your main working branch with all the complete generators and system.

---

## 📁 PDF Locations

### Location 1: Main Product PDFs
**Directory:** `samples/brown_bear/matching/`

**What's Here:**
- Full matching activities (color & B&W, 60 pages each)
- Individual level PDFs (15 pages each)
  - Level 1 (Orange - Errorless)
  - Level 2 (Blue - Easy)
  - Level 3 (Green - Medium)
  - Level 4 (Purple - Challenge)
- Each level has 3 versions:
  - Color version
  - Black & White version
  - Preview version (WITH WATERMARK)
- Quick Start guide
- TpT documentation

**Files:**
```
samples/brown_bear/matching/
├── brown_bear_matching_color.pdf (4.1 MB, 60 pages)
├── brown_bear_matching_bw.pdf (2.0 MB, 60 pages)
├── brown_bear_matching_level1_color.pdf (3.9 MB, 15 pages)
├── brown_bear_matching_level1_bw.pdf (1.9 MB, 15 pages)
├── brown_bear_matching_level1_preview.pdf (4.0 MB, 15 pages) ⭐
├── brown_bear_matching_level2_color.pdf (3.5 MB, 15 pages)
├── brown_bear_matching_level2_bw.pdf (1.5 MB, 15 pages)
├── brown_bear_matching_level2_preview.pdf (3.6 MB, 15 pages) ⭐
├── brown_bear_matching_level3_color.pdf (3.5 MB, 15 pages)
├── brown_bear_matching_level3_bw.pdf (1.5 MB, 15 pages)
├── brown_bear_matching_level3_preview.pdf (3.6 MB, 15 pages) ⭐
├── brown_bear_matching_level4_color.pdf (3.5 MB, 15 pages)
├── brown_bear_matching_level4_bw.pdf (1.5 MB, 15 pages)
├── brown_bear_matching_level4_preview.pdf (3.6 MB, 15 pages) ⭐
├── brown_bear_matching_quick_start.pdf (17 KB)
└── small_wins_tpt_documentation.pdf (15 KB)
```

### Location 2: Review Materials
**Directory:** `review_pdfs/`

**What's Here:**
- Professional cover pages for all levels
- Freebie sample for marketing
- Quick Start guides
- TpT documentation

**Files:**
```
review_pdfs/
├── brown_bear_matching_level1_cover.pdf (2.4 KB)
├── brown_bear_matching_level2_cover.pdf (2.4 KB)
├── brown_bear_matching_level3_cover.pdf (2.4 KB)
├── brown_bear_matching_level4_cover.pdf (2.4 KB)
├── brown_bear_matching_level5_cover.pdf (2.4 KB)
├── brown_bear_matching_freebie.pdf (13 KB)
├── brown_bear_matching_quick_start.pdf (17 KB)
├── brown_bear_find_cover_quick_start.pdf (17 KB)
└── small_wins_tpt_documentation.pdf (15 KB)
```

### Location 3: Draft Documents
**Directory:** `Draft General Docs/TOU_etc/`

**What's Here:**
- General TpT documentation templates
- Terms of Use
- How to Use guides
- Student directions

---

## ⚠️ Important Note About PDFs

**PDFs are NOT committed to Git!**

The `.gitignore` file excludes `*.pdf` to keep the repository size manageable.

This means:
- ✅ PDFs are generated locally when you run `./generate_all.sh`
- ✅ PDFs exist on your computer after generation
- ❌ PDFs are NOT pushed to GitHub
- ❌ PDFs won't appear in git status

---

## 🚀 How to Generate PDFs

If the PDF directories are empty, run:

```bash
./generate_all.sh
```

This will create all 25 PDF files in the locations above.

---

## 📂 How to Access PDFs

### On Your Local Computer:

1. **Navigate to the repository:**
   ```bash
   cd /path/to/small-wins-automation
   ```

2. **Check main products:**
   ```bash
   ls samples/brown_bear/matching/
   ```

3. **Check review materials:**
   ```bash
   ls review_pdfs/
   ```

4. **Open a PDF:**
   - On Mac: `open samples/brown_bear/matching/brown_bear_matching_level1_color.pdf`
   - On Linux: `xdg-open samples/brown_bear/matching/brown_bear_matching_level1_color.pdf`
   - On Windows: Double-click the file in File Explorer

### File Browser:
Navigate to your repository folder and open:
- `samples/brown_bear/matching/` - for main products
- `review_pdfs/` - for marketing materials

---

## 📊 What to Review

### For Product Quality:
**Check:** `samples/brown_bear/matching/brown_bear_matching_level1_color.pdf`
- Verify 300 DPI quality
- Check rounded borders (0.12" radius)
- Confirm navy borders (#1E3A5F)
- Verify orange level colors (#F4B400)
- Check image quality and centering

### For Marketing Materials:
**Check:** `review_pdfs/brown_bear_matching_freebie.pdf`
- Sample pages for TpT preview
- Make sure it's compelling for teachers

### For Teacher Experience:
**Check:** `samples/brown_bear/matching/brown_bear_matching_quick_start.pdf`
- Clear instructions
- Easy to understand
- Professional appearance

### For Preview/TpT Upload:
**Check:** `samples/brown_bear/matching/brown_bear_matching_level1_preview.pdf`
- Watermark is visible (25% opacity)
- Prevents unauthorized use
- Still shows product quality

---

## 📋 Quick Reference

| What to Review | Where to Find It |
|----------------|------------------|
| **Full Product** | `samples/brown_bear/matching/brown_bear_matching_color.pdf` |
| **Level 1 Sample** | `samples/brown_bear/matching/brown_bear_matching_level1_color.pdf` |
| **Preview (Watermarked)** | `samples/brown_bear/matching/brown_bear_matching_level1_preview.pdf` |
| **Freebie Sample** | `review_pdfs/brown_bear_matching_freebie.pdf` |
| **Cover Pages** | `review_pdfs/brown_bear_matching_level*_cover.pdf` |
| **Quick Start** | `samples/brown_bear/matching/brown_bear_matching_quick_start.pdf` |
| **Terms of Use** | `samples/brown_bear/matching/small_wins_tpt_documentation.pdf` |

---

## 💡 Tips

1. **Start with Level 1 Color PDF** - This shows the full product quality
2. **Review the Preview PDFs** - These go on TpT as samples
3. **Check the Freebie** - This is your marketing tool
4. **Verify Quick Start Guide** - Teachers need clear instructions

---

**Last Updated:** February 8, 2026  
**Branch:** copilot/enhance-automation-system  
**Status:** PDFs generated and ready for review (local only)
