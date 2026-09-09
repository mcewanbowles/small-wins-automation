import sys
import os
import json
import subprocess
import webbrowser
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
import socket
import urllib.request as _rq
import urllib.parse as _up
import re
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore

# Optional imaging lib for QA checks
try:
    from PIL import Image as _PIL_Image  # type: ignore
except Exception:
    _PIL_Image = None  # type: ignore

try:
    from UNIVERSAL_STANDARDS import SWS_TEAL, SWS_NAVY
except Exception:
    SWS_TEAL = "#31A8A0"
    SWS_NAVY = "#0D2545"

# Unified pill palette: state -> (fg, bg)
PILL = {
    "done": ("#14532D", "#D1FAE5"),
    "warn": ("#92400E", "#FEF3C7"),
    "todo": ("#B91C1C", "#FEE2E2"),
    "neutral": ("#475569", "#F1F5F9"),
    "active": ("#FFFFFF", SWS_TEAL),
}
NAV_BG = "#F9FAFB"
NAV_ACTIVE_BG = "#E6FFFB"


def _pill(widget, text, state="neutral"):
    try:
        fg, bg = PILL.get(state, PILL["neutral"])
        widget.config(text=text, fg=fg, bg=bg)
    except Exception:
        pass

# Import QA Reviewer UI with robust fallback to file path
try:
    from boardready.modules.qa_reviewer import QAReviewer  # type: ignore
except Exception:
    # Fallback: load directly from file if package import is unavailable
    QAReviewer = None  # type: ignore
    try:
        import importlib.util as _ilu
        _qa_path = Path(__file__).resolve().parent / "boardready" / "modules" / "qa_reviewer.py"
        if _qa_path.exists():
            _spec = _ilu.spec_from_file_location("qa_reviewer_mod", str(_qa_path))
            if _spec and _spec.loader:
                _mod = _ilu.module_from_spec(_spec)
                _spec.loader.exec_module(_mod)  # type: ignore
                QAReviewer = getattr(_mod, "QAReviewer", None)  # type: ignore
    except Exception:
        QAReviewer = None  # type: ignore

BASE_DIR = Path(__file__).resolve().parent.parent
STUDIOFORGE_DIR = Path(__file__).resolve().parent
# Always use the canonical repo-root assets/themes; do not fall back to the duplicate Studioforge/assets folder
THEMES_DIR = BASE_DIR / "assets" / "themes"
LOG_FILE = STUDIOFORGE_DIR / "_tool_launcher_log.json"

def _load_env_files():
    # Prefer BASE .env first, then Studioforge/.env with override semantics
    if load_dotenv is not None:
        for p, ov in [(BASE_DIR / ".env", False), (STUDIOFORGE_DIR / ".env", True)]:
            try:
                if p.exists():
                    load_dotenv(dotenv_path=str(p), override=ov, encoding="utf-8")
                    for idx, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
                        s = line.strip()
                        if s.startswith("\ufeff"):
                            s = s.lstrip("\ufeff")
                        if not s or s.startswith("#") or s.startswith(";") or "=" not in s:
                            continue
                        k, v = s.split("=", 1)
                        k = k.strip().lstrip("\ufeff"); v = v.strip().strip("'").strip('"')
                        if k == "ANTHROPIC_API_KEY" and v:
                            try:
                                os.environ["ANTHROPIC_API_KEY"] = v
                                os.environ["SWS_DOTENV_LAST"] = str(p)
                                os.environ["SWS_KEY_SRC"] = f"{p}#L{idx}"
                                os.environ["SWS_KEY_PREFIX"] = v[:15]
                            except Exception:
                                pass
                            break
            except Exception:
                pass
        return
    # Fallback manual loader: load BASE first, then Studioforge; Studioforge overrides
    for p in [BASE_DIR / ".env", STUDIOFORGE_DIR / ".env"]:
        try:
            if p.exists():
                for idx, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
                    s = line.strip()
                    if s.startswith("\ufeff"):
                        s = s.lstrip("\ufeff")
                    if not s or s.startswith("#") or s.startswith(";") or "=" not in s:
                        continue
                    k, v = s.split("=", 1)
                    k = k.strip().lstrip("\ufeff"); v = v.strip().strip("'").strip('"')
                    if not k or not v:
                        continue
                    if k in {"ANTHROPIC_API_KEY", "SERPER_API_KEY", "BING_SEARCH_V7_SUBSCRIPTION_KEY", "ANTHROPIC_MODEL", "BING_SEARCH_V7_ENDPOINT"}:
                        os.environ[k] = v
                        if k == "ANTHROPIC_API_KEY":
                            try:
                                os.environ["SWS_DOTENV_LAST"] = str(p)
                                os.environ["SWS_KEY_SRC"] = f"{p}#L{idx}"
                                os.environ["SWS_KEY_PREFIX"] = v[:15]
                            except Exception:
                                pass
                    elif k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass

_load_env_files()


def _read_dotenv_key(p: Path, name: str):
    try:
        if not p.exists():
            return None, None
        for idx, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            s = line.strip()
            if s.startswith("\ufeff"):
                s = s.lstrip("\ufeff")
            if not s or s.startswith("#") or s.startswith(";") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            k = k.strip().lstrip("\ufeff"); v = v.strip().strip("'").strip('"')
            if k == name and v:
                return v, f"{p}#L{idx}"
    except Exception:
        pass
    return None, None


def _get_anthropic_key():
    for _p in [STUDIOFORGE_DIR / ".env", BASE_DIR / ".env"]:
        v, src = _read_dotenv_key(_p, "ANTHROPIC_API_KEY")
        if v:
            return v, (src or str(_p))
    return os.environ.get("ANTHROPIC_API_KEY"), "env:process"

