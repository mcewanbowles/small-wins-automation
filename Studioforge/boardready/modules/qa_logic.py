from __future__ import annotations

import json
import os
import re
import shutil
import threading
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Fix 1 — Paths: Use D:\Seagate\small-wins-automation as the base
BASE = Path(r"D:\Seagate\small-wins-automation")
ASSETS_DIR = BASE / "assets"
VOCAB_DIR = BASE / "vocab"
QA_DATA_DIR = BASE / "Studioforge" / "boardready" / "data"

QA_LOG_PATH = QA_DATA_DIR / "qa_review_log.json"
QA_PROGRESS_PATH = QA_DATA_DIR / "qa_progress.json"
QA_BANLIST_PATH = QA_DATA_DIR / "qa_banlist.json"

AMBIGUOUS_WORDS = {
    "fly", "fall", "bat", "wave", "bark", "light", "bear", "saw",
    "duck", "spring", "rock", "cold", "left"
}


def _ensure_data_dir() -> None:
    QA_DATA_DIR.mkdir(parents=True, exist_ok=True)


_VOCAB_CACHE: Dict[str, object] = {"ts": 0.0, "data": None}
_VOCAB_TTL_S = 60.0


def load_vocab() -> Dict:
    """
    Load the unified vocab mapping of all books.

    Prefer a global file at BASE/vocab/book_vocab.json if present; otherwise
    aggregate from per-theme book_vocab.json files under assets/themes/*.
    Returns a dict mapping book_key (slug) -> book vocab dict.
    """
    import time as _t
    now = _t.time()
    cached = _VOCAB_CACHE.get("data")
    if isinstance(cached, dict) and (now - float(_VOCAB_CACHE.get("ts") or 0.0)) < _VOCAB_TTL_S:
        return cached
    vocab = _load_vocab_uncached()
    _VOCAB_CACHE["ts"] = now
    _VOCAB_CACHE["data"] = vocab
    return vocab


def _load_vocab_uncached() -> Dict:
    # Load global vocab if present
    p = VOCAB_DIR / "book_vocab.json"
    vocab: Dict[str, Dict] = {}
    try:
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                obj = json.load(f)
                if isinstance(obj, dict) and obj:
                    vocab.update(obj)
    except Exception:
        pass

    # Merge in any themes not represented in global vocab
    themes_dir = ASSETS_DIR / "themes"
    if not themes_dir.exists():
        return vocab
    for theme in sorted(themes_dir.iterdir()):
        try:
            if not theme.is_dir():
                continue
            slug = theme.name
            # Skip internal or system folders
            if slug.startswith('.') or slug.startswith('_'):
                continue
            tp = theme / "book_vocab.json"
            if not tp.exists():
                alt = theme / "config" / "book_vocab.json"
                tp = alt if alt.exists() else tp
            if not tp.exists():
                continue
        except OSError:
            # Unreadable theme folder/file (e.g. disk CRC error): skip it, keep the rest
            continue
        try:
            data = json.loads(tp.read_text(encoding="utf-8-sig"))
            if isinstance(data, dict):
                data.setdefault("title", slug.replace("_", " ").title())
                if slug not in vocab:
                    vocab[slug] = data
                else:
                    # Ensure a title is present in the merged entry
                    if not str(vocab.get(slug, {}).get("title", "")).strip():
                        vocab[slug]["title"] = data.get("title")
        except Exception:
            continue
    return vocab


def _theme_book_vocab_path(book_key: str) -> Path:
    p = ASSETS_DIR / "themes" / book_key / "book_vocab.json"
    try:
        if p.exists():
            return p
    except OSError:
        return p
    return ASSETS_DIR / "themes" / book_key / "config" / "book_vocab.json"


def load_theme_vocab(book_key: str) -> Dict:
    p = _theme_book_vocab_path(book_key)
    try:
        if not p.exists():
            return {}
        with p.open("r", encoding="utf-8-sig") as f:
            return json.load(f)
    except OSError:
        return {}


