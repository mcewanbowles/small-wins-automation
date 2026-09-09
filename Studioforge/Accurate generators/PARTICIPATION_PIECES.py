"""
Participation Pieces — Sentence Builder Module (v1)
Implements WINDSURF_BRIEF_SENTENCE_BUILDER_AAC.md as a module inside Participation Pieces.

Scope v1 (per brief):
- 3 levels: Supported (L1), Developing (L2), Independent (L3)
- For each level, build a small set of pages for one representative sentence:
  1) Word/icon tile sheet (cut-apart, icon + label)
  2) Blank base strip (with velcro-dot placeholders)
  3) Answer key page (teacher-facing)
  4) Cut/paste worksheet — icons+words
  5) Cut/paste worksheet — errorless (icons+words + printed guide order)

Sentences are sourced from assets/themes/{slug}/book_vocab.json
Prefer the field 'adapted_book_sentences' (list[str]).

Icons are resolved from two sources in order:
1) Book's locked icon set via tools.icon_resolver (for book fringe words)
2) Global AAC symbol bank under assets/symbols/png/Alpha/* (for core words)
Falls back to text-only tile if no symbol can be found.

Branding: uses utils.sws_design.apply_small_wins_frame; SWS_DPI.
"""
from __future__ import annotations

import io
import json
import random
import re
from pathlib import Path
import os
from typing import List, Tuple
import sys

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas

try:
    _repo_root = Path(__file__).resolve().parents[2]
    _extra_paths = [
        _repo_root,
        _repo_root / "utils",
        _repo_root / "Generators" / "ARCHIVE generators",
        _repo_root / "Generators",
        _repo_root / "production" / "generators" / "generators",
        _repo_root / "Studioforge" / "tools",
        _repo_root / "tools",
    ]
    for _p in _extra_paths:
        if _p.exists():
            _p_str = str(_p)
            if _p_str not in sys.path:
                sys.path.insert(0, _p_str)
except Exception:
    pass

from utils.sws_design import (
    apply_small_wins_frame,
    DPI as SWS_DPI,
    generate_teacher_cover_page,
    hex_to_rgb,
)
try:
    from tools import icon_resolver as ICONS
except Exception:
    ICONS = None

PAGE_WIDTH, PAGE_HEIGHT = letter
DPI = SWS_DPI
PAGE_W = int(PAGE_WIDTH * DPI / 72)
PAGE_H = int(PAGE_HEIGHT * DPI / 72)

# Level meta
LEVELS = {
    1: {"name": "Supported",   "min": 3,  "max": 4},
    2: {"name": "Developing",  "min": 5,  "max": 6},
    3: {"name": "Independent", "min": 7,  "max": 12},
}


