# Small Wins Studio Design System
## Matching Activity Products

---

## Overview

This design system defines the visual standards for all Small Wins Studio Matching Activity products. Consistency across themes ensures a professional appearance and helps teachers recognize and organize materials.

---

## Typography

### Fonts

**Primary Font:** Comic Sans MS
- Friendly, approachable appearance
- Highly legible for special education students
- Available on most systems

**Fallback:** Helvetica
- Used when Comic Sans MS is unavailable
- Similar readability and friendliness

### Font Sizes

| Element | Size | Weight | Use |
|---------|------|--------|-----|
| Page Title | 36pt | Bold | "Matching", "Cut Out Matching Pieces", "Storage Labels" |
| Page Subtitle | 28pt | Regular | Theme name (e.g., "Brown Bear") |
| Instruction Text | 14pt | Regular | "Match the [Icon Name]" |
| Storage Box Title | 18pt | Bold | "Matching" in storage label boxes |
| Storage Box Subtitle | 14pt | Regular | Theme and pack code |
| Storage Box Level | 16pt | Bold | "Level X" |
| Storage Box Icon Name | 12pt | Regular | Icon name below image |
| Footer Line 1 | 9pt | Regular | Level and pack code |
| Footer Line 2 | 9pt | Regular | Copyright notice |

---

## Color Palette

### Level-Based Colors

Each difficulty level has a distinct color for quick visual identification:

```
Level 1 (Errorless)  : #F4A259  [Orange]  - Warm, beginner-friendly
Level 2 (Easy)       : #4A90E2  [Blue]    - Calm, encouraging
Level 3 (Medium)     : #7BC47F  [Green]   - Growth, progress
Level 4 (Hard)       : #9B59B6  [Purple]  - Mastery, achievement
```

### Standard Interface Colors

```
Page Border          : #A0C4E8  [Light Blue]
Navy Border          : #1E3A5F  [Navy]       - Matching/Target boxes
Purple Border        : #6B5BE2  [Purple]     - Velcro boxes
Light Grey Fill      : #E8E8E8  [Light Grey] - Velcro box background
Velcro Dot Fill      : #CCCCCC  [Grey]
Velcro Dot Outline   : #999999  [Dark Grey]
```

### Storage Label Colors

```
Background           : #E3F2FD  [Pale Blue]
Border               : #90CAF9  [Medium Blue]
Title Text           : #1976D2  [Dark Blue]
Body Text            : #000000  [Black]
```

### Grayscale Conversion (BW Mode)

All colors convert to appropriate grayscale values:
- Maintains contrast and hierarchy
- Uses `hex_to_grayscale()` function
- Icons enhanced with `enhance_for_printing()`

---

## Layout

### Page Dimensions
- **Size:** 8.5" × 11" (US Letter)
- **Orientation:** Portrait
- **Margins:** 0.25" from edge to page border

