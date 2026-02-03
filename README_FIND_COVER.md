# Find and Cover - Brown Bear Theme

## Product Overview

**Find and Cover** is a visual scanning and discrimination activity designed for special education students. Students identify a target icon and find all matching instances in a 4×4 grid, covering them with chips, counters, or mini erasers.

### Product Details
- **39 Pages Total**
- **3 Difficulty Levels** (Progressive challenge)
- **12 Activities per Level** (One for each Brown Bear icon)
- **Storage Labels Included** (One page per level)
- **Both Color and B&W Versions**

---

## What's Included

### Activity Pages (36 pages)
Each activity page includes:
- **Target Icon Display:** Shows the icon to find
- **4×4 Grid:** 16 cells with various icons
- **Color-Coded Levels:**
  - Level 1 (Orange): Beginner - 1 vs 1 (target + 1 distractor)
  - Level 2 (Blue): Intermediate - 1 vs 2 (target + 2 distractors)
  - Level 3 (Green): Advanced - 1 vs 3 (target + 3 distractors)

### Storage Labels (3 pages)
- **12 Labels per Page** (3×4 grid)
- **One Set per Level** for easy organization
- **Professional Design** with icons and names
- **Cut and Attach** to folders for storage

---

## Icons Included

All 12 Brown Bear, Brown Bear, What Do You See? characters:

1. **Black Sheep** 7. **White Dog**
2. **Blue Horse** 8. **Yellow Duck**
3. **Brown Bear** 9. **Children**
4. **Green Frog** 10. **Goldfish**
5. **Purple Cat** 11. **Eyes** (See)
6. **Red Bird** 12. **Teacher**

---

## How to Generate

```bash
python generate_find_cover_constitution.py
```

### Outputs
- **Color PDF:** `brown_bear_find_cover_color.pdf` (39 pages)
- **B&W PDF:** `brown_bear_find_cover_bw.pdf` (39 pages)
- **Location:** `/samples/brown_bear/find_cover/`

---

## Configuration Files

### Main Product Config
`/config/find_cover_config.json` - All measurements, sizes, colors, and layout parameters

### Theme-Specific Config
`/config/brown_bear_find_cover.json` - Icon names, paths, metadata, and pack code (BB03)

### Design Specification
`/docs/find_cover_design_spec.md` - Complete design documentation

---

## Creating New Themes

1. **Prepare 12 Icons** (PNG, transparent background, 300 DPI)
2. **Create Theme Config** (Copy brown_bear_find_cover.json)
3. **Update Generator** (Point to new config)
4. **Generate PDFs** (Run generator → 39 pages created)

---

## Design Philosophy

- **SPED-Friendly:** Clean, predictable layouts with high contrast
- **Progressive Difficulty:** Builds from errorless learning to mastery
- **Professional Quality:** 300 DPI, color-coded, lamination-ready

---

## Version History

- **v2.2** - Optimized storage labels (icon size: 0.455", positioned lower)
- **v2.0** - Expanded to all 12 Brown Bear icons
- **v1.0** - Initial design

---

## Credits

**Product:** Find and Cover | **Studio:** Small Wins Studio | **Year:** 2025  
**Icons:** PCS® symbols used with active PCS Maker Personal License
