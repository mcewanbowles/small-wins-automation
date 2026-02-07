# Universal Sorting Toolkit with AAC Edge Strips

A professional sorting mats generator with AAC (Augmentative and Alternative Communication) core word prompts integrated around the edges.

## Overview

This generator creates landscape sorting mats perfect for special education, AAC modeling, and general classroom use. Each mat includes 16 core word buttons (with icons) around the edges to facilitate communication during sorting activities.

## Features

### Sorting Mat Types

1. **2-Way Sorting** - Binary classification
   - Examples: Flies/Doesn't fly, Big/Small, Happy/Sad
   - Large boxes for easy card placement
   
2. **3-Way Sorting** - Triple classification
   - Examples: 2 legs/4 legs/No legs, Beginning/Middle/End
   - Three equal columns
   
3. **Yes/No Sorting** - Question-based sorting
   - Examples: Is it green? Does it swim?
   - Encourages critical thinking

### AAC Edge Strip (16 Core Words)

**Top Row (8 buttons):**
- PUT, DIFFERENT, FINISHED, AGAIN, WAIT, I THINK, SAME, HELP

**Bottom Row (8 buttons):**
- STOP, LIKE, DON'T LIKE, FUNNY, UH-OH, WHOOPS, MORE, YES

Each button includes:
- AAC icon (from assets/global/aac_core/)
- Text label
- Rounded border for easy pointing

### Dual-Mode Output

- **Color PDFs** - For lamination and classroom display
- **B&W PDFs** - For cost-effective printing and student coloring

## Installation

```bash
pip install reportlab pillow
```

## Usage

### Default Categories

```bash
python generators/universal_sorting/universal_sorting_aac.py \
    --out_dir "OUTPUT/sorting" \
    --brand "Small Wins Studio"
```

### Custom Categories

```bash
python generators/universal_sorting/universal_sorting_aac.py \
    --out_dir "OUTPUT/sorting" \
    --brand "Small Wins Studio" \
    --categories "templates/universal_sorting_categories.json"
```

### Custom AAC Directory

```bash
python generators/universal_sorting/universal_sorting_aac.py \
    --out_dir "OUTPUT/sorting" \
    --aac_dir "path/to/aac/images"
```

## Output

Generates 2 PDFs:
- `universal_sorting_mats_aac_color.pdf` - Full color version
- `universal_sorting_mats_aac_bw.pdf` - Black & white version

Each PDF contains:
- Instruction page
- All 2-way sorting mats
- All 3-way sorting mats
- All Yes/No sorting mats

## Categories JSON Format

```json
{
  "two_way": [
    ["Category A", "Category B"],
    ["Happy", "Sad"]
  ],
  "three_way": [
    ["2 legs", "4 legs", "No legs"]
  ],
  "yes_no": [
    ["Is it green?"],
    ["Does it swim?"]
  ]
}
```

## Educational Applications

### AAC Modeling

Use the edge strip buttons to model core vocabulary:
- **PUT** - "Let's put the bird here"
- **I THINK** - "I think this goes in big"
- **SAME** - "These are the same"
- **DIFFERENT** - "This one is different"
- **HELP** - "Can you help me?"
- **FINISHED** - "We're finished sorting"
- **AGAIN** - "Let's do it again"

### SPED/Special Education

- **Errorless Learning:** Pre-place one example in each box
- **Visual Supports:** AAC icons support non-verbal students
- **Scaffolding:** Gradually reduce support as skills develop
- **Communication Practice:** Natural opportunities for AAC use

### Classroom Differentiation

**Level 1 (Errorless):**
- Teacher places examples
- Student matches identical items

**Level 2 (Scaffolded):**
- Verbal cues provided
- Student sorts with prompts

**Level 3 (Independent):**
- Student sorts without help
- May use AAC to explain

**Level 4 (Extension):**
- Student explains reasoning
- "I think... because..."
- Critical thinking skills

## Customization Ideas

### Theme Integration

Use with any theme by adding matching picture cards:
- Animals (zoo, farm, ocean)
- Transportation
- Food groups
- Weather
- Emotions
- Shapes and colors

### Cross-Curricular

**Science:**
- Living/Non-living
- Solid/Liquid/Gas
- Carnivore/Herbivore/Omnivore

**Math:**
- Odd/Even
- Greater than 10 / Less than 10
- 2D shapes / 3D shapes

**Literacy:**
- Letter sounds
- Syllable sorting
- Real words / Nonsense words

**Social Studies:**
- Past/Present/Future
- Wants/Needs
- Community helpers

## AAC Core Words

The 16 core words were selected based on:
- High frequency in communication
- Usefulness during sorting activities
- AAC research and best practices
- Applicability across contexts

All words have corresponding AAC icons for:
- Visual support
- Non-verbal communication
- Multi-modal learning

## Tips for Success

1. **Laminate for durability** - Use color PDFs
2. **Use velcro dots** - Attach to mat and cards
3. **Model AAC consistently** - Point as you speak
4. **Pause for responses** - Give time to communicate
5. **Celebrate attempts** - Encourage all communication
6. **Start simple** - Begin with 2-way sorting
7. **Add complexity gradually** - Move to 3-way when ready

## File Structure

```
generators/universal_sorting/
├── universal_sorting_aac.py    # Main generator
└── README.md                   # This file

templates/
└── universal_sorting_categories.json  # Example categories

OUTPUT/sorting/
├── universal_sorting_mats_aac_color.pdf
└── universal_sorting_mats_aac_bw.pdf
```

## Technical Details

- Page Size: A4 Landscape (297mm × 210mm)
- AAC Buttons: 18mm height, rounded corners
- AAC Icons: 14mm size
- Sort Boxes: 3mm bold border, 16mm corner radius
- Font: Helvetica (standard across all products)
- Resolution: Vector-based for crisp printing

## Troubleshooting

**No AAC icons showing:**
- Check that aac_dir path is correct
- Verify PNG files exist in assets/global/aac_core/
- Generator will fall back to text-only if icons not found

**Categories not loading:**
- Check JSON syntax
- Ensure file path is correct
- Use default categories if file missing

**PDF quality issues:**
- PDFs are vector-based and scale infinitely
- Print at 100% scale for intended size
- Use high-quality printer settings

## License

MIT License - Small Wins Studio

## Support

For issues or questions:
- Check this README
- Review example categories JSON
- Examine generated PDFs
- Test with default settings first

---

**Created with ❤️ for teachers, therapists, and students**
