# Social Stories Quick Start Guide

## 🚀 Getting Started

### Installation
1. Install Python 3.7 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Generate All Social Stories
```bash
python generators/social_stories/generator.py
```

This will generate PDFs for all 5 social stories in `exports/social_stories/`:
- ✅ Good Touch, Bad Touch (Safety)
- ✅ Erections & Wet Dreams (Boys Puberty)
- ✅ Bras & Body Changes (Girls Puberty)
- ✅ Body Odor & Deodorant (Hygiene)
- ✅ Masturbation is Private (Privacy)

### Generate a Single Story
```bash
python generators/social_stories/generator.py --story assets/social_stories/good_touch_bad_touch/SOCIAL_STORY_Good_Touch_Bad_Touch.txt
```

## 📋 What Gets Generated

Each PDF includes:
- **Cover page** with title, subtitle, and large image placeholder
- **Story pages** (one page per section from the text file)
- **Large image placeholders** (5" × 4") for Boardmaker icons
- **Professional branding** (Small Wins Studio colors and footers)
- **Page numbers** and copyright information
- **Rounded borders** and accent stripes

## 🎨 Design Features

✓ **Brand Colors:**
  - Navy (#1E3A5F) - main text and titles
  - Teal (#2AAEAE) - accent stripes
  - Gold (#E8C547) - branding elements

✓ **Typography:**
  - Primary: Helvetica (Comic Sans MS if available)
  - Accessible, clear, and professional

✓ **Layout:**
  - US Letter (8.5" × 11")
  - 0.5" margins
  - Large image placeholders for visual learners
  - Clear hierarchy and spacing

## 📝 Adding Icons

Each page has a **dotted-border placeholder** marked:
```
[ Image Placeholder ]
Add Boardmaker icon here
```

To add your Boardmaker icons:
1. Open the PDF in a PDF editor (Adobe Acrobat, etc.)
2. Place your Boardmaker icon image into the placeholder area
3. Resize to fill the 5" × 4" space
4. Save the updated PDF

## 🔄 Updating Content

To modify a social story:
1. Edit the text file in `assets/social_stories/[story_name]/`
2. Re-run the generator
3. The PDF will be regenerated with your changes

## 📊 Current Stories

| Story | Topic | Age Range | Pages |
|-------|-------|-----------|-------|
| Good Touch Bad Touch | Safety | All Ages (5+) | ~13 |
| Erections & Wet Dreams | Boys Puberty | 10-16 | ~9 |
| Bras & Body Changes | Girls Puberty | 8-14 | ~10 |
| Body Odor & Deodorant | Hygiene | All Ages | ~8 |
| Masturbation is Private | Privacy | 10+ | ~7 |

## 🎯 Next Steps

1. ✅ Generate PDFs (completed)
2. ⏳ Add Boardmaker icons to placeholders (tomorrow)
3. ⏳ Review and test with students
4. ⏳ Export to TPT marketplace

## 💡 Tips

- **Keep text simple:** 1-2 sentences per phrase
- **Use clear language:** Avoid jargon
- **Be sensitive:** These topics require careful, respectful handling
- **Include visuals:** The large icons are essential for visual learners
- **Test first:** Review with colleagues before using with students

## 📞 Support

For questions or issues:
- Check the detailed README in `generators/social_stories/`
- Review the Design Constitution in `design/Design-Constitution.md`
- Contact Small Wins Studio

---

© 2025 Small Wins Studio
