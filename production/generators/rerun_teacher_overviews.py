"""Re-run Teacher Overviews for the LLRP suite with final product names.

Updates product_name in each teacher_overview_examples/*.json to match the
canonical packager names, then regenerates every overview PDF into
Studioforge/_REVIEW/Teacher Overview Template 04-09/<subfolder>/.

Usage: python production/generators/rerun_teacher_overviews.py
"""

from __future__ import annotations

import json
from pathlib import Path

from production.generators.generate_teacher_overview import build_teacher_overview

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "production" / "generators" / "teacher_overview_examples"
OUT_BASE = ROOT / "Studioforge" / "_REVIEW" / "Teacher Overview Template 04-09"

# json file stem -> (overview output subfolder, final product name)
RENAMES = {
    "boardready_aac": ("boardready_aac", "AAC Communication Board"),
    "matching": ("matching", "Matching Cards"),
    "book_participation_pieces": ("book_participation_pieces", "Interactive Book Participation Pieces"),
    "sentence_building": ("sentence_building", "AAC Sentence Building"),
    "sequencing": ("sequencing", "Story Sequencing"),
    "yes_no_questions": ("yes_no_questions", "Yes/No Questions"),
    "inferencing_cards": ("inferencing_cards", "Clue, Think, Infer: Inferencing Cards"),
    "vocabulary_snap": ("vocabulary_snap", "Vocabulary Snap"),
    "syllable_awareness": ("syllable_awareness", "Syllable Awareness"),
    "decoding": ("decoding", "CVC Decode & Build"),
    "story_grammar": ("story_grammar", "Story Grammar & Retell"),
    "word_search": ("word_search", "Differentiated Word Search"),
    "bingo": ("bingo", "Differentiated Bingo"),
    "sorting": ("sorting", "Reason & Sort: Category Sorting"),
    "print_detective": ("print_detective", "Print Detective: Letters, Words & First Sounds"),
}

# Full overview spec for Print Detective (replaces the minimal quick-start data).
PRINT_DETECTIVE_OVERVIEW = {
    "product_name": "Print Detective: Letters, Words & First Sounds",
    "theme_name": "Llama Llama Red Pajama",
    "product_code": "LLRP-PD-LAUNCH",
    "version": "1.0",
    "page_counts": {"color": 9, "bw": 9},
    "formats": ["Color PDF", "B&W PDF"],
    "levels": ["Letter or Not a Letter", "Letter or Word", "First Sound Match", "Reading Detective"],
    "included": [
        "2 sort mats (Letter/Not-a-Letter, Letter/Word)",
        "2 cut-card sheets with theme vocabulary",
        "First-sound match mat + 7 picture cards",
        "Reading Detective page: directionality + concept of word",
        "Answer key",
    ],
    "best_for": ["print concepts", "letter knowledge", "emergent readers", "AAC users"],
    "access": ["Point or place cards", "AAC: 'letter', 'word', 'same'", "Dry-erase marker for Level 4"],
    "preparation": {"label": "Print and cut", "materials": "cardstock, scissors, laminator (optional)", "time": "10 minutes"},
    "teaching_steps": [
        {"title": "Sort", "detail": "Levels 1-2: student sorts each card and says the rule aloud."},
        {"title": "Match", "detail": "Level 3: say the picture name, stretch the first sound, place it under the letter."},
        {"title": "Track", "detail": "Level 4: follow the arrow, touch each word, find word boundaries."},
    ],
    "scarborough": {
        "strands": ["Alphabetic Principle", "Print Concepts"],
        "statement": "Fills the suite gap between phonological awareness and decoding; all words and pictures reuse the reviewed LLRP vocabulary and icons.",
        "tier": "lower",
    },
    "book_companion": True,
    "book_not_included": True,
    "pcs_used": True,
    "preview_image": "assets/themes/llama_llama_red_pajama/OUTPUT/LLRP-PD-LAUNCH_PrintDetective_COLOR.pdf",
}


def main() -> None:
    for stem, (subfolder, name) in RENAMES.items():
        data_path = EXAMPLES / f"{stem}.json"
        if stem == "print_detective":
            data = PRINT_DETECTIVE_OVERVIEW
            data_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        else:
            data = json.loads(data_path.read_text(encoding="utf-8"))
            data["product_name"] = name
            data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        out_dir = OUT_BASE / subfolder
        manifest = build_teacher_overview(data_path, out_dir)
        print(f"OK  {name} -> {manifest['files']['pdf']}")


if __name__ == "__main__":
    main()