def get_all_book_keys() -> List[str]:
    vocab = load_vocab()
    slugs = set(vocab.keys())
    themes_dir = ASSETS_DIR / "themes"
    if themes_dir.exists():
        for theme in sorted(themes_dir.iterdir()):
            try:
                if not theme.is_dir():
                    continue
                slug = theme.name
                if slug.startswith('.') or slug.startswith('_'):
                    continue
                # Include if it has a vocab file OR at least one accepted asset subfolder
                has_vocab = (theme / "book_vocab.json").exists() or (theme / "config" / "book_vocab.json").exists()
                # Accept real_images to match legacy Icon Labeler discovery; keep scope minimal (no png_raw for now)
                has_assets = any((theme / sub).exists() for sub in ("activity_images", "icons", "real_images", "aac_boards"))
                if has_vocab or has_assets:
                    slugs.add(slug)
            except OSError:
                continue
    return sorted(slugs)


def get_book_context(book_key: str, vocab: Optional[Dict] = None) -> str:
    if vocab is None:
        vocab = load_vocab()
    book = vocab.get(book_key, {})
    notes = book.get("notes", "")
    if notes:
        return notes
    hero = book.get("hero", {})
    if hero.get("description"):
        return f"{book.get('title', book_key)} — hero: {hero.get('name','')}. {hero['description']}"
    return book.get("title", book_key.replace("_", " ").title())


_QA_LOG_CACHE: Tuple[float, Dict] = (0.0, {})
_QA_LOG_LOCK = threading.Lock()


def load_qa_log() -> Dict:
    global _QA_LOG_CACHE
    _ensure_data_dir()
    if not QA_LOG_PATH.exists():
        return {}
    try:
        mtime = QA_LOG_PATH.stat().st_mtime
    except OSError:
        mtime = 0.0
    with _QA_LOG_LOCK:
        cached_mtime, cached_data = _QA_LOG_CACHE
        if cached_mtime == mtime and mtime > 0:
            return cached_data
    with QA_LOG_PATH.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    with _QA_LOG_LOCK:
        _QA_LOG_CACHE = (mtime, data)
    return data


def save_qa_log(data: Dict) -> None:
    global _QA_LOG_CACHE
    _ensure_data_dir()
    with QA_LOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    try:
        mtime = QA_LOG_PATH.stat().st_mtime
        with _QA_LOG_LOCK:
            _QA_LOG_CACHE = (mtime, data)
    except OSError:
        pass


def _theme_icons_dir(book_key: str) -> Path:
    return ASSETS_DIR / "themes" / book_key / "activity_images"


def _sanitized_png_name(word: str) -> str:
    base = _norm(str(word)).replace(" ", "_")
    return f"{base}.png" if base else "icon.png"


def load_progress() -> Dict:
    _ensure_data_dir()
    if not QA_PROGRESS_PATH.exists():
        return {}
    with QA_PROGRESS_PATH.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save_progress(data: Dict) -> None:
    _ensure_data_dir()
    with QA_PROGRESS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_banlist() -> List[str]:
    _ensure_data_dir()
    try:
        if QA_BANLIST_PATH.exists():
            with QA_BANLIST_PATH.open("r", encoding="utf-8") as f:
                obj = json.load(f)
                if isinstance(obj, list):
                    return [str(x) for x in obj]
    except Exception:
        pass
    return []


