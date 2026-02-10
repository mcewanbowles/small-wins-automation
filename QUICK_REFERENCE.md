# Quick Reference Card 🎯

**For when you need to find something FAST!**

---

## 📍 Where Is Everything?

### Need FINAL products?
→ `production/final_products/brown_bear/matching/`

### Need generators?
→ `production/generators/`

### Need support docs?
→ `production/support_docs/`

### Find & Cover (still developing)?
→ `samples/brown_bear/find_cover/`
→ `generators/find_cover/`

---

## 🚀 Quick Commands

### Generate Brown Bear Matching:
```bash
cd production/generators
python3 generate_matching_constitution.py
```

### Create Complete Products (with covers):
```bash
cd production/generators
python3 generate_complete_products_final.py
```

### Create TpT Packages:
```bash
cd production/generators
python3 create_tpt_packages.py
```

---

## 📊 File Counts

| What | Count | Where |
|------|-------|-------|
| FINAL PDFs | 12 | production/final_products/brown_bear/matching/ |
| Active Generators | 3 | production/generators/ |
| Support Docs | 2 | production/support_docs/ |

---

## ✅ One Simple Rule

**If it's in `production/`, it's FINAL and ready to use!**

**If it's NOT in `production/`, it's either:**
- Still being developed (like Find & Cover)
- Old version (can archive later)
- Not needed

---

## 🎯 Your Line of Truth

```
production/
├── README.md (← read this!)
├── generators/ (← 3 scripts)
├── support_docs/ (← TOU & templates)
└── final_products/
    └── brown_bear/
        └── matching/ (← 12 PDFs)
```

**That's it! Everything else is extra.**

---

## 💡 When In Doubt

1. Check `production/` first
2. Read `production/README.md`
3. If not there, it's in development or old

---

## ⏭️ Next Steps

**Now:** Use production/ for current work

**Soon:** Get official TOU and Quick Start templates

**Later:** Archive old files when confident

---

**Branch:** copilot/enhance-automation-system
**Your Line of Truth:** production/
**Last Updated:** February 10, 2026
