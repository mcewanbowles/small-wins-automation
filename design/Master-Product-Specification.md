# Small Wins Studio — Master Product Specification

This document defines the COMPLETE requirements for all TpT products. Every generator MUST produce outputs that comply with this specification.

---

## 1. Product Structure Overview

Every product (e.g., Matching, Find+Cover, AAC) consists of:

```
📦 Product (e.g., "Matching")
├── 📁 Level 1 (Errorless) — Color-coded
├── 📁 Level 2 (Easy)
├── 📁 Level 3 (Medium)
├── 📁 Level 4 (Hard)
├── 📄 Freebie Pack (1 page from each level)
└── 📄 Bundle Pack (all levels combined)
```

---

## 2. Level Color Coding

Each difficulty level has a designated color for easy identification:

| Level | Name | Color Code | Use |
|-------|------|------------|-----|
| Level 1 | Errorless | 🟢 Green | Accent stripe, tab color |
| Level 2 | Easy | 🔵 Blue | Accent stripe, tab color |
| Level 3 | Medium | 🟡 Yellow/Orange | Accent stripe, tab color |
| Level 4 | Hard | 🔴 Red/Pink | Accent stripe, tab color |

---

## 3. Required Outputs Per Level

Every level MUST include all of the following:

### 3.1 Core PDFs

| Output | Format | Required |
|--------|--------|----------|
| Activity Pages (Color) | PDF | ✅ Yes |
| Activity Pages (B&W) | PDF | ✅ Yes |
| Storage Labels (Color) | PDF | ✅ Yes |
| Storage Labels (B&W) | PDF | ✅ Yes |

### 3.2 Marketing Assets

| Output | Format | Purpose | Required |
|--------|--------|---------|----------|
| Thumbnail | PNG (1000×1000px) | TpT listing main image | ✅ Yes |
| Preview Images | PNG (various) | TpT listing gallery | ✅ Yes |
| Cover Page | PDF | First page of product | ✅ Yes |

### 3.3 Supporting Documents

| Output | Format | Contents | Required |
|--------|--------|----------|----------|
| Instructions | PDF | How to use this product | ✅ Yes |
| Terms of Use (TOU) | PDF | Copyright, usage rights | ✅ Yes |
| Credits | PDF | Font/clip art credits | ✅ Yes |

### 3.4 Final Package

| Output | Format | Contents | Required |
|--------|--------|----------|----------|
| TpT ZIP | ZIP | All PDFs for one level | ✅ Yes |
| SEO Description | TXT | Product description for TpT | ✅ Yes |

---

## 4. Branding Requirements

All products MUST include consistent branding:

### 4.1 Page Border
- 2–3 px rounded rectangle border on every page
- 0.12" corner radius
- Border sits 0.5" from page edge

### 4.2 Footer (Every Page)
```
{PACK_CODE} | {THEME} | Level {X} | Page {Y}/{TOTAL}
© 2025 Small Wins Studio. PCS® symbols used with active PCS Maker Personal License.
```

### 4.3 Logo
- Small Wins Studio logo on cover page
- Located in bottom right of cover

### 4.4 Copyright Notice
- Present in footer of every page
- Full copyright statement in TOU document

---

## 5. File Naming Convention

All files must follow this exact pattern:

```
{theme}_{product}_{level}_{variant}_{color}.{ext}
```

### Examples:
```
brown_bear_matching_level1_activity_color.pdf
brown_bear_matching_level1_activity_bw.pdf
brown_bear_matching_level1_storage_color.pdf
brown_bear_matching_level1_storage_bw.pdf
brown_bear_matching_level1_cover.pdf
brown_bear_matching_level1_instructions.pdf
brown_bear_matching_level1_thumbnail.png
brown_bear_matching_level1_preview_1.png
brown_bear_matching_level1.zip
brown_bear_matching_level1_seo.txt
```

---

## 6. Folder Structure

Exports must be organized as:

