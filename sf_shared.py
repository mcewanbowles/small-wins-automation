# -*- coding: utf-8 -*-
"""Shared utilities and state management for StudioForge.

Extracted from studioforge_app.py to reduce the monolith.
Contains: project paths, JSON I/O, book state, caching, session-state keys,
icon decision logic, and library scanning — all pure logic with no Streamlit UI.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from PIL import Image

try:
    from Studioforge.boardready.modules import qa_logic as icon_qa_logic
except Exception:
    icon_qa_logic = None


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

def project_root() -> Path:
    return Path(__file__).resolve().parent


def themes_root_candidates() -> list[Path]:
    root = project_root()
    cands: list[Path] = []
    env = os.environ.get("SF_THEMES_ROOT", "").strip()
    if env:
        p = Path(env)
        if p.exists():
            cands.append(p)
    p = root / "assets" / "themes"
    if p.exists():
        cands.append(p)
    p = root / "production" / "final_products"
    if p.exists():
        cands.append(p)
    return cands


_book_dir_cache: dict[str, Path | None] = {}


def find_book_dir(slug: str) -> Path | None:
    if slug in _book_dir_cache:
        return _book_dir_cache[slug]
    for base in themes_root_candidates():
        d = base / slug
        if d.exists():
            _book_dir_cache[slug] = d
            return d
    _book_dir_cache[slug] = None
    return None


def project_profile_path(slug: str) -> Path | None:
    d = find_book_dir(slug)
    return (d / "config" / "project_profile.json") if d else None


def book_state_path(slug: str) -> Path | None:
    d = find_book_dir(slug)
    return (d / "config" / "book_state.json") if d else None


def images_dir_for_book(slug: str) -> Path | None:
    d = find_book_dir(slug)
    if d is None:
        return None
    ai = d / "activity_images"
    ai.mkdir(parents=True, exist_ok=True)
    return ai


def output_dir_for_book(slug: str) -> Path | None:
    d = find_book_dir(slug)
    return (d / "OUTPUT") if d else None


def symbols_root() -> Path:
    env = os.environ.get("SF_SYMBOLS_ROOT", "").strip()
    if env and Path(env).exists():
        return Path(env)
    expanded = project_root() / "assets" / "symbols" / "png"
    if expanded.exists():
        return expanded
    return project_root() / "assets" / "symbols"


# ---------------------------------------------------------------------------
# JSON I/O
# ---------------------------------------------------------------------------

def _read_json_safe(p: Path, default: Any) -> Any:
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


_book_state_mem_cache: dict[str, tuple[float, dict]] = {}


def read_book_state(slug: str) -> dict:
    p = book_state_path(slug)
    if p is None:
        return {}
    try:
        mtime = p.stat().st_mtime
    except Exception:
        mtime = 0
    cached = _book_state_mem_cache.get(slug)
    if cached and cached[0] == mtime:
        return cached[1]
    data = _read_json_safe(p, default={})
    if not isinstance(data, dict):
        data = {}
    _book_state_mem_cache[slug] = (mtime, data)
    return data


def write_book_state(slug: str, state: dict, toast_ok: bool = False) -> None:
    p = book_state_path(slug)
    if p is None:
        return
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            _book_state_mem_cache[slug] = (p.stat().st_mtime, state)
        except Exception:
            pass
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Session-state keys
# ---------------------------------------------------------------------------

def get_kit_key(slug: str) -> str:
    return f"sf_kit_{slug}"


def get_hero_key(slug: str) -> str:
    return f"sf_hero_{slug}"


def vocab_state_key(slug: str) -> str:
    return f"sf_vocab_{slug}"


def qa_state_key(slug: str) -> str:
    return f"sf_qa_{slug}"


# ---------------------------------------------------------------------------
# Icon library scanning (cached)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=600, show_spinner=False)
def _cached_library_pngs(_root_str: str) -> list[str]:
    root = Path(_root_str)
    return [str(p) for p in root.rglob("*.png")]


def library_png_paths() -> list[Path]:
    return [Path(p) for p in _cached_library_pngs(str(symbols_root()))]


def clear_library_png_cache() -> None:
    _cached_library_pngs.clear()


# ---------------------------------------------------------------------------
# Name utilities
# ---------------------------------------------------------------------------

def sanitise_symbol_name(raw: str) -> str:
    s = str(raw or "").strip().lower()
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def decode_slug(slug: str) -> str:
    s = str(slug or "").replace("_", " ").strip()
    return s.title() if s else ""


def _tokenize(s: str) -> str:
    s = str(s or "").lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


# ---------------------------------------------------------------------------
# Icon decisions
# ---------------------------------------------------------------------------

_accepted_icon_cache: dict[str, dict[str, Path | None]] = {}


def icon_word_decision(slug: str, word: str) -> dict:
    state = read_book_state(slug)
    stored = (state.get("icon_decisions") or {}).get(word, {})
    if icon_qa_logic is not None:
        try:
            qa = icon_qa_logic.load_qa_log()
            qa_entry = (qa.get(slug) or {}).get(word) if isinstance(qa, dict) else None
            if isinstance(qa_entry, dict):
                stored = {**stored, **qa_entry}
        except Exception:
            pass
    return stored


def accepted_icon_for_word(slug: str, word: str) -> Path | None:
    book_cache = _accepted_icon_cache.get(slug)
    if book_cache is not None and word in book_cache:
        return book_cache[word]
    decision = icon_word_decision(slug, word)
    filename = str(decision.get("filename") or "").strip()
    base = images_dir_for_book(slug)
    if filename and base and (base / filename).is_file():
        result = base / filename
        _accepted_icon_cache.setdefault(slug, {})[word] = result
        return result
    source_path = str(decision.get("source_path") or "").strip()
    if str(decision.get("status") or "").lower() == "approved" and source_path and Path(source_path).is_file():
        result = Path(source_path)
        _accepted_icon_cache.setdefault(slug, {})[word] = result
        return result
    _accepted_icon_cache.setdefault(slug, {})[word] = None
    return None


def clear_accepted_icon_cache(slug: str | None = None) -> None:
    if slug:
        _accepted_icon_cache.pop(slug, None)
    else:
        _accepted_icon_cache.clear()


def set_icon_word_status(slug: str, word: str, status: str) -> None:
    state = read_book_state(slug)
    decisions = state.setdefault("icon_decisions", {})
    current = decisions.get(word, {}) if isinstance(decisions.get(word), dict) else {}
    decisions[word] = {
        **current,
        "status": status,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_book_state(slug, state)
    clear_accepted_icon_cache(slug)
    clear_icon_review_summary_cache(slug)
    if icon_qa_logic is not None:
        try:
            mapped = "skip" if status == "skipped" else status
            icon_qa_logic.save_decision(slug, word, mapped)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Icon review summary (cached per render)
# ---------------------------------------------------------------------------

_icon_review_summary_cache: dict[str, dict] = {}


def clear_icon_review_summary_cache(slug: str | None = None) -> None:
    if slug:
        _icon_review_summary_cache.pop(slug, None)
    else:
        _icon_review_summary_cache.clear()


# ---------------------------------------------------------------------------
# Workflow gate cache
# ---------------------------------------------------------------------------

_workflow_gate_cache: dict[str, dict] = {}


def clear_workflow_gate_cache(slug: str | None = None) -> None:
    if slug:
        _workflow_gate_cache.pop(slug, None)
    else:
        _workflow_gate_cache.clear()


# ---------------------------------------------------------------------------
# Vocabulary cache
# ---------------------------------------------------------------------------

_vocab_source_cache: dict[str, tuple[str | None, dict]] = {}


def clear_vocab_source_cache(slug: str | None = None) -> None:
    if slug:
        _vocab_source_cache.pop(slug, None)
    else:
        _vocab_source_cache.clear()


_book_vocab_cache: dict[str, dict | None] = {}


def clear_book_vocab_cache(slug: str | None = None) -> None:
    if slug:
        _book_vocab_cache.pop(slug, None)
    else:
        _book_vocab_cache.clear()


# ---------------------------------------------------------------------------
# Overwrite-safe save
# ---------------------------------------------------------------------------

def save_icon_to_library(source: Path, label: str, overwrite: bool = False) -> tuple[bool, str, Path | None]:
    """Save an icon to the shared symbol library with overwrite protection.
    Returns (success, message, destination_path).
    """
    stem = sanitise_symbol_name(label)
    if not stem:
        return False, "Enter a valid icon label.", None
    lib = symbols_root() / f"{stem}.png"
    if lib.exists() and not overwrite:
        return False, f"An icon named '{stem}' already exists in the library. Enable 'Overwrite' to replace it.", lib
    try:
        lib.parent.mkdir(parents=True, exist_ok=True)
        img = Image.open(str(source)).convert("RGBA")
        img.save(str(lib), "PNG")
        return True, f"Saved '{stem}' to the library.", lib
    except Exception as e:
        return False, f"Could not save: {e}", None


def save_uploaded_icon_to_library(uploaded_file, label: str, overwrite: bool = False) -> tuple[bool, str, Path | None]:
    """Save a Streamlit UploadedFile to the shared symbol library with overwrite protection."""
    import io
    stem = sanitise_symbol_name(label)
    if not stem:
        return False, "Enter a valid icon label.", None
    lib = symbols_root() / f"{stem}.png"
    if lib.exists() and not overwrite:
        return False, f"An icon named '{stem}' already exists in the library. Enable 'Overwrite' to replace it.", lib
    try:
        lib.parent.mkdir(parents=True, exist_ok=True)
        img = Image.open(io.BytesIO(uploaded_file.getvalue())).convert("RGBA")
        img.save(str(lib), "PNG")
        return True, f"Saved '{stem}' to the library.", lib
    except Exception as e:
        return False, f"Could not save: {e}", None
