# MATCHING PRODUCT SPECIFICATION
Small Wins Studio — Product‑Specific Rules

This file defines the exact layout, proportions, logic, and behaviour required for all MATCHING activities.  
These rules override the global Design Constitution where conflicts occur.

---

## 1. PAGE STRUCTURE
- Portrait orientation.
- 5 ROWS × 2 COLUMNS layout.
- Target image at top, small and centered.
- Matching boxes are large and dominate the page.
- Velcro boxes are same size as matching boxes.

Spacing:
- Top margin before title: 0.5"
- Space between title and subtitle: 0.2"
- Space between subtitle and target icon: 0.3"
- Space between target icon and first row: 0.5"
- Vertical spacing between rows: 0.1"–0.15"
- Horizontal spacing between columns: 1.0"–1.3"

---

## 2. TARGET IMAGE
- Purpose: visual reference only.
- Size: approx. 0.8"–1.0" square.
- Placed inside a rounded rectangle with thin border.
- Centered horizontally above grid.
- Never larger than matching boxes.

---

## 3. MATCHING BOXES
- Size: approx. 1.4"–1.6" square.
- Rounded corners: 0.12"
- Border: 2–3 px navy.
- Image fills 90–95% of box.
- Padding: 3–6 px max.
- Always centered and crisp.

Grid:
- 5 rows × 2 columns.
- Left column = image boxes.
- Right column = velcro boxes.

---

## 4. VELCRO BOXES
- Same size as image boxes.
- Light grey fill.
- Purple border.
- Centered velcro dot:
  - Diameter: ~0.3"
  - Fill: #CCCCCC
  - Outline: #999999
  - Optional label: “velcro” in 8pt font

---

## 5. LEVEL LOGIC
### Level 1 — Errorless
- 5 targets, 0 distractors.
- All 5 pictures match the target.
- Watermark behind each picture box:
  - Opacity: 20–30%
  - Scale: 70–80% of box
  - Centered behind velcro dot
- Student places 5 pieces.

### Level 2 — Easy
- 4 targets, 1 distractor.
- Student places 4 pieces.
- No watermark.

### Level 3 — Medium
- 3 targets, 2 distractors.
- Student places 3 pieces.
- No watermark.

### Level 4 — Hard
- 1 target, 4 distractors.
- Student places 1 piece.
- No watermark.

---

## 6. ICON SELECTION
- Load all 12 icons from `/assets/{theme}/icons/`.
- Each icon must appear at least once across the 4 levels.
- Do not repeat a single icon (e.g., sheep) across all rows.
- Distractors chosen from remaining icons.
- Shuffle rows for each page.

Special override:
- If icon name is “see”, replace with “eyes” for display.

---

## 7. CUTOUT PAGE
- 4 columns × 5 rows = 20 boxes.
- Box size matches activity boxes (1.4"–1.6").
- Boxes touch or have minimal spacing (0–0.1").
- Each icon appears at least once.
- Images fill 90–95% of box.
- Title: “Cutout Matching Pieces – {Theme}”

Fixes applied:
- Icon size increased to 60pt for 12 images.
- Blue box height increased to 180pt.
- Spacing between icons increased to 15pt.
- Border thickness increased to 3pt.

---

## 8. BLACK & WHITE VERSION
- Accent stripe must convert to grayscale.
- No orange or theme colors.
- Icons must remain visible (no black-on-black).
- Borders remain visible in grayscale.

---

## 9. FOOTER
- Single line.
- 8–10 pt font.
- Centered.
- Within 0.3" of bottom margin.

Format:
`{PACK_CODE} | {THEME} | Matching Level {X} | Page {Y}/{TOTAL} @ 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License.`

---

## 10. OUTPUT REQUIREMENTS
- Generate Levels 1–4.
- Generate cutout page.
- Generate storage labels.
- Export both COLOR and BW.
- Save to `/samples/{theme}/matching/`.
- Overwrite existing files.