_venv_py = STUDIOFORGE_DIR / "backend" / ".venv311_x64" / "Scripts" / ("python.exe" if os.name == "nt" else "python")
def _probe_python(path):
    try:
        p = subprocess.run([str(path), "-c", "print(1)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        return p.returncode == 0
    except Exception:
        return False
PYTHON = str(_venv_py) if (_venv_py.exists() and _probe_python(_venv_py)) else (sys.executable or "python")
PYTHON_SOURCE = "venv" if (_venv_py.exists() and _probe_python(_venv_py)) else "system"
_PY_WARNED = False

def _maybe_warn_python_fallback():
    global _PY_WARNED
    if PYTHON_SOURCE != "venv" and not _PY_WARNED:
        try:
            messagebox.showinfo("Interpreter fallback", "Using system Python (venv not available).")
        except Exception:
            pass
        return

TOOLS = {
    "board_ready": {
        "name": "Board Ready",
        "desc": "Generate AAC board PDFs for a selected book.",
        "requires": ["aac_board_generator"],
        "runnable": "board_ready",
        "tip": "Build after curating icons; rerun if you swap icons in QA Review.",
    },
    "matching": {
        "name": "Matching",
        "desc": "Generate Matching pack (4 levels) for the selected book.",
        "requires": ["matching_generate_all"],
        "runnable": "matching",
        "tip": "Gated on 15 curated icons in activity_images. Use Icon Labeler first.",
    },
    "code_words": {
        "name": "Code Words",
        "desc": "Generate letter-clue Code Words (3 levels) using book word bank.",
        "runnable": "code_words",
        "tip": "Uses Essential + Optional word bank; emits vocab requests for gaps.",
    },
    "book_insert_strips": {
        "name": "Book Insert Strips",
        "desc": "Create printable insert strips with themed icons.",
        "runnable": "book_insert_strips",
        "tip": "Uses activity_images or extracted symbols; two content pages + cover.",
    },
    "icon_labeler": {
        "name": "Icon Labeler",
        "desc": "Launch opens a browser tab. The icons already picked for this book are at the top under 'Required Icons'.",
        "runnable": "icon_labeler",
        "tip": "In the browser: check each picture, Skip or Replace any wrong ones, then click 'Save icons to book'. First load can take up to a minute.",
    },
    "listing_generator": {
        "name": "Listing Generator",
        "desc": "Generate TPT listing JSON for the selected book.",
        "requires": ["listing_generator"],
        "runnable": "listing_generator",
        "tip": "Run after activities are generated; uses book vocab and outputs.",
    },
    "ai_prep": {
        "name": "AI Pre-Populate",
        "desc": "Generate All Vocab & Content — Dry-Run builder + Live Preview (no writes).",
        "runnable": "ai_prep",
        "tip": "Start here to pre-populate book_vocab and needs_review before icon work.",
    },
    "topic_builder": {
        "name": "Topic Content Builder",
        "desc": "Generate topic-based book_vocab + needs_review with grounding and hero image.",
        "runnable": "topic_builder",
        "tip": "Creates a new topic theme (slug begins with topic_).",
    },
    "pack_ready": {
        "name": "Pack Ready",
        "desc": "Packaging step — awaiting confirmation before wiring.",
        "runnable": "pack_ready",
        "disabled_reason": "Awaiting confirmation — do not use yet.",
        "tip": "Collects docs (TOU, Quick Start, Rope) + outputs into a single ZIP.",
    },
    "qa_reviewer": {
        "name": "QA Review",
        "desc": "Visually review icons per book; search-and-swap, save, and regenerate.",
        "runnable": "qa_reviewer",
        "tip": "Use to resolve icon gaps quickly; then regenerate affected products.",
    },
}

# Left sidebar navigation groups for workflow staging
NAV_GROUPS = [
    ("Start", [
        ("Guided Start", None),
    ]),
    ("Set up", [
        ("AI Pre-Populate", "ai_prep"),
        ("Topic Builder", "topic_builder"),
    ]),
    ("Build assets", [
        ("Icon Labeler", "icon_labeler"),
    ]),
    ("Generate activities", [
        ("Matching", "matching"),
        ("Code Words", "code_words"),
        ("Book Insert Strips", "book_insert_strips"),
        ("Board Ready", "board_ready"),
    ]),
    ("Review and track", [
        ("Review and track", None),
    ]),
    ("Finish and publish", [
        ("QA Review", "qa_reviewer"),
        ("Listing Generator", "listing_generator"),
        ("Pack Ready", "pack_ready"),
    ]),
]

# Simple per-tool added dates for "New" badges (ISO date)
NEW_WINDOW_DAYS = 14
TOOL_ADDED_DATES = {
    "qa_reviewer": "2026-08-18",
    "topic_builder": "2026-08-15",
    "code_words": "2026-08-30",
    "book_insert_strips": "2026-08-30",
}


def _read_log():
    try:
        if LOG_FILE.exists():
            return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _write_log(data):
    try:
        LOG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _touch_used(key):
    data = _read_log()
    data[key] = datetime.now().isoformat(timespec="seconds")
    try:
        data["_python_source"] = PYTHON_SOURCE
    except Exception:
        pass
    _write_log(data)


def _last_used(key):
    return _read_log().get(key, "— never —")


def _log_event(ev_type, payload=None):
    try:
        data = _read_log()
        events = data.get("events")
        if not isinstance(events, list):
            events = []
        rec = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "type": str(ev_type),
            "data": payload or {},
        }
        events.append(rec)
        data["events"] = events
        _write_log(data)
    except Exception:
        pass


_BOOKS_CACHE = {"ts": 0.0, "data": None}
_BOOKS_TTL_S = 60.0


def _list_books(force: bool = False):
    now = time.time()
    cached = _BOOKS_CACHE.get("data")
    if not force and isinstance(cached, list) and (now - float(_BOOKS_CACHE.get("ts") or 0.0)) < _BOOKS_TTL_S:
        return list(cached)
    books = []
    if not THEMES_DIR.exists():
        return books
    try:
        entries = sorted((e for e in os.scandir(THEMES_DIR) if e.is_dir()), key=lambda e: e.name)
    except OSError:
        return books
    for e in entries:
        slug = e.name
        # Filter dot/underscore-prefixed/internal folders (e.g., .sf_build, _reports)
        if slug.startswith('.') or slug.startswith('_'):
            continue
        p = Path(e.path)
        title = slug.replace("_", " ").title()
        code = None
        # Prefer root book_vocab.json; fallback to config/book_vocab.json
        try:
            root_cfg = p / "book_vocab.json"
            cfg = root_cfg if root_cfg.exists() else (p / "config" / "book_vocab.json")
            if not cfg.exists():
                # Not a real book theme without a vocab file
                continue
        except OSError as ex:
            # Disk read failure (e.g. CRC error) on this book: skip it rather than crash the launcher
            print(f"[launcher] skipping {slug}: {ex}", file=sys.stderr)
            continue
        try:
            obj = json.loads(cfg.read_text(encoding="utf-8-sig"))
            title = obj.get("title", title)
            code = obj.get("code")
        except Exception:
            pass
        books.append({"slug": slug, "title": title, "code": code})
    _BOOKS_CACHE["ts"] = now
    _BOOKS_CACHE["data"] = list(books)
    return books


def _generator_has_named_args():
    try:
        src = (STUDIOFORGE_DIR / "AAC_BOARD_GENERATOR.py").read_text(encoding="utf-8", errors="ignore")
        return "add_argument(\"--book\"" in src or "--book" in src
    except Exception:
        return True


def _run_in_console(args, cwd):
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_CONSOLE
    try:
        env = os.environ.copy()
        try:
            env["STUDIOFORGE_ROOT"] = str(BASE_DIR)
            add_paths = os.pathsep.join([str(STUDIOFORGE_DIR), str(STUDIOFORGE_DIR / "boardready")])
            cur_pp = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = add_paths + (os.pathsep + cur_pp if cur_pp else "")
        except Exception:
            pass
        _maybe_warn_python_fallback()
        try:
            _log_event("launch", {"mode": "console", "cwd": str(cwd), "args": list(map(str, args)), "python": str(PYTHON), "source": str(PYTHON_SOURCE)})
        except Exception:
            pass
        subprocess.Popen(args, cwd=str(cwd), creationflags=creationflags, env=env)
        return True
    except FileNotFoundError:
        messagebox.showerror("Missing Python", "Could not find Python interpreter.")
        _log_event("error", {"where": "_run_in_console", "error": "Missing Python"})
    except Exception as e:
        messagebox.showerror("Launch error", str(e))
        _log_event("error", {"where": "_run_in_console", "error": str(e)})
    return False


def _run_in_console_persist(args, cwd):
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_CONSOLE
    try:
        env = os.environ.copy()
        try:
            env["STUDIOFORGE_ROOT"] = str(BASE_DIR)
            add_paths = os.pathsep.join([str(STUDIOFORGE_DIR), str(STUDIOFORGE_DIR / "boardready")])
            cur_pp = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = add_paths + (os.pathsep + cur_pp if cur_pp else "")
        except Exception:
            pass
        if os.name == "nt":
            cmd = ["cmd.exe", "/k"] + args
            try:
                _log_event("launch", {"mode": "console_persist", "cwd": str(cwd), "args": list(map(str, cmd)), "python": str(PYTHON), "source": str(PYTHON_SOURCE)})
            except Exception:
                pass
            subprocess.Popen(cmd, cwd=str(cwd), creationflags=creationflags, env=env)
        else:
            try:
                _log_event("launch", {"mode": "console_persist", "cwd": str(cwd), "args": list(map(str, args)), "python": str(PYTHON), "source": str(PYTHON_SOURCE)})
            except Exception:
                pass
            subprocess.Popen(args, cwd=str(cwd), creationflags=creationflags, env=env)
        return True
    except FileNotFoundError:
        messagebox.showerror("Missing Python", "Could not find Python interpreter.")
        _log_event("error", {"where": "_run_in_console_persist", "error": "Missing Python"})
    except Exception as e:
        messagebox.showerror("Launch error", str(e))
        _log_event("error", {"where": "_run_in_console_persist", "error": str(e)})
    return False


def _run_in_console_env(args, cwd, extra_env=None):
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_CONSOLE
    try:
        env = os.environ.copy()
        try:
            env["STUDIOFORGE_ROOT"] = str(BASE_DIR)
            add_paths = os.pathsep.join([str(STUDIOFORGE_DIR), str(STUDIOFORGE_DIR / "boardready")])
            cur_pp = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = add_paths + (os.pathsep + cur_pp if cur_pp else "")
        except Exception:
            pass
        if isinstance(extra_env, dict):
            xe = {str(k): str(v) for k, v in extra_env.items()}
            if "PYTHONPATH" in xe:
                prev = env.get("PYTHONPATH", "")
                newv = xe.pop("PYTHONPATH")
                env["PYTHONPATH"] = (str(newv) + os.pathsep + prev) if prev else str(newv)
            env.update(xe)
        try:
            _log_event("launch", {"mode": "console_env", "cwd": str(cwd), "args": list(map(str, args)), "python": str(PYTHON), "source": str(PYTHON_SOURCE), "extra_env": extra_env or {}})
        except Exception:
            pass
        subprocess.Popen(args, cwd=str(cwd), creationflags=creationflags, env=env)
        return True
    except FileNotFoundError:
        messagebox.showerror("Missing Python", "Could not find Python interpreter.")
        _log_event("error", {"where": "_run_in_console_env", "error": "Missing Python"})
    except Exception as e:
        messagebox.showerror("Launch error", str(e))
        _log_event("error", {"where": "_run_in_console_env", "error": str(e)})
    return False


def _python_has_module(mod_name: str) -> bool:
    try:
        p = subprocess.run([str(PYTHON), "-c", f"import {mod_name}"], cwd=str(STUDIOFORGE_DIR),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return p.returncode == 0
    except Exception:
        return False


def _requirement_candidates(token: str):
    try:
        if token == "aac_board_generator":
            return [STUDIOFORGE_DIR / "AAC_BOARD_GENERATOR.py"]
        if token == "matching_generate_all":
            return [
                Path("D:/Seagate/small-wins-automation/Studioforge/Accurate generators/GENERATE_ALL.py"),
                STUDIOFORGE_DIR / "Accurate generators" / "GENERATE_ALL.py",
            ]
        if token == "listing_generator":
            return [STUDIOFORGE_DIR / "LISTING_GENERATOR.py"]
    except Exception:
        pass
    return []


def _requirement_name(token: str) -> str:
    names = {
        "aac_board_generator": "AAC_BOARD_GENERATOR.py",
        "matching_generate_all": "GENERATE_ALL.py",
        "listing_generator": "LISTING_GENERATOR.py",
    }
    return names.get(token, token)


def _open_icon_labeler_later(delay_s=1.5, url="http://127.0.0.1:5052", ping_path="/api/ping"):
    def _t():
        time.sleep(delay_s)
        try:
            # Always ping the server origin (host:port), not the UI path (e.g. /pdf)
            pu = _up.urlparse(url)
            origin = f"{pu.scheme}://{pu.netloc}"
            ping_url = origin + (ping_path or "/")
            for _ in range(20):
                try:
                    _rq.urlopen(ping_url, timeout=1)
                    break
                except Exception:
                    time.sleep(0.25)
            webbrowser.open(url)
        except Exception:
            pass
    threading.Thread(target=_t, daemon=True).start()


def _is_server_alive(port: int) -> bool:
    try:
        base = f"http://127.0.0.1:{port}"
        for pth in ("/api/ping", "/api/theme_slugs"):
            try:
                _rq.urlopen(base + pth, timeout=0.75)
                return True
            except Exception:
                pass
    except Exception:
        pass
    return False

def _resolved_generator_path(tool_key: str):
    try:
        if tool_key == "board_ready":
            return STUDIOFORGE_DIR / "AAC_BOARD_GENERATOR.py"
        if tool_key == "matching":
            d_gen = Path("D:/Seagate/small-wins-automation/Studioforge/Accurate generators/GENERATE_ALL.py")
            return d_gen if d_gen.exists() else (STUDIOFORGE_DIR / "Accurate generators" / "GENERATE_ALL.py")
        if tool_key == "listing_generator":
            return STUDIOFORGE_DIR / "LISTING_GENERATOR.py"
        if tool_key == "code_words":
            return BASE_DIR / "production" / "generators" / "generate_code_words_constitution.py"
        if tool_key == "book_insert_strips":
            return BASE_DIR / "production" / "generators" / "generate_book_insert_strips_constitution.py"
    except Exception:
        pass
    return None


def _packaging_docs_find():
    try:
        # Prefer the new canonical SWS support docs handoff folder
        sws_root = BASE_DIR / "SWS_Support_Docs_Handoff"
        root = sws_root if sws_root.exists() else (STUDIOFORGE_DIR / "TPT_LINE_OF_TRUTH")
        if not root.exists():
            alt = BASE_DIR / "TPT_LINE_OF_TRUTH"
            root = alt if alt.exists() else root
        if not root.exists():
            return {"root": None, "tou": None, "quick": None, "rope": []}
        def first_match(patterns):
            for pat in patterns:
                try:
                    fp = next(root.rglob(pat))
                    if fp.is_file():
                        return fp
                except StopIteration:
                    continue
                except Exception:
                    continue
            return None
        # Terms of Use and Quick Start can be PDF or Markdown in SWS handoff
        tou = first_match(["*TERMS_OF_USE*.*", "*Terms_of_Use*.*", "*Terms*Use*.*", "*TOU*.*", "*Terms*.*"])  # Terms of Use
        quick = first_match(["*Quick*Start*.*", "*QuickStart*.*", "*QUICK_START*.*"])  # Quick Start guide
        rope = []
        try:
            for fp in root.rglob("*Scarborough*Rope*.*"):
                try:
                    if fp.is_file():
                        rope.append(fp)
                        if len(rope) >= 6:
                            break
                except Exception:
                    continue
        except Exception:
            rope = []
        return {"root": root, "tou": tou, "quick": quick, "rope": rope}
    except Exception:
        return {"root": None, "tou": None, "quick": None, "rope": []}


_ICONS_API_DOWN_UNTIL = 0.0


def _icons_check_status(slug: str):
    global _ICONS_API_DOWN_UNTIL
    try:
        if not slug:
            return None
        if time.time() < _ICONS_API_DOWN_UNTIL:
            return None
        url = f"http://127.0.0.1:8001/api/icons/checklist?book={slug}"
        try:
            with _rq.urlopen(url, timeout=0.75) as resp:
                if getattr(resp, "status", 200) != 200:
                    return None
                raw = resp.read()
        except Exception:
            _ICONS_API_DOWN_UNTIL = time.time() + 30.0
            return None
        try:
            data = json.loads(raw.decode("utf-8", errors="ignore"))
        except Exception:
            return None
        miss = None
        ready = None
        if isinstance(data, dict):
            if "missing_count" in data:
                try:
                    miss = int(data.get("missing_count"))
                except Exception:
                    miss = None
            if miss is None and isinstance(data.get("missing"), list):
                try:
                    miss = len(data.get("missing"))
                except Exception:
                    miss = None
            if "ready" in data:
                try:
                    ready = bool(data.get("ready"))
                except Exception:
                    ready = None
        if ready is True:
            return True, "OK"
        if isinstance(miss, int):
            if miss > 0:
                return False, f"{miss} required icons missing"
            return True, "OK"
        return None
    except Exception:
        return None


def _open_icons_checklist(slug: str):
    try:
        if not slug:
            return
        url = f"http://127.0.0.1:8001/icons/checklist?book={slug}"
        webbrowser.open(url)
    except Exception:
        pass

def _theme_has_hero(slug: str) -> bool:
    try:
        if not slug:
            return False
        base = THEMES_DIR / slug
        if (base / "hero.png").is_file():
            return True
        hd = base / "heroes"
        if hd.is_dir():
            return any(f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp") for f in hd.iterdir())
        return False
    except Exception:
        return False


def _theme_has_cover(slug: str) -> bool:
    try:
        if not slug:
            return False
        base = THEMES_DIR / slug
        for f in base.glob("cover*"):
            if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                return True
        return False
    except Exception:
        return False

class _ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = str(text)
        self.tip = None
        self._after_id = None
        try:
            widget.bind("<Enter>", self._show)
            widget.bind("<Leave>", self._hide)
        except Exception:
            pass

    def _show(self, *_):
        try:
            if self._after_id is None:
                self._after_id = self.widget.after(250, self._do_show)
        except Exception:
            self.tip = None

    def _hide(self, *_):
        try:
            if self._after_id is not None:
                try:
                    self.widget.after_cancel(self._after_id)
                except Exception:
                    pass
                self._after_id = None
            if self.tip:
                self.tip.destroy()
                self.tip = None
        except Exception:
            self.tip = None

    def _do_show(self):
        try:
            self._after_id = None
            if self.tip:
                return
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
            self.tip = tk.Toplevel(self.widget)
            self.tip.wm_overrideredirect(True)
            self.tip.wm_geometry(f"+{x}+{y}")
            tk.Label(self.tip, text=self.text, bg="#ffffe0", relief="solid", borderwidth=1, padx=6, pady=3).pack()
        except Exception:
            self.tip = None


def _tip(widget, text):
    try:
        _ToolTip(widget, text)
    except Exception:
        pass


class ToolLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Small Wins Studio — Tool Launcher")
        self.geometry("1040x740")
        # Light background for maximum contrast with content
        self.configure(bg="#FFFFFF")
        # Restore saved window geometry if present, clamped to the current screen
        try:
            g = _read_log().get("_geometry")
            if g:
                self.geometry(self._clamp_geometry(g))
        except Exception:
            pass

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        # Improve contrast: white tab bar, white unselected tabs with dark text; teal highlight on selected
        style.configure("TNotebook", background="#FFFFFF")
        style.configure("TNotebook.Tab", background="#FFFFFF", padding=(16, 10), font=("Segoe UI", 11), foreground="#0D2545")
        style.map(
            "TNotebook.Tab",
            background=[("selected", SWS_TEAL), ("active", "#E5E7EB")],
            foreground=[("selected", "white"), ("active", "#0D2545")],
        )
        try:
            # Keep a visible-tab variant for nested notebooks before hiding the main tab UI
            style.layout("Sub.TNotebook.Tab", style.layout("TNotebook.Tab"))
            style.configure("Sub.TNotebook", background="#FFFFFF")
            style.configure("Sub.TNotebook.Tab", background="#F1F5F9", padding=(12, 6), font=("Segoe UI", 10), foreground="#0D2545")
            style.map("Sub.TNotebook.Tab", background=[("selected", "#FFFFFF"), ("active", "#E5E7EB")], foreground=[("selected", "#0D2545")])
        except Exception:
            pass
        try:
            # Hide the native tab UI; we control selection via a left sidebar
            style.layout("TNotebook.Tab", [])
        except Exception:
            pass

        header = tk.Frame(self, bg=SWS_TEAL, height=46)
        header.pack(fill="x")
        title_lbl = tk.Label(header, text="Tool Launcher", fg="white", bg=SWS_TEAL,
                             font=("Segoe UI", 12, "bold"))
        title_lbl.pack(side="left", padx=12, pady=10)
        _tip(title_lbl, "Small Wins Studio — Tool Launcher")
        self._header = header

        btn_row = tk.Frame(header, bg=SWS_TEAL)
        btn_row.pack(side="right", padx=8, pady=8)
        # Keep only frequently used actions visible
        btn_refresh = tk.Button(btn_row, text="🔄 Refresh", command=self._refresh_books,
                                bg="#FFFFFF", fg="#0D2545", activebackground="#E5E7EB", activeforeground="#0D2545", relief="ridge")
        btn_refresh.pack(side="left")
        _tip(btn_refresh, "Reload books and rebuild all views (F5)")
        btn_theme = tk.Button(btn_row, text="🗂 Theme", command=self._open_theme_current,
                               bg="#FFFFFF", fg="#0D2545", activebackground="#E5E7EB", activeforeground="#0D2545", relief="ridge")
        btn_theme.pack(side="left", padx=(8, 0))
        _tip(btn_theme, "Open current book's theme folder (Ctrl+O)")
        btn_out = tk.Button(btn_row, text="📁 Output", command=lambda: self._open_path(STUDIOFORGE_DIR / "OUTPUT"),
                            bg="#FFFFFF", fg="#0D2545", activebackground="#E5E7EB", activeforeground="#0D2545", relief="ridge")
        btn_out.pack(side="left", padx=(8, 0))
        _tip(btn_out, "Open Studioforge/OUTPUT")
        btn_next = tk.Button(btn_row, text="Next ▶", command=self._do_next_step_current,
                             bg="#FFFFFF", fg="#0D2545", activebackground="#E5E7EB", activeforeground="#0D2545", relief="ridge")
        btn_next.pack(side="left", padx=(8, 0))
        _tip(btn_next, "Navigate (and optionally launch) the next recommended action for the current book")
        btn_tips = tk.Button(btn_row, text="💡 Tips", command=self._toggle_tips,
                             bg="#FFFFFF", fg="#0D2545", activebackground="#E5E7EB", activeforeground="#0D2545", relief="ridge")
        btn_tips.pack(side="left", padx=(8, 0))
        self._tips_btn = btn_tips
        # Overflow menu for rarely used items
        more = tk.Menubutton(btn_row, text="⋮ More", bg="#FFFFFF", fg="#0D2545", relief="ridge", activebackground="#E5E7EB")
        mnu = tk.Menu(more, tearoff=0)
        mnu.add_command(label="❓ Help", command=self._show_help)
        mnu.add_command(label="🧪 Diagnostics", command=self._show_diagnostics)
        mnu.add_command(label="⌨️ Command Palette (Ctrl+K)", command=self._open_command_palette)
        mnu.add_command(label="📚 Switch Book (Ctrl+B)", command=lambda: self._open_book_switcher())
        mnu.add_command(label="📜 Open Logs", command=self._open_logs)
        mnu.add_separator()
        mnu.add_command(label="📂 Open Themes", command=lambda: self._open_path(THEMES_DIR))
        mnu.add_command(label="📦 Open Packages", command=lambda p=STUDIOFORGE_DIR / "UPLOAD_READY", q=BASE_DIR / "03_UPLOAD_READY": self._open_path(p if p.exists() else q))
        mnu.add_command(label="📁 Open Canonical OUTPUTS", command=lambda: self._open_path(STUDIOFORGE_DIR / "_CANONICAL_LOCKED" / "OUTPUTS"))
        mnu.add_command(label="📦 Open Last Package", command=self._open_last_package_zip)
        mnu.add_separator()
        mnu.add_command(label="🚀 Open Icon Labeler (launch)", command=self._open_icon_labeler_from_tips)
        mnu.add_command(label="📄 Open PDF Extractor (launch)", command=self._open_pdf_extractor_from_tips)
        mnu.add_separator()
        mnu.add_command(label="↕️ Toggle Density", command=self._toggle_density)
        mnu.add_command(label="🌓 Toggle High Contrast", command=self._toggle_high_contrast)
        more.config(menu=mnu)
        more.pack(side="left", padx=(8, 0))
        try:
            ok_key, key_txt = self._anthropic_key_brief()
            lbl_key = tk.Label(header, text=("Claude ✓" if ok_key else "Claude ✗"), bg=SWS_TEAL, fg=("#E6FFFB" if ok_key else "#FFE4E6"), font=("Segoe UI", 9))
            lbl_key.pack(side="right", padx=(4, 8), pady=10)
            _tip(lbl_key, key_txt)
        except Exception:
            pass

        # Build Flow stepper (Setup → Icons → Activities → QA → Pack)
        try:
            self._flow_frame = tk.Frame(self, bg="#FFFFFF")
            self._flow_frame.pack(fill="x")
            self._build_flow_stepper()
        except Exception:
            pass

        try:
            self._show_tips = int(_read_log().get("_show_tips_launcher", 1))
        except Exception:
            self._show_tips = 1
        self._tips_frame = tk.Frame(self, bg="#E6FFFB")
        if self._show_tips:
            self._tips_frame.pack(fill="x")
        tipbox = tk.Frame(self._tips_frame, bg="#E6FFFB")
        tipbox.pack(fill="x", padx=12, pady=6)
        tip1 = tk.Label(tipbox, text="New here? Start on Guided Start: pick a book, then follow the checklist top to bottom. Sidebar pills show each tool's status for the current book (✓ done, • to do, n/15 icons).", bg="#E6FFFB", fg="#0D2545", justify="left", anchor="w", wraplength=980)
        tip1.pack(fill="x")
        tip2 = tk.Label(tipbox, text="Shortcuts: Enter = Launch • Ctrl+O = Open Theme • Ctrl+K = Command Palette • Ctrl+B = Switch Book • F5 = Refresh All • Full help under ⋮ More › Help.", bg="#E6FFFB", fg="#475569", justify="left", anchor="w", wraplength=980)
        tip2.pack(fill="x")
        def _rewrap_tips(e=None):
            try:
                w = max(300, self._tips_frame.winfo_width() - 28)
                tip1.config(wraplength=w); tip2.config(wraplength=w)
            except Exception:
                pass
        self._tips_frame.bind("<Configure>", _rewrap_tips)
        btnrow = tk.Frame(tipbox, bg="#E6FFFB")
        btnrow.pack(anchor="w", pady=(4, 0))
        tk.Button(btnrow, text="Open Icon Labeler", command=self._open_icon_labeler_from_tips,
                  bg="#FFFFFF", fg="#0D2545", activebackground="#E5E7EB", activeforeground="#0D2545", relief="ridge").pack(side="left")
        tk.Button(btnrow, text="Open PDF Extractor", command=self._open_pdf_extractor_from_tips,
                  bg="#FFFFFF", fg="#0D2545", activebackground="#E5E7EB", activeforeground="#0D2545", relief="ridge").pack(side="left", padx=(8, 0))
        try:
            _tip(btnrow.winfo_children()[0], "Start Icon Labeler (opens current/last book if available)")
            _tip(btnrow.winfo_children()[1], "Start integrated PDF Extractor (/pdf)")
        except Exception:
            pass
        try:
            self._tips_btn.config(text=("💡 Hide Tips" if self._show_tips else "💡 Show Tips"))
        except Exception:
            pass
        # Layout: left sidebar + right content (tabs hidden by style)
        body = tk.Frame(self, bg="#FFFFFF")
        body.pack(fill="both", expand=True)
        self._sidebar = tk.Frame(body, bg="#F9FAFB", width=240)
        self._sidebar.pack(side="left", fill="y")
        try:
            self._sidebar.pack_propagate(False)
        except Exception:
            pass
        right = tk.Frame(body, bg="#FFFFFF")
        right.pack(side="right", fill="both", expand=True)
        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill="both", expand=True)
        # Map tab ids to tool keys for tab-tooltips
        self._tab_tooltips = {}
        # Status bar with shortcut hints
        try:
            self.status = tk.Label(
                self,
                text="Enter: Launch • Ctrl+O: Open Theme • Ctrl+K: Command Palette • Ctrl+L: Logs • Ctrl+Shift+E: PDF • F5: Refresh All",
                anchor="w",
                bg="#FFFFFF",
                fg="#0D2545",
            )
            self.status.pack(fill="x", side="bottom")
        except Exception:
            pass

        self.books = _list_books()
        try:
            self._last_book_slug = _read_log().get("_last_book")
        except Exception:
            self._last_book_slug = None
        # Shared, sticky book selection across all product tabs
        self._shared_book_disp = tk.StringVar()
        self._shared_book_slug = tk.StringVar()
        self._label2slug = {}
        for b in self.books:
            slug = b["slug"]
            title = b.get("title") or slug.replace("_", " ").title()
            lab = (title or "").replace("_", " ")
            self._label2slug[lab] = slug
        default_label = (list(self._label2slug.keys())[0] if self._label2slug else "")
        try:
            last = self._last_book_slug
            if last:
                for lab, s in self._label2slug.items():
                    if s == last:
                        default_label = lab
                        break
        except Exception:
            pass
        self._shared_book_disp.set(default_label)
        try:
            self._global_book_var = tk.StringVar(value=default_label)
            gb = tk.Frame(self._header, bg=SWS_TEAL)
            gb.pack(side="left", padx=8)
            tk.Label(gb, text="Book:", fg="white", bg=SWS_TEAL).pack(side="left")
            try:
                opts = list(self._label2slug.keys())
            except Exception:
                opts = []
            try:
                om = tk.OptionMenu(gb, self._global_book_var, *opts, command=lambda v: self._set_global_book_by_label(v))
            except Exception:
                om = tk.OptionMenu(gb, self._global_book_var, *opts)
                try:
                    self._global_book_var.trace_add("write", lambda *_: self._set_global_book_by_label(self._global_book_var.get()))
                except Exception:
                    pass
            try:
                om.config(width=26, anchor="w")
            except Exception:
                pass
            om.pack(side="left")
            self._book_menu_tip = _ToolTip(om, self._global_book_var.get() or "Set current book across tools")
            try:
                self._global_book_var.trace_add("write", lambda *_: setattr(self._book_menu_tip, "text", self._global_book_var.get() or ""))
            except Exception:
                pass
            # Icons curated count chip
            try:
                self._icons_chip = tk.Label(gb, text="", bg=SWS_TEAL, fg="#FFFFFF")
                self._icons_chip.pack(side="left", padx=(8, 0))
            except Exception:
                self._icons_chip = None
            try:
                cur_slug = self._label2slug.get(self._global_book_var.get())
                if cur_slug:
                    self._update_header_icons_chip(cur_slug)
            except Exception:
                pass
        except Exception:
            pass
        try:
            self._density = _read_log().get("_density", "comfortable")
        except Exception:
            self._density = "comfortable"
        # Apply density and update header button label
        try:
            self._apply_density()
            self._density_btn.config(text=f"↕️ Density: {self._density.title()}")
        except Exception:
            pass
        # Load and apply High Contrast preference
        try:
            self._high_contrast = bool(int(_read_log().get("_high_contrast", 0)))
        except Exception:
            self._high_contrast = False
        try:
            self._apply_high_contrast()
            self._contrast_btn.config(text=f"🌓 High Contrast: {'On' if self._high_contrast else 'Off'}")
        except Exception:
            pass

        self._init_board_tab()
        self._init_matching_tab()
        self._init_guided_tab()
        self._init_code_words_tab()
        self._init_book_insert_strips_tab()
        self._init_listing_tab()
        self._init_ai_tab()
        self._init_topic_builder_tab()
        self._init_icon_labeler_tab()
        self._init_review_tab()
        self._init_pack_tab()
        self._init_qa_tab()
        # Build the left sidebar navigation after tabs exist
        try:
            self._build_left_nav()
        except Exception:
            pass
        try:
            self._bind_shortcuts()
        except Exception:
            pass
        try:
            self.bind("<Control-b>", lambda e: self._open_book_switcher())
        except Exception:
            pass
        try:
            self.tabs.bind("<<NotebookTabChanged>>", self._on_tab_change)
            self._set_initial_tab_from_log()
            try:
                cur = self.tabs.tab(self.tabs.select(), "text")
                self._highlight_nav_for_text(cur)
            except Exception:
                pass
        except Exception:
            pass
        try:
            # Bind lightweight per-tab tooltip logic
            self.tabs.bind("<Motion>", self._on_tabs_motion)
            self.tabs.bind("<Leave>", self._on_tabs_leave)
        except Exception:
            pass
        try:
            self.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception:
            pass
        try:
            slug = self._current_slug_guess()
            if slug:
                self._update_flow_stepper(slug)
        except Exception:
            pass

    def _palette_items(self):
        items = []
        try:
            items.append(("Next Step", self._do_next_step_current))
            items.append(("Open Theme Folder", lambda: self._open_theme_current()))
            items.append(("Open Output Folder", lambda: self._open_output_for(self._current_slug_guess(), self._pack_code_for_slug(self._current_slug_guess() or ""))))
            items.append(("Open Canonical OUTPUTS", lambda: self._open_path(STUDIOFORGE_DIR / "_CANONICAL_LOCKED" / "OUTPUTS")))
            items.append(("Open Logs", self._open_logs))
            items.append(("Diagnostics", self._show_diagnostics))
            items.append(("Toggle High Contrast", self._toggle_high_contrast))
            items.append(("Toggle Density", self._toggle_density))
            items.append(("Open Icon Labeler (launch)", self._open_icon_labeler_from_tips))
            items.append(("Open PDF Extractor (launch)", self._open_pdf_extractor_from_tips))
        except Exception:
            pass
        for txt in ["Guided Start", "Matching", "Board Ready", "Icon Labeler", "QA Review", "Pipeline Dashboard", "Jobs + Progress", "Pack Ready", "AI Pre-Populate", "Topic Content Builder", "Listing Generator"]:
            items.append((f"Go: {txt}", lambda t=txt: self._select_tab_by_text(t)))
        try:
            for lab, slug in (self._label2slug or {}).items():
                items.append((f"Book: {lab}", lambda l=lab: self._shared_book_disp.set(l)))
        except Exception:
            pass
        return items

    def _open_command_palette(self):
        try:
            items = self._palette_items()
        except Exception:
            items = []
        win = tk.Toplevel(self)
        try:
            win.transient(self)
        except Exception:
            pass
        win.title("Command Palette")
        frm = tk.Frame(win)
        frm.pack(fill="both", expand=True, padx=10, pady=10)
        q = tk.StringVar()
        ent = tk.Entry(frm, textvariable=q, width=60)
        ent.pack(fill="x")
        lb = tk.Listbox(frm, height=12)
        lb.pack(fill="both", expand=True, pady=(6, 0))
        data = [(lbl, fn) for (lbl, fn) in items]
        for lbl, _ in data:
            lb.insert("end", lbl)
        def _apply_filter(*_):
            s = (q.get() or "").strip().lower()
            lb.delete(0, "end")
            for lbl, _ in data:
                if not s or s in lbl.lower():
                    lb.insert("end", lbl)
            try:
                lb.selection_set(0)
            except Exception:
                pass
        def _run_selected(*_):
            try:
                idxs = lb.curselection()
                if not idxs:
                    return
                sel = lb.get(idxs[0])
                for lbl, fn in data:
                    if lbl == sel and callable(fn):
                        win.destroy()
                        fn()
                        return
            except Exception:
                win.destroy()
        ent.bind("<KeyRelease>", _apply_filter)
        ent.bind("<Return>", _run_selected)
        lb.bind("<Return>", _run_selected)
        def _esc(*_):
            try:
                win.destroy()
            except Exception:
                pass
        ent.bind("<Escape>", _esc)
        lb.bind("<Escape>", _esc)
        try:
            ent.focus_set()
            lb.selection_set(0)
        except Exception:
            pass

    def _book_selector(self, parent):
        row = tk.Frame(parent, bg="#FFFFFF")
        row.pack(fill="x", pady=4)
        tk.Label(row, text="Book:", width=14, anchor="e", bg="#FFFFFF", fg="#0D2545").pack(side="left")
        labels = list(self._label2slug.keys())
        disp_var = self._shared_book_disp
        cb = ttk.Combobox(row, values=labels, textvariable=disp_var, state="readonly", width=44)
        cb.pack(side="left")
        btn_find = tk.Button(row, text="🔎 Find…", command=lambda: self._find_book_dialog(cb, self._label2slug))
        btn_find.pack(side="left", padx=6)
        _tip(btn_find, "Quick search across all books")
        # Icons X/15 chip
        chip = tk.Label(row, text="", padx=6, pady=1, bg="#FFFFFF", font=("Segoe UI", 8, "bold"))
        chip.pack(side="left", padx=(6,0))
        _tip(chip, "Curated activity icons for this book (15 needed)")

        # Title and Code fields (collapsed by default; header Book picker is global)
        details = tk.Frame(parent, bg="#FFFFFF")
        def _toggle_details():
            if details.winfo_manager():
                details.pack_forget(); btn_det.config(text="Details ▸")
            else:
                details.pack(fill="x", after=row); btn_det.config(text="Details ▾")
        btn_det = tk.Button(row, text="Details ▸", relief="flat", bd=0, bg="#FFFFFF", fg="#475569", cursor="hand2", command=_toggle_details)
        btn_det.pack(side="left", padx=(8, 0))
        _tip(btn_det, "Show/hide title and pack code for this book")
        row2 = tk.Frame(details, bg="#FFFFFF")
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="Title:", width=14, anchor="e", bg="#FFFFFF", fg="#0D2545").pack(side="left")
        title_var = tk.StringVar()
        tk.Entry(row2, textvariable=title_var, width=40).pack(side="left")

        row3 = tk.Frame(details, bg="#FFFFFF")
        row3.pack(fill="x", pady=2)
        tk.Label(row3, text="Pack code:", width=14, anchor="e", bg="#FFFFFF", fg="#0D2545").pack(side="left")
        code_var = tk.StringVar()
        tk.Entry(row3, textvariable=code_var, width=12).pack(side="left")
        btn_save_code = tk.Button(row3, text="Save Pack Code", command=lambda: self._save_pack_code((slug_var.get() or "").strip(), (code_var.get() or "").strip()))
        btn_save_code.pack(side="left", padx=(6, 0))
        _tip(btn_save_code, "Persist this code to assets/themes/<slug>/book_vocab.json")

        slug_var = self._shared_book_slug

        def _refresh_fields(*_):
            lab = disp_var.get()
            slug = self._label2slug.get(lab, lab)
            slug_var.set(slug)
            self._last_book_slug = slug
            meta = next((b for b in self.books if b["slug"] == slug), None)
            if meta:
                title_var.set(meta.get("title") or slug.replace("_", " ").title())
                code_var.set(meta.get("code") or (slug[:3].upper() + "1"))
            # Update icons chip
            try:
                n = self._count_activity_icons(slug)
                _pill(chip, f"Icons {n}/15", "done" if n >= 15 else ("warn" if n >= 10 else "todo"))
            except Exception:
                pass
        disp_var.trace_add("write", _refresh_fields)
        _refresh_fields()

        return slug_var, title_var, code_var

    def _find_book_dialog(self, cb, label2slug: dict):
        try:
            win = tk.Toplevel(self)
            win.title("Find Book")
            win.geometry("420x480")
            top = tk.Frame(win)
            top.pack(fill="x", padx=8, pady=8)
            tk.Label(top, text="Filter:").pack(side="left")
            var = tk.StringVar()
            ent = tk.Entry(top, textvariable=var, width=28)
            ent.pack(side="left", padx=(6, 0))
            mid = tk.Frame(win)
            mid.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            sb = tk.Scrollbar(mid, orient="vertical")
            lst = tk.Listbox(mid, yscrollcommand=sb.set)
            sb.config(command=lst.yview)
            lst.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            all_labels = sorted(label2slug.keys(), key=lambda s: s.lower())

            def _refresh(*_):
                term = (var.get() or "").strip().lower()
                lst.delete(0, tk.END)
                for lab in all_labels:
                    if term in lab.lower():
                        lst.insert(tk.END, lab)

            def _choose():
                try:
                    sel = lst.curselection()
                    if not sel:
                        return
                    lab = lst.get(sel[0])
                    cb.set(lab)
                    try:
                        cb.event_generate("<<ComboboxSelected>>")
                    except Exception:
                        pass
                    win.destroy()
                except Exception:
                    pass

            _refresh()
            var.trace_add("write", _refresh)
            lst.bind("<Double-Button-1>", lambda *_: _choose())
            lst.bind("<Return>", lambda *_: _choose())
            bot = tk.Frame(win)
            bot.pack(fill="x", padx=8, pady=(0, 8))
            tk.Button(bot, text="Select", command=_choose).pack(side="left")
            tk.Button(bot, text="Close", command=win.destroy).pack(side="right")
            try:
                ent.focus_set()
                ent.select_range(0, tk.END)
            except Exception:
                pass
        except Exception:
            pass

    def _card(self, parent, tool_key):
        f = tk.Frame(parent, padx=16, pady=12, bg="#FFFFFF")
        f.pack(fill="both", expand=True)
        tk.Label(f, text=TOOLS[tool_key]["name"], font=("Segoe UI", 12, "bold"), bg="#FFFFFF", fg="#0D2545").pack(anchor="w")
        tk.Label(f, text=TOOLS[tool_key]["desc"], fg="#0D2545", bg="#FFFFFF", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 6))
        try:
            tip_txt = (TOOLS.get(tool_key, {}) or {}).get("tip")
        except Exception:
            tip_txt = None
        if tip_txt:
            cof = tk.Frame(f, bg="#E6FFFB", bd=1, relief="solid")
            cof.pack(fill="x", pady=(0, 10))
            tk.Label(cof, text=f"💡 Top tip: {tip_txt}", bg="#E6FFFB", fg="#0D2545", anchor="w", justify="left").pack(anchor="w", padx=8, pady=6)
        lu = tk.Label(f, text=f"Last used: {_last_used(tool_key)}", fg="#0D2545", bg="#FFFFFF")
        lu.pack(anchor="w", pady=(0, 16))
        return f, lu

    # Sidebar navigation helpers --------------------------------------------
    def _is_tool_new(self, tool_key: str) -> bool:
        try:
            added = (TOOL_ADDED_DATES.get(tool_key) or "").strip()
            if not added:
                return False
            dt = datetime.fromisoformat(added)
            return (datetime.now() - dt) <= timedelta(days=int(NEW_WINDOW_DAYS))
        except Exception:
            return False

    def _build_left_nav(self):
        try:
            # Clear old items
            for c in list(self._sidebar.children.values()):
                try:
                    c.destroy()
                except Exception:
                    pass
            self._nav_btns = {}
            self._nav_badges = {}
            self._nav_rows = {}
            for gi, (grp, items) in enumerate(NAV_GROUPS):
                hdr = tk.Label(self._sidebar, text=grp.upper(), bg=NAV_BG, fg="#64748B", anchor="w", font=("Segoe UI", 8, "bold"))
                hdr.pack(fill="x", padx=14, pady=((12 if gi else 10), 2))
                for disp, tool_key in items:
                    row = tk.Frame(self._sidebar, bg=NAV_BG)
                    row.pack(fill="x", padx=6, pady=1)
                    bar = tk.Frame(row, bg=NAV_BG, width=3)
                    bar.pack(side="left", fill="y")
                    btn = tk.Button(row, text=disp, anchor="w", relief="flat", bd=0,
                                    bg=NAV_BG, fg="#0D2545",
                                    activebackground=NAV_ACTIVE_BG, activeforeground="#0D2545", font=("Segoe UI", 10),
                                    command=lambda t=disp: self._nav_select_by_text(t))
                    btn.pack(side="left", fill="x", expand=True, padx=(6, 0))
                    self._nav_btns[disp] = btn
                    self._nav_rows[disp] = (row, bar)
                    try:
                        if tool_key and self._is_tool_new(tool_key):
                            badge = tk.Label(row, text="New", bg="#DCFCE7", fg="#14532D", padx=4, pady=0, font=("Segoe UI", 8, "bold"))
                            badge.pack(side="right", padx=(4, 6))
                    except Exception:
                        pass
                    try:
                        b = tk.Label(row, text="", bg=NAV_BG, fg="#0D2545", padx=5, pady=0, font=("Segoe UI", 8, "bold"))
                        b.pack(side="right", padx=(4, 4))
                        self._nav_badges[disp] = b
                    except Exception:
                        pass
                    try:
                        if tool_key and tool_key in TOOLS:
                            _tip(btn, TOOLS[tool_key].get("tip") or TOOLS[tool_key].get("desc") or disp)
                    except Exception:
                        pass
            # Initial highlight
            try:
                cur = self.tabs.tab(self.tabs.select(), "text")
            except Exception:
                cur = None
            if cur:
                self._highlight_nav_for_text(cur)
            try:
                slug = self._current_slug_guess()
                if slug:
                    self._update_nav_badges(slug)
            except Exception:
                pass
        except Exception:
            pass

    def _highlight_nav_for_text(self, text: str | None):
        try:
            for name, btn in (getattr(self, "_nav_btns", {}) or {}).items():
                on = bool(text and name == text)
                btn.configure(bg=(NAV_ACTIVE_BG if on else NAV_BG), font=("Segoe UI", 10, "bold" if on else "normal"))
                try:
                    row, bar = self._nav_rows.get(name, (None, None))
                    if row is not None:
                        row.configure(bg=(NAV_ACTIVE_BG if on else NAV_BG))
                        bar.configure(bg=(SWS_TEAL if on else (NAV_ACTIVE_BG if on else NAV_BG)))
                        badge = self._nav_badges.get(name)
                        if badge is not None and not badge.cget("text"):
                            badge.configure(bg=(NAV_ACTIVE_BG if on else NAV_BG))
                except Exception:
                    pass
        except Exception:
            pass

    def _guided_status_async(self, slug: str, callback):
        """Deliver guided status for slug via callback on the Tk thread; uses cache when fresh."""
        try:
            if not slug:
                callback(slug, self._guided_status(""))
                return
            cached = getattr(self, "_guided_cache", {}).get(slug)
            if cached and (time.time() - cached.get("_ts", 0)) < 20:
                callback(slug, cached)
                return
            def _worker(s=slug):
                try:
                    st = self._guided_status(s)
                except Exception:
                    st = self._guided_status("")
                try:
                    self.after(0, lambda: callback(s, st))
                except Exception:
                    pass
            threading.Thread(target=_worker, daemon=True).start()
        except Exception:
            pass

    # Build Flow stepper -----------------------------------------------------
    def _build_flow_stepper(self):
        try:
            for c in list(getattr(self, "_flow_frame", {}).children.values() if hasattr(self, "_flow_frame") else []):
                try:
                    c.destroy()
                except Exception:
                    pass
            if not hasattr(self, "_flow_frame"):
                return
            row = tk.Frame(self._flow_frame, bg="#FFFFFF")
            row.pack(fill="x", padx=12, pady=(6, 4))
            tk.Label(row, text="Pipeline", bg="#FFFFFF", fg="#64748B", font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 8))
            stages = []
            for _k, stage, *_rest in self.GUIDED_STEPS:
                if stage not in stages:
                    stages.append(stage)
            self._flow_steps = {}
            for i, name in enumerate(stages):
                w = tk.Label(row, text=name, padx=8, pady=2, bg=PILL["neutral"][1], fg=PILL["neutral"][0], cursor="hand2", font=("Segoe UI", 9))
                w.pack(side="left")
                self._flow_steps[name] = w
                _tip(w, f"{name}: click to open Guided Start")
                if i < len(stages) - 1:
                    tk.Label(row, text="›", bg="#FFFFFF", fg="#94A3B8").pack(side="left", padx=5)
            tk.Frame(self._flow_frame, bg="#E5E7EB", height=1).pack(fill="x")
        except Exception:
            pass

    def _flow_chip(self, w, text, fg, bg, cmd=None):
        try:
            if w is None:
                return
            w.config(text=text, fg=fg, bg=bg)
            try:
                w.unbind("<Button-1>")
            except Exception:
                pass
            if callable(cmd):
                w.bind("<Button-1>", lambda *_: cmd())
        except Exception:
            pass

    def _update_flow_stepper(self, slug: str):
        try:
            if not getattr(self, "_flow_steps", None):
                return
            if not slug:
                for name, w in self._flow_steps.items():
                    self._flow_chip(w, name, *PILL["neutral"], cmd=self._open_book_switcher)
                return
            for name, w in self._flow_steps.items():
                if not (w.cget("text") or "").startswith(name) or "/" not in w.cget("text"):
                    self._flow_chip(w, f"{name} …", *PILL["neutral"])
            self._guided_status_async(slug, self._paint_flow_stepper)
        except Exception:
            pass

    def _paint_flow_stepper(self, slug: str, st: dict):
        try:
            if slug != self._current_slug_guess():
                return
            per = {}
            for key, stage, _name, _hint, required, _tab, _rk in self.GUIDED_STEPS:
                d, t, first_missing = per.get(stage, (0, 0, None))
                if required:
                    t += 1
                    if st.get(key):
                        d += 1
                    elif first_missing is None:
                        first_missing = key
                per[stage] = (d, t, first_missing)
            blocked = False
            for name, w in self._flow_steps.items():
                d, t, missing = per.get(name, (0, 0, None))
                if d >= t:
                    state = "done"
                elif blocked:
                    state = "neutral"
                elif d > 0:
                    state = "warn"
                else:
                    state = "todo"
                if d < t:
                    blocked = True
                self._flow_chip(w, f"{name} {d}/{t}", *PILL[state], cmd=lambda: self._nav_select_by_text("Guided Start"))
        except Exception:
            pass

    # Global book handlers and nav badges (class versions) -------------------
    def _set_global_book_by_label(self, label: str):
        try:
            slug = self._label2slug.get(label)
        except Exception:
            slug = None
        if not slug:
            return
        try:
            for tid in list(self.tabs.tabs()):
                try:
                    tf = self.nametowidget(tid)
                    ctx = getattr(tf, "_ctx", None)
                    if ctx:
                        sv = ctx.get("slug_var")
                        if sv:
                            try:
                                sv.set(slug)
                            except Exception:
                                pass
                except Exception:
                    continue
            self._remember_last_book(slug)
            try:
                self._update_header_icons_chip(slug)
            except Exception:
                pass
            try:
                self._update_nav_badges(slug)
            except Exception:
                pass
            try:
                self._update_flow_stepper(slug)
            except Exception:
                pass
        except Exception:
            pass

    def _canonical_outputs_present(self, slug: str) -> bool:
        try:
            manp = STUDIOFORGE_DIR / "_CANONICAL_LOCKED" / "OUTPUTS" / "manifest.json"
            if manp.exists() and slug:
                try:
                    man = json.loads(manp.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    man = {}
                for _product, themes in (man or {}).items():
                    if isinstance(themes, dict) and slug in themes:
                        paths = (themes.get(slug, {}) or {}).get("paths", {})
                        for v in paths.values():
                            try:
                                if (BASE_DIR / v).exists():
                                    return True
                            except Exception:
                                continue
                        break
            root = STUDIOFORGE_DIR / "_CANONICAL_LOCKED" / "OUTPUTS"
            try:
                if root.exists():
                    for p in root.rglob(slug):
                        try:
                            if p.is_dir() and any(x.suffix.lower()==".pdf" for x in p.glob("*.pdf")):
                                return True
                        except Exception:
                            continue
            except Exception:
                pass
        except Exception:
            pass
        return False

    def _update_nav_badges(self, slug: str):
        try:
            if not getattr(self, "_nav_badges", None):
                return
            self._guided_status_async(slug, self._paint_nav_badges)
        except Exception:
            pass

    # nav label -> (status key, kind) ; kind: req | opt | count
    NAV_BADGE_KEYS = {
        "AI Pre-Populate": ("vocab", "req"),
        "Icon Labeler": ("icons", "count"),
        "Matching": ("matching", "req"),
        "Board Ready": ("board", "req"),
        "Code Words": ("code_words", "opt"),
        "Book Insert Strips": ("strips", "opt"),
        "Listing Generator": ("listing", "req"),
        "Pack Ready": ("package", "req"),
    }

    def _paint_nav_badges(self, slug: str, st: dict):
        try:
            if slug and slug != self._current_slug_guess():
                return
            try:
                cur = self.tabs.tab(self.tabs.select(), "text")
            except Exception:
                cur = None
            for name, lab in (getattr(self, "_nav_badges", {}) or {}).items():
                spec = self.NAV_BADGE_KEYS.get(name)
                if not spec or not slug:
                    lab.config(text="", bg=(NAV_ACTIVE_BG if name == cur else NAV_BG))
                    continue
                key, kind = spec
                ok = bool(st.get(key))
                if kind == "count":
                    n = int(st.get("icons_n") or 0)
                    _pill(lab, f"{n}/15", "done" if ok else ("warn" if n >= 10 else "todo"))
                elif ok:
                    _pill(lab, "✓", "done")
                else:
                    _pill(lab, "•", "warn" if kind == "opt" else "todo")
        except Exception:
            pass

    def _open_book_switcher(self):
        try:
            win = tk.Toplevel(self)
            win.title("Switch Book")
            try:
                win.geometry("420x480")
            except Exception:
                pass
            top = tk.Frame(win)
            top.pack(fill="x", padx=8, pady=8)
            tk.Label(top, text="Filter:").pack(side="left")
            var = tk.StringVar()
            ent = tk.Entry(top, textvariable=var, width=28)
            ent.pack(side="left", padx=(6, 0))
            mid = tk.Frame(win)
            mid.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            sb = tk.Scrollbar(mid, orient="vertical")
            lst = tk.Listbox(mid, yscrollcommand=sb.set)
            sb.config(command=lst.yview)
            lst.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            all_labels = sorted(self._label2slug.keys(), key=lambda s: s.lower())

            def _refresh(*_):
                term = (var.get() or "").strip().lower()
                lst.delete(0, tk.END)
                for lab in all_labels:
                    if term in lab.lower():
                        lst.insert(tk.END, lab)

            def _choose(*_):
                try:
                    sel = lst.curselection()
                    if not sel:
                        return
                    lab = lst.get(sel[0])
                    self._global_book_var.set(lab)
                    self._set_global_book_by_label(lab)
                    win.destroy()
                except Exception:
                    pass

            _refresh()
            var.trace_add("write", _refresh)
            lst.bind("<Double-Button-1>", _choose)
            lst.bind("<Return>", _choose)
            bot = tk.Frame(win)
            bot.pack(fill="x", padx=8, pady=(0, 8))
            tk.Button(bot, text="Select", command=_choose).pack(side="left")
            tk.Button(bot, text="Close", command=win.destroy).pack(side="right")
            try:
                ent.focus_set()
                ent.select_range(0, tk.END)
            except Exception:
                pass
        except Exception:
            pass

    def _update_header_icons_chip(self, slug: str):
        try:
            n = self._count_activity_icons(slug)
        except Exception:
            n = 0
        try:
            fg, bg = self._icons_chip_style(n)
        except Exception:
            fg, bg = ("#0D2545", "#FFFFFF")
        try:
            if getattr(self, "_icons_chip", None):
                self._icons_chip.config(text=f"Icons {n}/15", fg=fg, bg=bg)
        except Exception:
            pass

    def _nav_select_by_text(self, text: str):
        try:
            self._select_tab_by_text(text)
            self._highlight_nav_for_text(text)
        except Exception:
            pass

    def _make_launch_callable(self, tool_key, sv, tv, cv, lu):
        try:
            if tool_key == "board_ready":
                return lambda: self._launch_board_ready(sv.get(), tv.get(), cv.get(), lu)
            if tool_key == "matching":
                return lambda: self._launch_matching(sv.get(), tv.get(), cv.get(), lu)
            if tool_key == "listing_generator":
                return lambda: self._launch_listing(sv.get(), lu)
            if tool_key == "icon_labeler":
                return lambda: self._launch_icon_labeler(lu)
            if tool_key == "code_words":
                return lambda: self._launch_code_words(sv.get(), tv.get(), cv.get(), lu)
            if tool_key == "book_insert_strips":
                return lambda: self._launch_book_insert_strips(sv.get(), tv.get(), cv.get(), lu)
        except Exception:
            pass
        return lambda: messagebox.showinfo("Not wired", f"Tool '{tool_key}' is not launchable yet.")

    def _setup_book_tab(self, tab, tool_key):
        card, lu = self._card(tab, tool_key)
        sel_frame = tk.Frame(card, bg="#FFFFFF")
        sel_frame.pack(fill="x")
        slug_var, title_var, code_var = self._book_selector(sel_frame)
        launch_fn = self._make_launch_callable(tool_key, slug_var, title_var, code_var, lu)
        padY = 6 if getattr(self, "_density", "comfortable") == "compact" else 12
        btn = tk.Button(card, text="Launch", bg=SWS_TEAL, fg="white", relief="ridge", command=launch_fn)
        btn.pack(anchor="w", pady=padY)
        try:
            _tip(btn, "Launch (Enter)")
        except Exception:
            pass
        st = tk.Label(card, text="", fg="#0D2545", bg="#FFFFFF")
        st.pack(anchor="w", pady=(0, 4))
        try:
            def _on_slug_change(*_):
                try:
                    self._update_preflight(tool_key, slug_var.get(), btn, st)
                except Exception:
                    pass
                try:
                    if callable(locals().get("_update_next_step")):
                        _update_next_step()
                except Exception:
                    pass
            slug_var.trace_add("write", _on_slug_change)
            self._update_preflight(tool_key, slug_var.get(), btn, st)
        except Exception:
            pass
        nsf = tk.Frame(card, bg="#FFFFFF")
        nsf.pack(anchor="w", pady=(2, 6))
        ns_label = tk.Label(nsf, text="", fg="#0D2545", bg="#FFFFFF")
        ns_label.pack(side="left")
        ns_btn = tk.Button(nsf, text="")
        ns_btn.pack(side="left", padx=8)
        def _update_next_step():
            try:
                slug = slug_var.get()
                ready, _msg, n = self._icons_ready_and_count(slug)
                if not ready:
                    ns_label.config(text=f"Next step: Add icons ({n}/15)")
                    ns_btn.config(text="Open Icon Labeler", command=lambda: self._select_tab_by_text("Icon Labeler"))
                else:
                    ns_label.config(text=f"Next step: Run Matching ({n}/15 ready)")
                    ns_btn.config(text="Go to Matching", command=lambda: self._select_tab_by_text("Matching"))
            except Exception:
                pass
        try:
            _update_next_step()
        except Exception:
            pass
        ql = tk.Frame(card, bg="#FFFFFF")
        ql.pack(anchor="w")
        open_theme_btn = tk.Button(ql, text="📂 Open Theme Folder", command=lambda: self._open_theme_folder(slug_var.get()))
        open_theme_btn.pack(side="left")
        _tip(open_theme_btn, "Open assets/themes/<slug>")
        open_output_btn = tk.Button(ql, text="📦 Open Output Folder", command=lambda: self._open_output_for(slug_var.get(), code_var.get()))
        open_output_btn.pack(side="left", padx=6)
        _tip(open_output_btn, "Open OUTPUT directory for this pack")
        try:
            manage_codes_btn = tk.Button(ql, text="🏷 Manage Pack Codes…", command=self._open_pack_codes_dialog)
            manage_codes_btn.pack(side="left", padx=6)
            _tip(manage_codes_btn, "View all books, derived codes, and September/back‑to‑school flags. Save codes per book.")
        except Exception:
            pass
        try:
            gp = _resolved_generator_path(tool_key)
            if gp and Path(gp).exists():
                btn_gen = tk.Button(ql, text="🔧 Open Generator Script", command=lambda p=gp: self._open_path(p))
                btn_gen.pack(side="left", padx=6)
                _tip(btn_gen, f"Open generator script ({Path(gp).name})")
        except Exception:
            pass
        try:
            if tool_key in ("board_ready", "matching"):
                btn_ic = tk.Button(ql, text="🧾 Open Icons Checklist", command=lambda: _open_icons_checklist(slug_var.get()))
                btn_ic.pack(side="left", padx=6)
                _tip(btn_ic, "Open per-book icons checklist UI")
        except Exception:
            pass
        try:
            tab._ctx = {
                "tool": tool_key,
                "slug_var": slug_var,
                "title_var": title_var,
                "code_var": code_var,
                "lu": lu,
                "launch": launch_fn,
            }
        except Exception:
            pass
        return card

    def _save_pack_code(self, slug: str, code: str):
        try:
            slug = (slug or "").strip()
            code = (code or "").strip()
            if not slug:
                messagebox.showwarning("Pack Code", "Select a book first.")
                return
            if not code:
                messagebox.showwarning("Pack Code", "Enter a pack code to save.")
                return
            theme = THEMES_DIR / slug
            root_cfg = theme / "book_vocab.json"
            cfg = root_cfg if root_cfg.exists() else (theme / "config" / "book_vocab.json")
            if not cfg.exists():
                messagebox.showerror("Pack Code", f"Missing book_vocab.json for {slug}.")
                return
            try:
                obj = json.loads(cfg.read_text(encoding="utf-8"))
            except Exception:
                obj = {}
            obj["code"] = code
            try:
                txt = json.dumps(obj, ensure_ascii=False, indent=2)
                cfg.write_text(txt, encoding="utf-8")
            except Exception as e:
                messagebox.showerror("Pack Code", str(e))
                return
            # Refresh books cache
            try:
                self.books = _list_books()
            except Exception:
                pass
            messagebox.showinfo("Pack Code", f"Saved pack code '{code}' for {slug}.")
        except Exception as e:
            try:
                messagebox.showerror("Pack Code", str(e))
            except Exception:
                pass

    def _derive_pack_code(self, slug: str, title: str) -> str:
        try:
            # Prefer acronym from title words, dropping small stopwords
            stop = {"the","a","an","of","and","to","in","on","for","with","at","by"}
            words = [w for w in re.split(r"[^A-Za-z0-9]+", str(title or "")) if w]
            letters = [w[0].upper() for w in words if w.lower() not in stop]
            if len(letters) >= 3:
                return ("".join(letters))[:5]
            # Fallback to slug parts
            parts = [p for p in str(slug or "").split("_") if p]
            if parts:
                ac = "".join(p[0] for p in parts).upper()
                return (ac or (slug[:3].upper() or "UNK"))[:5]
            return (slug[:3].upper() or "UNK")
        except Exception:
            return (slug[:3].upper() or "UNK")

    def _is_september_title(self, slug: str, title: str) -> bool:
        try:
            t = f"{slug} {title}".lower()
            keys = ["september", "back to school", "school", "first day", "classroom"]
            return any(k in t for k in keys)
        except Exception:
            return False

    def _open_pack_codes_dialog(self):
        try:
            win = tk.Toplevel(self)
            win.title("Manage Pack Codes")
            frm = tk.Frame(win)
            frm.pack(fill="both", expand=True, padx=10, pady=8)
            cols = ("Title", "Slug", "Current", "Derived", "September?")
            tv = ttk.Treeview(frm, columns=cols, show="headings", height=16)
            for c in cols:
                tv.heading(c, text=c)
                tv.column(c, width=140 if c != "Title" else 260, anchor="w")
            tv.pack(fill="both", expand=True)
            sb = tk.Scrollbar(frm, orient="vertical", command=tv.yview)
            tv.configure(yscrollcommand=sb.set)
            sb.pack(side="right", fill="y")

            btns = tk.Frame(win)
            btns.pack(fill="x", padx=10, pady=(6, 8))
            sel_code_var = tk.StringVar()
            tk.Label(btns, text="New code:").pack(side="left")
            ent = tk.Entry(btns, textvariable=sel_code_var, width=14)
            ent.pack(side="left", padx=(4, 8))

            def on_row_select(_e=None):
                try:
                    cur = tv.focus()
                    if not cur:
                        sel_code_var.set("")
                        return
                    vals = tv.item(cur, "values")
                    # Prefill with current or derived
                    sel_code_var.set(vals[2] or vals[3] or "")
                except Exception:
                    sel_code_var.set("")
            tv.bind("<<TreeviewSelect>>", on_row_select)

            def do_save():
                try:
                    cur = tv.focus()
                    if not cur:
                        messagebox.showwarning("Manage Pack Codes", "Select a book.")
                        return
                    vals = tv.item(cur, "values")
                    title, slug, curc, der = vals[0], vals[1], vals[2], vals[3]
                    code = (sel_code_var.get() or curc or der or "").strip()
                    if not code:
                        messagebox.showwarning("Manage Pack Codes", "Enter a code.")
                        return
                    self._save_pack_code(slug, code)
                    # Refresh row values
                    try:
                        for i in tv.get_children():
                            tv.delete(i)
                    except Exception:
                        pass
                    fill_table()
                except Exception as e:
                    messagebox.showerror("Manage Pack Codes", str(e))

            tk.Button(btns, text="Save for selected", command=do_save).pack(side="left")

            def fill_table():
                try:
                    # Build records — September titles first, then alphabetic
                    recs = []
                    for b in (self.books or []):
                        slug = b.get("slug")
                        title = b.get("title") or (slug or "").replace("_", " ").title()
                        curc = b.get("code") or ""
                        der = self._derive_pack_code(slug, title)
                        sep = self._is_september_title(slug, title)
                        recs.append((sep, title, slug, curc, der))
                    recs.sort(key=lambda x: (not x[0], x[1].lower()))
                    # Style tag for September
                    try:
                        tv.tag_configure("sep", background="#FFF7CC")
                    except Exception:
                        pass
                    for sep, title, slug, curc, der in recs:
                        vals = (title, slug, curc, der, "Yes" if sep else "")
                        iid = tv.insert("", "end", values=vals)
                        if sep:
                            try:
                                tv.item(iid, tags=("sep",))
                            except Exception:
                                pass
                except Exception:
                    pass

            fill_table()
        except Exception:
            pass

    def _init_board_tab(self):
        tab = tk.Frame(self.tabs)
        self.tabs.add(tab, text="Board Ready")
        self._setup_book_tab(tab, "board_ready")
        try:
            tid = self.tabs.tabs()[-1]
            self._tab_tooltips[tid] = TOOLS["board_ready"]["desc"]
        except Exception:
            pass

    def _init_matching_tab(self):
        tab = tk.Frame(self.tabs)
        self.tabs.add(tab, text="Matching")
        card = self._setup_book_tab(tab, "matching")
        try:
            tid = self.tabs.tabs()[-1]
            self._tab_tooltips[tid] = TOOLS["matching"]["desc"]
        except Exception:
            pass
        try:
            ctx = getattr(tab, "_ctx", None)
            if isinstance(ctx, dict) and "slug_var" in ctx:
                sv = ctx["slug_var"]
                btn_cc = tk.Button(card, text="📝 Open cover_config.json", command=lambda: self._open_cover_config_for(sv.get()))
                btn_cc.pack(anchor="w")
                _tip(btn_cc, "Edit per-activity cover content")
        except Exception:
            pass

    def _guided_status(self, slug: str, force: bool = False) -> dict:
        if not hasattr(self, "_guided_cache"):
            self._guided_cache = {}
        try:
            hit = self._guided_cache.get(slug)
            if hit and not force and (time.time() - hit.get("_ts", 0)) < 20:
                return hit
        except Exception:
            pass
        st = {"_ts": time.time(), "icons_n": 0, "icons_ok": False, "hero": False, "cover": False,
              "matching": False, "board": False, "docs": False}
        if not slug:
            return st
        try:
            ok, _msg, n = self._icons_ready_and_count(slug)
            st["icons_ok"], st["icons_n"] = bool(ok), int(n)
        except Exception:
            pass
        st["icons"] = st["icons_ok"]
        st["hero"] = _theme_has_hero(slug)
        st["cover"] = _theme_has_cover(slug)
        st["vocab"] = self._has_vocab(slug)
        st["matching"] = self._has_matching_outputs(slug)
        st["board"] = self._has_aac_boards(slug)
        code = self._pack_code_for_slug(slug)
        st["matching_ts"] = self._latest_mtime(self._resolve_output_dir(slug, code), "matching")
        st["board_ts"] = self._latest_mtime(THEMES_DIR / slug / "aac_boards", None)
        base_code = (code or slug[:3].upper()).strip()
        st["code_words_ts"] = self._latest_mtime(STUDIOFORGE_DIR / "OUTPUT" / f"{base_code}-CW", None)
        st["code_words"] = st["code_words_ts"] is not None
        st["strips_ts"] = self._latest_mtime(STUDIOFORGE_DIR / "OUTPUT" / f"{base_code}-BIS", None)
        st["strips"] = st["strips_ts"] is not None
        lp = STUDIOFORGE_DIR / "OUTPUT" / "LISTINGS" / f"{slug}_listing.json"
        st["listing"] = lp.is_file()
        st["listing_ts"] = (lp.stat().st_mtime if st["listing"] else None)
        try:
            st["docs"] = bool(self._packaging_docs_status()[0])
        except Exception:
            pass
        st["package_ts"] = self._latest_zip_mtime(slug)
        st["package"] = st["package_ts"] is not None
        self._guided_cache[slug] = st
        return st

    # Pipeline definition: (key, stage, label, hint, required, tool_tab, run_key)
    GUIDED_STEPS = [
        ("vocab", "Set up", "Vocab prepared", "book_vocab.json has hero/fringe words", True, "AI Pre-Populate", None),
        ("icons", "Build assets", "Curate icons", "15 images in activity_images/", True, "Icon Labeler", None),
        ("hero", "Build assets", "Hero image", "hero.png or heroes/ in theme folder", False, None, None),
        ("cover", "Build assets", "Cover reference", "cover*.jpg/png in theme folder", False, None, None),
        ("matching", "Generate activities", "Matching pack", "Matching PDFs in OUTPUT/<code>", True, "Matching", "matching"),
        ("board", "Generate activities", "AAC board", "PDF in aac_boards/", True, "Board Ready", "board_ready"),
        ("code_words", "Generate activities", "Code Words", "OUTPUT/<code>-CW", False, "Code Words", "code_words"),
        ("strips", "Generate activities", "Book Insert Strips", "OUTPUT/<code>-BIS", False, "Book Insert Strips", "book_insert_strips"),
        ("listing", "Finish and publish", "Listing JSON", "OUTPUT/LISTINGS/<slug>_listing.json", True, "Listing Generator", "listing_generator"),
        ("docs", "Finish and publish", "Packaging docs", "TOU + Quick Start present", True, "Pack Ready", None),
        ("package", "Finish and publish", "Upload-ready ZIP", "UPLOAD_READY/*_<slug>_UPLOAD_READY_*.zip", True, "Pack Ready", "pack_ready"),
    ]

    def _has_vocab(self, slug: str) -> bool:
        try:
            p = THEMES_DIR / slug / "book_vocab.json"
            if not p.is_file():
                p = THEMES_DIR / slug / "config" / "book_vocab.json"
            if not p.is_file():
                return False
            obj = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
            for k in ("hero", "fringe_12", "fringe_11", "activity_images"):
                v = obj.get(k)
                if isinstance(v, (list, dict)) and len(v) > 0:
                    return True
            return False
        except Exception:
            return False

    def _latest_zip_mtime(self, slug: str):
        try:
            best = None
            for root in (STUDIOFORGE_DIR / "UPLOAD_READY", BASE_DIR / "03_UPLOAD_READY"):
                if not root.is_dir():
                    continue
                for f in root.glob(f"*{slug}*.zip"):
                    try:
                        mt = f.stat().st_mtime
                        if best is None or mt > best:
                            best = mt
                    except Exception:
                        continue
            return best
        except Exception:
            return None

    def _guided_run(self, run_key: str, slug: str):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        title = next((b.get("title") for b in self.books if b.get("slug") == slug), slug.replace("_", " ").title())
        code = self._pack_code_for_slug(slug)
        dummy = tk.Label(self)
        if run_key == "matching":
            self._launch_matching(slug, title, code, dummy)
        elif run_key == "board_ready":
            self._launch_board_ready(slug, title, code, dummy)
        elif run_key == "code_words":
            self._launch_code_words(slug, title, code, dummy)
        elif run_key == "book_insert_strips":
            self._launch_book_insert_strips(slug, title, code, dummy)
        elif run_key == "listing_generator":
            self._launch_listing(slug, dummy)
        elif run_key == "pack_ready":
            self._run_core_packager(slug, dummy)
        try:
            self._guided_cache.pop(slug, None)
        except Exception:
            pass

    def _latest_mtime(self, folder, name_contains):
        try:
            if not folder or not Path(folder).is_dir():
                return None
            best = None
            for f in Path(folder).iterdir():
                try:
                    if not f.is_file() or f.suffix.lower() != ".pdf":
                        continue
                    if name_contains and name_contains not in f.name.lower():
                        continue
                    mt = f.stat().st_mtime
                    if best is None or mt > best:
                        best = mt
                except Exception:
                    continue
            return best
        except Exception:
            return None

    @staticmethod
    def _fmt_ago(ts) -> str:
        try:
            if not ts:
                return ""
            d = time.time() - float(ts)
            if d < 3600:
                return f"{int(d // 60)}m ago"
            if d < 86400:
                return f"{int(d // 3600)}h ago"
            return datetime.fromtimestamp(ts).strftime("%d %b")
        except Exception:
            return ""

    def _init_guided_tab(self):
        tab = tk.Frame(self.tabs, bg="#FFFFFF")
        self.tabs.add(tab, text="Guided Start")
        try:
            tid = self.tabs.tabs()[-1]
            self._tab_tooltips[tid] = "Pick a book → work down the checklist → click Next Step"
        except Exception:
            pass
        card = tk.Frame(tab, padx=16, pady=12, bg="#FFFFFF")
        card.pack(fill="both", expand=True)
        tk.Label(card, text="Guided Start", font=("Segoe UI", 12, "bold"), bg="#FFFFFF", fg="#0D2545").pack(anchor="w")
        tk.Label(card, text="Pick a book and work top to bottom. Green = done, red = required and missing, amber = optional. Click a row to open its tool, or press Run to generate it now. The big button always jumps to the next required step.",
                 bg="#FFFFFF", fg="#0D2545", justify="left", wraplength=760).pack(anchor="w", pady=(0, 8))
        sel = tk.Frame(card, bg="#FFFFFF"); sel.pack(fill="x")
        slug_var, title_var, code_var = self._book_selector(sel)

        # Next Step CTA + progress
        cta = tk.Frame(card, bg="#E6FFFB", bd=1, relief="solid"); cta.pack(fill="x", pady=(10, 8))
        cta_l = tk.Frame(cta, bg="#E6FFFB"); cta_l.pack(side="left", fill="x", expand=True, padx=10, pady=6)
        ns_label = tk.Label(cta_l, text="", bg="#E6FFFB", fg="#0D2545", font=("Segoe UI", 11, "bold"), anchor="w")
        ns_label.pack(anchor="w")
        prog_row = tk.Frame(cta_l, bg="#E6FFFB"); prog_row.pack(anchor="w", fill="x", pady=(4, 0))
        prog_bar = ttk.Progressbar(prog_row, orient="horizontal", mode="determinate", length=260, maximum=100)
        prog_bar.pack(side="left")
        prog_lbl = tk.Label(prog_row, text="", bg="#E6FFFB", fg="#0D2545")
        prog_lbl.pack(side="left", padx=(8, 0))
        ns_btn = tk.Button(cta, text="Next Step ▶", bg=SWS_TEAL, fg="white", relief="ridge", font=("Segoe UI", 10, "bold"), padx=10)
        ns_btn.pack(side="right", padx=10, pady=6)
        _tip(ns_btn, "Go to (and optionally run) the next required step for this book")

        # Checklist grouped by stage
        steps_frame = tk.Frame(card, bg="#FFFFFF"); steps_frame.pack(fill="x")
        rows = {}
        last_stage = None
        num = 0
        for key, stage, name, hint, required, tool_tab, run_key in self.GUIDED_STEPS:
            if stage != last_stage:
                tk.Label(steps_frame, text=stage.upper(), bg="#FFFFFF", fg="#64748B", font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(8 if last_stage else 0, 2))
                last_stage = stage
            num += 1
            if tool_tab:
                act = (lambda s, t=tool_tab: self._goto_tool_with_slug(t, s))
            else:
                act = (lambda s: self._open_theme_folder(s))
            r = tk.Frame(steps_frame, bg="#FFFFFF", cursor="hand2"); r.pack(fill="x", pady=1)
            chip = tk.Label(r, text="—", width=9, bd=1, relief="ridge", padx=4, bg="#FFFFFF", fg="#0D2545")
            chip.pack(side="left", padx=(0, 8))
            lbl = tk.Label(r, text=f"{num}. {name}" + ("" if required else "  (optional)"), bg="#FFFFFF", fg="#0D2545", font=("Segoe UI", 10, "bold"), anchor="w", width=26)
            lbl.pack(side="left")
            hl = tk.Label(r, text=hint, bg="#FFFFFF", fg="#64748B", anchor="w")
            hl.pack(side="left", fill="x", expand=True)
            _tip(hl, hint)
            if run_key:
                rb = tk.Button(r, text="▶ Run", relief="ridge", command=lambda k=run_key: self._guided_run(k, slug_var.get()))
                rb.pack(side="right", padx=(4, 0))
                _tip(rb, f"Run {name} for the selected book now")
            go = tk.Button(r, text="Open", relief="ridge", command=lambda a=act: a(slug_var.get()))
            go.pack(side="right")
            for w in (r, chip, lbl, hl):
                w.bind("<Button-1>", lambda e, a=act: a(slug_var.get()))
            rows[key] = (chip, required)

        def _paint(chip, ok, text_ok="Done", text_bad="To do", warn=False):
            _pill(chip, text_ok if ok else text_bad, "done" if ok else ("warn" if warn else "todo"))

        def _apply(slug, st):
            if slug != slug_var.get():
                return
            n = st.get("icons_n", 0)
            done_req = tot_req = 0
            for key, chip_req in rows.items():
                chip, required = chip_req
                ok = bool(st.get(key))
                if required:
                    tot_req += 1
                    done_req += int(ok)
                ts = self._fmt_ago(st.get(f"{key}_ts"))
                if key == "icons":
                    _paint(chip, ok, text_ok=f"{n}/15", text_bad=f"{n}/15", warn=(n >= 10))
                else:
                    _paint(chip, ok, text_ok=(ts or "Done"), text_bad=("Missing" if required else "Skip?"), warn=(not required))
            try:
                pct = int(100 * done_req / tot_req) if tot_req else 0
                prog_bar.config(value=pct)
                prog_lbl.config(text=f"{done_req}/{tot_req} required steps done")
            except Exception:
                pass
            try:
                lbl, act = self._next_step_for_slug(slug, status=st)
                ns_label.config(text=f"Next step: {lbl}")
                ns_btn.config(command=act, state="normal")
            except Exception:
                ns_label.config(text="Next step: select a book")
                ns_btn.config(command=lambda: None, state="disabled")

        def _refresh(force=False):
            slug = slug_var.get()
            if not slug:
                _apply(slug, self._guided_status(slug))
                return
            cached = getattr(self, "_guided_cache", {}).get(slug)
            if cached and not force and (time.time() - cached.get("_ts", 0)) < 20:
                _apply(slug, cached)
                return
            for chip, _req in rows.values():
                _pill(chip, "Checking…", "neutral")
            ns_label.config(text="Next step: checking…")
            ns_btn.config(state="disabled")

            def _worker(s=slug):
                try:
                    st = self._guided_status(s, force=force)
                except Exception:
                    st = self._guided_status("")
                try:
                    self.after(0, lambda: _apply(s, st))
                except Exception:
                    pass
            threading.Thread(target=_worker, daemon=True).start()

        tab._guided_refresh = _refresh
        _refresh()
        try:
            slug_var.trace_add("write", lambda *_: _refresh())
        except Exception:
            pass

        ql = tk.Frame(card, bg="#FFFFFF"); ql.pack(fill="x", pady=(10, 0))
        b = tk.Button(ql, text="🔄 Re-check", command=lambda: _refresh(force=True)); b.pack(side="left")
        _tip(b, "Re-scan folders for this book (status is cached for 20s)")
        tk.Button(ql, text="📂 Open Theme", command=lambda: self._open_theme_folder(slug_var.get())).pack(side="left", padx=6)
        tk.Button(ql, text="📁 Open Output", command=lambda: self._open_output_for(slug_var.get(), code_var.get())).pack(side="left", padx=6)
        tk.Button(ql, text="📄 PDF Extractor", command=self._open_pdf_extractor_from_tips).pack(side="left", padx=6)
        tk.Button(ql, text="🧾 Required Icons", command=lambda: _open_icons_checklist(slug_var.get())).pack(side="left", padx=6)
        try:
            tab._ctx = {"tool": "guided", "slug_var": slug_var, "title_var": title_var, "code_var": code_var,
                        "launch": lambda: ns_btn.invoke()}
        except Exception:
            pass

    def _init_code_words_tab(self):
        tab = tk.Frame(self.tabs)
        self.tabs.add(tab, text="Code Words")
        self._setup_book_tab(tab, "code_words")
        try:
            tid = self.tabs.tabs()[-1]
            self._tab_tooltips[tid] = TOOLS["code_words"]["desc"]
        except Exception:
            pass

    def _init_book_insert_strips_tab(self):
        tab = tk.Frame(self.tabs)
        self.tabs.add(tab, text="Book Insert Strips")
        self._setup_book_tab(tab, "book_insert_strips")
        try:
            tid = self.tabs.tabs()[-1]
            self._tab_tooltips[tid] = TOOLS["book_insert_strips"]["desc"]
        except Exception:
            pass

    def _init_ai_tab(self):
        tab = tk.Frame(self.tabs)
        self.tabs.add(tab, text="AI Pre-Populate")
        card, lu = self._card(tab, "ai_prep")
        try:
            tid = self.tabs.tabs()[-1]
            self._tab_tooltips[tid] = TOOLS["ai_prep"]["desc"]
        except Exception:
            pass
        # Book selector
        sel_frame = tk.Frame(card, bg="#FFFFFF")
        sel_frame.pack(fill="x")
        sv, tv, cv = self._book_selector(sel_frame)
        # Grounding option
        use_grounding_var = tk.IntVar(value=1)
        cbg = tk.Checkbutton(card, text="Use Web Grounding (Bing/Serper)", variable=use_grounding_var)
        cbg.pack(anchor="w", pady=(0, 4))
        _tip(cbg, "Fetch web sources and require citations; set BING_SEARCH_V7_SUBSCRIPTION_KEY or SERPER_API_KEY")
        # Dry-run button (no external calls)
        btn = tk.Button(
            card,
            text="Generate All Vocab & Content (Dry-Run)",
            bg=SWS_TEAL,
            fg="white",
            relief="ridge",
            command=lambda: self._ai_dry_run(sv.get(), tv.get(), cv.get(), lu),
        )
        btn.pack(anchor="w", pady=12)
        _tip(btn, "Build and preview the Claude request payload (no network call)")
        btn2 = tk.Button(
            card,
            text="Run Live (Preview Only)",
            bg=SWS_NAVY,
            fg="white",
            relief="ridge",
            command=lambda: self._ai_live_preview(sv.get(), tv.get(), cv.get(), lu, bool(use_grounding_var.get())),
        )
        btn2.pack(anchor="w", pady=6)
        _tip(btn2, "Call Claude with this payload and preview the raw JSON + needs_review (no writes)")
        # Placement note
        try:
            tk.Label(card, text="Runs before Icon Matching (pre-populates content list for icons)", fg="#0D2545", bg="#FFFFFF").pack(anchor="w")
        except Exception:
            pass

    def _init_topic_builder_tab(self):
        tab = tk.Frame(self.tabs)
        self.tabs.add(tab, text="Topic Builder")
        card, lu = self._card(tab, "topic_builder")
        try:
            tid = self.tabs.tabs()[-1]
            self._tab_tooltips[tid] = TOOLS["topic_builder"]["desc"]
        except Exception:
            pass
        row1 = tk.Frame(card, bg="#FFFFFF"); row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Topic:", width=14, anchor="e", bg="#FFFFFF", fg="#0D2545").pack(side="left")
        topic_var = tk.StringVar()
        tk.Entry(row1, textvariable=topic_var, width=44).pack(side="left")

        row2 = tk.Frame(card, bg="#FFFFFF"); row2.pack(fill="x", pady=2)
        tk.Label(row2, text="Keywords:", width=14, anchor="e", bg="#FFFFFF", fg="#0D2545").pack(side="left")
        kw_var = tk.StringVar()
        tk.Entry(row2, textvariable=kw_var, width=44).pack(side="left")
        _tip(tk.Label(row2, text="(comma-separated)", bg="#FFFFFF", fg="#0D2545"), "Optional comma-separated seed words")

        row3 = tk.Frame(card, bg="#FFFFFF"); row3.pack(fill="x", pady=2)
        tk.Label(row3, text="Slug:", width=14, anchor="e", bg="#FFFFFF", fg="#0D2545").pack(side="left")
        slug_var = tk.StringVar()
        ent_slug = tk.Entry(row3, textvariable=slug_var, width=36)
        ent_slug.pack(side="left")
        def _slugify_name(name: str) -> str:
            s = (name or "").strip().lower()
            s = re.sub(r"[^a-z0-9]+", "_", s)
            s = re.sub(r"_+", "_", s).strip("_")
            return f"topic_{s}" if s else "topic_"
        _prev = {"v": ""}
        def _update_slug(*_):
            sug = _slugify_name(topic_var.get())
            cur = (slug_var.get() or "").strip()
            if not cur or cur == _prev["v"]:
                slug_var.set(sug)
            _prev["v"] = sug
        try:
            topic_var.trace_add("write", _update_slug)
        except Exception:
            pass
        btn_reset = tk.Button(row3, text="Reset from Topic", command=_update_slug)
        btn_reset.pack(side="left", padx=6)

        padY = 6 if getattr(self, "_density", "comfortable") == "compact" else 12
        run_btn = tk.Button(card, text="Run Topic Content Builder", bg=SWS_TEAL, fg="white", relief="ridge",
                            command=lambda: self._launch_topic_builder(topic_var.get(), kw_var.get(), slug_var.get(), lu))
        run_btn.pack(anchor="w", pady=padY)
        _tip(run_btn, "Generate topic-based content and hero image")

        ql = tk.Frame(card, bg="#FFFFFF"); ql.pack(anchor="w")
        open_theme_btn = tk.Button(ql, text="📂 Open Theme Folder", command=lambda: self._open_theme_folder(slug_var.get()))
        open_theme_btn.pack(side="left")
        _tip(open_theme_btn, "Open assets/themes/<slug>")

        try:
            tab._ctx = {"tool": "topic_builder", "topic_var": topic_var, "keywords_var": kw_var, "slug_var": slug_var, "lu": lu}
        except Exception:
            pass

    def _ai_build_payload(self, slug: str, title: str, code: str) -> dict:
        # Fields per brief
        fields_needed = [
            "word_search_words",
            "starting_sight_words",
            "sequence_order",
            "sorting_categories",
            "sequencing_strips_verbs",
            "adapted_book_sentences",
            "wh_questions",
            "yes_no_questions",
            "aac_fringe_vocab",
            "inferencing_questions",
            "participation_qna",
        ]
        # Gather adapted_book context (first few pages preview)
        pages = []
        pages_count = 0
        try:
            ab = THEMES_DIR / slug / "config" / "adapted_book.json"
            if ab.exists():
                obj = json.loads(ab.read_text(encoding="utf-8", errors="ignore"))
                arr = obj.get("pages") or []
                pages_count = len(arr)
                for it in arr[:3]:
                    if isinstance(it, dict):
                        pages.append({
                            "page_num": it.get("page_num"),
                            "scene_note": it.get("scene_note"),
                            "sentence": it.get("sentence"),
                        })
        except Exception:
            pass
        payload = {
            "book_slug": slug,
            "book_title": title or slug.replace("_", " ").title(),
            "fields_needed": fields_needed,
            "trigger_position": "before_icon_matching",
            "picturability": {"max_tokens_per_choice": 3},
            "context": {
                "pack_code": code or (slug[:3].upper() + "1"),
                "adapted_book_preview": {"pages_count": pages_count, "pages": pages},
            },
            "guardrails": {
                "grounding_required": "Use web-search-verified facts per book; include grounded:boolean and grounding_note per item.",
                "word_sense_disambiguation": "Confirm intended sense before icon lookup (e.g., bat animal vs. bat tool).",
                "picturability_filter": "Short, concrete, symbol-representable phrases; ≤3 tokens per choice; flag text-only choices.",
                "yes_no_specific": "No double negatives; no opinion/inference-coded statements.",
                "inferencing_specific": "Answers must not be directly stated in source; flag if near-verbatim.",
                "fail_safe": "Low-confidence or unpicturable items route to needs_review.json; never silently ship.",
                "emotion_internal_state_only_for_aac_fringe": "Emotion/internal-state words (cry, scared, sad, happy, etc.) must ONLY appear in aac_fringe_vocab; EXCLUDE them from word_search_words, sorting_categories, sequencing_strips_verbs (aka sentence_strip_verbs), and other concrete-vocabulary fields.",
            },
            "outputs": {
                "book_vocab_json": "book_vocab.json",
                "participation_qna_json": "config/participation_qna.json",
            },
        }
        return payload

    def _ai_show_dry_run(self, payload: dict):
        try:
            win = tk.Toplevel(self)
            win.title("AI Pre-Populate — Dry-Run Payload")
            win.geometry("780x560")
            # Text area with scrollbar
            frm = tk.Frame(win)
            frm.pack(fill="both", expand=True)
            txt = tk.Text(frm, wrap="none")
            sb = tk.Scrollbar(frm, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=sb.set)
            txt.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            txt.insert("1.0", json.dumps(payload, indent=2))
            # Buttons
            row = tk.Frame(win)
            row.pack(fill="x")
            def _copy():
                try:
                    data = json.dumps(payload, indent=2)
                    self.clipboard_clear(); self.clipboard_append(data)
                except Exception:
                    pass
            tk.Button(row, text="Copy JSON", command=_copy).pack(side="left", padx=6, pady=6)
            tk.Button(row, text="Close", command=win.destroy).pack(side="right", padx=6, pady=6)
        except Exception as e:
            try:
                messagebox.showerror("Preview error", str(e))
            except Exception:
                pass

    def _ai_dry_run(self, slug: str, title: str, code: str, lu_label):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        payload = self._ai_build_payload(slug, title, code)
        self._ai_show_dry_run(payload)
        try:
            _touch_used("ai_prep")
            lu_label.config(text=f"Last used: {_last_used('ai_prep')}")
        except Exception:
            pass

    def _web_search_bing(self, query: str, top: int = 5):
        try:
            key = os.environ.get("BING_SEARCH_V7_SUBSCRIPTION_KEY")
            if not key:
                return []
            import urllib.parse as _up
            ep = os.environ.get("BING_SEARCH_V7_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search")
            url = f"{ep}?q={_up.quote_plus(query)}&mkt=en-US&safeSearch=Strict&count={int(top)}"
            req = _rq.Request(url, headers={"Ocp-Apim-Subscription-Key": key})
            with _rq.urlopen(req, timeout=20) as resp:
                obj = json.loads(resp.read().decode("utf-8", errors="ignore"))
            vals = ((obj.get("webPages") or {}).get("value") or [])
            out = []
            for v in vals[:top]:
                out.append({
                    "title": v.get("name"),
                    "snippet": v.get("snippet"),
                    "url": v.get("url"),
                    "source": "bing",
                })
            return out
        except Exception:
            return []

    def _web_search_serper(self, query: str, top: int = 5):
        try:
            key = os.environ.get("SERPER_API_KEY")
            if not key:
                return []
            body = json.dumps({"q": query}).encode("utf-8")
            req = _rq.Request(
                url="https://google.serper.dev/search",
                data=body,
                headers={"content-type": "application/json", "X-API-KEY": key},
                method="POST",
            )
            with _rq.urlopen(req, timeout=20) as resp:
                obj = json.loads(resp.read().decode("utf-8", errors="ignore"))
            vals = obj.get("organic") or []
            out = []
            for v in vals[:top]:
                out.append({
                    "title": v.get("title"),
                    "snippet": v.get("snippet"),
                    "url": v.get("link"),
                    "source": "serper",
                })
            return out
        except Exception:
            return []

    def _fetch_url_text(self, url: str, max_chars: int = 4000) -> str:
        try:
            with _rq.urlopen(url, timeout=20) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            import re as __re
            txt = __re.sub(r"<script[\s\S]*?</script>", " ", html, flags=__re.I)
            txt = __re.sub(r"<style[\s\S]*?</style>", " ", txt, flags=__re.I)
            txt = __re.sub(r"<[^>]+>", " ", txt)
            txt = __re.sub(r"\s+", " ", txt).strip()
            return txt[:max_chars]
        except Exception:
            return ""

    def _collect_grounding_sources(self, slug: str, title: str, payload: dict, top: int = 5):
        # Build a small set of targeted queries
        queries = []
        bt = title or (slug.replace("_", " ").title())
        queries.append(f"{bt} children's book summary")
        queries.append(f"{bt} plot summary")
        queries.append(f"{bt} characters")
        try:
            prev = ((payload or {}).get("context") or {}).get("adapted_book_preview") or {}
            pages = prev.get("pages") or []
            for p in pages:
                sent = (p.get("sentence") or "").split()
                if sent:
                    qfrag = " ".join(sent[:6])
                    queries.append(f"{bt} \"{qfrag}\"")
        except Exception:
            pass

        seen = set(); sources = []
        for q in queries:
            rows = self._web_search_bing(q, top=top) or self._web_search_serper(q, top=top)
            for r in rows:
                u = r.get("url")
                if not u or u in seen:
                    continue
                seen.add(u)
                text = self._fetch_url_text(u, max_chars=1500)
                src = {"url": u, "title": r.get("title"), "snippet": r.get("snippet"), "text": text}
                sources.append(src)
                if len(sources) >= top:
                    break
            if len(sources) >= top:
                break
        return sources

    def _ai_call_claude(self, payload: dict, evidence: list | None = None):
        # Reload env and then read key directly from .env (Studioforge first)
        try:
            _load_env_files()
        except Exception:
            pass
        key, key_src = _get_anthropic_key()
        if not key:
            return False, "Missing ANTHROPIC_API_KEY in environment.", None
        ground_txt = ""
        if evidence:
            try:
                ground_txt = ("\n\nEVIDENCE (use ONLY these sources for grounding; cite by index in 'citations'):\n" +
                              json.dumps(evidence, indent=2))
            except Exception:
                ground_txt = "\n\nEVIDENCE provided but could not be serialized."
        body = {
            "model": os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            "max_tokens": 2000,
            # Enforce JSON-only output and disable chain-of-thought tokens
            "response_format": {"type": "json"},
            "thinking": {"type": "disabled"},
            "system": (
                "You are a content generator for AAC educational materials. "
                "Return STRICT JSON only with keys: book_vocab, participation_qna, needs_review. "
                "book_vocab: object of arrays by field; each item should include grounded(boolean) and grounding_note(string). "
                "participation_qna: pp_qna.v1 compliant object (book_slug, book_title, pages[...]). "
                "needs_review: include any low-confidence/unpicturable items routed for manual review. "
                "Emotion/internal-state words (cry, scared, sad, happy, etc.) must ONLY be proposed in aac_fringe_vocab; explicitly EXCLUDE them from word_search_words, sorting_categories, sequencing_strips_verbs (aka sentence_strip_verbs), and any other concrete-vocabulary fields (which must focus on concrete story nouns/verbs and actions). "
                "If evidence is provided, you MUST set grounded=true ONLY when at least one citation supports the item; "
                "include a 'citations' array with indexes into the evidence list. Otherwise route to needs_review with a reason."
            ),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Apply guardrails (grounding, sense disambiguation, picturability ≤3 tokens/choice with text_only flags, "
                                "yes/no specificity, inference-not-recall, fail-safe to needs_review). "
                                "Produce JSON for book_vocab (fields listed) and participation_qna.\n\nPAYLOAD:\n" + json.dumps(payload, indent=2) + ground_txt
                            ),
                        }
                    ],
                }
            ],
        }
        try:
            # Debug provenance (safe: prefix only)
            try:
                _kp = (key or "")[:15]; _km = len(key or "")
                _model = str(body.get("model"))
                _last = os.environ.get("SWS_DOTENV_LAST", "")
                print(f"SWS_DEBUG key_prefix={_kp} len={_km} model={_model} dotenv_last={_last} key_src={key_src}")
            except Exception:
                pass
            req = _rq.Request(
                url="https://api.anthropic.com/v1/messages",
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "content-type": "application/json",
                    "anthropic-version": "2023-06-01",
                    "x-api-key": key,
                },
                method="POST",
            )
            with _rq.urlopen(req, timeout=90) as resp:
                txt = resp.read().decode("utf-8", errors="ignore")
                obj = json.loads(txt)
            parts = obj.get("content") or []
            raw = "".join([p.get("text", "") for p in parts if isinstance(p, dict) and isinstance(p.get("text"), str)])
            if not raw and isinstance(parts, list):
                for p in parts:
                    if isinstance(p, dict) and "json" in p:
                        try:
                            jv = p.get("json")
                            raw = json.dumps(jv, indent=2)
                            break
                        except Exception:
                            pass
            if not raw:
                raw = obj.get("output_text") or obj.get("completion") or ""
            if not raw:
                try:
                    raw = json.dumps(obj)
                except Exception:
                    raw = ""
            return True, raw, obj
        except Exception as e:
            return False, str(e), None

    def _ai_partition_result(self, slug: str, raw_text: str, require_citations: bool = False):
        raw = raw_text.strip()
        i = raw.find('{')
        j = raw.rfind('}')
        if i >= 0 and j > i:
            raw = raw[i:j+1]
        try:
            data = json.loads(raw)
        except Exception:
            data = {"_unparsed": raw_text}

        needs = {"book_vocab": {}, "participation_qna": {"pages": [], "errors": []}}
        finals = {"book_vocab": {}, "participation_qna": None}

        fields = [
            "word_search_words","starting_sight_words","sequence_order","sorting_categories",
            "sequencing_strips_verbs","adapted_book_sentences","wh_questions","yes_no_questions",
            "aac_fringe_vocab","inferencing_questions"
        ]
        bv = data.get("book_vocab") or {}
        for f in fields:
            items = bv.get(f) or []
            good, review = [], []
            for it in items:
                grounded = None
                has_citations = False
                if isinstance(it, dict):
                    grounded = it.get("grounded")
                    try:
                        c = it.get("citations")
                        has_citations = isinstance(c, list) and len(c) > 0
                    except Exception:
                        has_citations = False
                if grounded is False or grounded is None or (require_citations and grounded is True and not has_citations):
                    review.append(it)
                else:
                    good.append(it)
            if review:
                needs["book_vocab"][f] = review
            if good:
                finals["book_vocab"][f] = good

        pq = data.get("participation_qna")
        if isinstance(pq, dict):
            try:
                from tools.pp_qna_loader import validate_qna
                vr = validate_qna(pq, slug, strict=True)
                import re as _re
                idx_to_reasons = {}
                for e in vr.errors:
                    m = _re.search(r"pages\[(\d+)\]", e)
                    if m:
                        k = int(m.group(1))
                        idx_to_reasons.setdefault(k, []).append(e)
                pages = pq.get("pages") or []
                good_pages = []
                for k, pg in enumerate(pages):
                    if k in idx_to_reasons:
                        needs["participation_qna"]["pages"].append({
                            "index": k,
                            "page_num": pg.get("page_num"),
                            "reasons": idx_to_reasons[k],
                        })
                    else:
                        good_pages.append(pg)
                if good_pages:
                    finals["participation_qna"] = {k: v for k, v in pq.items() if k != "pages"}
                    finals["participation_qna"]["pages"] = good_pages
                if vr.warnings:
                    needs["participation_qna"].setdefault("warnings", []).extend(vr.warnings)
            except Exception as e:
                needs["participation_qna"]["errors"].append(f"validator_error:{e}")
        elif pq is not None:
            needs["participation_qna"]["errors"].append("invalid_participation_qna_format")

        return data, finals, needs

    def _ai_live_preview(self, slug: str, title: str, code: str, lu_label, use_web_grounding: bool = False):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        payload = self._ai_build_payload(slug, title, code)
        evidence = None
        if use_web_grounding:
            try:
                evidence = self._collect_grounding_sources(slug, title, payload, top=5)
            except Exception:
                evidence = None
            if not evidence:
                try:
                    messagebox.showerror(
                        "Web Grounding required",
                        "'Use Web Grounding' is enabled but no sources were found.\n\nSet BING_SEARCH_V7_SUBSCRIPTION_KEY or SERPER_API_KEY and try again."
                    )
                except Exception:
                    pass
                return
        ok, txt, _raw = self._ai_call_claude(payload, evidence=evidence)
        if not ok:
            try:
                messagebox.showerror("Claude API error", txt)
            except Exception:
                pass
            return
        data, finals, needs = self._ai_partition_result(slug, txt, require_citations=bool(evidence))
        try:
            win = tk.Toplevel(self)
            win.title("AI Pre-Populate — Live Preview")
            win.geometry("900x640")
            top = tk.LabelFrame(win, text="Raw JSON from API")
            top.pack(fill="both", expand=True)
            txtbox = tk.Text(top, wrap="none")
            sb = tk.Scrollbar(top, orient="vertical", command=txtbox.yview)
            txtbox.configure(yscrollcommand=sb.set)
            txtbox.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            try:
                txtbox.insert("1.0", json.dumps(data, indent=2))
            except Exception:
                txtbox.insert("1.0", str(txt))
            bot = tk.LabelFrame(win, text="Partition — needs_review vs finals (no writes)")
            bot.pack(fill="x")
            summ = tk.Text(bot, height=12, wrap="word")
            summ.pack(fill="x")
            def _summarize():
                lines = []
                bv = needs.get("book_vocab", {})
                for f, arr in bv.items():
                    lines.append(f"needs_review.book_vocab.{f}: {len(arr)} item(s)")
                pq = needs.get("participation_qna", {})
                pgs = pq.get("pages", [])
                lines.append(f"needs_review.participation_qna.pages: {len(pgs)} page(s)")
                warn = pq.get("warnings", [])
                if warn:
                    lines.append(f"warnings: {len(warn)} — first: {warn[0]}")
                summ.delete("1.0", tk.END)
                summ.insert("1.0", "\n".join(lines) or "No issues detected.")
            _summarize()
            row = tk.Frame(win); row.pack(fill="x")
            def _save_files():
                try:
                    outdir = STUDIOFORGE_DIR / "_ai_preview"
                    outdir.mkdir(exist_ok=True)
                    (outdir / f"{slug}_raw.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
                    (outdir / f"{slug}_needs_review.json").write_text(json.dumps(needs, indent=2), encoding="utf-8")
                    (outdir / f"{slug}_final_preview.json").write_text(json.dumps(finals, indent=2), encoding="utf-8")
                    messagebox.showinfo("Saved", f"Saved to {outdir}")
                except Exception as e:
                    messagebox.showerror("Save error", str(e))
            tk.Button(row, text="💾 Save Preview Files", command=_save_files).pack(side="left", padx=6, pady=6)
            tk.Button(row, text="Close", command=win.destroy).pack(side="right", padx=6, pady=6)
        except Exception:
            pass

    def _init_icon_labeler_tab(self):
        tab = tk.Frame(self.tabs)
        self.tabs.add(tab, text="Icon Labeler")
        card, lu = self._card(tab, "icon_labeler")
        try:
            tid = self.tabs.tabs()[-1]
            self._tab_tooltips[tid] = TOOLS["icon_labeler"]["desc"]
        except Exception:
            pass
        btn = tk.Button(card, text="Launch", bg=SWS_TEAL, fg="white", relief="ridge",
                        command=lambda: self._launch_icon_labeler(lu))
        btn.pack(anchor="w", pady=12)
        _tip(btn, "Start Icon Labeler server and open browser")
        tk.Label(card, text="Default URL: http://127.0.0.1:5052", fg="#0D2545", bg="#FFFFFF").pack(anchor="w")
        def _open_icon_labeler_url_default():
            try:
                last = getattr(self, "_last_book_slug", None) or ""
                q = (f"?book={last}" if last else "")
                webbrowser.open(f"http://127.0.0.1:5052{q}")
            except Exception:
                webbrowser.open("http://127.0.0.1:5052")
        open_url_btn = tk.Button(card, text="🌐 Open URL", command=_open_icon_labeler_url_default)
        open_url_btn.pack(anchor="w")
        _tip(open_url_btn, "Open http://127.0.0.1:5052")
        def _open_vocab_suggestions(autogen=False):
            try:
                last = getattr(self, "_last_book_slug", None) or ""
                q = []
                if last:
                    q.append(f"book={last}")
                if autogen:
                    q.append("autogen=1")
                qs = ("?"+"&".join(q)) if q else ""
                webbrowser.open(f"http://127.0.0.1:5052/vocab_suggestions{qs}")
            except Exception:
                webbrowser.open("http://127.0.0.1:5052/vocab_suggestions")
        vs_btn = tk.Button(card, text="Open Vocab Suggestions", command=lambda: _open_vocab_suggestions(False))
        vs_btn.pack(anchor="w")
        _tip(vs_btn, "Review and approve AI suggestions before commit")
        gen_btn = tk.Button(card, text="Suggest vocab & content", command=lambda: _open_vocab_suggestions(True))
        gen_btn.pack(anchor="w")
        _tip(gen_btn, "Open Suggestions and auto-start generation for the selected book")
        pdf_btn = tk.Button(card, text="📄 Open PDF Extractor", command=self._open_pdf_extractor_from_tips)
        pdf_btn.pack(anchor="w")
        _tip(pdf_btn, "Start server and open http://127.0.0.1:5052/pdf")
        # Preflight status for Icon Labeler (fallback script or original+flask)
        st = tk.Label(card, text="", fg="#0D2545", bg="#FFFFFF")
        st.pack(anchor="w", pady=(0, 4))
        try:
            ok, msg = self._preflight_tool("icon_labeler", "")
            icon = "✅" if ok else "⚠️"
            st.config(text=f"{icon} {msg}", fg=("#0a0" if ok else "#a00"))
            btn.config(state=("normal" if ok else "disabled"))
        except Exception:
            pass
        try:
            tab._ctx = {
                "tool": "icon_labeler",
                "lu": lu,
                "launch": lambda: self._launch_icon_labeler(lu),
            }
        except Exception:
            pass

    def _init_review_tab(self):
        tab = tk.Frame(self.tabs, bg="#FFFFFF")
        self.tabs.add(tab, text="Review and track")
        try:
            tid = self.tabs.tabs()[-1]
            self._tab_tooltips[tid] = "Pipeline status for every book, plus queued jobs and progress"
        except Exception:
            pass
        sub = ttk.Notebook(tab, style="Sub.TNotebook")
        sub.pack(fill="both", expand=True)
        self._sub_notebooks = getattr(self, "_sub_notebooks", [])
        self._sub_notebooks.append((tab, sub))
        self._init_pipeline_tab(sub)
        self._init_jobs_tab(sub)

    def _init_pipeline_tab(self, parent_nb=None):
        nb = parent_nb or self.tabs
        tab = tk.Frame(nb)
        nb.add(tab, text="Pipeline Dashboard")
        try:
            tid = nb.tabs()[-1]
            self._tab_tooltips[tid] = "Per-book pipeline status with Next-Step CTA"
        except Exception:
            pass
        # Controls
        ctrl = tk.Frame(tab, bg="#FFFFFF"); ctrl.pack(fill="x", padx=12, pady=(8, 4))
        tk.Label(ctrl, text="Filter:", bg="#FFFFFF", fg="#0D2545").pack(side="left")
        filt_var = tk.StringVar()
        ent = tk.Entry(ctrl, textvariable=filt_var, width=30)
        ent.pack(side="left", padx=(6, 0))
        tk.Button(ctrl, text="Refresh", command=lambda: rebuild()).pack(side="left", padx=6)
        # Table
        cols = ("book", "icons", "board", "matching", "docs", "next")
        tv = ttk.Treeview(tab, columns=cols, show="headings", height=14)
        for c, w, mn in [("book", 230, 140), ("icons", 64, 56), ("board", 64, 56), ("matching", 80, 70), ("docs", 56, 48), ("next", 200, 140)]:
            tv.heading(c, text=c.title())
            tv.column(c, width=w, minwidth=mn, stretch=(c in ("book", "next")), anchor=("w" if c == "book" else "center"))
        tv.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        # Action row
        act = tk.Frame(tab, bg="#FFFFFF"); act.pack(fill="x", padx=12, pady=(0, 8))
        tk.Button(act, text="Open Theme", command=lambda: on_open_theme()).pack(side="left")
        tk.Button(act, text="Do Next Step", command=lambda: on_next_step()).pack(side="left", padx=8)

        row_actions = {}

        def compute_row(slug: str):
            try:
                meta = next((b for b in self.books if b.get("slug") == slug), {})
                title = meta.get("title") or slug.replace("_", " ").title()
                pc = self._pack_code_for_slug(slug)
                ready, _imsg, icons_n = self._icons_ready_and_count(slug)
                icons_txt = f"{icons_n}/15"
                board_ok = self._has_aac_boards(slug)
                match_ok = self._has_matching_outputs(slug)
                # Prefer readiness_report results when available
                try:
                    rr = self._readiness_report(slug, title, pc or (slug[:3].upper()+"1"), ["aac_board", "matching"])
                except Exception:
                    rr = None
                if isinstance(rr, dict):
                    try:
                        board_ok = bool((rr.get("aac_board") or 0) > 0)
                    except Exception:
                        pass
                    try:
                        match_ok = bool((rr.get("matching") or 0) > 0)
                    except Exception:
                        pass
                # Docs are global, check once
                try:
                    ok_docs, _ = self._packaging_docs_status()
                except Exception:
                    ok_docs = False
                next_label = ""
                action = (lambda: None)
                if not ready:
                    next_label = f"Add icons ({icons_n}/15)"
                    action = lambda s=slug: self._goto_tool_with_slug("Icon Labeler", s)
                elif not match_ok:
                    next_label = "Run Matching"
                    action = lambda s=slug: self._goto_tool_with_slug("Matching", s)
                elif not board_ok:
                    next_label = "Build AAC Board"
                    action = lambda s=slug: self._goto_tool_with_slug("Board Ready", s)
                elif not ok_docs:
                    next_label = "Add Packaging Docs"
                    action = lambda: self._select_tab_by_text("Pack Ready")
                else:
                    next_label = "Package Upload-Ready"
                    action = lambda: self._select_tab_by_text("Pack Ready")
                row = (
                    f"{title} ({slug}) [{pc}]",
                    icons_txt,
                    "✓" if board_ok else "—",
                    "✓" if match_ok else "—",
                    "✓" if ok_docs else "—",
                    next_label,
                )
                return row, action
            except Exception:
                return (slug, "?", "?", "?", "?", ""), (lambda: None)

        def _norm_title_key(text: str) -> str:
            try:
                t = (text or "").lower().replace("_", " ").strip()
                if t.startswith("the "):
                    t = t[4:]
                elif t.startswith("a "):
                    t = t[2:]
                elif t.startswith("an "):
                    t = t[3:]
                t = re.sub(r"[^a-z0-9]+", "", t)
                return t
            except Exception:
                return str(text or "").lower()

        def _pick_canonical(slugs: list[str]) -> str:
            try:
                cands = [s for s in slugs if not s.lower().startswith("the_")] or list(slugs)
                try:
                    cands.sort(key=lambda s: self._count_activity_icons(s), reverse=True)
                except Exception:
                    pass
                return cands[0]
            except Exception:
                return slugs[0]

        gen = {"n": 0}

        def rebuild():
            gen["n"] += 1
            my_gen = gen["n"]
            try:
                tv.delete(*tv.get_children())
                row_actions.clear()
                tv.insert("", tk.END, iid="__scanning__", values=("Scanning books…", "", "", "", "", ""))
            except Exception:
                pass
            filt = (filt_var.get() or "").lower().strip()
            books_snapshot = list(self.books)

            def _worker():
                results = []
                try:
                    metas = {b.get("slug"): b for b in books_snapshot if b.get("slug")}
                    groups = {}
                    for slug, meta in metas.items():
                        title = meta.get("title") or slug.replace("_", " ").title()
                        key = _norm_title_key(title)
                        groups.setdefault(key, []).append(slug)
                    for key in sorted(groups.keys()):
                        if gen["n"] != my_gen:
                            return
                        slugs = groups[key]
                        canon = _pick_canonical(slugs)
                        meta = metas.get(canon, {})
                        title = meta.get("title") or canon.replace("_", " ").title()
                        if filt:
                            pool = [title.lower(), canon.lower()] + [s.lower() for s in slugs if s != canon]
                            if not any(filt in p for p in pool):
                                continue
                        row, action = compute_row(canon)
                        aliases = [s for s in slugs if s != canon]
                        if aliases:
                            try:
                                alias_txt = ", ".join(f"{a} [{self._pack_code_for_slug(a)}]" for a in aliases)
                            except Exception:
                                alias_txt = ", ".join(aliases)
                            vals = list(row)
                            vals[0] = f"{row[0]}  • aliases: {alias_txt}"
                            row_disp = tuple(vals)
                        else:
                            row_disp = row
                        results.append((canon, row_disp, action))
                except Exception:
                    pass

                def _apply():
                    if gen["n"] != my_gen:
                        return
                    try:
                        tv.delete(*tv.get_children())
                        row_actions.clear()
                        for canon, row_disp, action in results:
                            tv.insert("", tk.END, iid=canon, values=row_disp)
                            row_actions[canon] = action
                        if not results:
                            tv.insert("", tk.END, iid="__empty__", values=("No books match", "", "", "", "", ""))
                    except Exception:
                        pass

                try:
                    self.after(0, _apply)
                except Exception:
                    pass

            threading.Thread(target=_worker, daemon=True).start()

        def on_open_theme():
            try:
                sel = tv.selection()
                if not sel:
                    return
                slug = sel[0]
                self._open_theme_folder(slug)
            except Exception:
                pass

        def on_next_step():
            try:
                sel = tv.selection()
                if not sel:
                    return
                slug = sel[0]
                act_fn = row_actions.get(slug)
                if callable(act_fn):
                    act_fn()
            except Exception:
                pass

        try:
            filt_var.trace_add("write", lambda *_: rebuild())
        except Exception:
            pass
        try:
            self.after(1500, rebuild)
        except Exception:
            rebuild()

    def _init_listing_tab(self):
        tab = tk.Frame(self.tabs)
        self.tabs.add(tab, text="Listing Generator")
        self._setup_book_tab(tab, "listing_generator")
        try:
            tid = self.tabs.tabs()[-1]
            self._tab_tooltips[tid] = TOOLS["listing_generator"]["desc"]
        except Exception:
            pass

    def _init_pack_tab(self):
        tab = tk.Frame(self.tabs)
        self.tabs.add(tab, text="Pack Ready")
        card, lu = self._card(tab, "pack_ready")
        sel_frame = tk.Frame(card)
        sel_frame.pack(fill="x")
        sv, tv, cv = self._book_selector(sel_frame)
        try:
            tid = self.tabs.tabs()[-1]
            self._tab_tooltips[tid] = TOOLS["pack_ready"]["desc"]
        except Exception:
            pass
        try:
            disabled_msg = TOOLS.get("pack_ready", {}).get("disabled_reason", "Unavailable")
        except Exception:
            disabled_msg = "Unavailable"
        btn = tk.Button(card, text="Launch", state="disabled")
        btn.pack(anchor="w", pady=(6, 0))
        tk.Label(card, text=disabled_msg, fg="#a00").pack(anchor="w", pady=(4, 0))
        st = tk.Label(card, text="", fg="#0D2545", bg="#FFFFFF")
        st.pack(anchor="w", pady=(4, 0))
        df = tk.Frame(card, bg="#FFFFFF")
        df.pack(anchor="w", pady=(2, 0), fill="x")
        try:
            ok, msg = self._packaging_docs_status()
            icon = "✅" if ok else "⚠️"
            st.config(text=f"{icon} {msg}", fg=("#0a0" if ok else "#a00"))
        except Exception:
            pass
        try:
            docs = _packaging_docs_find()
            tou = docs.get("tou")
            quick = docs.get("quick")
            rope = docs.get("rope") or []
            row1 = tk.Frame(df, bg="#FFFFFF"); row1.pack(anchor="w", fill="x")
            tk.Label(row1, text=f"TOU: {tou.name if tou else 'Missing'}", fg=("#0a0" if tou else "#a00"), bg="#FFFFFF").pack(side="left")
            if tou:
                tk.Button(row1, text="Open", command=lambda p=tou: self._open_path(p)).pack(side="left", padx=6)
                tk.Button(row1, text="Copy Path", command=lambda p=tou: self._copy_to_clipboard(str(p))).pack(side="left")
            row2 = tk.Frame(df, bg="#FFFFFF"); row2.pack(anchor="w", fill="x")
            tk.Label(row2, text=f"Quick Start: {quick.name if quick else 'Missing'}", fg=("#0a0" if quick else "#a00"), bg="#FFFFFF").pack(side="left")
            if quick:
                tk.Button(row2, text="Open", command=lambda p=quick: self._open_path(p)).pack(side="left", padx=6)
                tk.Button(row2, text="Copy Path", command=lambda p=quick: self._copy_to_clipboard(str(p))).pack(side="left")
            row3 = tk.Frame(df, bg="#FFFFFF"); row3.pack(anchor="w", fill="x")
            tk.Label(row3, text=f"Scarborough Rope: {len(rope)} file(s)", fg=("#0a0" if rope else "#a00"), bg="#FFFFFF").pack(side="left")
            if rope:
                tk.Button(row3, text="Open Folder", command=lambda r=docs.get("root"): self._open_path(r)).pack(side="left", padx=6)
                try:
                    sub = tk.Frame(df, bg="#FFFFFF"); sub.pack(anchor="w", fill="x")
                    for idx, rp in enumerate(list(rope)[:4]):
                        try:
                            tk.Button(sub, text=f"Open {Path(rp).name}", command=lambda p=rp: self._open_path(p)).pack(anchor="w")
                        except Exception:
                            continue
                except Exception:
                    pass
        except Exception:
            pass
        try:
            btn_docs = tk.Button(card, text="📚 Open Packaging Docs", command=lambda: self._open_path((_packaging_docs_find().get("root") or (BASE_DIR / "TPT_LINE_OF_TRUTH"))))
            btn_docs.pack(anchor="w", pady=(4, 0))
            _tip(btn_docs, "Open SWS Support Docs (handoff) root")
        except Exception:
            pass
        try:
            btn_std = tk.Button(card, text="📘 Open Standards", command=self._open_standards_docs)
            btn_std.pack(anchor="w", pady=(2, 0))
            _tip(btn_std, "Open README_START_HERE or 02_windsurf_briefs")
        except Exception:
            pass
        try:
            pf = _python_has_module("fitz")
        except Exception:
            pf = False
        try:
            pil = _python_has_module("PIL")
        except Exception:
            pil = False
        try:
            row_env = tk.Frame(card, bg="#FFFFFF")
            row_env.pack(anchor="w", pady=(4, 0))
            env_txt = f"Preview support — PyMuPDF: {'OK' if pf else 'Not installed'} • Pillow: {'OK' if pil else 'Not installed'}"
            tk.Label(row_env, text=env_txt, bg="#FFFFFF", fg=("#0a0" if (pf and pil) else "#a00")).pack(side="left")
        except Exception:
            pass
        try:
            btn_pk = tk.Button(card, text="📦 Open Slug Packages", command=lambda s=sv: self._open_path(BASE_DIR / "03_UPLOAD_READY" / "TPT_Packs" / s.get()))
            btn_pk.pack(anchor="w", pady=(4, 0))
            _tip(btn_pk, "Open 03_UPLOAD_READY/TPT_Packs/<slug>")
        except Exception:
            pass
        # Slug assets status & quick actions
        lbl_thumb = None
        try:
            row_thumb = tk.Frame(card, bg="#FFFFFF"); row_thumb.pack(anchor="w", pady=(2, 0))
            lbl_thumb = tk.Label(row_thumb, text="Thumb: —", bg="#FFFFFF")
            lbl_thumb.pack(side="left")
            tk.Button(row_thumb, text="Open Thumb", command=lambda s=sv: self._open_thumb_for(s.get())).pack(side="left", padx=6)
            tk.Button(row_thumb, text="Open Thumbs Folder", command=lambda: self._open_path(BASE_DIR / "assets" / "canva_thumbs")).pack(side="left", padx=6)
        except Exception:
            pass
        try:
            row_q = tk.Frame(card, bg="#FFFFFF"); row_q.pack(anchor="w", pady=(2, 0))
            tk.Button(row_q, text="📷 Open Previews Folder", command=lambda s=sv: self._open_previews_for(s.get())).pack(side="left")
            tk.Button(row_q, text="📁 Open Canonical Outputs (slug)", command=lambda s=sv: self._open_canonical_outputs_for(s.get())).pack(side="left", padx=6)
        except Exception:
            pass
        # Preflight checks UI
        chk_lbl_pdfs = chk_lbl_prev = chk_lbl_thumb = chk_lbl_docs = None
        try:
            tk.Label(card, text="Preflight checks (beta)", bg="#FFFFFF", fg="#0D2545").pack(anchor="w", pady=(8, 2))
            fr = tk.Frame(card, bg="#FFFFFF"); fr.pack(anchor="w", fill="x")
            row1 = tk.Frame(fr, bg="#FFFFFF"); row1.pack(anchor="w")
            tk.Label(row1, text="Canonical PDFs:", width=18, anchor="w", bg="#FFFFFF").pack(side="left")
            chk_lbl_pdfs = tk.Label(row1, text="—", bg="#FFFFFF"); chk_lbl_pdfs.pack(side="left")
            row2 = tk.Frame(fr, bg="#FFFFFF"); row2.pack(anchor="w")
            tk.Label(row2, text="Previews:", width=18, anchor="w", bg="#FFFFFF").pack(side="left")
            chk_lbl_prev = tk.Label(row2, text="—", bg="#FFFFFF"); chk_lbl_prev.pack(side="left")
            row3 = tk.Frame(fr, bg="#FFFFFF"); row3.pack(anchor="w")
            tk.Label(row3, text="Thumbnail:", width=18, anchor="w", bg="#FFFFFF").pack(side="left")
            chk_lbl_thumb = tk.Label(row3, text="—", bg="#FFFFFF"); chk_lbl_thumb.pack(side="left")
            row4 = tk.Frame(fr, bg="#FFFFFF"); row4.pack(anchor="w")
            tk.Label(row4, text="Support docs:", width=18, anchor="w", bg="#FFFFFF").pack(side="left")
            chk_lbl_docs = tk.Label(row4, text="—", bg="#FFFFFF"); chk_lbl_docs.pack(side="left")
            tk.Button(fr, text="Refresh Checks", command=lambda s=sv: self._update_pack_ready_preflight_ui(s.get(), chk_lbl_pdfs, chk_lbl_prev, chk_lbl_thumb, chk_lbl_docs)).pack(anchor="w", pady=(6, 0))
        except Exception:
            pass
        # QA checklist UI (non-blocking)
        qa_lbl_name = qa_lbl_footer = qa_lbl_prev = qa_lbl_thumb = None
        try:
            tk.Label(card, text="QA checklist (beta)", bg="#FFFFFF", fg="#0D2545").pack(anchor="w", pady=(10, 2))
            qf = tk.Frame(card, bg="#FFFFFF"); qf.pack(anchor="w", fill="x")
            r1 = tk.Frame(qf, bg="#FFFFFF"); r1.pack(anchor="w")
            tk.Label(r1, text="File naming:", width=18, anchor="w", bg="#FFFFFF").pack(side="left")
            qa_lbl_name = tk.Label(r1, text="—", bg="#FFFFFF"); qa_lbl_name.pack(side="left")
            r2 = tk.Frame(qf, bg="#FFFFFF"); r2.pack(anchor="w")
            tk.Label(r2, text="Footer standard:", width=18, anchor="w", bg="#FFFFFF").pack(side="left")
            qa_lbl_footer = tk.Label(r2, text="Manual check", fg="#555", bg="#FFFFFF"); qa_lbl_footer.pack(side="left")
            tk.Button(r2, text="Open", command=lambda s=sv: self._open_canonical_outputs_for(s.get())).pack(side="left", padx=6)
            r3 = tk.Frame(qf, bg="#FFFFFF"); r3.pack(anchor="w")
            tk.Label(r3, text="Previews count:", width=18, anchor="w", bg="#FFFFFF").pack(side="left")
            qa_lbl_prev = tk.Label(r3, text="—", bg="#FFFFFF"); qa_lbl_prev.pack(side="left")
            r4 = tk.Frame(qf, bg="#FFFFFF"); r4.pack(anchor="w")
            tk.Label(r4, text="Thumb size:", width=18, anchor="w", bg="#FFFFFF").pack(side="left")
            qa_lbl_thumb = tk.Label(r4, text="—", bg="#FFFFFF"); qa_lbl_thumb.pack(side="left")
            tk.Button(qf, text="Check again", command=lambda s=sv: self._update_pack_ready_qacheck_ui(s.get(), qa_lbl_name, qa_lbl_prev, qa_lbl_thumb)).pack(anchor="w", pady=(6, 0))
        except Exception:
            pass
        # Manual acceptance: footer confirmation toggle (persisted)
        try:
            conf_fc = _read_log()
            fc_def = int(conf_fc.get("_pack_footer_confirmed", 0))
        except Exception:
            fc_def = 0
        try:
            self._qa_footer_confirmed_var = getattr(self, "_qa_footer_confirmed_var", tk.IntVar(value=fc_def))
        except Exception:
            self._qa_footer_confirmed_var = tk.IntVar(value=fc_def)
        try:
            r5 = tk.Frame(card, bg="#FFFFFF"); r5.pack(anchor="w", pady=(2, 0))
            tk.Checkbutton(r5, text="Footer confirmed (manual)", variable=self._qa_footer_confirmed_var, command=self._on_qa_footer_confirmed_change).pack(side="left")
        except Exception:
            pass
        def _refresh_pack_ready_extras():
            try:
                slug = sv.get()
                th = BASE_DIR / "assets" / "canva_thumbs" / f"{slug}.png"
                ok = th.exists()
                if lbl_thumb:
                    lbl_thumb.config(text=f"Thumb: {'Found' if ok else 'Missing'}", fg=("#0a0" if ok else "#a00"))
                if chk_lbl_pdfs and chk_lbl_prev and chk_lbl_thumb and chk_lbl_docs:
                    self._update_pack_ready_preflight_ui(slug, chk_lbl_pdfs, chk_lbl_prev, chk_lbl_thumb, chk_lbl_docs)
                if qa_lbl_name and qa_lbl_prev and qa_lbl_thumb:
                    self._update_pack_ready_qacheck_ui(slug, qa_lbl_name, qa_lbl_prev, qa_lbl_thumb)
            except Exception:
                pass
        try:
            sv.trace_add("write", lambda *_: _refresh_pack_ready_extras())
            _refresh_pack_ready_extras()
        except Exception:
            pass
        # Packaging toggles
        try:
            conf = _read_log()
            inc_docs_def = int(conf.get("_pack_include_docs", 1))
            inc_out_def = int(conf.get("_pack_include_outputs", 1))
            inc_icons_def = int(conf.get("_pack_require_icons_ok", 0))
            inc_qa_def = int(conf.get("_pack_require_qa_ok", 0))
        except Exception:
            inc_docs_def, inc_out_def, inc_icons_def, inc_qa_def = 1, 1, 0, 0
        try:
            self._pack_docs_var = getattr(self, "_pack_docs_var", tk.IntVar(value=inc_docs_def))
            self._pack_outputs_var = getattr(self, "_pack_outputs_var", tk.IntVar(value=inc_out_def))
            self._pack_icons_req_var = getattr(self, "_pack_icons_req_var", tk.IntVar(value=inc_icons_def))
            self._pack_qa_req_var = getattr(self, "_pack_qa_req_var", tk.IntVar(value=inc_qa_def))
        except Exception:
            self._pack_docs_var = tk.IntVar(value=inc_docs_def)
            self._pack_outputs_var = tk.IntVar(value=inc_out_def)
            self._pack_icons_req_var = tk.IntVar(value=inc_icons_def)
            self._pack_qa_req_var = tk.IntVar(value=inc_qa_def)
        rowt = tk.Frame(card)
        rowt.pack(anchor="w", pady=(4, 0))
        tk.Checkbutton(rowt, text="Include Docs", variable=self._pack_docs_var, command=self._on_pack_toggle_change).pack(side="left")
        tk.Checkbutton(rowt, text="Include Outputs", variable=self._pack_outputs_var, command=self._on_pack_toggle_change).pack(side="left", padx=8)
        tk.Checkbutton(rowt, text="Require Icons OK", variable=self._pack_icons_req_var, command=self._on_pack_toggle_change).pack(side="left", padx=8)
        tk.Checkbutton(rowt, text="Require QA OK", variable=self._pack_qa_req_var, command=self._on_pack_toggle_change).pack(side="left", padx=8)
        # Naming pattern and version tag
        try:
            conf2 = _read_log()
            pat_def = conf2.get("_pack_name_pattern", "{pack_code}_{slug}_UPLOAD_READY_{ts}{ver}.zip")
            ver_def = conf2.get("_pack_version_tag", "")
        except Exception:
            pat_def, ver_def = "{pack_code}_{slug}_UPLOAD_READY_{ts}{ver}.zip", ""
        try:
            self._pack_name_pattern_var = getattr(self, "_pack_name_pattern_var", tk.StringVar(value=pat_def))
            self._pack_version_var = getattr(self, "_pack_version_var", tk.StringVar(value=ver_def))
        except Exception:
            self._pack_name_pattern_var = tk.StringVar(value=pat_def)
            self._pack_version_var = tk.StringVar(value=ver_def)
        rowp = tk.Frame(card)
        rowp.pack(anchor="w", pady=(4, 0), fill="x")
        tk.Label(rowp, text="Filename:").pack(side="left")
        ent_pat = tk.Entry(rowp, textvariable=self._pack_name_pattern_var, width=40)
        ent_pat.pack(side="left", padx=(4, 6))
        _tip(ent_pat, "Placeholders: {pack_code}, {slug}, {title}, {ts}, {ver} (adds _<version> if set)")
        tk.Label(rowp, text="Version:").pack(side="left")
        ent_ver = tk.Entry(rowp, textvariable=self._pack_version_var, width=10)
        ent_ver.pack(side="left", padx=(4, 0))
        _tip(ent_ver, "Optional version tag; used by {ver} placeholder")
        try:
            self._pack_name_pattern_var.trace_add("write", lambda *_: self._on_pack_name_change())
            self._pack_version_var.trace_add("write", lambda *_: self._on_pack_name_change())
        except Exception:
            pass
        # Manifest defaults (non-binding presets)
        try:
            conf3 = _read_log()
            thumbs_def = int(conf3.get("_pack_def_include_thumbs", 1))
            policy_def = str(conf3.get("_pack_def_previews_policy", "First pages"))
            docset_def = str(conf3.get("_pack_def_doc_set", "Standard"))
            prev_pages_def = int(conf3.get("_pack_preview_pages", 2))
            prev_pdf_pages_def = int(conf3.get("_pack_preview_pdf_pages", 3))
        except Exception:
            thumbs_def, policy_def, docset_def, prev_pages_def, prev_pdf_pages_def = 1, "First pages", "Standard", 2, 3
        try:
            self._pack_def_include_thumbs_var = getattr(self, "_pack_def_include_thumbs_var", tk.IntVar(value=thumbs_def))
            self._pack_def_previews_policy_var = getattr(self, "_pack_def_previews_policy_var", tk.StringVar(value=policy_def))
            self._pack_def_doc_set_var = getattr(self, "_pack_def_doc_set_var", tk.StringVar(value=docset_def))
            self._pack_prev_pages_var = getattr(self, "_pack_prev_pages_var", tk.StringVar(value=str(prev_pages_def)))
            self._pack_prev_pdf_pages_var = getattr(self, "_pack_prev_pdf_pages_var", tk.StringVar(value=str(prev_pdf_pages_def)))
        except Exception:
            self._pack_def_include_thumbs_var = tk.IntVar(value=thumbs_def)
            self._pack_def_previews_policy_var = tk.StringVar(value=policy_def)
            self._pack_def_doc_set_var = tk.StringVar(value=docset_def)
            self._pack_prev_pages_var = tk.StringVar(value=str(prev_pages_def))
            self._pack_prev_pdf_pages_var = tk.StringVar(value=str(prev_pdf_pages_def))
        try:
            mf = tk.Frame(card, bg="#FFFFFF"); mf.pack(anchor="w", pady=(6, 0), fill="x")
            tk.Label(mf, text="Manifest defaults (non-binding)", bg="#FFFFFF", fg="#0D2545").pack(anchor="w")
            r0 = tk.Frame(mf, bg="#FFFFFF"); r0.pack(anchor="w")
            tk.Checkbutton(r0, text="Include thumbs", variable=self._pack_def_include_thumbs_var, command=self._on_manifest_defaults_change).pack(side="left")
            r1m = tk.Frame(mf, bg="#FFFFFF"); r1m.pack(anchor="w")
            tk.Label(r1m, text="Previews policy:", bg="#FFFFFF").pack(side="left")
            try:
                tk.OptionMenu(r1m, self._pack_def_previews_policy_var, "None", "First pages", "All pages (heavy)").pack(side="left", padx=(6, 0))
            except Exception:
                tk.Entry(r1m, textvariable=self._pack_def_previews_policy_var, width=18).pack(side="left", padx=(6, 0))
            r2m = tk.Frame(mf, bg="#FFFFFF"); r2m.pack(anchor="w")
            tk.Label(r2m, text="Doc set:", bg="#FFFFFF").pack(side="left")
            try:
                tk.OptionMenu(r2m, self._pack_def_doc_set_var, "Standard", "Minimal", "Full").pack(side="left", padx=(6, 0))
            except Exception:
                tk.Entry(r2m, textvariable=self._pack_def_doc_set_var, width=14).pack(side="left", padx=(6, 0))
            r3m = tk.Frame(mf, bg="#FFFFFF"); r3m.pack(anchor="w")
            tk.Label(r3m, text="Preview images pages:", bg="#FFFFFF").pack(side="left")
            tk.Entry(r3m, textvariable=self._pack_prev_pages_var, width=3).pack(side="left", padx=(4, 12))
            tk.Label(r3m, text="Preview PDF pages:", bg="#FFFFFF").pack(side="left")
            tk.Entry(r3m, textvariable=self._pack_prev_pdf_pages_var, width=3).pack(side="left", padx=(4, 0))
            # Persist on change
            try:
                self._pack_def_previews_policy_var.trace_add("write", lambda *_: self._on_manifest_defaults_change())
                self._pack_def_doc_set_var.trace_add("write", lambda *_: self._on_manifest_defaults_change())
                self._pack_prev_pages_var.trace_add("write", lambda *_: self._on_manifest_defaults_change())
                self._pack_prev_pdf_pages_var.trace_add("write", lambda *_: self._on_manifest_defaults_change())
            except Exception:
                pass
        except Exception:
            pass
        try:
            btn_bdef = tk.Button(card, text="📖 Build Definition", command=lambda: self._open_path(BASE_DIR / "MD" / "WINDSURF_COMPLETE_BUILD_DEFINITION.md"))
            btn_bdef.pack(anchor="w", pady=(4, 0))
            _tip(btn_bdef, "Open WINDSURF_COMPLETE_BUILD_DEFINITION.md")
        except Exception:
            pass
        try:
            btn_ref = tk.Button(card, text="🔄 Refresh Docs", command=self._rebuild_pack_tab)
            btn_ref.pack(anchor="w", pady=(4, 0))
            _tip(btn_ref, "Re-scan packaging docs")
        except Exception:
            pass
        try:
            docs = _packaging_docs_find()
            ready = bool(docs.get("root") and docs.get("tou") and docs.get("quick"))
            btn_fin = tk.Button(card, text="✅ Finalize / Packaging", state=("normal" if ready else "disabled"), command=self._finalize_packaging)
            btn_fin.pack(anchor="w", pady=(6, 0))
            _tip(btn_fin, "Prepare files for upload (requires docs)")
        except Exception:
            pass
        try:
            btn_multi = tk.Button(card, text="📦 Multi-book Packaging…", command=self._finalize_packaging_multi_dialog)
            btn_multi.pack(anchor="w", pady=(4, 0))
            _tip(btn_multi, "Build packages for multiple selected books")
        except Exception:
            pass
        # Last package info and quick actions
        try:
            data = _read_log()
            last_zip = data.get("_last_package_zip")
            if last_zip:
                rowz = tk.Frame(card); rowz.pack(anchor="w", pady=(6, 0), fill="x")
                try:
                    nm = Path(last_zip).name
                except Exception:
                    nm = str(last_zip)
                tk.Label(rowz, text=f"Last package: {nm}").pack(side="left")
                tk.Button(rowz, text="Open", command=lambda p=last_zip: self._open_path(p)).pack(side="left", padx=6)
                tk.Button(rowz, text="Copy Path", command=lambda p=last_zip: self._copy_to_clipboard(str(p))).pack(side="left", padx=6)
                tk.Button(rowz, text="View Manifest", command=lambda p=last_zip: self._view_manifest_for_zip(p)).pack(side="left", padx=6)
                tk.Button(rowz, text="Rebuild", command=self._rebuild_last_package).pack(side="left", padx=6)
                try:
                    conf = _read_log()
                    try:
                        d = 'on' if int(conf.get("_last_pack_include_docs", conf.get("_pack_include_docs", 1))) else 'off'
                    except Exception:
                        d = 'on'
                    try:
                        o = 'on' if int(conf.get("_last_pack_include_outputs", conf.get("_pack_include_outputs", 1))) else 'off'
                    except Exception:
                        o = 'on'
                    try:
                        i = 'on' if int(conf.get("_last_pack_require_icons_ok", conf.get("_pack_require_icons_ok", 0))) else 'off'
                    except Exception:
                        i = 'off'
                    try:
                        q = 'on' if int(conf.get("_last_pack_require_qa_ok", conf.get("_pack_require_qa_ok", 0))) else 'off'
                    except Exception:
                        q = 'off'
                    tip_prev = f"Prev toggles → Docs: {d} • Outputs: {o} • Icons OK req: {i} • QA OK req: {q}"
                except Exception:
                    tip_prev = "Prev toggles: using last-used settings"
                btn_rprev = tk.Button(rowz, text="Rebuild (Prev Toggles)", command=self._rebuild_last_package_prev)
                btn_rprev.pack(side="left", padx=6)
                _tip(btn_rprev, tip_prev)
        except Exception:
            pass
        try:
            sep = tk.Frame(card, bg="#E5E7EB", height=1)
            sep.pack(fill="x", pady=(10, 6))
        except Exception:
            pass
        tk.Label(card, text="TPT Ready (beta)", font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg="#0D2545").pack(anchor="w")
        rowb = tk.Frame(card, bg="#FFFFFF")
        rowb.pack(anchor="w", pady=(4, 0))
        tk.Button(rowb, text="Run Core Packager", command=lambda s=sv, l=lu: self._run_core_packager(s.get(), l)).pack(side="left")
        try:
            tab._ctx = {
                "tool": "pack_ready",
                "slug_var": sv,
                "title_var": tv,
                "code_var": cv,
            }
        except Exception:
            pass

    def _run_core_packager(self, slug, lu_label):
        if not slug:
            try:
                messagebox.showwarning("Select book", "Please choose a book slug.")
            except Exception:
                pass
            return
        script = STUDIOFORGE_DIR / "tpt_packager.py"
        try:
            if not script.exists():
                messagebox.showerror("Missing file", f"Not found: {script}")
                return
        except Exception:
            return
        try:
            # Pass preview page defaults to the packager
            try:
                pp = int(str(self._pack_prev_pages_var.get()).strip())
            except Exception:
                try:
                    pp = int(_read_log().get("_pack_preview_pages", 2))
                except Exception:
                    pp = 2
            try:
                ppdf = int(str(self._pack_prev_pdf_pages_var.get()).strip())
            except Exception:
                try:
                    ppdf = int(_read_log().get("_pack_preview_pdf_pages", 3))
                except Exception:
                    ppdf = 3
            # Map manifest defaults to CLI flags
            try:
                inc_thumbs = int(getattr(self, "_pack_def_include_thumbs_var", tk.IntVar(value=1)).get())
            except Exception:
                try:
                    inc_thumbs = int(_read_log().get("_pack_def_include_thumbs", 1))
                except Exception:
                    inc_thumbs = 1
            try:
                pol_label = str(getattr(self, "_pack_def_previews_policy_var", tk.StringVar(value="First pages")).get())
            except Exception:
                pol_label = str(_read_log().get("_pack_def_previews_policy", "First pages"))
            pol = {
                "None": "none",
                "First pages": "first",
                "All pages (heavy)": "all",
            }.get(pol_label, "first")
            try:
                doc_label = str(getattr(self, "_pack_def_doc_set_var", tk.StringVar(value="Standard")).get())
            except Exception:
                doc_label = str(_read_log().get("_pack_def_doc_set", "Standard"))
            doc_set = {
                "Minimal": "minimal",
                "Standard": "standard",
                "Full": "full",
            }.get(doc_label, "standard")
            args = [PYTHON, str(script), "--slug", slug, "--preview-pages", str(max(0, pp)), "--preview-pdf-pages", str(max(0, ppdf))]
            args += ["--include-thumbs", str(1 if int(inc_thumbs) else 0), "--previews-policy", pol, "--doc-set", doc_set]
            _run_in_console(args, STUDIOFORGE_DIR)
        except Exception:
            pass
        try:
            self._remember_last_book(slug)
            _touch_used("pack_ready")
            lu_label.config(text=f"Last used: {_last_used('pack_ready')}")
        except Exception:
            pass

    def _init_jobs_tab(self, parent_nb=None):
        nb = parent_nb or self.tabs
        tab = tk.Frame(nb)
        nb.add(tab, text="Jobs + Progress")
        try:
            tid = nb.tabs()[-1]
            self._tab_tooltips[tid] = "Queue tool runs and view progress"
        except Exception:
            pass
        if not hasattr(self, "_jobs"):
            self._jobs = []
        row = tk.Frame(tab)
        row.pack(fill="x", padx=12, pady=8)
        btn_add = tk.Button(row, text="➕ Add Current", command=self._queue_current)
        btn_add.pack(side="left")
        _tip(btn_add, "Add the current tab's launch as a job")
        btn_e2e = tk.Button(row, text="📚 Queue End‑to‑End", command=self._queue_end_to_end)
        btn_e2e.pack(side="left", padx=8)
        _tip(btn_e2e, "Queue Matching → Board Ready → Listing for current book")
        btn_run = tk.Button(row, text="▶️ Run Queue", command=self._run_jobs)
        btn_run.pack(side="left", padx=8)
        _tip(btn_run, "Run all queued jobs in order")
        btn_clear = tk.Button(row, text="🧹 Clear", command=self._clear_jobs)
        btn_clear.pack(side="left", padx=8)
        _tip(btn_clear, "Clear queued jobs and log")
        opts = tk.Frame(tab)
        opts.pack(fill="x", padx=12, pady=(0, 6))
        try:
            _conf = _read_log()
            wait_def = int(_conf.get("_jobs_wait", 0))
            to_def = str(_conf.get("_jobs_timeout_min", "8"))
        except Exception:
            wait_def, to_def = 0, "8"
        try:
            self._jobs_wait_var = getattr(self, "_jobs_wait_var", tk.IntVar(value=wait_def))
            self._jobs_timeout_var = getattr(self, "_jobs_timeout_var", tk.StringVar(value=to_def))
        except Exception:
            self._jobs_wait_var = tk.IntVar(value=wait_def)
            self._jobs_timeout_var = tk.StringVar(value=to_def)
        tk.Checkbutton(opts, text="Wait for completion (outputs change)", variable=self._jobs_wait_var).pack(side="left")
        tk.Label(opts, text="Timeout (min):").pack(side="left", padx=(12, 4))
        tk.Entry(opts, textvariable=self._jobs_timeout_var, width=4).pack(side="left")
        self.jobs_list = tk.Listbox(tab, height=14)
        self.jobs_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _append_job_log(self, text):
        try:
            ts = datetime.now().strftime("%H:%M:%S")
            line = f"[{ts}] {text}"
            self.jobs_list.insert("end", line)
            self.jobs_list.see("end")
        except Exception:
            pass

    def _queue_current(self):
        try:
            tf = self._current_tab_frame()
            ctx = getattr(tf, "_ctx", None)
            if not ctx:
                messagebox.showinfo("Jobs", "Current tab is not queueable.")
                return
            tool = ctx.get("tool")
            if tool not in ("board_ready", "matching", "listing_generator", "pack_ready"):
                messagebox.showinfo("Jobs", "Only Board Ready, Matching, Listing, and Pack Ready can be queued.")
                return
            sv = ctx.get("slug_var"); tv = ctx.get("title_var"); cv = ctx.get("code_var")
            slug = sv.get() if sv else ""
            title = tv.get() if tv else ""
            code = cv.get() if cv else ""
            if not slug and tool != "listing_generator":
                messagebox.showwarning("Jobs", "Select a book first.")
                return
            job = {"tool": tool, "slug": slug, "title": title, "code": code, "ts": datetime.now().isoformat(timespec="seconds")}
            self._jobs.append(job)
            self._append_job_log(f"Queued {tool} — {slug or '(all)'}")
        except Exception as e:
            messagebox.showerror("Jobs", str(e))

    def _run_jobs(self):
        try:
            if not getattr(self, "_jobs", None):
                self._append_job_log("No jobs to run.")
                return
            # Persist current job options
            try:
                data = _read_log()
                data["_jobs_wait"] = int(self._jobs_wait_var.get())
                data["_jobs_timeout_min"] = str(self._jobs_timeout_var.get())
                _write_log(data)
            except Exception:
                pass
            self._append_job_log(f"Running {len(self._jobs)} job(s)...")
            for job in list(self._jobs):
                tool = job.get("tool"); slug = job.get("slug"); title = job.get("title"); code = job.get("code")
                try:
                    before = None
                    try:
                        if self._jobs_wait_var.get() and slug:
                            before = self._snapshot_output(slug, code)
                    except Exception:
                        before = None
                    if tool == "board_ready":
                        self._append_job_log(f"Launching Board Ready — {slug}")
                        self._launch_board_ready(slug, title, code, tk.Label(self))
                    elif tool == "matching":
                        self._append_job_log(f"Launching Matching — {slug}")
                        self._launch_matching(slug, title, code, tk.Label(self))
                    elif tool == "listing_generator":
                        self._append_job_log(f"Launching Listing — {slug or '(selected)'}")
                        self._launch_listing(slug, tk.Label(self))
                    elif tool == "pack_ready":
                        self._append_job_log(f"Launching Pack Ready — {slug}")
                        self._run_core_packager(slug, tk.Label(self))
                    else:
                        self._append_job_log(f"Skipped unknown tool: {tool}")
                    # Optional wait for completion (outputs change)
                    try:
                        if self._jobs_wait_var.get() and slug:
                            to_min = float(self._jobs_timeout_var.get() or 8.0)
                            ok = self._wait_for_outputs(before, slug, code, int(max(1, to_min * 60)))
                            self._append_job_log("Done: outputs changed" if ok else "Proceeding: timeout/no change detected")
                    except Exception:
                        pass
                except Exception as ex:
                    self._append_job_log(f"Error launching {tool}: {ex}")
            self._jobs.clear()
            self._append_job_log("Queue complete.")
        except Exception as e:
            messagebox.showerror("Jobs", str(e))

    def _queue_end_to_end(self):
        try:
            slug = self._current_slug_guess()
            if not slug:
                messagebox.showwarning("Jobs", "Select a book first.")
                return
            meta = next((b for b in self.books if b.get("slug") == slug), {})
            title = meta.get("title") or slug.replace("_", " ").title()
            code = self._pack_code_for_slug(slug)
            if not hasattr(self, "_jobs"):
                self._jobs = []
            for tool in ("matching", "board_ready", "listing_generator", "pack_ready"):
                job = {"tool": tool, "slug": slug, "title": title, "code": code, "ts": datetime.now().isoformat(timespec="seconds")}
                self._jobs.append(job)
                self._append_job_log(f"Queued {tool} — {slug}")
        except Exception as e:
            try:
                messagebox.showerror("Jobs", str(e))
            except Exception:
                pass

    def _resolve_output_dir(self, slug, code):
        try:
            if not slug:
                return None
            pack_code = code or (slug[:3].upper() + "1")
            for p in [
                STUDIOFORGE_DIR / "OUTPUT" / str(pack_code),
                THEMES_DIR / slug / "OUTPUT",
                THEMES_DIR / slug / "05 outputs",
                THEMES_DIR / slug / "output",
            ]:
                try:
                    if p.exists():
                        return p
                except Exception:
                    continue
            return None
        except Exception:
            return None

    def _snapshot_output(self, slug, code):
        try:
            base = self._resolve_output_dir(slug, code)
            if not base:
                return None
            n = 0
            mt = 0.0
            for fp in base.rglob("*"):
                try:
                    if fp.is_file():
                        n += 1
                        try:
                            mt = max(mt, fp.stat().st_mtime)
                        except Exception:
                            pass
                except Exception:
                    continue
            return {"dir": base, "count": n, "mtime": mt}
        except Exception:
            return None

    def _wait_for_outputs(self, before, slug, code, timeout_s=480):
        try:
            start = time.time()
            while (time.time() - start) < max(30, int(timeout_s)):
                now = self._snapshot_output(slug, code)
                try:
                    if before and now and now.get("dir") == before.get("dir"):
                        if (now.get("count", 0) > before.get("count", 0)) or (now.get("mtime", 0) > before.get("mtime", 0)):
                            return True
                except Exception:
                    pass
                time.sleep(3)
            return False
        except Exception:
            return False

    def _clear_jobs(self):
        try:
            self._jobs = []
            try:
                self.jobs_list.delete(0, "end")
            except Exception:
                pass
            self._append_job_log("Cleared.")
        except Exception:
            pass

    def _init_qa_tab(self):
        tab = tk.Frame(self.tabs)
        self.tabs.add(tab, text="QA Review")
        try:
            tid = self.tabs.tabs()[-1]
            self._tab_tooltips[tid] = TOOLS["qa_reviewer"]["desc"]
        except Exception:
            pass
        if QAReviewer is None:
            tk.Label(tab, text="QA Reviewer module not found.", fg="#a00").pack(padx=16, pady=16, anchor="w")
            return
        # Embed the QA Reviewer panel inside the tab
        frame = QAReviewer(tab)
        frame.pack(fill="both", expand=True)

    def _launch_board_ready(self, slug, title, code, lu_label):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        gen = STUDIOFORGE_DIR / "AAC_BOARD_GENERATOR.py"
        if not gen.exists():
            messagebox.showerror("Missing file", f"Not found: {gen}")
            return
        if _generator_has_named_args():
            args = [PYTHON, str(gen), "--book", slug]
        else:
            args = [PYTHON, str(gen), slug, title or slug.replace("_", " ").title(), code or (slug[:3].upper() + "1")]
        ok = _run_in_console_persist(args, STUDIOFORGE_DIR)
        if ok:
            self._remember_last_book(slug)
            _touch_used("board_ready")
            lu_label.config(text=f"Last used: {_last_used('board_ready')}")

    def _images_dir_for_book(self, slug):
        if not slug:
            return None
        base = THEMES_DIR / slug
        cands = [base / "activity_images", base / "icons"]
        for p in cands:
            try:
                if p.exists():
                    files = list(p.glob("*.png"))
                    if len(files) >= 4:
                        return p
            except Exception:
                continue
        return None

    def _open_path(self, p):
        try:
            target = Path(p)
            if not target.exists():
                messagebox.showerror("Not found", f"Not found: {target}")
                return
            if os.name == "nt":
                os.startfile(str(target))  # type: ignore
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(target)])
            else:
                subprocess.Popen(["xdg-open", str(target)])
        except Exception as e:
            messagebox.showerror("Open failed", str(e))

    def _open_theme_folder(self, slug):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        base = THEMES_DIR / slug
        self._open_path(base)

    def _open_output_for(self, slug, code):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        pack_code = code or (slug[:3].upper() + "1")
        cands = [
            STUDIOFORGE_DIR / "OUTPUT" / str(pack_code),
            THEMES_DIR / slug / "OUTPUT",
            THEMES_DIR / slug / "05 outputs",
            THEMES_DIR / slug / "output",
        ]
        for p in cands:
            try:
                if p.exists():
                    self._open_path(p)
                    return
            except Exception:
                continue
        self._open_path(STUDIOFORGE_DIR / "OUTPUT")

    def _open_thumb_for(self, slug: str):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        try:
            th = BASE_DIR / "assets" / "canva_thumbs" / f"{slug}.png"
            if th.exists():
                self._open_path(th)
                return
            messagebox.showinfo("Thumbs", f"No thumb found for {slug}. Opening thumbs folder.")
            self._open_path(BASE_DIR / "assets" / "canva_thumbs")
        except Exception as e:
            messagebox.showerror("Thumbs", str(e))

    def _open_previews_for(self, slug: str):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        try:
            cands = [
                BASE_DIR / "_previews" / slug,
                BASE_DIR / "03_UPLOAD_READY" / "TPT_Packs" / slug / "Previews",
            ]
            for p in cands:
                try:
                    if p.exists():
                        self._open_path(p)
                        return
                except Exception:
                    continue
            self._open_path(BASE_DIR / "_previews")
        except Exception as e:
            messagebox.showerror("Previews", str(e))

    def _open_canonical_outputs_for(self, slug: str):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        try:
            manp = STUDIOFORGE_DIR / "_CANONICAL_LOCKED" / "OUTPUTS" / "manifest.json"
            if manp.exists():
                try:
                    man = json.loads(manp.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    man = {}
                # find slug in manifest
                try:
                    for _product, themes in (man or {}).items():
                        if isinstance(themes, dict) and slug in themes:
                            paths = (themes.get(slug, {}) or {}).get("paths", {})
                            for v in paths.values():
                                try:
                                    target = (BASE_DIR / v)
                                    parent = target.parent
                                    if parent.exists():
                                        self._open_path(parent)
                                        return
                                except Exception:
                                    continue
                except Exception:
                    pass
            root = STUDIOFORGE_DIR / "_CANONICAL_LOCKED" / "OUTPUTS"
            if root.exists():
                # Try to find a directory matching slug
                try:
                    for p in root.rglob(slug):
                        try:
                            if p.is_dir():
                                self._open_path(p)
                                return
                        except Exception:
                            continue
                except Exception:
                    pass
                self._open_path(root)
                return
            # Fallback to normal outputs
            self._open_output_for(slug, self._pack_code_for_slug(slug))
        except Exception as e:
            messagebox.showerror("Canonical Outputs", str(e))

    def _update_pack_ready_preflight_ui(self, slug: str, lbl_pdfs, lbl_prev, lbl_thumb, lbl_docs):
        try:
            # Canonical PDFs check via manifest, fallback to scan
            ok_pdfs = False
            pdf_detail = ""
            try:
                manp = STUDIOFORGE_DIR / "_CANONICAL_LOCKED" / "OUTPUTS" / "manifest.json"
                if manp.exists() and slug:
                    try:
                        man = json.loads(manp.read_text(encoding="utf-8", errors="ignore"))
                    except Exception:
                        man = {}
                    found = 0
                    total = 0
                    for _product, themes in (man or {}).items():
                        if isinstance(themes, dict) and slug in themes:
                            paths = (themes.get(slug, {}) or {}).get("paths", {})
                            total = len(paths)
                            for v in paths.values():
                                try:
                                    if (BASE_DIR / v).exists():
                                        found += 1
                                except Exception:
                                    continue
                            break
                    if found > 0:
                        ok_pdfs = True
                    pdf_detail = f"{found}/{max(total, 1) if total else 0}"
                if not ok_pdfs and slug:
                    root = STUDIOFORGE_DIR / "_CANONICAL_LOCKED" / "OUTPUTS"
                    if root.exists():
                        try:
                            cnt = 0
                            for p in root.rglob(slug):
                                try:
                                    if p.is_dir():
                                        cnt += len(list(p.glob("*.pdf")))
                                        if cnt > 0:
                                            break
                                except Exception:
                                    continue
                            ok_pdfs = cnt > 0
                            if not pdf_detail:
                                pdf_detail = f"{cnt} file(s)"
                        except Exception:
                            pass
            except Exception:
                ok_pdfs = False
            try:
                lbl_pdfs.config(text=("OK " + (f"({pdf_detail})" if pdf_detail else "")) if ok_pdfs else "Missing", fg=("#0a0" if ok_pdfs else "#a00"))
            except Exception:
                pass

            # Previews folder check
            try:
                prev_ok = False
                prev_cnt = 0
                if slug:
                    pd = BASE_DIR / "_previews" / slug
                    if pd.exists():
                        try:
                            prev_cnt = len(list(pd.glob("*.png"))) + len(list(pd.glob("*.pdf")))
                        except Exception:
                            prev_cnt = 0
                    if prev_cnt == 0:
                        # fallback to packaged previews
                        pd2 = BASE_DIR / "03_UPLOAD_READY" / "TPT_Packs" / slug / "Previews"
                        if pd2.exists():
                            try:
                                prev_cnt = len(list(pd2.glob("*.png"))) + len(list(pd2.glob("*.pdf")))
                            except Exception:
                                prev_cnt = 0
                    prev_ok = prev_cnt > 0
                lbl_prev.config(text=(f"OK ({prev_cnt} file(s))" if prev_ok else "Missing"), fg=("#0a0" if prev_ok else "#a00"))
            except Exception:
                try:
                    lbl_prev.config(text="—")
                except Exception:
                    pass

            # Thumbnail check
            try:
                th_ok = False
                if slug:
                    th = BASE_DIR / "assets" / "canva_thumbs" / f"{slug}.png"
                    th_ok = th.exists()
                lbl_thumb.config(text=("OK" if th_ok else "Missing"), fg=("#0a0" if th_ok else "#a00"))
            except Exception:
                try:
                    lbl_thumb.config(text="—")
                except Exception:
                    pass

            # Support docs check
            try:
                docs = _packaging_docs_find()
                root = docs.get("root")
                tou = docs.get("tou")
                quick = docs.get("quick")
                okd = bool(root and (tou or quick))
                lbl_docs.config(text=("OK" if okd else "Missing"), fg=("#0a0" if okd else "#a00"))
            except Exception:
                try:
                    lbl_docs.config(text="—")
                except Exception:
                    pass
        except Exception:
            pass

    def _remember_last_book(self, slug):
        try:
            data = _read_log()
            data["_last_book"] = slug
            _write_log(data)
            self._last_book_slug = slug
        except Exception:
            pass

    def _open_logs(self):
        try:
            if not LOG_FILE.exists():
                LOG_FILE.write_text("{}", encoding="utf-8")
            self._open_path(LOG_FILE)
        except Exception as e:
            messagebox.showerror("Open Logs", str(e))

    def _copy_to_clipboard(self, text: str, notice: str = "Copied to clipboard"):
        try:
            if not text:
                return
            self.clipboard_clear()
            self.clipboard_append(str(text))
            try:
                messagebox.showinfo("Copy", notice)
            except Exception:
                pass
        except Exception:
            pass

    def _open_last_package_zip(self):
        try:
            p = _read_log().get("_last_package_zip")
            if not p:
                messagebox.showinfo("Packages", "No last package recorded yet.")
                return
            self._open_path(p)
        except Exception as e:
            messagebox.showerror("Packages", str(e))

    def _open_last_package_folder(self):
        try:
            p = _read_log().get("_last_package_zip")
            if not p:
                messagebox.showinfo("Packages", "No last package recorded yet.")
                return
            parent = Path(p).parent
            self._open_path(parent)
        except Exception as e:
            messagebox.showerror("Packages", str(e))

    def _open_standards_docs(self):
        try:
            docs = _packaging_docs_find()
            root = docs.get("root")
            if not root:
                messagebox.showinfo("Standards", "Support docs root not found.")
                return
            rootp = Path(root)
            # Prefer README_START_HERE.md
            readme = rootp / "README_START_HERE.md"
            if readme.exists():
                self._open_path(readme)
                return
            # Fallback: briefs folder
            briefs = rootp / "02_windsurf_briefs"
            if briefs.exists():
                self._open_path(briefs)
                return
            # Else open root
            self._open_path(rootp)
        except Exception as e:
            try:
                messagebox.showerror("Standards", str(e))
            except Exception:
                pass

    def _rebuild_last_package(self):
        try:
            p = _read_log().get("_last_package_zip")
            if not p:
                messagebox.showinfo("Packaging", "No last package recorded yet.")
                return
            zp = Path(p)
            if not zp.exists():
                messagebox.showerror("Packaging", f"Not found: {zp}")
                return
            import zipfile
            with zipfile.ZipFile(str(zp), "r") as zf:
                try:
                    raw = zf.read("manifest.json")
                    man = json.loads(raw.decode("utf-8", errors="ignore"))
                except Exception:
                    messagebox.showerror("Packaging", "manifest.json not found in last package.")
                    return
            slug = (man.get("slug") or "").strip()
            title = (man.get("title") or "").strip()
            code = (man.get("pack_code") or "").strip()
            if not slug:
                messagebox.showerror("Packaging", "manifest.json missing slug; cannot rebuild.")
                return
            docs = _packaging_docs_find()
            # Respect current toggles
            try:
                inc_docs = bool(self._pack_docs_var.get())
                inc_out = bool(self._pack_outputs_var.get())
                inc_icons = bool(self._pack_icons_req_var.get())
                inc_qa = bool(self._pack_qa_req_var.get())
            except Exception:
                inc_docs, inc_out, inc_icons, inc_qa = True, True, False, False
            if not inc_docs and not inc_out:
                messagebox.showinfo("Packaging", "Select at least one: Include Docs and/or Include Outputs.")
                return
            if inc_docs and not (docs.get("root") and docs.get("tou") and docs.get("quick")):
                messagebox.showinfo("Packaging", "Required docs not present yet (need TOU and Quick Start).")
                return
            if inc_icons:
                ic = _icons_check_status(slug)
                if not (isinstance(ic, tuple) and bool(ic[0])):
                    try:
                        reason = ic[1] if isinstance(ic, tuple) else "unknown"
                    except Exception:
                        reason = "unknown"
                    messagebox.showinfo("Packaging", f"Icons gating: {reason}. Rebuild aborted.")
                    return
            if inc_qa:
                ok_qa, reasons = self._qa_acceptance_status(slug, include_outputs=inc_out)
                if not ok_qa:
                    try:
                        why = "; ".join([str(r) for r in (reasons or [])]) or "QA not accepted"
                    except Exception:
                        why = "QA not accepted"
                    messagebox.showinfo("Packaging", f"QA gating: {why}. Rebuild aborted.")
                    return
            # Build
            zp_new = self._build_package_for(slug, title, code, docs, inc_docs, inc_out)
            if not zp_new:
                messagebox.showinfo("Packaging", "Rebuild failed; check outputs and docs.")
                return
            try:
                data = _read_log()
                data["_last_package_zip"] = str(zp_new)
                try:
                    data["_last_package_time"] = datetime.now().isoformat(timespec="seconds")
                except Exception:
                    pass
                _write_log(data)
            except Exception:
                pass
            try:
                self._update_last_package_header_status(schedule=False)
            except Exception:
                pass
            try:
                self._open_path(Path(zp_new).parent)
            except Exception:
                pass
            messagebox.showinfo("Packaging", f"Rebuilt package: {Path(zp_new).name}")
        except Exception as e:
            messagebox.showerror("Packaging", str(e))

    def _rebuild_last_package_prev(self):
        try:
            p = _read_log().get("_last_package_zip")
            if not p:
                messagebox.showinfo("Packaging", "No last package recorded yet.")
                return
            zp = Path(p)
            if not zp.exists():
                messagebox.showerror("Packaging", f"Not found: {zp}")
                return
            import zipfile
            with zipfile.ZipFile(str(zp), "r") as zf:
                try:
                    raw = zf.read("manifest.json")
                    man = json.loads(raw.decode("utf-8", errors="ignore"))
                except Exception:
                    messagebox.showerror("Packaging", "manifest.json not found in last package.")
                    return
            slug = (man.get("slug") or "").strip()
            title = (man.get("title") or "").strip()
            code = (man.get("pack_code") or "").strip()
            if not slug:
                messagebox.showerror("Packaging", "manifest.json missing slug; cannot rebuild.")
                return
            docs = _packaging_docs_find()
            # Use last-used toggles if present; otherwise fall back to saved prefs; last to current UI
            conf = _read_log()
            try:
                inc_docs = bool(int(conf.get("_last_pack_include_docs", conf.get("_pack_include_docs", 1))))
            except Exception:
                inc_docs = True
            try:
                inc_out = bool(int(conf.get("_last_pack_include_outputs", conf.get("_pack_include_outputs", 1))))
            except Exception:
                inc_out = True
            try:
                inc_icons = bool(int(conf.get("_last_pack_require_icons_ok", conf.get("_pack_require_icons_ok", 0))))
            except Exception:
                inc_icons = False
            try:
                inc_qa = bool(int(conf.get("_last_pack_require_qa_ok", conf.get("_pack_require_qa_ok", 0))))
            except Exception:
                inc_qa = False
            if not inc_docs and not inc_out:
                messagebox.showinfo("Packaging", "Last-used toggles select neither Docs nor Outputs; nothing to build.")
                return
            if inc_docs and not (docs.get("root") and docs.get("tou") and docs.get("quick")):
                messagebox.showinfo("Packaging", "Docs required by last-used toggles are missing.")
                return
            if inc_icons:
                ic = _icons_check_status(slug)
                if not (isinstance(ic, tuple) and bool(ic[0])):
                    try:
                        reason = ic[1] if isinstance(ic, tuple) else "unknown"
                    except Exception:
                        reason = "unknown"
                    messagebox.showinfo("Packaging", f"Icons gating: {reason}. Rebuild aborted.")
                    return
            if inc_qa:
                ok_qa, reasons = self._qa_acceptance_status(slug, include_outputs=inc_out)
                if not ok_qa:
                    try:
                        why = "; ".join([str(r) for r in (reasons or [])]) or "QA not accepted"
                    except Exception:
                        why = "QA not accepted"
                    messagebox.showinfo("Packaging", f"QA gating: {why}. Rebuild aborted.")
                    return
            zp_new = self._build_package_for(slug, title, code, docs, inc_docs, inc_out)
            if not zp_new:
                messagebox.showinfo("Packaging", "Rebuild failed; check outputs and docs.")
                return
            try:
                data = _read_log()
                data["_last_package_zip"] = str(zp_new)
                try:
                    data["_last_package_time"] = datetime.now().isoformat(timespec="seconds")
                except Exception:
                    pass
                _write_log(data)
            except Exception:
                pass
            try:
                self._update_last_package_header_status(schedule=False)
            except Exception:
                pass
            try:
                self._open_path(Path(zp_new).parent)
            except Exception:
                pass
            messagebox.showinfo("Packaging", f"Rebuilt package (prev toggles): {Path(zp_new).name}")
        except Exception as e:
            messagebox.showerror("Packaging", str(e))

    def _update_last_package_header_status(self, schedule: bool = True):
        try:
            lbl = getattr(self, "_lastpkg_label", None)
            if not lbl:
                return
            data = _read_log()
            p = data.get("_last_package_zip")
            t = data.get("_last_package_time")
            try:
                name = Path(p).name if p else ""
            except Exception:
                name = str(p) if p else ""
            lbl.config(text=name)
            # Freshness highlight: green for <= 10 minutes
            bg = SWS_TEAL
            try:
                if t:
                    dt = datetime.fromisoformat(t)
                    age_min = (datetime.now() - dt).total_seconds() / 60.0
                    if age_min <= 10.0:
                        bg = "#2e7d32"  # green
            except Exception:
                pass
            try:
                lbl.config(bg=bg)
            except Exception:
                pass
            if schedule:
                try:
                    if getattr(self, "_lastpkg_after", None):
                        self.after_cancel(self._lastpkg_after)
                except Exception:
                    pass
                try:
                    self._lastpkg_after = self.after(60000, self._update_last_package_header_status)
                except Exception:
                    pass
        except Exception:
            pass
    def _on_pack_toggle_change(self):
        try:
            data = _read_log()
            try:
                data["_pack_include_docs"] = int(self._pack_docs_var.get())
            except Exception:
                pass
            try:
                data["_pack_include_outputs"] = int(self._pack_outputs_var.get())
            except Exception:
                pass
            try:
                data["_pack_require_icons_ok"] = int(self._pack_icons_req_var.get())
            except Exception:
                pass
            try:
                data["_pack_require_qa_ok"] = int(self._pack_qa_req_var.get())
            except Exception:
                pass
            _write_log(data)
        except Exception:
            pass

    def _on_pack_name_change(self, *_):
        try:
            data = _read_log()
            try:
                data["_pack_name_pattern"] = str(self._pack_name_pattern_var.get())
            except Exception:
                pass
            try:
                data["_pack_version_tag"] = str(self._pack_version_var.get())
            except Exception:
                pass
            _write_log(data)
        except Exception:
            pass

    def _on_manifest_defaults_change(self):
        try:
            data = _read_log()
            try:
                data["_pack_def_include_thumbs"] = int(self._pack_def_include_thumbs_var.get())
            except Exception:
                pass
            try:
                data["_pack_def_previews_policy"] = str(self._pack_def_previews_policy_var.get())
            except Exception:
                pass
            try:
                data["_pack_def_doc_set"] = str(self._pack_def_doc_set_var.get())
            except Exception:
                pass
            try:
                # Store as ints if possible
                data["_pack_preview_pages"] = int(str(self._pack_prev_pages_var.get()).strip())
            except Exception:
                pass
            try:
                data["_pack_preview_pdf_pages"] = int(str(self._pack_prev_pdf_pages_var.get()).strip())
            except Exception:
                pass
            _write_log(data)
        except Exception:
            pass

    def _on_qa_footer_confirmed_change(self):
        try:
            data = _read_log()
            try:
                data["_pack_footer_confirmed"] = int(self._qa_footer_confirmed_var.get())
            except Exception:
                pass
            _write_log(data)
        except Exception:
            pass

    def _qa_acceptance_status(self, slug: str, include_outputs: bool = True):
        try:
            reasons = []
            if not slug:
                return False, ["No book selected"]
            # Outputs presence (if required) and file listing
            files = []
            outputs_present = False
            try:
                manp = STUDIOFORGE_DIR / "_CANONICAL_LOCKED" / "OUTPUTS" / "manifest.json"
                if manp.exists() and slug:
                    try:
                        man = json.loads(manp.read_text(encoding="utf-8", errors="ignore"))
                    except Exception:
                        man = {}
                    for _product, themes in (man or {}).items():
                        if isinstance(themes, dict) and slug in themes:
                            paths = (themes.get(slug, {}) or {}).get("paths", {})
                            for v in paths.values():
                                try:
                                    f = (BASE_DIR / v)
                                    if f.exists() and f.suffix.lower() == ".pdf":
                                        files.append(f)
                                except Exception:
                                    continue
                            break
                if not files:
                    root = STUDIOFORGE_DIR / "_CANONICAL_LOCKED" / "OUTPUTS"
                    if root.exists():
                        try:
                            for p in root.rglob(slug):
                                try:
                                    if p.is_dir():
                                        files.extend(list(p.glob("*.pdf")))
                                        if files:
                                            break
                                except Exception:
                                    continue
                        except Exception:
                            pass
                outputs_present = len(files) > 0
            except Exception:
                outputs_present = False
            if include_outputs and not outputs_present:
                reasons.append("Canonical outputs missing")
            # File naming prefix check (CODE_*.pdf)
            try:
                if files:
                    import re as _re
                    if not all(bool(_re.match(r"^[A-Z0-9]{3,}_.+\.pdf$", f.name)) for f in files):
                        reasons.append("File naming not code‑prefixed")
            except Exception:
                pass
            # Previews count (>= 2 recommended)
            try:
                prev_cnt = 0
                pd = BASE_DIR / "_previews" / slug
                if pd.exists():
                    try:
                        prev_cnt = len(list(pd.glob("*.png"))) + len(list(pd.glob("*.pdf")))
                    except Exception:
                        prev_cnt = 0
                if prev_cnt == 0:
                    pd2 = BASE_DIR / "03_UPLOAD_READY" / "TPT_Packs" / slug / "Previews"
                    if pd2.exists():
                        try:
                            prev_cnt = len(list(pd2.glob("*.png"))) + len(list(pd2.glob("*.pdf")))
                        except Exception:
                            prev_cnt = 0
                if prev_cnt < 2:
                    reasons.append("Insufficient previews (<2)")
            except Exception:
                pass
            # Thumbnail size check (square and >= 1000px)
            try:
                th = BASE_DIR / "assets" / "canva_thumbs" / f"{slug}.png"
                if not th.exists():
                    reasons.append("Thumbnail missing")
                else:
                    if _PIL_Image is not None:
                        try:
                            with _PIL_Image.open(str(th)) as im:
                                w, h = im.size
                            if abs(w - h) > 6 or min(w, h) < 1000:
                                reasons.append(f"Thumbnail size not OK ({w}×{h})")
                        except Exception:
                            pass
            except Exception:
                pass
            # Manual footer confirmation gate
            try:
                fc = int(self._qa_footer_confirmed_var.get()) if hasattr(self, "_qa_footer_confirmed_var") else int(_read_log().get("_pack_footer_confirmed", 0))
            except Exception:
                fc = 0
            if fc != 1:
                reasons.append("Footer not confirmed")
            return (len(reasons) == 0), reasons
        except Exception:
            return False, ["QA check error"]

    def _view_manifest_for_zip(self, zpath):
        try:
            if not zpath:
                messagebox.showinfo("Manifest", "No package recorded yet.")
                return
            zp = Path(zpath)
            if not zp.exists():
                messagebox.showerror("Manifest", f"Not found: {zp}")
                return
            import zipfile
            with zipfile.ZipFile(str(zp), "r") as zf:
                try:
                    raw = zf.read("manifest.json")
                except KeyError:
                    messagebox.showinfo("Manifest", "manifest.json not found in package.")
                    return
            try:
                txt = json.dumps(json.loads(raw.decode("utf-8", errors="ignore")), indent=2)
            except Exception:
                try:
                    txt = raw.decode("utf-8", errors="ignore")
                except Exception:
                    txt = str(raw)
            # Show in a simple dialog
            win = tk.Toplevel(self)
            win.title("Package manifest.json")
            try:
                win.geometry("640x520")
            except Exception:
                pass
            frm = tk.Frame(win)
            frm.pack(fill="both", expand=True)
            txtw = tk.Text(frm, wrap="none")
            txtw.pack(fill="both", expand=True, side="left")
            try:
                sb = tk.Scrollbar(frm, command=txtw.yview)
                sb.pack(side="right", fill="y")
                txtw.configure(yscrollcommand=sb.set)
            except Exception:
                pass
            try:
                txtw.insert("1.0", txt)
                txtw.configure(state="disabled")
            except Exception:
                pass
            tk.Button(win, text="Close", command=win.destroy).pack(pady=6)
        except Exception as e:
            messagebox.showerror("Manifest", str(e))

    def _show_help(self):
        try:
            win = tk.Toplevel(self)
            win.title("Tool Launcher — Help & Top Tips")
            try:
                win.geometry("620x520")
            except Exception:
                pass
            pad = {"padx": 12, "pady": 4, "anchor": "w"}
            tk.Label(win, text="Top Tips", font=("Segoe UI", 11, "bold")).pack(**pad, pady=(12, 6))
            tips = [
                "Select a book, then press Enter to Launch the current tool.",
                "Use Ctrl+O to open the selected book's theme folder.",
                "F5 refreshes all tabs and the book list without restarting.",
                "Open Output Folder jumps to Studioforge/OUTPUT/{pack_code} or theme OUTPUT fallbacks.",
                "Preflight shows readiness — green means Launch is enabled.",
                "Diagnostics summarizes interpreter, paths, and environment.",
                "Density toggles Comfortable/Compact tab spacing.",
            ]
            for t in tips:
                tk.Label(win, text=f"• {t}", wraplength=580, justify="left").pack(**pad)

            tk.Label(win, text="Quick Actions", font=("Segoe UI", 11, "bold")).pack(**pad, pady=(10, 6))
            row = tk.Frame(win)
            row.pack(fill="x", padx=12, pady=4)
            tk.Button(row, text="Open Themes Root", command=lambda: self._open_path(THEMES_DIR)).pack(side="left")
            tk.Button(row, text="Open Global OUTPUT", command=lambda: self._open_path(STUDIOFORGE_DIR / "OUTPUT")).pack(side="left", padx=6)
            tk.Button(row, text="Open Studioforge", command=lambda: self._open_path(STUDIOFORGE_DIR)).pack(side="left", padx=6)
            tk.Button(row, text="Open Generators", command=lambda: self._open_path(BASE_DIR / "Generators")).pack(side="left", padx=6)
            tk.Button(row, text="Open Logs", command=self._open_logs).pack(side="left", padx=6)
            tk.Button(row, text="Open Build Definition", command=lambda: self._open_path(BASE_DIR / "MD" / "WINDSURF_COMPLETE_BUILD_DEFINITION.md")).pack(side="left", padx=6)
            # Last package shortcuts
            row2 = tk.Frame(win)
            row2.pack(fill="x", padx=12, pady=4)
            tk.Button(row2, text="Open Last Package (ZIP)", command=self._open_last_package_zip).pack(side="left")
            tk.Button(row2, text="Open Last Package Folder", command=self._open_last_package_folder).pack(side="left", padx=6)

            tk.Label(win, text="Icon Labeler", font=("Segoe UI", 11, "bold")).pack(**pad, pady=(10, 6))
            tk.Label(win, text="Launch starts a local server and opens your browser. Default URL starts at http://127.0.0.1:5052.", wraplength=580, justify="left").pack(**pad)
            tk.Button(win, text="Open Icon Labeler URL", command=lambda: webbrowser.open("http://127.0.0.1:5052")).pack(**pad, pady=(6, 6))

            tk.Button(win, text="Close", command=win.destroy).pack(padx=12, pady=12, anchor="e")
        except Exception as e:
            messagebox.showerror("Help", str(e))

    def _set_density(self, density: str):
        try:
            density = (density or "").strip().lower()
            if density not in ("comfortable", "compact"):
                density = "comfortable"
            self._density = density
            data = _read_log()
            data["_density"] = density
            _write_log(data)
        except Exception:
            self._density = density

    def _apply_density(self):
        try:
            style = ttk.Style(self)
            if getattr(self, "_density", "comfortable") == "compact":
                style.configure("TNotebook.Tab", padding=(8, 3), font=("Segoe UI", 10))
                # Compact defaults for tk and ttk widgets
                try:
                    self.option_add("*Button.padx", 6)
                    self.option_add("*Button.pady", 2)
                    self.option_add("*Label.padx", 2)
                    self.option_add("*Label.pady", 1)
                except Exception:
                    pass
                try:
                    style.configure("TButton", padding=(6, 3))
                except Exception:
                    pass
            else:
                style.configure("TNotebook.Tab", padding=(12, 6), font=("Segoe UI", 10))
                try:
                    self.option_add("*Button.padx", 10)
                    self.option_add("*Button.pady", 5)
                    self.option_add("*Label.padx", 4)
                    self.option_add("*Label.pady", 2)
                except Exception:
                    pass
                try:
                    style.configure("TButton", padding=(10, 5))
                except Exception:
                    pass
        except Exception:
            pass

    def _toggle_density(self):
        try:
            newd = "compact" if getattr(self, "_density", "comfortable") == "comfortable" else "comfortable"
            self._set_density(newd)
            self._apply_density()
            try:
                self._density_btn.config(text=f"↕️ Density: {self._density.title()}")
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Density", str(e))

    # High Contrast helpers
    def _set_high_contrast(self, on: bool):
        try:
            self._high_contrast = bool(on)
            data = _read_log()
            try:
                data["_high_contrast"] = 1 if self._high_contrast else 0
            except Exception:
                data["_high_contrast"] = 0
            _write_log(data)
        except Exception:
            self._high_contrast = bool(on)

    def _apply_high_contrast(self):
        try:
            style = ttk.Style(self)
            # Base palette already set to white surfaces + navy text; in HC, strengthen states and footer
            if getattr(self, "_high_contrast", False):
                # Selected tab stays teal with white text
                style.configure("TNotebook", background="#FFFFFF")
                style.configure("TNotebook.Tab", foreground="#0B1220")
                style.map(
                    "TNotebook.Tab",
                    background=[("selected", SWS_TEAL), ("active", "#D1D5DB")],
                    foreground=[("selected", "white"), ("active", "#0B1220")],
                )
                try:
                    if getattr(self, "status", None):
                        self.status.config(bg="#0D2545", fg="#FFFFFF")
                except Exception:
                    pass
            else:
                # Default light theme
                style.configure("TNotebook", background="#FFFFFF")
                style.configure("TNotebook.Tab", foreground="#0D2545")
                style.map(
                    "TNotebook.Tab",
                    background=[("selected", SWS_TEAL), ("active", "#E5E7EB")],
                    foreground=[("selected", "white"), ("active", "#0D2545")],
                )
                try:
                    if getattr(self, "status", None):
                        self.status.config(bg="#FFFFFF", fg="#0D2545")
                except Exception:
                    pass
            # Update header toggle text
            try:
                if getattr(self, "_contrast_btn", None):
                    self._contrast_btn.config(text=f"🌓 High Contrast: {'On' if self._high_contrast else 'Off'}")
            except Exception:
                pass
        except Exception:
            pass

    def _toggle_high_contrast(self):
        try:
            self._set_high_contrast(not bool(getattr(self, "_high_contrast", False)))
            self._apply_high_contrast()
        except Exception as e:
            messagebox.showerror("High Contrast", str(e))

    def _toggle_tips(self):
        try:
            self._show_tips = 0 if int(getattr(self, "_show_tips", 1)) else 1
        except Exception:
            self._show_tips = 0 if bool(getattr(self, "_show_tips", True)) else 1
        # Persist
        try:
            data = _read_log()
            data["_show_tips_launcher"] = int(self._show_tips)
            _write_log(data)
        except Exception:
            pass
        # Update UI
        try:
            if getattr(self, "_tips_frame", None):
                if int(self._show_tips):
                    self._tips_frame.pack(fill="x")
                else:
                    self._tips_frame.pack_forget()
        except Exception:
            pass
        try:
            if getattr(self, "_tips_btn", None):
                self._tips_btn.config(text=("💡 Hide Tips" if int(self._show_tips) else "💡 Show Tips"))
        except Exception:
            pass

    def _open_icon_labeler_from_tips(self):
        try:
            # Reuse launcher logic; create a dummy label for log updates
            if not hasattr(self, "_il_lu_dummy"):
                self._il_lu_dummy = tk.Label(self, text="")
            self._launch_icon_labeler(self._il_lu_dummy)
        except Exception as e:
            try:
                messagebox.showerror("Icon Labeler", str(e))
            except Exception:
                pass

    def _open_pdf_extractor_from_tips(self):
        try:
            # Single instance on 5052: reuse if running, otherwise start ICON_LABELER.py there.
            port = 5052
            try:
                if _is_server_alive(port):
                    webbrowser.open(f"http://127.0.0.1:{port}/pdf")
                    _touch_used("pdf_extractor")
                    return
            except Exception:
                pass
            script = STUDIOFORGE_DIR / "ICON_LABELER.py"
            if not script.exists():
                messagebox.showerror("Missing file", f"Not found: {script}")
                return
            ok = _run_in_console([PYTHON, str(script), str(port)], STUDIOFORGE_DIR)
            if ok:
                url = f"http://127.0.0.1:{port}/pdf"
                _open_icon_labeler_later(url=url, ping_path="/api/ping")
                _touch_used("pdf_extractor")
        except Exception as e:
            try:
                messagebox.showerror("PDF Extractor", str(e))
            except Exception:
                pass

    def _show_diagnostics(self):
        try:
            lines = []
            lines.append(f"Python: {PYTHON}")
            try:
                lines.append(f"Interpreter source: {PYTHON_SOURCE}")
            except Exception:
                lines.append("Interpreter source: unknown")
            lines.append(f"STUDIOFORGE_DIR: {STUDIOFORGE_DIR}")
            lines.append(f"BASE_DIR: {BASE_DIR}")
            lines.append(f"THEMES_DIR: {THEMES_DIR} ({'ok' if THEMES_DIR.exists() else 'missing'})")
            try:
                bcount = len(self.books) if hasattr(self, 'books') and isinstance(self.books, list) else 0
                lines.append(f"Books detected: {bcount}")
            except Exception:
                pass
            lines.append(f"Env STUDIOFORGE_ROOT: {os.environ.get('STUDIOFORGE_ROOT', '')}")
            lines.append(f"Env PYTHONPATH: {os.environ.get('PYTHONPATH', '')}")
            try:
                kp = os.environ.get('SWS_KEY_PREFIX')
                ks = os.environ.get('SWS_KEY_SRC')
                if not kp:
                    v, src = _get_anthropic_key()
                    kp = (v or '')[:15] if v else ''
                    ks = src or ks
                if kp:
                    lines.append(f"Anthropic key: present ({kp}… from {ks})")
                else:
                    lines.append("Anthropic key: missing")
            except Exception:
                lines.append("Anthropic key: unknown")
            msg = "\n".join(lines)
            messagebox.showinfo("Diagnostics", msg)
        except Exception as e:
            messagebox.showerror("Diagnostics", str(e))

    def _preflight_tool(self, tool, slug):
        try:
            issues = []
            try:
                needs_slug = tool in ("board_ready", "matching", "listing_generator")
            except Exception:
                needs_slug = True
            if needs_slug and not slug:
                issues.append("No book selected")
            reqs = []
            try:
                reqs = (TOOLS.get(tool, {}) or {}).get("requires", []) or []
            except Exception:
                reqs = []
            for tok in reqs:
                cands = _requirement_candidates(tok)
                ok = False
                for p in cands:
                    try:
                        if p.exists():
                            ok = True
                            break
                    except Exception:
                        continue
                if not ok:
                    issues.append(f"Missing {_requirement_name(tok)}")
            try:
                if tool in ("board_ready", "matching") and slug:
                    ready, imsg, n = self._icons_ready_and_count(slug)
                    if not ready:
                        issues.append(f"Icons gating: require 15 curated icons ({n}/15). {imsg}")
            except Exception:
                pass
            if tool == "icon_labeler":
                try:
                    ok_script = (STUDIOFORGE_DIR / "ICON_LABELER.py").exists()
                except Exception:
                    ok_script = False
                if not ok_script:
                    issues.append("Missing ICON_LABELER.py")
            if issues:
                return False, "Preflight: " + "; ".join(issues)
            return True, "Preflight OK"
        except Exception as e:
            return False, f"Preflight error: {e}"

    def _update_preflight(self, tool, slug, launch_btn, status_label):
        try:
            status_label.config(text="⏳ Checking…", fg="#64748B")
        except Exception:
            pass

        def _paint(ok, msg):
            try:
                icon = "✅" if ok else "⚠️"
                status_label.config(text=f"{icon} {msg}", fg=("#0a0" if ok else "#a00"))
            except Exception:
                pass
            try:
                launch_btn.config(state=("normal" if ok else "disabled"))
            except Exception:
                pass

        def _worker():
            try:
                ok, msg = self._preflight_tool(tool, slug)
            except Exception as e:
                ok, msg = False, f"Preflight error: {e}"
            try:
                self.after(0, lambda: _paint(ok, msg))
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _current_tab_frame(self):
        try:
            tid = self.tabs.select()
            return self.nametowidget(tid)
        except Exception:
            return None

    # Helpers: icons count, tint, and tab selection
    def _clamp_geometry(self, g: str) -> str:
        try:
            import re
            m = re.match(r"(\d+)x(\d+)([+-]\d+)([+-]\d+)", g)
            if not m:
                return "1040x740"
            w, h, x, y = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            if w > sw:
                w = sw
            if h > sh:
                h = sh
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            if x + w > sw:
                x = max(0, sw - w)
            if y + h > sh:
                y = max(0, sh - h)
            return f"{w}x{h}+{x}+{y}"
        except Exception:
            return "1040x740"

    def _count_activity_icons(self, slug: str) -> int:
        try:
            p = THEMES_DIR / slug / "activity_images"
            if not p.exists():
                return 0
            exts = {".png", ".jpg", ".jpeg", ".webp"}
            return sum(1 for f in p.iterdir() if f.is_file() and f.suffix.lower() in exts)
        except Exception:
            return 0

    def _icons_chip_style(self, n: int):
        try:
            if n >= 15:
                return ("#14532D", "#D1FAE5")  # fg, bg (emerald)
            if n >= 10:
                return ("#92400E", "#FEF3C7")  # amber
            return ("#B91C1C", "#FEE2E2")      # red
        except Exception:
            return ("#0D2545", "#FFFFFF")

    def _icons_ready_and_count(self, slug: str):
        try:
            # Prefer live checklist service if available
            ic = _icons_check_status(slug)
            n = self._count_activity_icons(slug)
            if isinstance(ic, tuple):
                try:
                    _svc_ready = bool(ic[0])
                except Exception:
                    _svc_ready = None
                try:
                    msg = str(ic[1])
                except Exception:
                    msg = ""
                # Gate strictly on curated count; service only informs the message
                return (n >= 15), (msg or ("OK" if n >= 15 else f"{n}/15 icons")), n
            # Fallback to curated icons count
            return (n >= 15), ("OK" if n >= 15 else f"{n}/15 icons"), n
        except Exception:
            try:
                n = self._count_activity_icons(slug)
            except Exception:
                n = 0
            return (n >= 15), ("OK" if n >= 15 else f"{n}/15 icons"), n

    def _readiness_report(self, slug: str, title: str, code: str, keys: list[str]):
        try:
            # Locate readiness_report.py from env or common locations
            cand_env = os.environ.get("READINESS_REPORT_PY")
            candidates = []
            if cand_env:
                try:
                    candidates.append(Path(cand_env))
                except Exception:
                    pass
            candidates.append(Path(__file__).resolve().parent / "tools" / "readiness_report.py")
            # Preferred D: source-of-truth path
            candidates.append(Path("D:/Seagate/small-wins-automation/Studioforge/tools/readiness_report.py"))
            script = next((p for p in candidates if isinstance(p, Path) and p.exists()), None)
            if not script:
                return None
            # Lazy init cache
            if not hasattr(self, "_readiness_cache"):
                self._readiness_cache = {}
            cache_key = (slug, tuple(sorted(keys)))
            if cache_key in self._readiness_cache:
                return self._readiness_cache[cache_key]
            cmd = [PYTHON, str(script), "--slug", slug, "--title", title or "", "--code", code, "--keys", *keys]
            p = subprocess.run(cmd, cwd=str(script.parent), capture_output=True, text=True, timeout=180)
            out = (p.stdout or "") + "\n" + (p.stderr or "")
            # Parse report path
            json_path = None
            try:
                m = re.search(r"Report:\s*(.+)", out)
                if m:
                    jp = m.group(1).strip().strip('"')
                    jpp = Path(jp)
                    if not jpp.is_absolute():
                        jpp = (script.parent / jpp).resolve()
                    json_path = jpp
            except Exception:
                json_path = None
            if not json_path or not json_path.exists():
                # Fallback to latest readiness JSON for this slug in _reports
                rep_dir = script.parent / "_reports"
                try:
                    cands = sorted(rep_dir.glob(f"readiness_{slug}_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                except Exception:
                    cands = []
                if cands:
                    json_path = cands[0]
            if not json_path or not json_path.exists():
                return None
            try:
                data = json.loads(json_path.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                return None
            summary = {}
            for r in data.get("results", []):
                k = r.get("product_key")
                try:
                    summary[k] = int(r.get("outputs_found") or 0)
                except Exception:
                    continue
            self._readiness_cache[cache_key] = summary
            return summary
        except Exception:
            return None

    def _select_tab_by_text(self, text: str):
        try:
            for tid in list(self.tabs.tabs()):
                try:
                    if self.tabs.tab(tid, "text") == text:
                        self.tabs.select(tid)
                        return
                except Exception:
                    continue
            # Sub-notebooks (e.g. Review and track -> Pipeline Dashboard / Jobs + Progress)
            for outer, sub in getattr(self, "_sub_notebooks", []):
                for stid in list(sub.tabs()):
                    try:
                        if sub.tab(stid, "text") == text:
                            self.tabs.select(str(outer))
                            sub.select(stid)
                            return
                    except Exception:
                        continue
        except Exception:
            pass

    def _pack_code_for_slug(self, slug: str) -> str:
        try:
            meta = next((b for b in self.books if b.get("slug") == slug), None)
            code = (meta or {}).get("code")
            return code or (slug[:3].upper() + "1")
        except Exception:
            return slug[:3].upper() + "1"

    def _has_aac_boards(self, slug: str) -> bool:
        try:
            p = THEMES_DIR / slug / "aac_boards"
            if not p.exists():
                return False
            for f in p.iterdir():
                try:
                    if f.is_file() and f.suffix.lower() == ".pdf":
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            return False

    def _has_matching_outputs(self, slug: str) -> bool:
        try:
            base = self._resolve_output_dir(slug, self._pack_code_for_slug(slug))
            if not base:
                return False
            # Look for Matching PDFs or BuildResult
            for f in base.iterdir():
                try:
                    nm = f.name.lower()
                    if (f.is_file() and (nm.endswith(".pdf") or nm.endswith(".json")) and ("matching" in nm)):
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            return False

    def _goto_tool_with_slug(self, tab_text: str, slug: str):
        try:
            for tid in list(self.tabs.tabs()):
                try:
                    if self.tabs.tab(tid, "text") == tab_text:
                        tf = self.nametowidget(tid)
                        ctx = getattr(tf, "_ctx", None)
                        if ctx:
                            sv = ctx.get("slug_var")
                            if sv:
                                try:
                                    sv.set(slug)
                                except Exception:
                                    pass
                        self.tabs.select(tid)
                        break
                except Exception:
                    continue
        except Exception:
            pass

    def _current_slug_guess(self):
        try:
            tf = self._current_tab_frame()
            ctx = getattr(tf, "_ctx", None)
            sv = ctx.get("slug_var") if ctx else None
            if sv:
                s = sv.get()
                if s:
                    return s
        except Exception:
            pass
        try:
            if getattr(self, "_last_book_slug", None):
                return self._last_book_slug
        except Exception:
            pass
        try:
            if isinstance(self.books, list) and self.books:
                return self.books[0].get("slug")
        except Exception:
            pass
        return None

    def _anthropic_key_brief(self):
        try:
            v, src = _get_anthropic_key()
            if v:
                pref = (v or '')[:6]
                s = os.environ.get("SWS_KEY_SRC") or src or "env"
                try:
                    s_disp = Path(str(s).split('#')[0]).name
                except Exception:
                    s_disp = str(s)
                return True, f"Claude: OK ({pref}… · {s_disp})"
            return False, "Claude: Missing"
        except Exception:
            return False, "Claude: Unknown"

    def _next_step_for_slug(self, slug: str, status: dict | None = None):
        st = status if isinstance(status, dict) else self._guided_status(slug)
        for key, _stage, name, _hint, required, tool_tab, run_key in self.GUIDED_STEPS:
            if not required or st.get(key):
                continue
            def _go(s=slug, t=tool_tab, rk=run_key, nm=name):
                if t:
                    self._goto_tool_with_slug(t, s)
                else:
                    self._open_theme_folder(s)
                if rk:
                    try:
                        if messagebox.askyesno(nm, f"Run {nm} now for {s}?"):
                            self._guided_run(rk, s)
                    except Exception:
                        pass
            return name, _go
        return "All done — open Upload-Ready ZIPs", (lambda: self._open_path(STUDIOFORGE_DIR / "UPLOAD_READY"))

    def _do_next_step_current(self):
        slug = self._current_slug_guess()
        if not slug:
            try:
                messagebox.showwarning("Next Step", "Please select a book first.")
            except Exception:
                pass
            return
        try:
            _label, act = self._next_step_for_slug(slug)
            if callable(act):
                act()
        except Exception as e:
            try:
                messagebox.showerror("Next Step", str(e))
            except Exception:
                pass

    def _launch_current(self, *_):
        try:
            tf = self._current_tab_frame()
            ctx = getattr(tf, "_ctx", None)
            if ctx and callable(ctx.get("launch")):
                ctx["launch"]()
        except Exception:
            pass

    def _open_theme_current(self, *_):
        try:
            tf = self._current_tab_frame()
            ctx = getattr(tf, "_ctx", None)
            sv = ctx.get("slug_var") if ctx else None
            if sv:
                self._open_theme_folder(sv.get())
        except Exception:
            pass

    def _refresh_books(self, *_):
        try:
            # Reset transient readiness cache so fresh reports are used
            try:
                if hasattr(self, "_readiness_cache"):
                    self._readiness_cache = {}
            except Exception:
                pass
            try:
                self._guided_cache = {}
            except Exception:
                pass
            self.books = _list_books(force=True)
            # Rebuild all tabs to pick up new book list
            for tid in list(self.tabs.tabs()):
                try:
                    self.tabs.forget(tid)
                except Exception:
                    pass
            self._init_board_tab()
            self._init_matching_tab()
            self._init_guided_tab()
            self._init_code_words_tab()
            self._init_book_insert_strips_tab()
            self._init_listing_tab()
            self._init_ai_tab()
            self._init_topic_builder_tab()
            self._init_icon_labeler_tab()
            self._sub_notebooks = []
            self._init_review_tab()
            self._init_pack_tab()
            self._init_qa_tab()
            try:
                self._build_left_nav()
            except Exception:
                pass
            try:
                _log_event("refresh_books", {"count": len(self.books)})
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Refresh All", str(e))

    def _bind_shortcuts(self):
        # Global key bindings
        try:
            self.bind("<Return>", self._launch_current)
        except Exception:
            pass
        try:
            self.bind("<Control-o>", self._open_theme_current)
        except Exception:
            pass
        try:
            self.bind("<F5>", self._refresh_books)
        except Exception:
            pass
        try:
            self.bind("<Control-k>", lambda e: self._open_command_palette())
        except Exception:
            pass
        # Convenience shortcuts
        try:
            self.bind("<Control-l>", lambda e: self._open_logs())
        except Exception:
            pass
        try:
            self.bind("<Control-Shift-O>", lambda e: self._open_path(STUDIOFORGE_DIR / "OUTPUT"))
        except Exception:
            pass
        try:
            self.bind("<Control-Shift-P>", lambda e: self._open_path(STUDIOFORGE_DIR / "UPLOAD_READY"))
        except Exception:
            pass
        try:
            self.bind("<Control-Shift-E>", lambda e: self._open_pdf_extractor_from_tips())
        except Exception:
            pass
        try:
            self.bind("<Control-Shift-H>", lambda e: self._toggle_high_contrast())
        except Exception:
            pass

    def _on_tab_change(self, *_):
        try:
            tid = self.tabs.select()
            txt = self.tabs.tab(tid, "text")
            data = _read_log()
            data["_last_tab_text"] = txt
            _write_log(data)
            try:
                self._highlight_nav_for_text(txt)
            except Exception:
                pass
        except Exception:
            pass

    def _set_initial_tab_from_log(self):
        try:
            last = _read_log().get("_last_tab_text") or "Guided Start"
            for tid in list(self.tabs.tabs()):
                try:
                    if self.tabs.tab(tid, "text") == last:
                        self.tabs.select(tid)
                        break
                except Exception:
                    continue
        except Exception:
            pass

    def _on_tabs_motion(self, e):
        try:
            idx = None
            try:
                idx = self.tabs.index(f"@{e.x},{e.y}")
            except Exception:
                idx = None
            if idx is None:
                self._on_tabs_leave()
                return
            tids = list(self.tabs.tabs())
            if idx < 0 or idx >= len(tids):
                self._on_tabs_leave()
                return
            tid = tids[idx]
            txt = self._tab_tooltips.get(tid)
            if not txt:
                self._on_tabs_leave()
                return
            x = self.tabs.winfo_rootx() + e.x + 16
            y = self.tabs.winfo_rooty() + e.y + 20
            if getattr(self, "_tab_tip", None) is None:
                self._tab_tip = tk.Toplevel(self.tabs)
                self._tab_tip.wm_overrideredirect(True)
            try:
                self._tab_tip.wm_geometry(f"+{x}+{y}")
                for c in list(self._tab_tip.children.values()):
                    try:
                        c.destroy()
                    except Exception:
                        pass
                tk.Label(self._tab_tip, text=txt, bg="#ffffe0", relief="solid", borderwidth=1, padx=6, pady=3).pack()
            except Exception:
                self._on_tabs_leave()
        except Exception:
            self._on_tabs_leave()

    def _on_tabs_leave(self, *_):
        try:
            if getattr(self, "_tab_tip", None) is not None:
                self._tab_tip.destroy()
                self._tab_tip = None
        except Exception:
            self._tab_tip = None

    def _rebuild_pack_tab(self):
        try:
            idx = None
            for i, tid in enumerate(self.tabs.tabs()):
                try:
                    if self.tabs.tab(tid, "text") == "Pack Ready":
                        idx = i
                        break
                except Exception:
                    continue
            if idx is None:
                return
            tid = self.tabs.tabs()[idx]
            self.tabs.forget(tid)
            self._init_pack_tab()
            try:
                self.tabs.select(self.tabs.tabs()[-1])
            except Exception:
                pass
        except Exception:
            pass

    def _finalize_packaging(self):
        try:
            docs = _packaging_docs_find()
            inc_docs = True
            inc_out = True
            inc_icons = False
            inc_qa = False
            try:
                inc_docs = bool(self._pack_docs_var.get())
                inc_out = bool(self._pack_outputs_var.get())
                inc_icons = bool(self._pack_icons_req_var.get())
                inc_qa = bool(self._pack_qa_req_var.get())
            except Exception:
                pass
            if not inc_docs and not inc_out:
                messagebox.showinfo("Packaging", "Select at least one: Include Docs and/or Include Outputs.")
                return
            if inc_docs and not (docs.get("root") and docs.get("tou") and docs.get("quick")):
                messagebox.showinfo("Packaging", "Required docs not present yet (need TOU and Quick Start).")
                return
            tf = self._current_tab_frame()
            ctx = getattr(tf, "_ctx", None) if tf else None
            slug = None
            title = None
            code = None
            try:
                if ctx:
                    sv = ctx.get("slug_var")
                    tv = ctx.get("title_var")
                    cv = ctx.get("code_var")
                    slug = sv.get() if sv else None
                    title = tv.get() if tv else None
                    code = cv.get() if cv else None
            except Exception:
                pass
            if not slug:
                try:
                    slug = getattr(self, "_last_book_slug", None)
                except Exception:
                    slug = None
            if not slug:
                messagebox.showwarning("Packaging", "Please select a book (slug) in the Pack Ready tab before finalizing.")
                return
            # Optional icons gating
            if inc_icons and slug:
                ic = _icons_check_status(slug)
                ic_ok = (isinstance(ic, tuple) and bool(ic[0]))
                if not ic_ok:
                    imsg = "Icons status unknown"
                    try:
                        if isinstance(ic, tuple):
                            imsg = str(ic[1])
                    except Exception:
                        pass
                    messagebox.showinfo("Packaging", f"Icons gating: {imsg}. Packaging aborted (Require Icons OK).")
                    return
            # Optional QA acceptance gating
            if inc_qa and slug:
                ok_qa, reasons = self._qa_acceptance_status(slug, include_outputs=inc_out)
                if not ok_qa:
                    try:
                        why = "; ".join([str(r) for r in (reasons or [])]) or "QA not accepted"
                    except Exception:
                        why = "QA not accepted"
                    messagebox.showinfo("Packaging", f"QA gating: {why}. Packaging aborted (Require QA OK).")
                    return
            # Determine output dir with fallbacks
            pack_code = code or (slug[:3].upper() + "1")
            out_dir = None
            for p in [
                STUDIOFORGE_DIR / "OUTPUT" / str(pack_code),
                THEMES_DIR / slug / "OUTPUT",
                THEMES_DIR / slug / "05 outputs",
                THEMES_DIR / slug / "output",
            ]:
                try:
                    if p.exists():
                        out_dir = p
                        break
                except Exception:
                    continue
            if inc_out and not out_dir:
                try:
                    ok = messagebox.askyesno("Packaging", "No outputs found for this pack. Continue without outputs?")
                except Exception:
                    ok = True
                if not ok:
                    return
            # Dry-run preview
            try:
                if not self._show_single_pack_preview(slug, code, docs, inc_docs, inc_out, inc_icons):
                    return
            except Exception:
                pass
            # Build ZIP
            import zipfile  # local import
            dest_root = STUDIOFORGE_DIR / "UPLOAD_READY"
            try:
                dest_root.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            try:
                pat = self._pack_name_pattern_var.get()
            except Exception:
                try:
                    pat = _read_log().get("_pack_name_pattern", "{pack_code}_{slug}_UPLOAD_READY_{ts}{ver}.zip")
                except Exception:
                    pat = "{pack_code}_{slug}_UPLOAD_READY_{ts}{ver}.zip"
            try:
                ver = self._pack_version_var.get()
            except Exception:
                try:
                    ver = _read_log().get("_pack_version_tag", "")
                except Exception:
                    ver = ""
            zname = self._render_zip_name(pat, pack_code, slug, (title or slug.replace("_", " ").title()), ts, ver)
            zpath = dest_root / zname
            manifest = {
                "slug": slug,
                "title": (title or slug.replace("_", " ").title()),
                "pack_code": pack_code,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "outputs_dir": str(out_dir) if out_dir else None,
                "docs": {
                    "root": str(docs.get("root")) if docs.get("root") else None,
                    "tou": str(docs.get("tou")) if docs.get("tou") else None,
                    "quick": str(docs.get("quick")) if docs.get("quick") else None,
                    "rope_count": len(docs.get("rope") or []),
                },
            }
            with zipfile.ZipFile(str(zpath), "w", compression=zipfile.ZIP_DEFLATED) as zf:
                # Docs (optional)
                if inc_docs:
                    try:
                        tou = docs.get("tou")
                        quick = docs.get("quick")
                        rope = docs.get("rope") or []
                        if tou and Path(tou).exists():
                            zf.write(str(tou), arcname=f"docs/{Path(tou).name}")
                        if quick and Path(quick).exists():
                            zf.write(str(quick), arcname=f"docs/{Path(quick).name}")
                        for rp in rope:
                            try:
                                if Path(rp).is_file():
                                    zf.write(str(rp), arcname=f"docs/{Path(rp).name}")
                            except Exception:
                                continue
                    except Exception:
                        pass
                # OUTPUT (optional)
                if inc_out and out_dir and out_dir.exists():
                    for fp in out_dir.rglob("*"):
                        try:
                            if fp.is_file():
                                rel = fp.relative_to(out_dir)
                                zf.write(str(fp), arcname=str(Path("OUTPUT") / rel))
                        except Exception:
                            continue
                # Manifest
                try:
                    zf.writestr("manifest.json", json.dumps(manifest, indent=2))
                except Exception:
                    pass
            try:
                _log_event("package", {"zip": str(zpath), "slug": slug, "pack_code": pack_code})
            except Exception:
                pass
            # Remember last package location
            try:
                data = _read_log()
                data["_last_package_zip"] = str(zpath)
                try:
                    data["_last_package_time"] = datetime.now().isoformat(timespec="seconds")
                except Exception:
                    pass
                # Persist last-used toggles
                try:
                    data["_last_pack_include_docs"] = int(inc_docs)
                except Exception:
                    pass
                try:
                    data["_last_pack_include_outputs"] = int(inc_out)
                except Exception:
                    pass
                try:
                    data["_last_pack_require_icons_ok"] = int(inc_icons)
                except Exception:
                    pass
                try:
                    data["_last_pack_require_qa_ok"] = int(inc_qa)
                except Exception:
                    pass
                _write_log(data)
            except Exception:
                pass
            try:
                self._update_last_package_header_status(schedule=False)
            except Exception:
                pass
            self._open_path(dest_root)
            messagebox.showinfo("Packaging", f"Package created: {zname}")
        except Exception as e:
            messagebox.showerror("Packaging", str(e))

    def _build_package_for(self, slug, title, code, docs, include_docs=True, include_outputs=True):
        try:
            if not include_docs and not include_outputs:
                return None
            if include_docs and not (docs and docs.get("root") and docs.get("tou") and docs.get("quick")):
                return None
            pack_code = code or (slug[:3].upper() + "1")
            out_dir = self._resolve_output_dir(slug, code)
            import zipfile  # local import
            dest_root = STUDIOFORGE_DIR / "UPLOAD_READY"
            try:
                dest_root.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            try:
                pat = self._pack_name_pattern_var.get()
            except Exception:
                try:
                    pat = _read_log().get("_pack_name_pattern", "{pack_code}_{slug}_UPLOAD_READY_{ts}{ver}.zip")
                except Exception:
                    pat = "{pack_code}_{slug}_UPLOAD_READY_{ts}{ver}.zip"
            try:
                ver = self._pack_version_var.get()
            except Exception:
                try:
                    ver = _read_log().get("_pack_version_tag", "")
                except Exception:
                    ver = ""
            zname = self._render_zip_name(pat, pack_code, slug, (title or slug.replace("_", " ").title()), ts, ver)
            zpath = dest_root / zname
            manifest = {
                "slug": slug,
                "title": (title or slug.replace("_", " ").title()),
                "pack_code": pack_code,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "outputs_dir": str(out_dir) if out_dir else None,
                "docs": {
                    "root": str(docs.get("root")) if docs.get("root") else None,
                    "tou": str(docs.get("tou")) if docs.get("tou") else None,
                    "quick": str(docs.get("quick")) if docs.get("quick") else None,
                    "rope_count": len(docs.get("rope") or []),
                },
            }
            with zipfile.ZipFile(str(zpath), "w", compression=zipfile.ZIP_DEFLATED) as zf:
                if include_docs:
                    try:
                        tou = docs.get("tou"); quick = docs.get("quick"); rope = docs.get("rope") or []
                        if tou and Path(tou).exists():
                            zf.write(str(tou), arcname=f"docs/{Path(tou).name}")
                        if quick and Path(quick).exists():
                            zf.write(str(quick), arcname=f"docs/{Path(quick).name}")
                        for rp in rope:
                            try:
                                if Path(rp).is_file():
                                    zf.write(str(rp), arcname=f"docs/{Path(rp).name}")
                            except Exception:
                                continue
                    except Exception:
                        pass
                if include_outputs and out_dir and out_dir.exists():
                    for fp in out_dir.rglob("*"):
                        try:
                            if fp.is_file():
                                rel = fp.relative_to(out_dir)
                                zf.write(str(fp), arcname=str(Path("OUTPUT") / rel))
                        except Exception:
                            continue
                try:
                    zf.writestr("manifest.json", json.dumps(manifest, indent=2))
                except Exception:
                    pass
            try:
                _log_event("package", {"zip": str(zpath), "slug": slug, "pack_code": pack_code})
            except Exception:
                pass
            return zpath
        except Exception:
            return None

    def _fmt_size(self, b):
        try:
            b = float(b or 0)
            if b < 1024:
                return f"{int(b)} B"
            if b < 1024 * 1024:
                return f"{b / 1024.0:.1f} KB"
            return f"{b / (1024.0 * 1024.0):.1f} MB"
        except Exception:
            return str(b)

    def _sanitize_filename(self, name: str) -> str:
        try:
            out = []
            for ch in str(name):
                if ch.isalnum() or ch in "._-":
                    out.append(ch)
                else:
                    out.append("_")
            s = "".join(out)
            return s.strip("._ ") or "package.zip"
        except Exception:
            return "package.zip"

    def _render_zip_name(self, pattern: str, pack_code: str, slug: str, title: str, ts: str, version: str) -> str:
        try:
            base_pat = pattern or "{pack_code}_{slug}_UPLOAD_READY_{ts}{ver}.zip"
            ver_clean = str(version or "").strip()
            ver_token = ("_" + ver_clean) if ver_clean else ""
            mapping = {
                "pack_code": pack_code,
                "slug": slug,
                "title": (title or slug.replace("_", " ").title()),
                "ts": ts,
                "ver": ver_token,
            }
            try:
                name = str(base_pat).format(**mapping)
            except Exception:
                name = f"{pack_code}_{slug}_UPLOAD_READY_{ts}{ver_token}.zip"
            if not name.lower().endswith(".zip"):
                name = name + ".zip"
            return self._sanitize_filename(name)
        except Exception:
            fallback = f"{pack_code}_{slug}_UPLOAD_READY_{ts}.zip"
            return self._sanitize_filename(fallback)

    def _estimate_package(self, slug, code, docs, include_docs=True, include_outputs=True):
        try:
            res = {"docs_count": 0, "docs_size": 0, "outputs_count": 0, "outputs_size": 0}
            if include_docs and isinstance(docs, dict):
                for fp in [docs.get("tou"), docs.get("quick")]:
                    try:
                        if fp and Path(fp).is_file():
                            res["docs_count"] += 1
                            res["docs_size"] += Path(fp).stat().st_size
                    except Exception:
                        pass
                for rp in (docs.get("rope") or []):
                    try:
                        if Path(rp).is_file():
                            res["docs_count"] += 1
                            res["docs_size"] += Path(rp).stat().st_size
                    except Exception:
                        pass
            if include_outputs:
                try:
                    base = self._resolve_output_dir(slug, code)
                except Exception:
                    base = None
                if base and base.exists():
                    for fp in base.rglob("*"):
                        try:
                            if fp.is_file():
                                res["outputs_count"] += 1
                                res["outputs_size"] += fp.stat().st_size
                        except Exception:
                            continue
            res["total_size"] = int(res["docs_size"] + res["outputs_size"])
            return res
        except Exception:
            return {"docs_count": 0, "docs_size": 0, "outputs_count": 0, "outputs_size": 0, "total_size": 0}

    def _show_single_pack_preview(self, slug, code, docs, include_docs, include_outputs, require_icons):
        try:
            est = self._estimate_package(slug, code, docs, include_docs, include_outputs)
            win = tk.Toplevel(self)
            win.title(f"Packaging Preview — {slug}")
            try:
                win.geometry("420x260")
            except Exception:
                pass
            frm = tk.Frame(win)
            frm.pack(fill="both", expand=True, padx=12, pady=10)
            tk.Label(frm, text=f"Include Docs: {'Yes' if include_docs else 'No'}").pack(anchor="w")
            tk.Label(frm, text=f"Include Outputs: {'Yes' if include_outputs else 'No'}").pack(anchor="w")
            tk.Label(frm, text=f"Require Icons OK: {'Yes' if require_icons else 'No'}").pack(anchor="w", pady=(0, 6))
            # Also show QA requirement status (from current UI toggle if present)
            try:
                rq = bool(self._pack_qa_req_var.get())
            except Exception:
                try:
                    rq = bool(int(_read_log().get("_pack_require_qa_ok", 0)))
                except Exception:
                    rq = False
            tk.Label(frm, text=f"Require QA OK: {'Yes' if rq else 'No'}").pack(anchor="w", pady=(0, 6))
            tk.Label(frm, text=f"Docs: {est['docs_count']} file(s), {self._fmt_size(est['docs_size'])}").pack(anchor="w")
            tk.Label(frm, text=f"Outputs: {est['outputs_count']} file(s), {self._fmt_size(est['outputs_size'])}").pack(anchor="w")
            tk.Label(frm, text=f"Total approx: {self._fmt_size(est['total_size'])}", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(6, 0))
            row = tk.Frame(frm); row.pack(fill="x", pady=(10, 0))
            proceed = {"v": False}
            def _go():
                proceed["v"] = True
                try:
                    win.destroy()
                except Exception:
                    pass
            def _cancel():
                proceed["v"] = False
                try:
                    win.destroy()
                except Exception:
                    pass
            tk.Button(row, text="Proceed", command=_go).pack(side="right")
            tk.Button(row, text="Cancel", command=_cancel).pack(side="right", padx=6)
            try:
                win.transient(self); win.grab_set()
            except Exception:
                pass
            try:
                self.wait_window(win)
            except Exception:
                pass
            try:
                _log_event("package_preview", {"slug": slug, "docs": int(bool(include_docs)), "outputs": int(bool(include_outputs)), "icons_req": int(bool(require_icons)), "docs_count": int(est.get('docs_count',0)), "outputs_count": int(est.get('outputs_count',0)), "total_size": int(est.get('total_size',0))})
            except Exception:
                pass
            return bool(proceed["v"])
        except Exception:
            return False

    def _show_multi_pack_preview(self, metas, docs, include_docs, include_outputs, require_icons):
        try:
            win = tk.Toplevel(self)
            win.title("Packaging Preview — Multiple Books")
            try:
                win.geometry("540x420")
            except Exception:
                pass
            body = tk.Frame(win); body.pack(fill="both", expand=True, padx=12, pady=10)
            tk.Label(body, text=f"Include Docs: {'Yes' if include_docs else 'No'} • Include Outputs: {'Yes' if include_outputs else 'No'} • Require Icons OK: {'Yes' if require_icons else 'No'}").pack(anchor="w", pady=(0, 8))
            lb = tk.Listbox(body, height=12)
            lb.pack(fill="both", expand=True)
            total = 0; t_docs = 0; t_out = 0
            for m in metas:
                slug = (m.get("slug") or "").strip()
                code = m.get("code")
                est = self._estimate_package(slug, code, docs, include_docs, include_outputs)
                t_docs += int(est.get("docs_size", 0)); t_out += int(est.get("outputs_size", 0))
                total += int(est.get("total_size", 0))
                ic_msg = ""
                if require_icons and slug:
                    try:
                        ic = _icons_check_status(slug)
                        if isinstance(ic, tuple):
                            ic_msg = " • Icons: " + ("OK" if bool(ic[0]) else f"{ic[1]}")
                    except Exception:
                        ic_msg = ""
                lb.insert("end", f"{m.get('title') or slug} ({slug}) — Docs: {est['docs_count']} ({self._fmt_size(est['docs_size'])}), Outputs: {est['outputs_count']} ({self._fmt_size(est['outputs_size'])}){ic_msg}")
            tk.Label(body, text=f"Totals — Docs: {self._fmt_size(t_docs)} • Outputs: {self._fmt_size(t_out)} • All: {self._fmt_size(total)}", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(6, 0))
            row = tk.Frame(body); row.pack(fill="x", pady=(10, 0))
            proceed = {"v": False}
            def _go():
                proceed["v"] = True
                try:
                    win.destroy()
                except Exception:
                    pass
            def _cancel():
                proceed["v"] = False
                try:
                    win.destroy()
                except Exception:
                    pass
            tk.Button(row, text="Proceed", command=_go).pack(side="right")
            tk.Button(row, text="Cancel", command=_cancel).pack(side="right", padx=6)
            try:
                win.transient(self); win.grab_set()
            except Exception:
                pass
            try:
                self.wait_window(win)
            except Exception:
                pass
            try:
                _log_event("package_preview_multi", {"count": len(metas), "docs": int(bool(include_docs)), "outputs": int(bool(include_outputs)), "icons_req": int(bool(require_icons)), "total_size": int(total)})
            except Exception:
                pass
            return bool(proceed["v"])
        except Exception:
            return False

    def _finalize_packaging_multi_dialog(self):
        try:
            docs = _packaging_docs_find()
            if not (docs.get("root") and docs.get("tou") and docs.get("quick")):
                messagebox.showinfo("Packaging", "Required docs not present yet (need TOU and Quick Start).")
                return
            win = tk.Toplevel(self)
            win.title("Multi-book Packaging")
            try:
                win.geometry("520x560")
            except Exception:
                pass
            tk.Label(win, text="Select books to package", font=("Segoe UI", 11, "bold")).pack(padx=12, pady=(12, 6), anchor="w")
            # Local toggles for this multi build
            try:
                conf = _read_log()
                d_def = int(conf.get("_pack_include_docs", 1))
                o_def = int(conf.get("_pack_include_outputs", 1))
                i_def = int(conf.get("_pack_require_icons_ok", 0))
            except Exception:
                d_def, o_def, i_def = 1, 1, 0
            opt = tk.Frame(win); opt.pack(fill="x", padx=12, pady=(0, 6))
            # Default for QA gating from saved prefs
            try:
                q_def = int(conf.get("_pack_require_qa_ok", 0))
            except Exception:
                q_def = 0
            d_var = tk.IntVar(value=d_def); o_var = tk.IntVar(value=o_def); i_var = tk.IntVar(value=i_def); q_var = tk.IntVar(value=q_def)
            tk.Checkbutton(opt, text="Include Docs", variable=d_var).pack(side="left")
            tk.Checkbutton(opt, text="Include Outputs", variable=o_var).pack(side="left", padx=8)
            tk.Checkbutton(opt, text="Require Icons OK", variable=i_var).pack(side="left", padx=8)
            tk.Checkbutton(opt, text="Require QA OK", variable=q_var).pack(side="left", padx=8)
            # Sorting/filtering controls
            ctl = tk.Frame(win); ctl.pack(fill="x", padx=12, pady=(0, 4))
            show_ready_var = tk.IntVar(value=0)
            tk.Checkbutton(ctl, text="Show only ready", variable=show_ready_var).pack(side="left")
            tk.Label(ctl, text="Sort:").pack(side="left", padx=(12, 4))
            sort_var = tk.StringVar(value="Title (A→Z)")
            try:
                tk.OptionMenu(ctl, sort_var, "Title (A→Z)", "Ready first", "Outputs first", "Icons first").pack(side="left")
            except Exception:
                tk.Entry(ctl, textvariable=sort_var, width=14).pack(side="left")
            lb = tk.Listbox(win, selectmode="extended", height=16)
            lb.pack(fill="both", expand=True, padx=12, pady=(0, 4))
            books = list(self.books or [])
            # Build per-book preflight stats
            stats = []  # list of dicts: {slug,title,code,out_ok,icons:(ok,msg),out_dir}
            out_ok_count = 0
            ic_ok_count = 0
            # Global docs presence (packaging docs are shared)
            try:
                docs_ok = bool(docs.get("root") and docs.get("tou") and docs.get("quick"))
            except Exception:
                docs_ok = False
            for b in books:
                try:
                    slug = b.get('slug')
                    title = b.get('title') or slug.replace('_', ' ').title()
                    code = b.get('code')
                    odir = self._resolve_output_dir(slug, code)
                    out_ok = bool(odir and odir.exists())
                    if out_ok:
                        out_ok_count += 1
                    ic = None
                    try:
                        ic = _icons_check_status(slug)
                    except Exception:
                        ic = None
                    ic_ok = (isinstance(ic, tuple) and bool(ic[0]))
                    if ic_ok:
                        ic_ok_count += 1
                    stats.append({
                        'slug': slug,
                        'title': title,
                        'code': code,
                        'out_ok': out_ok,
                        'icons': ic,
                        'out_dir': odir,
                        'docs_ok': docs_ok,
                    })
                    # Label with icons: 📦 for outputs ok, ⚠️ otherwise; ✅ icons ok / ⚠️ otherwise
                    pfx_out = '📦' if out_ok else '⚠️'
                    if isinstance(ic, tuple):
                        pfx_ic = '✅' if ic[0] else '⚠️'
                    else:
                        pfx_ic = '❔'
                    pfx_doc = '📄' if docs_ok else '⚠️'
                    lab = f"{pfx_out} {pfx_ic} {pfx_doc}  {title}  ({slug})"
                except Exception:
                    lab = b.get('slug')
                lb.insert("end", lab)
            # Summary row
            sum_row = tk.Frame(win); sum_row.pack(fill="x", padx=12, pady=(4, 6))
            sum_lbl = tk.Label(sum_row, text=f"Summary • Outputs: {out_ok_count}/{len(books)} • Icons OK: {ic_ok_count}/{len(books)} • Docs: {'OK' if docs_ok else 'Missing'}")
            sum_lbl.pack(anchor="w")
            # Ordering and helpers
            order = list(range(len(books)))
            def _is_icons_ok(i):
                ic = stats[i].get('icons')
                return bool(isinstance(ic, tuple) and bool(ic[0]))
            def _is_ready(i):
                try:
                    need_out = bool(o_var.get())
                    need_icons = bool(i_var.get())
                except Exception:
                    need_out = True; need_icons = False
                out_ok = bool(stats[i].get('out_ok'))
                icons_ok = _is_icons_ok(i)
                cond_out = (not need_out) or out_ok
                cond_ic = (not need_icons) or icons_ok
                # Docs are shared; if included and missing, nothing is ready
                try:
                    if bool(d_var.get()) and not docs_ok:
                        return False
                except Exception:
                    pass
                return bool(cond_out and cond_ic)
            def _label_for(i):
                try:
                    st = stats[i]
                    pfx_out = '📦' if st.get('out_ok') else '⚠️'
                    ic = st.get('icons')
                    pfx_ic = '✅' if (isinstance(ic, tuple) and ic[0]) else ('⚠️' if isinstance(ic, tuple) else '❔')
                    pfx_doc = '📄' if docs_ok else '⚠️'
                    return f"{pfx_out} {pfx_ic} {pfx_doc}  {st.get('title')}  ({st.get('slug')})"
                except Exception:
                    return "(book)"
            def _rebuild_list(*_):
                nonlocal order
                # Build candidate indices
                base = list(range(len(books)))
                # Filter
                try:
                    if bool(show_ready_var.get()):
                        base = [i for i in base if _is_ready(i)]
                except Exception:
                    pass
                # Sort
                key = sort_var.get() if isinstance(sort_var.get(), str) else "Title (A→Z)"
                def _key_fn(i):
                    try:
                        if key == "Ready first":
                            return (0 if _is_ready(i) else 1, stats[i].get('title',''))
                        if key == "Outputs first":
                            return (0 if stats[i].get('out_ok') else 1, stats[i].get('title',''))
                        if key == "Icons first":
                            return (0 if _is_icons_ok(i) else 1, stats[i].get('title',''))
                        # Default by title
                        return (stats[i].get('title',''),)
                    except Exception:
                        return (stats[i].get('slug',''),)
                try:
                    base.sort(key=_key_fn)
                except Exception:
                    pass
                order = base
                # Recompute ready count and refresh summary
                try:
                    ready_count = sum(1 for i in range(len(books)) if _is_ready(i))
                    sum_lbl.config(text=f"Summary • Outputs: {out_ok_count}/{len(books)} • Icons OK: {ic_ok_count}/{len(books)} • Docs: {'OK' if docs_ok else 'Missing'} • Ready: {ready_count}/{len(books)}")
                except Exception:
                    pass
                # Rebuild listbox
                try:
                    lb.delete(0, "end")
                    for i in order:
                        lb.insert("end", _label_for(i))
                except Exception:
                    pass
            # Wire controls
            try:
                sort_var.trace_add('write', _rebuild_list)
            except Exception:
                pass
            try:
                show_ready_var.trace_add('write', _rebuild_list)
            except Exception:
                pass
            # Initial list build
            _rebuild_list()
            # Detail panel for selected book
            det = tk.Frame(win); det.pack(fill="x", padx=12, pady=(0, 8))
            det_lbl = tk.Label(det, text="Select a book to view details…", fg="#555")
            det_lbl.pack(anchor="w")
            def _upd_detail(*_):
                try:
                    idxs = list(lb.curselection())
                    if not idxs:
                        det_lbl.config(text="Select a book to view details…")
                        return
                    j = idxs[0]
                    i = order[j]
                    st = stats[i]
                    slug = st.get('slug'); title = st.get('title')
                    out_ok = st.get('out_ok'); odir = st.get('out_dir')
                    ic = st.get('icons')
                    ic_txt = 'unknown'
                    if isinstance(ic, tuple):
                        ic_txt = 'OK' if ic[0] else f"{ic[1]}"
                    out_txt = (str(odir) if (odir and out_ok) else 'missing')
                    try:
                        if docs_ok:
                            tou = docs.get('tou'); quick = docs.get('quick')
                            docs_txt = f"OK ({Path(tou).name if tou else 'TOU'}, {Path(quick).name if quick else 'QuickStart'})"
                        else:
                            docs_txt = 'Missing'
                    except Exception:
                        docs_txt = 'Unknown'
                    det_lbl.config(text=f"{title} ({slug}) • Outputs: {out_txt} • Icons: {ic_txt} • Docs: {docs_txt}")
                except Exception:
                    pass
            try:
                lb.bind('<<ListboxSelect>>', _upd_detail)
            except Exception:
                pass
            row = tk.Frame(win); row.pack(fill="x", padx=12, pady=(0, 10))
            def _sel_all():
                try:
                    lb.select_set(0, "end")
                except Exception:
                    pass
            def _sel_none():
                try:
                    lb.select_clear(0, "end")
                except Exception:
                    pass
            tk.Button(row, text="Select All", command=_sel_all).pack(side="left")
            tk.Button(row, text="Select None", command=_sel_none).pack(side="left", padx=6)
            def _sel_ready():
                try:
                    lb.select_clear(0, "end")
                    for pos, i in enumerate(order):
                        if _is_ready(i):
                            lb.select_set(pos)
                    lb.see(0)
                except Exception:
                    pass
            tk.Button(row, text="Select Ready Only", command=_sel_ready).pack(side="left", padx=6)
            def _run():
                try:
                    idxs = list(lb.curselection())
                except Exception:
                    idxs = []
                if not idxs:
                    messagebox.showinfo("Packaging", "No books selected.")
                    return
                inc_docs = bool(d_var.get()); inc_out = bool(o_var.get()); inc_icons = bool(i_var.get()); inc_qa = bool(q_var.get())
                if not inc_docs and not inc_out:
                    messagebox.showinfo("Packaging", "Select at least one: Include Docs and/or Include Outputs.")
                    return
                # Respect current list order when mapping selections to books
                try:
                    sel_indices = [order[pos] for pos in idxs]
                except Exception:
                    sel_indices = [int(pos) for pos in idxs]
                # Dry-run preview across selected metas
                try:
                    metas = [books[i] for i in sel_indices]
                except Exception:
                    metas = []
                try:
                    if not self._show_multi_pack_preview(metas, docs, inc_docs, inc_out, inc_icons):
                        return
                except Exception:
                    pass
                made = []
                skipped = []
                for i in sel_indices:
                    try:
                        meta = books[i]
                        slug = meta.get("slug")
                        title = meta.get("title")
                        code = meta.get("code")
                        # Optional icons gating per book
                        if inc_icons and slug:
                            ic = _icons_check_status(slug)
                            ic_ok = (isinstance(ic, tuple) and bool(ic[0]))
                            if not ic_ok:
                                try:
                                    r = ic[1] if isinstance(ic, tuple) else "unknown"
                                except Exception:
                                    r = "unknown"
                                skipped.append((slug, r))
                                continue
                        # Optional QA gating per book
                        if inc_qa and slug:
                            ok_qa, reasons = self._qa_acceptance_status(slug, include_outputs=inc_out)
                            if not ok_qa:
                                try:
                                    r = "; ".join([str(x) for x in (reasons or [])]) or "QA not accepted"
                                except Exception:
                                    r = "QA not accepted"
                                skipped.append((slug, r))
                                continue
                        zp = self._build_package_for(slug, title, code, docs, inc_docs, inc_out)
                        if zp:
                            made.append(zp)
                    except Exception:
                        continue
                if not made:
                    if skipped:
                        det = ", ".join([f"{s} ({r})" for s, r in skipped])
                        messagebox.showinfo("Packaging", f"No packages created. Skipped {len(skipped)} due to gating: {det}")
                    else:
                        messagebox.showinfo("Packaging", "No packages created (check outputs/docs).")
                    return
                try:
                    data = _read_log()
                    data["_last_package_zip"] = str(made[-1])
                    try:
                        data["_last_package_time"] = datetime.now().isoformat(timespec="seconds")
                    except Exception:
                        pass
                    data["_pack_include_docs"] = int(inc_docs)
                    data["_pack_include_outputs"] = int(inc_out)
                    data["_pack_require_icons_ok"] = int(inc_icons)
                    data["_pack_require_qa_ok"] = int(inc_qa)
                    # Also persist as last-used toggles for Rebuild (Prev)
                    data["_last_pack_include_docs"] = int(inc_docs)
                    data["_last_pack_include_outputs"] = int(inc_out)
                    data["_last_pack_require_icons_ok"] = int(inc_icons)
                    data["_last_pack_require_qa_ok"] = int(inc_qa)
                    _write_log(data)
                except Exception:
                    pass
                try:
                    self._update_last_package_header_status(schedule=False)
                except Exception:
                    pass
                try:
                    self._open_path(STUDIOFORGE_DIR / "UPLOAD_READY")
                except Exception:
                    pass
                try:
                    if skipped:
                        det = ", ".join([f"{s} ({r})" for s, r in skipped])
                        messagebox.showinfo("Packaging", f"Created {len(made)} package(s). Skipped {len(skipped)} due to gating: {det}")
                    else:
                        messagebox.showinfo("Packaging", f"Created {len(made)} package(s).")
                except Exception:
                    pass
                try:
                    win.destroy()
                except Exception:
                    pass
            tk.Button(win, text="Package Selected", command=_run).pack(padx=12, pady=(0, 12), anchor="e")
        except Exception as e:
            messagebox.showerror("Packaging", str(e))

    def _packaging_docs_status(self):
        try:
            root = STUDIOFORGE_DIR / "TPT_LINE_OF_TRUTH"
            if not root.exists():
                alt = BASE_DIR / "TPT_LINE_OF_TRUTH"
                root = alt if alt.exists() else root
            if not root.exists():
                return False, "Packaging docs root missing (TPT_LINE_OF_TRUTH)"
            patterns = ["*Terms*.*", "*TOU*.*", "*Quick*Start*.*", "*Scarborough*Rope*.*"]
            found = []
            for pat in patterns:
                fp = None
                try:
                    fp = next(root.rglob(pat))
                except StopIteration:
                    fp = None
                except Exception:
                    fp = None
                if fp:
                    found.append(fp.name)
            if not found:
                return True, "Packaging docs root found; add TOU/Quick Start/Rope when ready"
            return True, "Docs present: " + ", ".join(sorted(set(found))[:4])
        except Exception as e:
            return False, f"Docs check error: {e}"

    def _open_cover_config_for(self, slug: str):
        try:
            if not slug:
                messagebox.showinfo("Cover Config", "No book selected.")
                return
            p = THEMES_DIR / slug / "cover_config.json"
            if p.exists():
                self._open_path(p)
            else:
                messagebox.showinfo("Cover Config", f"Not found: {p}")
        except Exception as e:
            messagebox.showerror("Cover Config", str(e))

    def _on_close(self):
        try:
            data = _read_log()
            data["_geometry"] = self.geometry()
            _write_log(data)
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            os._exit(0)

    def _launch_topic_builder(self, topic: str, keywords: str, slug: str, lu_label):
        try:
            if not topic:
                messagebox.showwarning("Enter topic", "Please enter a topic name.")
                return
            script = STUDIOFORGE_DIR / "TOPIC_CONTENT_BUILDER.py"
            if not script.exists():
                messagebox.showerror("Missing file", f"Not found: {script}")
                return
            args = [PYTHON, str(script), "--topic", topic]
            if keywords and keywords.strip():
                args += ["--keywords", keywords.strip()]
            if slug and slug.strip():
                args += ["--slug", slug.strip()]
            ok = _run_in_console_persist(args, STUDIOFORGE_DIR)
            if ok:
                try:
                    _touch_used("topic_builder")
                    lu_label.config(text=f"Last used: {_last_used('topic_builder')}")
                except Exception:
                    pass
        except Exception as e:
            try:
                messagebox.showerror("Topic Builder", str(e))
            except Exception:
                pass

    def _launch_matching(self, slug, title, code, lu_label):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        # Prefer the D: copy of the Accurate generator; fall back to local copy
        d_gen = Path("D:/Seagate/small-wins-automation/Studioforge/Accurate generators/GENERATE_ALL.py")
        gen_all = d_gen if d_gen.exists() else (STUDIOFORGE_DIR / "Accurate generators" / "GENERATE_ALL.py")
        if not gen_all.exists():
            messagebox.showerror("Missing file", f"Not found: {gen_all}")
            return
        pack_code = code or (slug[:3].upper() + "1")
        theme_name = title or slug.replace("_", " ").title()
        # Run only Matching; GENERATE_ALL resolves images folder with fallbacks
        args = [PYTHON, str(gen_all), slug, theme_name, pack_code, "--only", "matching"]
        # Derive repo root from the selected generator path (two levels up)
        try:
            repo_root = gen_all.resolve().parents[2]
        except Exception:
            repo_root = BASE_DIR
        extra_env = {
            "STUDIOFORGE_ROOT": str(repo_root),
            "PYTHONPATH": str(repo_root),
        }
        ok = _run_in_console_env(args, gen_all.parent, extra_env)
        if ok:
            self._remember_last_book(slug)
            _touch_used("matching")
            lu_label.config(text=f"Last used: {_last_used('matching')}")

    def _launch_icon_labeler(self, lu_label):
        # Single instance on 5052: reuse if already running, otherwise start ICON_LABELER.py there.
        port = 5052
        try:
            last = getattr(self, "_last_book_slug", None) or ""
            q = (f"?book={last}" if last else "")
            if _is_server_alive(port):
                url = f"http://127.0.0.1:{port}{q}"
                webbrowser.open(url)
                _touch_used("icon_labeler")
                lu_label.config(text=f"Last used: {_last_used('icon_labeler')} — {url}")
                return
        except Exception:
            pass
        script = STUDIOFORGE_DIR / "ICON_LABELER.py"
        if not script.exists():
            messagebox.showerror("Missing file", f"Not found: {script}")
            return
        ok = _run_in_console([PYTHON, str(script), str(port)], STUDIOFORGE_DIR)
        if ok:
            try:
                last = getattr(self, "_last_book_slug", None) or ""
                q = (f"?book={last}" if last else "")
            except Exception:
                q = ""
            url = f"http://127.0.0.1:{port}{q}"
            _open_icon_labeler_later(url=url, ping_path="/api/ping")
            _touch_used("icon_labeler")
            lu_label.config(text=f"Last used: {_last_used('icon_labeler')} — {url}")

    def _launch_listing(self, slug, lu_label):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        script = STUDIOFORGE_DIR / "LISTING_GENERATOR.py"
        if not script.exists():
            messagebox.showerror("Missing file", f"Not found: {script}")
            return
        args = [PYTHON, str(script), "--book", slug, "--all"]
        ok = _run_in_console(args, STUDIOFORGE_DIR)
        if ok:
            self._remember_last_book(slug)
            _touch_used("listing_generator")
            lu_label.config(text=f"Last used: {_last_used('listing_generator')}")

    def _launch_code_words(self, slug, title, code, lu_label):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        script = _resolved_generator_path("code_words")
        if not script or not Path(script).exists():
            messagebox.showerror("Missing file", f"Not found: {script}")
            return
        pack_base = (code or slug[:3].upper()).strip()
        pack_code = f"{pack_base}-CW"
        disp_title = title or slug.replace("_", " ").title()
        args = [PYTHON, str(script), "--slug", slug, "--title", disp_title, "--pack", pack_code]
        extra_env = {"STUDIOFORGE_ROOT": str(BASE_DIR), "PYTHONPATH": str(BASE_DIR)}
        ok = _run_in_console_env(args, BASE_DIR, extra_env)
        if ok:
            self._remember_last_book(slug)
            _touch_used("code_words")
            lu_label.config(text=f"Last used: {_last_used('code_words')}")

    def _launch_book_insert_strips(self, slug, title, code, lu_label):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        script = _resolved_generator_path("book_insert_strips")
        if not script or not Path(script).exists():
            messagebox.showerror("Missing file", f"Not found: {script}")
            return
        pack_base = (code or slug[:3].upper()).strip()
        pack_code = f"{pack_base}-BIS"
        disp_title = title or slug.replace("_", " ").title()
        args = [PYTHON, str(script), "--slug", slug, "--title", disp_title, "--pack", pack_code]
        extra_env = {"STUDIOFORGE_ROOT": str(BASE_DIR), "PYTHONPATH": str(BASE_DIR)}
        ok = _run_in_console_env(args, BASE_DIR, extra_env)
        if ok:
            self._remember_last_book(slug)
            _touch_used("book_insert_strips")
            lu_label.config(text=f"Last used: {_last_used('book_insert_strips')}")


def main():
    app = ToolLauncher()
    # Bring window to front on launch
    try:
        app.lift()
        app.attributes("-topmost", True)
        app.after(300, lambda: app.attributes("-topmost", False))
        app.focus_force()
    except Exception:
        pass
    app.mainloop()


if __name__ == "__main__":
    main()
