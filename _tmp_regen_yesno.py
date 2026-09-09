import sys, os
sys.path.insert(0, '.')
os.chdir('.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from pathlib import Path

# Regenerate Yes/No Questions
from Studioforge._TRUTH.YES_NO import generate_yes_no_pack

images_folder = r'assets/themes/llama_llama_back_to_school/activity_images'
pack_code = 'LLB01'
theme_name = 'Llama Llama Back to School'
output_dir = r'assets/themes/llama_llama_back_to_school/OUTPUT'

print("=== Regenerating Yes/No Questions ===")
result = generate_yes_no_pack(
    images_folder=images_folder,
    pack_code=pack_code,
    theme_name=theme_name,
    output_dir=output_dir,
)
print(f"Result: {result}")

# Check output files
out = Path(output_dir)
for f in sorted(out.glob('*YesNo*')):
    import datetime
    stat = f.stat()
    print(f"  {f.name}: {datetime.datetime.fromtimestamp(stat.st_mtime)}, {stat.st_size} bytes")
