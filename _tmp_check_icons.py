from pathlib import Path
p = Path(r'assets/themes/llama_llama_back_to_school/activity_images')
files = sorted([f for f in p.glob('*.png') if f.is_file() and not f.name.startswith('.')])
for f in files:
    print(f'  {f.stem}')
print(f'\nTotal: {len(files)} icons')
