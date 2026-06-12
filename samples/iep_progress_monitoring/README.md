# IEP Progress Monitoring Toolkit

A comprehensive, "done for you" system for collecting IEP data and producing progress-report-ready summaries.

## Overview

The IEP Progress Monitoring Toolkit provides special education teachers, therapists, and paraprofessionals with professional-quality tools for tracking student progress on IEP goals. The toolkit includes both print and digital resources designed to be practical, efficient, and compliant with educational privacy requirements.

## Product Components

### 1. Print Pack (PDF)
A comprehensive 11-page PDF toolkit that includes:

#### Quick-Start Guide (3 pages)
- Welcome & How to Use This Toolkit
- Measurement Type Quick Reference
- Privacy & Best Practices

#### Data Collection Sheets (8 pages)
Seven different measurement types to match various IEP goals:

1. **Trials/Accuracy Data Sheet (DTT-Style)** - For discrete trial training and skills with clear correct/incorrect responses
2. **Frequency Count Data Sheet** - For counting how many times a behavior occurs
3. **Duration Tracking Data Sheet** - For measuring how long a behavior or activity lasts
4. **Interval Recording (5-Minute Intervals)** - For sampling behavior at 5-minute intervals over 30 minutes
5. **Interval Recording (10-Minute Intervals)** - For sampling behavior at 10-minute intervals over 60 minutes
6. **ABC Observation Form** - For analyzing antecedents, behaviors, and consequences
7. **Work Sample / Anecdotal Log** - For documenting complex skills and qualitative progress
8. **Goal Snapshot Page** - For tracking overall goal progress, supports, and success criteria

### 2. Digital Tracker Templates

#### CSV Format (4 files)
- `caseload_overview.csv` - Track students, goals, and review dates
- `session_log.csv` - Record daily session data and scores
- `auto_summary.csv` - Organize summary statistics
- `next_steps.csv` - Document action items and follow-ups

#### XLSX Format (1 file)
- `iep_tracker_sample.xlsx` - All four tabs in one formatted workbook with:
  - Color-coded headers (light blue)
  - Bold header fonts
  - Auto-sized columns
  - Ready for formulas and data entry

## Design Standards

### Branding
- **Brand:** Small Wins Studio
- **Footer:** © 2025 Small Wins Studio. All rights reserved.
- **Page Numbers:** Included on all sheets

### Print-Friendly Features
- Minimal ink usage
- High contrast for photocopying
- No clipart or decorative graphics
- Non-seasonal design
- Clear, readable fonts (Helvetica family)

### Page Layout
- **Page Size:** US Letter (8.5" × 11")
- **Margins:** 0.75" left, 0.5" right/top/bottom
- **Spacing:** Optimized for handwriting
- **Tables:** Clear gridlines and headers

## File Structure

```
small-wins-automation/
├── design/
│   └── product_specs/
│       └── iep_progress_monitoring_toolkit.md    # Complete specification
├── data/
│   └── iep_progress_monitoring/
│       └── sample_config.json                     # Configuration file
├── generators/
│   └── iep_progress_monitoring_toolkit_generator.py  # Python generator
└── samples/
    └── iep_progress_monitoring/
        ├── iep_progress_monitoring_toolkit_sample.pdf  # Print pack
        ├── iep_tracker_sample.xlsx                     # Excel template
        ├── caseload_overview.csv                       # CSV templates
        ├── session_log.csv
        ├── auto_summary.csv
        └── next_steps.csv
```

## Generator Usage

### Prerequisites
```bash
pip install reportlab openpyxl
```

### Running the Generator
```bash
python3 generators/iep_progress_monitoring_toolkit_generator.py
```

### Output
The generator creates:
- 1 PDF file (11 pages) with all print materials
- 4 CSV files for digital tracking
- 1 XLSX file with all tracker tabs

All files are saved to `samples/iep_progress_monitoring/`

## Configuration

The generator is driven by `data/iep_progress_monitoring/sample_config.json`, which allows customization of:

- Page layout and margins
- Fonts and colors
- Number of trials, sessions, and intervals
- Prompt levels and rating scales
- Tracker template columns
- Content sections

## Features

### Privacy-First Design
- No hard-coded student names or identifying information
- Uses generic labels (Student A, Student B, etc.)
- Reminder pages about FERPA compliance
- Suitable for shared digital environments

### Flexible Measurement Approaches
Choose the right tool for each IEP goal:
- **Accuracy-based goals:** Use Trials/Accuracy sheet
- **Behavioral frequency:** Use Frequency Count sheet
- **Time-based goals:** Use Duration Tracking sheet
- **Sampling approach:** Use Interval Recording sheets
- **Behavior analysis:** Use ABC Observation form
- **Complex skills:** Use Work Sample/Anecdotal Log
- **Overall tracking:** Use Goal Snapshot page

### Professional Quality
- Meets educational documentation standards
- Suitable for IEP meetings and progress reports
- Clear, organized layouts
- Consistent formatting across all materials

### IT-Friendly
- No macros or scripts (safe for school IT restrictions)
- Simple CSV format compatible with any spreadsheet software
- XLSX uses basic formatting only (no advanced features)
- Works offline (no internet connectivity required)

## Use Cases

1. **Special Education Teachers** - Track progress on multiple IEP goals across a caseload
2. **Speech-Language Pathologists** - Document therapy sessions and skill acquisition
3. **Occupational/Physical Therapists** - Monitor fine/gross motor skill development
4. **Behavior Specialists** - Analyze behavior patterns and intervention effectiveness
5. **Paraprofessionals** - Collect accurate data during instructional sessions

## Best Practices

### Data Collection
- Define success criteria clearly before starting
- Collect data at consistent times
- Record immediately after sessions
- Be specific about prompts and supports used

### Data Management
- Review data weekly to identify trends
- Use the tracker template for calculations
- Keep paper data sheets in secure storage
- Follow district FERPA guidelines

### Progress Reporting
- Calculate percentages using tracker summaries
- Include specific examples from anecdotal logs
- Note changes in supports or strategies
- Keep language objective and data-based

## Technical Details

### Dependencies
- Python 3.7+
- reportlab 4.0+ (PDF generation)
- openpyxl 3.0+ (XLSX generation, optional)

### PDF Generation
- Uses ReportLab PDF library
- Letter size pages (612 × 792 points)
- Helvetica font family for compatibility
- Tables built with reportlab.platypus.Table

### Spreadsheet Generation
- CSV: Standard Python csv module
- XLSX: openpyxl library with basic styling
- No formulas in CSV (manual calculations)
- XLSX ready for formula addition by users

## Compliance & Legal

- **Privacy:** Designed to comply with FERPA requirements
- **Copyright:** © 2025 Small Wins Studio. All rights reserved.
- **License:** Proprietary
- **Intended Use:** Educational data collection and progress monitoring

## Support & Customization

To customize the toolkit:
1. Edit `data/iep_progress_monitoring/sample_config.json`
2. Modify page content, table structures, or session counts
3. Run the generator to create updated outputs
4. Review and test before distribution

## Version History

- **Version 1.0** (February 2025)
  - Initial release
  - 8 data sheet types
  - 4-tab tracker template
  - Full quick-start guide

## Credits

Developed by Small Wins Studio for the special education community.

---

**For questions or issues, please refer to the product specification document at:**
`design/product_specs/iep_progress_monitoring_toolkit.md`
