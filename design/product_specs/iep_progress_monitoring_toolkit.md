# IEP PROGRESS MONITORING TOOLKIT — PRODUCT SPECIFICATION
Small Wins Studio — Product-Specific Rules  
This file defines the exact layout, content, and structure required for the IEP Progress Monitoring Toolkit.

---

## 1. OVERVIEW
The IEP Progress Monitoring Toolkit is a "done for you" system to collect IEP data and produce progress-report-ready summaries.

**Product Components:**
- Print Pack (PDF): Quick-start guide + data collection sheets
- Tracker Template (CSV/XLSX): Digital tracking and summary tool

**Target Users:** Special education teachers, therapists, paraprofessionals  
**Use Case:** Track student progress on IEP goals, document interventions, prepare progress reports

---

## 2. BRAND & PRINT RULES

### 2.1 Branding
- Brand: Small Wins Studio
- Footer on every printable page: `© 2025 Small Wins Studio. All rights reserved.`
- Consistent with Design Constitution standards

### 2.2 Print-Friendly Requirements
- Minimal ink usage
- No clipart or decorative graphics
- Non-seasonal design
- High contrast for photocopying
- Clear, readable fonts

### 2.3 Page Layout
- Page size: US Letter (8.5" × 11") 
- Margins: 0.75" left, 0.5" right/top/bottom
- Footer: 9pt, light grey (#666666)
- Page numbers on all sheets (format: "Page X")

---

## 3. PRINT PACK CONTENT

### 3.1 Quick-Start Pages (2-3 pages)

**Page 1: Welcome & How to Use This Toolkit**
- Title: "IEP Progress Monitoring Toolkit"
- Subtitle: "Quick-Start Guide"
- Content sections:
  - What's included in this toolkit
  - How to choose the right data sheet
  - Tips for consistent data collection
  
**Page 2: Measurement Type Quick Reference**
- Table format showing:
  - Measurement type
  - When to use it
  - Example goals
- Measurement types:
  1. Trials/Accuracy (DTT-style)
  2. Frequency Count
  3. Duration Tracking
  4. Interval Recording
  5. ABC Observation
  6. Work Sample/Anecdotal
  7. Goal Snapshot

**Page 3: Privacy & Best Practices**
- Privacy reminder: Do not store identifying student info in shared files
- Best practices for data collection
- Tips for progress report preparation

### 3.2 Data Sheet Templates

Each data sheet must include:
- Clear title identifying the measurement type
- Student name field (blank line)
- Date field(s)
- Goal/Skill description field
- Structured data collection area (table or grid)
- Notes section
- Footer with copyright
- Page identifier

**Template 1: Trials/Accuracy (DTT-Style)**
- Grid layout: 10 trials × multiple sessions
- Columns: Trial #, Response (+/−), Prompt Level
- Prompt level key: I=Independent, V=Verbal, G=Gestural, PP=Partial Physical, FP=Full Physical
- Running accuracy calculation area
- Session summary section

**Template 2: Frequency Count**
- Date/Time tracking
- Tally mark area
- Total count per session
- Notes column
- Graph area (optional grid for plotting)

**Template 3: Duration Tracking**
- Start time / End time columns
- Total duration calculation
- Multiple session rows
- Average duration calculation area

**Template 4a: Interval Recording (5-minute)**
- Time intervals: 0-5, 5-10, 10-15, 15-20, 20-25, 25-30 (6 intervals)
- Mark occurrence: +/− or checkmarks
- Percentage calculation: (#intervals with behavior / total intervals) × 100

**Template 4b: Interval Recording (10-minute)**
- Time intervals: 0-10, 10-20, 20-30, 30-40, 40-50, 50-60 (6 intervals)
- Same calculation method

**Template 5: ABC Observation Form**
- Columns: Date/Time, Antecedent, Behavior, Consequence
- Multiple rows for observations
- Pattern analysis section at bottom

**Template 6: Work Sample / Anecdotal Log**
- Date field
- Activity/Task field
- Observation notes (large text area)
- Student performance notes
- Next steps section

**Template 7: Goal Snapshot Page**
- IEP Goal statement (multi-line)
- Current level of performance
- Supports/Accommodations needed
- Success criteria
- Progress notes section
- Review date field

---

## 4. TRACKER TEMPLATE (SPREADSHEET)

### 4.1 Design Philosophy
- Generic and easy to duplicate per student
- No macros (avoid school IT restrictions)
- Simple formulas only (SUM, AVERAGE, COUNT)
- Color-coded headers for clarity

### 4.2 Spreadsheet Structure

**Tab 1: Caseload Overview**
Columns:
- Student ID (generic: Student A, B, C)
- Goal Area (e.g., Communication, Math, Behavior)
- Goal Short Description
- Baseline Data
- Target Criterion
- Next Review Date
- Status (In Progress / Met / Modified)

**Tab 2: Session Log**
Columns:
- Date
- Student ID
- Goal ID
- Session Type (Direct, Observation, Probe)
- Score/Data Point
- Prompt Level Used
- Notes
- Entered By (initials)

**Tab 3: Auto Summary**
- Student dropdown or filter area
- Goal dropdown or filter area
- Summary statistics:
  - Total sessions logged
  - Average score
  - Latest 3 scores
  - Trend (improving/declining/stable)
  - Last session date
- Simple charts (optional, if XLSX)

**Tab 4: Next Steps & Notes**
Columns:
- Student ID
- Goal ID
- Observation Date
- Next Steps/Action Items
- Follow-up Date
- Completed (Y/N)

### 4.3 Format Requirements
- CSV templates (minimum viable)
- XLSX if supported (includes formulas)
- Headers in bold
- Color coding (light blue for headers)
- Print-friendly (fits on standard paper when printed)

---

## 5. GENERATOR REQUIREMENTS

### 5.1 Configuration-Driven Approach
- Use JSON config file to define:
  - Measurement types and their parameters
  - Interval lengths (5-min vs 10-min)
  - Number of trials/sessions
  - Column headers
  - Rating scales

### 5.2 Library Constraints
- Reuse existing PDF stack (no new PDF libraries)
- Standard Python libraries only
- CSV output: built-in `csv` module
- XLSX output: `openpyxl` if available, otherwise skip

### 5.3 Output Requirements
- Deterministic output naming
- Format: `iep_progress_monitoring_toolkit_sample.pdf`
- Format: `iep_tracker_sample.csv` (and `.xlsx` if supported)
- All outputs to `/samples/iep_progress_monitoring/`

### 5.4 Code Quality
- Type hints where appropriate
- Docstrings for all functions
- Config validation
- Error handling for missing dependencies

---

## 6. SAMPLE CONFIG STRUCTURE

```json
{
  "toolkit_name": "IEP Progress Monitoring Toolkit",
  "version": "1.0",
  "page_size": "letter",
  "margins": {
    "left": 0.75,
    "right": 0.5,
    "top": 0.5,
    "bottom": 0.5
  },
  "data_sheets": [
    {
      "type": "trials_accuracy",
      "title": "Trials/Accuracy Data Sheet (DTT-Style)",
      "trials": 10,
      "sessions": 5,
      "prompt_levels": ["I", "V", "G", "PP", "FP"]
    },
    {
      "type": "frequency_count",
      "title": "Frequency Count Data Sheet",
      "sessions": 10
    },
    {
      "type": "duration",
      "title": "Duration Tracking Data Sheet",
      "sessions": 8
    },
    {
      "type": "interval_5min",
      "title": "Interval Recording (5-Minute Intervals)",
      "intervals": 6,
      "session_length": 30
    },
    {
      "type": "interval_10min",
      "title": "Interval Recording (10-Minute Intervals)",
      "intervals": 6,
      "session_length": 60
    },
    {
      "type": "abc_observation",
      "title": "ABC Observation Form",
      "rows": 12
    },
    {
      "type": "work_sample",
      "title": "Work Sample / Anecdotal Log",
      "sections": 1
    },
    {
      "type": "goal_snapshot",
      "title": "Goal Snapshot Page"
    }
  ],
  "tracker_template": {
    "format": ["csv", "xlsx"],
    "tabs": ["caseload_overview", "session_log", "auto_summary", "next_steps"]
  }
}
```

---

## 7. ACCESSIBILITY & USABILITY

- High contrast for visibility
- Clear section headers
- Consistent layout across all sheets
- Large enough fields for handwriting
- Intuitive organization
- Professional appearance suitable for IEP meetings

---

## 8. DELIVERABLES CHECKLIST

- [x] Product specification document
- [ ] Sample configuration JSON
- [ ] Python generator script
- [ ] Sample PDF (print pack with all sheets)
- [ ] Sample CSV tracker template
- [ ] Sample XLSX tracker (if supported)
- [ ] Footer verification
- [ ] Print-friendliness verification
- [ ] Documentation in generator code

---

## 9. NOTES

- This toolkit is designed to be legally compliant and privacy-conscious
- No student-identifying information should be hard-coded
- Generic examples only (e.g., "Student A", "Goal 1")
- Suitable for photocopying and digital use
- Must work in restricted school IT environments (no macros, no internet connectivity required)
