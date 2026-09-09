"""Wrapper for IEP Monitoring Form generator — exposes the standard
(images_folder, pack_code, theme_name) signature used by the StudioForge app."""
from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "_iep_monitoring_gen",
        str(Path(__file__).resolve().parent / "IEP_MONITORING_FORM.py"),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate_iep_monitoring_pack(images_folder: str, pack_code: str = "IEP", theme_name: str = "Theme") -> bool:
    """Build IEP monitoring form PDF. Derives slug and output dir from images_folder path."""
    try:
        p = Path(images_folder).resolve()
        if p.name.lower() == "activity_images":
            theme_dir = p.parent
            slug = theme_dir.name
        elif p.name.lower() == "icons" and p.parent.name == ".sf_build":
            theme_dir = p.parent.parent
            slug = theme_dir.name
        else:
            theme_dir = p
            slug = p.name
        out_dir = theme_dir / "OUTPUT"
        out_dir.mkdir(parents=True, exist_ok=True)
        gen = _load_generator()
        return gen.generate_iep_monitoring_form(slug, theme_name, pack_code, output_dir=str(out_dir))
    except Exception as e:
        print(f"IEP Monitoring build error: {e}")
        import traceback
        traceback.print_exc()
        return False
