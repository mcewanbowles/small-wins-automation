# Matching Product Specification Template

## Product Overview
- **Product Name:** [Product Name] Matching Activity
- **Theme:** [Theme Name] (e.g., Brown Bear, Polar Bear, etc.)
- **Pack Code:** [Code] (e.g., BB03)
- **Target Audience:** Special education students (SPED-friendly)
- **Levels:** 4 (Errorless, Easy, Medium, Hard)

---

## Page Structure

### General Layout
- **Orientation:** Portrait (8.5" × 11")
- **Page Border:** Light blue (#A0C4E8), 3px, 0.25" from edge
- **Accent Stripe:** Level-specific color, 1.0" tall, 0.08" from top border
- **Fonts:** Comic Sans MS (with Helvetica fallback)

### Title Block
- **Title:** "Matching" (36pt, centered on stripe)
- **Subtitle:** "[Theme Name]" (28pt, centered on stripe)
- **Spacing:** 30px between title and subtitle
- **Positioning:** Both centered within accent stripe with padding from edges

### Accent Stripe Colors (Level-Based)
- **Level 1:** Orange #F4A259 (Errorless/Beginner)
- **Level 2:** Blue #4A90E2 (Easy)
- **Level 3:** Green #7BC47F (Medium)
- **Level 4:** Purple #9B59B6 (Hard)
- **BW Mode:** Convert to grayscale using hex_to_grayscale()

---

## Activity Pages

### Target Box (Reference Image)
- **Size:** 0.72" × 0.72"
- **Border:** Navy #1E3A5F, 4px
- **Position:** Centered, 0.08" below instruction line
- **Rounded Corners:** 0.12" radius
- **Shadow:** 6% opacity, simulated with layers

### Instruction Line
- **Text:** "Match the [Icon Name]"
- **Font:** Comic Sans MS, 14pt
- **Position:** Below subtitle, above target box

### Matching Boxes (Left Column)
- **Size:** 1.28" × 1.28"
- **Border:** Navy #1E3A5F, 3.5px
- **Rounded Corners:** 0.12" radius
- **Rows:** 5 boxes vertically
- **Spacing:** 0.16" between rows
- **Start Position:** 0.2" below target box
- **Icon Fill:** 97% of box (minimal padding)

### Velcro Boxes (Right Column)
- **Size:** 1.28" × 1.28" (same as matching boxes)
- **Fill:** Light grey #E8E8E8
- **Border:** Purple #6B5BE2, 3.5px
- **Rounded Corners:** 0.12" radius
- **Velcro Dot:** 0.3" diameter, centered
  - Fill: #CCCCCC
  - Outline: #999999

### Column Layout
- **Gap:** 1.45" between left and right columns
- **Alignment:** Both columns centered on page

---

## Level Logic

### Level 1 - Errorless (5 targets, 0 distractors)
- All 5 boxes show the target image
- **Watermark:** 25% opacity, 75% of box size, centered
- Student places 5 matching pieces

### Level 2 - Easy (4 targets, 1 distractor)
- 4 boxes show target, 1 shows different image
- No watermarks
- Student places 4 matching pieces

### Level 3 - Medium (3 targets, 2 distractors)
- 3 boxes show target, 2 show different images
- No watermarks
- Student places 3 matching pieces

### Level 4 - Hard (1 target, 4 distractors)
- 1 box shows target, 4 show different images
- No watermarks
- Student places 1 matching piece

---

## Cutout Pages

### Layout
- **Pages per Level:** 2 pages (60 pieces total)
- **Page 1:** First 6 icons, 5 copies each = 30 pieces
- **Page 2:** Last 6 icons, 5 copies each = 30 pieces
- **Grid:** 6 columns × 5 rows per page

### Box Specifications
- **Size:** 1.28" × 1.28" (matches activity boxes)
- **Border:** 3pt (0.042")
- **Spacing:** Minimal (boxes touch for guillotine cutting)
- **Rounded Corners:** 0.12" radius
- **Icon Fill:** 97% of box

### Title Block
- **Title:** "Cut Out Matching Pieces" (36pt, centered)
- **Subtitle:** "[Theme Name]" (28pt, centered)
- **Stripe Color:** Level-specific (same as activity pages)

---

## Storage Labels

### Layout
- **Grid:** 3 columns × 4 rows = 12 boxes (one per icon)
- **Box Size:** Rectangular (approx. 2.5" × 2.2")

### Box Design
- **Background:** Pale blue #E3F2FD
- **Border:** Medium blue #90CAF9, 2pt
- **Rounded Corners:** 0.15" radius

### Content per Box
1. **Title:** "Matching" (18pt, dark blue #1976D2)
2. **Subtitle:** "[Theme Name] BB[XX]" (14pt, dark blue)
3. **Level:** "Level X" (16pt bold, dark blue)
4. **Icon Image:** 0.6" centered (y=0.35")
5. **Icon Name:** Below image (12pt, black, y=0.18" below icon)

### Title Block
- **Title:** "Storage Labels" (36pt, centered)
- **Stripe Color:** Level-specific

---

## Footer

### Format (2 lines)
- **Line 1:** "Matching – Level X | [PACK_CODE]" (9pt, centered)
- **Line 2:** "© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License." (9pt, light grey #999999)
- **Position:** 0.3" from bottom margin

---

## PDF Structure

### Each Level Package (15 pages)
1. **Activity Pages:** 12 pages (one per icon, all 12 icons)
2. **Cutout Pages:** 2 pages (60 matching pieces total)
3. **Storage Labels:** 1 page (12 labeled boxes)

### Complete Product (60 pages)
- Level 1: Pages 1-15
- Level 2: Pages 16-30
- Level 3: Pages 31-45
- Level 4: Pages 46-60

### Output Files
- `[theme]_matching_color.pdf` (full color)
- `[theme]_matching_bw.pdf` (grayscale)

---

## Icon Requirements

### Source Directory
- `/assets/themes/[theme]/icons/`
- All icons as high-resolution PNG files

### Icon List (12 required)
1. [Icon 1 Name]
2. [Icon 2 Name]
3. [Icon 3 Name]
4. [Icon 4 Name]
5. [Icon 5 Name]
6. [Icon 6 Name]
7. [Icon 7 Name]
8. [Icon 8 Name]
9. [Icon 9 Name]
10. [Icon 10 Name]
11. [Icon 11 Name]
12. [Icon 12 Name]

### Icon Guidelines
- **Format:** PNG with transparency
- **Size:** Minimum 500×500px (will be scaled)
- **Style:** Consistent across all icons
- **Background:** Transparent
- **Content:** Clear, recognizable images suitable for SPED learners

---

## Color Palette

### Level Colors
```
Level 1: #F4A259 (Orange - Beginner)
Level 2: #4A90E2 (Blue - Easy)
Level 3: #7BC47F (Green - Medium)
Level 4: #9B59B6 (Purple - Hard)
```

### Standard Colors
```
Page Border: #A0C4E8 (Light Blue)
Navy Border: #1E3A5F (Matching/Target Boxes)
Purple Border: #6B5BE2 (Velcro Boxes)
Light Grey Fill: #E8E8E8 (Velcro Box Background)
Velcro Dot Fill: #CCCCCC
Velcro Dot Outline: #999999
```

### Storage Label Colors
```
Background: #E3F2FD (Pale Blue)
Border: #90CAF9 (Medium Blue)
Text: #1976D2 (Dark Blue)
```

---

## Black & White Mode

### Conversion Rules
- All colors convert to grayscale using `hex_to_grayscale()`
- Icons enhanced for printing using `enhance_for_printing()`
- Borders remain visible with high contrast
- No black-on-black issues

---

## File Naming Convention

### Output Files
- `[theme_name]_matching_color.pdf`
- `[theme_name]_matching_bw.pdf`

### Examples
- `brown_bear_matching_color.pdf`
- `polar_bear_matching_color.pdf`
- `panda_matching_color.pdf`

---

## Notes

- All measurements in inches unless specified
- Comic Sans MS font provides friendly, accessible appearance
- Level-based colors enable quick visual identification for teachers
- Guillotine-friendly cutouts (boxes touch) for easy classroom prep
- Professional storage labels help organize materials
- Each level can be sold separately or as complete package