### Page Border
- **Color:** Light Blue (#A0C4E8)
- **Width:** 3px
- **Style:** Solid
- **Position:** 0.25" from page edge
- **Rounded Corners:** None

### Accent Stripe
- **Height:** 1.0"
- **Position:** 0.08" from top border
- **Color:** Level-dependent (see Level Colors)
- **Rounded Corners:** Matches page border curve
- **Width:** Inside page border

### Title Block
- **Title:** Centered, 36pt, within stripe
- **Subtitle:** Centered, 28pt, within stripe
- **Spacing:** 30px between title and subtitle
- **Padding:** Both have space from stripe edges

---

## Activity Page Components

### Target Box
```
Size:              0.72" × 0.72"
Border:            Navy #1E3A5F, 4px
Position:          Centered, 0.08" below instruction
Rounded Corners:   0.12" radius
Shadow:            6% opacity (simulated)
Background:        White
Icon Size:         Fills ~90% of box
```

### Matching Boxes (Left Column)
```
Size:              1.28" × 1.28"
Border:            Navy #1E3A5F, 3.5px
Rounded Corners:   0.12" radius
Rows:              5 boxes
Spacing:           0.16" between rows
Start:             0.2" below target
Icon Fill:         97% of box
Background:        White
```

### Velcro Boxes (Right Column)
```
Size:              1.28" × 1.28" (matches matching boxes)
Fill:              Light Grey #E8E8E8
Border:            Purple #6B5BE2, 3.5px
Rounded Corners:   0.12" radius
Velcro Dot:        0.3" diameter, centered
  - Fill:          #CCCCCC
  - Outline:       #999999, 1px
```

### Column Layout
```
Gap:               1.45" between columns
Alignment:         Both columns centered on page
```

---

## Cutout Page Components

### Cutout Boxes
```
Size:              1.28" × 1.28" (matches activity boxes)
Border:            3pt (0.042")
Spacing:           Minimal (boxes touch)
Rounded Corners:   0.12" radius
Grid:              6 columns × 5 rows = 30 boxes
Pages:             2 per level (60 pieces total)
Icon Fill:         97% of box
Background:        White
```

### Layout
```
Page 1:            First 6 icons, 5 copies each
Page 2:            Last 6 icons, 5 copies each
Title:             "Cut Out Matching Pieces"
Subtitle:          Theme name only
```

---

## Storage Label Components

### Label Boxes
```
Size:              ~2.5" × 2.2" (rectangular)
Background:        Pale Blue #E3F2FD
Border:            Medium Blue #90CAF9, 2pt
Rounded Corners:   0.15" radius
Grid:              3 columns × 4 rows = 12 boxes
```

### Box Content
```
Title:             "Matching" (18pt, Dark Blue)
Subtitle:          "[Theme] [Code]" (14pt, Dark Blue)
Level:             "Level X" (16pt bold, Dark Blue)
Icon:              0.6" centered, y=0.35"
Icon Name:         12pt, Black, 0.18" below icon
```

---

## Spacing System

### Vertical Spacing
```
Page top to stripe:        0.08"
Title to subtitle:         30px
Subtitle to instruction:   Variable (auto-calculated)
Instruction to target:     0.08"
Target to matching boxes:  0.2"
Between matching rows:     0.16"
Bottom box to footer:      ≥0.3"
```

### Horizontal Spacing
```
Page margin:               0.25"
Column gap:                1.45"
Cutout box spacing:        Minimal (touching)
Storage box padding:       0.1" internal
```

---

## Visual Hierarchy

### Importance Levels

1. **Primary:** Page title (largest, boldest)
2. **Secondary:** Subtitle and level indicators
3. **Tertiary:** Instructions and labels
4. **Supporting:** Footer and metadata

### Contrast

- High contrast between text and backgrounds
- Navy borders provide visual containment
- Level colors provide organizational cues
- Grayscale mode maintains hierarchy

---

## Accessibility

### SPED-Friendly Design Principles

1. **Clear Visual Hierarchy:** Obvious relationship between elements
2. **High Contrast:** Easy to distinguish elements
3. **Consistent Layout:** Predictable structure across pages
4. **Friendly Fonts:** Comic Sans MS for readability
5. **Adequate Spacing:** No crowding or overlap
6. **Color + Shape:** Not relying on color alone
7. **Rounded Corners:** Softer, less intimidating
8. **Large Icons:** Easy to recognize and manipulate

### Print Considerations

- Icons enhanced for black & white printing
- Borders remain visible in grayscale
- No fine details that might not print well
- Guillotine-friendly cutouts (boxes touch)

---

## Components Library

### Borders
```
Thin:    1-2px (fine details)
Medium:  3-4px (standard boxes)
Thick:   4-5px (emphasis)
```

### Rounded Corners
```
Small:   0.1" (tight curves)
Medium:  0.12" (standard boxes)
Large:   0.15" (storage labels)
```

### Shadows
```
Soft:    5-8% opacity (subtle depth)
None:    Most elements (flat design)
```

---

## Grid System

### Activity Page Grid
```
Columns:    2 (left: matching, right: velcro)
Rows:       5 (matching boxes)
Gutters:    1.45" horizontal, 0.16" vertical
```

### Cutout Page Grid
```
Columns:    6 (icon columns)
Rows:       5 (copies per icon)
Gutters:    Minimal (boxes touch)
```

### Storage Labels Grid
```
Columns:    3 (label boxes)
Rows:       4 (12 boxes total)
Gutters:    0.2" horizontal, 0.2" vertical
```

---

## State Variations

### Color Mode (Default)
- Full color as specified
- Level-based accent stripe colors
- All colors vivid and distinct

### Black & White Mode
- Grayscale conversion of all colors
- Icons enhanced for printing
- Maintains visual hierarchy
- All borders remain visible

---

## Consistency Checklist

When creating new themes, verify:

- ✅ Comic Sans MS font used throughout
- ✅ Level colors match specification
- ✅ Box sizes are correct (1.28" activity, 0.72" target)
- ✅ Spacing follows the system
- ✅ Rounded corners are consistent (0.12")
- ✅ Footer format is correct
- ✅ Title and subtitle are centered in stripe
- ✅ BW mode converts properly
- ✅ All icons are high quality
- ✅ Storage labels follow template

---

## Version History

- **v1.0** (Feb 2026): Initial design system based on Brown Bear Matching

---

## Design Tokens

For developers implementing the design system:

```javascript
// Colors
const COLORS = {
  level1: '#F4A259',
  level2: '#4A90E2',
  level3: '#7BC47F',
  level4: '#9B59B6',
  pageBorder: '#A0C4E8',
  navyBorder: '#1E3A5F',
  purpleBorder: '#6B5BE2',
  lightGrey: '#E8E8E8',
  paleBlueBg: '#E3F2FD',
  mediumBlueBorder: '#90CAF9',
  darkBlueText: '#1976D2'
};

// Typography
const FONTS = {
  primary: 'Comic Sans MS',
  fallback: 'Helvetica',
  sizes: {
    title: 36,
    subtitle: 28,
    instruction: 14,
    footer: 9
  }
};

// Spacing
const SPACING = {
  titleSubtitle: 30,
  rowGap: 0.16,  // inches
  columnGap: 1.45, // inches
  pagePadding: 0.25  // inches
};

// Sizes
const SIZES = {
  activityBox: 1.28,  // inches
  targetBox: 0.72,    // inches
  velcroDot: 0.3,     // inches
  borderRadius: 0.12  // inches
};
```

---

© 2025 Small Wins Studio
