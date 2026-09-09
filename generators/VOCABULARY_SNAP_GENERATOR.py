from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE = BASE_DIR / "Studioforge" / "Accurate generators" / "VOCAB_WORD_WALL.py"


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


def generate_vocabulary_snap_pack(images_folder: str, pack_code: str = "VWW", theme_name: str = "Theme") -> bool:
    slug = _slug_for_images(images_folder)
    if not slug:
        print(f"ERROR: Could not resolve book slug from images folder: {images_folder}")
        return False
    result = _load_generator()(slug, theme_name, pack_code, include_teacher_cover=False)
    # Only return True if the generator explicitly succeeded
    return result is True
