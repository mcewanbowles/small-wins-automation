import hashlib
import json
from pathlib import Path

# Load icons
p = Path(r'assets/themes/llama_llama_back_to_school/activity_images')
files = sorted([f for f in p.glob('*.png') if f.is_file() and not f.name.startswith('.')])
icon_names = [f.stem.replace('_', ' ').replace('-', ' ').title() for f in files]

# Load vocab
vocab = json.loads(open(r'assets/themes/llama_llama_back_to_school/book_vocab.json', encoding='utf-8').read())

# Simulate the NEW word-hash-based No trial selection
def _word_hash(name):
    return int(hashlib.md5(name.encode('utf-8')).hexdigest(), 16)

icon_names_sorted = sorted(icon_names)
no_count = min(4, len(icon_names) // 3)
no_trial_names = set(sorted(icon_names_sorted, key=_word_hash)[:no_count])

print(f"Total icons: {len(icon_names)}")
print(f"No trial count: {no_count}")
print(f"No trial names: {sorted(no_trial_names)}")
print()

# Show swap partners
for name in sorted(no_trial_names):
    other_names = [n for n in icon_names_sorted if n != name]
    swap_name = sorted(other_names, key=lambda n: (_word_hash(name + n), n))[0]
    print(f"  No trial: {name:20s} -> swaps with: {swap_name}")

print()
print("All cards (question -> icon shown -> answer):")
for name in icon_names_sorted:
    if name in no_trial_names:
        other_names = [n for n in icon_names_sorted if n != name]
        swap_name = sorted(other_names, key=lambda n: (_word_hash(name + n), n))[0]
        print(f"  Q about: {name:20s} -> shows: {swap_name:20s} -> NO")
    else:
        print(f"  Q about: {name:20s} -> shows: {name:20s} -> YES")
