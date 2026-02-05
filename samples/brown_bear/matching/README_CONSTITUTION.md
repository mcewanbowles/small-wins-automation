# Brown Bear Matching Cards - Design Constitution Compliant

This folder contains the complete Brown Bear Matching Cards product following the **Small Wins Studio Design Constitution v1.0** (`.github/copilot-instructions.md`).

## Files Generated

**Latest - Design Constitution Compliant:**
1. **brown_bear_matching_color.pdf** (742 KB, 50 pages) ✅ **DESIGN CONSTITUTION COMPLIANT**
2. **brown_bear_matching_bw.pdf** (742 KB, 50 pages) ✅ **DESIGN CONSTITUTION COMPLIANT**

**Previous Versions (deprecated):**
- ~~brown_bear_matching_velcro_color.pdf~~ (deprecated - non-compliant layout)
- ~~brown_bear_matching_velcro_bw.pdf~~ (deprecated - non-compliant layout)

## Design Constitution Compliance

### Global Page Structure (Section 2)

**2.1 Border:**
- ✅ Thin rounded rectangle
- ✅ 3px stroke
- ✅ 0.25" margin from page edge

**2.2 Accent Stripe:**
- ✅ Height: 0.35"
- ✅ Positioned at top of page
- ✅ Color: Warm orange (Matching product type)
- ✅ Full width

**2.3 Title + Subtitle:**
- ✅ Sitting ON the accent stripe, aligned left
- ✅ Title: "Matching – Level X" (22pt Helvetica-Bold)
- ✅ Subtitle: "Brown Bear Pack (BB03)" (16pt Helvetica)

