"""Wrapper for Adapted Book generator — exposes the standard
(images_folder, pack_code, theme_name) signature used by the StudioForge app."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "_adapted_book_gen",
        str(Path(__file__).resolve().parent / "ADAPTED_BOOK_GENERATOR.py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate_adapted_book_pack(images_folder: str, pack_code: str = "ADPT", theme_name: str = "Theme") -> bool:
    """Build adapted book PDFs. Derives slug from images_folder path."""
    try:
        p = Path(images_folder).resolve()
        if p.name.lower() == "activity_images":
            slug = p.parent.name
        elif p.name.lower() == "icons" and p.parent.name == ".sf_build":
            slug = p.parent.parent.name
        else:
            slug = p.name
        gen = _load_generator()
        color_path, bw_path = gen.build_pdf(slug, theme_name, pack_code)
        return color_path is not None
    except Exception as e:
        print(f"Adapted Book build error: {e}")
        import traceback
        traceback.print_exc()
        return False
