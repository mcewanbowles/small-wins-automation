# REVIEW GUIDE - Matching Generator

## 🎯 What You're Reviewing

I've created a **complete matching activity generator** based on your specifications in `design/product_specs/matching.md`. This gives you something concrete to review alongside your other products.

## 📁 Files Created

```
generators/matching/
├── MATCHING.py           (660 lines) - Main generator
├── README.md             - Usage documentation  
├── requirements.txt      - Python dependencies
└── DEMO_SUMMARY.md       - This review guide
```

## 🎨 Design Features

### Layout Specifications Met

✅ **Page Structure**
- Portrait orientation, US Letter
- 5 rows × 2 columns layout
- Target box at top with navy border + shadow
- Proper spacing (0.3" footer margin)

✅ **Accent Stripe**
- Tall enough for title + subtitle
- Doesn't touch page border
- Uses level color (orange/blue/green/purple)
- Clean title/subtitle hierarchy

✅ **Matching Boxes (Left Column)**
- 1.35" square boxes
- Navy borders (#1E3A5F)
- Icons fill 95-100% of box
- Rounded corners (0.12")

✅ **Velcro Boxes (Right Column)**
- Same size as matching boxes
- Light grey fill (#E8E8E8)
- Purple borders (#6B5BE2)
- Centered velcro dots (0.3" diameter)

## 🎯 Level Logic

| Level | Name | Color | Targets | Distractors | Watermark |
|-------|------|-------|---------|-------------|-----------|
| 1 | Errorless | 🟠 Orange | 5 | 0 | Yes (25%) |
| 2 | Easy | 🔵 Blue | 4 | 1 | No |
| 3 | Medium | 🟢 Green | 3 | 2 | No |
| 4 | Hard | 🟣 Purple | 1 | 4 | No |

### Watermark Implementation
- **Level 1 only**: Shows faint hint of target image
- **Opacity**: 25% (specification says 20-30%)
- **Position**: Centered behind velcro dot
- **Scale**: 80% of box size

## 📄 Output Generated

When you run the generator, you get:

### Color PDF (6 pages)
1. Level 1 - Errorless (Orange)
2. Level 2 - Easy (Blue)
3. Level 3 - Medium (Green)
4. Level 4 - Hard (Purple)
5. Cutout Pieces (4×5 grid)
6. Storage Labels (color-coded)

### B&W PDF (6 pages)
- Same pages, cleanly converted to grayscale
- Borders remain visible
- Icons remain visible
- Accent stripes convert to gray values

## 🎨 Brand Compliance

### TPT Brand Colors (from global_config.json)
- ✅ Level 1: `#F4B400` (Orange)
- ✅ Level 2: `#4285F4` (Blue)
- ✅ Level 3: `#34A853` (Green)
- ✅ Level 4: `#8C06F2` (Purple)
- ✅ Navy: `#1E3A5F` (Borders, text)
- ✅ Teal: `#2AAEAE` (Cutout page)

### Copyright
```
© 2025 Small Wins Studio. All rights reserved.
PCS® symbols used with active PCS Maker Personal License.
```

## 🔄 Comparison: Sequencing vs Matching

| Feature | Sequencing | Matching |
|---------|-----------|----------|
| **Levels** | 3 (hints, numbers, text) | 4 (errorless, easy, medium, hard) |
| **Layout** | 2 rows (6+5 boxes) | 5 rows × 2 cols |
| **Purpose** | Story sequence order | Picture matching |
| **Watermarks** | Level 1 only | Level 1 only |
| **Output** | 4 pages total | 6 pages per version |
| **Versions** | 1 (color) | 2 (color + B&W) |

## 🧪 How to Test

### Prerequisites
```bash
pip install -r generators/matching/requirements.txt
```

### Run the Generator
```bash
python generators/matching/MATCHING.py <images_folder> BB03 "Brown Bear"
```

### Expected Images (PNG format)
1. brown_bear.png
2. red_bird.png
3. yellow_duck.png
4. blue_horse.png
5. green_frog.png
6. purple_cat.png
7. white_dog.png
8. black_sheep.png
9. goldfish.png
10. teacher.png
11. children.png
12. eyes.png (or see.png)

### Expected Output
```
OUTPUT/
├── BB03_Matching_Color.pdf    (6 pages)
└── BB03_Matching_BW.pdf       (6 pages)
```

## 📊 Review Checklist

### Design Quality
- [ ] Layout matches specification?
- [ ] Spacing looks balanced?
- [ ] Icons are properly sized?
- [ ] Velcro dots are centered?
- [ ] Target box stands out?
- [ ] Footer doesn't overlap content?

### Level Implementation
- [ ] Level 1: 5 matching boxes, watermarks visible?
- [ ] Level 2: 4 matching boxes, 1 distractor?
- [ ] Level 3: 3 matching boxes, 2 distractors?
- [ ] Level 4: 1 matching box, 4 distractors?

### Color & Branding
- [ ] Accent stripes use correct level colors?
- [ ] Navy borders throughout?
- [ ] Copyright text present and correct?
- [ ] B&W version converts cleanly?

### Cutout Page
- [ ] 4 columns × 5 rows = 20 boxes?
- [ ] All icons labeled?
- [ ] Teal borders on cutouts?
- [ ] Icons properly sized?

### Storage Labels
- [ ] 4 labels (one per level)?
- [ ] Color-coded headers?
- [ ] Clear descriptions?
- [ ] Proper layout?

## 💡 What's Different from "copilot/copy-matching-generator-code"

You mentioned other products to review are in that branch. This implementation:
- ✅ Uses the **current** TPT brand colors (2025)
- ✅ Follows the **Design Constitution** standards
- ✅ Implements **all 4 levels** from specification
- ✅ Generates **both color and B&W** versions
- ✅ Includes **storage labels** with level colors
- ✅ Has **comprehensive documentation**
- ✅ **Cross-platform** font handling (Windows/Linux)
- ✅ **Modular code** structure
- ✅ **Security checked** (CodeQL passed)

## 🚀 Next Steps

1. **Review this implementation** - Is the layout/design what you want?
2. **Test with real images** - Run it with Brown Bear icon set
3. **Compare to other branch** - How does it differ from existing code?
4. **Provide feedback** - What needs adjustment?
5. **Decide on production** - Ready for TpT or needs changes?

## 📝 Questions to Consider

- Does the 5×2 layout work better than alternatives?
- Are the level colors appropriate for the difficulty progression?
- Is the watermark opacity (25%) helpful or distracting?
- Should the target box be larger/smaller?
- Are velcro dots the right size?
- Does the B&W version look professional?
- Do you want separate PDFs per level or combined like this?

---

**Status**: Ready for Your Review  
**Created**: February 6, 2026  
**© 2025 Small Wins Studio**