def save_banlist(items: List[str]) -> None:
    _ensure_data_dir()
    try:
        with QA_BANLIST_PATH.open("w", encoding="utf-8") as f:
            json.dump(list(items), f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def add_to_banlist(path: str) -> None:
    try:
        p = Path(path).resolve()
    except Exception:
        p = Path(path)
    cur = load_banlist()
    s = set(cur)
    sp = str(p)
    if sp not in s:
        s.add(sp)
    save_banlist(sorted(s))


def _banned_set() -> set:
    try:
        return {os.path.normcase(str(x)) for x in load_banlist()}
    except Exception:
        return set()


def _is_banned(path: Path, ban: Optional[set] = None) -> bool:
    try:
        if ban is None:
            ban = _banned_set()
        if not ban:
            return False
        if os.path.normcase(str(path)) in ban:
            return True
        return os.path.normcase(str(path.resolve())) in ban
    except Exception:
        return False


# --- Icon discovery helpers ---

def _norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


_ICON_LABEL_INDEX_CACHE: Dict[str, object] = {"mtime": None, "labels": {}}


def _icon_label_index() -> Dict[str, str]:
    path = ASSETS_DIR / "symbols" / "png" / "Alpha" / "icon_labels.json"
    try:
        mtime = path.stat().st_mtime if path.exists() else None
        if _ICON_LABEL_INDEX_CACHE.get("mtime") == mtime:
            return _ICON_LABEL_INDEX_CACHE.get("labels", {})  # type: ignore[return-value]
        raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        labels: Dict[str, str] = {}
        if isinstance(raw, dict):
            for key, value in raw.items():
                label = str(value or "").strip()
                if not label:
                    continue
                candidate = Path(str(key))
                labels[str(candidate)] = label
                try:
                    labels[str(candidate.resolve())] = label
                except Exception:
                    pass
        _ICON_LABEL_INDEX_CACHE.update({"mtime": mtime, "labels": labels})
        return labels
    except Exception:
        return {}


def _filename_label(p: Path) -> str:
    label = _icon_label_index().get(str(p))
    return _norm(label or p.stem)


def _score_label(label: str, term: str) -> float:
    label_n = _norm(label)
    term_n = _norm(term)
    if not label_n or not term_n:
        return 0.0
    score = 0.0
    if label_n == term_n:
        score += 0.7
    if label_n.startswith(term_n):
        score += 0.2
    if term_n in label_n:
        score += 0.2
    score += 0.6 * SequenceMatcher(None, label_n, term_n).ratio()
    # Cap at 1.0
    return min(score, 1.0)


def _candidate_png_dirs(book_key: Optional[str] = None) -> List[Path]:
    dirs: List[Path] = []
    if book_key:
        bk = ASSETS_DIR / "themes" / book_key
        # Include a broader set of theme subfolders
        for sub in ("activity_images", "icons", "icons_colored", "real_images", "png_raw"):
            d = bk / sub
            if d.exists():
                dirs.append(d)
    # Global/shared libraries (if present) under current assets tree
    for rel in [
        ASSETS_DIR / "symbols" / "png",
        ASSETS_DIR / "global",
        ASSETS_DIR / "png_raw",
    ]:
        if rel.exists():
            dirs.append(rel)
    # Legacy Studioforge/assets mirrors retained for back-compat
    legacy_root = BASE / "Studioforge" / "assets"
    for rel in [
        legacy_root / "symbols" / "png",
        legacy_root / "global",
        legacy_root / "png_raw",
    ]:
        if rel.exists():
            dirs.append(rel)
    # Also scan first-level children under assets for common structures (e.g., "Asking for Help/png_raw")
    try:
        for child in ASSETS_DIR.iterdir():
            if not child.is_dir():
                continue
            for sub in ("png_raw", "icons", "icons_colored", "real_images"):
                p = child / sub
                if p.exists():
                    dirs.append(p)
            sp = child / "symbols" / "png"
            if sp.exists():
                dirs.append(sp)
    except Exception:
        pass
    # Deduplicate while preserving order
    uniq: List[Path] = []
    seen = set()
    for d in dirs:
        try:
            dp = d.resolve()
        except Exception:
            dp = d
        if dp not in seen:
            seen.add(dp)
            uniq.append(d)
    return uniq


_PNG_DIR_CACHE: Dict[str, Tuple[float, List[Path]]] = {}
_PNG_DIR_LOCK = threading.Lock()


def _walk_pngs(root: Path) -> List[Path]:
    out: List[Path] = []
    stack = [str(root)]
    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                for e in it:
                    try:
                        if e.is_dir(follow_symlinks=False):
                            stack.append(e.path)
                        elif e.name.lower().endswith(".png") and e.is_file(follow_symlinks=False):
                            out.append(Path(e.path))
                    except OSError:
                        continue
        except OSError:
            continue
    return out


def _iter_pngs_from_dirs(dirs: List[Path]) -> List[Path]:
    results: List[Path] = []
    for d in dirs:
        if d.is_file() and d.suffix.lower() == ".png":
            results.append(d)
            continue
        if not d.exists():
            continue
        key = str(d.resolve()) if d.exists() else str(d)
        try:
            mtime = d.stat().st_mtime
        except OSError:
            mtime = 0.0
        cached = _PNG_DIR_CACHE.get(key)
        if cached and cached[0] == mtime:
            results.extend(cached[1])
            continue
        with _PNG_DIR_LOCK:
            cached = _PNG_DIR_CACHE.get(key)
            if cached and cached[0] == mtime:
                found = cached[1]
            else:
                found = _walk_pngs(d)
                _PNG_DIR_CACHE[key] = (mtime, found)
        results.extend(found)
    return results


def _library_paths(book_key: Optional[str] = None) -> List[Path]:
    dirs = _candidate_png_dirs(book_key)
    if not dirs:
        dirs = _candidate_png_dirs(None)
    return _iter_pngs_from_dirs(dirs)


def _build_label_index(paths: List[Path]) -> Dict[str, Path]:
    index: Dict[str, Path] = {}
    ban = _banned_set()
    for p in paths:
        try:
            lab = _filename_label(p)
            if not lab or lab in index:
                continue
            try:
                if _is_banned(p, ban):
                    continue
            except Exception:
                pass
            index[lab] = p
        except Exception:
            continue
    return index


def search_png_library(term: str, book_key: Optional[str] = None, top_k: int = 5,
                       paths: Optional[List[Path]] = None) -> List[Dict]:
    if paths is None:
        paths = _library_paths(book_key)
    ban = _banned_set()
    scored: List[Tuple[float, Path]] = []
    for p in paths:
        try:
            if _is_banned(p, ban):
                continue
        except Exception:
            pass
        label = _filename_label(p)
        score = _score_label(label, term)
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda t: t[0], reverse=True)
    out = []
    for score, p in scored[:top_k]:
        out.append({
            "label": p.stem,
            "path": str(p),
            "score": round(float(score), 4),
        })
    return out


