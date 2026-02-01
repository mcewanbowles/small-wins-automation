# Small Wins Studio — Design Constitution

This document defines the universal visual, structural, and accessibility standards for all Small Wins Studio resources. All generators must comply with these rules unless explicitly overridden for a specific product type.

---

## 1. Page Structure
- Page size: US Letter (8.5" × 11")
- Margins: 0.5" on all sides
- Border: 2–3 px rounded rectangle, 0.12" corner radius
- Footer: always present, consistent across all products  
  Format: `{PACK_CODE} | {THEME} | Level {X} | Page {Y}/{TOTAL} @ 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License.`

---

## 2. Title Block
- Title and subtitle sit inside an accent stripe.
- Accent stripe height: 0.5"–0.6"
- Stripe must sit inside the border with rounded corners.
- Title: product type (e.g., “Matching Activity”)
- Subtitle: theme (e.g., “Brown Bear”)
- No level in the title.
- Title and subtitle centered vertically and horizontally within the stripe.

---

## 3. Icon Standards
- All icons sourced from `/assets/{theme}/icons/`
- Icon style: consistent stroke, color, and proportions
- Icon scaling:
  - Target images: 1.4" box, minimal padding
  - Matching boxes: 1.0"–1.15" box, reduced padding
- Icons must be crisp, centered, and never distorted.

---

## 4. Matching Box Standards
- Box size: 1.0"–1.15"
- Rounded corners: 0.12"
- Velcro dot centered
- Vertical spacing: 0.25"–0.35"
- Horizontal spacing between columns: generous, balanced

---

## 5. Watermark Logic
- Level 1 only:
  - Watermark of the correct icon
  - Opacity: 20–30%
  - Scale: 70–80% of box
  - Centered behind velcro dot
- Levels 2–4: no watermark

---

## 6. Cutout Standards
- 5 icons per strip
- Icons touch the edges of their boxes
- Rounded corners
- Title: “Cutout Matching Pieces – {Theme}”
- Include all icons used in the activity

---

## 7. Storage Labels
- Title: “{Theme} Matching Cards”
- Pack code displayed
- 3-column vocabulary table
- All icons included
- Clean alignment and spacing

---

## 8. Color System
- Accent stripe uses theme color (e.g., warm orange for Brown Bear)
- Text colors:
  - Title: navy
  - Subtitle: dark grey
  - Body text: black

---

## 9. Accessibility
- High contrast
- Clear iconography
- Predictable layout
- Errorless learning logic applied consistently

---

## 10. Output Requirements
- Color and BW versions
- Saved to `/samples/{theme}/{product_type}/`
- File names: `{theme}_{product_type}_color.pdf`, `{theme}_{product_type}_bw.pdf`
