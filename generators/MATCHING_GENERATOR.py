import sys
from pathlib import Path
import importlib
import json
import importlib.util
import traceback

# Wrapper to route backend 'matching' builds to the locked canonical generator.
# Expected argv from backend (style 'slug_bt_pc'):
#   python MATCHING_GENERATOR.py <slug> <book_title> <pack_code>

BASE_DIR = Path(__file__).resolve().parents[1]
LOCKED_DIR = BASE_DIR / "Studioforge" / "_CANONICAL_LOCKED"
LOCKED_SOURCE = LOCKED_DIR / "MATCHING_GENERATOR__LLRP_STANDARD__LOCKED_2026-09-04.py"

# Ensure repo root is importable (so 'utils.*' modules can be resolved)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def _shim_universal_standards():
    """Map utils.UNIVERSAL_STANDARDS to top-level UNIVERSAL_STANDARDS for legacy imports."""
    try:
        mod = importlib.import_module("utils.UNIVERSAL_STANDARDS")
        sys.modules.setdefault("UNIVERSAL_STANDARDS", mod)
    except Exception:
        pass


def _load_locked_generator():
    """Load the explicitly pinned locked matching generator and return its generate function."""
    # Provide import alias expected by locked file
    _shim_universal_standards()
    if not LOCKED_DIR.exists():
        raise FileNotFoundError(f"Locked dir not found: {LOCKED_DIR}")
    if not LOCKED_SOURCE.exists():
        raise FileNotFoundError(f"Locked matching generator not found: {LOCKED_SOURCE}")
    spec = importlib.util.spec_from_file_location("_SWS_MATCHING_LOCKED", str(LOCKED_SOURCE))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to create import spec for: {LOCKED_SOURCE}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    gen = getattr(mod, "generate_matching_pack", None)
    if not callable(gen):
        raise AttributeError("Locked generator does not expose generate_matching_pack")
    return gen


def _approved_stems(theme_dir: Path):
    config_path = theme_dir / "config" / "matching.json"
    if not config_path.exists():
        return None
    data = json.loads(config_path.read_text(encoding="utf-8"))
    stems = data.get("approved_stems")
    return stems if isinstance(stems, list) and stems else None


def generate_matching_pack(images_folder, pack_code="MATCH01", theme_name="Theme"):
    generator = _load_locked_generator()
    source = Path(images_folder)
    theme_dir = source.parent
    # Use the passed source (book kit / staging) by default so updated icons are used.
    # Only use a locked icon set if the source is already the activity_images root and
    # a config explicitly requests a locked set.
    if source.name.lower() == "activity_images" and not _approved_stems(theme_dir):
        locked_source = theme_dir / "activity_images_locked"
        if locked_source.exists() and any(locked_source.glob("*.png")):
            source = locked_source
    result = generator(str(source), pack_code=pack_code, theme_name=theme_name, selected_stems=_approved_stems(theme_dir))
    return result is True or result is None or (isinstance(result, int) and result == 0)


def main(argv):
    if len(argv) < 3:
        print("Usage: MATCHING_GENERATOR.py <slug> <book_title> <pack_code>", file=sys.stderr)
        return 2
    slug, book_title, pack_code = argv[0], argv[1], argv[2]

    # Resolve approved images first, falling back only when no locked set exists
    theme_dir = BASE_DIR / "assets" / "themes" / slug
    locked_images = theme_dir / "activity_images_locked"
    images_folder = locked_images if locked_images.exists() else theme_dir / "activity_images"

    try:
        gen = _load_locked_generator()
        res = gen(str(images_folder), pack_code=pack_code, theme_name=book_title, selected_stems=_approved_stems(theme_dir))
        # Treat True/None/0 as success
        if res is True or res is None or (isinstance(res, int) and res == 0):
            return 0
        return 1
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
