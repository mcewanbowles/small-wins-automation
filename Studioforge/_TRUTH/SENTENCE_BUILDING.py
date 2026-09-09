from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE = BASE_DIR / "_TRUTH" / "_SENTENCE_STRIPS_AAC_LOCKED.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("_SWS_SENTENCE_BUILDING_CANDIDATE", SOURCE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load sentence-building candidate: {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate_aac_pack


def generate_sentence_building_pack(images_folder: str, pack_code: str = "AAC-STRIPS", theme_name: str = "Theme") -> bool:
    result = _load_generator()(images_folder, pack_code, theme_name, strips_per_page=4, show_aac_labels=True)
    return result is True or result is None or (isinstance(result, int) and result == 0)
