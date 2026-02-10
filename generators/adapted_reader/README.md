# Adapted Reader Generator

Creates literacy-focused Adapted Reader PDFs with two difficulty levels and dual-mode output (color + B&W).

## Features

### Two Reading Levels

**Level A: Errorless Reading (Point to the word)**
- Student reads sentence with target word represented by icon
- Large icon displayed below for pointing/touching
- Errorless learning approach - correct answer is shown
- Perfect for beginning readers and SPED students

**Level B: Cloze Reading (Fill in the blank)**
- Sentence with blank replacing target word
- 3 icon choices (target + 2 distractors)
- Student must choose correct icon to complete sentence
- More challenging comprehension task

### Dual-Mode Output

- **Color PDFs**: Full color for lamination and interactive use
- **B&W PDFs**: Black & white for cost-effective printing and coloring activities

### Automatic or Custom Content

- **Default Mode**: Automatically generates pages from icon filenames (Brown Bear sequence if detected)
- **Manifest Mode**: Use JSON file to define exact sentences, target words, and distractors

## Installation

```bash
pip install reportlab pillow
```

## Usage

### Basic Usage (Auto-generated content)

```bash
python generators/adapted_reader/adapted_reader.py \
    --icons_dir "assets/themes/brown_bear/icons" \
    --out_dir "OUTPUT/readers" \
    --theme "Brown Bear"
```

### With Custom Manifest

```bash
python generators/adapted_reader/adapted_reader.py \
    --icons_dir "assets/themes/brown_bear/icons" \
    --out_dir "OUTPUT/readers" \
    --theme "Brown Bear" \
    --manifest "templates/adapted_reader_manifest.json"
```

### Command-Line Arguments

- `--icons_dir`: Path to folder containing icon images (PNG recommended)
- `--out_dir`: Output directory for generated PDFs
- `--theme`: Theme name (used in titles and filenames)
- `--brand`: Brand name for footer (default: "Small Wins Studio")
- `--manifest`: Optional path to JSON manifest file

## Output Files

For theme "Brown Bear", generates 4 PDFs:

1. `brown_bear_adapted_reader_level_a_color.pdf`
2. `brown_bear_adapted_reader_level_a_bw.pdf`
3. `brown_bear_adapted_reader_level_b_color.pdf`
4. `brown_bear_adapted_reader_level_b_bw.pdf`

## Manifest Format

Create a JSON file defining your custom pages:

```json
{
  "pages": [
    {
      "sentence": "I see a Red Bird.",
      "target_word": "Red Bird",
      "target_icon": "red_bird",
      "distractors": ["yellow_duck", "blue_horse"]
    },
    {
      "sentence": "The Yellow Duck is swimming.",
      "target_word": "Yellow Duck",
      "target_icon": "yellow_duck",
      "distractors": ["red_bird", "green_frog"]
    }
  ]
}
```

### Manifest Fields

- `sentence`: The full sentence to display
- `target_word`: The word to be replaced with icon (Level A) or blank (Level B)
- `target_icon`: Icon filename (without extension) for the target word
- `distractors`: Array of icon filenames to use as wrong choices in Level B

## Educational Applications

### SPED/Special Education

- **Errorless Learning**: Level A provides immediate visual support
- **Scaffolded Learning**: Progress from Level A (errorless) to Level B (choice)
- **AAC Support**: Icons support students using augmentative communication
- **Visual Supports**: Strong visual component aids comprehension

### Literacy Development

- **Sight Word Practice**: Reinforce key vocabulary
- **Sentence Structure**: Model simple sentence patterns
- **Reading Comprehension**: Check understanding through cloze activities
- **Engagement**: Interactive pointing/choosing maintains interest

### Classroom Use

- **Independent Work Stations**: Students can work through levels independently
- **Small Group Instruction**: Perfect for guided reading groups
- **Assessment**: Level B serves as comprehension check
- **Differentiation**: Two levels meet varying student needs

## Design Features

- A4 page size (210mm × 297mm)
- Professional Small Wins Studio branding
- Clear, large fonts for readability
- Navy blue borders and accents
- Consistent layout across all pages
- Footer with theme, level, mode, and page number

## Tips

1. **Icon Quality**: Use high-resolution PNG images with transparent backgrounds
2. **Icon Names**: Use lowercase with underscores (e.g., `red_bird.png`)
3. **Consistent Sizing**: Keep icon dimensions similar for best results
4. **Test First**: Generate with default content first, then customize with manifest
5. **Print Settings**: Use "Fit to Page" when printing for best results

## Example: Brown Bear Theme

The generator automatically detects Brown Bear icons and creates appropriate sentences:

- "I see a Red Bird."
- "I see a Yellow Duck."
- "I see a Blue Horse."
- etc.

Each sentence features the target animal with appropriate distractors for Level B.

## Troubleshooting

**No PDFs generated?**
- Check that `--icons_dir` path is correct
- Ensure icons directory contains PNG/JPG files
- Verify you have write permissions to `--out_dir`

**Icons not appearing?**
- Icon filenames should match those referenced in sentences
- Remove spaces from filenames (use underscores)
- Ensure icons are in supported formats (PNG, JPG, JPEG, WEBP)

**Manifest errors?**
- Validate JSON syntax using online JSON validator
- Ensure all icon names in manifest exist in icons directory
- Check that target_icon and distractors reference valid files

## License

Created by Small Wins Studio for TPT educational resources.
