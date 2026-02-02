# MATCHING PRODUCT SPECIFICATION
Small Wins Studio — Product‑Specific Rules  
This file defines the exact layout, proportions, logic, and behaviour required for all MATCHING activities.  
These rules override the global Design Constitution where conflicts occur.

---

# 1. PAGE STRUCTURE
- Portrait orientation.
- 5 ROWS × 2 COLUMNS layout.
- Matching boxes slightly smaller for vertical fit (approx. 1.4"–1.6").
- Icons must be as large as possible inside the box (90–95% fill).
- Columns spaced 1.0"–1.3" apart.
- Title and subtitle must be centered.
- Subtitle “Match the ___” must appear ABOVE the target box.
- Accent stripe must NOT touch page border and must have increased height.
- Footer must NOT be overlapped by boxes (minimum 0.3" bottom margin).

---

# 2. TARGET BOX (REFERENCE IMAGE)
- May be rectangular or square.
- Navy border (#1E3A5F).
- Soft shadow (5–8% opacity).
- Rounded corners (0.12").
- Slightly thicker border than matching boxes.
- Centered horizontally above the grid.
- Target icon size: approx. 0.8"–1.0".
- Target icon sits inside the bordered box with minimal padding.

---

# 3. MATCHING BOXES (LEFT COLUMN)
- Box size: approx. 1.4"–1.6" square.
- Rounded corners: 0.12".
- Border colour: Navy (#1E3A5F) OR theme accent colour.
- Decorative corner detail required:
  - Slightly thicker stroke on two opposite corners OR
  - Small corner embellishment matching original Husky design.
- Border width: 2–3 px.
- Image fills 90–95% of box.
- Minimal padding (3–6 px).
- Image must be centered and crisp.
- No text labels inside boxes.

---

# 4. VELCRO BOXES (RIGHT COLUMN)
- Same size as matching boxes.
- Light grey fill (#E8E8E8).
- Purple border (#6B5BE2).
- Rounded corners (0.12").
- Velcro dot:
  - Diameter approx. 0.3".
  - Fill: #CCCCCC.
  - Outline: #999999.
  - Centered.
- No oversized velcro circles.

---

# 5. LEVEL LOGIC
## Level 1 — Errorless
- 5 targets, 0 distractors.
- All 5 pictures match the target.
- Watermark required behind each picture box:
  - Opacity: 20–30%.
  - Scale: 70–80% of box.
  - Centered behind velcro dot.
- Student places 5 pieces.

## Level 2 — Easy
- 4 targets, 1 distractor.
- Student places 4 pieces.
- No watermark.

## Level 3 — Medium
- 3 targets, 2 distractors.
- Student places 3 pieces.
- No watermark.

## Level 4 — Hard
- 1 target, 4 distractors.
- Student places 1 piece.
- No watermark.

---

# 6. ICON SELECTION RULES
- Load all 12 icons from `/assets/{theme}/icons/`.
- Each icon must appear at least once across the 4 levels.
- No repeating the same icon across all rows.
- No placeholder icons.
- No empty boxes.
- Distractors must be varied.
- “See” must be renamed to “Eyes”.

---

# 7. CUTOUT PAGE
- 4 columns × 5 rows = 20 boxes.
- Box size matches activity boxes (1.4"–1.6").
- Icons must be 60pt minimum.
- Blue cutout box height: 180pt.
- Spacing between icons: 15pt.
- Border thickness: 3pt.
- All icons must appear at least once.
- Title: “Cutout Matching Pieces – {Theme}”.

---

# 8. ACCENT STRIPE
- Must NOT touch page border.
- Must have increased height to visually separate title block.
- Must remain behind title + subtitle.
- Must convert cleanly to grayscale in BW version.

---

# 9. BLACK & WHITE VERSION
- Must be grayscale only.
- No orange or theme colours.
- Borders must remain visible.
- Icons must remain visible (no black-on-black).
- Accent stripe must convert to grayscale.

---

# 10. FOOTER
- Single line.
- 8–10 pt font.
- Centered.
- Must sit within 0.3" of bottom margin.
- Must never be overlapped by matching boxes.

Format:
`{PACK_CODE} | {THEME} | Matching Level {X} | Page {Y}/{TOTAL} @ 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License.`

---

# 11. OUTPUT REQUIREMENTS
- Generate Levels 1–4.
- Generate cutout page.
- Generate storage labels.
- Export COLOR and BW.
- Save to `/samples/{theme}/matching/`.
- Overwrite existing files.

