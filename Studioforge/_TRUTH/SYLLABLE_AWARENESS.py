from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE = BASE_DIR / "_TRUTH" / "_SYLLABLE_CARDS.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("_SWS_SYLLABLE_AWARENESS_CANDIDATE", SOURCE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load syllable candidate: {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate_syllable_cards_pack


def generate_syllable_awareness_pack(images_folder: str, pack_code: str = "SYL", theme_name: str = "Theme") -> bool:
    result = _load_generator()(images_folder, pack_code, theme_name)
    return result is True or result is None or (isinstance(result, int) and result == 0)
