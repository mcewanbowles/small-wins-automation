# 📖 HOW TO VIEW YOUR GENERATED PDFs

## 🎯 Quick Answer

**To review your PDFs, you need to generate them on YOUR COMPUTER:**

```bash
# Step 1: Install dependencies
pip install Pillow reportlab PyPDF2

# Step 2: Generate PDFs
./generate_all.sh

# Step 3: PDFs will be in these folders:
# - samples/brown_bear/matching/ (16 PDFs)
# - review_pdfs/ (9 PDFs)
```

**PDFs exist on YOUR COMPUTER, not in Git/GitHub**

---

## 📋 DETAILED STEP-BY-STEP INSTRUCTIONS

### Step 1: Open Terminal or Command Prompt

**On Mac:**
- Press `Cmd + Space`
- Type "Terminal"
- Press Enter

**On Windows:**
- Press `Win + R`
- Type "cmd"
- Press Enter

**On Linux:**
- Press `Ctrl + Alt + T`

---

### Step 2: Navigate to Your Repository

```bash
# Replace this with your actual path
cd /path/to/small-wins-automation
```

**To find your path:**
- **Mac/Linux:** `pwd` shows current directory
- **Windows:** `cd` shows current directory

**Example paths:**
```bash
# Mac example
cd /Users/yourname/Documents/small-wins-automation

# Windows example
cd C:\Users\yourname\Documents\small-wins-automation

# Linux example
cd /home/yourname/small-wins-automation
```

---

### Step 3: Install Dependencies (One-Time Setup)

```bash
pip install Pillow reportlab PyPDF2
```

**What this does:**
- Installs Python libraries needed to generate PDFs
- Only need to do this once
- Takes ~30 seconds

**If you get "pip not found":**
- Try `pip3` instead of `pip`
- Or install Python first

---

### Step 4: Generate PDFs

```bash
./generate_all.sh
```

**What happens:**
1. Script starts running
2. Shows progress messages
3. Creates 26 PDF files
4. Takes 2-3 minutes
5. Shows "Done!" when finished

**Expected output:**
```
🎨 Generating Small Wins TpT Products...
📄 Generating matching activities...
✓ Level 1 complete
✓ Level 2 complete
✓ Level 3 complete
✓ Level 4 complete
📄 Generating covers...
✓ Covers complete
📄 Generating freebie...
✓ Freebie complete
🎉 Done! 26 PDFs created
```

---

### Step 5: Find PDFs on Your Computer

**Use your file explorer/finder:**

**On Mac:**
1. Open Finder
2. Navigate to repository folder
3. Look for these folders:
   - `samples/brown_bear/matching/`
   - `review_pdfs/`

**On Windows:**
1. Open File Explorer
2. Navigate to repository folder
3. Look for these folders:
   - `samples\brown_bear\matching\`
   - `review_pdfs\`

**On Linux:**
1. Open file manager (Nautilus, Dolphin, etc.)
2. Navigate to repository folder
3. Look for these folders:
   - `samples/brown_bear/matching/`
   - `review_pdfs/`

---

### Step 6: Open and Review PDFs

**Method 1: Double-click**
- Just double-click any PDF file
- Opens in your default PDF viewer

**Method 2: Right-click**
- Right-click PDF file
- Choose "Open With..."
- Select your preferred PDF viewer

**Method 3: Command line**
```bash
# Mac
open samples/brown_bear/matching/brown_bear_matching_level1_color.pdf

# Windows
start samples\brown_bear\matching\brown_bear_matching_level1_color.pdf

