# Small Wins Automation - Copilot Instructions

## Project Overview

This repository contains automated TpT (Teachers Pay Teachers) resource generators for Small Wins Studio. The system generates educational materials with multiple activity types based on themed content, specifically designed for AAC (Augmentative and Alternative Communication) and special education resources.

**Key Features:**
- Theme-based resource generation (e.g., "Brown Bear, Brown Bear, What Do You See?")
- Multiple activity types (matching, sorting, sequencing, wh-sentences, etc.)
- Dual output modes: color and black & white (BW) PDFs
- Automatic storage label generation for each activity
- Icon-based and symbol-supported materials

## Technology Stack

- **Language:** Python (primary generator language)
- **Output Format:** PDF generation for educational worksheets
- **Data Format:** JSON for theme configurations
- **Assets:** PNG images for icons, real images, and Boardmaker symbols
- **Version Control:** Git/GitHub

## Project Structure

```
/
├── .github/                    # GitHub configuration and Copilot instructions
├── assets/
│   ├── global/                 # Shared assets (AAC core, colors, etc.)
│   └── themes/                 # Theme-specific assets
│       └── {theme_name}/
│           ├── icons/          # Theme-specific icons
│           ├── real_images/    # Real photograph images
│           └── colouring/      # Black & white colouring images
├── docs/                       # Specifications and documentation
├── themes/                     # Theme configuration JSON files
└── README.md
```

## Theme Configuration

Themes are defined in JSON files under `/themes/` directory. Each theme must include:

- **theme_id:** Unique identifier (lowercase, underscore-separated)
- **theme_name:** Display name
- **fonts:** Primary and secondary font families
- **colours:** Primary, secondary, and accent colors (hex format)
- **core_icons:** AAC core vocabulary list
- **wh_words, colour_words, emotion_words, location_words:** Vocabulary categories
- **fringe_icons, real_image_icons, boardmaker_icons:** Icon mappings
- **Activity-specific settings:** Configuration for each activity type (find_cover, matching, sorting, wh_sentences, colouring, sequencing, book_adaptation)

## Coding Standards

### Generator Development

1. **Modular Design:** Each activity generator should be a separate, self-contained module
2. **Consistent Return Structure:** All generators must return a dictionary with:
   ```python
   {
       "color_pdf": "path/to/color.pdf",
       "bw_pdf": "path/to/bw.pdf",
       "storage_labels": {
           "color": "path/to/label_color.pdf",
           "bw": "path/to/label_bw.pdf"
       }
   }
   ```

3. **Import Pattern for Storage Labels:**
   ```python
   from generators.storage_labels import generate_storage_labels
   ```

4. **Output Directory Structure:**
   - All outputs must be saved to: `/output/{theme}/{activity}/`
   - Do NOT change folder structure
   - Maintain consistency across all generators

### Storage Label Integration (CRITICAL)

**GOAL:** Every activity generator must automatically produce storage labels (color + BW).

**Integration Requirements:**

1. **In Master Generator (`generate_all.py`):**
   - After each activity PDF is generated, call:
     ```python
     label_paths = generate_storage_labels(theme, activity_name)
     ```
   - Store returned paths in activity's output dictionary

2. **In Each Activity Generator:**
   - Import storage label generator
   - Add call to generate storage labels
   - Include returned paths in output dictionary
   - Example:
     ```python
     from generators.storage_labels import generate_storage_labels
     
     def generate(activity_inputs...):
         # Generate activity PDFs
         color_pdf = ...
         bw_pdf = ...
         
         # Generate storage labels
         labels = generate_storage_labels(theme, "Activity Name")
         
         return {
             "color_pdf": color_pdf,
             "bw_pdf": bw_pdf,
             "storage_labels": labels
         }
     ```

3. **Shared Helper (Optional but Recommended):**
   - Create in `utils/generator_helpers.py`:
     ```python
     def attach_storage_labels(theme, activity_name, output_dict):
         labels = generate_storage_labels(theme, activity_name)
         output_dict["storage_labels"] = labels
         return output_dict
     ```

### Design Constitution Compliance

**Core Principles:**

1. **Minimal Changes Only:**
   - Make surgical, targeted modifications
   - Do NOT redesign existing functionality
   - Do NOT refactor working code unless explicitly required
   - Keep scope strictly limited to requirements

2. **Integration Over Modification:**
   - Add integration hooks rather than rewriting
   - Maintain existing generator patterns
   - Preserve existing packaging and output structures
   - Do NOT modify storage label generator itself
   - Do NOT modify theme loader or dual-mode infrastructure

3. **Consistency:**
   - All activity generators must follow the same pattern
   - Return structures must be uniform across generators
   - File naming conventions must remain consistent

4. **Validation:**
   - Each activity must produce all four outputs:
     - Color PDF
     - BW PDF
     - Storage labels color PDF
     - Storage labels BW PDF
   - All paths must be returned to master generator

## Activity Types

The system supports multiple activity types:

- **Find/Cover:** Grid-based activities with errorless, mixed, and field-of-6 (six-option selection) levels
- **Matching:** Errorless, identical, and field-of-6 (six-option selection) matching activities
- **Sorting:** Category-based sorting (animals, people, other)
- **WH Sentences:** Question-based sentence activities with size scaling
- **Colouring:** Black & white images for coloring activities
- **Sequencing:** 3-step and 4-step sequencing activities
- **Book Adaptation:** Sentence frame-based book pages

## File Naming Conventions

- **Theme files:** `{theme_id}.json` (lowercase, underscore-separated)
- **Asset directories:** `{theme_id}/` (lowercase, underscore-separated)
- **Icon files:** `{descriptive_name}.png` (spaces allowed for readability)
- **Output files:** Follow generator-specific patterns

## Scope Guidelines for Changes

**DO:**
- Add integration hooks for new features
- Update return structures to include new output paths
- Create shared helpers for consistent patterns
- Follow existing generator patterns
- Maintain output directory structure

**DO NOT:**
- Modify existing core generators unless integrating new features
- Change packaging systems
- Modify theme loader infrastructure
- Redesign working functionality
- Change output folder structure
- Refactor code that is not part of the current task

## Full Product Suite Regeneration

When making changes that affect generators:

1. **Test with all activity types:** Ensure changes work across all generators
2. **Validate theme compatibility:** Test with at least one complete theme
3. **Check output structure:** Verify all four outputs (color PDF, BW PDF, color label, BW label) are generated
4. **Maintain backwards compatibility:** Existing themes and generators must continue to work

## Common Patterns

### Error Handling
- Validate theme configuration before generation
- Check for required assets before processing
- Provide clear error messages for missing resources

### Asset Loading
- Load theme-specific assets from `/assets/themes/{theme_id}/`
- Fall back to global assets when theme-specific not available
- Validate asset paths before use

### PDF Generation
- Always generate both color and BW versions
- Maintain consistent page sizing and formatting
- Use theme colors and fonts from configuration

## Notes for AI Assistants

- **Priority:** Storage label integration is critical for all generators
- **Scope:** This is an integration project, not a redesign project
- **Pattern:** Follow the established generator pattern consistently
- **Validation:** Every generator must return all four PDF paths
- **Structure:** Do not modify the output directory structure