```
exports/{date}_{theme}/
├── matching/
│   ├── level1/
│   │   ├── brown_bear_matching_level1_activity_color.pdf
│   │   ├── brown_bear_matching_level1_activity_bw.pdf
│   │   ├── brown_bear_matching_level1_storage_color.pdf
│   │   ├── brown_bear_matching_level1_storage_bw.pdf
│   │   ├── brown_bear_matching_level1_cover.pdf
│   │   ├── brown_bear_matching_level1_instructions.pdf
│   │   ├── brown_bear_matching_level1_thumbnail.png
│   │   ├── brown_bear_matching_level1_preview_1.png
│   │   ├── brown_bear_matching_level1_tou.pdf
│   │   ├── brown_bear_matching_level1_credits.pdf
│   │   ├── brown_bear_matching_level1.zip
│   │   └── brown_bear_matching_level1_seo.txt
│   ├── level2/
│   ├── level3/
│   ├── level4/
│   ├── freebie/
│   └── bundle/
├── find_cover/
│   └── (same structure)
└── aac/
    └── (same structure)
```

---

## 7. ZIP Contents (TpT Ready)

Each level's ZIP file must contain:

```
{theme}_{product}_level{X}.zip
├── {theme}_{product}_level{X}_activity_color.pdf
├── {theme}_{product}_level{X}_activity_bw.pdf
├── {theme}_{product}_level{X}_storage_color.pdf
├── {theme}_{product}_level{X}_storage_bw.pdf
├── {theme}_{product}_level{X}_cover.pdf
├── {theme}_{product}_level{X}_instructions.pdf
├── Terms_of_Use.pdf
└── Credits.pdf
```

**Note:** Thumbnails and previews are NOT included in ZIP (uploaded separately to TpT).

---

## 8. Freebie Pack Specification

Purpose: Drive customers to buy the full bundle.

### Contents:
- 1 sample page from EACH level (3–4 pages total)
- Cover page (marked as "FREEBIE SAMPLER")
- Instructions
- TOU & Credits
- Promotional page linking to full bundle

### File Naming:
```
{theme}_{product}_freebie.zip
{theme}_{product}_freebie_seo.txt
```

### Freebie SEO Text Should Include:
- "Try before you buy!"
- Link/mention of full bundle
- What's included in the sampler
- Grade levels & skills covered

---

## 9. Bundle Pack Specification

Purpose: All levels in one discounted package.

### Contents:
- ALL levels (1–4) combined
- Single cover page for bundle
- Combined instructions
- TOU & Credits

### File Naming:
```
{theme}_{product}_bundle.zip
{theme}_{product}_bundle_seo.txt
```

---

## 10. SEO Product Description Template

Each product must have a text file with TpT-ready description:

```txt
📚 {PRODUCT_NAME} - {THEME} Theme | Level {X}

Perfect for special education, autism classrooms, and speech therapy!

✨ WHAT'S INCLUDED:
• {X} activity pages (color)
• {X} activity pages (black & white)
• Storage labels
• Step-by-step instructions
• Terms of Use

🎯 SKILLS TARGETED:
• {Skill 1}
• {Skill 2}
• {Skill 3}

📋 LEVELS AVAILABLE:
• Level 1: Errorless (scaffolded support)
• Level 2: Easy
• Level 3: Medium
• Level 4: Hard

💡 PERFECT FOR:
• Special Education
• Autism/ASD Classrooms
• Speech Therapy
• Early Intervention
• Preschool & Kindergarten

🔗 SAVE WITH THE BUNDLE:
{Link to bundle product}

© 2025 Small Wins Studio
```

---

## 11. Generator Checklist

Before a generator is considered complete, verify:

### Per Level:
- [ ] Activity pages generated (color + B&W)
- [ ] Storage labels generated (color + B&W)
- [ ] Cover page generated
- [ ] Thumbnail PNG generated (1000×1000)
- [ ] Preview images generated
- [ ] Instructions page generated
- [ ] TOU included
- [ ] Credits included
- [ ] ZIP file created
- [ ] SEO text file created

### Per Product:
- [ ] All levels complete (1–4)
- [ ] Freebie pack created
- [ ] Bundle pack created
- [ ] Level color coding applied correctly
- [ ] Branding consistent across all outputs
- [ ] Footer on every page
- [ ] File naming follows convention

---

## 12. Common Documents (Reusable)

These documents are the same across all products and themes:

| Document | Location | Notes |
|----------|----------|-------|
| Terms of Use | `/assets/global/tou.pdf` | Standard TOU |
| Credits Template | `/assets/global/credits_template.pdf` | Update per product |
| Instructions Template | `/assets/global/instructions_template.pdf` | Customize per product |

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-05 | 1.0 | Initial comprehensive specification |
