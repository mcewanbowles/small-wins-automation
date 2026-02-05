# Small Wins Studio — Master Product Specification

> **DEFINITIVE SPEC** — No optional variants unless explicitly marked as "BACKLOG".

This document defines the COMPLETE requirements for all TpT products. Every generator MUST produce outputs that comply with this specification.

---

## 1. Key Definitions

| Term | Definition |
|------|------------|
| **Product** | ONE TpT listing = ONE final ZIP file |
| **Level** | A specific difficulty variant (e.g., "Matching Level 2" = one product/listing/ZIP) |
| **Artefact** | Any generated file (PDF, PNG, TXT) |
| **Listing assets** | Preview/thumbnail/SEO text — NOT inside product PDFs |
| **Product PDFs** | Cover, Instructions, Activity pages — ARE inside the ZIP |

---

## 2. Level Color Coding (UNIVERSAL)

These colors are CONSISTENT across ALL products (covers, labels, page headers, accent stripes):

| Level | Color | Hex Code | Name |
|-------|-------|----------|------|
| **L1** | 🟠 Orange | `#F4B400` | Errorless |
| **L2** | 🔵 Blue | `#4285F4` | Distractors |
| **L3** | 🟢 Green | `#34A853` | Picture + Text |
| **L4** | 🟣 Purple | `#8C06F2` | Generalisation |

> **IMPORTANT:** The accent stripe color instantly tells teachers which level they're using.

---

## 3. Product Specifications by Type

### 3.1 MATCHING — 4 Levels

#### Level 1: Errorless (🟠 Orange)
- **Matching type:** Identical picture → picture
- **Distractors:** None
- **Logic:** No wrong answers (any placement is correct)
- **Representation:** Single type only (icons only OR photos only)

#### Level 2: Distractors (🔵 Blue)
- **Matching type:** Picture → picture with distractors
- **Distractors:** Start obvious, become more similar within the set
- **Representation:** Single type only (icons only OR photos only) per page

#### Level 3: Picture + Text (🟢 Green)
- **Content:** BOTH directions included in same product:
  - A) Picture → Word (words in target boxes)
  - B) Word → Picture (words on cards matched to pictures)
- **Orientations:** BOTH left/right for each direction:
  - Version 1: Prompts/targets on RIGHT
  - Version 2: Prompts/targets on LEFT
- **Note:** Increased page count is intentional for L3
- **Extra outputs:** Cutouts with text required

#### Level 4: Generalisation (🟣 Purple)
- **Matching type:** Icon ↔ Real photo (cross-representation)
- **Distractors:** Hardest (most similar items)
- **Additional set:** BW ↔ Colour matching (requires colouring images + real images)

---

### 3.2 FIND + COVER — 4 Levels

Levels based on distractor load:

| Level | Distractors | Layout | Description |
|-------|-------------|--------|-------------|
| **L1** | Lowest | Fewer items | Easy visual search |
| **L2** | More | More items | Still fairly distinct |
| **L3** | High | Tighter layout | Items more similar |
| **L4** | Highest | Densest layout | Most similar items |

---

### 3.3 AAC — NO LEVELS

- AAC is **STD only** (one product stream)
- No differentiation levels
- Single product per theme

---

## 4. Required "9 Parts" Output Per Product

For EVERY product listing (e.g., `BrownBear_Matching_Level2`), generate these artefacts:

### 4.1 PDFs (Inside the ZIP)

| # | File | Description | Inside ZIP? |
|---|------|-------------|-------------|
| 1 | **Cover** | Title page with branding, level color | ✅ Yes |
| 2 | **Instructions** | How to use this product | ✅ Yes |
| 3 | **Activity Pages (Color)** | Main activity content | ✅ Yes |
| 4 | **Activity Pages (B&W)** | Printer-friendly version | ✅ Yes |
| 5 | **Storage Labels (Color)** | For organizing materials | ✅ Yes |
| 6 | **Storage Labels (B&W)** | Printer-friendly version | ✅ Yes |
| 7 | **Terms of Use** | Copyright and usage rights | ✅ Yes |
| 8 | **Credits** | Font/clip art attribution | ✅ Yes |

### 4.2 Listing Assets (NOT in ZIP — for TpT upload)

| # | File | Format | Purpose |
|---|------|--------|---------|
| 9 | **Thumbnail** | PNG (1000×1000) | TpT listing main image |
| 10 | **Preview Images** | PNG (various) | TpT listing gallery |
| 11 | **SEO Description** | TXT | Product description for TpT |

### 4.3 Final Package

