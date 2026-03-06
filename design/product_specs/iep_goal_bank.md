# IEP GOAL BANK PRODUCT SPECIFICATION
Small Wins Studio — Product-Specific Rules  
This file defines the exact layout, structure, and behavior required for the IEP Goal Bank generator.

---

## 1. PRODUCT OVERVIEW

The IEP Goal Bank is a print-friendly, non-seasonal, SPED-focused resource providing structured goal banks organized by:
- **Domain** → **Subdomain** → **Level** → **Goal entries**

Each goal entry includes:
- domain (string)
- subdomain (string)
- level (enum): Emerging | Developing | Proficient | Generalisation
- goal_text (string; measurable)

Optional fields:
- criteria (string, e.g., "4/5 opportunities across 2 sessions")
- prompt_level (string, e.g., independent/minimal/moderate)
- measurement_type (string, e.g., trials/frequency/duration/interval/rubric)
- notes (string)

---

## 2. PAGE STRUCTURE

### Page Setup
- **Page size**: US Letter (8.5" × 11")
- **Orientation**: Portrait
- **Margins**: 0.75" left, 0.5" right/top/bottom
- **No borders**: Clean, uncluttered design suitable for printing in black & white
- **No decorative elements**: No seasonal themes, no clipart, no background images

### Header
- **Title**: "IEP Goal Bank" (18–22 pt, bold, Comic Sans MS or fallback)
- **Subtitle**: Domain name when filtered (14–16 pt, bold)
  - Example: "Communication" or "Literacy"
- **Optional tagline** (small, 9 pt): "Small Wins Studio — Classroom-Ready IEP Supports"
- Spacing: 0.2" below header before body content

### Body
- Goals grouped by subdomain with clear headings
- **Subdomain heading**: 12–13 pt, bold, with 0.15" space above and below
- Within each subdomain, goals ordered by level:
  - Emerging → Developing → Proficient → Generalisation
- Goal text: 10–11 pt, regular weight
- Line spacing: 1.2x for readability

