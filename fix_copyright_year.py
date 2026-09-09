"""Fix all hard-coded © 2025 strings in generator files to use © 2026."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Files with hard-coded © 2025 from the audit
FILES_TO_FIX = [
    "production/generators/generators/WORD_SEARCH_GENERATOR.py",
    "production/generators/generators/TOKEN_BOARDS.py",
    "production/generators/generators/generate_freebie_new.py",
    "production/generators/create_tpt_packages_updated.py",
    "production/generators/generators/generate_matching_constitution.py",
    "production/generators/generate_text_matching_bonus.py",
    "production/generators/generators/generate_quick_start_instructions.py",
    "production/generators/generators/generate_product_covers_windows.py",
    "production/generators/generators/generate_product_covers_marketing.py",
    "production/generators/generators/generate_level_covers_with_preview.py",
    "production/generators/generators/generate_freebie.py",
    "production/generators/generators/generate_final_products_complete.py",
    "production/generators/generators/generate_cover_page_new.py",
    "production/generators/generators/generate_covers_amended.py",
    "production/generators/generators/generate_cover_page.py",
    "production/generators/generators/SENTENCE_STRIPS_MODULAR_GENERATOR.py",
    "production/generators/generators/AAC_BOARD_GENERATOR.py",
    "production/generators/generators/STORY_MAPS_HIGHCONTRAST.py",
    "production/generators/generators/TOKEN_BOARDS_HIGHCONTRAST.py",
    "production/generators/generators/AAC_BOARD_WRAPPER.py",
    "production/generators/generators/STORAGE_LABELS.py",
]

fixed = 0
errors = 0

for rel in FILES_TO_FIX:
    p = ROOT / rel
    if not p.exists():
        print(f"SKIP (not found): {rel}")
        continue
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        # Replace © 2025 with © 2026 (various formats)
        new_content = content
        # Match: © 2025, (c) 2025, Copyright 2025, COPYRIGHT 2025
        new_content = re.sub(r'©\s*2025', '© 2026', new_content)
        new_content = re.sub(r'\(c\)\s*2025', '(c) 2026', new_content, flags=re.IGNORECASE)
        new_content = re.sub(r'Copyright\s+2025', 'Copyright 2026', new_content, flags=re.IGNORECASE)
        new_content = re.sub(r'COPYRIGHT\s+2025', 'COPYRIGHT 2026', new_content, flags=re.IGNORECASE)
        # Also fix standalone "2025" in copyright context strings like "© 2025 Small Wins"
        new_content = re.sub(r'2025\s+Small\s+Wins', '2026 Small Wins', new_content)
        
        if new_content != content:
            p.write_text(new_content, encoding="utf-8")
            # Count replacements
            count = content.count("2025") - new_content.count("2025")
            print(f"OK   {rel} ({count} replacement(s))")
            fixed += 1
        else:
            # Check if 2025 still appears - might be in different format
            if "2025" in content:
                # Find remaining 2025 references for manual review
                lines_with_2025 = [(i+1, line.strip()) for i, line in enumerate(content.split('\n')) if "2025" in line and "NEVER" not in line and "#" not in line[:5]]
                if lines_with_2025:
                    print(f"WARN {rel} - 2025 still in: {lines_with_2025[:3]}")
                else:
                    print(f"SKIP {rel} (only comments)")
            else:
                print(f"SKIP {rel} (no 2025 found)")
    except Exception as e:
        print(f"ERR  {rel}: {e}")
        errors += 1

print(f"\nDone: {fixed} fixed, {errors} errors")
