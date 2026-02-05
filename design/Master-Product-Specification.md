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

## 4. Required Output Per Product

For EVERY product listing (e.g., `BrownBear_Matching_Level2`), generate these artefacts:

### 4.1 PDFs (Inside the ZIP)

| # | File | Description | Template |
|---|------|-------------|----------|
| 1 | **Cover** | Title page with branding, level color | SMS branding, star icon, borders |
| 2 | **Student Directions** | Simple visual instructions for students | `assets/global/templates/Student_Directions.md` |
| 3 | **Support Tips (PODD/AAC)** | Quick reference for paras/support staff | `assets/global/templates/Support_Tips_PODD_AAC.md` |
| 4 | **Activity Pages (Color)** | Main activity content | File folder format, Comic Sans MS |
| 5 | **Activity Pages (B&W)** | Printer-friendly version | File folder format, Comic Sans MS |
| 6 | **Storage Labels (Color)** | For organizing materials | **Include icons + Storage Note** |
| 7 | **Storage Labels (B&W)** | Printer-friendly version | **Include icons + Storage Note** |
| 8 | **TOU + Credits** | Combined Terms of Use and Credits | `assets/global/templates/TOU_Credits.md` |

### 4.2 Listing Assets (NOT in ZIP — for TpT upload separately)

| # | File | Format | Purpose |
|---|------|--------|---------|
| 9 | **Thumbnail** | PNG (1000×1000) | TpT listing main square image |
| 10 | **Preview Images** | PNG (various) | **Sample activity pages showing the product in action** |
| 11 | **SEO Description** | TXT | Product description for TpT copy/paste |

### 4.3 Final Package

| # | File | Contents |
|---|------|----------|
| 12 | **Product ZIP** | All PDFs (items 1-8) bundled for download |

---

## 5. Product Formats

### 5.1 File Folder Format (PRIMARY)
- **Size:** US Letter (8.5" × 11")
- **Use:** Standard file folder activities
- **Default format for all products**

### 5.2 Task Box Format (SECONDARY)
- **Size:** Photo box size (to be defined)
- **Use:** Task box activities for teachers who prefer this method
- **Same product content, different dimensions**
- **Different SEO text for TpT listing**
- **BACKLOG:** Size adjustments to be tweaked later

> **Note:** Each product will be offered in BOTH formats as separate TpT listings.

---

## 6. Freebie Pack (Per Product)

Each product type gets ONE freebie to drive sales:

### Contents of Freebie ZIP:
| # | Component | Description |
|---|-----------|-------------|
| 1 | **Cover** | Freebie-branded cover |
| 2 | **Quick Start Instructions** | Same as main product |
| 3 | **Sample Activity Pages** | ONE activity page from EACH level (4 pages total) |
| 4 | **Storage Labels** | With icons |
| 5 | **Terms of Use** | Standard TOU |
| 6 | **Credits** | Standard credits |
| 7 | **"Buy the Full Product" Page** | Encourages purchase + review |

### Freebie Naming:
```
BrownBear_Matching_Freebie.zip
BrownBear_Matching_Freebie_Thumbnail.png
BrownBear_Matching_Freebie_SEO.txt
```

---

## 7. File Naming Convention

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
BrownBear_Matching_Level1_QuickStart.pdf
BrownBear_Matching_Level1_TOU.pdf
BrownBear_Matching_Level1_Credits.pdf
BrownBear_Matching_Level1.zip

BrownBear_Matching_Level1_Thumbnail.png
BrownBear_Matching_Level1_Preview1.png
BrownBear_Matching_Level1_SEO.txt

BrownBear_Matching_Freebie.zip
BrownBear_Matching_Freebie_SEO.txt
```

---

## 8. Folder Structure

```
exports/{date}_{theme}/
├── matching/
│   ├── file_folder/           # US Letter size
│   │   ├── level1/
│   │   │   ├── BrownBear_Matching_Level1_Cover.pdf
│   │   │   ├── BrownBear_Matching_Level1_Activity_Color.pdf
│   │   │   ├── BrownBear_Matching_Level1_Activity_BW.pdf
│   │   │   ├── BrownBear_Matching_Level1_Storage_Color.pdf
│   │   │   ├── BrownBear_Matching_Level1_Storage_BW.pdf
│   │   │   ├── BrownBear_Matching_Level1_QuickStart.pdf
│   │   │   ├── BrownBear_Matching_Level1_TOU.pdf
│   │   │   ├── BrownBear_Matching_Level1_Credits.pdf
│   │   │   ├── BrownBear_Matching_Level1.zip
│   │   │   ├── BrownBear_Matching_Level1_Thumbnail.png
│   │   │   ├── BrownBear_Matching_Level1_Preview1.png
│   │   │   └── BrownBear_Matching_Level1_SEO.txt
│   │   ├── level2/
│   │   ├── level3/
│   │   ├── level4/
│   │   └── freebie/
│   │       ├── BrownBear_Matching_Freebie.zip
│   │       └── BrownBear_Matching_Freebie_SEO.txt
│   └── task_box/              # Photo box size (BACKLOG)
│       └── (same structure, different dimensions)
├── find_cover/
│   └── (same structure)
└── aac/
    └── BrownBear_AAC_STD.zip (no levels)
```

---

## 9. Page Layout & Branding

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

## 10. Available Icon Types

Each theme has THREE types of images:

| Type | Folder | Use |
|------|--------|-----|
| **Coloured Icons** | `/assets/themes/{theme}/icons/` | Standard activities, storage labels |
| **Real Images** | `/assets/themes/{theme}/real_images/` | Generalisation (L4) |
| **Colouring Outlines** | `/assets/themes/{theme}/colouring/` | B&W matching, colouring |

---

## 11. Generator Checklist

Before a generator is considered complete:

### Per Product/Level:
- [ ] Cover page (level color, SMS branding)
- [ ] Quick Start Instructions (SMS branding, borders)
- [ ] Activity pages (Color) - File folder format
- [ ] Activity pages (B&W) - File folder format
- [ ] Storage labels (Color) **with icons**
- [ ] Storage labels (B&W) **with icons**
- [ ] TOU page
- [ ] Credits page
- [ ] Final ZIP created
- [ ] Thumbnail PNG (1000×1000)
- [ ] Preview images (sample activity pages)
- [ ] SEO text file

### Per Product (Freebie):
- [ ] Freebie ZIP with 1 activity page from each level
- [ ] "Buy Full Product" promotional page
- [ ] Freebie SEO text

### Branding:
- [ ] Accent stripe uses correct level color
- [ ] Pack code and page numbers above border
- [ ] "Small Wins Studio" branding present
- [ ] Copyright footer on every page

### Formats (BACKLOG):
- [ ] Task Box version (photo box size)
- [ ] Task Box SEO text

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-05 | 2.1 | Added: Quick Start instructions, icons on storage labels, preview = sample activity, freebie spec, file folder + task box formats |
| 2026-02-05 | 2.0 | **DEFINITIVE SPEC** — Complete rewrite with exact level definitions for Matching/Find+Cover |
| 2026-02-05 | 1.1 | Added icon types, page layout details |
| 2026-02-05 | 1.0 | Initial specification |