def _required_words_for_book(book_key: str, include_core: bool = False) -> List[str]:
    words: List[str] = []
    tv = load_theme_vocab(book_key)
    for key in ("fringe_12", "fringe_11", "activity_images", "aac_extras"):
        vals = tv.get(key)
        if isinstance(vals, list):
            words.extend([str(v) for v in vals])
    if include_core:
        core_path = ASSETS_DIR / "Core Vocab to use" / "aac_core_vocab.json"
        if core_path.exists():
            with core_path.open("r", encoding="utf-8") as f:
                core = json.load(f)
            for row in core.get("fixed_left_cols", []):
                for w in row.get("words", []):
                    words.append(w)
            for w in core.get("fixed_right_row6", []):
                words.append(w)
    # If theme vocab didn't provide any words, derive from filesystem assets
    if not words:
        theme_dir = ASSETS_DIR / "themes" / book_key
        stems: List[str] = []
        for sub in ("activity_images", "icons"):
            d = theme_dir / sub
            if not d.exists():
                continue
            for p in d.rglob("*.png"):
                try:
                    lab = _filename_label(p)
                    if lab:
                        stems.append(lab)
                except Exception:
                    continue
        # keep order and limit to a reasonable number
        words = stems[:200]

    # De-dup while preserving order
    seen = set()
    out = []
    for w in words:
        wn = _norm(str(w))
        if wn and wn not in seen:
            seen.add(wn)
            out.append(w)
    return out