def _best_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    paths = (
        [
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for p in paths:
        try:
            return ImageFont.truetype(p, int(size * (DPI / 72)))
        except Exception:
            pass
    return ImageFont.load_default()


def _load_fonts() -> dict:
    return {
        "title": _best_font(24, bold=True),
        "label": _best_font(12, bold=True),
        "small": _best_font(9, bold=False),
    }


def _symbols_root() -> Path:
    candidates = [
        Path("assets") / "symbols" / "png" / "Alpha",
        Path(__file__).resolve().parents[1] / "assets" / "symbols" / "png" / "Alpha",
    ]
    for c in candidates:
        if c.exists():
            return c
    return Path("assets")


def _sanitize_stem(s: str) -> str:
    t = (s or "").strip().lower()
    t = re.sub(r"[^a-z0-9]+", "_", t)
    return t.strip("_")


def _find_symbol_png(word: str) -> Path | None:
    root = _symbols_root()
    stem = _sanitize_stem(word)
    try:
        exact = list(root.rglob(f"{stem}.png"))
        if exact:
            return exact[0]
        pref = [p for p in root.rglob("*.png") if _sanitize_stem(p.stem) == stem or _sanitize_stem(p.stem).startswith(stem + "_")]
        if pref:
            return pref[0]
    except Exception:
        return None
    return None


def _tokenize(sentence: str) -> List[str]:
    return [w for w in re.findall(r"[A-Za-z']+", sentence or "") if w]


def _read_book_sentences(slug: str) -> List[str]:
    p = Path("assets") / "themes" / slug / "book_vocab.json"
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        arr = data.get("adapted_book_sentences") or data.get("sentences") or []
        if isinstance(arr, list):
            out: List[str] = []
            for s in arr:
                if isinstance(s, str) and s.strip():
                    out.append(s.strip())
                elif isinstance(s, dict):
                    v = s.get("sentence") or s.get("text") or s.get("s")
                    if isinstance(v, str) and v.strip():
                        out.append(v.strip())
            return out
    except Exception:
        return []
    return []


def _load_dotenv_vars() -> None:
    cands = [
        Path(".env"),
        Path(__file__).resolve().parents[2] / ".env",
        Path(__file__).resolve().parents[1] / "backend" / ".env",
    ]
    for p in cands:
        try:
            if not p.exists():
                continue
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if (not line) or line.startswith("#") or ("=" not in line):
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and (k not in os.environ):
                    os.environ[k] = v
        except Exception:
            pass


def _read_ai_policy(slug: str) -> dict:
    base = {
        "enable": True,
        "levels": {"L1": {"min": 3, "max": 4}, "L2": {"min": 5, "max": 6}, "L3": {"min": 7, "max": 12}},
        "must_include_at_least_one_of": [],
        "allowed_vocab_sources": ["activity_images", "icons_colored", "icons", "real_images", "characters"],
        "banned_words": [],
        "attempts": 2,
        "overwrite": False,
    }
    try:
        p = Path("assets") / "themes" / slug / "book_vocab.json"
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8")) or {}
            pol = data.get("ai_sentence_policy") or {}
            if isinstance(pol, dict):
                for k, v in pol.items():
                    base[k] = v if v is not None else base.get(k)
    except Exception:
        pass
    try:
        _load_dotenv_vars()
        if os.environ.get("SWS_AI_SENTENCE_ENABLE"):
            base["enable"] = os.environ.get("SWS_AI_SENTENCE_ENABLE").strip().lower() in ("1","true","yes","on")
        if os.environ.get("SWS_AI_SENTENCE_OVERWRITE"):
            base["overwrite"] = os.environ.get("SWS_AI_SENTENCE_OVERWRITE").strip().lower() in ("1","true","yes","on")
        if os.environ.get("SWS_AI_SENTENCE_ATTEMPTS"):
            try:
                base["attempts"] = max(1, int(os.environ.get("SWS_AI_SENTENCE_ATTEMPTS")))
            except Exception:
                pass
    except Exception:
        pass
    return base


def _theme_vocab_words(slug: str, sources: List[str] | None = None) -> List[str]:
    bases = [
        Path("assets") / "themes" / slug / "activity_images",
        Path("assets") / "themes" / slug / "icons_colored",
        Path("assets") / "themes" / slug / "icons",
        Path("assets") / "themes" / slug / "real_images",
        Path("assets") / "themes" / slug / "characters",
    ]
    if isinstance(sources, list) and sources:
        m = {
            "activity_images": bases[0],
            "icons_colored":  bases[1],
            "icons":          bases[2],
            "real_images":    bases[3],
            "characters":     bases[4],
        }
        bases = [m[n] for n in sources if n in m]
    seen = set()
    out: List[str] = []
    for b in bases:
        if not b.exists():
            continue
        for f in sorted(b.glob("*.png")):
            stem = _sanitize_stem(f.stem)
            if stem and stem not in seen:
                seen.add(stem)
                out.append(stem.replace("_", " "))
            if len(out) >= 40:
                return out
    return out


def _ai_generate_level_sentences(slug: str, book_title: str, vocab: List[str], policy: dict) -> dict:
    _load_dotenv_vars()
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("SWS_OPENAI_API_KEY")
    if not key:
        return {}
    try:
        import json as _json
        import urllib.request as _rq
        import urllib.error as _er
        model = os.environ.get("SWS_OPENAI_MODEL", "gpt-4o-mini")
        url = os.environ.get("SWS_OPENAI_BASE", "https://api.openai.com/v1/chat/completions")
        sys_msg = "You are an SLP generating 3 child-friendly sentences for a picture book. Keep them concrete, positive, and relevant to the book. Use content words only from the provided list; function words are allowed."
        prompt = (
            "Book: " + book_title + "\n" +
            "Allowed content words (examples): " + ", ".join(vocab[:30]) + "\n" +
            f"Rules: Provide exactly 3 sentences using only simple words plus basic function words. L1 must be {policy['levels']['L1']['min']}-{policy['levels']['L1']['max']} words. L2 must be {policy['levels']['L2']['min']}-{policy['levels']['L2']['max']} words. L3 must be {policy['levels']['L3']['min']}-{policy['levels']['L3']['max']} words.\n" +
            "Output strict JSON with keys L1, L2, L3 and string values. No extra text."
        )
        payload = _json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }).encode("utf-8")
        req = _rq.Request(url, data=payload, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with _rq.urlopen(req, timeout=30) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        content = ((data or {}).get("choices") or [{}])[0].get("message", {}).get("content", "{}")
        try:
            obj = _json.loads(content)
        except Exception:
            obj = {}
        if isinstance(obj, dict):
            return obj
    except Exception:
        return {}
    return {}


def _heuristic_sentences(vocab: List[str], book_title: str) -> dict:
    words = [w for w in vocab if w]
    a = (words[0] if len(words) > 0 else "llama").split()[0].title()
    b = (words[1] if len(words) > 1 else "mama").split()[0].title()
    c = (words[2] if len(words) > 2 else "bed").split()[0]
    d = (words[3] if len(words) > 3 else "night").split()[0]
    l1 = f"{a} is {c}."
    l2 = f"{b} hugs {a} at {d}."
    l3 = f"{a} and {b} read in the {c} tonight."
    return {"L1": l1, "L2": l2, "L3": l3}


def _is_function_word(w: str) -> bool:
    w = w.lower()
    return w in {
        "a","an","the","i","you","he","she","we","they","it","and","or","but","of","for","with","to","in","on","at","is","are","am","was","were","be","been","being","do","does","did","go","can","will","not","like","more","my","your","his","her","our","their","this","that","these","those","here","there","up","down","out","by","from","as","than","so","very","too","then","now","me","him","us","them"
    }


def _validate_sentence(s: str, level_key: str, policy: dict, vocab_set: set[str]) -> bool:
    n = len(_tokenize(s))
    rng = (policy.get("levels") or {}).get(level_key, {"min": 1, "max": 99})
    if not (rng["min"] <= n <= rng["max"]):
        return False
    for bad in (policy.get("banned_words") or []):
        if bad and bad.lower() in s.lower():
            return False
    tokens = [t.lower() for t in _tokenize(s)]
    content_like = [t for t in tokens if not _is_function_word(t)]
    req = [t.lower() for t in (policy.get("must_include_at_least_one_of") or [])]
    if req and not any(t in req for t in content_like):
        return False
    for t in content_like:
        if t not in vocab_set:
            return False
    return True


def _ensure_level_sentences_list(slug: str, book_title: str) -> List[str]:
    existing = _read_book_sentences(slug)
    policy = _read_ai_policy(slug)
    if policy.get("overwrite"):
        existing = []
    need_l1 = True
    need_l2 = True
    need_l3 = True
    for s in existing:
        n = len(_tokenize(s))
        if 3 <= n <= 4:
            need_l1 = False
        if 5 <= n <= 6:
            need_l2 = False
        if 7 <= n <= 12:
            need_l3 = False
    if not (need_l1 or need_l2 or need_l3):
        return existing
    vocab = _theme_vocab_words(slug, policy.get("allowed_vocab_sources"))
    ai: dict = {}
    if policy.get("enable", True):
        ai = _ai_generate_level_sentences(slug, book_title, vocab, policy) or {}
    if not ai:
        ai = _heuristic_sentences(vocab, book_title)
    add: List[str] = []
    vocab_set = { _sanitize_stem(w).lower() for w in [w.replace("_"," ") for w in vocab] }
    attempts = max(1, int(policy.get("attempts", 2)))
    def _get_level(level_key: str) -> str | None:
        nonlocal ai
        val = (ai.get(level_key) or "").strip() if ai else ""
        tries = 0
        while val and not _validate_sentence(val, level_key, policy, vocab_set) and tries < attempts and policy.get("enable", True):
            ai = _ai_generate_level_sentences(slug, book_title, vocab, policy) or {}
            val = (ai.get(level_key) or "").strip()
            tries += 1
        return val if val and _validate_sentence(val, level_key, policy, vocab_set) else None
    if need_l1:
        v = _get_level("L1") or _heuristic_sentences(vocab, book_title)["L1"]
        add.append(v)
    if need_l2:
        v = _get_level("L2") or _heuristic_sentences(vocab, book_title)["L2"]
        add.append(v)
    if need_l3:
        v = _get_level("L3") or _heuristic_sentences(vocab, book_title)["L3"]
        add.append(v)
    final = existing + add
    try:
        p = Path("assets") / "themes" / slug / "book_vocab.json"
        data = {}
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8")) or {}
            except Exception:
                data = {}
        arr = list({s.strip(): 1 for s in final if isinstance(s, str) and s.strip()}.keys())
        data["adapted_book_sentences"] = arr
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            tpath = p.parent / "ai_trace.json"
            tdata = {
                "policy": policy,
                "generated_sample": {"L1": (ai.get("L1") if isinstance(ai, dict) else None),
                                       "L2": (ai.get("L2") if isinstance(ai, dict) else None),
                                       "L3": (ai.get("L3") if isinstance(ai, dict) else None)},
                "vocab_sample": vocab[:30],
            }
            tpath.write_text(json.dumps(tdata, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
    except Exception:
        pass
    return final


def _build_book_icon_index(slug: str) -> dict:
    idx = {}
    targets = []
    try:
        if ICONS is not None:
            targets = ICONS.collect_targets(slug)
    except Exception:
        targets = []
    for key in targets:
        try:
            rr = ICONS.resolve(key, slug, context={"generator": "sentence_builder"}) if ICONS is not None else None
        except Exception:
            rr = None
        if rr and rr.path and rr.path.exists():
            try:
                im = Image.open(rr.path)
                if im.mode != "RGBA":
                    im = im.convert("RGBA")
                idx[_sanitize_stem(key)] = im
            except Exception:
                pass
    return idx


def _tile_icon_for(word: str, *, book_idx: dict, color: bool) -> Image.Image:
    stem = _sanitize_stem(word)
    # 1) Try book icon set
    img = book_idx.get(stem)
    if img is not None:
        return img.copy() if color else img.convert("L").convert("RGBA")
    # 2) Try global AAC symbol bank
    p = _find_symbol_png(word)
    if p and p.exists():
        try:
            im = Image.open(p)
            im = im.convert("RGBA")
            return im.copy() if color else im.convert("L").convert("RGBA")
        except Exception:
            pass
    # 3) Fallback: text-only tile rendered later
    return None


def _draw_tile(d: ImageDraw.ImageDraw, page: Image.Image, x: int, y: int, w: int, h: int, *, img: Image.Image | None, label: str, color: bool):
    teal = hex_to_rgb("#31A8A0")
    d.rounded_rectangle([x, y, x + w, y + h], radius=int(0.10 * DPI), fill="white", outline=teal, width=max(2, int(3 * (DPI / 150))))
    pad = int(0.08 * h)
    icon_box_h = int(h * 0.72)
    fonts = _load_fonts()
    if img is not None:
        ic = img.copy()
        ic.thumbnail((w - pad * 2, icon_box_h - pad * 2), Image.Resampling.LANCZOS)
        page.paste(ic, (x + (w - ic.width) // 2, y + pad + (icon_box_h - ic.height) // 2), ic)
    else:
        # Text-only placeholder
        bb = d.textbbox((0, 0), label, font=fonts["label"])
        d.text((x + (w - (bb[2] - bb[0])) // 2, y + (icon_box_h - (bb[3] - bb[1])) // 2), label, fill=(30, 30, 30), font=fonts["label"])    
    # Label
    bb = d.textbbox((0, 0), label, font=fonts["label"])
    d.text((x + (w - (bb[2] - bb[0])) // 2, y + icon_box_h + (h - icon_box_h - (bb[3] - bb[1])) // 2), label, fill=hex_to_rgb("#0D2545"), font=fonts["label"])


def _page_frame(page: Image.Image, *, product_title: str, subtitle: str, pack_code: str, page_num: int, total_pages: int, level: int | None, instruction: str | None = None, header_left_icon: Image.Image | None = None):
    apply_small_wins_frame(
        page,
        product_title=product_title,
        subtitle=subtitle,
        instruction_text=instruction,
        pack_code=pack_code,
        page_num=page_num,
        total_pages=total_pages,
        level=level,
        header_left_icon=header_left_icon,
        draw_accent_strip=True,
        draw_header=True,
        draw_subtitle=True,
        draw_footer=True,
        footer_compact=False,
        footer_y_offset_px=int(0.20 * DPI),
        show_data_strip=False,
    )


def _create_tile_sheet(words: List[str], *, slug: str, book_title: str, pack_code: str, page_num: int, total_pages: int, level: int, color: bool, header_left_icon: Image.Image | None = None) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    _page_frame(page, product_title="Participation Pieces — Sentence Builder", subtitle=book_title, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=level, instruction="Cut Out Word Tiles", header_left_icon=header_left_icon)
    d = ImageDraw.Draw(page)

    cols = 4
    gap = int(0.18 * DPI)
    side = int(1.20 * DPI)
    total_w = cols * side + (cols - 1) * gap
    x0 = (PAGE_W - total_w) // 2
    # content top
    top = int(1.90 * DPI)

    book_idx = _build_book_icon_index(slug)
    tiles = [(w, _tile_icon_for(w, book_idx=book_idx, color=color)) for w in words]

    for i, (wrd, im) in enumerate(tiles):
        r = i // cols
        c = i % cols
        x = x0 + c * (side + gap)
        y = top + r * (side + gap)
        _draw_tile(d, page, x, y, side, side, img=im, label=wrd.title(), color=color)
    return page


def _create_base_strip(words: List[str], *, book_title: str, pack_code: str, page_num: int, total_pages: int, level: int, header_left_icon: Image.Image | None = None) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    _page_frame(page, product_title="Participation Pieces — Sentence Builder", subtitle=book_title, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=level, instruction="Base Strip — Place Tiles on Velcro Dots", header_left_icon=header_left_icon)
    d = ImageDraw.Draw(page)

    teal = hex_to_rgb("#31A8A0")
    slots = len(words)
    pad_x = int(0.50 * DPI)
    gap = int(0.20 * DPI)
    slot_w = int(1.10 * DPI)
    slot_h = int(0.95 * DPI)

    total_w = slots * slot_w + (slots - 1) * gap
    x = max(pad_x, (PAGE_W - total_w) // 2)
    y = int(3.0 * DPI)

    for i in range(slots):
        d.rounded_rectangle([x, y, x + slot_w, y + slot_h], radius=int(0.14 * DPI), outline=teal, width=int(3 * (DPI / 150)))
        # Velcro dot
        vx = x + slot_w // 2
        vy = y + slot_h // 2
        r = int(0.10 * DPI)
        d.ellipse([vx - r, vy - r, vx + r, vy + r], fill=(220, 235, 235), outline=teal, width=1)
        x += slot_w + gap
    return page


def _create_answer_key(words: List[str], *, book_title: str, pack_code: str, page_num: int, total_pages: int, level: int, header_left_icon: Image.Image | None = None) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    _page_frame(page, product_title="Participation Pieces — Sentence Builder", subtitle=book_title, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=level, instruction="Answer Key — Correct Order", header_left_icon=header_left_icon)
    d = ImageDraw.Draw(page)
    fonts = _load_fonts()

    sent = " ".join(words).strip().capitalize()
    bb = d.textbbox((0, 0), sent, font=fonts["title"])
    d.text(((PAGE_W - (bb[2] - bb[0])) // 2, int(2.0 * DPI)), sent, fill=hex_to_rgb("#0D2545"), font=fonts["title"])

    # Show numbered slots below
    y = int(3.1 * DPI)
    gap = int(0.12 * DPI)
    for i, w in enumerate(words, 1):
        txt = f"{i}. {w.title()}"
        tb = d.textbbox((0, 0), txt, font=fonts["label"])
        d.text((int(0.9 * DPI), y), txt, fill=(70, 70, 70), font=fonts["label"])
        y += (tb[3] - tb[1]) + gap
    return page


def _create_worksheet(words: List[str], *, slug: str, book_title: str, pack_code: str, page_num: int, total_pages: int, level: int, color: bool, errorless: bool, header_left_icon: Image.Image | None = None) -> Image.Image:
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    instr = "Cut & Paste — Icons + Words (Errorless)" if errorless else "Cut & Paste — Icons + Words"
    _page_frame(page, product_title="Participation Pieces — Sentence Builder", subtitle=book_title, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=level, instruction=instr, header_left_icon=header_left_icon)
    d = ImageDraw.Draw(page)

    book_idx = _build_book_icon_index(slug)
    tiles = [(w, _tile_icon_for(w, book_idx=book_idx, color=color)) for w in words]

    # Base strip area
    teal = hex_to_rgb("#31A8A0")
    slots = len(words)
    pad_x = int(0.40 * DPI)
    gap = int(0.16 * DPI)
    slot_w = int(1.00 * DPI)
    slot_h = int(0.85 * DPI)

    total_w = slots * slot_w + (slots - 1) * gap
    x = max(pad_x, (PAGE_W - total_w) // 2)
    y = int(2.0 * DPI)

    for i in range(slots):
        d.rounded_rectangle([x, y, x + slot_w, y + slot_h], radius=int(0.14 * DPI), outline=teal, width=int(3 * (DPI / 150)))
        if errorless:
            # print faint guide order inside slot
            label = words[i].title()
            bb = d.textbbox((0, 0), label, font=_load_fonts()["small"])
            d.text((x + (slot_w - (bb[2] - bb[0])) // 2, y + (slot_h - (bb[3] - bb[1])) // 2), label, fill=(170, 190, 190), font=_load_fonts()["small"])
        x += slot_w + gap

    # Tile bank (scrambled unless errorless where we keep the same order for cutting simplicity)
    order = list(range(len(tiles)))
    if not errorless:
        random.Random(len(words) * 997).shuffle(order)

    cols = 4
    gap2 = int(0.14 * DPI)
    side = int(1.10 * DPI)
    total_w2 = cols * side + (cols - 1) * gap2
    x0 = (PAGE_W - total_w2) // 2
    top = int(3.2 * DPI)

    for row_idx, i in enumerate(order):
        r = row_idx // cols
        c = row_idx % cols
        x = x0 + c * (side + gap2)
        y = top + r * (side + gap2)
        _draw_tile(d, page, x, y, side, side, img=tiles[i][1], label=tiles[i][0].title(), color=color)

    return page


def _pick_sentence_for_level(all_sentences: List[str], level: int) -> List[str] | None:
    rng = random.Random(12345 + level)
    rng.shuffle(all_sentences)
    meta = LEVELS[level]
    for s in all_sentences:
        words = _tokenize(s)
        if meta["min"] <= len(words) <= meta["max"]:
            return [w.lower() for w in words]
    return None


def generate_participation_pieces_sentence_builder(slug: str, book_title: str, pack_code: str = "SB-PARTS") -> bool:
    print(f"\n{'='*70}")
    print(f"  PARTICIPATION PIECES — SENTENCE BUILDER: {pack_code}  ({book_title})")
    print(f"{'='*70}\n")

    sentences = _ensure_level_sentences_list(slug, book_title)
    if not sentences:
        print("  ERROR: No 'adapted_book_sentences' found in book_vocab.json")
        return False

    output_dir = Path("OUTPUT")
    output_dir.mkdir(exist_ok=True)

    # Build pages for color/BW in one go
    def build_pages(color: bool) -> list[Image.Image]:
        pages: list[Image.Image] = []
        # Insert standardized teacher cover (portrait) as first page
        hero_path_str = None
        book_cover_path_str = None
        try:
            tdir = Path("assets") / "themes" / slug
            hero_candidates = [
                tdir / "hero_header.png",
                tdir / "heroes" / "hero_header.png",
                tdir / "characters" / "hero_header.png",
                tdir / "hero.png",
                tdir / "heroes" / "hero.png",
                tdir / "characters" / "hero.png",
                tdir / "header_icon.png",
            ]
            for hp in hero_candidates:
                if hp.exists():
                    hero_path_str = str(hp)
                    break
            cover_names = ["book_cover", "cover", "front_cover", "bookfront", "book", "cover_reference"]
            cover_subdirs = [tdir, tdir / "covers", tdir / "images", tdir / "marketing", tdir / "book"]
            exts = ["png", "jpg", "jpeg", "webp"]
            for sd in cover_subdirs:
                for nm in cover_names:
                    for ex in exts:
                        fp = sd / f"{nm}.{ex}"
                        if fp.exists():
                            book_cover_path_str = str(fp)
                            break
                    if book_cover_path_str:
                        break
                if book_cover_path_str:
                    break
        except Exception:
            hero_path_str = None
            book_cover_path_str = None
        content_pages_after_cover = 3 * 5
        cov = generate_teacher_cover_page(
            theme_name=book_title,
            pack_code=pack_code,
            product_name="Participation Pieces — Sentence Builder",
            page_count=content_pages_after_cover,
            level_count=3,
            hero_image=None,
            hero_image_path=hero_path_str,
            book_cover_path=book_cover_path_str,
            draw_footer=True,
            whats_included=[
                "3 levels: Supported, Developing, Independent",
                "Word/icon tile sheets",
                "Base strips with velcro dots",
                "Answer keys",
                "Cut & paste worksheets (icons + words, errorless)",
            ],
            also_included=[
                "Black & white version",
                "Terms of Use",
            ],
            top_tips=[
                "Model AAC/core words as you build.",
                "Use the errorless sheet for emerging learners.",
                "Encourage pointing/placing for engagement.",
            ],
            small_win_text="Small Wins",
        )
        if not color:
            try:
                cov = cov.convert("L").convert("RGB")
            except Exception:
                pass
        pages.append(cov)
        # We will build 5 pages per level as per scope
        total_pages = 3 * 5
        page_num = 1
        try:
            header_icon_img = Image.open(hero_path_str).convert("RGBA") if hero_path_str else None
        except Exception:
            header_icon_img = None
        for level in (1, 2, 3):
            words = _pick_sentence_for_level(sentences, level)
            if not words:
                print(f"  WARN: No sentence matched Level {level} word count; skipping level")
                continue
            pages.append(_create_tile_sheet(words, slug=slug, book_title=book_title, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=level, color=color, header_left_icon=header_icon_img)); page_num += 1
            pages.append(_create_base_strip(words, book_title=book_title, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=level, header_left_icon=header_icon_img)); page_num += 1
            pages.append(_create_answer_key(words, book_title=book_title, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=level, header_left_icon=header_icon_img)); page_num += 1
            pages.append(_create_worksheet(words, slug=slug, book_title=book_title, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=level, color=color, errorless=False, header_left_icon=header_icon_img)); page_num += 1
            pages.append(_create_worksheet(words, slug=slug, book_title=book_title, pack_code=pack_code, page_num=page_num, total_pages=total_pages, level=level, color=color, errorless=True, header_left_icon=header_icon_img)); page_num += 1
        return pages

    def to_pdf(pages, path):
        c = rl_canvas.Canvas(str(path), pagesize=letter)
        for pg in pages:
            buf = io.BytesIO()
            pg.save(buf, format="PNG", dpi=(DPI, DPI))
            buf.seek(0)
            c.drawImage(ImageReader(buf), 0, 0, width=PAGE_WIDTH, height=PAGE_HEIGHT)
            c.showPage()
        c.save()

    color_path = output_dir / f"{pack_code}_SentenceBuilder_COLOR.pdf"
    bw_path    = output_dir / f"{pack_code}_SentenceBuilder_BW.pdf"

    print("  Writing COLOR PDF ...")
    to_pdf(build_pages(color=True), color_path)
    print(f"  ✓  {color_path}")

    print("  Writing B&W PDF ...")
    to_pdf(build_pages(color=False), bw_path)
    print(f"  ✓  {bw_path}")

    print(f"\n{'='*70}")
    print("  SENTENCE BUILDER MODULE COMPLETE")
    print(f"{'='*70}\n")
    return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python PARTICIPATION_PIECES.py <slug> <book_title> [pack_code]")
        sys.exit(1)
    ok = generate_participation_pieces_sentence_builder(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "SB-PARTS")
    sys.exit(0 if ok else 1)
