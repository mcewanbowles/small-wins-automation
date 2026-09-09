from __future__ import annotations

import json
import sys
from pathlib import Path
import importlib.util

ROOT = Path(r"D:\Seagate\small-wins-automation")
ICONS_DIR = ROOT / "assets" / "themes" / "topic_f1_pit_stops" / "activity_images"

def list_icons(p: Path) -> list[str]:
    exts = ("*.png", "*.jpg", "*.jpeg")
    files = sorted({x.name for pat in exts for x in p.glob(pat)})
    return files

print("icons_dir:", ICONS_DIR)
files = list_icons(ICONS_DIR)
print("icons_count:", len(files))
print("icons_json:", json.dumps(files, ensure_ascii=False))

# Resolve images folder via GENERATE_ALL.resolve_images_folder (read-only)
GA = ROOT / "Studioforge" / "Accurate generators" / "GENERATE_ALL.py"
try:
    spec = importlib.util.spec_from_file_location("SWS_GENERATE_ALL", str(GA))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    found_path, n = mod.resolve_images_folder("topic_f1_pit_stops", min_icons=6)
    print("resolved_path:", found_path)
    print("resolved_count:", n)
    fp = str(found_path).replace("\\", "/").lower() if found_path else ""
    print("resolved_in_theme:", "assets/themes/topic_f1_pit_stops" in fp)
except Exception as e:
    print("resolve_images_folder_error:", type(e).__name__, e)
