# Find and Cover - Design Specification

## Product Overview

**Find and Cover** is a visual scanning and discrimination activity for special education. Students find a target icon in a 4×4 grid and cover all matching instances with chips or counters.

### Product Structure
- **39 Pages Total**
- **3 Difficulty Levels** (13 pages each)
  - Level 1 (Orange accent stripe)
  - Level 2 (Blue accent stripe)
  - Level 3 (Green accent stripe)
- **12 Activities per Level** (one for each icon)
- **1 Storage Labels Page per Level**

---

## Page Dimensions and Layout

### Page Setup
- **Page Size:** 8.5" × 11" (US Letter)
- **Orientation:** Portrait
- **DPI:** 300 (high resolution for print)

### Page Borders
- **Border Color:** Light blue (#A0C4E8)
- **Border Style:** Rounded rectangle
- **Border Width:** 3px
- **Corner Radius:** 0.25"
- **Margin from Edge:** 0.25"

---

## Accent Stripe (Header)

### Position and Size
- **Y Position:** 0.35" from top of page
- **Height:** 0.8"
- **Width:** Full page width (within borders)

### Colors by Level
- **Level 1:** Orange #F4A259 (warm, friendly)
- **Level 2:** Blue #4A90E2 (calm, progressive)
- **Level 3:** Green #7BC47F (growth, mastery)

### Typography
- **Title Font:** Comic Sans MS (friendly, educational)
- **Title Size:** 36pt
- **Title Text:** "Find and Cover"
- **Title Color:** White (for good contrast)

- **Subtitle Font:** Comic Sans MS
- **Subtitle Size:** 28pt
- **Subtitle Text:** "Brown Bear" (or theme name)
- **Subtitle Color:** White

### Positioning
- Title and subtitle centered on accent stripe
- Title: 5px offset from center
- Subtitle: 30px below title

---

## Activity Pages

### Instruction Line
- **Y Position:** 1.52" from top
- **Font:** Comic Sans MS
- **Size:** 24pt
- **Color:** Navy #2B4C7E
- **Text:** "Find the [Icon Name]"
- **Alignment:** Centered

### Target Box
- **Y Position:** 2.57" from top
- **Size:** 1.8" × 1.8"
- **Border:** Navy #2B4C7E, 3px
- **Corner Radius:** 0.1"
- **Alignment:** Centered horizontally
- **Icon Size:** Fit within box with 8px padding
- **Icon:** Target icon for the activity

### Activity Grid
- **Y Position:** 4.6" from top
- **Grid Size:** 4×4 (16 cells)
- **Cell Size:** Variable (fits available space)
- **Gridlines:** Steel blue #5B7AA0, 2px
- **No External Border:** Only internal gridlines
- **Icon Size per Cell:** Fit with 8px padding

### Grid Content by Level
**Level 1 (1 vs 1):**
- Target appears: 10 times
- Distractor 1 appears: 6 times

**Level 2 (1 vs 2):**
- Target appears: 8 times
- Distractor 1 appears: 4 times
- Distractor 2 appears: 4 times

**Level 3 (1 vs 3):**
- Target appears: 6 times
- Remaining 10 cells: Distributed among 3 distractors

### Footer
**Line 1:**
- Font: Arial/Sans-serif, 10-11pt
- Text: `[Pack Code] | [Theme Name] | Level X | Page N/Total`

**Line 2:**
- Font: Arial/Sans-serif, 9pt
- Color: Light grey #999999
- Text: `© 2025 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License`

---

## Storage Labels Pages

### Page Layout
- **Accent Stripe:** Same as activity pages (0.35" from top)
- **Title:** "Storage Labels"
- **Subtitle:** "Find and Cover - [Theme] - Level X"
- **Label Grid Start:** 3.5" from top

### Label Grid
- **Grid:** 3 columns × 4 rows = 12 labels
- **Labels per Page:** 12 (one for each icon/activity)
- **Label Box Size:** 1.8" × 1.5"
- **Spacing:** 0.2" between boxes

### Individual Label Box
**Background:**
- Color: Pale blue #E3F2FD
- Border: Medium blue #90CAF9, 2px
- Corner Radius: 0.1"

**Content Layout:**
1. **Title Area (Top):**
   - Text: "Find and Cover"
   - Font: Arial Bold, 10pt
   - Position: 0.3" from top of box

2. **Pack Info:**
   - Text: "[Theme] [Pack Code]"
   - Font: Arial, 8pt
   - Position: Below title

3. **Level Info:**
   - Text: "Level X"
   - Font: Arial, 8pt
   - Position: Below pack info

4. **Icon:**
   - **Size:** 0.455" × 0.455"
   - **Position:** 0.35" from bottom of box
   - **Background:** Transparent (PNG with alpha)
   - **Mask:** 'auto' (preserves transparency)
   - **Centered:** Horizontally in box

5. **Icon Name:**
   - Text: Icon name (e.g., "Black Sheep")
   - Font: Arial Bold, 11pt
   - Position: 0.15" from bottom of box
   - Centered horizontally

### Instruction Line
- **Y Position:** 9.5" from top (near footer)
- **Font:** Arial, 10pt
- **Text:** "Cut out labels and attach to folders. Teacher provides chips/counters for covering."
- **Alignment:** Centered

---

## Icon Specifications

### Requirements
- **Format:** PNG
- **Background:** Transparent (alpha channel)
- **Resolution:** High (at least 300 DPI)
- **Style:** Clean, simple, recognizable
- **Color:** Full color (PCS symbols)

### Icon Set (12 Required)
1. Black Sheep
2. Blue Horse
3. Brown Bear
4. Green Frog
5. Purple Cat
6. Red Bird
7. White Dog
8. Yellow Duck
9. Children
10. Goldfish
11. Eyes (See)
12. Teacher

### Storage Locations
- **Path:** `/assets/[theme]/icons/`
- **Naming:** Descriptive (e.g., `Black Sheep.png`)
- **Case:** As shown in files (preserve spaces and capitals)

---

## Color Palette

### Level Colors (Accent Stripes)
```
Level 1 - Orange: #F4A259
Level 2 - Blue:   #4A90E2
Level 3 - Green:  #7BC47F
```

### UI Colors
```
Navy:        #2B4C7E (borders, titles)
Steel Blue:  #5B7AA0 (gridlines)
Light Blue:  #A0C4E8 (page borders)
Pale Blue:   #E3F2FD (label backgrounds)
Medium Blue: #90CAF9 (label borders)
```

### Grayscale Conversion
For BW versions, all colors convert to appropriate grayscale values maintaining contrast.

---

## Typography

### Primary Font
- **Family:** Comic Sans MS (friendly, educational)
- **Fallback:** DejaVu Sans (for Linux systems)

### Font Sizes
- Title: 36pt
- Subtitle: 28pt
- Instruction: 24pt
- Footer Line 1: 10-11pt
- Footer Line 2: 9pt
- Storage Label Title: 10pt
- Storage Label Info: 8pt
- Storage Label Icon Name: 11pt (Bold)

---

## Black & White Version

### Conversion Rules
- All colors convert to grayscale
- Accent stripes: Light grey
- Borders: Dark grey
- Text: Black
- Gridlines: Medium grey
- Icons: Grayscale (if color) or unchanged (if already grayscale)
- Storage labels: Light grey background, darker grey borders

---

## File Naming Conventions

### PDFs
- **Color:** `[theme]_find_cover_color.pdf`
- **BW:** `[theme]_find_cover_bw.pdf`

### Examples
- `brown_bear_find_cover_color.pdf`
- `brown_bear_find_cover_bw.pdf`

---

## Pack Code System

### Format
`[Theme Initials][Product Number]`

### Examples
- BB03 = Brown Bear, Find and Cover
- BB01 = Brown Bear, WH Questions
- BB02 = Brown Bear, Matching
- BB04 = Brown Bear, Sentence Strips

---

## Design Iterations and Rationale

### Storage Label Icon Size Evolution

**Version 1:** 0.8" - Too large, covered text  
**Version 2:** 0.35" - Too small, hard to see  
**Version 3:** 0.455" - Increased 30%, better visibility  
**Version 4:** 0.91" - Doubled (100% bigger), covered text again  
**Final:** 0.455" - Perfect balance ✓

**Rationale:**
- 0.455" allows all text to be readable
- Icon positioned low enough to not cover title/pack info
- Icon large enough to be easily identifiable
- Maintains professional appearance

### Icon Position
- Final position: 0.35" from bottom of label box
- Keeps title, pack code, and level info fully visible
- Centers icon in available vertical space
- Leaves room for icon name below

---

## Accessibility Considerations

### Visual Design
- High contrast text and backgrounds
- Large, clear fonts (Comic Sans MS for readability)
- Simple, uncluttered layouts
- Consistent spacing and alignment

### SPED-Friendly Features
- Clean, predictable structure
- Progressive difficulty levels (Level 1 with minimal distractors for scaffolding)
- Progressive difficulty levels
- Realistic, recognizable icons
- Transparent backgrounds don't interfere with recognition

---

## Production Notes

### PDF Generation
- Use ReportLab for Python PDF generation
- 300 DPI for print quality
- Letter size (8.5" × 11")
- Both color and grayscale versions required

### Print Recommendations
- Laminate for durability
- Use cardstock for sturdiness
- Color version preferred for visual appeal
- BW version for budget-friendly printing

---

## Version History

- **v1.0** - Initial design with 4 icons
- **v2.0** - Expanded to 12 icons (all Brown Bear icons)
- **v2.1** - Storage label icon size optimization
- **v2.2** - Final layout with readable text

---

## Contact & Credits

**Product:** Find and Cover  
**Studio:** Small Wins Studio  
**License:** PCS® symbols used with active PCS Maker Personal License  
**Year:** 2025  
