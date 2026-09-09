import json, sys, runpy
from pathlib import Path
import fitz
from PIL import Image

base = Path(r"D:\Seagate\small-wins-automation\assets\themes")
# Find a candidate images folder (prefer activity_images, then icons_colored, then icons) with >=4 PNGs
cand = None
book = None
for slug_dir in sorted([d for d in base.iterdir() if d.is_dir() and not d.name.startswith((".", "_"))]):
    for sub in ("activity_images", "icons_colored", "icons"):
        p = slug_dir / sub
        if p.exists():
            cnt = sum(1 for _ in p.glob("*.png"))
            if cnt >= 4:
                cand = p
                book = slug_dir.name
                break
    if cand:
        break

if not cand:
    print(json.dumps({"error": "no_candidate_found"}, ensure_ascii=False))
    sys.exit(1)

# Build pack code
pk = (book[:4].upper() or "TEST") + "-M2P"
gen_path = r"D:\Seagate\small-wins-automation\production\generators\generators\MATCHING_GENERATOR.py"
ns = runpy.run_path(gen_path)
ok = ns["generate_matching_pack"](str(cand), pk, book.replace("_", " ").title())

out_dir = Path(r"D:\Seagate\small-wins-automation\Studioforge\OUTPUT") / pk
preview_pdf = out_dir / f"{pk}_Matching_PREVIEW.pdf"
thumbs_dir = out_dir / "thumbnails"
thumbs = sorted(thumbs_dir.glob(f"{pk}_Matching_thumb*.png"))
thumb = thumbs[0] if thumbs else None

# Read PDF metadata using PyMuPDF
pdf_meta = {}
try:
    d = fitz.open(str(preview_pdf))
    pdf_meta = d.metadata or {}
    d.close()
except Exception as e:
    pdf_meta = {"error": str(e)}

# Read PNG metadata using Pillow
png_info = {}
if thumb and thumb.exists():
    im = Image.open(thumb)
    info = {}
    for k, v in (im.info or {}).items():
        if isinstance(v, (bytes, bytearray)):
            try:
                v = v.decode("latin-1")
            except Exception:
                v = str(v)
        info[k] = v
    png_info = {"path": str(thumb), "info": info}
else:
    png_info = {"error": "no_thumbnail_found", "thumbs_dir": str(thumbs_dir)}

print(json.dumps({
    "book": book,
    "images_folder": str(cand),
    "pack_code": pk,
    "preview_pdf": str(preview_pdf),
    "pdf_metadata": pdf_meta,
    "png_info": png_info
}, ensure_ascii=False, indent=2))