@dataclass
class IconItem:
    word: str
    current_path: Optional[str]
    is_core: bool
    is_ambiguous: bool


def _resolve_icon_path_for_word(book_key: str, word: str,
                                paths: Optional[List[Path]] = None,
                                index: Optional[Dict[str, Path]] = None,
                                tv: Optional[Dict] = None) -> Optional[str]:
    # 1) Per-book directories in fallback order (shared index when supplied)
    if paths is None:
        paths = _library_paths(book_key)
    if index is None:
        index = _build_label_index(paths)
    hit = index.get(_norm(word))
    if hit is not None:
        return str(hit)

    # 2) Use theme-specific search terms to broaden
    if tv is None:
        tv = load_theme_vocab(book_key)
    st = None
    if isinstance(tv.get("icon_search_terms"), dict):
        st = tv["icon_search_terms"].get(word)

    # Normalize st which may be a string or a list of strings
    terms_to_try: List[str] = []
    if isinstance(st, list):
        for x in st:
            xs = str(x).strip()
            if xs:
                terms_to_try.append(xs)
    elif isinstance(st, str) and st.strip():
        terms_to_try.append(st.strip())
    # Always try the literal word as a fallback
    if word and str(word).strip():
        terms_to_try.append(str(word).strip())

    # 3) Global search across library using the best of the provided terms
    best: Optional[Dict] = None
    for t in terms_to_try:
        try:
            cand = search_png_library(t, book_key=book_key, top_k=1, paths=paths)
        except Exception:
            cand = []
        if cand:
            if not best or float(cand[0].get("score", 0.0)) > float(best.get("score", 0.0)):
                best = cand[0]
    if best:
        return best["path"]
    return None


def get_icons_for_book(book_key: str, include_core: bool = False, include_context: bool = True,
                       include_ambiguous_flags: bool = True) -> List[Dict]:
    words = _required_words_for_book(book_key, include_core=include_core)
    tv = load_theme_vocab(book_key)
    amb_list = set()
    if include_ambiguous_flags:
        # Theme-specific ambiguous words
        for a in tv.get("ambiguous", []) if isinstance(tv.get("ambiguous"), list) else []:
            w = str(a.get("word", "")).strip().lower()
            if w:
                amb_list.add(w)
        amb_list.update(AMBIGUOUS_WORDS)

    # Load any prior decisions
    qa_log = load_qa_log()
    prior = qa_log.get(book_key, {}).get("words", {})

    # Scan the library once for this book and reuse for every word
    paths = _library_paths(book_key)
    index = _build_label_index(paths)
    core_only = set(_required_words_for_book(book_key, include_core=True)) - set(_required_words_for_book(book_key, include_core=False))

    items: List[Dict] = []
    for w in words:
        entry = prior.get(w, {})
        entry_path = entry.get("path") if isinstance(entry, dict) else None
        entry_path_banned = bool(entry_path and _is_banned(Path(str(entry_path))))
        if entry_path_banned:
            entry_path = None
        path = entry_path or _resolve_icon_path_for_word(book_key, w, paths=paths, index=index, tv=tv)
        is_core = w in core_only
        is_amb = (w.lower() in amb_list) if include_ambiguous_flags else False
        status = str(entry.get("status", "")).strip().lower() if isinstance(entry, dict) else ""
        if entry_path_banned or not status:
            status = "auto" if path else "missing"
        item = {
            "word": w,
            "current_path": path,
            "status": status,
            "target_label": str(entry.get("target_label", "")) if isinstance(entry, dict) else "",
            "excluded": bool(entry.get("exclude_activities")) if isinstance(entry, dict) else False,
            "is_core": bool(is_core),
            "is_ambiguous": bool(is_amb),
        }
        items.append(item)

    if include_context:
        vocab = load_vocab()
        ctx = get_book_context(book_key, vocab)
        for it in items:
            it["book_context"] = ctx
    return items


