# Production Folder - Line of Truth 🎯

**This folder contains ONLY current, ready-to-use files for Small Wins Studio products.**

## 📁 Structure

```
production/
├── generators/          ← Active generator scripts ONLY
├── support_docs/        ← Official TOU and Quick Start templates
└── final_products/      ← FINAL, ready-to-use PDFs
    └── brown_bear/
        └── matching/    ← Brown Bear Matching FINAL PDFs
```

## ✅ What's in Production

### Brown Bear Matching (Complete ✓)
**Final Products:** 12 PDFs
- Level 1 Errorless: Color + B&W (17 pages each)
- Level 2 Easy: Color + B&W (17 pages each)
- Level 3 Medium: Color + B&W (17 pages each)
- Level 4 Challenge: Color + B&W (17 pages each)
- 4 Cover PDFs

**Generators:** 3 active scripts
- `generate_matching_constitution.py` - Main product generator
- `generate_complete_products_final.py` - Adds covers and How to Use
- `create_tpt_packages.py` - Creates TpT ZIP packages

## 🎯 How to Use

### To Generate Brown Bear Matching:
```bash
cd production/generators
python3 generate_matching_constitution.py
python3 generate_complete_products_final.py
```

### To Create TpT Packages:
```bash
cd production/generators
python3 create_tpt_packages.py
```

## 📂 Other Products

**Find & Cover** - Still in development
- Located in: `samples/brown_bear/find_cover/`
- Located in: `generators/find_cover/`
- Status: Not ready for production yet
- Will be added here when FINAL versions exist

## 🔄 Adding New Products

When a product is finalized:
1. Create folder: `production/final_products/{theme}/{product}/`
2. Copy FINAL PDFs only
3. Update this README
4. Move relevant generator to `production/generators/`

## ⚠️ Important Rules

**Only put files in production/ if:**
- ✅ They have "FINAL" in the name (for PDFs)
- ✅ They are actively used (for generators)
- ✅ They are official versions (for support docs)
- ✅ They are ready for customer use

**Don't put in production/:**
- ❌ Draft versions
- ❌ Test files
- ❌ Old versions
- ❌ Work in progress

## 💡 ADHD-Friendly Tips

**One simple rule:** If it's in `production/`, it's current and ready to use.

**When in doubt:** Check this folder first. If it's not here, it's either:
- Still being developed (check `samples/` or `generators/`)
- Old version (may be in `archive/` later)
- Not needed

---

**Last Updated:** February 10, 2026
**Maintained by:** Line of Truth system
**Branch:** copilot/enhance-automation-system
