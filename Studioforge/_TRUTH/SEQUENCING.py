from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from PIL import Image

from Studioforge._TRUTH.STORY_STRIPS_SEQUENCE import generate_story_strips


def _pdf_to_thumbnails(pdf_path: Path, thumb_dir: Path, prefix: str, max_pages: int = 2) -> list[str]:
    """Convert first pages of a PDF to thumbnail PNGs."""
    import io
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return []
    thumb_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    try:
        doc = fitz.open(str(pdf_path))
        for i in range(min(max_pages, len(doc))):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB" if pix.n < 4 else "RGBA", (pix.width, pix.height), pix.samples)
            img.thumbnail((500, 647), Image.Resampling.LANCZOS)
            path = thumb_dir / f"{prefix}_thumb{i + 1}.png"
            img.save(path, "PNG")
            paths.append(str(path))
        doc.close()
    except Exception:
        pass
    return paths


def _theme_dir(images_folder: str) -> Path:
    path = Path(images_folder).resolve()
    if path.name == "icons" and path.parent.name == ".sf_build":
        return path.parent.parent
    return path.parent


def generate_grounded_sequence_pack(images_folder: str, pack_code: str = "SEQ", theme_name: str = "Theme") -> bool:
    theme_dir = _theme_dir(images_folder)
    source = theme_dir / "book_vocab.json"
    if not source.exists():
        print(f"ERROR: Missing reviewed book vocabulary: {source}")
        return False
    data = json.loads(source.read_text(encoding="utf-8"))
    sequence = data.get("story_sequence") or []
    captions = data.get("story_event_captions") or {}
    if len(sequence) != 4 or any(not captions.get(key) for key in sequence):
        print("ERROR: Grounded sequencing requires exactly four ordered events with captions")
        return False
    output_dir = theme_dir / "OUTPUT"
    ok = generate_story_strips(images_folder, pack_code, theme_name, sequence_order=sequence, output_dir=str(output_dir))
    if not ok:
        return False

    # Generate thumbnails from color PDF
    color_pdf_path = output_dir / f"{pack_code}_Sequencing_COLOR.pdf"
    thumb_paths = _pdf_to_thumbnails(color_pdf_path, output_dir / "thumbnails", f"{pack_code}_Sequencing", max_pages=2)

    files = {
        "color_pdf": str(output_dir / f"{pack_code}_Sequencing_COLOR.pdf"),
        "bw_pdf": str(output_dir / f"{pack_code}_Sequencing_BW.pdf"),
        "preview_pdf": str(output_dir / f"{pack_code}_Sequencing_PREVIEW.pdf"),
        "thumbnails": thumb_paths,
    }
    manifest = {
        "schema_version": 1,
        "status": "pilot_review",
        "product_name": "Story Sequencing",
        "slug": theme_dir.name,
        "pack_code": pack_code,
        "page_count": 3,
        "reading_rope": ["Language Structures", "Literacy Knowledge"],
        "teacher_review_required": True,
        "source": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "sequence": [{"image_key": key, "caption": captions[key]} for key in sequence],
        "files": files,
        "meta": {"built_at": datetime.now().isoformat(timespec="seconds"), "warnings": []},
    }
    (output_dir / f"{pack_code}_Sequencing_BuildResult.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return True
