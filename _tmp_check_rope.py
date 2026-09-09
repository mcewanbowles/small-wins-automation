import sys, os
sys.path.insert(0, '.')
os.chdir('.')
from pathlib import Path
from PIL import Image

# Simulate the rope image search logic from generate_teacher_cover_page
DPI = 300
scar_strand = "Language Structures"
rope_key = ("word_recognition" if scar_strand == "Word Recognition" else "language_comprehension")
print(f"rope_key = {rope_key}")

variant_dirs = [
    Path("assets/branding/rope/realistic"),
    Path("assets/covers"),
    Path("assets/branding/rope"),
    Path("Studioforge/Accurate generators/Internal covers"),
    Path("utils"),
    Path("Studioforge/Accurate generators"),
]

pref_patterns = [
    f"scarborough_rope_realistic_{rope_key}.*",
    f"realistic_scarborough_rope_{rope_key}.*",
    f"scarborough-rope-{rope_key}.*",
    f"rope_diagram_{rope_key}.*",
    "*Scarborough*Rope*.*",
    f"*{rope_key}*rope*.*",
]

rope_img = None
for vd in variant_dirs:
    if rope_img is not None:
        break
    if not vd.exists():
        print(f"  SKIP (not found): {vd}")
        continue
    print(f"  Scanning: {vd}")
    for pat in pref_patterns:
        cands = [fp for fp in vd.glob(pat) if fp.is_file() and "PLACEHOLDER" not in fp.name.upper()]
        if cands:
            print(f"    FOUND pattern={pat}: {cands[0].name}")
            rope_img = Image.open(str(cands[0]))
            break

if rope_img is None:
    print("  No rope image found - will use braided fallback")
    # Check placeholder
    for vd in variant_dirs:
        if not vd.exists():
            continue
        cands = list(vd.glob(f"rope_diagram_{rope_key}_PLACEHOLDER*.*"))
        if cands:
            print(f"    PLACEHOLDER found: {cands[0]}")
            rope_img = Image.open(str(cands[0]))
            break
else:
    print(f"  Rope image: {rope_img.size}")
