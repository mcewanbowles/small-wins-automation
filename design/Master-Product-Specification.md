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

Each difficulty level has a designated accent stripe color:

| Level | Name | Color | Hex Code | Use |
|-------|------|-------|----------|-----|
| Level 1 | Errorless | 🟠 Orange | `#F4B400` | Accent stripe |
| Level 2 | Easy | 🔵 Blue | `#4285F4` | Accent stripe |
| Level 3 | Medium | 🟢 Green | `#34A853` | Accent stripe |
| Level 4 | Hard | 🟣 Purple | `#8C06F2` | Accent stripe |

> **Note:** These colors are used for the accent stripe on activity pages. The stripe color instantly tells teachers which level they're looking at.

---

## 2.5 Page Layout & Branding

### Page Structure (Top to Bottom)

```
┌─────────────────────────────────────────────────────────┐
│  PACK CODE: BB-M-L1      Page 1/12           (grey)    │  ← Above border
│  "Small Wins Studio"                         (grey)    │  ← Above border
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │                                                     │ │  ← Page border
│ │  ┌─────────────────────────────────────────────┐    │ │
│ │  │     ACCENT STRIPE (Level Color)             │    │ │  ← Rounded corners
│ │  │     "Matching Activity"                     │    │ │  ← Title
│ │  │     "Brown Bear Theme"                      │    │ │  ← Subtitle
│ │  └─────────────────────────────────────────────┘    │ │
│ │                                                     │ │
│ │              [ACTIVITY CONTENT]                     │ │
│ │                                                     │ │
│ │                                                     │ │
│ │─────────────────────────────────────────────────────│ │
│ │  © 2025 Small Wins Studio. All rights reserved.    │ │  ← Footer inside border
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Accent Stripe Details

| Property | Value |
|----------|-------|
| Height | 0.5" – 0.6" |
| Corner Radius | 0.12" (rounded corners) |
| Padding from border | 0.1" – 0.15" on all sides |
| Background | Level color (see Section 2) |
| Title Font | Arial Rounded MT Bold, 18pt, Navy |
| Subtitle Font | Arial, 12pt, Dark Grey |

### Header (Above Border)

| Element | Position | Style |
|---------|----------|-------|
| Pack Code | Top left | Grey (#666666), 8pt |
| Page Numbers | Top right | Grey (#666666), 8pt, "Page X/Y" |
| "Small Wins Studio" | Centered below pack code | Grey (#999999), 10pt |

### Footer (Inside Border)

| Element | Position | Style |
|---------|----------|-------|
| Copyright | Centered at bottom | Grey (#999999), 8pt |
| Format | `© 2025 Small Wins Studio. All rights reserved.` |

### Page Border

| Property | Value |
|----------|-------|
| Stroke Width | 2–3 px |
| Corner Radius | 0.12" |
| Color | Navy (#1E3A5F) |
| Margin from page edge | 0.5" on all sides |

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

## 12. Available Icon Types

Each theme has THREE types of images available:

### 12.1 Icon Types

| Type | Folder | Description | Use Case |
|------|--------|-------------|----------|
| **Coloured Icons** | `/assets/themes/{theme}/icons/` | Boardmaker-style colored icons | Activity pages, matching |
| **Real Images** | `/assets/themes/{theme}/real_images/` | Photographs | Real-world recognition |
| **Colouring Outlines** | `/assets/themes/{theme}/colouring/` | Black & white line art | Coloring activities |

### 12.2 Brown Bear Theme Icons Available

**Coloured Icons (Boardmaker-style):**
- Brown bear, Red bird, Yellow duck, Blue horse
- Green frog, Purple cat, White dog, Black sheep
- Teacher, Children, Goldfish, See (eye)

**Real Images (Photos):**
- Bear, Bird, Cat, Dog, Duck, Eyes
- Frog, Goldfish, Horse, Sheep, Teacher

**Colouring Outlines:**
- Bear, Bird, Cat, Dog, Duck
- Frog, Goldfish, Horse, Sheep

### 12.3 Global Assets

| Asset Type | Location |
|------------|----------|
| AAC Core Icons | `/assets/global/aac_core/` |
| AAC Core Text | `/assets/global/aac_core_text/` |
| Colour Swatches | `/assets/global/colours/` |
| Branding/Logo | `/assets/branding/` |

---

## 13. Common Documents (Reusable)

These documents are the same across all products and themes:

| Document | Location | Notes |
|----------|----------|-------|
| Terms of Use | `/assets/global/tou.pdf` | Standard TOU |
| Credits Template | `/assets/global/credits_template.pdf` | Update per product |
| Instructions Template | `/assets/global/instructions_template.pdf` | Customize per product |

---

## 14. Questions To Clarify With User

The following details need user input before generators can be finalized:

### Level Content (What's in each level?)

| Product | Level 1 | Level 2 | Level 3 | Level 4 |
|---------|---------|---------|---------|---------|
| Matching | Errorless (identical matches) | ? | ? | ? |
| Find+Cover | Errorless | ? | ? | ? |
| AAC | ? | ? | ? | ? |

### Documents To Create/Update

- [ ] **Terms of Use (TOU)** — Does current version need updates?
- [ ] **Activity Instructions** — Per-product instructions for teachers
- [ ] **Product Description (SEO)** — Separate file or combined with TOU?

### Design Decisions

- [ ] Confirm level colors: L1=Orange, L2=Blue, L3=?, L4=?
- [ ] Pack code format (e.g., "BB-M-L1" for Brown Bear Matching Level 1)
- [ ] Any other branding elements needed?

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-05 | 1.1 | Added icon types, page layout details, questions section |
| 2026-02-05 | 1.0 | Initial comprehensive specification |
