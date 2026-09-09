---
title: SPED Gold Mine — Product Draft v1
owner: Small Wins Studio
status: Draft for review
source_doc: Pipeline Products/SPED_TPT_Strategy_Guide.docx
---

# SPED Gold Mine — Draft Product Blueprint

## 1) Product Direction (Recommended)

**Primary product family:**
1. **SPED IEP Caseload Binder** (print + editable)
2. **SPED Data Collection System** (print + editable)
3. **SPED Life Skills Pack** (print + editable)
4. **Mega Bundle** (all combined)

**Best launch sequence (recommended):**
1. Free 5-page **IEP Snapshot Sampler**
2. IEP Binder
3. Data Collection Bundle
4. Life Skills Pack
5. Mega Bundle

This gives fast validation and review momentum before full bundle release.

---

## 2) Small Wins Design System (Applied)

Use current branded patterns already in repo:
- Rounded light-blue outer border
- Teal/orange section accents
- Navy headings, clean hierarchy
- Footer format with Small Wins + PCS license line
- Consistent spacing and non-cluttered page composition

### Color roles
- **Navy:** `#1E3A5F` (titles + structure)
- **Teal:** `#2CA6A4` (section accents + key labels)
- **Light blue border:** `#A0C4E8` (outer frame)
- **Warm accent:** `#F5A623` / section variant colors as needed

### Section color map (clear scanning)
- **IEP Management:** blue-leaning accent
- **Data Collection:** orange accent
- **Life Skills:** green accent

### Typography
- Follow existing Small Wins typography behavior (Comic Sans preferred/fallback chain already implemented in utilities).
- Keep body text readable and print-safe.

---

## 3) Page Architecture Template (All Pages)

Each page follows one reusable structure:

1. **Header bar**
   - Section name + page title
2. **Info strip**
   - Student Name | Date | Teacher/Recorder
3. **Main content body**
   - Form, tracker, checklist, or worksheet block
4. **Footer**
   - Product code + page number + copyright/PCS line

### Layout constraints
- 0.5 in print-safe margin baseline
- Strong gridlines for data-entry pages
- Generous white space
- Avoid dense text blocks

---

## 4) Draft Scope (Phase 1 Build)

### A) Freebie (5 pages)
**IEP Snapshot Sampler**
- Cover
- IEP at a Glance
- Parent Communication Log
- Goal Progress Snapshot
- Meeting Notes

### B) Paid Product 1 — IEP Caseload Binder (v1 target: 30 pages)
Core pages:
- Caseload master sheet
- IEP due date planner (monthly)
- Student profile / at-a-glance
- Annual goals tracking
- Accommodations/modifications checklist
- Service minutes log
- Meeting agenda + notes + checklist
- Parent contact + communication logs
- Compliance deadline tracker
- Para schedule + duties

### C) Paid Product 2 — Data Collection Bundle (v1 target: 40 pages)
Core sheets:
- Trial-by-trial
- Task analysis
- Frequency
- Duration
- Interval (whole/partial/MTS)
- Rate
- Multi-student quick sheet
- ABC data
- Prompt fading tracker
- Goal progress graphs
- Monthly progress summary

### D) Paid Product 3 — Life Skills Pack (v1 target: 40 pages)
Core worksheets:
- Personal info + self-advocacy scripts
- Community sign reading
- Menu/price reading
- Schedule reading
- Money (coins/bills/change)
- Budget basics
- Safety routines
- Hygiene routines
- Vocational readiness pages

---

## 5) Output Targets

### Print outputs (PDF)
- `SPED_IEP_Binder_Printable.pdf`
- `SPED_Data_Collection_Printable.pdf`
- `SPED_Life_Skills_Printable.pdf`
- `SPED_MEGA_BUNDLE_ALL.pdf`
- `SPED_IEP_Snapshot_Freebie.pdf`

### Editable outputs
- `SPED_IEP_Binder_Editable.pptx`
- `SPED_Data_Collection_Editable.pptx`
- `SPED_Life_Skills_Editable.pptx`

### Listing assets
- Preview PNGs/PDF
- Cover thumbnails (280x280, 500x500)
- Quick Start PDF
- TOU/Credits PDF
- TpT description text

---

## 6) Product Positioning Copy (Draft)

### Working title
**The Ultimate SPED Teacher System | Editable IEP Binder + Data Collection + Life Skills | Digital + Printable**

### Promise statement
A complete special education organization and progress-monitoring system designed to reduce paperwork stress and increase instructional clarity.

### What’s included (draft)
- IEP management forms and planning tools
- Data collection sheets for goals, behavior, and progress
- Functional life-skills worksheets
- Print + editable formats
- Consistent design across all pages for fast use

---

## 7) Technical Build Plan (Repo-Aligned)

### Reuse-first approach
- Reuse existing frame utilities and footer style from current generators.
- Create one page-template engine, then feed section/page configs.

### Proposed files
- `production/generators/generate_sped_gold_mine_constitution.py`
- `production/generators/create_tpt_packages_sped_gold_mine.py`
- `production/generators/sped_gold_mine_config.json` (or yaml)

### Build principles
- Config-driven text/content
- Shared style tokens (color, spacing, header/footer)
- Deterministic naming and output folders
- Preview generation integrated in same run

---

## 8) Review Questions for You

1. Do you want **v1 to launch as 3 products + mega bundle**, or start with only freebie + IEP binder?
2. Do you want **only one visual theme first** (recommended), then themed variants later?
3. Should I make the first build **fillable PDF forms** now, or first ship printable + editable PPTX and add fillable fields in v2?

---

## 9) Recommended Next Step

**Best next move:** build the **Freebie + IEP Binder v1** first using this style system, generate previews, and review layout before scaling to 200+ pages.

This de-risks design quickly and keeps speed high.