**2.4 Footer (Two Lines):**
- ✅ Line 1: "BB03 | Brown Bear | Level X | Page N/Total" (10pt Helvetica-Bold)
- ✅ Line 2: "© 2025 Small Wins Studio • PCS® symbols..." (9pt Helvetica, light grey #999999)

### Global Measurements & Layout (Section 6)

**Page Margins:**
- ✅ 0.25" outer margin
- ✅ 0.5" top margin before content

**Activity Boxes:**
- ✅ Width: 1.0"
- ✅ Height: 1.0"
- ✅ Rounded corners: radius 0.1-0.15"
- ✅ Vertical spacing: 0.15"

**Target Image:**
- ✅ Width: 1.8"
- ✅ Height: 1.8"
- ✅ Centered

**Velcro Dot:**
- ✅ 0.35" diameter (middle of 0.3-0.4" range)
- ✅ Centered in matching box
- ✅ Light grey fill (#E6E6E6)
- ✅ Thin outline (1-2px medium grey)
- ✅ Optional tiny "velcro" text (6-7pt)

### Level Logic (Section 7.1)

- ✅ Level 1: 5 targets, 0 distractors (errorless learning)
- ✅ Level 2: 4 targets, 1 distractor
- ✅ Level 3: 3 targets, 2 distractors
- ✅ Level 4: 1 target, 4 distractors

### Level 1 Watermark Logic (Section 8)

- ✅ Matching boxes contain transparent watermark of target icon
- ✅ Opacity: 25% (within 20-30% range)
- ✅ Centered in box
- ✅ Velcro dot appears on top

### Cutout Pages (Section 9)

- ✅ Title: "Cutout Matching Pieces"
- ✅ Subtitle: "Brown Bear Pack (BB03)"
- ✅ 5-icon strips
- ✅ Strips touch (no gaps) for guillotine cutting
- ✅ 4×5 layout (20 icons per page)
- ✅ Rounded boxes
- ✅ Crisp icons
- ✅ Max icon size: 1.5" × 1.5"
- ✅ No watermarking on cutouts

### Storage Labels (Section 10)

- ✅ Title: "Storage Labels – Matching Pack"
- ✅ Subtitle: "Brown Bear Pack (BB03)"
- ✅ Clean 3-column vocabulary table
- ✅ Consistent font and spacing

### Naming Conventions (Section 11)

- ✅ snake_case filenames: `brown_bear_matching_color.pdf`, `brown_bear_matching_bw.pdf`
- ✅ Color version included
- ✅ Black & white version included
- ✅ Activity pages included
- ✅ Cutouts included
- ✅ Storage labels included

## Product Structure

### Total Pages: 50

**Matching Activity Pages: 48** (Pages 1-48)
- 12 icons × 4 difficulty levels = 48 pages

**Layout per Matching Page:**
```
┌─────────────────────────────────────────┐
│ ╔═══ Warm Orange Accent Stripe ═════╗  │  ← 0.35" height
│ ║ Matching – Level X                 ║  │  ← 22pt title ON stripe
│ ║ Brown Bear Pack (BB03)             ║  │  ← 16pt subtitle ON stripe
│ ║                                    ║  │
│ ║      ┌─────────────┐               ║  │
│ ║      │   TARGET    │               ║  │  ← 1.8" × 1.8"
│ ║      │  (1.8×1.8)  │               ║  │
│ ║      └─────────────┘               ║  │
│ ║                                    ║  │
│ ║  Row 1:  ┌────┐      ◯             ║  │  ← 1.0" box + 0.35" dot
│ ║          │IMG │     velcro         ║  │  ← Level 1: 25% watermark
│ ║          └────┘                    ║  │
│ ║  Row 2:  ┌────┐      ◯             ║  │
│ ║          │IMG │     velcro         ║  │
│ ║          └────┘                    ║  │
│ ║  Row 3:  ┌────┐      ◯             ║  │
│ ║          │IMG │     velcro         ║  │
│ ║          └────┘                    ║  │
│ ║  Row 4:  ┌────┐      ◯             ║  │
│ ║          │IMG │     velcro         ║  │
│ ║          └────┘                    ║  │
│ ║  Row 5:  ┌────┐      ◯             ║  │
│ ║          │IMG │     velcro         ║  │
│ ║          └────┘                    ║  │
│ ║                                    ║  │
│ ║  BB03 | Brown Bear | Level X |..  ║  │  ← 10pt Helvetica-Bold
│ ║  © 2025 Small Wins Studio • PCS®  ║  │  ← 9pt Helvetica #999999
│ ╚════════════════════════════════════╝  │  ← 3px rounded border
└─────────────────────────────────────────┘  ← 0.25" margin
```

**Cutout Page: 1** (Page 49)
- 20 icons in 4×5 layout (5 icons per strip, 4 strips touching)
- Max icon size: 1.5" × 1.5"
- Rounded boxes for cutting
- No watermarks

**Storage Label Page: 1** (Page 50)
- Product title and pack code
- 3-column vocabulary table with all 12 icon names

## Icon Processing

All 12 Brown Bear icons processed:
1. Black Sheep (Pages 1-4: Levels 1-4)
2. Blue Horse (Pages 5-8: Levels 1-4)
3. Brown Bear (Pages 9-12: Levels 1-4)
4. Green Frog (Pages 13-16: Levels 1-4)
5. Purple Cat (Pages 17-20: Levels 1-4)
6. Red Bird (Pages 21-24: Levels 1-4)
7. White Dog (Pages 25-28: Levels 1-4)
8. Yellow Duck (Pages 29-32: Levels 1-4)
9. Children (Pages 33-36: Levels 1-4)
10. Goldfish (Pages 37-40: Levels 1-4)
11. See (Pages 41-44: Levels 1-4)
12. Teacher (Pages 45-48: Levels 1-4)

## Differentiation Levels

### Level 1 - Errorless Learning (25% opacity watermark)
- 5 matching boxes, all with the target image
- 0 distractors
- Target icon watermark (25% opacity) in each matching box
- Velcro dot on top of watermark
- Perfect for emerging learners

### Level 2 - Minimal Challenge
- 4 matching boxes with target image
- 1 distractor (different icon)
- Students identify which 4 match the target

### Level 3 - Moderate Difficulty
- 3 matching boxes with target image
- 2 distractors (different icons)
- Increased cognitive load

### Level 4 - Maximum Challenge
- 1 matching box with target image
- 4 distractors (different icons)
- Requires careful visual discrimination

## Classroom Usage

### Teachers:
1. Print color or BW version (50 pages)
2. Laminate all pages
3. Cut out icons from page 49 (cutout page)
4. Attach velcro dots to grey circles on matching pages
5. Attach velcro dots to backs of cutout icons
6. Use storage label (page 50) to organize

### Students:
1. Look at target image at top of page
2. Find matching images in the 5 image boxes (left column)
3. Place cutout icon on corresponding velcro dot (right column)
4. Progress through Levels 1-4 for skill mastery

## Quality Assurance Checklist (Section 14)

- ✅ Border present (3px, rounded, 0.25" margin)
- ✅ Accent stripe present (0.35", warm orange)
- ✅ Title + subtitle present (ON stripe, correct fonts)
- ✅ Footer present (2 lines, correct typography)
- ✅ Crisp icons (full-resolution PNGs)
- ✅ Correct level logic (5-0, 4-1, 3-2, 1-4)
- ✅ Correct velcro dot (0.35" diameter, centered)
- ✅ Correct watermark (Level 1, 25% opacity)
- ✅ Correct spacing (0.15" between boxes)
- ✅ Correct page numbering (1-50)
- ✅ Correct pack code (BB03)
- ✅ Correct theme name (Brown Bear)
- ✅ Cutouts included (page 49)
- ✅ Storage labels included (page 50)
- ✅ Color + BW versions included

## Generator

This product was generated using:
- `generate_matching_constitution.py` - Design Constitution compliant generator
- Follows all standards in `.github/copilot-instructions.md`
- Icons loaded from `/assets/themes/brown_bear/icons/`
- Output to `/samples/brown_bear/matching/`

---

**Product Code:** BB03  
**Theme:** Brown Bear Brown Bear What Do You See?  
**Design Standard:** Small Wins Studio Design Constitution v1.0  
**Status:** ✅ PRODUCTION READY - FULLY COMPLIANT
