# Small Wins Studio - Design Constitution

This document defines the universal visual, structural, and accessibility standards for all Small Wins Studio resources. All generators must comply with these rules unless explicitly overridden for a specific product type.

---

## 1. Page Structure
- Page size: US Letter (8.5" x 11")
- Margins: 0.25" on all sides (outer border margin)
- Border: 3 px rounded rectangle, 0.1" corner radius
- Footer: always present, consistent across all products  
  Format: `{PACK_CODE} | {THEME} | Level {X} | Page {Y}/{TOTAL} @ 2025 Small Wins Studio. PCS symbols used with active PCS Maker Personal License.`

---

## 2. Title Block
- Title and subtitle sit inside an accent stripe.
- Accent stripe height: 0.35"
- Stripe must sit inside the border with rounded corners.
- **Accent stripe color: LEVEL-SPECIFIC** (see Level Color Coding below)
- Title: "Matching - Level X: {Level Name}" (white text, 22pt Helvetica-Bold)
- Subtitle: "{Theme} Pack ({Pack Code})" (white text, 16pt Helvetica)
- Text aligned left within the stripe.

---

## 2.1 Level Color Coding (UNIVERSAL)

These colors are CONSISTENT across ALL products (covers, labels, page headers, accent stripes):

| Level | Color | Hex Code | Name | Logic |
|-------|-------|----------|------|-------|
| **L1** | Orange | `#F4B400` | Errorless | 5 targets, 0 distractors |
| **L2** | Blue | `#4285F4` | Distractors | 4 targets, 1 distractor |
| **L3** | Green | `#34A853` | Moderate | 3 targets, 2 distractors |
| **L4** | Purple | `#8C06F2` | Challenge | 1 target, 4 distractors |

> **IMPORTANT:** The accent stripe color instantly tells teachers which level they're using.

### Future Advanced Levels (BACKLOG)
- **L3 Advanced**: Picture to Text matching (word cards)
- **L4 Advanced**: Icon to Real Photo cross-representation
- **L5+**: Additional generalisation activities

---

## 3. Icon Standards
- All icons sourced from `/assets/{theme}/icons/`
- Icon style: consistent stroke, color, and proportions
- Icon scaling:
  - Target images: 1.8" box, centered
  - Matching boxes: 1.0" x 1.0" box, 0.75 scale inside
- Icons must be crisp, centered, and never distorted.

---

## 4. Matching Box Standards
- Box size: 1.0" x 1.0"
- Rounded corners: 0.1"
- Velcro dot: 0.35" diameter, centered, light grey (#E6E6E6)
- Vertical spacing: 0.15" between rows
- 5 rows per page (5x2 layout)

---

## 5. Watermark Logic
- Level 1 only:
  - Watermark of the correct icon
  - Opacity: 25%
  - Scale: 70% of box
  - Centered behind velcro dot
- Levels 2-4: no watermark

---

## 6. Cutout Standards
- 5 icons per strip
- Icons touch the edges of their boxes
- Rounded corners
- Title: "Cutout Matching Pieces"
- Accent stripe: Orange (Level 1 color)
- Include all icons used in the activity

---

## 7. Storage Labels
- Title: "Storage Labels - Matching Pack"
- Pack code displayed
- 3-column vocabulary table
- All icons included
- Clean alignment and spacing
- Accent stripe: Orange (Level 1 color)

---

## 8. Color System
- Level-specific accent stripe colors (see Section 2.1)
- Text colors:
  - Title on accent stripe: white
  - Subtitle on accent stripe: white
  - Body text: black
  - Footer line 2: light grey (#999999)

---

## 9. Accessibility
- High contrast (white text on colored stripes)
- Clear iconography
- Predictable layout
- Errorless learning logic applied consistently
- Level colors provide instant visual differentiation

---

## 10. Output Requirements
- Color and BW versions
- Saved to `/review_pdfs/` or `/samples/{theme}/{product_type}/`
- File names: `{theme}_{product_type}_color.pdf`, `{theme}_{product_type}_bw.pdf`

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-05 | 2.2 | Updated: Level-specific accent colors, hybrid level approach |
| 2026-02-05 | 2.1 | Added: 5x2 velcro layout, watermark logic |
| 2026-02-05 | 2.0 | Design Constitution compliant generator |
| 2026-02-05 | 1.0 | Initial specification |
