import sys, os
sys.path.insert(0, '.')
os.chdir('.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pathlib import Path

# Regenerate AAC Board
print("=== Regenerating AAC Board ===")
from Studioforge._TRUTH.AAC_BOARD import generate_aac_board_pack
result = generate_aac_board_pack(
    images_path=r'assets/themes/llama_llama_back_to_school/activity_images',
    pack_code='LLB01',
    book_title='Llama Llama Back to School',
)
print(f"AAC Board result: {result}")

# Regenerate Adapted Book
print("\n=== Regenerating Adapted Book ===")
from Studioforge._TRUTH.ADAPTED_BOOK_GENERATOR import build_pdf
try:
    color_pdf, bw_pdf = build_pdf('llama_llama_back_to_school', 'Llama Llama Back to School', 'LLB01')
    print(f"Adapted Book color: {color_pdf}")
    print(f"Adapted Book BW: {bw_pdf}")
except Exception as e:
    print(f"Adapted Book error: {e}")
    import traceback
    traceback.print_exc()
