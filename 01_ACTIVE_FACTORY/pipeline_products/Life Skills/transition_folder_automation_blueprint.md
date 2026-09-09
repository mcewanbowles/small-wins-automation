# Transition Folder Automation Blueprint

## Goal
Ship practical, independent life-skills packs that are easy for teachers to run in morning folders, stations, and transition classes.

## Product format (single theme)
1. Cover + teacher guide
2. 12 printable student tasks (3 levels x 4 tasks each)
3. Cutout/answer card pages
4. Answer key pages
5. Digital deck mapping (Google Slides + PowerPoint)
6. Quiz export (Baamboozle-style question bank)

## Recommended first themes
1. Train & Bus Timetable Basics
2. Vending Machine Money Math
3. Grocery List Shopping and Coins
4. Community QR Clue Hunt (reading signs + help seeking)

## Difficulty model
- Level A: Match icon/word/number
- Level B: Choose from 3 options
- Level C: Open response (calculate/justify)

## Automation input schema
Use `transition_folder_task_template.csv` with one row per task card.
Required columns include:
- product_key, theme, level, activity_type, prompt_text
- option_a/option_b/option_c, correct_answer
- icon filenames, worksheet layout metadata

## Placeholder policy
If icon missing:
1. Keep build passing with placeholder filename.
2. Append missing icon to placeholder manifest.
3. Render [Icon Placeholder] in templates.
4. Rebuild without changing task IDs.

## QA rules (must-pass)
- All text boxes inside page border with padding.
- Prompt/option text does not overlap icons.
- Footer remains inside safe border area.
- Cutout cell grid fully in-bounds.
- Every task has answer key mapping.
- Digital export rows preserve task order.

## Border-safe layout standards
- Keep consistent page border margin.
- Keep top header zone clear from task content.
- Maintain minimum vertical gap between prompt, options, and footer.
- Auto-fit fonts before truncation.

## Digital replication map
For each task row:
- Printable page ID -> Slides slide ID -> PowerPoint slide ID -> Quiz question ID
- This allows bulk updates from a single task CSV.

## Production flow
1. Fill task CSV
2. Validate schema
3. Generate printable pack
4. Run QA
5. Export Slides/PPT source rows
6. Export quiz CSV
7. Package and thumbnail generation
