import sys
from pathlib import Path
import importlib
import importlib.util
import traceback
import json
import shutil
from datetime import datetime

# Wrapper module expected by backend (style 'py_module').
# Exposes: generate_aac_board_pack(images_path, pack_code, book_title) -> bool

BASE_DIR = Path(__file__).resolve().parents[1]

# Ensure project root is importable so 'BoardReady.boardready' can be resolved
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def _load_boardready_module():
    """Import BoardReady.boardready.AAC_BOARD_GENERATOR, with path fallback."""
    try:
        return importlib.import_module("BoardReady.boardready.AAC_BOARD_GENERATOR")
    except Exception:
        # Fallback: load by file path
        target = BASE_DIR / "BoardReady" / "boardready" / "AAC_BOARD_GENERATOR.py"
        if not target.exists():
            raise
        spec = importlib.util.spec_from_file_location("_BR_AAC", str(target))
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to import BoardReady AAC generator at {target}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        return mod


def generate_aac_board_pack(images_path: str, pack_code: str, book_title: str):
    """
    Backend entrypoint. Derive slug from images_path and call BoardReady CLI main().
    Generates standard color + BW, plus high-visibility black and yellow variants.
    Returns True on success.
    """
    try:
        p = Path(images_path).resolve()
        # Derive slug/theme_dir robustly for staging or direct activity_images paths
        if p.name.lower() == "icons" and p.parent.name == ".sf_build":
            theme_dir = p.parent.parent
        elif p.name.lower() == "activity_images":
            theme_dir = p.parent
        else:
            theme_dir = p
        slug = theme_dir.name
        BR = _load_boardready_module()
        argv_old = sys.argv[:]
        vocab_path = theme_dir / "book_vocab.json"
        themes_root = theme_dir.parent
        try:
            vocab_data = json.loads(vocab_path.read_text(encoding="utf-8"))
        except Exception:
            vocab_data = {}
        if slug not in vocab_data:
            wrapped_vocab = theme_dir / "config" / "boardready_vocab.json"
            wrapped_vocab.parent.mkdir(parents=True, exist_ok=True)
            wrapped_vocab.write_text(json.dumps({slug: vocab_data}, ensure_ascii=False, indent=2), encoding="utf-8")
            vocab_path = wrapped_vocab

        base_argv = [
            "AAC_BOARD_GENERATOR.py",
            "--book", slug,
            "--vocab", str(vocab_path),
            "--themes-root", str(themes_root),
            "--pack-code", str(pack_code),
            "--no-cover",
        ]

        # Run 1: standard color + BW
        try:
            sys.argv = base_argv[:]
            BR.main()
        finally:
            sys.argv = argv_old

        # Run 2: high-visibility black
        try:
            sys.argv = base_argv + ["--high-vis", "--high-vis-style", "black"]
            BR.main()
        except Exception:
            pass  # HV is best-effort; don't fail the whole pack
        finally:
            sys.argv = argv_old

        # Run 3: high-visibility yellow
        try:
            sys.argv = base_argv + ["--high-vis", "--high-vis-style", "yellow"]
            BR.main()
        except Exception:
            pass
        finally:
            sys.argv = argv_old

        # Move outputs from Studioforge/OUTPUT/<pack_code> to theme_dir/OUTPUT
        # PDFs are already coverless (Page 1/1) thanks to --no-cover flag
        src_dir = BASE_DIR / "OUTPUT" / pack_code
        out_dir = theme_dir / "OUTPUT"
        out_dir.mkdir(parents=True, exist_ok=True)
        if src_dir.exists():
            for src in src_dir.glob("*.pdf"):
                name = src.name
                # Normalize names: keep pack code and drop _BR_/_WS_ variants
                if "_AAC_Board_" in name:
                    name = name.replace("_BR_", "_").replace("_WS_", "_")
                    name = name.replace("__", "_")
                dest = out_dir / name
                try:
                    shutil.copy2(str(src), str(dest))
                    print(f"Wrote {dest}")
                except Exception as e:
                    print(f"WARN: copy failed for {src}: {e}")

        # Write BuildResult.json
        try:
            out_files = sorted([str(p) for p in out_dir.glob(f"{pack_code}_AAC_Board*.pdf")])
            files_map = {}
            for f in out_files:
                key = Path(f).name.replace(f"{pack_code}_", "").replace(".pdf", "").lower().replace("_", "_")
                # Simplify keys
                if "color_highvis_black" in key:
                    key = "highvis_black_pdf"
                elif "color_highvis_yellow" in key:
                    key = "highvis_yellow_pdf"
                elif "_bw" in key:
                    key = "bw_pdf"
                else:
                    key = "color_pdf"
                files_map[key] = f
            manifest = {
                "schema_version": 1,
                "status": "pilot_review",
                "product_name": "AAC Communication Board",
                "slug": slug,
                "pack_code": pack_code,
                "page_count": 1,
                "high_vis_variants": ["black", "yellow"],
                "files": files_map,
                "meta": {
                    "built_at": datetime.now().isoformat(timespec="seconds"),
                    "warnings": []
                }
            }
            (out_dir / f"{pack_code}_AAC_Board_BuildResult.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"WARN: Could not write AAC Board BuildResult: {e}")
        return True
    except SystemExit as e:
        code = getattr(e, "code", 1)
        try:
            code = int(code)
        except Exception:
            code = 1 if code else 0
        return code == 0
    except Exception:
        traceback.print_exc()
        return False