def save_decision(book_key: str, word: str, decision: str, replacement_path: Optional[str] = None) -> None:
    decision = decision.lower().strip()
    qa = load_qa_log()
    b = qa.setdefault(book_key, {"words": {}, "completed": False})
    w = b["words"].setdefault(word, {})
    w["status"] = "replaced" if (decision == "wrong" and replacement_path) else decision
    if replacement_path is not None:
        w["path"] = replacement_path
    w["updated_at"] = datetime.utcnow().isoformat() + "Z"
    save_qa_log(qa)


def mark_book_complete(book_key: str) -> None:
    qa = load_qa_log()
    b = qa.setdefault(book_key, {"words": {}, "completed": False})
    b["completed"] = True
    b["completed_at"] = datetime.utcnow().isoformat() + "Z"
    save_qa_log(qa)


def get_missing_icons(book_key: str, include_core: bool = False) -> List[str]:
    items = get_icons_for_book(book_key, include_core=include_core, include_context=False)
    missing: List[str] = []
    qa = load_qa_log()
    prior = qa.get(book_key, {}).get("words", {})
    for it in items:
        w = it["word"]
        status = prior.get(w, {}).get("status", "")
        if not it["current_path"] or status == "missing":
            missing.append(w)
    return missing


def write_missing_icons_file(book_key: str) -> Path:
    _ensure_data_dir()
    missing = get_missing_icons(book_key, include_core=False)
    tv = load_theme_vocab(book_key)
    ts_map = tv.get("icon_search_terms", {}) if isinstance(tv.get("icon_search_terms"), dict) else {}
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = QA_DATA_DIR / f"missing_icons_{book_key}_{ts}.csv"
    lines = ["word,search_term"]
    for w in missing:
        raw = ts_map.get(w, w)
        # If a list of terms, join with a pipe for readability/export
        term = " | ".join(str(x) for x in raw) if isinstance(raw, list) else str(raw)
        # escape commas by quoting if needed
        if "," in term or "," in w:
            lines.append(f'"{w}","{term}"')
        else:
            lines.append(f"{w},{term}")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def get_qa_report() -> Dict:
    qa = load_qa_log()
    report = {"books": {}, "summary": {}}
    total_books = 0
    completed_books = 0
    total_words = 0
    decided = 0
    replaced = 0
    missing = 0

    for bk, data in qa.items():
        words = data.get("words", {})
        total_books += 1
        if data.get("completed"):
            completed_books += 1
        book_stats = {"total": len(words), "keep": 0, "skip": 0, "missing": 0, "replaced": 0}
        for w, info in words.items():
            total_words += 1
            st = info.get("status")
            if st in ("keep", "kept"):
                decided += 1
                book_stats["keep"] += 1
            elif st == "skip":
                decided += 1
                book_stats["skip"] += 1
            elif st == "missing":
                decided += 1
                missing += 1
                book_stats["missing"] += 1
            elif st == "replaced":
                decided += 1
                replaced += 1
                book_stats["replaced"] += 1
        report["books"][bk] = book_stats

    report["summary"] = {
        "total_books": total_books,
        "completed_books": completed_books,
        "total_words": total_words,
        "decided": decided,
        "replaced": replaced,
        "missing": missing,
    }
    return report


def apply_replacements_for_book(book_key: str) -> Dict[str, int]:
    qa = load_qa_log()
    book = qa.get(book_key, {})
    words = book.get("words", {})
    dest_dir = _theme_icons_dir(book_key)
    dest_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    updated = 0
    for w, info in words.items():
        if info.get("status") != "replaced":
            continue
        src = Path(str(info.get("path", "")))
        if not src.exists():
            continue
        dst = dest_dir / _sanitized_png_name(w)
        try:
            if not dst.exists() or src.resolve() != dst.resolve():
                shutil.copy2(src, dst)
                copied += 1
            info["path"] = str(dst)
            updated += 1
        except Exception:
            continue

    if updated:
        save_qa_log(qa)

    return {"copied": copied, "updated": updated}
