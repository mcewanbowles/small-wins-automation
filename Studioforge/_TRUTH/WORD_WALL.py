"""Wrapper for Vocabulary Word Wall generator — exposes the standard
(images_folder, pack_code, theme_name) signature used by the StudioForge app."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "_vocab_word_wall_gen",
        str(Path(__file__).resolve().parent / "_VOCAB_WORD_WALL.py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate_word_wall_pack(images_folder: str, pack_code: str = "VWW", theme_name: str = "Theme") -> bool:
    """Build Word Wall + WordSnap PDFs. Derives slug from images_folder path."""
    try:
        p = Path(images_folder).resolve()
        if p.name.lower() == "activity_images":
            slug = p.parent.name
        else:
            slug = p.name
        gen = _load_generator()
        return gen.generate_word_wall(slug, theme_name, pack_code)
    except Exception as e:
        print(f"Word Wall build error: {e}")
        import traceback
        traceback.print_exc()
        return False
