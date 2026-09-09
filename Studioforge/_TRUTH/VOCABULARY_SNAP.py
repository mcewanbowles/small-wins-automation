from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE = BASE_DIR / "_TRUTH" / "_VOCAB_WORD_WALL.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("_SWS_VOCAB_WORD_WALL_CANDIDATE", SOURCE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load Vocabulary Snap candidate: {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate_word_wall


def _slug_for_images(images_folder: str) -> str:
    images = Path(images_folder).resolve()
    if images.name == "icons" and images.parent.name == ".sf_build":
        return images.parent.parent.name
    return images.parent.name


def _write_build_result(theme_dir: Path, pack_code: str, theme_name: str, files: list[str]) -> None:
    out_dir = theme_dir / "OUTPUT"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Count actual pages from the consolidated WordSnap COLOR PDF
    actual_pages = 0
    try:
        import fitz
        snap_pdf = out_dir / f"{pack_code}_WordSnap_COLOR.pdf"
        if snap_pdf.exists():
            doc = fitz.open(str(snap_pdf))
            actual_pages = doc.page_count
            doc.close()
    except Exception:
        pass
    manifest = {
        "schema_version": 1,
        "status": "pilot_review",
        "product_name": "Vocabulary Snap",
        "slug": theme_dir.name,
        "pack_code": pack_code,
        "page_count": actual_pages or 15,
        "edition_neutral": False,
        "source_book_required": True,
        "files": {Path(f).stem.split("_")[-1].lower() + "_pdf" if not f.endswith("_BW.pdf") else "bw_pdf": f for f in files},
        "meta": {
            "built_at": datetime.now().isoformat(timespec="seconds"),
            "warnings": []
        }
    }
    (out_dir / f"{pack_code}_WordSnap_BuildResult.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_vocabulary_snap_pack(images_folder: str, pack_code: str = "VWW", theme_name: str = "Theme") -> bool:
    # Ensure title is title-cased (fixes lowercase slug leaking through)
    if theme_name and theme_name == theme_name.lower():
        theme_name = theme_name.title()
    slug = _slug_for_images(images_folder)
    if not slug:
        print(f"ERROR: Could not resolve book slug from images folder: {images_folder}")
        return False
    result = _load_generator()(slug, theme_name, pack_code, include_teacher_cover=False)
    if result is not True:
        return False
    # Write BuildResult.json
    try:
        images = Path(images_folder).resolve()
        theme_dir = images.parent.parent if images.name == "icons" and images.parent.name == ".sf_build" else images.parent
        out_dir = theme_dir / "OUTPUT"
        files = sorted([str(p) for p in out_dir.glob(f"{pack_code}_WordSnap*.pdf")] + [str(p) for p in out_dir.glob(f"{pack_code}_WordWall*.pdf")])
        _write_build_result(theme_dir, pack_code, theme_name, files)
    except Exception as e:
        print(f"WARN: Could not write Vocabulary Snap BuildResult: {e}")
    return True