| # | File | Contents |
|---|------|----------|
| 12 | **Product ZIP** | All PDFs (items 1-8) bundled for download |

---

## 5. File Naming Convention

### Pattern
```
{Theme}_{Product}_Level{X}_{Variant}.{ext}
```

### Examples
```
BrownBear_Matching_Level1_Cover.pdf
BrownBear_Matching_Level1_Activity_Color.pdf
BrownBear_Matching_Level1_Activity_BW.pdf
BrownBear_Matching_Level1_Storage_Color.pdf
BrownBear_Matching_Level1_Storage_BW.pdf
BrownBear_Matching_Level1_Instructions.pdf
BrownBear_Matching_Level1_TOU.pdf
BrownBear_Matching_Level1_Credits.pdf
BrownBear_Matching_Level1.zip

BrownBear_Matching_Level1_Thumbnail.png
BrownBear_Matching_Level1_Preview1.png
BrownBear_Matching_Level1_SEO.txt
```

---

## 6. Folder Structure

```
exports/{date}_{theme}/
├── matching/
│   ├── level1/
│   │   ├── BrownBear_Matching_Level1_Cover.pdf
│   │   ├── BrownBear_Matching_Level1_Activity_Color.pdf
│   │   ├── BrownBear_Matching_Level1_Activity_BW.pdf
│   │   ├── BrownBear_Matching_Level1_Storage_Color.pdf
│   │   ├── BrownBear_Matching_Level1_Storage_BW.pdf
│   │   ├── BrownBear_Matching_Level1_Instructions.pdf
│   │   ├── BrownBear_Matching_Level1_TOU.pdf
│   │   ├── BrownBear_Matching_Level1_Credits.pdf
│   │   ├── BrownBear_Matching_Level1.zip
│   │   ├── BrownBear_Matching_Level1_Thumbnail.png
│   │   ├── BrownBear_Matching_Level1_Preview1.png
│   │   └── BrownBear_Matching_Level1_SEO.txt
│   ├── level2/
│   ├── level3/
│   ├── level4/
│   ├── freebie/
│   └── bundle/
├── find_cover/
│   └── (same structure)
└── aac/
    └── BrownBear_AAC_STD.zip (no levels)
```

---

## 7. Page Layout & Branding

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
│ │  │     "Matching Activity — Level 1"           │    │ │  ← Title
│ │  │     "Brown Bear Theme"                      │    │ │  ← Subtitle
│ │  └─────────────────────────────────────────────┘    │ │
│ │                                                     │ │
│ │              [ACTIVITY CONTENT]                     │ │
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

### Branding Elements

| Element | Position | Style |
|---------|----------|-------|
| Pack Code | Above border, left | Grey (#666666), 8pt |
| Page Numbers | Above border, right | Grey (#666666), 8pt |
| "Small Wins Studio" | Above border, center | Grey (#999999), 10pt |
| Copyright | Footer inside border | Grey (#999999), 8pt |

---

## 8. Available Icon Types

Each theme has THREE types of images:

| Type | Folder | Use |
|------|--------|-----|
| **Coloured Icons** | `/assets/themes/{theme}/icons/` | Standard activities |
| **Real Images** | `/assets/themes/{theme}/real_images/` | Generalisation (L4) |
| **Colouring Outlines** | `/assets/themes/{theme}/colouring/` | B&W matching, colouring |

---

## 9. Freebie & Bundle Packs

### Freebie (BACKLOG)
- 1 sample page from each level (3-4 pages total)
- Same packaging (cover, instructions, TOU)
- Purpose: Drive customers to buy full product

### Bundle (BACKLOG)
- All levels combined at discount
- Single cover page for bundle

---

## 10. Generator Checklist

Before a generator is considered complete:

### Per Product/Level:
- [ ] Cover page (level color)
- [ ] Instructions page
- [ ] Activity pages (Color)
- [ ] Activity pages (B&W)
- [ ] Storage labels (Color)
- [ ] Storage labels (B&W)
- [ ] TOU page
- [ ] Credits page
- [ ] Final ZIP created
- [ ] Thumbnail PNG
- [ ] Preview images
- [ ] SEO text file

### Branding:
- [ ] Accent stripe uses correct level color
- [ ] Pack code and page numbers above border
- [ ] "Small Wins Studio" branding present
- [ ] Copyright footer on every page

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-05 | 2.0 | **DEFINITIVE SPEC** — Complete rewrite with exact level definitions for Matching/Find+Cover |
| 2026-02-05 | 1.1 | Added icon types, page layout details |
| 2026-02-05 | 1.0 | Initial specification |
