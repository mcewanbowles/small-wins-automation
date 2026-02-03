# SMALL WINS STUDIO — DESIGN CONSTITUTION
### The Official Standards for All TpT Factory Generators  
**Version 1.0 — February 2026**

---

# 1. Brand Identity

Small Wins Studio resources follow a consistent, SPED‑friendly visual language:

- Clean, uncluttered layouts  
- High contrast, predictable structure  
- Realistic icons and images  
- Consistent spacing and alignment  
- Warm, friendly colour palette  
- Professional, teacher‑trusted design  
- Errorless learning options for emerging learners  

All generators must follow these principles.

---

# 2. Global Page Structure

Every page in every product must include:

## 2.1 Border
- Thin rounded rectangle  
- Light neutral tone  
- 3 px stroke  
- 0.25" margin from page edge  

## 2.2 Accent Stripe
- Positioned at the top of the page  
- Height: **0.35"**  
- Full width  
- Colour determined by **product type**:  
  - Matching = warm orange  
  - Find & Cover = teal  
  - Sentence Strips = purple  
  - Sorting = green  
  - WH Questions = blue  
  - Word Search = red  

## 2.3 Title + Subtitle
Placed **inside the border**, aligned left, sitting **on the accent stripe**:

- **Title:**  
  “

\[Product Name\]

 – Level X”  
- **Subtitle:**  
  “

\[Theme Name\]

 Pack (

\[Pack Code\]

)”

### Typography:
- Title: 22–24 pt  
- Subtitle: 16–18 pt  
- Font: clean, sans‑serif  

## 2.4 Footer (Two Lines)
Every page must include:

**Line 1:**  
`[Pack Code] | [Theme Name] | Level X | Page N/Total`

**Line 2:**  
`© 2025 Small Wins Studio • PCS® symbols used with active PCS Maker Personal License`

### Footer typography:
- Line 1: 10–11 pt  
- Line 2: **9 pt**, light grey `#999999`  

---

# 3. Theme Coding System

Each theme has:

- **Theme Name** (e.g., Brown Bear)  
- **Pack Code** (e.g., BB03)  
- **Asset Folder:**  
  `/assets/[theme]/icons/`  
- **Output Folder:**  
  `/samples/[theme]/[product]/`  

Pack codes follow a consistent sequence:

- BB01 = WH Questions  
- BB02 = Find & Cover  
- BB03 = Matching  
- BB04 = Sentence Strips  
- BB05 = Sorting  
- BB06 = Word Search  

---

# 4. Velcro Dot Standard

Velcro dots must be:

- Small circle  
- Centered inside the matching box  
- Diameter = **25–30%** of box width  
- Light grey fill `#E6E6E6`  
- Thin outline (1–2 px medium grey)  
- Optional tiny “velcro” text (6–7 pt)  
- Never scaled to fill the box  
- Never stretched or distorted  

---

# 5. Icon Standards

All icons must:

- Use **full‑resolution PNGs**  
- Come from `/assets/[theme]/icons/`  
- Never be upscaled from thumbnails  
- Be centered inside their boxes  
- Maintain consistent scaling across pages  
- Use optional subtle drop shadow  
- Never appear fuzzy or pixelated  

If an icon is missing, the generator must stop and notify the user.

---

# 6. Global Measurements & Layout Specs

These measurements apply across all products:

### Page Margins
- 0.25" outer margin  
- 0.5" top margin before title  

### Activity Boxes
- Width: **1.0"**  
- Height: **1.0"**  
- Rounded corners: radius **0.1–0.15"**  
- Vertical spacing: **0.15"**  

### Target Image
- Width: **1.8"**  
- Height: **1.8"**  
- Centered  

### Velcro Dot
- 0.3–0.4" diameter  
- Centered  

### Cutout Icons
- Max width: **1.5"**  
- Max height: **1.5"**  
- 5 icons per strip  
- Strips must **touch** for guillotine cutting  

---

# 7. Level Logic (Product‑Specific)

## 7.1 Matching
- Level 1: 5 targets, 0 distractors  
- Level 2: 4 targets, 1 distractor  
- Level 3: 3 targets, 2 distractors  
- Level 4: 1 target, 4 distractors  

## 7.2 Find & Cover
- Level 1: target + 1 distractor  
- Level 2: target + 2 distractors  
- Level 3: target + 3 distractors  

## 7.3 Word Search
- Level 1: symbol padding  
- Level 2: letters, no diagonals  
- Level 3: letters + diagonals  
- Level 4: smaller grid + diagonals  

## 7.4 Sentence Strips
- Core words + fringe icons  
- Big/little versions  
- Velcro box at end  

## 7.5 Sorting
- 2 categories  
- 4 cards  
- Answer key  

---

# 8. Level 1 Watermark Logic (Errorless Learning)

For any Level 1 activity that uses matching:

- The matching box must contain a **transparent watermark** of the target icon  
- Opacity: **20–30%**  
- Centered  
- Velcro dot still appears on top  

---

# 9. Cutout Pages

Cutouts must include:

- Title: “Cutout Matching Pieces” (or product‑specific equivalent)  
- Subtitle: “

\[Theme\]

 Pack (

\[Pack Code\]

)”  
- Footer  
- **5‑icon strips**  
- Strips must **touch** (no gaps)  
- 4×5 or 5×5 strips per page  
- Rounded boxes  
- Crisp icons  
- No watermarking  

---

# 10. Storage Labels

Storage label pages must include:

- Title: “Storage Labels – 

\[Product\]

 Pack”  
- Subtitle: “

\[Theme\]

 Pack (

\[Pack Code\]

)”  
- Footer  
- Clean 3‑column vocabulary table  
- Consistent font and spacing  

---

# 11. Naming Conventions

Use snake_case filenames:

- `brown_bear_matching_color.pdf`  
- `brown_bear_matching_bw.pdf`  
- `brown_bear_sentence_strips_color.pdf`  

All outputs must include:

- color version  
- black & white version  
- activity pages  
- cutouts  
- storage labels  

---

# 12. Global Generator Defaults

All generators must:

- Load icons from `/assets/[theme]/icons/`  
- Output to `/samples/[theme]/[product]/`  
- Generate color + BW versions  
- Include cutouts + storage labels  
- Apply border + stripe + footer  
- Use crisp PNGs  
- Apply SPED‑friendly spacing  
- Include page numbering  
- Use correct pack code  
- Use correct theme name  
- Follow this Design Constitution  

---

# 13. Error Handling Rules

If an icon is missing:
- Stop  
- Notify the user  
- Do not generate placeholders  

If a generator fails:
- Report the error  
- Do not commit partial files  

If a layout element is missing:
- Regenerate the page  
- Apply defaults  

---

# 14. Quality Assurance Checklist

Before committing files, Copilot must verify:

- Border present  
- Accent stripe present  
- Title + subtitle present  
- Footer present  
- Crisp icons  
- Correct level logic  
- Correct velcro dot  
- Correct watermark (Level 1)  
- Correct spacing  
- Correct page numbering  
- Correct pack code  
- Correct theme name  
- Cutouts included  
- Storage labels included  
- Color + BW versions included  