# Linux
xdg-open samples/brown_bear/matching/brown_bear_matching_level1_color.pdf
```

---

## 📁 What You'll Find

### In samples/brown_bear/matching/ (16 PDFs)

**Full Activity PDFs (60 pages each):**
1. `brown_bear_matching_color.pdf` (4.1 MB)
   - Complete matching activities, all 4 levels, color version
2. `brown_bear_matching_bw.pdf` (2.0 MB)
   - Complete matching activities, all 4 levels, B&W version

**Level 1 (Errorless - Orange, 15 pages each):**
3. `brown_bear_matching_level1_color.pdf` (3.9 MB)
4. `brown_bear_matching_level1_bw.pdf` (1.9 MB)
5. `brown_bear_matching_level1_preview.pdf` (4.0 MB) ⭐ WITH WATERMARK

**Level 2 (Easy - Blue, 15 pages each):**
6. `brown_bear_matching_level2_color.pdf` (3.5 MB)
7. `brown_bear_matching_level2_bw.pdf` (1.5 MB)
8. `brown_bear_matching_level2_preview.pdf` (3.6 MB) ⭐ WITH WATERMARK

**Level 3 (Medium - Green, 15 pages each):**
9. `brown_bear_matching_level3_color.pdf` (3.5 MB)
10. `brown_bear_matching_level3_bw.pdf` (1.5 MB)
11. `brown_bear_matching_level3_preview.pdf` (3.6 MB) ⭐ WITH WATERMARK

**Level 4 (Challenge - Purple, 15 pages each):**
12. `brown_bear_matching_level4_color.pdf` (3.5 MB)
13. `brown_bear_matching_level4_bw.pdf` (1.5 MB)
14. `brown_bear_matching_level4_preview.pdf` (3.6 MB) ⭐ WITH WATERMARK

**Supporting Materials:**
15. `brown_bear_matching_quick_start.pdf` (17 KB)
16. `small_wins_tpt_documentation.pdf` (15 KB)

### In review_pdfs/ (9 PDFs)

**Cover Pages:**
1. `brown_bear_matching_level1_cover.pdf` (2.4 KB)
2. `brown_bear_matching_level2_cover.pdf` (2.4 KB)
3. `brown_bear_matching_level3_cover.pdf` (2.4 KB)
4. `brown_bear_matching_level4_cover.pdf` (2.4 KB)
5. `brown_bear_matching_level5_cover.pdf` (2.4 KB)

**Freebie Sample:**
6. `brown_bear_matching_freebie.pdf` (13 KB)

**Quick Start Guides:**
7. `brown_bear_matching_quick_start.pdf` (17 KB)
8. `brown_bear_find_cover_quick_start.pdf` (17 KB)

**Documentation:**
9. `small_wins_tpt_documentation.pdf` (15 KB)

---

## 🔧 PDF Viewer Options

### Free PDF Viewers You Can Use

**Windows:**
- **Adobe Acrobat Reader DC** (most popular, free)
  - Download: https://get.adobe.com/reader/
- **Microsoft Edge** (built-in with Windows 10/11)
- **Google Chrome** (built-in, if installed)
- **SumatraPDF** (free, lightweight, fast)
  - Download: https://www.sumatrapdfreader.org/

**Mac:**
- **Preview** (built-in with macOS) ⭐ RECOMMENDED
- **Adobe Acrobat Reader DC** (free)
  - Download: https://get.adobe.com/reader/
- **Google Chrome** (built-in, if installed)

**Linux:**
- **Evince** (usually pre-installed on GNOME)
- **Okular** (usually pre-installed on KDE)
- **Adobe Acrobat Reader** (free download)

---

## 💡 Understanding the Workflow

### Why PDFs Aren't in GitHub

**GitHub stores:**
- ✅ Source code (Python generators)
- ✅ Utilities (helper functions)
- ✅ Configurations (theme settings)
- ✅ Documentation (guides like this)

**Your computer stores:**
- ✅ Generated PDFs (after you run generators)

**Think of it like:**
- GitHub = Recipe book (stores the recipe)
- Your computer = Kitchen (where you cook/generate)
- PDFs = Finished meal (created in your kitchen)

**Why this design?**
1. **Size** - PDFs are ~40 MB total (too large for Git)
2. **Regenerable** - Can create PDFs anytime from source code
3. **Best practice** - Git is for source code, not output files
4. **Efficiency** - Keeps repository small and fast to clone

---

## 🎓 Frequently Asked Questions

### Q: Why can't I see PDFs in GitHub?

**A:** PDFs are gitignored (excluded from Git via `.gitignore` file). They exist only on your computer after you generate them.

### Q: Do I need to generate PDFs every time I clone?

**A:** Yes. When you clone the repository fresh, you get source code only. Run `./generate_all.sh` to create PDFs.

### Q: Can I share PDFs with someone else?

**A:** Yes! PDFs are regular files on your computer. Email them, use Dropbox, Google Drive, USB drive, etc.

### Q: Where exactly are PDFs stored?

**A:** In the repository folder on your computer:
```
your-repository-folder/
├── samples/
│   └── brown_bear/
│       └── matching/     ← 16 PDFs here
└── review_pdfs/          ← 9 PDFs here
```

### Q: How do I find the repository folder?

**A:** Use file explorer and navigate to where you cloned it, or:
```bash
# In terminal, from repository directory
pwd    # Mac/Linux - shows full path
cd     # Windows - shows full path
```

### Q: Can I move PDFs to another folder?

**A:** Yes! They're regular PDF files. Copy/move them anywhere you want.

### Q: What if generation fails?

**A:** Check:
1. Dependencies installed? `pip list | grep -i pillow`
2. In correct folder? `ls generate_all.sh` should show the file
3. Script executable? `chmod +x generate_all.sh`
4. Python installed? `python3 --version`

### Q: How do I regenerate if I delete PDFs?

**A:** Just run `./generate_all.sh` again. Takes 2-3 minutes.

### Q: Are PDFs print-ready?

**A:** Yes! All PDFs are 300 DPI, professional quality, ready to print or upload to TpT.

---

## 🚀 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ 1. CLONE REPOSITORY                                     │
│    git clone <repo>                                     │
│    → Gets source code only (no PDFs)                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. INSTALL DEPENDENCIES                                 │
│    pip install Pillow reportlab PyPDF2                  │
│    → Installs required libraries                        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. GENERATE PDFs                                        │
│    ./generate_all.sh                                    │
│    → Creates 26 PDFs in ~2-3 minutes                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 4. PDFs APPEAR ON YOUR COMPUTER                         │
│    samples/brown_bear/matching/  (16 PDFs)             │
│    review_pdfs/                  (9 PDFs)              │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 5. OPEN AND REVIEW PDFs                                 │
│    Double-click any PDF                                 │
│    → Opens in your PDF viewer                           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 6. USE YOUR PDFs!                                       │
│    Print, share, upload to TpT, etc.                    │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Quick Checklist

Follow these steps in order:

- [ ] Open Terminal/Command Prompt
- [ ] Navigate to repository: `cd small-wins-automation`
- [ ] Verify you're in right place: `ls generate_all.sh`
- [ ] Install dependencies: `pip install Pillow reportlab PyPDF2`
- [ ] Generate PDFs: `./generate_all.sh`
- [ ] Wait for completion (2-3 minutes)
- [ ] Open file explorer/finder
- [ ] Navigate to `samples/brown_bear/matching/`
- [ ] Verify 16 PDFs exist ✓
- [ ] Navigate to `review_pdfs/`
- [ ] Verify 9 PDFs exist ✓
- [ ] Double-click any PDF to open
- [ ] Review your products!
- [ ] 🎉 Done!

---

## 🎯 Summary

**To review your PDFs:**
1. Generate them locally with `./generate_all.sh`
2. Find them in `samples/` and `review_pdfs/` folders
3. Open with any PDF viewer on your computer

**PDFs are:**
- ✅ On your computer (not in Git)
- ✅ Print-ready (300 DPI)
- ✅ Professional quality
- ✅ Ready to use/share/upload

**That's it!** You now know how to view and review your generated PDFs! 🎉