### Footer
- **Left**: "© 2025 Small Wins Studio. All rights reserved."
- **Right**: "Page X of Y"
- **Font size**: 8–9 pt
- **Position**: Bottom of page, within margin area
- **Color**: Dark grey (#666666) for subtlety

---

## 3. TYPOGRAPHY

### Font Family
- **Primary**: Comic Sans MS (if available in environment)
- **Fallback**: Helvetica (documented as fallback for Linux environments without Comic Sans MS)
- **Rationale**: Comic Sans MS is accessible and friendly for educational materials; Helvetica provides professional clarity

### Font Sizes (minimum standards)
- Title: 18–22 pt, bold
- Subtitle: 14–16 pt, bold
- Tagline: 9 pt, regular
- Subdomain heading: 12–13 pt, bold
- Goal text: 10–11 pt, regular
- Footer: 8–9 pt, regular

---

## 4. GOAL ENTRY FORMAT

Each goal is displayed with consistent formatting:

**Level label in bold**, followed by goal text.

Example:
```
**Emerging:** The student will point to a named picture from a field of 2 with gestural prompting.

**Developing:** The student will point to a named picture from a field of 4 with minimal verbal prompting, with 80% accuracy across 3 consecutive sessions.
```

If optional fields are present, display on a second line in smaller italic text (9 pt):
- Format: `Criteria | Prompt | Measurement | Notes` (only fields that are present)

Example with optional fields:
```
**Proficient:** The student will verbally label 10 common objects independently.
  _Criteria: 4/5 opportunities | Prompt: Independent | Measurement: Frequency_
```

---

## 5. COLOR SCHEME

### Minimalist Approach
- **Primary text**: Black (#000000)
- **Headings**: Navy (#1E3A5F)
- **Footer**: Dark grey (#666666)
- **No accent colors**: Design must print clearly in black & white

### Accessibility
- High contrast for all text
- No reliance on color to convey information
- Clear hierarchy through size and weight, not color

---

## 6. PAGINATION RULES

### Multi-Domain PDF (All Domains)
- Each domain starts on a new page
- Domain name appears in the subtitle
- Goals for all subdomains within that domain appear on subsequent pages as needed

### Single-Domain PDF
- Domain name in subtitle
- All subdomains for that domain included
- Continuous pagination

### Footer Pagination
- Always shows "Page X of Y" on bottom right
- Uses total page count for the document

---

## 7. DATA STRUCTURE

Goals are stored in `/data/iep_goal_bank/sample_goals.json` with structure:

```json
{
  "domains": [
    {
      "name": "Communication",
      "subdomains": [
        {
          "name": "Receptive Language",
          "goals": [
            {
              "level": "Emerging",
              "goal_text": "The student will...",
              "criteria": "4/5 opportunities",
              "prompt_level": "Moderate",
              "measurement_type": "Trials",
              "notes": "Use visual supports"
            }
          ]
        }
      ]
    }
  ]
}
```

### Ordering Logic
- Domains: Alphabetical by name (or as ordered in JSON array)
- Subdomains: Alphabetical by name (or as ordered in JSON array)
- Levels: Fixed order → Emerging, Developing, Proficient, Generalisation
- Goals within same subdomain and level: As ordered in JSON array

---

## 8. EXTENSIBILITY

### Adding New Content
To add new domains, subdomains, or goals:
1. Edit `/data/iep_goal_bank/sample_goals.json`
2. Follow the existing JSON structure
3. Ensure level values match enum: Emerging | Developing | Proficient | Generalisation
4. Re-run generator

### Future Enhancements (Not Implemented Now)
The design supports future connections to:
- **Data collection sheets**: Goals could link to matching progress monitoring sheets
- **Skill progression maps**: Goals could reference developmental sequences
- **Accommodation banks**: Goals could suggest related accommodations
- **Standards alignment**: Goals could map to state standards or Common Core

Implementation notes for future:
- Add "goal_id" field to each goal for cross-referencing
- Create separate JSON files for related resources
- Use goal_id as foreign key in related resources

---

## 9. GENERATOR IMPLEMENTATION

### CLI Interface
```bash
python generators/iep_goal_bank_generator.py --output all
python generators/iep_goal_bank_generator.py --output communication
python generators/iep_goal_bank_generator.py --output literacy
```

### Required Outputs
1. `/samples/iep_goal_bank/iep_goal_bank_sample_all_domains.pdf`
2. `/samples/iep_goal_bank/iep_goal_bank_sample_communication.pdf`
3. `/samples/iep_goal_bank/iep_goal_bank_sample_literacy.pdf`

### PDF Generation Stack
- Use ReportLab (standard Python PDF library)
- No additional PDF libraries required
- Follows repository convention for PDF generation

---

## 10. SAMPLE DATASET REQUIREMENTS

Minimum sample dataset:
- **2 domains**: Communication + Literacy
- **2 subdomains per domain** (4 total)
- **3–4 goals per subdomain** across different levels
- **At least one goal** uses optional fields (criteria/prompt/measurement_type/notes)

Goals must be:
- Original content (not copied from commercial products)
- General and classroom-appropriate
- Measurable and observable
- Aligned to special education best practices

---

## 11. QUALITY STANDARDS

### Print Quality
- All text must be crisp and readable at 10 pt minimum
- No pixelated or blurry elements
- Clean page breaks (no orphaned headings)

### Content Quality
- Goals written in professional IEP language
- Measurable and observable behaviors
- Appropriate developmental progression across levels
- Practical for classroom implementation

### Accessibility
- High contrast throughout
- Clear hierarchy
- Logical reading order
- Prints well in black & white (tested)

---

## 12. COMPLIANCE WITH GLOBAL STANDARDS

### Design Constitution Overrides
This product diverges from the global Design Constitution in:
- **No border**: IEP documents use clean, borderless design
- **No accent stripe**: Professional document format
- **Footer format**: Simplified copyright notice instead of pack code format
- **Page margins**: 0.75" left for binding-friendly layout

### Retained Standards
- High contrast and accessibility
- Clean, professional appearance
- Page size: US Letter
- Print-friendly design

---

## 13. VERSION HISTORY

- v1.0 (2025-02-02): Initial specification
  - Primary font: Comic Sans MS (preferred for accessibility)
  - Fallback font: Helvetica (for environments without Comic Sans MS)
  - Page size: US Letter (8.5" × 11")
  - Two sample domains: Communication and Literacy
