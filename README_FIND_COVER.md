# Find and Cover Product - Brown Bear Theme

## Overview

The **Find and Cover** activity is a visual scanning and discrimination exercise where students find and cover matching images in a 4×4 grid. This product uses the same professional design system as the Matching product.

## Product Features

### Design Elements

- **Light blue page borders** (#A0C4E8) for consistent branding
- **Level-based color coding** for easy classroom organization:
  - Level 1: Orange #F4A259 (Beginner)
  - Level 2: Blue #4A90E2 (Intermediate)  
  - Level 3: Green #7BC47F (Advanced)
- **Comic Sans MS fonts** for readability
- **Professional storage labels** with pale blue design
- **Both COLOR and BW versions** for printing flexibility

### Structure (15 Pages)

**Level 1 - Beginner (Pages 1-4):**
- Target + 1 distractor only
- Target appears 10 times, distractor 6 times
- 2-choice visual scanning (1 vs 1)
- Easiest difficulty - builds confidence!

**Level 2 - Intermediate (Pages 5-8):**
- Target + 2 distractors
- Target appears 8 times, each distractor 4 times
- 3-choice visual scanning (1 vs 2)
- Moderate challenge

**Level 3 - Advanced (Pages 9-12):**
- Target + 3 distractors (all 4 images)
- Target appears 6 times, distractors share remaining 10
- 4-choice visual scanning (1 vs 3)
- Maximum challenge!

**Storage Labels (Pages 13-15):**
- One page per level
- Folder-style labels (2×2 grid with 4 icons)
- Professional pale blue background
- Includes pack code BB03
- Teacher provides chips/counters

## Icons Used

Four Brown Bear theme icons:
1. **Children** - Group of children
2. **Goldfish** - Swimming goldfish
3. **Eyes** - Pair of eyes (renamed from "See")
4. **Teacher** - Teacher figure

## Grid System

- **4×4 grid** = 16 cells per page
- **Steel blue gridlines** inside (#5B7AA0)
- **Navy border** around entire grid (#1E3A5F)
- **Randomized placement** on each page
- **Varying target/distractor ratios** by level

## How to Use

### For Teachers:

1. **Print** the appropriate level for your student
2. **Laminate** for durability
3. Student sees **target** in box at top of page
4. Student **finds** all matching images in 4×4 grid
5. Student **covers** with chips, counters, or mini erasers
6. Student **counts** covered items to self-check

### Materials Needed:

- Printed and laminated activity sheets
- Chips, counters, mini erasers, or bingo daubers for covering
- Storage folders labeled with provided labels

## Skills Practiced

- ✅ **Visual scanning** - Searching systematically
- ✅ **Visual discrimination** - Distinguishing similar images
- ✅ **Attention to detail** - Finding all instances
- ✅ **Focus & concentration** - Completing the task
- ✅ **Counting** - Self-checking answers

## Perfect For

- Special education classrooms
- Autism programs
- Speech therapy
- Early childhood education
- Work task boxes
- Independent work stations

## Generation

### To Generate PDFs:

```bash
python generate_find_cover_constitution.py
```

### Outputs:

- `brown_bear_find_cover_color.pdf` - 2.8MB, 15 pages
- `brown_bear_find_cover_bw.pdf` - 1.0MB, 15 pages

### Output Location:

```
/samples/brown_bear/find_cover/
```

## Technical Details

### Generator:

**File:** `generate_find_cover_constitution.py`  
**Size:** 17.6KB  
**Dependencies:** reportlab, pillow  

### Page Dimensions:

- Letter size (8.5" × 11")
- 0.25" outer margins
- 1.0" accent stripe height

### Box Specifications:

- Target box: 0.9" square
- Grid cells: ~1.65" square (calculated to fit)
- Storage label boxes: 2.6" × 1.9"

### Colors:

**Color Mode:**
- Page border: #A0C4E8 (light blue)
- Navy: #1E3A5F (boxes)
- Steel blue: #5B7AA0 (gridlines)
- Level 1 stripe: #F4A259 (orange)
- Level 2 stripe: #4A90E2 (blue)
- Level 3 stripe: #7BC47F (green)
- Storage labels: #E3F2FD background, #90CAF9 borders

**BW Mode:**
- All colors converted to appropriate grayscale values
- Maintains contrast and readability

## Customization

### To Create for Another Theme:

1. Update the `load_brown_bear_icons()` function
2. Change the icons directory path
3. Update icon filenames
4. Update subtitle text
5. Update pack code if needed
6. Run the generator

### Example:

```python
def load_polar_bear_icons():
    icons_dir = "/path/to/polar_bear/icons"
    icon_files = {
        "Polar Bear": "polar_bear.png",
        "Seal": "seal.png",
        "Walrus": "walrus.png",
        "Penguin": "penguin.png"
    }
    # ... rest of loading logic
```

## File Structure

```
samples/brown_bear/find_cover/
├── brown_bear_find_cover_color.pdf  (2.8MB, 15 pages)
└── brown_bear_find_cover_bw.pdf     (1.0MB, 15 pages)
```

## Copyright

© 2025 Small Wins Studio  
PCS® symbols used with active PCS Maker Personal License

## Related Products

- **Matching Product** - Same design system, different activity
- See `README_MATCHING_SYSTEM.md` for details

## Support

For questions or issues with generation:
1. Check that all icon files exist in the correct directory
2. Verify reportlab and pillow are installed
3. Check console output for specific error messages
4. Ensure output directory is writable

## Version History

- **v1.0** (Feb 2026) - Initial release
  - 3 difficulty levels
  - 15-page structure
  - Matching design system
  - Brown Bear theme
