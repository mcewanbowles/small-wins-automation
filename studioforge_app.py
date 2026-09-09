# -*- coding: utf-8 -*-
import os
import json
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import shutil
from PIL import Image, ImageChops, ImageDraw, ImageFont
import re
import zipfile
import io
import importlib
import csv
import base64
import urllib.parse
import urllib.request
import html
import hashlib
import time
import threading

from utils.sws_design import DPI, NAVY_HEX, apply_small_wins_frame, hex_to_rgb

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None
import streamlit as st
import streamlit.components.v1 as components
try:
    from dotenv import load_dotenv
except Exception:  # package may not be installed yet
    def load_dotenv(*args, **kwargs):
        return False
try:
    import anthropic
except Exception:
    anthropic = None
try:
    from Studioforge.boardready.modules import qa_logic as icon_qa_logic
except Exception:
    icon_qa_logic = None

# Extracted modules
from sf_shared import (
    project_root as _sf_project_root,
    find_book_dir as _sf_find_book_dir,
    images_dir_for_book as _sf_images_dir_for_book,
    symbols_root as _sf_symbols_root,
    sanitise_symbol_name as _sf_sanitise_symbol_name,
    save_icon_to_library as _sf_save_icon_to_library,
    save_uploaded_icon_to_library as _sf_save_uploaded_icon_to_library,
    library_png_paths as _sf_library_png_paths,
    clear_library_png_cache as _sf_clear_library_png_cache,
    accepted_icon_for_word as _sf_accepted_icon_for_word,
    clear_accepted_icon_cache as _sf_clear_accepted_icon_cache,
    set_icon_word_status as _sf_set_icon_word_status,
    icon_word_decision as _sf_icon_word_decision,
    read_book_state as _sf_read_book_state,
    write_book_state as _sf_write_book_state,
    get_kit_key as _sf_get_kit_key,
    get_hero_key as _sf_get_hero_key,
    vocab_state_key as _sf_vocab_state_key,
    clear_icon_review_summary_cache as _sf_clear_icon_review_summary_cache,
    clear_workflow_gate_cache as _sf_clear_workflow_gate_cache,
    clear_vocab_source_cache as _sf_clear_vocab_source_cache,
    clear_book_vocab_cache as _sf_clear_book_vocab_cache,
)
from sf_tracker import (
    read_upload_tracker as _sf_read_upload_tracker,
    write_upload_tracker as _sf_write_upload_tracker,
    init_tracker_pack as _sf_init_tracker_pack,
    update_tracker_record as _sf_update_tracker_record,
    tracker_stats as _sf_tracker_stats,
    tracker_record_id as _sf_tracker_record_id,
    tracker_status_cycle as _sf_tracker_status_cycle,
    export_tracker_csv as _sf_export_tracker_csv,
    _now_iso_date as _sf_now_iso_date,
    _now_iso_dt as _sf_now_iso_dt,
)


def project_root() -> Path:
    return Path(__file__).resolve().parent


def upload_tracker_path() -> Path:
    return project_root() / "upload_tracker.json"


def upload_tracker_audit_path() -> Path:
    return project_root() / "upload_tracker_audit.jsonl"


def _read_json_safe(p: Path, default):
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def read_upload_tracker() -> list[dict]:
    data = _read_json_safe(upload_tracker_path(), default=[])
    return data if isinstance(data, list) else []


def write_upload_tracker(records: list[dict]) -> None:
    p = upload_tracker_path()
    try:
        p.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def append_upload_tracker_audit(event: dict) -> None:
    p = upload_tracker_audit_path()
    try:
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _now_iso_date() -> str:
    return datetime.now().date().isoformat()


def _now_iso_dt() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _today_cache_path() -> Path:
    p = project_root() / "assets" / "config" / "today_recommendations.json"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return p


def load_today_cache() -> dict:
    try:
        p = _today_cache_path()
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def save_today_cache(data: dict) -> None:
    try:
        _today_cache_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_today_recommendations(display_map: dict, season: str, force: bool = False) -> list[str]:
    """Return fast local picks by default; request AI picks only on an explicit refresh."""
    try:
        today = _now_iso_date()
        ai_available = (anthropic is not None) and bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
        use_ai = bool(force and ai_available)
        if not force:
            data = load_today_cache()
            if (
                isinstance(data, dict)
                and data.get("date") == today
                and data.get("season") == season
                and bool(data.get("ai")) is False
                and isinstance(data.get("picks"), list)
            ):
                return [str(x) for x in data.get("picks")][:3]
        if use_ai:
            picks = ai_today_recommendations(display_map, season)
            if not picks:
                picks = season_recommendations(display_map, season)
        else:
            picks = season_recommendations(display_map, season)
        save_today_cache({"date": today, "season": season, "ai": use_ai, "picks": picks})
        return [str(x) for x in picks][:3]
    except Exception:
        # Absolute fallback
        return season_recommendations(display_map, season)[:3]


def ai_today_recommendations(display_map: dict, season: str) -> list[str]:
    """Use Anthropic to choose up to 3 titles. Returns empty list on failure."""
    try:
        if anthropic is None:
            return []
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            return []
        try:
            client = anthropic.Anthropic(api_key=api_key)
        except Exception:
            # Older SDKs may use a different constructor
            client = anthropic.Client(api_key=api_key)  # type: ignore[attr-defined]
        titles = [display_map[k] for k in display_map.keys()]
        # Build a compact prompt requesting strict JSON array output
        system_msg = (
            "You recommend which book packs to build today. "
            "Return ONLY a JSON array (no prose) of up to 3 titles from the provided list."
        )
        lst = "\n".join(f"- {t}" for t in titles[:200])
        user_msg = (
            f"Season: {season}\n"
            "Consider variety across product types and recent activity is unknown.\n"
            "Pick widely appealing options. Titles list follows.\n\n"
            f"Titles:\n{lst}\n\nReturn JSON only, e.g. [\"Title A\", \"Title B\"]."
        )
        # Prefer a small, economical model; fall back to sonnet if needed
        model = os.environ.get("SF_AI_MODEL", "claude-3-haiku-20240307")
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=256,
                system=system_msg,
                messages=[{"role": "user", "content": user_msg}],
            )
            # SDK returns content list with text blocks
            content = getattr(resp, "content", None)
            if isinstance(content, list) and content:
                text = getattr(content[0], "text", None) or (content[0].get("text") if isinstance(content[0], dict) else None)
            else:
                text = getattr(resp, "text", None) or str(resp)
        except Exception:
            return []
        # Parse JSON array defensively
        try:
            s = str(text or "").strip()
            # If the model wrapped JSON in prose, extract the first [...]
            i = s.find("[")
            j = s.rfind("]")
            if i != -1 and j != -1 and j > i:
                s = s[i : j + 1]
            arr = json.loads(s)
            if not isinstance(arr, list):
                return []
            want = set(titles)
            picks = [str(x) for x in arr if str(x) in want][:3]
            return picks
        except Exception:
            return []
    except Exception:
        return []


def _thumbs_dir() -> Path:
    p = project_root() / ".cache" / "thumbs"
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return p

def _thumb_cache_path(src: Path) -> Path:
    try:
        mtime = int(src.stat().st_mtime) if src.exists() else 0
    except Exception:
        mtime = 0
    try:
        key = hashlib.sha1(f"{str(src.resolve())}|{mtime}".encode("utf-8")).hexdigest()
    except Exception:
        key = hashlib.sha1(str(src).encode("utf-8")).hexdigest()
    return _thumbs_dir() / f"{key}.png"

def _make_thumbnail(src: Path, max_w: int = 300, max_h: int = 180) -> Path | None:
    try:
        if not src or not src.exists():
            return None
        dest = _thumb_cache_path(src)
        if dest.exists():
            return dest
        ext = src.suffix.lower()
        if ext == ".pdf":
            if fitz is None:
                return None
            doc = fitz.open(str(src))
            pg = doc.load_page(0)
            pix = pg.get_pixmap(matrix=fitz.Matrix(1.0, 1.0), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        elif ext in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            img = Image.open(str(src)).convert("RGB")
        else:
            return None
        try:
            img.thumbnail((max_w, max_h), Image.LANCZOS)
        except Exception:
            img.thumbnail((max_w, max_h))
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(dest), format="PNG")
        return dest
    except Exception:
        return None

def tracker_record_id(book_slug: str, pack_code: str, product_type: str) -> str:
    return f"{book_slug}__{pack_code}__{product_type}".lower()


def tracker_status_cycle(status: str) -> str:
    order = ["not_started", "ready", "uploaded"]
    s = (status or "not_started").strip().lower()
    if s not in order:
        return "not_started"
    return order[(order.index(s) + 1) % len(order)]


def init_tracker_pack(*, book_slug: str, book_title: str, pack_code: str, product_types: list[str]) -> int:
    """Ensure records exist for pack; do not overwrite existing."""
    records = read_upload_tracker()
    by_id = {str(r.get("id")): r for r in records if isinstance(r, dict) and r.get("id")}
    created = 0
    now = _now_iso_dt()
    for pt in product_types:
        rid = tracker_record_id(book_slug, pack_code, pt)
        if rid in by_id:
            continue
        rec = {
            "id": rid,
            "book_slug": book_slug,
            "book_title": book_title,
            "pack_code": pack_code,
            "product_type": pt,
            "status": "not_started",
            "uploaded_date": None,
            "tpt_url": None,
            "tpt_listing_id": None,
            "notes": "",
            "thumbnail_path": None,
            "listing_exported": False,
            "created_at": now,
            "updated_at": now,
        }
        records.append(rec)
        created += 1
        append_upload_tracker_audit({"ts": now, "action": "create", "id": rid, "record": rec})
    if created:
        write_upload_tracker(records)
    return created


def update_tracker_record(record_id: str, patch: dict) -> None:
    records = read_upload_tracker()
    now = _now_iso_dt()
    updated = False
    for r in records:
        if not isinstance(r, dict):
            continue
        if str(r.get("id")) == str(record_id):
            before = dict(r)
            for k, v in (patch or {}).items():
                r[k] = v
            r["updated_at"] = now
            updated = True
            append_upload_tracker_audit({"ts": now, "action": "patch", "id": record_id, "before": before, "patch": patch})
            break
    if updated:
        write_upload_tracker(records)


def tracker_stats(records: list[dict]) -> dict[str, int]:
    out = {"uploaded": 0, "ready": 0, "not_started": 0, "needs_update": 0, "paused": 0}
    for r in records:
        if not isinstance(r, dict):
            continue
        s = str(r.get("status") or "not_started").strip().lower()
        if s not in out:
            continue
        out[s] += 1
    return out


def render_status_badge(status: str, key: str) -> bool:
    s = (status or "not_started").strip().lower()
    styles = {
        "not_started": ("#F3F3F3", "#999999", "Not started"),
        "ready": ("#E8F8F8", "#006379", "Ready"),
        "uploaded": ("#EEFFEE", "#2D8A00", "Uploaded"),
        "needs_update": ("#FFF8E0", "#E07B00", "Needs update"),
        "paused": ("#F3F3F3", "#999999", "Paused"),
    }
    bg, fg, label = styles.get(s, styles["not_started"])
    clicked = st.button(
        label,
        key=key,
        help="Click to cycle status: Not started -> Ready -> Uploaded",
    )
    st.markdown(
        f"""
<style>
  button#{key} {{ background: {bg} !important; color: {fg} !important; border: 1px solid {fg}33 !important; }}
</style>
""",
        unsafe_allow_html=True,
    )
    return bool(clicked)


def render_tracker_screen(display_map: dict[str, str]):
    st.header("Upload Tracker")
    records = read_upload_tracker()
    stats = tracker_stats(records)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Uploaded", stats.get("uploaded", 0))
    with c2:
        st.metric("Ready", stats.get("ready", 0))
    with c3:
        st.metric("Not started", stats.get("not_started", 0))
    with c4:
        st.metric("Needs update", stats.get("needs_update", 0))
    with c5:
        st.metric("Paused", stats.get("paused", 0))

    st.divider()

    # Filters
    status_opts = ["not_started", "ready", "uploaded", "needs_update", "paused"]
    f1, f2, f3, f4 = st.columns([2, 2, 2, 2])
    with f1:
        status_sel = st.multiselect("Status", options=status_opts, default=[])
    with f2:
        book_q = st.text_input("Book search", value="")
    with f3:
        pt_sel = st.multiselect(
            "Product type",
            options=sorted({str(r.get("product_type")) for r in records if isinstance(r, dict) and r.get("product_type")}),
            default=[],
        )
    with f4:
        pack_q = st.text_input("Pack code", value=st.session_state.get("trk_pack_filter", ""), key="trk_pack_filter")

    # Seed missing tracker records for current active book/pack
    try:
        active_slug = st.session_state.get("active_book")
        if active_slug:
            st.caption("")
            a1, a2 = st.columns([2, 2])
            with a1:
                st.caption(f"Active book: {display_map.get(active_slug, decode_slug(active_slug))}")
            with a2:
                st.caption("")
            b1, b2 = st.columns([2, 2])
            with b1:
                if st.button("Seed missing products for current pack", key="trk_seed_missing"):
                    st_data = read_book_state(active_slug)
                    pack = ((st_data.get("build", {}) or {}).get("pack_code") or default_pack_code(active_slug))
                    pts = [spec["name"] for spec in PRODUCT_SPECS]
                    created = init_tracker_pack(book_slug=active_slug, book_title=display_map.get(active_slug, decode_slug(active_slug)), pack_code=pack, product_types=pts)
                    if created:
                        show_toast("success", f"Created {created} tracker record(s)")
                    else:
                        show_toast("info", "No new records - already up to date")
                    safe_rerun()
    except Exception:
        pass

    filt = []
    for r in records:
        if not isinstance(r, dict):
            continue
        s = str(r.get("status") or "not_started").strip().lower()
        if status_sel and s not in set(status_sel):
            continue
        if pt_sel and str(r.get("product_type") or "") not in set(pt_sel):
            continue
        if book_q.strip():
            hay = (str(r.get("book_title") or "") + " " + str(r.get("book_slug") or "")).lower()
            if book_q.strip().lower() not in hay:
                continue
        if pack_q and pack_q.strip() and pack_q.strip().lower() not in str(r.get("pack_code") or "").lower():
            continue
        filt.append(r)

    # Sort by updated_at desc
    def _k(rr: dict):
        return str(rr.get("updated_at") or "")
    filt.sort(key=_k, reverse=True)

    st.caption(f"Records: {len(filt)}")

    # Bulk selection and actions
    if "trk_sel" not in st.session_state:
        st.session_state["trk_sel"] = []
    sel_ids = st.session_state.get("trk_sel", [])
    bc1, bc2, bc3 = st.columns([2, 2, 2])
    with bc1:
        st.caption(f"Selected: {len(sel_ids)}")
        if st.button("Select all (filtered)", key="trk_sel_all"):
            st.session_state["trk_sel"] = [str(r.get("id")) for r in filt if isinstance(r, dict) and r.get("id")]
            safe_rerun()
        if st.button("Invert selection", key="trk_sel_inv"):
            all_ids = [str(r.get("id")) for r in filt if isinstance(r, dict) and r.get("id")]
            cur = set(st.session_state.get("trk_sel", []))
            st.session_state["trk_sel"] = [rid for rid in all_ids if rid not in cur]
            safe_rerun()
        if st.button("Clear selection", key="trk_sel_clear"):
            st.session_state["trk_sel"] = []
            safe_rerun()
    with bc2:
        if st.button("Mark Ready", key="trk_mark_ready", disabled=not sel_ids):
            for rid in list(sel_ids):
                update_tracker_record(rid, {"status": "ready"})
            show_toast("success", f"Updated {len(sel_ids)} record(s) -> Ready")
            safe_rerun()
        if st.button("Mark Uploaded", key="trk_mark_uploaded", disabled=not sel_ids):
            for rid in list(sel_ids):
                update_tracker_record(rid, {"status": "uploaded", "uploaded_date": _now_iso_date()})
            show_toast("success", f"Updated {len(sel_ids)} record(s) -> Uploaded")
            safe_rerun()
        if st.button("Mark Not Started", key="trk_mark_not_started", disabled=not sel_ids):
            for rid in list(sel_ids):
                update_tracker_record(rid, {"status": "not_started", "uploaded_date": None})
            show_toast("success", f"Updated {len(sel_ids)} record(s) -> Not started")
            safe_rerun()
        if st.button("Mark Needs Update", key="trk_mark_needs_update", disabled=not sel_ids):
            for rid in list(sel_ids):
                update_tracker_record(rid, {"status": "needs_update"})
            show_toast("success", f"Updated {len(sel_ids)} record(s) -> Needs update")
            safe_rerun()
        if st.button("Mark Paused", key="trk_mark_paused", disabled=not sel_ids):
            for rid in list(sel_ids):
                update_tracker_record(rid, {"status": "paused"})
            show_toast("success", f"Updated {len(sel_ids)} record(s) -> Paused")
            safe_rerun()
    with bc3:
        try:
            import io as _io, csv as _csv
            buf = _io.StringIO()
            wr = _csv.writer(buf)
            wr.writerow(["id","book_title","book_slug","pack_code","product_type","status","uploaded_date","tpt_url","tpt_listing_id","notes","updated_at"])
            rows = [r for r in filt if isinstance(r, dict)]
            for r in rows:
                wr.writerow([r.get("id"), r.get("book_title"), r.get("book_slug"), r.get("pack_code"), r.get("product_type"), r.get("status"), r.get("uploaded_date"), r.get("tpt_url"), r.get("tpt_listing_id"), (r.get("notes") or "").replace("\n", " ").strip(), r.get("updated_at")])
            st.download_button("Export CSV (filtered)", data=buf.getvalue().encode("utf-8-sig"), file_name="tracker_export.csv", mime="text/csv", key="trk_export_csv")
        except Exception:
            pass
        active_slug = st.session_state.get("active_book")
        if active_slug and st.button("Open TPT_UPLOAD (active)", key="trk_open_upload"):
            out = output_dir_for_book(active_slug)
            up = (out / "TPT_UPLOAD") if out else None
            if up and up.exists():
                open_folder(up)
            else:
                show_toast("info", "TPT_UPLOAD not found")
        if active_slug and st.button("Open FINAL (active)", key="trk_open_final"):
            out = output_dir_for_book(active_slug)
            fi = (out / "FINAL") if out else None
            if fi and fi.exists():
                open_folder(fi)
            else:
                show_toast("info", "FINAL not found")

    pending_ids = [str(r.get("id")) for r in filt if str(r.get("status") or "not_started").strip().lower() in {"not_started","ready","needs_update"} and r.get("id")]
    st.session_state["trk_pending_ids"] = pending_ids
    fp1, fp2, fp3 = st.columns([1, 1, 2])
    with fp1:
        if st.button("Prev Pending", key="trk_prev_pending", disabled=not pending_ids):
            idx = int(st.session_state.get("trk_focus_idx", 0) or 0)
            idx = (idx - 1) % len(pending_ids) if pending_ids else 0
            st.session_state["trk_focus_idx"] = idx
            st.session_state["trk_focus_id"] = pending_ids[idx] if pending_ids else None
            safe_rerun()
    with fp2:
        if st.button("Next Pending", key="trk_next_pending", disabled=not pending_ids):
            idx = int(st.session_state.get("trk_focus_idx", -1) or -1)
            idx = (idx + 1) % len(pending_ids) if pending_ids else 0
            st.session_state["trk_focus_idx"] = idx
            st.session_state["trk_focus_id"] = pending_ids[idx] if pending_ids else None
            safe_rerun()
    with fp3:
        if pending_ids:
            cur = int(st.session_state.get("trk_focus_idx", 0) or 0) % len(pending_ids)
            st.caption(f"Pending focus: {cur+1}/{len(pending_ids)}")
    if not filt:
        st.info("No tracker records yet. Build/Finalize a pack to auto-create records.")
        return

    # Table-ish list with inline expand
    for i, r in enumerate(filt[:250]):
        rid = str(r.get("id") or "")
        book_title = str(r.get("book_title") or display_map.get(str(r.get("book_slug") or ""), ""))
        pack = str(r.get("pack_code") or "")
        pt = str(r.get("product_type") or "")
        status = str(r.get("status") or "not_started")
        uploaded_date = r.get("uploaded_date")
        tpt_url = str(r.get("tpt_url") or "")
        notes = str(r.get("notes") or "")

        row = st.container()
        with row:
            a, b, c, d, e = st.columns([3, 2, 1.5, 2, 2])
            with a:
                sel_key = f"trk_sel_{rid}"
                checked = st.checkbox("Select", value=(rid in st.session_state.get("trk_sel", [])), key=sel_key)
                try:
                    cur = set(st.session_state.get("trk_sel", []))
                    if checked:
                        cur.add(rid)
                    else:
                        cur.discard(rid)
                    st.session_state["trk_sel"] = list(cur)
                except Exception:
                    pass
                st.markdown(f"**{book_title}**")
                st.caption(f"{pack} - {pt}")
            with b:
                new_s = tracker_status_cycle(status)
                status_labels = {"not_started": "Not started", "ready": "Ready", "uploaded": "Uploaded", "needs_update": "Needs update", "paused": "Paused"}
                if st.button(
                    f"{status_labels.get(status, 'Not started')} -> {status_labels.get(new_s, 'Ready')}",
                    key=f"trk_cycle_{rid}",
                    help=f"Change this product from {status_labels.get(status, 'Not started')} to {status_labels.get(new_s, 'Ready')}",
                    use_container_width=True,
                ):
                    patch = {"status": new_s}
                    if new_s == "uploaded" and not r.get("uploaded_date"):
                        patch["uploaded_date"] = _now_iso_date()
                    update_tracker_record(rid, patch)
                    show_toast("success", f"Status -> {new_s}")
                    safe_rerun()
                st.caption(status_labels.get(status, status.replace("_", " ").title()))
            with c:
                st.caption("Uploaded")
                st.write(uploaded_date or "-")
            with d:
                st.caption("TPT URL")
                if tpt_url:
                    st.markdown(f"[Open]({tpt_url})")
                    if st.button("Check", key=f"trk_url_chk_{rid}"):
                        try:
                            urllib.request.urlopen(tpt_url, timeout=5)
                            show_toast("success", "URL reachable")
                        except Exception:
                            show_toast("warning", "URL not reachable")
                    try:
                        st.text_input("URL", value=tpt_url, key=f"trk_url_copy_{rid}")
                    except Exception:
                        pass
                else:
                    st.write("-")
            with e:
                exp = st.expander("Edit", expanded=(rid == st.session_state.get("trk_focus_id")))
                with exp:
                    new_status = st.selectbox("Status", options=["not_started", "ready", "uploaded", "needs_update", "paused"], index=["not_started", "ready", "uploaded", "needs_update", "paused"].index(status) if status in {"not_started","ready","uploaded","needs_update","paused"} else 0, key=f"trk_status_{rid}")
                    new_date = st.text_input("Uploaded date (YYYY-MM-DD)", value=str(uploaded_date or ""), key=f"trk_date_{rid}")
                    new_url = st.text_input("TPT URL", value=tpt_url, key=f"trk_url_{rid}")
                    new_id = st.text_input("TPT Listing ID", value=str(r.get("tpt_listing_id") or ""), key=f"trk_lid_{rid}")
                    try:
                        st.text_input("Copy Listing ID", value=str(r.get("tpt_listing_id") or ""), key=f"trk_lid_copy_{rid}")
                    except Exception:
                        pass
                    new_notes = st.text_area("Notes", value=notes, height=80, key=f"trk_notes_{rid}")
                    ro1, ro2 = st.columns([1, 1])
                    with ro1:
                        if st.button("Open TPT_UPLOAD", key=f"trk_row_open_upload_{rid}"):
                            outp = output_dir_for_book(str(r.get("book_slug") or ""))
                            up = (outp / "TPT_UPLOAD") if outp else None
                            if up and up.exists():
                                open_folder(up)
                            else:
                                show_toast("info", "TPT_UPLOAD not found")
                    with ro2:
                        if st.button("Open FINAL", key=f"trk_row_open_final_{rid}"):
                            outp = output_dir_for_book(str(r.get("book_slug") or ""))
                            fi = (outp / "FINAL") if outp else None
                            if fi and fi.exists():
                                open_folder(fi)
                            else:
                                show_toast("info", "FINAL not found")
                    if st.button("Save", key=f"trk_save_{rid}"):
                        patch = {
                            "status": new_status,
                            "uploaded_date": new_date.strip() or None,
                            "tpt_url": new_url.strip() or None,
                            "tpt_listing_id": new_id.strip() or None,
                            "notes": new_notes,
                        }
                        update_tracker_record(rid, patch)
                        show_toast("success", "Saved")
                        safe_rerun()



def load_theme_titles(root: Path) -> dict:
    p = root / "theme_titles.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def write_theme_titles(root: Path, data: dict):
    p = root / "theme_titles.json"
    try:
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        show_toast("success", "Theme titles saved")
    except Exception:
        show_toast("warning", "Could not save theme_titles.json")


def decode_slug(slug: str) -> str:
    if not slug:
        return ""
    s = slug.replace("_", " ").strip()
    return s.title()


@st.cache_data(ttl=60, show_spinner=False)
def discover_books() -> list[str]:
    root = project_root()
    paths = []
    env = os.environ.get("SF_THEMES_ROOT", "").strip()
    if env:
        p = Path(env)
        if p.exists():
            paths.append(p)
    p = root / "assets" / "themes"
    if p.exists():
        paths.append(p)
    p = root / "production" / "final_products"
    if p.exists():
        paths.append(p)
    slugs: set[str] = set()
    for base in paths:
        try:
            for d in base.iterdir():
                if d.is_dir() and d.name not in {"_archive", "global"} and not d.name.startswith("."):
                    slugs.add(d.name)
        except Exception:
            pass
    # Also include slugs from canonical vocab JSON so books appear without a theme folder
    try:
        vocab_json = root / "BoardReady" / "boardready" / "vocab" / "book_vocab.json"
        if vocab_json.exists():
            data = json.loads(vocab_json.read_text(encoding="utf-8"))
            for k in list(data.keys()):
                if isinstance(k, str) and k and not k.startswith("_"):
                    slugs.add(k)
    except Exception:
        pass
    if not slugs:
        root_json = [f.stem for f in project_root().glob("*.json") if f.name not in {"global_config.json"}]
        for s in root_json:
            if s:
                slugs.add(s)
    return sorted(slugs)


_display_map_cache: tuple[float, dict] | None = None


def get_display_map(slugs: list[str], titles_map: dict) -> dict:
    global _display_map_cache
    # Cache key: tuple of slugs + titles_map content
    _cache_key = (tuple(slugs), tuple(sorted(titles_map.items())))
    if _display_map_cache is not None:
        _prev_key, _prev_map = _display_map_cache
        if _prev_key == _cache_key:
            return _prev_map
    disp = {}
    for s in slugs:
        profile = load_project_profile(s)
        disp[s] = titles_map.get(s) or profile.get("title") or decode_slug(s)
    _display_map_cache = (_cache_key, disp)
    return disp


def project_profile_path(slug: str) -> Path | None:
    book_dir = find_book_dir(slug)
    return (book_dir / "config" / "project_profile.json") if book_dir else None


def default_project_profile(slug: str, title: str | None = None) -> dict:
    is_topic = str(slug).startswith("topic_")
    return {
        "schema_version": 1,
        "slug": slug,
        "title": title or decode_slug(slug),
        "pathway": "topic" if is_topic else "book_companion",
        "topic": (title or decode_slug(slug)) if is_topic else "",
        "age_band": "Years 7–10 (teen SPED)" if is_topic else "Book-dependent",
        "instructional_reading_level": "Emergent to functional literacy",
        "communication_modes": ["Speech", "AAC", "Pointing"],
        "support_level": "Differentiated",
        "learning_targets": [],
        "curriculum_framework": "",
        "sensitive_content": False,
        "sensitive_review_notes": "",
        "seed_keywords": [],
        "content_review": {"status": "pending" if is_topic else "grandfathered"},
        "boardready_review": {"status": "pending" if is_topic else "grandfathered"},
    }


_profile_cache: dict[str, tuple[float, dict]] = {}


def load_project_profile(slug: str) -> dict:
    path = project_profile_path(slug)
    if path and path.exists():
        try:
            mtime = path.stat().st_mtime
        except Exception:
            mtime = 0
        cached = _profile_cache.get(slug)
        if cached and cached[0] == mtime:
            return cached[1]
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                result = {**default_project_profile(slug), **data}
                _profile_cache[slug] = (mtime, result)
                return result
        except Exception:
            pass
    return default_project_profile(slug)


def save_project_profile(slug: str, profile: dict) -> bool:
    path = project_profile_path(slug)
    if path is None:
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
        _profile_cache.pop(slug, None)
        clear_workflow_gate_cache(slug)
        clear_stage_caches(slug)
        return True
    except Exception:
        return False


def validate_project_profile(profile: dict) -> list[str]:
    errors = []
    if profile.get("pathway") not in {"topic", "book_companion", "teen_dignity"}:
        errors.append("Choose a supported project pathway")
    for key, label in (("title", "title"), ("age_band", "age band"), ("instructional_reading_level", "instructional reading level"), ("support_level", "support level")):
        if not str(profile.get(key) or "").strip():
            errors.append(f"Enter a {label}")
    if not profile.get("communication_modes"):
        errors.append("Choose at least one communication mode")
    if profile.get("pathway") in {"topic", "teen_dignity"} and not str(profile.get("topic") or "").strip():
        errors.append("Enter a topic or student interest")
    if profile.get("sensitive_content") and not str(profile.get("sensitive_review_notes") or "").strip():
        errors.append("Add safeguarding notes for sensitive content")
    return errors


_workflow_gate_cache: dict[str, dict] = {}


def workflow_gate_status(slug: str) -> dict:
    cached = _workflow_gate_cache.get(slug)
    if cached is not None:
        return cached
    profile = load_project_profile(slug)
    strict = profile.get("pathway") in {"topic", "teen_dignity"} or str(slug).startswith("topic_")
    vocab_pending = book_vocab_review_required(slug)
    result = {
        "strict": strict,
        "setup": not validate_project_profile(profile),
        "content": not vocab_pending and ((not strict) or (profile.get("content_review") or {}).get("status") == "approved"),
        "boardready": (not strict) or (profile.get("boardready_review") or {}).get("status") == "approved",
        "profile": profile,
    }
    _workflow_gate_cache[slug] = result
    return result


def clear_workflow_gate_cache(slug: str | None = None) -> None:
    if slug:
        _workflow_gate_cache.pop(slug, None)
    else:
        _workflow_gate_cache.clear()


def create_topic_project(profile: dict) -> tuple[bool, str, str | None]:
    topic = str(profile.get("topic") or profile.get("title") or "").strip()
    slug = "topic_" + re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")
    if slug == "topic_":
        return False, "Enter a valid topic name.", None
    root = Path(os.environ.get("SF_THEMES_ROOT", "").strip() or (project_root() / "assets" / "themes"))
    book_dir = root / slug
    if book_dir.exists():
        return False, f"A project named {slug} already exists.", slug
    try:
        (book_dir / "config").mkdir(parents=True)
        data = {**default_project_profile(slug, topic), **profile, "slug": slug, "title": topic, "topic": topic, "pathway": "topic", "created_at": datetime.now().isoformat(timespec="seconds")}
        (book_dir / "config" / "project_profile.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        (book_dir / "book_vocab.json").write_text(json.dumps({"schema_version": 1, "slug": slug, "title": topic, "fringe_12": [], "activity_images": []}, ensure_ascii=False, indent=2), encoding="utf-8")
        return True, f"Created {topic}. Review setup, then generate the grounded content draft.", slug
    except Exception as exc:
        return False, f"Could not create topic: {exc}", None


def topic_content_ready(slug: str) -> bool:
    book_dir = find_book_dir(slug)
    if not book_dir:
        return False
    path = book_dir / "book_vocab.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        meaningful = [key for key, value in data.items() if key not in {"schema_version", "slug", "title"} and value]
        return len(meaningful) >= 2
    except Exception:
        return False


def run_topic_content_builder(slug: str) -> tuple[bool, str]:
    profile = load_project_profile(slug)
    if profile.get("pathway") not in {"topic", "teen_dignity"}:
        return False, "Grounded topic generation is only used for topic pathways."
    errors = validate_project_profile(profile)
    if errors:
        return False, "; ".join(errors)
    book_dir = find_book_dir(slug)
    script = project_root() / "Studioforge" / "TOPIC_CONTENT_BUILDER.py"
    if not book_dir or not script.exists():
        return False, "Topic builder or project folder was not found."
    keywords = ", ".join(str(value) for value in profile.get("seed_keywords", []) if str(value).strip())
    command = [sys.executable, str(script), "--topic", str(profile.get("topic")), "--slug", slug, "--themes-root", str(book_dir.parent)]
    if keywords:
        command.extend(["--keywords", keywords])
    try:
        result = subprocess.run(command, cwd=str(script.parent), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    except Exception as exc:
        return False, f"Topic generation failed: {exc}"
    if result.returncode != 0 or not topic_content_ready(slug):
        detail = (result.stderr or result.stdout or "No grounded content was produced.").strip()
        return False, detail[-2000:]
    vocab_path = book_dir / "book_vocab.json"
    try:
        vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
        if not vocab.get("fringe_12"):
            raw_fringe = vocab.get("aac_fringe_vocab") or []
            fringe = []
            for item in raw_fringe:
                value = item.get("value") if isinstance(item, dict) else item
                if str(value or "").strip():
                    fringe.append(str(value).strip())
            vocab["fringe_12"] = list(dict.fromkeys(fringe))[:12]
        vocab.setdefault("slug", slug)
        vocab.setdefault("title", profile.get("title"))
        vocab_path.write_text(json.dumps(vocab, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    profile["content_review"] = {"status": "pending", "generated_at": datetime.now().isoformat(timespec="seconds")}
    profile["boardready_review"] = {"status": "pending", "reason": "Content draft regenerated"}
    save_project_profile(slug, profile)
    return True, "Grounded draft created. Complete the human content review next."


VOCAB_FOCUS_MANIFEST = "september_2026_sped_book_focus.json"
VOCAB_REVIEW_FILENAME = "needs_review_vocab.json"
VOCAB_BLOCKED_WORDS = {
    "between", "there", "here", "under", "over", "above", "below", "next to", "behind", "in front of", "through", "around", "across", "beside", "inside", "outside", "near", "far", "up", "down", "and", "but", "or", "nor", "so", "yet", "the", "a", "an", "it", "this", "that", "these", "those", "he", "she", "they", "we", "me", "him", "her", "them", "us", "my", "your", "his", "their", "our", "of", "to", "for", "with", "at", "by", "on", "in", "from", "as", "if", "is", "am", "are", "was", "were", "be", "been", "being", "has", "had", "does", "did", "can", "could", "would", "should", "will", "i", "you", "want", "see", "yes", "no", "same", "different", "more", "help", "like", "don't like", "dont like", "go", "stop", "choose", "colour", "color", "read", "think", "uh oh", "what", "where", "why", "i don't know", "i dont know", "don't know", "dont know", "finished", "thing", "things", "stuff", "something", "anything", "everything", "feel", "feeling", "good", "nice", "fun", "idea", "way", "time", "do", "make", "get", "have", "very", "really", "special",
}


def vocab_focus_manifest_path() -> Path:
    return project_root() / "assets" / "config" / VOCAB_FOCUS_MANIFEST


def load_vocab_focus_records() -> list[dict]:
    data = _read_json_safe(vocab_focus_manifest_path(), {})
    records = data.get("focus_books") if isinstance(data, dict) else []
    return [record for record in records if isinstance(record, dict) and str(record.get("slug") or "").strip()]


def book_vocab_review_required(slug: str) -> bool:
    book_dir = find_book_dir(slug)
    data = _read_json_safe(book_dir / "book_vocab.json", {}) if book_dir else {}
    return data.get("status") == "demand_candidate" and data.get("vocab_status") != "human_approved"


def run_vocab_builder_command(arguments: list[str], timeout: int = 1800) -> tuple[bool, str]:
    script = project_root() / "AAC_VOCAB_BUILDER.py"
    if not script.exists():
        return False, "AAC vocabulary builder was not found at the repository root."
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        result = subprocess.run([sys.executable, str(script), *arguments], cwd=str(project_root()), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
    except Exception as exc:
        return False, f"Vocabulary builder failed: {exc}"
    output = "\n".join(value.strip() for value in (result.stdout, result.stderr) if value and value.strip())
    return result.returncode == 0, output[-5000:] or ("Vocabulary operation completed." if result.returncode == 0 else "Vocabulary operation failed.")


def _clean_vocab_word(value) -> str:
    return " ".join(str(value or "").strip().lower().replace("’", "'").split())


def vocab_review_issues(data: dict) -> list[str]:
    issues = []
    hero = data.get("hero") if isinstance(data.get("hero"), dict) else {}
    hero_name = str(hero.get("name") or "").strip()
    words = data.get("fringe_11") if isinstance(data.get("fringe_11"), list) else []
    cleaned = [_clean_vocab_word(word) for word in words]
    if not str(data.get("title") or "").strip():
        issues.append("Confirm the book title.")
    if not str(data.get("author") or "").strip() or str(data.get("author")).strip().casefold() == "unknown":
        issues.append("Confirm the author.")
    if not str(data.get("pub_year") or "").strip():
        issues.append("Confirm the publication year.")
    if len(str(data.get("book_summary") or "").strip()) < 40:
        issues.append("Add a specific grounded book summary.")
    if not hero_name:
        issues.append("Choose a recognisable hero or central subject.")
    if len(words) != 11 or any(not value for value in cleaned):
        issues.append("Provide exactly 11 non-blank fringe words.")
    if len(cleaned) != len(set(cleaned)):
        issues.append("Remove duplicate fringe words.")
    blocked = [str(word) for word, value in zip(words, cleaned) if value in VOCAB_BLOCKED_WORDS]
    if blocked:
        issues.append("Replace unsuitable core, function, positional, or vague words: " + ", ".join(blocked))
    if data.get("fringe_12") != [hero_name] + words:
        issues.append("The twelve-word board must contain the hero followed by the eleven fringe words.")
    justifications = data.get("fringe_justifications") if isinstance(data.get("fringe_justifications"), dict) else {}
    search_terms = data.get("icon_search_terms") if isinstance(data.get("icon_search_terms"), dict) else {}
    for word in words:
        justification = " ".join(str(justifications.get(word) or "").strip().split())
        if len(justification) < 20 or any(phrase in justification.casefold() for phrase in ("important in the story", "used throughout the book", "used in the story")):
            issues.append(f"Add a story-specific justification for '{word}'.")
        if not str(search_terms.get(word) or "").strip():
            issues.append(f"Add a concrete icon search term for '{word}'.")
    if data.get("grounded") is not True:
        issues.append("Regenerate or verify the draft because it is not grounded.")
    try:
        searches_used = int(data.get("searches_used", 0))
    except (TypeError, ValueError):
        searches_used = 0
    if searches_used < 1:
        issues.append("The generator must record at least one grounding search.")
    return list(dict.fromkeys(issues))


def _vocab_queue_status(slug: str) -> str:
    book_dir = find_book_dir(slug)
    if not book_dir:
        return "Theme missing"
    vocab = _read_json_safe(book_dir / "book_vocab.json", {})
    if vocab.get("vocab_status") == "human_approved":
        return "Human approved"
    if (book_dir / VOCAB_REVIEW_FILENAME).exists():
        return "Review draft ready"
    fringe_12 = vocab.get("fringe_12") if isinstance(vocab.get("fringe_12"), list) else []
    fringe_11 = vocab.get("fringe_11") if isinstance(vocab.get("fringe_11"), list) else fringe_12[1:]
    if not fringe_12:
        return "Needs vocabulary"
    if len(fringe_11) < 11:
        missing = 11 - len(fringe_11)
        return f"Needs {missing} more {'word' if missing == 1 else 'words'}"
    if len(fringe_11) > 11:
        extra = len(fringe_11) - 11
        return f"Remove {extra} extra {'word' if extra == 1 else 'words'}"
    blocked = [str(word) for word in fringe_11 if _clean_vocab_word(word) in VOCAB_BLOCKED_WORDS]
    if blocked:
        return "Replace unsuitable: " + ", ".join(blocked[:3])
    justifications = vocab.get("fringe_justifications") if isinstance(vocab.get("fringe_justifications"), dict) else {}
    search_terms = vocab.get("icon_search_terms") if isinstance(vocab.get("icon_search_terms"), dict) else {}
    if any(not str(justifications.get(word) or "").strip() or not str(search_terms.get(word) or "").strip() for word in fringe_11):
        return "Guardrail refresh recommended"
    return "Existing vocab - human review needed"


def render_vocabulary_queue(slug: str):
    records = load_vocab_focus_records()
    if not records:
        return
    with st.expander("September vocabulary queue", expanded=book_vocab_review_required(slug)):
        st.caption("Generate missing drafts as a controlled batch. To refresh an existing book with missing, extra, or unsuitable words, open that book and generate a guarded review draft. Nothing is replaced until one book is reviewed and approved.")
        st.dataframe([{"Rank": record.get("rank"), "Book": record.get("title"), "Status": _vocab_queue_status(str(record.get("slug")))} for record in records], hide_index=True, use_container_width=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Check identities for missing books", key=f"vocab_identity_batch_{slug}", use_container_width=True):
                with st.spinner("Checking titles, authors, and summaries..."):
                    ok, message = run_vocab_builder_command(["--focus-file", str(vocab_focus_manifest_path()), "--missing-only", "--identity-check"])
                show_toast("success" if ok else "error", "Identity check completed." if ok else message)
                if message:
                    st.code(message)
        with c2:
            if st.button("Generate drafts for missing books", type="primary", key=f"vocab_generate_batch_{slug}", use_container_width=True):
                with st.spinner("Generating grounded vocabulary drafts. Real vocabulary will not be changed..."):
                    ok, message = run_vocab_builder_command(["--focus-file", str(vocab_focus_manifest_path()), "--missing-only"])
                show_toast("success" if ok else "error", "Vocabulary drafts generated. Review each book separately." if ok else message)
                if message:
                    st.code(message)
                if ok:
                    safe_rerun()
        identity_report = project_root() / "AAC_IDENTITY_CHECK.md"
        if identity_report.exists():
            with st.expander("Latest identity-check report"):
                st.markdown(identity_report.read_text(encoding="utf-8"))

    book_dir = find_book_dir(slug)
    if not book_dir:
        return
    vocab_path = book_dir / "book_vocab.json"
    review_path = book_dir / VOCAB_REVIEW_FILENAME
    canonical = _read_json_safe(vocab_path, {})
    st.markdown("#### Book vocabulary")
    if canonical.get("vocab_status") == "human_approved":
        st.success("This book's grounded vocabulary has been human approved.")
    elif canonical.get("fringe_12"):
        st.info("This book has existing vocabulary. You can create a fresh guarded review draft without replacing it.")
    else:
        st.warning("This candidate cannot move to icon review until its vocabulary draft is generated and approved.")
    generate_label = "Regenerate guarded review draft" if review_path.exists() or canonical.get("fringe_12") else "Generate guarded review draft"
    if st.button(generate_label, key=f"generate_vocab_{slug}"):
        arguments = ["--book", slug]
        if review_path.exists() or canonical.get("fringe_12"):
            arguments.append("--overwrite")
        with st.spinner("Researching the book and generating a review draft..."):
            ok, message = run_vocab_builder_command(arguments)
        show_toast("success" if ok else "error", "Review draft generated." if ok else message)
        if message:
            st.code(message)
        if ok:
            safe_rerun()
    if not review_path.exists():
        return

    review = _read_json_safe(review_path, {})
    st.warning("Draft only: inspect the identity, every word, justification, ambiguity, and icon search term before approval.")
    st.caption(f"Grounded: {'Yes' if review.get('grounded') is True else 'No'} | Searches recorded: {review.get('searches_used', 0)}")
    with st.form(f"vocab_review_form_{slug}"):
        title = st.text_input("Confirmed book title", value=str(review.get("title") or canonical.get("title") or ""))
        author = st.text_input("Confirmed author", value=str(review.get("author") or canonical.get("author") or ""))
        pub_year = st.text_input("First publication year", value=str(review.get("pub_year") or ""))
        summary = st.text_area("Grounded plot summary", value=str(review.get("book_summary") or ""), height=120)
        hero = review.get("hero") if isinstance(review.get("hero"), dict) else {}
        hero_name = st.text_input("Hero or central subject", value=str(hero.get("name") or ""))
        hero_search = st.text_input("Hero icon search term", value=str(hero.get("search_term") or ""))
        hero_needs_sourcing = st.checkbox("Hero needs a separately licensed or approved visual", value=bool(hero.get("needs_sourcing")))
        words = review.get("fringe_11") if isinstance(review.get("fringe_11"), list) else []
        justifications = review.get("fringe_justifications") if isinstance(review.get("fringe_justifications"), dict) else {}
        search_terms = review.get("icon_search_terms") if isinstance(review.get("icon_search_terms"), dict) else {}
        rows = []
        for index in range(11):
            word = str(words[index]) if index < len(words) else ""
            rows.append({"Word": word, "Icon search term": str(search_terms.get(word) or ""), "Why it belongs in this book": str(justifications.get(word) or "")})
        edited = st.data_editor(rows, hide_index=True, num_rows="fixed", use_container_width=True, key=f"vocab_rows_{slug}")
        edited_rows = edited.to_dict(orient="records") if hasattr(edited, "to_dict") else list(edited)
        edited_words = [str(row.get("Word") or "").strip() for row in edited_rows]
        edited_data = dict(review)
        edited_data.update({
            "title": title.strip(),
            "author": author.strip(),
            "pub_year": pub_year.strip(),
            "book_summary": summary.strip(),
            "hero": {**hero, "name": hero_name.strip(), "search_term": hero_search.strip(), "needs_sourcing": hero_needs_sourcing},
            "fringe_11": edited_words,
            "fringe_12": [hero_name.strip()] + edited_words,
            "fringe_justifications": {word: str(row.get("Why it belongs in this book") or "").strip() for word, row in zip(edited_words, edited_rows) if word},
            "icon_search_terms": {word: str(row.get("Icon search term") or "").strip() for word, row in zip(edited_words, edited_rows) if word},
            "activity_images": edited_words[:6],
            "aac_extras": edited_words[6:],
            "vocab_status": "pending_human_review",
        })
        issues = vocab_review_issues(edited_data)
        edited_data["guardrail_warnings"] = [] if not issues else issues
        if issues:
            st.error("Resolve before approval:\n- " + "\n- ".join(issues))
        if review.get("ambiguous"):
            with st.expander("Ambiguous words flagged by the generator"):
                st.json(review.get("ambiguous"))
        confirmed = st.checkbox("I checked the book identity, concrete word meanings, story-specific reasons, icon searches, ambiguities, and rights warnings.")
        save_col, approve_col = st.columns(2)
        with save_col:
            save_clicked = st.form_submit_button("Save review edits", use_container_width=True)
        with approve_col:
            approve_clicked = st.form_submit_button("Approve this vocabulary", type="primary", disabled=bool(issues) or not confirmed, use_container_width=True)
    if save_clicked or approve_clicked:
        edited_data["review_edited_at"] = datetime.now().isoformat(timespec="seconds")
        review_path.write_text(json.dumps(edited_data, ensure_ascii=False, indent=2), encoding="utf-8")
    if save_clicked:
        show_toast("success", "Vocabulary review edits saved. Canonical vocabulary was not changed.")
        safe_rerun()
    if approve_clicked:
        edited_data["human_review"] = {"status": "approved", "reviewed_at": datetime.now().isoformat(timespec="seconds"), "reviewer": "human"}
        review_path.write_text(json.dumps(edited_data, ensure_ascii=False, indent=2), encoding="utf-8")
        ok, message = run_vocab_builder_command(["--promote", slug], timeout=120)
        promoted = _read_json_safe(vocab_path, {})
        if ok and promoted.get("vocab_status") == "human_approved":
            show_toast("success", "Vocabulary approved and promoted. Continue to icon review.")
            safe_rerun()
        else:
            show_toast("error", message or "Promotion was refused by the vocabulary guardrails.")


def content_review_checks(profile: dict) -> list[tuple[str, str]]:
    checks = [
        ("accuracy", "Facts and teaching content are accurate and supported by the recorded sources."),
        ("dignity", "Language and visuals respect the chronological age and access needs of learners."),
        ("safety", "Safety, safeguarding, and implementation guidance are appropriate."),
        ("copyright", "Copyrighted text, images, trademarks, and licensing have been checked."),
        ("curriculum", "Curriculum and educational claims are specific and not overstated."),
        ("iep", "Any IEP or progress-monitoring wording matches the actual activity and contains no fabricated criteria."),
        ("flagged", "Items in needs_review.json have been amended or will remain excluded from production."),
    ]
    if profile.get("sensitive_content"):
        checks.append(("safeguarding", "A human safeguarding review has been completed for this sensitive topic."))
    return checks


def topic_fringe_words(slug: str) -> list[str]:
    _path, data = theme_vocab_source(slug)
    raw = data.get("fringe_12") or data.get("aac_fringe_vocab") or []
    words = []
    for item in raw:
        value = item.get("value") if isinstance(item, dict) else item
        text = str(value or "").strip()
        if text and text.casefold() not in {word.casefold() for word in words}:
            words.append(text)
    return words[:12]


def boardready_output_files(slug: str) -> list[Path]:
    book_dir = find_book_dir(slug)
    if not book_dir:
        return []
    roots = [book_dir / "aac_boards", book_dir / "OUTPUT"]
    files = []
    for root in roots:
        if root.exists():
            files.extend(path for path in root.rglob("*.pdf") if path.is_file() and any(token in path.name.lower() for token in ("aac", "board", "highvis")))
    return list(dict.fromkeys(files))


def run_boardready_generator(slug: str) -> tuple[bool, str]:
    images = images_dir_for_book(slug)
    if not images:
        return False, "The topic image folder is unavailable."
    if len(topic_fringe_words(slug)) != 12:
        return False, "BoardReady requires exactly 12 reviewed fringe words."
    try:
        module = importlib.import_module("Studioforge._TRUTH.AAC_BOARD")
        ok = bool(module.generate_aac_board_pack(str(images), default_pack_code(slug), load_project_profile(slug).get("title") or decode_slug(slug)))
    except Exception as exc:
        return False, f"BoardReady generation failed: {exc}"
    outputs = boardready_output_files(slug)
    return (True, f"BoardReady generated {len(outputs)} PDF file(s).") if ok and outputs else (False, "BoardReady did not produce a detectable PDF output.")


def show_toast(kind: str, msg: str, duration: int | None = None):
    if kind == "error":
        st.error(msg)
    elif kind == "warning":
        st.warning(msg)
    elif hasattr(st, "toast"):
        st.toast(msg)
    elif kind == "success":
        st.success(msg)
    else:
        st.info(msg)


# Compatibility helpers for Streamlit query params and rerun
def qp_get(name: str) -> str | None:
    try:
        if hasattr(st, "query_params"):
            val = st.query_params.get(name)
            if isinstance(val, list):
                return val[0] if val else None
            return val
        else:
            qp = st.experimental_get_query_params()
            lst = qp.get(name, [None])
            return lst[0]
    except Exception:
        return None


ICON_SUGGEST_SCORE = 0.55
ICON_AUTO_ACCEPT_SCORE = 0.85


def symbols_root() -> Path:
    env = os.environ.get("SF_SYMBOLS_ROOT", "").strip()
    if env and Path(env).exists():
        return Path(env)
    # Prefer the expanded symbol library if present
    expanded = project_root() / "assets" / "symbols" / "png"
    if expanded.exists():
        return expanded
    return project_root() / "assets" / "symbols"


@st.cache_data(ttl=600, show_spinner=False)
def _cached_library_pngs(_root_str: str) -> list[str]:
    """Cache the list of all PNG paths under the symbol library.
    Keyed by the root path string (and TTL) so it refreshes every 10 min.
    Returns list of string paths to avoid Path hashing issues.
    """
    root = Path(_root_str)
    return [str(p) for p in root.rglob("*.png")]


def library_png_paths() -> list[Path]:
    """Return cached list of all PNG paths in the symbol library."""
    return [Path(p) for p in _cached_library_pngs(str(symbols_root()))]


def clear_library_png_cache() -> None:
    _cached_library_pngs.clear()


def icon_labeler_url(path: str = "/", slug: str | None = None, port: int = 5053) -> str:
    route = "/" + str(path or "/").strip("/") if str(path or "/").strip("/") else "/"
    query = f"?book={urllib.parse.quote(str(slug))}" if slug else ""
    return f"http://127.0.0.1:{int(port)}{route}{query}"


def icon_labeler_is_running(port: int = 5053) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{int(port)}/api/ping", timeout=0.5) as response:
            return int(getattr(response, "status", 200)) == 200
    except Exception:
        return False


def ensure_icon_labeler_running(port: int = 5053) -> tuple[bool, str]:
    if icon_labeler_is_running(port):
        return True, "Icon Labeller is ready."
    script = project_root() / "Studioforge" / "ICON_LABELER.py"
    if not script.exists():
        return False, f"Icon Labeller entrypoint not found: {script}"
    python = project_root() / ".venv" / "Scripts" / "python.exe"
    if not python.exists():
        python = Path(sys.executable)
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        subprocess.Popen([str(python), str(script), str(int(port))], cwd=str(script.parent), creationflags=flags)
    except Exception as exc:
        return False, f"Could not start Icon Labeller: {exc}"
    for _ in range(30):
        if icon_labeler_is_running(port):
            return True, "Icon Labeller started."
        time.sleep(0.2)
    return False, "Icon Labeller did not become ready."


def parse_vocab_for_slug(slug: str) -> list[str]:
    """Parse assets/ALL_BOOKS_VOCAB_MASTER.md and return Essential vocab tokens for the slug.
    Falls back to nearest heading match by canonical token set (ignores stopwords like 'the').
    """
    md = (project_root() / "assets" / "ALL_BOOKS_VOCAB_MASTER.md")
    if not md.exists():
        return []
    try:
        text = md.read_text(encoding="utf-8", errors="ignore")
        # Collect all section headings of form '### slug'
        heads = [(m.start(), m.end(), m.group(1)) for m in re.finditer(r"^###\s+([a-z0-9_]+)\s*$", text, re.MULTILINE | re.IGNORECASE)]
        if not heads:
            return []
        def canon(s: str) -> set[str]:
            stop = {"the","a","an","to","and","of","on","in","at","my","your","our","is","are"}
            toks = [t for t in _tokenize(s).split("_") if t and t not in stop]
            return set(toks)
        want = canon(slug)
        # Try exact
        target_idx = None
        for i, (_, _, name) in enumerate(heads):
            if name == slug:
                target_idx = i
                break
        # Fuzzy by token overlap
        if target_idx is None:
            best_i, best_score = None, -1
            for i, (_, _, name) in enumerate(heads):
                score = len(want & canon(name))
                if score > best_score:
                    best_score = score
                    best_i = i
            target_idx = best_i
        if target_idx is None:
            return []
        start = heads[target_idx][1]
        # slice until next heading or end
        end = heads[target_idx + 1][0] if (target_idx + 1 < len(heads)) else len(text)
        sect = text[start:end]
        # Find Essential line
        em = re.search(r"\*\*Essential:\*\*\s*(.+)", sect)
        if not em:
            return []
        payload = em.group(1).strip()
        payload = payload.splitlines()[0]
        raw = [t.strip() for t in re.split(r",|/|;|\||-", payload)]
        toks = [t for t in raw if t]
        return toks[:80]
    except Exception:
        return []


def _tokenize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def sanitise_symbol_name(raw: str) -> str:
    """Convert any label to a valid symbol filename stem (lowercase underscore style)."""
    s = str(raw or "").strip().lower()
    s = s.replace("'", "")
    s = s.replace("-", "_")
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", "_", s)
    return s.strip("_")


def icon_candidates_for_word(word: str, slug: str, limit: int = 6) -> list[dict]:
    terms = []
    try:
        _source, vocab = theme_vocab_source(slug)
        configured = (vocab.get("icon_search_terms") or {}).get(word)
        if isinstance(configured, list):
            terms.extend(str(value).strip() for value in configured if str(value).strip())
        elif configured:
            terms.append(str(configured).strip())
    except Exception:
        pass
    terms.append(str(word).strip())
    terms = list(dict.fromkeys(term.casefold() for term in terms if term))
    if icon_qa_logic is not None:
        try:
            # Use cached library labels for speed (avoids re-scanning 14k PNGs)
            labelled_paths, _configured = _cached_library_labels(slug)
            scored = []
            for path_str, label in labelled_paths:
                score = max((icon_qa_logic._score_label(label, term) for term in terms), default=0.0)
                if score > 0:
                    scored.append({"label": label, "path": path_str, "score": round(float(score), 4)})
            scored.sort(key=lambda item: float(item.get("score", 0)), reverse=True)
            return scored[:limit]
        except Exception:
            pass
    match = find_symbol_for_word(word, slug)
    return [{"label": match.stem, "path": str(match), "score": 1.0}] if match else []


@st.cache_data(ttl=600, show_spinner=False)
def _cached_library_labels(slug: str) -> tuple[tuple[tuple[str, str], ...], dict]:
    """Scan the icon library once per session and cache the labelled paths.
    Returns (labelled_paths_tuple, configured_terms) so the scoring loop
    doesn't need to re-scan 14k+ PNGs on every page rerun.
    """
    if icon_qa_logic is None:
        return (), {}
    try:
        shared_paths = icon_qa_logic._library_paths(slug)
    except Exception:
        shared_paths = None
    _source, vocab = theme_vocab_source(slug)
    configured_terms = vocab.get("icon_search_terms") or {}
    labelled_paths = []
    seen_paths = set()
    try:
        banned = icon_qa_logic._banned_set()
    except Exception:
        banned = set()
    for path in shared_paths or []:
        path_key = str(path)
        if path_key in seen_paths:
            continue
        seen_paths.add(path_key)
        try:
            if icon_qa_logic._is_banned(path, banned):
                continue
            labelled_paths.append((str(path), icon_qa_logic._filename_label(path)))
        except Exception:
            continue
    return tuple(labelled_paths), configured_terms


@st.cache_data(ttl=300, show_spinner=False)
def cached_icon_candidate_map(slug: str, words: tuple[str, ...], limit: int = 5) -> dict[str, list[dict]]:
    if icon_qa_logic is None:
        return {word: icon_candidates_for_word(word, slug, limit) for word in words}
    labelled_paths, configured_terms = _cached_library_labels(slug)
    results: dict[str, list[dict]] = {}
    for word in words:
        configured = configured_terms.get(word) if isinstance(configured_terms, dict) else None
        terms = list(configured) if isinstance(configured, list) else ([configured] if configured else [])
        terms.append(word)
        terms.extend(token for token in re.split(r"[^a-z0-9]+", word.casefold()) if len(token) >= 3)
        terms = list(dict.fromkeys(str(term).strip().casefold() for term in terms if str(term).strip()))
        scored = []
        for path_str, label in labelled_paths:
            score = max((icon_qa_logic._score_label(label, term) for term in terms), default=0.0)
            if score > 0:
                scored.append((float(score), path_str, label))
        scored.sort(key=lambda item: item[0], reverse=True)
        results[word] = [{"label": label, "path": path_str, "score": round(score, 4)} for score, path_str, label in scored[:limit]]
    return results


def clear_icon_candidate_cache() -> None:
    try:
        cached_icon_candidate_map.clear()
    except Exception:
        pass
    try:
        _cached_library_labels.clear()
    except Exception:
        pass
    try:
        clear_library_png_cache()
    except Exception:
        pass


def quarantine_library_icon(path: str) -> tuple[bool, str, str | None]:
    try:
        source = Path(path).resolve()
        library = symbols_root().resolve()
        source.relative_to(library)
    except Exception:
        return False, "Only images in the shared PNG library can be quarantined.", None
    if not source.is_file():
        return False, "The library image no longer exists.", None
    try:
        if icon_qa_logic is not None:
            icon_qa_logic.add_to_banlist(str(source))
        quarantine = project_root() / "Studioforge" / "_QUARANTINE" / "icons"
        quarantine.mkdir(parents=True, exist_ok=True)
        destination = quarantine / source.name
        if destination.exists():
            destination = quarantine / f"{source.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{source.suffix}"
        shutil.move(str(source), str(destination))
        if icon_qa_logic is not None:
            try:
                icon_qa_logic._PNG_DIR_CACHE.clear()
            except Exception:
                pass
        clear_icon_candidate_cache()
        return True, f"Quarantined {source.name}", str(destination)
    except Exception as exc:
        return False, f"Could not quarantine {source.name}: {exc}", None


def icon_word_decision(slug: str, word: str) -> dict:
    state = read_book_state(slug)
    stored = (state.get("icon_decisions") or {}).get(word, {})
    result = dict(stored) if isinstance(stored, dict) else {}
    if icon_qa_logic is not None:
        try:
            qa = icon_qa_logic.load_qa_log()
            words = ((qa.get(slug) or {}).get("words") or {}) if isinstance(qa, dict) else {}
            external = words.get(word, {}) if isinstance(words.get(word), dict) else {}
            status = str(external.get("status") or "").lower()
            if status in {"keep", "kept", "replaced"}:
                result.setdefault("status", "approved")
                result.setdefault("source_path", external.get("path"))
            elif status == "skip":
                result["status"] = "skipped"
            elif status == "missing" and not result:
                result["status"] = "missing"
        except Exception:
            pass
    return result


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
            icon_qa_logic.save_decision(slug, word, mapped, current.get("source_path"))
        except Exception:
            pass


def _reset_icon_decision(slug: str, icon_stem: str) -> None:
    """Reset the icon decision for a word so it reappears in the review list.
    Tries to match the icon stem to a vocabulary word via the decisions dict."""
    state = read_book_state(slug)
    decisions = state.get("icon_decisions") or {}
    # Find any decision whose filename matches this stem
    target_word = None
    for word, info in decisions.items():
        if not isinstance(info, dict):
            continue
        fname = str(info.get("filename") or "")
        if fname.replace(".png", "").casefold() == icon_stem.casefold():
            target_word = word
            break
    if target_word:
        decisions[target_word] = {
            "status": "pending",
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        state["icon_decisions"] = decisions
        write_book_state(slug, state)
        # Also clear the vocab state so the word shows up again
        vkey = vocab_state_key(slug)
        if vkey in st.session_state:
            st.session_state[vkey]["skipped"].discard(target_word)
    else:
        # No matching decision found — just clear the kit entry
        state["icon_decisions"] = decisions
        write_book_state(slug, state)


def _ban_icon_from_library(path: str) -> None:
    """Ban an icon from the shared library so it won't appear in future searches."""
    try:
        ok, _message, _destination = quarantine_library_icon(str(path))
        if not ok:
            # If quarantine fails, try adding to banlist directly
            if icon_qa_logic is not None:
                icon_qa_logic.add_to_banlist(str(path))
    except Exception:
        pass


_accepted_icon_cache: dict[str, dict[str, Path | None]] = {}


def accepted_icon_for_word(slug: str, word: str) -> Path | None:
    # Per-render cache: avoid 4× calls per word doing glob() each time
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
    # Removed the base.glob("*.*") fallback — it scanned the entire activity_images
    # directory for every word on every call (4× per word per render).
    # Icons are approved via accept_icon_candidate which sets filename in state.
    _accepted_icon_cache.setdefault(slug, {})[word] = None
    return None


def clear_accepted_icon_cache(slug: str | None = None) -> None:
    if slug:
        _accepted_icon_cache.pop(slug, None)
    else:
        _accepted_icon_cache.clear()


def accept_icon_candidate(slug: str, word: str, source_path: str, target_label: str | None = None) -> tuple[bool, str]:
    source = Path(source_path)
    if not source.is_file():
        return False, "The selected icon is no longer available."
    label = str(target_label or word).strip()
    filename = f"{sanitise_symbol_name(label)}.png"
    if filename == ".png":
        return False, "Enter a valid icon label."
    destination_dir = images_dir_for_book(slug)
    if destination_dir is None:
        return False, "The book image folder is unavailable."
    destination = destination_dir / filename
    try:
        if source.resolve() != destination.resolve():
            image = Image.open(str(source)).convert("RGBA")
            image.save(str(destination), "PNG")
        normalize_icon_file(destination, target_px=512, margin=0.06, white_cutoff=245)
        state = read_book_state(slug)
        decisions = state.setdefault("icon_decisions", {})
        decisions[word] = {
            "status": "approved",
            "filename": filename,
            "label": label,
            "source_path": str(source.resolve()),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        kit_names = list(dict.fromkeys([*(state.get("icons_kit") or []), filename]))
        state["icons_kit"] = kit_names
        if not state.get("hero_icon"):
            state["hero_icon"] = filename
        write_book_state(slug, state)
        profile = load_project_profile(slug)
        if profile.get("pathway") in {"topic", "teen_dignity"}:
            profile["boardready_review"] = {"status": "pending", "reason": "Topic icon changed"}
            save_project_profile(slug, profile)
        if icon_qa_logic is not None:
            try:
                icon_qa_logic.save_decision(slug, word, "replaced", str(destination.resolve()))
            except Exception:
                pass
        kit_key = get_kit_key(slug)
        current = [str(Path(path)) for path in st.session_state.get(kit_key, [])]
        if str(destination) not in current:
            st.session_state[kit_key] = current + [str(destination)]
        clear_accepted_icon_cache(slug)
        clear_icon_review_summary_cache(slug)
        return True, f"Approved {filename} for {word}."
    except Exception as exc:
        return False, f"Could not approve the icon: {exc}"


def normalize_icon_file(path: Path, target_px: int = 512, margin: float = 0.06, alpha_threshold: int = 1, white_cutoff: int = 250) -> bool:
    """Normalize an icon PNG by cropping margins (transparent OR white), centering on a square canvas, and resizing.
    - If the image has transparency, use the alpha channel to crop.
    - If fully opaque (common for extracted tiles), crop by non-white content using white_cutoff.
    Returns True if saved successfully.
    """
    try:
        img = Image.open(str(path)).convert("RGBA")
        alpha = img.split()[-1]
        alpha_min, alpha_max = alpha.getextrema() if hasattr(alpha, 'getextrema') else (255, 255)
        if alpha_min < 255:
            # Transparent background present â†’ crop by alpha
            mask = alpha.point(lambda p: 255 if p > alpha_threshold else 0)
        else:
            # Fully opaque â†’ crop by non-white content
            gray = img.convert("L")
            mask = gray.point(lambda p: 255 if int(p) < int(white_cutoff) else 0)
        bbox = mask.getbbox()
        if not bbox:
            return False
        cropped = img.crop(bbox)
        w, h = cropped.size
        side = max(w, h)
        pad = int(round(side * float(max(0.0, margin))))
        canvas_side = side + pad * 2
        canvas = Image.new("RGBA", (canvas_side, canvas_side), (0, 0, 0, 0))
        ox = (canvas_side - w) // 2
        oy = (canvas_side - h) // 2
        canvas.paste(cropped, (ox, oy))
        # Resize to target size
        if target_px and canvas_side != int(target_px):
            canvas = canvas.resize((int(target_px), int(target_px)), Image.LANCZOS)
        canvas.save(str(path))
        return True
    except Exception:
        return False


def extract_boardmaker_grid(pdf_data: bytes, rows: int, cols: int, padding_percent: float = 2.0, zoom: float = 2.0) -> list[dict]:
    if fitz is None:
        raise RuntimeError("PDF extraction requires PyMuPDF.")
    row_count = int(rows)
    col_count = int(cols)
    if row_count < 1 or col_count < 1:
        raise ValueError("Rows and columns must both be at least 1.")
    document = fitz.open(stream=pdf_data, filetype="pdf")
    tiles = []
    pad_fraction = max(0.0, min(float(padding_percent), 20.0)) / 100.0
    for page_index in range(document.page_count):
        page = document.load_page(page_index)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        page_image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        cell_width = page_image.width / col_count
        cell_height = page_image.height / row_count
        pdf_cell_width = page.rect.width / col_count
        pdf_cell_height = page.rect.height / row_count
        words = page.get_text("words") or []
        for row in range(row_count):
            for col in range(col_count):
                left = int(col * cell_width)
                top = int(row * cell_height)
                right = int((col + 1) * cell_width)
                bottom = int((row + 1) * cell_height)
                pad_x = int((right - left) * pad_fraction)
                pad_y = int((bottom - top) * pad_fraction)
                crop = page_image.crop((left + pad_x, top + pad_y, right - pad_x, bottom - pad_y))
                buffer = io.BytesIO()
                crop.save(buffer, format="PNG")
                pdf_left = col * pdf_cell_width
                pdf_top = row * pdf_cell_height
                pdf_right = (col + 1) * pdf_cell_width
                pdf_bottom = (row + 1) * pdf_cell_height
                cell_words = [
                    item for item in words
                    if pdf_left <= (float(item[0]) + float(item[2])) / 2 < pdf_right
                    and pdf_top <= (float(item[1]) + float(item[3])) / 2 < pdf_bottom
                ]
                cell_words.sort(key=lambda item: (round(float(item[1]) / 4), float(item[0])))
                detected_label = " ".join(str(item[4]).strip() for item in cell_words if str(item[4]).strip())
                tiles.append({
                    "page": page_index + 1,
                    "row": row + 1,
                    "col": col + 1,
                    "image": buffer.getvalue(),
                    "detected_label": detected_label,
                })
    document.close()
    return tiles


def save_boardmaker_tiles_for_later(slug: str, source_name: str, tiles: list[dict], rows: int, cols: int, labels: list[str] | None = None) -> tuple[bool, str, Path | None]:
    book_dir = find_book_dir(slug)
    if not book_dir:
        return False, "The book folder could not be found.", None
    created_at = datetime.now()
    source_stem = sanitise_symbol_name(Path(source_name or "boardmaker").stem) or "boardmaker"
    batch_id = f"{created_at.strftime('%Y%m%d_%H%M%S_%f')}_{source_stem}"
    batch_dir = book_dir / "icon_imports" / "waiting_for_labels" / batch_id
    try:
        batch_dir.mkdir(parents=True, exist_ok=False)
        manifest_tiles = []
        for index, tile in enumerate(tiles, start=1):
            filename = f"cell_{index:03d}.png"
            (batch_dir / filename).write_bytes(bytes(tile["image"]))
            label = str((labels or [])[index - 1]).strip() if index <= len(labels or []) else ""
            manifest_tiles.append({
                "filename": filename,
                "page": int(tile.get("page", 1)),
                "row": int(tile.get("row", 1)),
                "col": int(tile.get("col", 1)),
                "label": label,
            })
        manifest = {
            "schema_version": 1,
            "batch_id": batch_id,
            "source_name": Path(source_name or "boardmaker.pdf").name,
            "created_at": created_at.isoformat(timespec="seconds"),
            "rows": int(rows),
            "cols": int(cols),
            "status": "waiting_for_labels",
            "tiles": manifest_tiles,
        }
        (batch_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return True, f"Saved {len(manifest_tiles)} cells for labelling later.", batch_dir
    except Exception as exc:
        return False, f"Could not save the extracted cells: {exc}", None


def boardmaker_batches_waiting_for_labels(slug: str) -> list[dict]:
    book_dir = find_book_dir(slug)
    root = (book_dir / "icon_imports" / "waiting_for_labels") if book_dir else None
    if root is None or not root.exists():
        return []
    batches = []
    for manifest_path in sorted(root.glob("*/manifest.json"), reverse=True):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("status") != "complete":
                manifest["manifest_path"] = str(manifest_path)
                batches.append(manifest)
        except Exception:
            continue
    return batches


def load_boardmaker_pending_tiles(manifest: dict) -> list[dict]:
    manifest_path = Path(str(manifest.get("manifest_path") or ""))
    tiles = []
    for item in manifest.get("tiles") or []:
        image_path = manifest_path.parent / str(item.get("filename") or "")
        if image_path.is_file():
            tiles.append({**item, "image": image_path.read_bytes()})
    return tiles


def save_boardmaker_batch_labels(manifest_path: str, labels: list[str], complete: bool = False) -> None:
    path = Path(manifest_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    for item, label in zip(data.get("tiles") or [], labels):
        item["label"] = label
    data["status"] = "complete" if complete else "waiting_for_labels"
    data["updated_at"] = datetime.now().isoformat(timespec="seconds")
    if complete:
        data["completed_at"] = data["updated_at"]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_labelled_boardmaker_tiles(slug: str, tiles: list[dict], labels: list[str], add_to_kit: bool) -> tuple[int, int]:
    saved = 0
    approved = 0
    seen_labels = set()
    for tile, stem in zip(tiles, labels):
        if not stem or stem in seen_labels:
            continue
        seen_labels.add(stem)
        first = stem[0].lower()
        bucket = first if "a" <= first <= "z" else "#"
        out_dir = symbols_root() / "Alpha" / bucket
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{stem}.png"
        Image.open(io.BytesIO(tile["image"])).convert("RGBA").save(str(out_path))
        normalize_icon_file(out_path, target_px=512, margin=0.06, white_cutoff=245)
        saved += 1
        if add_to_kit:
            accepted_ok, _message = accept_icon_candidate(slug, stem.replace("_", " "), str(out_path), stem)
            approved += int(accepted_ok)
    clear_icon_candidate_cache()
    if icon_qa_logic is not None:
        try:
            icon_qa_logic._PNG_DIR_CACHE.clear()
        except Exception:
            pass
    return saved, approved


def suggest_vocab_for_book(book_title: str) -> list[str]:
    if anthropic is None:
        return []
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return []
    try:
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": f"""List 8-12 key vocabulary words from the children's picture book \n"{book_title}". Focus on nouns and action words from the story.\nReturn only a JSON array of lowercase strings, no explanation.""",
            }],
        )
        raw = (msg.content[0].text if getattr(msg, "content", None) else "").strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x).strip().lower() for x in data if str(x).strip()]
    except Exception:
        return []
    return []

def find_symbol_matches(tokens: list[str], limit: int = 60) -> list[Path]:
    root = symbols_root()
    if not root.exists():
        return []
    files = library_png_paths()
    # Deduplicate by stem so variants in subfolders don't repeat
    by_stem: dict[str, Path] = {}
    for p in files:
        steme = p.stem.lower()
        if steme not in by_stem:
            by_stem[steme] = p
    out: list[Path] = []
    seen: set[str] = set()
    for t in tokens:
        tt = _tokenize(t)
        if not tt:
            continue
        # direct match by stem first
        cand = by_stem.get(tt)
        if cand and cand.stem.lower() not in seen:
            out.append(cand)
            seen.add(cand.stem.lower())
            if len(out) >= limit:
                break
            continue
        # fallback: contains token
        for stem, p in by_stem.items():
            if stem.find(tt) != -1 and stem not in seen:
                out.append(p)
                seen.add(stem)
                break
        if len(out) >= limit:
            break
    return out[:limit]


def promote_symbol_to_alpha_library(src_path: Path, preferred_stem: str | None = None) -> tuple[bool, str]:
    try:
        if not src_path.exists():
            return False, "Source file not found"
        lib_root = project_root() / "assets" / "symbols" / "png" / "Alpha"
        if not lib_root.exists():
            return False, "Alpha library not found"
        stem = sanitise_symbol_name(preferred_stem or src_path.stem)
        if not stem:
            return False, "Invalid name"
        first = stem[0].lower()
        bucket = first if ("a" <= first <= "z") else "#"
        dest_dir = lib_root / bucket
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{stem}.png"
        if dest.exists():
            return True, f"Already in library: {dest.name}"
        shutil.copy2(str(src_path), str(dest))
        return True, f"Promoted to library: {bucket}/{dest.name}"
    except Exception as e:
        return False, str(e)


def _fmt_secs(n: int) -> str:
    try:
        n = int(n)
    except Exception:
        n = 0
    if n <= 0:
        return "0s"
    m, s = divmod(n, 60)
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


# Phase 5 â€” Product tokens and specs
BUILT_PRODUCT_TOKENS: dict[str, list[str]] = {
    "Book Participation Pieces":       ["bookparticipation", "BookParticipation", "Book_Participation", "BPP"],
    "Matching":            ["matching", "Matching"],
    "Find & Cover":        ["find_and_cover", "Find_and_Cover", "FindCover", "find-and-cover", "FindAndCover"],
    "Word Search":         ["word_search", "Word_Search", "WordSearch"],
    "AAC Sentence Building": ["sentence_strips", "AAC_Sentence", "aac_strips", "AAC_SentenceStrips"],
    "AAC Board":           ["aac_board", "aacboard", "AAC_Board", "AACBoard"],
    "Sequencing":          ["sequencing", "sequence", "story_strip", "storystrips", "story_strips"],
    "Sorting Cards":       ["sorting_cards", "Sorting_Cards", "SortingCards"],
    "Bingo":               ["bingo", "Bingo"],
    "Spin & Cover":         ["spincov", "spincover", "spin_cover", "spin-cover", "SpinCover", "SpinCover"],
    "Yes/No Questions":    ["yesno", "yes_no", "yes-no", "YesNo", "YesNoQuestions"],
    "Inferencing Cards":    ["inferencing", "Inferencing_Cards", "InferencingCards"],
    "Vocabulary Snap":      ["wordsnap", "WordSnap", "Vocabulary_Snap", "VocabularySnap"],
    "Syllable Awareness":    ["syllable", "Syllable_Cards", "SyllableCards"],
    "CVC Decode & Build":    ["decoding", "Decoding", "Decode_Build"],
    "Story Grammar & Retell": ["story_elements", "Story_Elements", "StoryGrammar", "Story_Grammar"],
    "Print Detective":       ["print_detective", "PrintDetective", "Print_Detective", "PD-LAUNCH"],
    "Adapted Book":          ["adapted_book", "AdaptedBook", "Adapted_Book"],
    "IEP Monitoring Form":   ["iep_monitoring", "IEP_Monitoring", "IEP_MonitoringForm"],
    "Vocabulary Word Wall":  ["word_wall", "WordWall", "Word_Wall", "VocabWordWall"],
}

PRODUCT_SPECS = [
    {"name": "Book Participation Pieces", "display_name": "Interactive Book Participation Pieces", "module": "Studioforge._TRUTH.BOOK_PARTICIPATION", "func": "generate_book_participation_pack", "pages": 9, "min_icons": 12, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Edition-neutral trade-book insert pieces use reviewed vocabulary and flexible prompts; human icon and visual approval remain required."},
    {"name": "Matching", "display_name": "Matching Cards", "module": "Studioforge._TRUTH.MATCHING", "func": "generate_matching_pack", "pages": 19, "min_icons": 4, "production_status": "active"},
    {"name": "Find & Cover", "module": "Studioforge._TRUTH.FIND_AND_COVER_GENERATOR", "func": "generate_find_and_cover_pack", "pages": 40, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Differentiated find-and-cover activity uses approved local icons; final human approval remains required."},
    {"name": "Word Search", "display_name": "Differentiated Word Search", "module": "Studioforge._TRUTH.WORD_SEARCH", "func": "generate_word_search", "pages": 5, "min_icons": 6, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Six reviewed words, four differentiated grids and an answer key have clean branded output; final human visual approval remains required."},
    {"name": "AAC Sentence Building", "module": "Studioforge._TRUTH.SENTENCE_BUILDING", "func": "generate_sentence_building_pack", "pages": 8, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Four reviewed communication patterns use curated theme vocabulary; human AAC and visual approval remain required."},
    {"name": "AAC Board", "display_name": "AAC Communication Board", "module": "Studioforge._TRUTH.AAC_BOARD", "func": "generate_aac_board_pack", "pages": 1, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Canonical BoardReady layout; current review set passes all 36 icon checks and includes verified grayscale and high-visibility variants."},
    {"name": "Sequencing", "display_name": "Story Sequencing", "module": "Studioforge._TRUTH.SEQUENCING", "func": "generate_grounded_sequence_pack", "pages": 3, "min_icons": 5, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Uses a four-event reviewed sequence from book_vocab.json; final human story-order approval remains required."},
    {"name": "Sorting Cards", "display_name": "Reason & Sort: Category Sorting", "module": "Studioforge._TRUTH.SORTING", "func": "generate_grounded_sorting_pack", "pages": 11, "min_icons": 6, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Guided sorts, open mats, reusable headers and create-a-rule options have complete branded output; final human approval remains required."},
    {"name": "Bingo", "display_name": "Differentiated Bingo", "module": "Studioforge._TRUTH.BINGO", "func": "generate_bingo_pack", "pages": 18, "min_icons": 8, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Four differentiated levels use eight unique reviewed concepts without within-board repeats; final human visual approval remains required."},
    {"name": "Spin & Cover", "module": "Studioforge._TRUTH.SPIN_COVER_GENERATOR", "func": "generate_spin_cover_pack", "pages": 10, "min_icons": 6, "production_status": "review", "status_reason": "Candidate implementation is not wired to the canonical build path."},
    {"name": "Yes/No Questions", "module": "Studioforge._TRUTH.YES_NO", "func": "generate_yes_no_pack", "pages": 8, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Clean pilot generated with eight explicitly mapped questions; includes differentiated desk strip; human launch approval remains required."},
    {"name": "Inferencing Cards", "display_name": "Clue, Think, Infer: Inferencing Cards", "module": "Studioforge._TRUTH.INFERENCING", "func": "generate_inferencing_reasoning_pack", "pages": 5, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Four clue-based reasoning cards and a discussion guide are generated from reviewed content; final human approval remains required."},
    {"name": "Vocabulary Snap", "module": "Studioforge._TRUTH.VOCABULARY_SNAP", "func": "generate_vocabulary_snap_pack", "pages": 15, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Clean WordSnap deck uses approved local symbols; final activity and packaging approval remain required."},
    {"name": "Syllable Awareness", "module": "Studioforge._TRUTH.SYLLABLE_AWARENESS", "func": "generate_syllable_awareness_pack", "pages": 4, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Uses explicit reviewed syllable counts and segmentation; human literacy approval remains required."},
    {"name": "Print Detective", "display_name": "Print Detective: Letters, Words & First Sounds", "module": "Studioforge._TRUTH.PRINT_DETECTIVE", "func": "generate_print_detective_pack_wrapper", "pages": 8, "min_icons": 7, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Print concepts + alphabet knowledge linked to reviewed vocabulary and icons; human literacy approval remains required."},
    {"name": "CVC Decode & Build", "module": "Studioforge._TRUTH.DECODING", "func": "generate_decoding_pack", "pages": 6, "min_icons": 0, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Explicit CVC grapheme mappings replace unreliable phoneme heuristics; human phonics approval remains required."},
    {"name": "Story Grammar & Retell", "module": "Studioforge._TRUTH.STORY_ELEMENTS", "func": "generate_story_elements_mat_pack", "pages": 1, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Six-part retell mat has clean pilot output; human visual and literacy approval remain required."},
    {"name": "Adapted Book", "display_name": "Adapted Book Companion", "module": "Studioforge._TRUTH.ADAPTED_BOOK", "func": "generate_adapted_book_pack", "pages": 8, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Simplified text with picture supports and interactive cut-out pieces; human content and visual approval remain required."},
    {"name": "IEP Monitoring Form", "display_name": "IEP Progress Monitoring", "module": "Studioforge._TRUTH.IEP_MONITORING", "func": "generate_iep_monitoring_pack", "pages": 1, "min_icons": 0, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Progress tracking tool aligned to book companion goals; human IEP goal approval remains required."},
    {"name": "Vocabulary Word Wall", "display_name": "Vocabulary Word Wall & Banner", "module": "Studioforge._TRUTH.WORD_WALL", "func": "generate_word_wall_pack", "pages": 9, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "A-Z vocabulary cards, classroom banner, and consolidated WordSnap deck; human visual approval remains required."},
]

# ── Dignity product specs (SEPARATE from book companion products) ──
# These generators live in Studioforge/_TRUTH/DIGNITY/ and read from the
# enriched Dignity topic JSON, not from book_vocab.json. They are only
# built from the 'teen_dignity' pathway and shown in the Dignity tab.
DIGNITY_PRODUCT_SPECS = [
    {"name": "Dignity Cover", "display_name": "Dignity Bundle Cover", "module": "Studioforge._TRUTH.DIGNITY.DIGNITY_COVER", "func": "generate_dignity_cover_pack", "pages": 1, "min_icons": 0, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Bundle cover with badge, activities list, and bonus section; human visual approval remains required."},
    {"name": "Social Story", "display_name": "Social Story (full-page + half-page + mini adapted book + participation pieces)", "module": "Studioforge._TRUTH.DIGNITY.SOCIAL_STORY", "func": "generate_social_story_pack", "pages": 29, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "One product with four formats: full-page, half-page, mini adapted book, and participation pieces for engagement; human content and visual approval remain required."},
    {"name": "Scenario Activity", "display_name": "Scenario Sort, Game & Cards (public/private)", "module": "Studioforge._TRUTH.DIGNITY.SCENARIO_ACTIVITY", "func": "generate_scenario_activity_pack", "pages": 3, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "One product with three pages: public/private scenario sort, game board, and cut-out cards; human content and visual approval remain required."},
    {"name": "Choice Board", "display_name": "Replacement Behavior Choice Board", "module": "Studioforge._TRUTH.DIGNITY.CHOICE_BOARD", "func": "generate_choice_board_pack", "pages": 2, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Selection board with cut-out replacement behavior option pieces; human content and visual approval remain required."},
    {"name": "Visual Supports", "display_name": "Visual Support Cards + If-Then Prompts", "module": "Studioforge._TRUTH.DIGNITY.VISUAL_SUPPORTS", "func": "generate_visual_supports_pack", "pages": 1, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Concept cards with purpose labels and if-then behavior prompts; human content and visual approval remain required."},
    {"name": "Lanyard Cards", "display_name": "Lanyard Cards (2x3 inch, hole-punch, portable)", "module": "Studioforge._TRUTH.DIGNITY.LANYARD_CARDS", "func": "generate_lanyard_cards_pack", "pages": 2, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Portable prompt cards for teacher lanyard, student bag, bathroom wall, desk; colour + BW; human visual approval required."},
    {"name": "Routine Strips", "display_name": "Location-Specific Routine Strips (desk, bathroom, bedroom, locker)", "module": "Studioforge._TRUTH.DIGNITY.ROUTINE_STRIPS", "func": "generate_routine_strips_pack", "pages": 2, "min_icons": 4, "production_status": "pilot_review", "build_enabled": True, "status_reason": "First-Next-Then-Finally strips for placement where the behaviour happens; colour + BW; human visual approval required."},
    {"name": "IEP Monitoring", "display_name": "IEP Progress Monitoring Form (non-verbal response tracking)", "module": "Studioforge._TRUTH.DIGNITY.IEP_MONITORING", "func": "generate_iep_monitoring_pack", "pages": 1, "min_icons": 0, "production_status": "pilot_review", "build_enabled": True, "status_reason": "Topic-specific IEP form tracking non-verbal responses; human review required."},
    {"name": "Teacher Guide", "display_name": "Teacher Guide (implementation, adaptation, safety)", "module": "Studioforge._TRUTH.DIGNITY.TEACHER_GUIDE", "func": "generate_teacher_guide_pack", "pages": 2, "min_icons": 0, "production_status": "pilot_review", "build_enabled": True, "status_reason": "2-page guide with implementation notes, adaptation guidance, safety considerations; human review required."},
]

BUILD_STAGES = [
    ("setup", "1  Setup"),
    ("content", "2  Content"),
    ("icons", "3  Icons"),
    ("boardready", "4  BoardReady"),
    ("qa", "5  Visual QA"),
    ("build", "6  Activities"),
    ("dignity", "7  Dignity"),
    ("listing", "8  Listing"),
    ("promote", "9  Promote"),
]
BUILD_STAGE_KEYS = {key for key, _label in BUILD_STAGES}

PRODUCTION_STAGE_GUIDANCE = {
    "setup": {
        "purpose": "Confirm the project pathway and anonymous learner-access settings.",
        "action": "Review age band, instructional level, communication access, support, targets, and sensitive-content classification.",
        "done": "All required project fields are complete and the profile is saved.",
        "tip": "Describe access needs without storing a student name or other identifying information.",
    },
    "content": {
        "purpose": "Review generated or supplied content before it reaches any product renderer.",
        "action": "Check accuracy, dignity, safety, copyright, curriculum claims, source evidence, and any IEP wording.",
        "done": "Every mandatory review check is confirmed and the content review is explicitly approved.",
        "tip": "Sensitive topics require safeguarding notes and human approval; AI output is never self-approving.",
    },
    "icons": {
        "purpose": "Choose and approve the exact topic images that generators may use.",
        "action": "Resolve missing or ambiguous vocabulary first, then check the final icon kit.",
        "done": "Every required word is approved or intentionally skipped, with a suitable hero image selected.",
        "tip": "Use Extract and label a PDF only when the shared library does not already contain a suitable image.",
    },
    "qa": {
        "purpose": "Perform a final visual check before any products are generated.",
        "action": "Accept suitable icons, replace incorrect ones, and mark genuinely unavailable images as Missing.",
        "done": "Every displayed icon has a decision and QA is explicitly marked as passed.",
        "tip": "Accept all high-confidence icons first, then concentrate on the smaller exception set.",
    },
    "build": {
        "purpose": "Generate only products whose icon and QA requirements are satisfied.",
        "action": "Use Build all ready for a first run, or Rebuild Stale after changing icons or source content.",
        "done": "Required Color, B&W, Preview, Quick Start, and upload files exist without unresolved warnings.",
        "tip": "Preview one representative output before rebuilding the entire product set.",
    },
    "dignity": {
        "purpose": "Build Dignity life-skills products (social stories, scenario activities, choice boards, visual supports, covers) from the enriched topic JSON.",
        "action": "Build individual Dignity products or use Build All, then confirm the outputs are correct.",
        "done": "Dignity PDFs exist in OUTPUT and the stage is confirmed.",
        "tip": "Dignity products are separate from book companion activities and only available for the Teen Dignity pathway.",
    },
    "listing": {
        "purpose": "Prepare accurate buyer-facing copy for the products you actually generated.",
        "action": "Generate the draft, verify contents and claims against the PDFs, then save the approved listing.",
        "done": "The title, description, bullets, tags, and price are reviewed and saved.",
        "tip": "Describe the teaching problem solved; do not rely on a list of files alone.",
    },
    "promote": {
        "purpose": "Create a reviewed Pinterest campaign that sends teachers to the exact TPT product page.",
        "action": "Enter the published TPT product URL, generate six fresh Pin designs, and review the local upload pack.",
        "done": "Every Pin has an approved image, title, description, alt text, board and exact destination URL.",
        "tip": "Upload the images through Tailwind as drafts first; schedule them only after checking every link.",
    },
    "boardready": {
        "purpose": "Confirm the canonical BoardReady communication board and topic fringe vocabulary.",
        "action": "Check the fixed core positions, twelve fringe words, icon meanings, and output variants.",
        "done": "The BoardReady board has passed visual review in Color, B&W, and high-visibility formats where required.",
        "tip": "Embedded response strips support an activity but never replace the complete 6×6 BoardReady board.",
    },
}


def production_stage_guidance(stage: str) -> dict:
    return dict(PRODUCTION_STAGE_GUIDANCE.get(normalize_build_stage(stage), PRODUCTION_STAGE_GUIDANCE["setup"]))


def normalize_build_stage(stage: str | None) -> str:
    value = str(stage or "").strip().lower()
    return value if value in BUILD_STAGE_KEYS else "setup"


def product_readiness(icon_count: int, qa_passed: bool) -> dict[str, dict]:
    count = max(0, int(icon_count or 0))
    readiness = {}
    for spec in PRODUCT_SPECS:
        required = max(0, int(spec.get("min_icons", 0) or 0))
        missing = max(0, required - count)
        production_ready = spec.get("production_status", "review") == "active"
        build_enabled = bool(spec.get("build_enabled", production_ready))
        readiness[spec["name"]] = {
            "ready": bool(build_enabled and qa_passed and missing == 0),
            "icons": count,
            "required_icons": required,
            "missing_icons": missing,
            "qa_passed": bool(qa_passed),
            "build_enabled": build_enabled,
            "production_ready": production_ready,
            "status_reason": spec.get("status_reason", ""),
        }
    return readiness


def product_preflight(slug: str, product_name: str) -> tuple[bool, str]:
    book_dir = find_book_dir(slug)
    if not book_dir:
        return False, "Book folder not found"
    required_configs = {
        "Book Participation Pieces": book_dir / "config" / "book_participation_pieces.json",
        "AAC Sentence Building": book_dir / "config" / "sentence_building.json",
        "Syllable Awareness": book_dir / "config" / "syllables.json",
        "CVC Decode & Build": book_dir / "config" / "decoding.json",
    }
    required = required_configs.get(product_name)
    if required is not None and not required.exists():
        return False, f"Missing reviewed content: {required.name}"
    vocab_path = book_dir / "book_vocab.json"
    if product_name in {"Sequencing", "Inferencing Cards"}:
        if not vocab_path.exists():
            return False, "Missing reviewed book_vocab.json"
        try:
            vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
        except Exception:
            return False, "book_vocab.json could not be read"
        if product_name == "Sequencing":
            sequence = vocab.get("story_sequence") or []
            captions = vocab.get("story_event_captions") or {}
            if len(sequence) != 4 or any(not captions.get(key) for key in sequence):
                return False, "Add four reviewed story events and captions"
        if product_name == "Inferencing Cards" and not vocab.get("inferencing_questions"):
            return False, "Add reviewed inferencing questions"
    return True, "Ready"


def required_builds_complete(built: dict) -> bool:
    required = [spec["name"] for spec in PRODUCT_SPECS if spec.get("production_status") == "active"]
    return bool(required) and all(bool((built or {}).get(name)) for name in required)


def next_production_stage(icon_count: int, qa_passed: bool, built: dict, listing_saved: bool, icon_review_complete: bool | None = None, setup_complete: bool = True, content_approved: bool = True, boardready_confirmed: bool = True, promotion_ready: bool = True) -> str:
    if not setup_complete:
        return "setup"
    if not content_approved:
        return "content"
    if int(icon_count or 0) < min(int(spec.get("min_icons", 0) or 0) for spec in PRODUCT_SPECS if spec.get("production_status") == "active"):
        return "icons"
    if icon_review_complete is False:
        return "icons"
    if not boardready_confirmed:
        return "boardready"
    if not qa_passed:
        return "qa"
    if not required_builds_complete(built):
        return "build"
    if not listing_saved:
        return "listing"
    if not promotion_ready:
        return "promote"
    return "tracker"


# Phase 5 â€” Book state persistence
def images_dir_for_book(slug: str) -> Path | None:
    """Return the activity_images directory for a book, creating it if needed.
    Prefer SF_THEMES_ROOT if set; otherwise fall back to assets/themes.
    """
    d = find_book_dir(slug)
    if not d:
        # Choose a base root to create the book folder
        env = os.environ.get("SF_THEMES_ROOT", "").strip()
        base = Path(env) if env else (project_root() / "assets" / "themes")
        try:
            base.mkdir(parents=True, exist_ok=True)
            d = base / slug
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            return None
    ai = d / "activity_images"
    try:
        ai.mkdir(parents=True, exist_ok=True)
    except Exception:
        return None
    return ai


def book_state_path(slug: str) -> Path | None:
    d = find_book_dir(slug)
    if not d:
        return None
    return d / "config" / "book_state.json"


def _book_state_defaults(slug: str) -> dict:
    return {
        "schema_version": 1,
        "slug": slug,
        "icons_kit": [],
        "hero_icon": None,
        "qa": {"status": "not_reviewed", "reviewed_at": None, "items": []},
        "build": {"last_built_at": None, "products_built": [], "pack_code": default_pack_code(slug)},
    }


_book_state_mem_cache: dict[str, tuple[float, dict]] = {}
_book_state_mem_lock = threading.Lock()


def read_book_state(slug: str) -> dict:
    p = book_state_path(slug)
    if not p:
        return _book_state_defaults(slug)
    try:
        mtime = p.stat().st_mtime if p.exists() else 0.0
    except Exception:
        mtime = 0.0
    # Check in-memory cache first (avoids re-reading JSON on every word lookup)
    with _book_state_mem_lock:
        cached = _book_state_mem_cache.get(slug)
        if cached and cached[0] == mtime and mtime > 0:
            return cached[1]
    try:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            with _book_state_mem_lock:
                _book_state_mem_cache[slug] = (mtime, data)
            return data
    except Exception:
        return _book_state_defaults(slug)
    return _book_state_defaults(slug)


def write_book_state(slug: str, data: dict, toast_ok: bool = False):
    p = book_state_path(slug)
    if not p:
        return
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        # Update in-memory cache immediately
        try:
            mtime = p.stat().st_mtime
            with _book_state_mem_lock:
                _book_state_mem_cache[slug] = (mtime, data)
        except Exception:
            pass
        if toast_ok:
            show_toast("success", "Config saved")
    except Exception:
        show_toast("warning", "Could not save book state - changes are session-only.")


def default_pack_code(slug: str) -> str:
    name = decode_slug(slug)
    parts = [w for w in name.split() if w]
    abbr = "".join(p[0] for p in parts)[:3].upper() or slug[:3].upper()
    return f"{abbr}01"


def sanitise_pack_code(value: str) -> str:
    return re.sub(r"[^A-Z0-9_-]", "", str(value or "").strip().upper())[:12]


def hydrate_book_session_from_state(slug: str):
    # prevent double hydration per rerun
    mark_key = "sf_hydrated_books"
    hydrated: set[str] = set(st.session_state.get(mark_key, set()))
    if slug in hydrated:
        return
    state = read_book_state(slug)
    kit_key = get_kit_key(slug)
    hero_key = get_hero_key(slug)
    if state.get("icons_kit"):
        base = images_dir_for_book(slug) or Path("")
        st.session_state[kit_key] = [str((base / fn)) for fn in state.get("icons_kit", []) if (base / fn).exists()]
    if state.get("hero_icon"):
        st.session_state[hero_key] = state.get("hero_icon")
    hydrated.add(slug)
    st.session_state[mark_key] = hydrated


def flush_current_book_state(slug: str):
    state = read_book_state(slug)
    # icons kit and hero
    kit = st.session_state.get(get_kit_key(slug), [])
    hero = st.session_state.get(get_hero_key(slug))
    # convert kit to filenames relative to activity_images
    names = []
    for p in kit:
        try:
            names.append(Path(p).name)
        except Exception:
            continue
    state["icons_kit"] = names
    if hero:
        state["hero_icon"] = hero
    write_book_state(slug, state)


def persist_icons_hero(slug: str, toast_ok: bool = False):
    state = read_book_state(slug)
    kit = st.session_state.get(get_kit_key(slug), [])
    names = [Path(p).name for p in kit]
    state["icons_kit"] = names
    hero = st.session_state.get(get_hero_key(slug))
    if hero:
        state["hero_icon"] = hero
    write_book_state(slug, state, toast_ok=toast_ok)
    clear_stage_caches(slug)


def persist_qa_pass(slug: str):
    state = read_book_state(slug)
    qa_items = []
    for sp, v in st.session_state.get(qa_state_key(slug), {}).items():
        qa_items.append({
            "filename": Path(sp).name,
            "decision": v.get("status"),
            "replacement": v.get("replacement"),
            "confidence": float(v.get("confidence", 0)),
        })
    state["qa"] = {"status": "passed", "reviewed_at": datetime.now().isoformat(timespec="seconds"), "items": qa_items}
    write_book_state(slug, state, toast_ok=True)
    clear_stage_caches(slug)


def persist_qa_draft(slug: str):
    state = read_book_state(slug)
    prev = state.get("qa", {}) if isinstance(state, dict) else {}
    status = prev.get("status")
    if status == "passed":
        return
    qa_items = []
    for sp, v in st.session_state.get(qa_state_key(slug), {}).items():
        qa_items.append({
            "filename": Path(sp).name,
            "decision": v.get("status"),
            "replacement": v.get("replacement"),
            "confidence": float(v.get("confidence", 0)),
        })
    state["qa"] = {"status": "in_progress", "saved_at": datetime.now().isoformat(timespec="seconds"), "items": qa_items}
    write_book_state(slug, state)


def approved_icon_filenames_for_book(slug: str) -> list[str]:
    """Return filenames (not full paths) of icons that should be used in builds.
    Uses the current kit as the base set, excluding any QA items marked as missing.
    """
    try:
        state = read_book_state(slug)
    except Exception:
        state = {}
    kit_key = get_kit_key(slug)
    kit = st.session_state.get(kit_key)
    if not kit:
        base = images_dir_for_book(slug) or Path("")
        kit = [str((base / fn)) for fn in (state.get("icons_kit") or [])]

    names: list[str] = []
    for p in kit or []:
        try:
            names.append(Path(p).name)
        except Exception:
            continue

    excluded: set[str] = set()
    try:
        for it in (state.get("qa", {}) or {}).get("items", []) or []:
            if (it or {}).get("decision") in ("missing", "quarantine"):
                fn = (it or {}).get("filename")
                if fn:
                    excluded.add(str(fn))
    except Exception:
        pass

    # Build the approved list, deduplicated and excluding any icons marked Missing, Quarantine, Rejected or Skipped
    # Icons in the kit without an explicit decision are treated as approved (not rejected)
    decision_map: dict[str, str] = {}
    try:
        for word, dec in (state.get("icon_decisions") or {}).items():
            fn = str(dec.get("filename") or "").strip()
            status = str(dec.get("status") or "").lower()
            if fn:
                decision_map.setdefault(fn, status)
    except Exception:
        pass

    _REJECTED_STATUSES = {"rejected", "skipped", "missing", "quarantine", "banned", "not_needed"}
    out: list[str] = []
    seen: set[str] = set()
    for n in names:
        if not n or n in excluded or n in seen:
            continue
        status = decision_map.get(n)
        if status is not None and status in _REJECTED_STATUSES:
            continue
        out.append(n)
        seen.add(n)
    return out


def _pdf_page_count(p: Path) -> int:
    try:
        from PyPDF2 import PdfReader  # type: ignore
    except Exception:
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception:
            return 0
    try:
        return len(PdfReader(str(p)).pages)
    except Exception:
        return 0


def _audit_pdf_margins(pdf_path: Path, *, label: str, inset_pt: float = 24.0) -> list[str]:
    """Heuristic: flag any extracted text spans too close to page edge (possible clipping)."""
    if fitz is None:
        return []
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        return [f"{label}: cannot open for audit: {e}"]
    warnings: list[str] = []
    max_pages = min(2, len(doc))
    for i in range(max_pages):
        pg = doc.load_page(i)
        w, h = pg.rect.width, pg.rect.height
        data = pg.get_text("dict")
        for b in data.get("blocks", []):
            for l in b.get("lines", []):
                for s in l.get("spans", []):
                    bbox = s.get("bbox") or [0, 0, 0, 0]
                    x0, y0, x1, y1 = float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
                    if x0 < inset_pt or y0 < inset_pt or (w - x1) < inset_pt or (h - y1) < inset_pt:
                        snippet = (s.get("text", "") or "").strip().replace("\n", " ")
                        if snippet:
                            warnings.append(f"{label}: text near edge p{i+1}: '{snippet[:30]}'")
    doc.close()
    return warnings


def _cover_state_path(slug: str) -> Path | None:
    d = find_book_dir(slug)
    if not d:
        return None
    return d / "config" / "cover_state.json"


def load_cover_state(slug: str) -> dict:
    p = _cover_state_path(slug)
    try:
        if p and p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {f"cover_{i}": False for i in range(4)}


def save_cover_state(slug: str, data: dict) -> None:
    p = _cover_state_path(slug)
    if not p:
        return
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def build_cover_csv(
    slug: str,
    title: str,
    built_info: dict,
    output_dir: Path,
    pack_code: str,
) -> str:
    """Create Canva Bulk Create CSV content for 4 cover images per book.
    Columns follow the Phase 5B spec. Image paths are absolute file paths to help Canva locate them when uploaded.
    """
    # Hero images from vocab
    words: list[str] = []
    rec = extract_book_vocab(slug)
    if rec and isinstance(rec, dict):
        try:
            arr = (rec.get("book_words") or []) or (rec.get("activity_images") or [])
            words = [w for w in arr if isinstance(w, str) and w.strip()]
        except Exception:
            words = []

    def _hero_image_path(idx: int) -> str:
        if idx < 0 or idx >= len(words):
            return ""
        stem = sanitise_symbol_name(words[idx])
        ai = images_dir_for_book(slug) or Path("")
        if ai and ai.exists():
            p = ai / f"{stem}.png"
            if p.exists():
                return str(p)
        # best-effort search in symbols library
        try:
            lib = symbols_root()
            for p in lib.rglob("*.png"):
                if p.stem.lower() == stem:
                    return str(p)
        except Exception:
            pass
        return ""

    # Select up to 3 preview thumbnails from OUTPUT/thumbnails (if present)
    thumb_dir = output_dir / "thumbnails"
    previews: list[tuple[str, str]] = []  # (label, path)
    try:
        if thumb_dir.exists():
            # Prefer Adapted Book, Matching, Find & Cover, AAC Board order
            pref = [spec["name"] for spec in PRODUCT_SPECS]
            for name in pref:
                if not built_info.get(name, {}).get("built"):
                    continue
                # Heuristic: take first PNG that starts with pack code + product token and ends with _Page1.png
                candidates = list(thumb_dir.glob("*.png"))
                cand = next((p for p in candidates if p.name.lower().endswith("page1.png") and any(t in p.name for t in BUILT_PRODUCT_TOKENS.get(name, []))), None)
                if cand and cand.exists():
                    previews.append((name, str(cand)))
                if len(previews) >= 3:
                    break
    except Exception:
        pass
    while len(previews) < 3:
        previews.append(("", ""))

    # Build bullet strings from actually built products and their page counts
    def _pages_for_product(prod_name: str) -> int:
        files = _product_output_files(output_dir, prod_name)
        p = files.get("color") or files.get("bw")
        return _pdf_page_count(p) if p else 0

    bullet_templates = {
        "Book Participation Pieces": "[x] Book Participation Pieces - {pages} pages",
        "Matching": "[x] Matching Activities - {pages} pages (4 levels)",
        "Find & Cover": "[x] Find & Cover - {pages} pages (3 levels)",
        "AAC Board": "[x] AAC Communication Board - {pages} pages",
        "Word Search": "[x] Word Search - {pages} pages",
        "AAC Sentence Building": "[x] AAC Sentence Strips - {pages} pages",
        "Sorting Cards": "[x] Sorting Cards - {pages} pages",
    }
    bullets: list[str] = []
    for spec in PRODUCT_SPECS:
        name = spec["name"]
        if built_info.get(name, {}).get("built"):
            pages = _pages_for_product(name)
            if pages > 0:
                template = bullet_templates.get(name, f"[x] {name} - {{pages}} pages")
                bullets.append(template.format(pages=pages))
    bullets = bullets[:7]
    while len(bullets) < 7:
        bullets.append("")

    total_pages = 0
    built_count = 0
    for spec in PRODUCT_SPECS:
        name = spec["name"]
        if built_info.get(name, {}).get("built"):
            built_count += 1
            total_pages += _pages_for_product(name)
    product_count_str = f"{built_count} Products - {total_pages}+ Pages"

    how_to = [
        "Print and laminate all pages",
        "Cut out matching/sorting pieces",
        "Store in zip bag or file folder",
        "Re-use across multiple sessions!",
    ]
    audience = "SPED Classrooms - AAC Users - Speech Therapy - Autism Support"
    product_subtitle = "Book Companion Pack"
    grade_band = "SPED - Autism - AAC"

    fields = [
        "template",
        "book_title",
        "product_subtitle",
        "grade_band",
        "hero_image_1",
        "hero_image_2",
        "product_count",
        "bullet1",
        "bullet2",
        "bullet3",
        "bullet4",
        "bullet5",
        "bullet6",
        "bullet7",
        "preview_image1",
        "preview_image2",
        "preview_image3",
        "closer_label_1",
        "closer_label_2",
        "closer_label_3",
        "how_to_use_1",
        "how_to_use_2",
        "how_to_use_3",
        "how_to_use_4",
        "audience_tags",
    ]

    rows = []
    hero1, hero2 = _hero_image_path(0), _hero_image_path(1)
    prev_paths = [p for (_, p) in previews]
    prev_labels = [l for (l, _) in previews]
    for tmpl in ["cover", "whats_included", "closer_look", "how_to_use"]:
        rows.append([
            tmpl,
            title,
            product_subtitle,
            grade_band,
            hero1,
            hero2,
            product_count_str,
            *bullets,
            *prev_paths,
            *prev_labels,
            *how_to,
            audience,
        ])

    buf = io.StringIO()
    w = csv.writer(buf, quoting=csv.QUOTE_MINIMAL)
    w.writerow(fields)
    w.writerows(rows)
    return buf.getvalue()


def _pdf_first_page_image(pdf_path: Path, scale: float = 1.6) -> Image.Image | None:
    """Render the first page of a PDF to a PIL image (RGB)."""
    try:
        if fitz is None or not pdf_path or not pdf_path.exists():
            return None
        doc = fitz.open(str(pdf_path))
        pg = doc.load_page(0)
        pix = pg.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return img
    except Exception:
        return None


def _ensure_square(img: Image.Image, size: int = 1200, bg=(255, 255, 255)) -> Image.Image:
    try:
        w, h = img.size
        side = max(w, h)
        canvas = Image.new("RGB", (side, side), bg)
        ox = (side - w) // 2
        oy = (side - h) // 2
        canvas.paste(img, (ox, oy))
        return canvas.resize((size, size), Image.LANCZOS)
    except Exception:
        return img


def _compose_grid(images: list[Image.Image], size: int = 1200, gap: int = 12, bg=(255, 255, 255)) -> Image.Image:
    try:
        grid = Image.new("RGB", (size, size), bg)
        cell = (size - gap * 3) // 2
        coords = [(gap, gap), (gap * 2 + cell, gap), (gap, gap * 2 + cell), (gap * 2 + cell, gap * 2 + cell)]
        for i, im in enumerate(images[:4]):
            if im is None:
                continue
            im2 = im.copy()
            im2.thumbnail((cell, cell), Image.LANCZOS)
            x, y = coords[i]
            bx = x + (cell - im2.size[0]) // 2
            by = y + (cell - im2.size[1]) // 2
            grid.paste(im2, (bx, by))
        return grid
    except Exception:
        return Image.new("RGB", (size, size), bg)


def _tpt_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _tpt_wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int, max_lines: int = 3) -> list[str]:
    words = str(text or "").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or draw.textlength(candidate, font=font) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
            if len(lines) == max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and " ".join(lines) != " ".join(words):
        while lines[-1] and draw.textlength(lines[-1] + "...", font=font) > width:
            lines[-1] = lines[-1][:-1].rstrip()
        lines[-1] += "..."
    return lines


def _tpt_fitted_lines(draw: ImageDraw.ImageDraw, text: str, width: int, max_lines: int, start: int, minimum: int, bold: bool = True):
    for size in range(start, minimum - 1, -2):
        font = _tpt_font(size, bold)
        lines = _tpt_wrap(draw, text, font, width, max_lines)
        if not lines or "..." not in lines[-1]:
            return font, lines
    font = _tpt_font(minimum, bold)
    return font, _tpt_wrap(draw, text, font, width, max_lines)


def _tpt_draw_lines(draw: ImageDraw.ImageDraw, lines: list[str], xy: tuple[int, int], font: ImageFont.ImageFont, fill, gap: int = 8) -> int:
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        box = draw.textbbox((x, y), line, font=font)
        y = box[3] + gap
    return y


def _pdf_page_image(pdf_path: Path, page_index: int = 0, scale: float = 1.7) -> Image.Image | None:
    try:
        if fitz is None or not pdf_path or not pdf_path.exists():
            return None
        doc = fitz.open(str(pdf_path))
        if not len(doc):
            doc.close()
            return None
        page = doc.load_page(min(max(0, page_index), len(doc) - 1))
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return image
    except Exception:
        return None


def _tpt_paste_page(canvas: Image.Image, image: Image.Image | None, box: tuple[int, int, int, int], label: str = "") -> None:
    x1, y1, x2, y2 = box
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((x1 + 10, y1 + 12, x2 + 10, y2 + 12), radius=24, fill="#D7E1E3")
    draw.rounded_rectangle(box, radius=24, fill="white", outline="#D4DEDF", width=3)
    label_h = 62 if label else 20
    if image is not None:
        fitted = image.copy()
        fitted.thumbnail((x2 - x1 - 36, y2 - y1 - label_h - 24), Image.LANCZOS)
        px = x1 + (x2 - x1 - fitted.width) // 2
        py = y1 + 18 + (y2 - y1 - label_h - 24 - fitted.height) // 2
        canvas.paste(fitted, (px, py))
    if label:
        font, lines = _tpt_fitted_lines(draw, label, x2 - x1 - 30, 1, 26, 18)
        tw = draw.textlength(lines[0], font=font)
        draw.text((x1 + (x2 - x1 - tw) / 2, y2 - 48), lines[0], font=font, fill="#0D2545")


def _tpt_base(eyebrow: str, heading: str, subtitle: str = "") -> Image.Image:
    canvas = Image.new("RGB", (1200, 1200), "#FDFCF8")
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((28, 28, 1172, 1172), radius=42, fill="#FDFCF8", outline="#31A8A0", width=8)
    draw.rounded_rectangle((54, 52, 1146, 142), radius=28, fill="#0D2545")
    draw.text((86, 76), eyebrow.upper(), font=_tpt_font(34, True), fill="white")
    font, lines = _tpt_fitted_lines(draw, heading, 1030, 2, 66, 42)
    y = _tpt_draw_lines(draw, lines, (84, 174), font, "#0D2545", 6)
    if subtitle:
        sub_font, sub_lines = _tpt_fitted_lines(draw, subtitle, 1030, 2, 30, 22, False)
        _tpt_draw_lines(draw, sub_lines, (86, y + 8), sub_font, "#52606D", 4)
    draw.line((70, 1122, 1130, 1122), fill="#C9DDDC", width=2)
    draw.text((82, 1138), "SMALL WINS STUDIO", font=_tpt_font(25, True), fill="#0D2545")
    footer = "Clear • practical • accessible"
    fw = draw.textlength(footer, font=_tpt_font(23))
    draw.text((1118 - fw, 1140), footer, font=_tpt_font(23), fill="#39736F")
    return canvas


def _tpt_chip(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fill: str = "#E8F5F4") -> int:
    font = _tpt_font(24, True)
    width = int(draw.textlength(text, font=font)) + 42
    draw.rounded_rectangle((x, y, x + width, y + 52), radius=20, fill=fill, outline="#31A8A0", width=2)
    draw.text((x + 21, y + 12), text, font=font, fill="#0D2545")
    return x + width + 14


def _tpt_best_product_page(source: Path, page_count: int) -> Image.Image | None:
    candidates: list[tuple[float, Image.Image]] = []
    for page_index in range(1 if page_count > 1 else 0, min(page_count, 6)):
        image = _pdf_page_image(source, page_index)
        if image is None:
            continue
        sample = image.copy()
        sample.thumbnail((180, 180), Image.LANCZOS)
        histogram = sample.convert("L").histogram()
        non_white = sum(histogram[:242]) / max(1, sum(histogram))
        candidates.append((non_white, image))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def _tpt_product_samples(out_dir: Path, built_info: dict) -> tuple[list[dict], list[tuple[Image.Image, str]]]:
    order = ["Matching", "Find & Cover", "AAC Sentence Building", "Book Participation Pieces", "Sorting Cards", "Bingo", "Spin & Cover", "AAC Board", "Word Search", "Yes/No Questions", "Sequencing"]
    products: list[dict] = []
    samples: list[tuple[Image.Image, str]] = []
    for name in order:
        if not built_info.get(name, {}).get("built"):
            continue
        files = _product_output_files(out_dir, name)
        source = files.get("color") or files.get("bw")
        pages = _pdf_page_count(source) if source else 0
        if not source or pages < 1:
            continue
        products.append({"name": name, "pages": pages, "files": files, "source": source})
        image = _tpt_best_product_page(source, pages)
        if image is not None:
            samples.append((image, name))
    for product in products:
        for page_index in range(2, min(product["pages"], 5)):
            if len(samples) >= 6:
                break
            image = _pdf_page_image(product["source"], page_index)
            if image is not None:
                samples.append((image, product["name"]))
        if len(samples) >= 6:
            break
    return products, samples


def generate_tpt_marketing_pages(slug: str, pack_code: str, out_dir: Path, built_info: dict, title: str | None = None) -> list[Path]:
    products, samples = _tpt_product_samples(out_dir, built_info)
    if not products or not samples:
        return []
    title = (title or decode_slug(slug)).strip()
    total_pages = sum(item["pages"] for item in products)
    formats = []
    if any(item["files"].get("color") for item in products):
        formats.append("Color")
    if any(item["files"].get("bw") for item in products):
        formats.append("B&W")
    if any(item["files"].get("preview") for item in products):
        formats.append("Preview")
    pages: list[tuple[str, str, Image.Image]] = []

    cover = _tpt_base("Special Education Resource", title, "Visual, practical activities ready for real classrooms")
    draw = ImageDraw.Draw(cover)
    _tpt_paste_page(cover, samples[0][0], (270, 370, 930, 1010), samples[0][1])
    chips = [f"{total_pages} pages", f"{len(products)} resource{'s' if len(products) != 1 else ''}"] + formats[:1]
    x = 84
    for chip in chips:
        x = _tpt_chip(draw, x, 1040, chip)
    pages.append(("1_cover", "Cover", cover))

    included = _tpt_base("See exactly what you get", "What’s included", f"{len(products)} classroom resources • {total_pages} total pages")
    draw = ImageDraw.Draw(included)
    y = 390
    for item in products[:7]:
        draw.ellipse((82, y + 8, 112, y + 38), fill="#31A8A0")
        draw.line((90, y + 23, 99, y + 32), fill="white", width=4)
        draw.line((99, y + 32, 108, y + 15), fill="white", width=4)
        font, lines = _tpt_fitted_lines(draw, f"{item['name']} — {item['pages']} pages", 450, 2, 31, 23)
        y = _tpt_draw_lines(draw, lines, (132, y), font, "#0D2545", 4) + 18
    grid_samples = samples[:4]
    boxes = [(625, 390, 860, 705), (880, 390, 1115, 705), (625, 730, 860, 1045), (880, 730, 1115, 1045)]
    for (image, label), box in zip(grid_samples, boxes):
        _tpt_paste_page(included, image, box, label)
    pages.append(("2_whats_included", "What’s included", included))

    closer = _tpt_base("Actual resource pages", "Take a closer look", "Preview the layout, visual supports, and student response demands")
    for (image, label), box in zip(samples[:3], [(70, 385, 425, 1035), (423, 385, 778, 1035), (776, 385, 1131, 1035)]):
        _tpt_paste_page(closer, image, box, label)
    pages.append(("3_closer_look", "A closer look", closer))

    confidence = _tpt_base("Designed for flexible teaching", "Ready for your learners", "The practical details teachers check before purchasing")
    draw = ImageDraw.Draw(confidence)
    sections = [
        ("FILES", " • ".join(formats) + " PDF" if formats else "Printable PDF"),
        ("USE", "Whole group • small group • 1:1 support"),
        ("PREP", "Print • choose pages • laminate or cut only as needed"),
        ("BEST FOR", "Special education • intervention • visual learning"),
    ]
    y = 390
    for heading, body in sections:
        draw.rounded_rectangle((76, y, 650, y + 132), radius=22, fill="#E8F5F4")
        draw.text((102, y + 18), heading, font=_tpt_font(24, True), fill="#278A84")
        font, lines = _tpt_fitted_lines(draw, body, 520, 2, 29, 22, False)
        _tpt_draw_lines(draw, lines, (102, y + 58), font, "#0D2545", 3)
        y += 153
    _tpt_paste_page(confidence, samples[min(1, len(samples) - 1)][0], (700, 390, 1115, 1028), samples[min(1, len(samples) - 1)][1])
    pages.append(("4_teacher_confidence", "Teacher confidence", confidence))

    images_dir = out_dir / "TPT_UPLOAD" / "IMAGES" / pack_code
    images_dir.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []
    captions: list[dict] = []
    for stem, caption, image in pages:
        path = images_dir / f"{pack_code}_{stem}.png"
        image.save(path, format="PNG", optimize=True)
        results.append(path)
        captions.append({"filename": path.name, "caption": caption})
    with open(images_dir / f"{pack_code}_captions.csv", "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["filename", "caption"])
        writer.writeheader()
        writer.writerows(captions)
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        preview = canvas.Canvas(str(images_dir / f"{pack_code}_preview.pdf"), pagesize=(1200, 1200))
        for path in results:
            preview.drawImage(ImageReader(str(path)), 0, 0, width=1200, height=1200)
            preview.showPage()
        preview.save()
    except Exception:
        pass
    return results


def generate_listing_images(slug: str, pack_code: str, out_dir: Path, built_info: dict) -> list[Path]:
    """Generate up to 6 listing JPGs (1200x1200) into OUTPUT/TPT_UPLOAD/IMAGES/[pack_code]/.
    Also writes a captions CSV and a multi-page preview PDF into the same folder.
    """
    images_dir = out_dir / "TPT_UPLOAD" / "IMAGES" / pack_code
    try:
        images_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    results: list[Path] = []
    captions: dict[str, str] = {}
    # Slide 1: Cover (prefer Canva cover PDF)
    covers_root = project_root() / "covers" / slug
    cover_pdf = covers_root / f"{pack_code}_cover.pdf"
    cover_img = _pdf_first_page_image(cover_pdf) if cover_pdf.exists() else None
    if cover_img is None:
        # Fallback: any *_COVER.pdf in FINAL
        final_dir = out_dir / "FINAL"
        guess = next(final_dir.glob(f"{pack_code}_*_COVER.pdf"), None) if final_dir.exists() else None
        if guess:
            cover_img = _pdf_first_page_image(guess)
    if cover_img is not None:
        im = _ensure_square(cover_img, 1200)
        p = images_dir / f"{pack_code}_1_cover.jpg"
        try:
            im.save(p, format="JPEG", quality=88, optimize=True, progressive=True)
            results.append(p)
            captions[p.name] = "Cover"
        except Exception:
            pass
    # Slides 2–4: sample activity pages
    sample_targets = ["Matching", "AAC Sentence Building", "Word Search"]
    sample_pairs: list[tuple[Image.Image, str]] = []
    for name in sample_targets:
        try:
            if not built_info.get(name, {}).get("built"):
                continue
            files = _product_output_files(out_dir, name)
            pth = files.get("color") or files.get("bw")
            if pth and pth.exists() and pth.suffix.lower() == ".pdf":
                img = _pdf_first_page_image(pth)
                if img:
                    sample_pairs.append((img, name))
        except Exception:
            pass
    if sample_pairs:
        grid = _compose_grid([im for im, _ in sample_pairs[:4]], 1200)
        p2 = images_dir / f"{pack_code}_2_sampler.jpg"
        try:
            grid.save(p2, format="JPEG", quality=88, optimize=True, progressive=True)
            results.append(p2)
            captions[p2.name] = "Activities sampler"
        except Exception:
            pass
    # Individual samples
    for i, pair in enumerate(sample_pairs[:2], start=3):
        try:
            img, sname = pair
            im = _ensure_square(img, 1200)
            pp = images_dir / f"{pack_code}_{i}_sample.jpg"
            im.save(pp, format="JPEG", quality=88, optimize=True, progressive=True)
            results.append(pp)
            captions[pp.name] = f"{sname} sample"
        except Exception:
            pass
    # Slide 5: What's Included
    wi_pdf = covers_root / f"{pack_code}_whats_included.pdf"
    wi_img = _pdf_first_page_image(wi_pdf) if wi_pdf.exists() else None
    if wi_img is not None:
        im = _ensure_square(wi_img, 1200)
        p5 = images_dir / f"{pack_code}_5_whats_included.jpg"
        try:
            im.save(p5, format="JPEG", quality=88, optimize=True, progressive=True)
            results.append(p5)
            captions[p5.name] = "What's Included"
        except Exception:
            pass
    # Optional: Closer Look (if provided via Canva PDF)
    try:
        cl_pdf = covers_root / f"{pack_code}_closer_look.pdf"
        cl_img = _pdf_first_page_image(cl_pdf) if cl_pdf.exists() else None
        if cl_img is not None:
            im = _ensure_square(cl_img, 1200)
            idx = len(results) + 1
            p_cl = images_dir / f"{pack_code}_{idx}_closer_look.jpg"
            im.save(p_cl, format="JPEG", quality=88, optimize=True, progressive=True)
            results.append(p_cl)
            captions[p_cl.name] = "Closer Look"
    except Exception:
        pass
    # Optional: How to Use (if provided via Canva PDF)
    try:
        htu_pdf = covers_root / f"{pack_code}_how_to_use.pdf"
        htu_img = _pdf_first_page_image(htu_pdf) if htu_pdf.exists() else None
        if htu_img is not None:
            im = _ensure_square(htu_img, 1200)
            idx = len(results) + 1
            p_htu = images_dir / f"{pack_code}_{idx}_how_to_use.jpg"
            im.save(p_htu, format="JPEG", quality=88, optimize=True, progressive=True)
            results.append(p_htu)
            captions[p_htu.name] = "How to Use"
    except Exception:
        pass
    # Slide 6: End card (brand logo centered; fallback to text)
    try:
        end = Image.new("RGB", (1200, 1200), (0xF3, 0xF3, 0xF3))
        logo_candidates = [
            (project_root() / "TPT_LINE_OF_TRUTH" / "new_small_wins_logo.png") if project_root().exists() else None,
        ]
        logo_path = None
        for pth in logo_candidates:
            try:
                if pth and Path(pth).exists():
                    logo_path = Path(pth)
                    break
            except Exception:
                continue
        if logo_path is not None:
            try:
                lg = Image.open(str(logo_path)).convert("RGBA")
                max_w, max_h = 880, 880
                w0, h0 = lg.size
                sc = min(max_w / float(w0), max_h / float(h0), 1.0)
                nw, nh = max(1, int(w0 * sc)), max(1, int(h0 * sc))
                lg = lg.resize((nw, nh), Image.LANCZOS)
                end_rgba = end.convert("RGBA")
                x = (1200 - nw) // 2
                y = (1200 - nh) // 2
                end_rgba.paste(lg, (x, y), mask=lg)
                end = end_rgba.convert("RGB")
            except Exception:
                # Fallback to text if logo load fails
                dr = ImageDraw.Draw(end)
                txt = "Small Wins Studios"
                try:
                    fnt = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 64)
                except Exception:
                    fnt = ImageFont.load_default()
                bbox = dr.textbbox((0, 0), txt, font=fnt)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                dr.text(((1200 - tw) // 2, (1200 - th) // 2), txt, fill=(0x00, 0x63, 0x79), font=fnt)
        else:
            dr = ImageDraw.Draw(end)
            txt = "Small Wins Studios"
            try:
                fnt = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 64)
            except Exception:
                fnt = ImageFont.load_default()
            bbox = dr.textbbox((0, 0), txt, font=fnt)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            dr.text(((1200 - tw) // 2, (1200 - th) // 2), txt, fill=(0x00, 0x63, 0x79), font=fnt)
        idx = len(results) + 1
        p6 = images_dir / f"{pack_code}_{idx}_more_from_sws.jpg"
        end.save(p6, format="JPEG", quality=88, optimize=True, progressive=True)
        results.append(p6)
        captions[p6.name] = "Small Wins Studios"
    except Exception:
        pass
    # Write captions CSV and preview PDF (best effort)
    try:
        cap_csv = images_dir / f"{pack_code}_captions.csv"
        with open(cap_csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["filename", "caption"])
            w.writeheader()
            for p in results:
                w.writerow({"filename": p.name, "caption": captions.get(p.name, "")})
    except Exception:
        pass
    try:
        from reportlab.pdfgen import canvas  # type: ignore
        from reportlab.lib.utils import ImageReader  # type: ignore
        prev_pdf = images_dir / f"{pack_code}_preview.pdf"
        c = canvas.Canvas(str(prev_pdf), pagesize=(1200, 1200))
        for p in results:
            try:
                c.drawImage(ImageReader(str(p)), 0, 0, width=1200, height=1200)
            except Exception:
                pass
            c.showPage()
        c.save()
    except Exception:
        pass
    return results


def generate_pinterest_csv(slug: str, pack_code: str, out_dir: Path, listing: dict, images_dir: Path, default_board: str | None = None, link_base: str | None = None) -> Path | None:
    """Create a Pinterest bulk CSV with 5 pins. Media URLs are local paths (user can later map to public links).
    If provided, default_board is used for the Board column and link_base is used for the Link column.
    """
    try:
        pins_dir = out_dir / "TPT_UPLOAD" / "PINTEREST"
        pins_dir.mkdir(parents=True, exist_ok=True)
        csv_path = pins_dir / f"{pack_code}_pins.csv"
        title = listing.get("tpt_title") or f"{decode_slug(slug)} Book Companion"
        kws = listing.get("seed_keywords", []) if isinstance(listing.get("seed_keywords"), list) else []
        desc_base = (listing.get("description", "") or "").split("\n\n")[0]
        imgs = sorted([p for p in images_dir.glob("*.jpg")], key=lambda p: p.name)[:6]
        today = datetime.now().date()
        rows = []
        for i in range(5):
            media = str(imgs[i % len(imgs)]) if imgs else ""
            desc = f"{desc_base} " + (" ".join(kws[:3]) if kws else "")
            # ASCII-safe title to reduce mojibake risk in CSV consumers
            safe_title = str(title or "").replace("–", "-").replace("—", "-")
            rows.append({
                "title": safe_title if i == 0 else f"{safe_title} - {i+1}",
                "description": desc.strip(),
                "link": str(link_base or ""),  # Fill with TPT listing or store URL after publishing
                "board": str(default_board or ""),
                "media_url": media,
                "publish_date": (today + timedelta(days=i * 3)).isoformat(),
            })
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=["title", "description", "link", "board", "media_url", "publish_date"])
            w.writeheader()
            for r in rows:
                w.writerow(r)
        return csv_path
    except Exception:
        return None


def is_tpt_product_url(value: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(str(value or "").strip())
        host = (parsed.hostname or "").lower()
        return parsed.scheme == "https" and (host == "teacherspayteachers.com" or host.endswith(".teacherspayteachers.com")) and "/product/" in parsed.path.lower()
    except Exception:
        return False


def _render_guided_pin(source: Path, destination: Path, headline: str, subhead: str, badge: str, accent: str) -> None:
    canvas = Image.new("RGB", (1000, 1500), "#F4F7F8")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1000, 300), fill=hex_to_rgb("#1E3A5F"))
    draw.rectangle((0, 290, 1000, 310), fill=hex_to_rgb(accent))
    headline_font, headline_lines = _tpt_fitted_lines(draw, headline, 860, 2, 72, 44, True)
    headline_widths = [draw.textbbox((0, 0), line, font=headline_font)[2] for line in headline_lines]
    y = 48
    for line, line_width in zip(headline_lines, headline_widths):
        draw.text(((1000 - line_width) // 2, y), line, font=headline_font, fill="white")
        y += draw.textbbox((0, 0), line, font=headline_font)[3] + 8
    sub_font, sub_lines = _tpt_fitted_lines(draw, subhead, 860, 2, 38, 26, False)
    y = max(y + 8, 190)
    for line in sub_lines:
        line_width = draw.textbbox((0, 0), line, font=sub_font)[2]
        draw.text(((1000 - line_width) // 2, y), line, font=sub_font, fill="#DDEAF2")
        y += draw.textbbox((0, 0), line, font=sub_font)[3] + 5

    image = Image.open(source).convert("RGB")
    image.thumbnail((850, 820), Image.Resampling.LANCZOS)
    card = Image.new("RGB", (890, 870), "white")
    card_x, card_y = 55, 350
    canvas.paste(card, (card_x, card_y))
    canvas.paste(image, ((1000 - image.width) // 2, card_y + (870 - image.height) // 2))

    draw.rounded_rectangle((80, 1260, 920, 1360), radius=28, fill=hex_to_rgb(accent))
    badge_font, badge_lines = _tpt_fitted_lines(draw, badge, 760, 2, 42, 28, True)
    badge_y = 1280
    for line in badge_lines:
        line_width = draw.textbbox((0, 0), line, font=badge_font)[2]
        draw.text(((1000 - line_width) // 2, badge_y), line, font=badge_font, fill="white")
        badge_y += draw.textbbox((0, 0), line, font=badge_font)[3] + 4
    footer_font = _tpt_font(28, True)
    footer = "Small Wins Studio  |  View on TPT"
    footer_width = draw.textbbox((0, 0), footer, font=footer_font)[2]
    draw.text(((1000 - footer_width) // 2, 1415), footer, font=footer_font, fill="#1E3A5F")
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, "PNG", optimize=True)


def generate_guided_pinterest_campaign(slug: str, pack_code: str, out_dir: Path, listing: dict, images_dir: Path, destination_url: str, default_board: str) -> tuple[bool, str, Path | None]:
    if not is_tpt_product_url(destination_url):
        return False, "Enter the exact published TPT product URL, not the general store URL.", None
    source_images = sorted(
        [path for path in images_dir.iterdir() if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}],
        key=lambda path: path.name.lower(),
    ) if images_dir.exists() else []
    if not source_images:
        return False, "Generate the TPT marketing pages before creating a Pinterest campaign.", None

    title = str(listing.get("tpt_title") or f"{decode_slug(slug)} visual learning resource").strip()
    description = str(listing.get("description") or "").split("\n\n")[0].strip()
    book_title = decode_slug(slug)
    angles = [
        ("Teacher problem", "LOW-PREP VISUAL SUPPORT", "Make read-aloud participation easier", "Practical SPED resource", "#31A8A0", "Visual Supports for Special Education"),
        ("Student outcome", "SUPPORT ACTIVE PARTICIPATION", "Accessible choices for diverse communicators", "AAC-friendly learning", "#7B61A8", "AAC and Communication Boards"),
        ("Differentiation", "BUILT FOR DIFFERENTIATION", "Clear visuals and flexible response modes", "Support every learner", "#D9822B", "Autism Classroom Resources"),
        ("Contents", "SEE WHAT IS INCLUDED", "A coordinated, ready-to-use resource pack", "Preview the complete pack", "#2E7D5B", "Adapted Books and Book Companions"),
        ("Classroom use", "PRINT, PREP, TEACH", "Designed for real SPED classrooms", "Low-prep classroom use", "#3F6FA0", "Special Education Classroom Ideas"),
        ("Teacher time", "SAVE TEACHER PREP TIME", "Consistent visuals in one organised pack", "View it on TPT", "#A64B6A", "Low Prep Special Education Resources"),
    ]
    campaign_dir = out_dir / "TPT_UPLOAD" / "PROMOTE" / pack_code
    campaign_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, (angle, headline, subhead, badge, accent, suggested_board) in enumerate(angles, start=1):
        source = source_images[(index - 1) % len(source_images)]
        pin_path = campaign_dir / f"{pack_code}_pin_{index:02d}_{sanitise_symbol_name(angle)}.png"
        _render_guided_pin(source, pin_path, headline, book_title, badge, accent)
        pin_title = _truncate(f"{book_title}: {subhead}", 100)
        pin_description = _truncate(
            f"{subhead}. {description or title} Designed for special education, visual learning and accessible classroom participation. View the complete resource on TPT.",
            500,
        )
        rows.append({
            "filename": pin_path.name,
            "pin_title": pin_title,
            "pin_description": pin_description,
            "alt_text": _truncate(f"Preview of {book_title} teaching resource showing {angle.lower()} benefits from Small Wins Studio.", 500),
            "destination_url": destination_url,
            "suggested_board": default_board.strip() or suggested_board,
            "creative_angle": angle,
            "suggested_day_offset": (index - 1) * 4,
            "review_status": "Needs review",
        })

    csv_path = campaign_dir / f"{pack_code}_guided_upload_review.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "schema_version": 1,
        "campaign_type": "guided_tailwind_upload",
        "status": "review_required",
        "slug": slug,
        "pack_code": pack_code,
        "destination_url": destination_url,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "pins": rows,
    }
    manifest_path = campaign_dir / f"{pack_code}_campaign.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    cards = "".join(
        f"<article><img src='{html.escape(row['filename'])}' alt='{html.escape(row['alt_text'])}'><h2>{html.escape(row['pin_title'])}</h2><p>{html.escape(row['pin_description'])}</p><p><b>Board:</b> {html.escape(row['suggested_board'])}</p><p><b>Link:</b> {html.escape(row['destination_url'])}</p></article>"
        for row in rows
    )
    review_html = f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(book_title)} Pinterest Review</title><style>body{{font-family:Segoe UI,Arial;background:#f4f7f8;color:#17324d;margin:24px}}main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}}article{{background:white;border:1px solid #cbd8df;border-radius:12px;padding:16px}}img{{width:100%;height:auto}}h1{{margin-bottom:6px}}h2{{font-size:18px}}p{{line-height:1.45}}</style></head><body><h1>{html.escape(book_title)} guided Pinterest campaign</h1><p>Review every image, title, description, board and TPT destination before uploading to Tailwind.</p><main>{cards}</main></body></html>"
    (campaign_dir / "REVIEW_CAMPAIGN.html").write_text(review_html, encoding="utf-8")
    zip_path = campaign_dir / f"{pack_code}_guided_tailwind_upload.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in campaign_dir.iterdir():
            if path.is_file() and path != zip_path:
                archive.write(path, arcname=path.name)
    return True, f"Created {len(rows)} fresh Pin drafts for guided Tailwind upload.", campaign_dir


_marketing_cache: dict[str, bool] = {}


def marketing_campaign_ready(slug: str) -> bool:
    if slug in _marketing_cache:
        return _marketing_cache[slug]
    out_dir = output_dir_for_book(slug)
    if not out_dir:
        _marketing_cache[slug] = False
        return False
    manifests = list((out_dir / "TPT_UPLOAD" / "PROMOTE").rglob("*_campaign.json"))
    result = False
    for path in manifests:
        try:
            if json.loads(path.read_text(encoding="utf-8")).get("status") == "approved":
                result = True
                break
        except Exception:
            continue
    _marketing_cache[slug] = result
    return result


def _extract_pages_pdf(src: Path, pages: list[int], dst: Path) -> bool:
    try:
        try:
            from PyPDF2 import PdfReader, PdfWriter  # type: ignore
        except Exception:
            from pypdf import PdfReader, PdfWriter  # type: ignore
        r = PdfReader(str(src))
        w = PdfWriter()
        for i in pages:
            if 0 <= int(i) < len(r.pages):
                w.add_page(r.pages[int(i)])
        with open(dst, "wb") as f:
            w.write(f)
        return dst.exists()
    except Exception:
        return False


def _create_freebie_cover_pdf(*, out_path: Path, theme_name: str, pack_code: str, product_name: str) -> tuple[bool, str]:
    """Create a branded FREEBIE cover page PDF using the Small Wins frame."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader

        w_pt, h_pt = letter
        w = int(w_pt * DPI / 72)
        h = int(h_pt * DPI / 72)
        page = Image.new("RGB", (w, h), "white")
        d = ImageDraw.Draw(page)

        apply_small_wins_frame(
            page,
            product_title=f"{theme_name} {product_name}",
            subtitle="FREE SAMPLE",
            pack_code=pack_code,
            page_num=1,
            total_pages=1,
            level=None,
            footer_title=f"{theme_name} - {pack_code}",
        )

        # Big FREE banner
        banner_h = int(0.9 * DPI)
        d.rectangle([(0, 0), (w, banner_h)], fill=hex_to_rgb(NAVY_HEX))
        try:
            fnt = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(52 * DPI / 96))
        except Exception:
            fnt = ImageFont.load_default()
        txt = "FREE SAMPLE"
        bbox = d.textbbox((0, 0), txt, font=fnt)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((w - tw) // 2, (banner_h - th) // 2), txt, fill=(255, 255, 255), font=fnt)

        # Notes
        try:
            body = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(18 * DPI / 96))
        except Exception:
            body = ImageFont.load_default()
        y = int(2.0 * DPI)
        d.text((int(0.8 * DPI), y), "Includes sample pages from the full resource.", fill=hex_to_rgb(NAVY_HEX), font=body)
        y += int(0.35 * DPI)
        d.text((int(0.8 * DPI), y), "See inside for Terms of Use and how to get the full version.", fill=hex_to_rgb(NAVY_HEX), font=body)

        buf = io.BytesIO()
        page.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(out_path), pagesize=letter)
        c.drawImage(ImageReader(buf), 0, 0, width=w_pt, height=h_pt)
        c.showPage()
        c.save()
        return True, ""
    except Exception as e:
        return False, str(e)


def _create_upsell_pdf(*, out_path: Path, theme_name: str, pack_code: str, product_name: str) -> tuple[bool, str]:
    """Create a single-page upsell PDF with link placeholder to full TPT listing."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        w_pt, h_pt = letter
        c = canvas.Canvas(str(out_path), pagesize=letter)
        c.setFillColorRGB(1, 1, 1)
        c.rect(0, 0, w_pt, h_pt, stroke=0, fill=1)
        c.setFillColorRGB(0, 0.39, 0.47)
        c.setFont("Helvetica-Bold", 28)
        c.drawString(72, h_pt - 72 - 20, "Get the full version")
        c.setFillColorRGB(0.15, 0.15, 0.15)
        c.setFont("Helvetica", 13)
        lines = [
            f"Title: {theme_name} – {product_name}",
            f"Pack code: {pack_code}",
            "Includes all levels, printable pages, and teacher quick starts.",
            "Visit your TPT listing and paste your URL here after publish.",
        ]
        y = h_pt - 72 - 20 - 40
        for ln in lines:
            c.drawString(72, y, ln)
            y -= 18
        c.setFillColorRGB(0, 0.39, 0.47)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, y - 10, "URL: ")
        c.rect(110, y - 14, w_pt - 180, 24, stroke=1, fill=0)
        c.showPage()
        c.save()
        return True, ""
    except Exception as e:
        return False, str(e)


def _safe_name(s: str) -> str:
    return s.replace(" ", "_").replace("/", "-").replace("\\", "-")


def generate_freebie_zip(slug: str, product_name: str, out_dir: Path, pack_code: str) -> tuple[bool, str, Path | None]:
    """Create a FREEBIE zip containing cover+sample pages+TOU+upsell for a single product."""
    try:
        built = detect_products_in_output(slug)
        if not built.get(product_name, {}).get("built"):
            return False, f"{product_name} not built yet", None
        files = _product_output_files(out_dir, product_name)
        content = files.get("color") or files.get("bw")
        if not content or not content.exists():
            return False, f"No PDF content for {product_name}", None
        tmp = out_dir / ".sf_freebie"
        tmp.mkdir(parents=True, exist_ok=True)
        theme_name = decode_slug(slug)
        cover_pdf = tmp / f"{pack_code}_{_safe_name(product_name)}_FREE_COVER.pdf"
        ok, err = _create_freebie_cover_pdf(out_path=cover_pdf, theme_name=theme_name, pack_code=pack_code, product_name=product_name)
        if not ok:
            return False, f"Cover failed: {err}", None
        # Choose first 4 pages as sample (best-effort)
        sample_pdf = tmp / f"{pack_code}_{_safe_name(product_name)}_SAMPLE.pdf"
        if not _extract_pages_pdf(content, [0, 1, 2, 3], sample_pdf):
            return False, "Could not extract sample pages", None
        tou = _terms_of_use_pdf()
        upsell_pdf = tmp / f"{pack_code}_{_safe_name(product_name)}_UPSELL.pdf"
        ok2, err2 = _create_upsell_pdf(out_path=upsell_pdf, theme_name=theme_name, pack_code=pack_code, product_name=product_name)
        if not ok2:
            return False, f"Upsell failed: {err2}", None
        # Merge PDFs: cover + sample + TOU + upsell
        upload_dir = out_dir / "TPT_UPLOAD"
        freebie_dir = upload_dir / "FREEBIE"
        freebie_dir.mkdir(parents=True, exist_ok=True)
        final_pdf = freebie_dir / f"{pack_code}_{_safe_name(product_name)}_FREEBIE.pdf"
        script = project_root() / "production" / "generators" / "generators" / "PDF_MERGER.py"
        chain = [cover_pdf, sample_pdf] + ([tou] if tou and tou.exists() else []) + [upsell_pdf]
        cur = chain[0]
        tmps: list[Path] = []
        for i, nxt in enumerate(chain[1:], start=1):
            mid = tmp / f"_merge_step_{i}.pdf"
            res = subprocess.run([sys.executable, str(script), str(cur), str(nxt), str(mid)], capture_output=True, text=True, encoding="utf-8", errors="replace")
            if not mid.exists():
                return False, f"Merge failed at step {i}: {res.stderr.strip() if res.stderr else ''}", None
            tmps.append(mid)
            cur = mid
        try:
            shutil.copy2(str(cur), str(final_pdf))
        except Exception as e:
            return False, f"Finalize failed: {e}", None
        # Zip it
        final_zip = freebie_dir / f"{pack_code}_{_safe_name(product_name)}_FREEBIE.zip"
        with zipfile.ZipFile(str(final_zip), "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.write(str(final_pdf), arcname=final_pdf.name)
            if tou and tou.exists():
                z.write(str(tou), arcname=tou.name)
        # Cleanup
        for p in tmps:
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass
        return True, f"Freebie ready: {final_zip.name}", final_zip
    except Exception as e:
        return False, str(e), None

def ensure_build_icons_staging(slug: str, product_name: str | None = None) -> Path | None:
    """Create/refresh a staging folder that contains only approved icons for building."""
    book_dir = find_book_dir(slug)
    images = images_dir_for_book(slug)
    if not book_dir or not images:
        return None

    approved = approved_icon_filenames_for_book(slug)

    # Special case: Matching generator uses exactly 4 icons.
    if product_name == "Matching":
        try:
            state = read_book_state(slug)
            chosen = ((state.get("build", {}) or {}).get("matching_icons") or [])
            chosen = [c for c in chosen if c in approved]
            if len(chosen) >= 4:
                approved = chosen[:4]
            else:
                # Fill from approved in stable order
                for n in approved:
                    if n not in chosen:
                        chosen.append(n)
                    if len(chosen) >= 4:
                        break
                approved = chosen[:4]
        except Exception:
            approved = approved[:4]

    stage = book_dir / ".sf_build" / "icons"
    try:
        stage.mkdir(parents=True, exist_ok=True)
    except Exception:
        return None

    # Clear stale icons so removed/missing don't leak in
    try:
        for p in stage.glob("*.png"):
            try:
                p.unlink()
            except Exception:
                pass
    except Exception:
        pass

    for fn in approved:
        src = images / fn
        if not src.exists():
            continue
        try:
            shutil.copy2(str(src), str(stage / fn))
        except Exception:
            continue
    return stage


def open_folder(path: Path):
    try:
        if os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        show_toast("info", f"Folder: {str(path)}")


# Built product detection in book OUTPUT
def output_dir_for_book(slug: str) -> Path | None:
    d = find_book_dir(slug)
    if not d:
        return None
    return d / "OUTPUT"


def write_product_support_docs(out_dir: Path, pack_code: str, product_name: str, display_name: str, pages: int) -> None:
    """Write a TPT-style description and teacher support text for a built product."""
    if not out_dir.exists():
        return
    safe_name = product_name.replace(" ", "_").replace("/", "-")
    stem = f"{pack_code}_{safe_name}"
    # TPT description
    desc_path = out_dir / f"{stem}_TPT_Description.txt"

    # Product-specific copy
    product_copy = {
        "Matching": ("Differentiated matching cards targeting visual discrimination and vocabulary",
                     "receptive vocabulary, visual scanning, and one-to-one correspondence"),
        "Find & Cover": ("Interactive find-and-cover mats targeting visual scanning and attention",
                         "visual discrimination, sustained attention, and receptive vocabulary"),
        "Word Search": ("Differentiated word search puzzles targeting letter recognition and vocabulary",
                        "letter recognition, word-finding, and vocabulary retention"),
        "AAC Sentence Building": ("AAC sentence building strips with core and book vocabulary",
                                  "sentence construction, core word use, and expressive communication"),
        "AAC Board": ("AAC communication board with core and book vocabulary in a 36-cell grid",
                      "expressive communication, core vocabulary, and AAC modeling during shared reading"),
        "Sequencing": ("Story sequencing cards for narrative retell and ordinal understanding",
                       "story retell, sequencing, and narrative comprehension"),
        "Sorting Cards": ("Category sorting cards with interchangeable headers and guided sorts",
                           "classification, categorization, and reasoning skills"),
        "Bingo": ("Differentiated bingo game targeting receptive vocabulary and group participation",
                  "receptive vocabulary, group participation, and listening comprehension"),
        "Yes/No Questions": ("Yes/No question cards with cut-out tokens and differentiated desk strips",
                             "question answering, yes/no discrimination, and expressive communication"),
        "Inferencing Cards": ("Clue-based inferencing cards with discussion guide",
                              "inferencing, critical thinking, and text-based reasoning"),
        "Vocabulary Snap": ("Vocabulary snap cards in three decks: symbol+text, symbol-only, and text-only, plus extra copy cards",
                            "vocabulary acquisition, word recognition, and matching skills"),
        "Syllable Awareness": ("Syllable segmentation cards for phonological awareness",
                               "syllable segmentation, phonological awareness, and word play"),
        "Story Grammar & Retell": ("Story element cards and retell framework for narrative comprehension",
                                   "story elements, narrative structure, and comprehension"),
        "Print Detective": ("Print concepts detective activity with four differentiated levels",
                            "print concepts, letter/word discrimination, and early literacy"),
        "CVC Decode & Build": ("CVC word building activity with cut-out letters and picture cards",
                               "phonics, decoding, and word building"),
        "Adapted Book": ("Adapted book with Velcro pieces for interactive reading",
                         "comprehension, engagement, and interactive reading"),
        "Book Participation Pieces": ("Interactive book participation pieces for read-aloud engagement",
                                      "engagement, comprehension, and participation during read-alouds"),
        "IEP Monitoring Form": ("IEP progress monitoring form for tracking student data across activities",
                                "progress monitoring, data collection, and IEP goal tracking"),
        "Vocabulary Word Wall": ("Vocabulary word wall cards and banner for classroom display",
                                 "word study, vocabulary display, and spelling reference"),
    }

    # Product-specific feature notes
    has_storage_labels = product_name in {
        "Matching", "Find & Cover", "AAC Sentence Building", "Book Participation Pieces",
        "Adapted Book", "Sequencing", "Sorting Cards", "Bingo", "Yes/No Questions",
        "Vocabulary Snap", "Syllable Awareness",
    }
    has_desk_strip = product_name == "Yes/No Questions"
    has_hivis = product_name == "AAC Board"

    page_word = "page" if pages == 1 else "pages"
    feature_lines = [
        f"- {pages} printable {page_word}",
        "- Color PDF for screen or classroom printing",
        "- Black-and-white PDF for economical printing",
        "- Preview PDF for listing/screen sharing",
    ]
    if has_storage_labels:
        feature_lines.append("- Storage labels for organizing cut-out pieces")
    if has_desk_strip:
        feature_lines.append("- Pointing & eye-gaze desk strip (2-choice and 3-choice with I don't know)")
    if has_hivis:
        feature_lines.append("- High-visibility variants (black and yellow backgrounds)")

    opening, skills = product_copy.get(product_name, (
        "A ready-to-print activity companion designed for special education, speech therapy, and inclusive classrooms",
        "special education, AAC, and early literacy skills",
    ))

    lines = [
        f"{display_name}",
        f"Pack code: {pack_code}",
        f"Pages: {pages}",
        "",
        f"{opening}. Uses Boardmaker PCS symbols to make learning accessible",
        "for AAC users and emergent readers.",
        "",
        f"Targets {skills}.",
        "",
        "Includes:",
        *feature_lines,
        "",
        "Print, laminate, and use again and again.",
        "",
        "Teacher support note:",
        "Review the visual layout before sharing with students. Ensure icons match your learner's AAC system.",
        "The IEP Monitoring Form is included as a bonus in the bundle for tracking progress across activities.",
    ]
    try:
        desc_path.write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass


def _terms_of_use_pdf() -> Path | None:
    p = project_root() / "assets" / "global" / "tpt_support_docs" / "Terms of Use.pdf"
    return p if p.exists() else None


def _aac_top_tips_pdf() -> Path | None:
    candidates = [
        project_root() / "assets" / "global" / "standard_docs" / "SWS_Top_Tips_AAC_Communication_Partners.pdf",
        project_root() / "SWS_Support_Docs_Handoff" / "01_reference_pdfs" / "SWS_Top_Tips_AAC_Communication_Partners.pdf",
    ]
    return next((path for path in candidates if path.exists()), None)


def _fallback_quick_start_pdf(product_name: str) -> Path | None:
    names = {
        "Matching": "SWS_Quick_Start_Matching.pdf",
        "AAC Board": "SWS_Quick_Start_AAC_Board.pdf",
        "AAC Sentence Building": "SWS_Quick_Start_AAC_Sentence_Strips.pdf",
    }
    name = names.get(product_name)
    path = project_root() / "assets" / "global" / "standard_docs" / str(name or "")
    return path if name and path.exists() else None


def support_documents_for_product(slug: str, product_name: str, quick_start: Path | None = None) -> tuple[list[tuple[Path, str]], list[str]]:
    documents: list[tuple[Path, str]] = []
    warnings: list[str] = []
    tou = _terms_of_use_pdf()
    if tou:
        documents.append((tou, "Terms of Use.pdf"))
    else:
        warnings.append("Canonical Terms of Use is missing")
    if not quick_start or not quick_start.exists():
        quick_start = _fallback_quick_start_pdf(product_name)
    if quick_start and quick_start.exists():
        documents.append((quick_start, quick_start.name))
    else:
        warnings.append(f"{product_name}: product-specific Quick Start is missing")
    if product_name in {"AAC Board", "AAC Sentence Building"}:
        tips = _aac_top_tips_pdf()
        if tips:
            documents.append((tips, "SWS_Top_Tips_AAC_Communication_Partners.pdf"))
        else:
            warnings.append(f"{product_name}: AAC Communication Partner Top Tips is missing")
    profile = load_project_profile(slug)
    approved_docs = profile.get("approved_support_documents") or {}
    for key, archive_name in (("scarborough", "Scarborough Alignment.pdf"), ("iep_data", "IEP Data Sheet.pdf")):
        entry = approved_docs.get(key, {}) if isinstance(approved_docs, dict) else {}
        path = Path(str(entry.get("path") or "")) if isinstance(entry, dict) else Path("")
        if isinstance(entry, dict) and entry.get("verified") is True and path.is_file():
            documents.append((path, archive_name))
    return documents, warnings


def _product_output_files(out_dir: Path, product_name: str) -> dict[str, Path]:
    """Return best-effort mapping: color/bw/preview for a product."""
    tokens = [t.lower() for t in (BUILT_PRODUCT_TOKENS.get(product_name) or [])]
    pdfs = [p for p in out_dir.glob("*.pdf") if p.is_file()]
    hits = []
    for p in pdfs:
        lower = p.name.lower()
        if any(tok in lower for tok in tokens):
            hits.append(p)
    out: dict[str, Path] = {}
    for p in hits:
        lname = p.name.lower()
        if "_color" in lname or "color" in lname or "colour" in lname:
            out.setdefault("color", p)
        elif "_bw" in lname or "bw" in lname:
            out.setdefault("bw", p)
        elif "preview" in lname:
            out.setdefault("preview", p)
    # Fallback: choose most recently modified as color
    if "color" not in out and hits:
        hits.sort(key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True)
        out["color"] = hits[0]
    return out


def _create_product_cover_pdf(*, out_path: Path, theme_name: str, pack_code: str, product_name: str, bullets: list[str]) -> tuple[bool, str]:
    """Create a single-page cover PDF using the Small Wins frame."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader

        w_pt, h_pt = letter
        w = int(w_pt * DPI / 72)
        h = int(h_pt * DPI / 72)
        page = Image.new("RGB", (w, h), "white")
        d = ImageDraw.Draw(page)

        apply_small_wins_frame(
            page,
            product_title=f"{theme_name} {product_name}",
            subtitle="Product Cover",
            pack_code=pack_code,
            page_num=1,
            total_pages=1,
            level=None,
            footer_title=f"{theme_name} - {pack_code}",
        )

        scale = DPI / 72
        body_font = ImageFont.truetype("C:/Windows/Fonts/comic.ttf", int(14 * scale)) if Path("C:/Windows/Fonts/comic.ttf").exists() else ImageFont.load_default()
        heading_font = ImageFont.truetype("C:/Windows/Fonts/comicbd.ttf", int(16 * scale)) if Path("C:/Windows/Fonts/comicbd.ttf").exists() else ImageFont.load_default()

        left = int(0.75 * DPI)
        top = int(2.05 * DPI)
        max_w = w - 2 * left

        title = "What's Included"
        d.text((left, top), title, fill=hex_to_rgb(NAVY_HEX), font=heading_font)
        y = top + int(0.30 * DPI)

        for b in bullets[:10]:
            line = f"-  {b}"
            d.text((left + int(0.10 * DPI), y), line, fill=hex_to_rgb(NAVY_HEX), font=body_font)
            y += int(0.22 * DPI)

        buf = io.BytesIO()
        page.save(buf, format="PNG", dpi=(DPI, DPI))
        buf.seek(0)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(out_path), pagesize=letter)
        c.drawImage(ImageReader(buf), 0, 0, width=w_pt, height=h_pt)
        c.showPage()
        c.save()
        return True, ""
    except Exception as e:
        return False, str(e)


def _product_quick_start_func(product_name: str):
    """Return callable from generators.generate_quick_start_professional for this product, if available."""
    try:
        mod = importlib.import_module("generate_quick_start_professional")
    except Exception:
        return None
    mapping = {
        "Matching": "generate_matching_quick_start",
        "Find & Cover": "generate_find_cover_quick_start",
        "Bingo": "generate_bingo_quick_start",
        "AAC Board": "generate_aac_quick_start",
        "Sequencing": "generate_sequencing_quick_start",
    }
    fn = mapping.get(product_name)
    return getattr(mod, fn, None) if fn else None


def finalize_and_package_book(slug: str) -> tuple[bool, str]:
    out_dir = output_dir_for_book(slug)
    if not out_dir or not out_dir.exists():
        return False, "OUTPUT folder not found"

    theme_name = decode_slug(slug)
    state = read_book_state(slug)
    pack_code = ((state.get("build", {}) or {}).get("pack_code") or default_pack_code(slug))
    tou = _terms_of_use_pdf()
    if not tou:
        return False, "Terms of Use.pdf not found"

    final_dir = out_dir / "FINAL"
    upload_dir = out_dir / "TPT_UPLOAD"
    final_dir.mkdir(parents=True, exist_ok=True)
    upload_dir.mkdir(parents=True, exist_ok=True)

    built_info = detect_products_in_output(slug)

    # Best-effort bullet points; keep short and consistent.
    product_bullets: dict[str, list[str]] = {
        "Book Participation Pieces": ["Read-aloud companion", "Velcro-friendly pieces", "Storage mat + labels", "Color + black & white"],
        "Matching": ["4 differentiated levels", "Storage labels included", "Color + black & white"],
        "Find & Cover": ["3 differentiated levels", "Storage labels included", "Color + black & white"],
        "Word Search": ["Vocabulary practice", "4 differentiated grids", "Preview included"],
        "AAC Sentence Building": ["Sentence building strips", "Core + book vocabulary", "Storage labels included", "Color + black & white"],
        "AAC Board": ["Core + book vocabulary", "4 variants: color, BW, hi-vis black, hi-vis yellow", "Board-only PDF (cover separate)"],
        "Sequencing": ["Story sequencing strips", "Cut-out picture cards", "Storage labels included", "Color + black & white"],
        "Sorting Cards": ["Guided + open sorts", "Interchangeable headers", "Storage labels included", "Color + black & white"],
        "Bingo": ["4 differentiated levels", "Calling cards included", "Storage labels included", "Color + black & white"],
        "Spin & Cover": ["Spinner + mats", "Cut-out arrow included", "Color + black & white"],
        "Yes/No Questions": ["Yes/No question cards", "Cut-out tokens + desk strip", "2-choice and 3-choice (I don't know) strips", "Storage labels included", "Color + black & white"],
        "Inferencing Cards": ["Clue-based reasoning cards", "Discussion guide", "Color + black & white"],
        "Vocabulary Snap": ["Symbol+text, symbol-only, text-only decks", "Extra copy cards included", "Storage labels included", "Color + black & white"],
        "Syllable Awareness": ["Syllable segmentation cards", "2x2 grid layout", "Storage labels included", "Color + black & white"],
        "Story Grammar & Retell": ["Story element cards", "Retell framework", "Color + black & white"],
        "Print Detective": ["4 print-concepts levels", "Letter/word sorting", "Color + black & white"],
        "CVC Decode & Build": ["CVC word building", "Cut-out letters + picture cards", "Color + black & white"],
        "Adapted Book": ["Adapted book with Velcro pieces", "Storage label included", "Color + black & white"],
        "IEP Monitoring Form": ["Progress tracking form", "IEP goal data sheet", "Bonus inclusion in bundle"],
        "Vocabulary Word Wall": ["Word Wall cards + banner", "Symbol + text format", "Color + black & white"],
    }

    merged_any = False
    warnings: list[str] = []

    for spec in PRODUCT_SPECS:
        product_name = spec["name"]
        if spec.get("production_status") != "active":
            if built_info.get(product_name, {}).get("built"):
                warnings.append(f"{product_name}: excluded from packaging while its generator is under review")
            continue
        if not built_info.get(product_name, {}).get("built"):
            continue

        files = _product_output_files(out_dir, product_name)
        color_pdf = files.get("color")
        bw_pdf = files.get("bw")
        preview_pdf = files.get("preview")
        if not color_pdf:
            warnings.append(f"{product_name}: missing COLOR PDF")
            continue
        if "bw" not in files:
            warnings.append(f"{product_name}: missing BW PDF")
        if "preview" not in files:
            warnings.append(f"{product_name}: missing PREVIEW PDF")

        expected_content_pages = int(spec.get("pages") or 0)
        actual_content_pages = _pdf_page_count(color_pdf)
        if expected_content_pages and actual_content_pages and actual_content_pages != expected_content_pages:
            warnings.append(f"{product_name}: COLOR page count {actual_content_pages} != expected {expected_content_pages}")

        cover_pdf = final_dir / f"{pack_code}_{product_name.replace(' ', '_')}_COVER.pdf"
        ok, msg = _create_product_cover_pdf(
            out_path=cover_pdf,
            theme_name=theme_name,
            pack_code=pack_code,
            product_name=product_name,
            bullets=product_bullets.get(product_name, ["Print & go", "Differentiated", "Color + black & white"]),
        )
        if not ok:
            warnings.append(f"{product_name}: cover generation failed: {msg}")
            continue

        # Merge cover + color content
        merged_color = final_dir / f"{pack_code}_{product_name.replace(' ', '_')}_FINAL_COLOR.pdf"
        merged_bw = final_dir / f"{pack_code}_{product_name.replace(' ', '_')}_FINAL_BW.pdf"

        merged_ok = False
        try:
            from production.generators.generators.PDF_MERGER import merge_pdfs  # type: ignore
            merged_ok = bool(merge_pdfs(cover_pdf, color_pdf, merged_color))
            if bw_pdf:
                merge_pdfs(cover_pdf, bw_pdf, merged_bw)
        except Exception:
            merged_ok = False

        if not merged_ok:
            # Fallback: at least copy content to FINAL so packaging doesn't block
            try:
                shutil.copyfile(color_pdf, merged_color)
                if bw_pdf:
                    shutil.copyfile(bw_pdf, merged_bw)
                merged_ok = True
            except Exception as e:
                warnings.append(f"{product_name}: failed to produce FINAL PDFs: {e}")
                continue

        merged_any = True

        merged_pages = _pdf_page_count(merged_color)
        if expected_content_pages and merged_pages and merged_pages != (expected_content_pages + 1):
            warnings.append(f"{product_name}: FINAL page count {merged_pages} != expected {expected_content_pages + 1}")

        # Optional clipping audit (best-effort)
        warnings.extend(_audit_pdf_margins(merged_color, label=f"{product_name} FINAL"))

        # Quick Start — prefer product-specific template; fall back to generic instructions
        quick_start_pdf = final_dir / f"{pack_code}_{product_name.replace(' ', '_')}_Quick_Start.pdf"
        qs_fn = _product_quick_start_func(product_name)
        generated_qs = False
        if qs_fn is not None:
            try:
                qs_fn(quick_start_pdf, theme_name=theme_name, pack_code=pack_code)
                generated_qs = quick_start_pdf.exists()
            except Exception as e:
                warnings.append(f"{product_name}: quick start generation failed: {e}")
        if not generated_qs:
            try:
                mod_g = importlib.import_module("generate_quick_start_instructions")
                if hasattr(mod_g, "generate_quick_start_pdf"):
                    mod_g.generate_quick_start_pdf(quick_start_pdf, pack_code=pack_code, theme_name=theme_name)
                    generated_qs = quick_start_pdf.exists()
                if not generated_qs:
                    warnings.append(f"{product_name}: no Quick Start template found")
            except Exception as e:
                warnings.append(f"{product_name}: fallback Quick Start failed: {e}")

        # ZIP per product
        support_documents, support_warnings = support_documents_for_product(slug, product_name, quick_start_pdf)
        warnings.extend(support_warnings)
        zip_path = upload_dir / f"{pack_code}_{product_name.replace(' ', '_')}_TPT.zip"
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                z.write(merged_color, merged_color.name)
                if merged_bw.exists():
                    z.write(merged_bw, merged_bw.name)
                if preview_pdf and preview_pdf.exists():
                    z.write(preview_pdf, preview_pdf.name)
                for support_path, archive_name in support_documents:
                    z.write(support_path, archive_name)
        except Exception as e:
            warnings.append(f"{product_name}: zip failed: {e}")

    boardready_files = boardready_output_files(slug)
    if boardready_files:
        board_support, board_warnings = support_documents_for_product(slug, "AAC Board", None)
        warnings.extend(board_warnings)
        board_zip = upload_dir / f"{pack_code}_AAC_Board_TPT.zip"
        try:
            with zipfile.ZipFile(board_zip, "w", zipfile.ZIP_DEFLATED) as archive:
                for board_file in boardready_files:
                    archive.write(board_file, board_file.name)
                for support_path, archive_name in board_support:
                    archive.write(support_path, archive_name)
            merged_any = True
        except Exception as exc:
            warnings.append(f"AAC Board: zip failed: {exc}")

    if not merged_any:
        return False, "No approved built products or BoardReady files found to finalize"

    # Seed Upload Tracker records for this pack (built products only)
    tracker_created = 0
    try:
        product_types = [spec["name"] for spec in PRODUCT_SPECS if spec.get("production_status") == "active" and built_info.get(spec["name"], {}).get("built")]
        if boardready_files:
            product_types.append("AAC Board")
        if product_types:
            tracker_created = int(init_tracker_pack(book_slug=slug, book_title=theme_name, pack_code=pack_code, product_types=product_types) or 0)
        st.session_state[f"sf_finalize_created_{slug}"] = tracker_created
    except Exception:
        try:
            st.session_state[f"sf_finalize_created_{slug}"] = 0
        except Exception:
            pass

    extra = f"\nTracker: created {tracker_created} record(s)" if tracker_created else "\nTracker: no new records"

    if warnings:
        return True, "Finalize complete with warnings:\n" + "\n".join(f"- {w}" for w in warnings[:40]) + extra
    return True, "Finalize complete" + extra


_products_cache: dict[str, dict] = {}


def detect_products_in_output(slug: str) -> dict:
    if slug in _products_cache:
        return _products_cache[slug]
    out = output_dir_for_book(slug)
    result: dict[str, dict] = {}
    for name, tokens in BUILT_PRODUCT_TOKENS.items():
        result[name] = {"built": False, "path": None, "mtime": None}
    if not out or not out.exists():
        _products_cache[slug] = result
        return result

    for p in out.rglob("*"):
        if not p.is_file():
            continue
        lower = p.name.lower()
        for prod, tokens in BUILT_PRODUCT_TOKENS.items():
            if result[prod]["built"]:
                continue
            for tok in tokens:
                if tok.lower() in lower:
                    try:
                        result[prod] = {"built": True, "path": str(p), "mtime": p.stat().st_mtime}
                    except Exception:
                        result[prod] = {"built": True, "path": str(p), "mtime": None}
                    break
    _products_cache[slug] = result
    return result


def delete_existing_product_outputs(slug: str, product_name: str) -> None:
    out = output_dir_for_book(slug)
    if not out or not out.exists():
        return
    tokens = BUILT_PRODUCT_TOKENS.get(product_name, [])
    if not tokens:
        return
    toks = [t.lower() for t in tokens if str(t).strip()]
    for p in out.rglob("*"):
        try:
            if not p.is_file():
                continue
            lower = p.name.lower()
            if any(tok in lower for tok in toks):
                p.unlink(missing_ok=True)
        except Exception:
            pass


# Update Today view detection to Phase 5 token set
def detect_built_products(slug: str) -> dict:
    info = detect_products_in_output(slug)
    return {k: v["built"] for k, v in info.items()}


def read_qa_status(slug: str) -> tuple[str, bool]:
    # First check book_state.json
    st_data = read_book_state(slug)
    try:
        if st_data.get("qa", {}).get("status") == "passed":
            return ("Passed OK", True)
    except Exception:
        pass
    # Fallback to historical logs
    candidates = [
        project_root() / "BoardReady" / "boardready" / "data" / "qa_review_log.json",
        project_root() / "boardready" / "data" / "qa_review_log.json",
        project_root() / "boardready" / "qa_review_log.json",
        project_root() / "qa_review_log.json",
    ]
    for p in candidates:
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                info = data.get(slug)
                if info and isinstance(info, dict):
                    reviewed = bool(info.get("reviewed"))
                    return ("Passed OK" if reviewed else "Partial"), reviewed
        except Exception:
            pass
    return ("Not run", False)


# Build runner
def run_product_build(slug: str, product_name: str, display_name: str) -> tuple[bool, str]:
    # Sync icons/vocab before every build so new files are picked up immediately
    ensure_kit(slug)
    spec = next((s for s in PRODUCT_SPECS if s["name"] == product_name), None)
    if not spec:
        return False, f"Unknown product: {product_name}"
    if not spec.get("build_enabled", spec.get("production_status") == "active"):
        reason = spec.get("status_reason") or "This generator has not passed canonical review."
        return False, f"{product_name} is not enabled for normal production. {reason}"
    preflight_ok, preflight_message = product_preflight(slug, product_name)
    if not preflight_ok:
        return False, preflight_message

    try:
        delete_existing_product_outputs(slug, product_name)
    except Exception:
        pass

    images = images_dir_for_book(slug)
    if not images or not images.exists():
        return False, "No activity_images found for this book"
    book_dir = find_book_dir(slug)
    proj = project_root()
    # Ensure OUTPUT exists (many generators assume it)
    try:
        outd = output_dir_for_book(slug)
        if outd:
            outd.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    pack_code = read_book_state(slug).get("build", {}).get("pack_code", default_pack_code(slug))
    theme_name = decode_slug(slug)
    stage_icons = ensure_build_icons_staging(slug, product_name=product_name)
    icons_folder_for_build = stage_icons or images
    # Force UTF-8 console output in the child process to prevent UnicodeEncodeError on Windows.
    code = (
        "import os,sys; "
        "os.environ['PYTHONIOENCODING']='utf-8'; "
        "\n"
        "try:\n"
        "    sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n"
        "    sys.stderr.reconfigure(encoding='utf-8', errors='replace')\n"
        "except Exception:\n"
        "    pass\n"
        f"os.chdir(r'{str(book_dir)}'); "
        f"sys.path.insert(0, r'{str(proj)}'); "
        f"from {spec['module']} import {spec['func']} as run; "
        f"ok = run(r'{str(icons_folder_for_build)}', r'{pack_code}', r'{theme_name}'); "
        "sys.exit(0 if ok else 1)"
    )
    def _tail(s: str, n: int = 2000) -> str:
        try:
            s = str(s or "")
            return s[-n:] if len(s) > n else s
        except Exception:
            return ""

    try:
        # On Windows, some downstream scripts can emit non-decodable bytes.
        # Force decoding behavior to avoid UnicodeDecodeError.
        timeout_sec = int(os.environ.get("SF_BUILD_TIMEOUT_SEC", "600") or 600)
        env = os.environ.copy()
        env.setdefault("PYTHONIOENCODING", "utf-8")
        p = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            env=env,
        )
        ok = p.returncode == 0
        if not ok:
            out_tail = _tail(p.stdout or "")
            err_tail = _tail(p.stderr or "")
            msg = (p.stderr or p.stdout or "").splitlines()[-1] if (p.stderr or p.stdout) else "Build failed"
            try:
                st.session_state.sf_last_build = {
                    "ok": False,
                    "product": product_name,
                    "message": msg,
                    "stdout_tail": out_tail,
                    "stderr_tail": err_tail,
                }
            except Exception:
                pass
            return False, msg
        # Write build record
        state = read_book_state(slug)
        built = state.get("build", {})
        recs = built.get("products_built", [])
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        # upsert by product name
        recs = [r for r in recs if r.get("name") != product_name]
        recs.append({"name": product_name, "built_at": now})
        built["products_built"] = recs
        built["last_built_at"] = now
        state["build"] = built
        write_book_state(slug, state)
        # Generate support docs for this product
        try:
            _out = output_dir_for_book(slug)
            if _out:
                _pages = next((s["pages"] for s in PRODUCT_SPECS if s["name"] == product_name), 0)
                write_product_support_docs(_out, pack_code, product_name, display_name, _pages)
        except Exception:
            pass
        try:
            st.session_state.sf_last_build = {
                "ok": True,
                "product": product_name,
                "message": f"{product_name} built",
                "stdout_tail": _tail(p.stdout or ""),
                "stderr_tail": _tail(p.stderr or ""),
            }
        except Exception:
            pass
        return True, f"{product_name} built - {next((s['pages'] for s in PRODUCT_SPECS if s['name']==product_name), '?')} pages"
    except subprocess.TimeoutExpired:
        msg = f"Timed out after {_fmt_secs(int(os.environ.get('SF_BUILD_TIMEOUT_SEC', '600') or 600))}. Try building products one-by-one to find the slow step, or increase SF_BUILD_TIMEOUT_SEC."
        try:
            st.session_state.sf_last_build = {
                "ok": False,
                "product": product_name,
                "message": msg,
                "stdout_tail": "",
                "stderr_tail": "",
            }
        except Exception:
            pass
        return False, msg
    except Exception as e:
        try:
            st.session_state.sf_last_build = {
                "ok": False,
                "product": product_name,
                "message": str(e),
                "stdout_tail": "",
                "stderr_tail": "",
            }
        except Exception:
            pass
        return False, str(e)


# Stage metadata for consistent headers
STAGE_META = {
    "setup": ("1", "Setup", "Confirm the project pathway and anonymous learner-access settings.", "📋"),
    "content": ("2", "Content", "Review grounded vocabulary and teaching content before icon work begins.", "📚"),
    "icons": ("3", "Icons", "Review, approve, and manage Boardmaker/PCS icons for this book.", "🎨"),
    "boardready": ("4", "BoardReady", "Review the canonical 6x6 AAC communication board layout.", "🗣️"),
    "qa": ("5", "Visual QA", "Inspect each icon for quality, clarity, and correctness.", "✅"),
    "build": ("6", "Activities", "Generate, rebuild, and review activity PDFs.", "🏗️"),
    "listing": ("7", "Listing", "Prepare the TPT product listing with title, description, and keywords.", "📝"),
    "promote": ("8", "Promote", "Plan and schedule marketing across Pinterest, Tailwind, and TPT.", "📣"),
}


def stage_header(stage_key: str, display_name: str):
    """Render a consistent header for each build stage tab."""
    meta = STAGE_META.get(stage_key, ("", stage_key.title(), "", ""))
    num, title, desc, icon = meta
    if num:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:4px;'>"
            f"<span style='font-size:28px'>{icon}</span>"
            f"<div><div style='font-size:22px;font-weight:700;color:#006379;line-height:1.2'>"
            f"Step {num}: {title}</div>"
            f"<div style='font-size:13px;color:#587080'>{desc}</div></div></div>",
            unsafe_allow_html=True,
        )
    else:
        st.subheader(title)
    if display_name:
        st.caption(f"Book: **{display_name}**")


def render_build_tab(slug: str, display_name: str):
    stage_header("build", display_name)
    # ── Review Dashboard (current book OUTPUT) ──
    _book_dash_script = project_root() / "Studioforge" / "_build_book_dashboard.py"
    _book_out = output_dir_for_book(slug)
    _book_dash = _book_out / "_REVIEW_DASHBOARD" / "REVIEW_DASHBOARD.html" if _book_out else None
    _rd1, _rd2 = st.columns([1, 3])
    with _rd1:
        if _book_dash and _book_dash.exists():
            if st.button("Open Review Dashboard", type="primary", key=f"open_review_dash_{slug}", help="Open the HTML review dashboard in your browser"):
                try:
                    import webbrowser
                    webbrowser.open(_book_dash.resolve().as_uri())
                    show_toast("success", "Opened review dashboard in browser")
                except Exception as e:
                    show_toast("error", f"Could not open: {e}")
        if st.button("Build/Refresh Dashboard", key=f"refresh_review_dash_{slug}", help="Regenerate the dashboard from the current book's OUTPUT PDFs"):
            try:
                import subprocess
                subprocess.Popen([str(Path(sys.executable)), str(_book_dash_script), slug, str(_book_out)], cwd=str(project_root()))
                show_toast("success", "Building dashboard from current OUTPUT...")
            except Exception as e:
                show_toast("error", f"Could not build dashboard: {e}")
    with _rd2:
        st.caption("The dashboard scans this book's OUTPUT folder for the latest COLOR PDFs — rebuild activities first, then refresh.")

    # Gates
    state = read_book_state(slug)
    kit = st.session_state.get(get_kit_key(slug)) or [str((images_dir_for_book(slug) or Path('')) / fn) for fn in state.get("icons_kit", [])]
    qa_label, qa_pass = read_qa_status(slug)
    gates = workflow_gate_status(slug)
    prerequisites_passed = bool(gates["setup"] and gates["content"] and gates["boardready"])
    readiness = product_readiness(len(kit), qa_pass and prerequisites_passed)
    for name, info in readiness.items():
        preflight_ok, preflight_message = product_preflight(slug, name)
        info["preflight_ok"] = preflight_ok
        info["preflight_message"] = preflight_message
        info["ready"] = bool(info["ready"] and preflight_ok)
    ready_names = {name for name, info in readiness.items() if info["ready"]}

    # Latest icon mtime (used to detect stale products)
    try:
        latest_kit_mtime = None
        try:
            times = []
            for fp in (kit or []):
                try:
                    p = Path(fp)
                    if p.exists():
                        times.append(p.stat().st_mtime)
                except Exception:
                    pass
            latest_kit_mtime = max(times) if times else None
        except Exception:
            latest_kit_mtime = None
    except Exception:
        latest_kit_mtime = None

    # ── Force Rebuild section (always visible at top) ──
    _all_specs = [s for s in PRODUCT_SPECS if s.get("build_enabled", s.get("production_status") == "active")]
    _can_force = bool(_all_specs) and not st.session_state.get("sf_building", False)
    if _can_force:
        st.markdown("#### Rebuild Activities")
        if not ready_names:
            st.caption("QA hasn't been formally passed. Use **Force Rebuild** below to regenerate activities with your latest icons for visual review.")
        _fc1, _fc2 = st.columns([1, 1])
        with _fc1:
            if st.button("Force Rebuild All", type="primary", key=f"tb_force_all_{slug}", help="Rebuild BoardReady board and all enabled activities regardless of QA status"):
                st.session_state.sf_building = True
                all_ok = True
                # Step 1: Regenerate the canonical BoardReady AAC board
                fringe = topic_fringe_words(slug)
                if len(fringe) == 12:
                    st.session_state.sf_building_product = "BoardReady AAC Board"
                    st.session_state.sf_build_total = len(_all_specs) + 1
                    st.session_state.sf_build_index = 0
                    prog = st.progress(0.0)
                    status = st.empty()
                    status.markdown(f"**Building 0 of {len(_all_specs) + 1}:** BoardReady AAC Board")
                    with st.spinner("Generating canonical BoardReady 6x6 board..."):
                        br_ok, br_msg = run_boardready_generator(slug)
                    if not br_ok:
                        show_toast("warning", f"BoardReady skipped: {br_msg}")
                    prog.progress(1.0 / float(len(_all_specs) + 1))
                else:
                    st.session_state.sf_build_total = len(_all_specs)
                    prog = st.progress(0.0)
                    status = st.empty()
                # Step 2: Build all activities
                total_count = len(_all_specs) + (1 if len(fringe) == 12 else 0)
                for idx, spec in enumerate(_all_specs, 1):
                    st.session_state.sf_building_product = spec["name"]
                    st.session_state.sf_build_index = idx
                    status.markdown(f"**Building {idx} of {total_count}:** {spec['name']}")
                    prog.progress(idx / float(total_count + 1))
                    with st.spinner(f"Building {idx} of {total_count}: {spec['name']}..."):
                        ok, msg = run_product_build(slug, spec["name"], display_name)
                    if not ok:
                        show_toast("error", f"Stopped - {spec['name']} failed: {msg}")
                        all_ok = False
                        break
                    prog.progress((idx + 1) / float(total_count + 1))
                st.session_state.sf_building = False
                st.session_state.sf_building_product = None
                st.session_state.sf_build_total = 0
                st.session_state.sf_build_index = 0
                try:
                    status.empty()
                except Exception:
                    pass
                if all_ok:
                    show_toast("success", f"Rebuilt {total_count} activities (including BoardReady).")
                qp_update(view="build", tab="build")
                safe_rerun()
        with _fc2:
            if st.button("Force Rebuild Stale", key=f"tb_force_stale_{slug}", help="Rebuild only activities older than the latest icons"):
                built_now = detect_products_in_output(slug)
                to_build = []
                for spec in _all_specs:
                    info = built_now.get(spec["name"], {})
                    built = bool(info.get("built"))
                    mtime = info.get("mtime") or 0
                    if not built or (latest_kit_mtime and mtime and mtime < latest_kit_mtime):
                        to_build.append(spec)
                if not to_build:
                    show_toast("info", "No stale products - all up to date.")
                else:
                    st.session_state.sf_building = True
                    all_ok = True
                    st.session_state.sf_build_total = len(to_build)
                    st.session_state.sf_build_index = 0
                    prog = st.progress(0.0)
                    status = st.empty()
                    for idx, spec in enumerate(to_build, 1):
                        st.session_state.sf_building_product = spec["name"]
                        st.session_state.sf_build_index = idx
                        status.markdown(f"**Building {idx} of {len(to_build)}:** {spec['name']}")
                        prog.progress((idx - 1) / float(len(to_build)))
                        with st.spinner(f"Building {idx} of {len(to_build)}: {spec['name']}..."):
                            ok, msg = run_product_build(slug, spec["name"], display_name)
                        if not ok:
                            show_toast("error", f"Stopped - {spec['name']} failed: {msg}")
                            all_ok = False
                            break
                        prog.progress(idx / float(len(to_build)))
                    st.session_state.sf_building = False
                    st.session_state.sf_building_product = None
                    st.session_state.sf_build_total = 0
                    st.session_state.sf_build_index = 0
                    try:
                        status.empty()
                    except Exception:
                        pass
                    if all_ok:
                        show_toast("success", f"Rebuilt {len(to_build)} stale activities.")
                    qp_update(view="build", tab="build")
                    safe_rerun()
        st.divider()
    # Ensure 'ok' exists for any later conditional checks
    ok = False
    # Toolbar toggle keys
    diag_key = f"sf_show_diag_{slug}"
    prev_key = f"sf_show_prev_{slug}"
    # Current pack code
    pack_code = ((state.get("build", {}) or {}).get("pack_code") or default_pack_code(slug))
    # Initialize filmstrip selection from saved state
    try:
        sel_key = f"fs_sel_{slug}"
        if sel_key not in st.session_state:
            names_all = [s["name"] for s in PRODUCT_SPECS]
            saved_sel = ((state.get("build", {}) or {}).get("rebuild_selected") or [])
            st.session_state[sel_key] = [n for n in (saved_sel or []) if n in names_all]
    except Exception:
        pass

    # Handle rebuild action from query param
    try:
        rb = qp_get("rebuild")
    except Exception:
        rb = None
    if rb:
        try:
            name = str(rb)
            if not st.session_state.get("sf_building") and name in ready_names:
                st.session_state.sf_building = True
                with st.spinner(f"Building {name}..."):
                    ok, msg = run_product_build(slug, name, display_name)
                st.session_state.sf_building = False
                show_toast("success" if ok else "error", msg)
            elif name not in ready_names:
                info = readiness.get(name, {})
                reason = "QA is not passed" if not qa_pass else f"{info.get('missing_icons', 0)} more icons required"
                show_toast("warning", f"{name} is not ready: {reason}")
        except Exception:
            pass
        qp_update(rebuild=None)
        safe_rerun()

    # Handle open OUTPUT action from query param
    try:
        oo = qp_get("openout")
    except Exception:
        oo = None
    if oo:
        try:
            out = output_dir_for_book(slug)
            if out and out.exists():
                open_folder(out)
        except Exception:
            pass
        qp_update(openout=None)
        safe_rerun()
    # Handle open FINAL action from query param
    try:
        ofn = qp_get("openfinal")
    except Exception:
        ofn = None
    if ofn:
        try:
            out = output_dir_for_book(slug)
            fi = (out / "FINAL") if out else None
            if fi and fi.exists():
                open_folder(fi)
        except Exception:
            pass
        qp_update(openfinal=None)
        safe_rerun()


    # Icon usage control (prevents unwanted/missing icons from leaking into builds)
    approved_names = approved_icon_filenames_for_book(slug)
    with st.expander("Icon set used for builds", expanded=False):
        st.caption(f"Approved icons available: {len(approved_names)}")
        st.caption("Builds use the book kit, excluding any QA items marked Missing.")
        if not approved_names:
            st.info("No approved icons found yet. Add icons to the book kit first.")
        else:
            # Matching generator uses exactly 4 icons; let the user choose them.
            try:
                chosen = ((state.get("build", {}) or {}).get("matching_icons") or [])
            except Exception:
                chosen = []
            chosen = [c for c in chosen if c in approved_names]
            defaults = chosen[:4] if chosen else approved_names[:4]
            if len(approved_names) >= 4:
                sel = st.multiselect(
                    "Matching: choose 4 icons",
                    options=approved_names,
                    default=defaults,
                    max_selections=4,
                    key=f"match_icons_sel_{slug}",
                )
                if st.button("Save Matching icon selection", key=f"match_icons_save_{slug}"):
                    st_data = read_book_state(slug)
                    b = st_data.get("build", {}) if isinstance(st_data.get("build"), dict) else {}
                    b["matching_icons"] = list(sel)
                    st_data["build"] = b
                    write_book_state(slug, st_data, toast_ok=True)
                    show_toast("success", "Saved")
                    safe_rerun()
            else:
                st.info("Matching requires at least 4 approved icons.")

    # QA unlock is handled in the status section below

    # Status section
    if not ready_names:
        if not prerequisites_passed:
            missing_gates = [label for key, label in (("setup", "Setup"), ("content", "Content review"), ("boardready", "BoardReady review")) if not gates[key]]
            st.warning("Prerequisites needed: " + ", ".join(missing_gates))
        elif not qa_pass:
            st.warning("Visual QA has not been marked as passed yet.")
            # Offer to mark QA as passed if all icons have been reviewed
            try:
                candidates = qa_candidates(slug, limit=48)
                ensure_qa_state(slug, candidates)
                qstate: dict = st.session_state.get(qa_state_key(slug), {})
                total = len(qstate)
                resolved = sum(1 for v in qstate.values() if v.get("status") in {"accepted", "missing", "replaced"})
                if total and resolved == total:
                    if st.button("Mark QA as Passed (unlock builds)", type="primary", key=f"build_unlock_qa_{slug}"):
                        persist_qa_pass(slug)
                        update_qa_log(slug, True)
                        clear_stage_caches(slug)
                        show_toast("success", "QA marked as passed — builds unlocked")
                        qp_update(view="build", tab="build")
                        safe_rerun()
                else:
                    st.caption(f"Icon review: {resolved}/{total} resolved. Go to the Visual QA tab to finish.")
            except Exception:
                pass
        else:
            available = [spec for spec in PRODUCT_SPECS if spec.get("build_enabled", spec.get("production_status") == "active")]
            minimums = [int(spec.get("min_icons", 0) or 0) for spec in available if int(spec.get("min_icons", 0) or 0) > 0]
            minimum = min(minimums) if minimums else 0
            if len(kit) < minimum:
                st.info(f"Add {minimum - len(kit)} more approved icons to unlock the first activities.")
            else:
                missing_content = sorted({info.get("preflight_message") for info in readiness.values() if info.get("build_enabled") and not info.get("preflight_ok")})
                st.info("Complete the required product content: " + "; ".join(message for message in missing_content if message))

    if len(ready_names) < len(PRODUCT_SPECS):
        blocked = [
            f"{name} (+{info['missing_icons']} icons)"
            for name, info in readiness.items()
            if not info["ready"] and info["missing_icons"]
        ]
        if blocked:
            st.caption("Ready now: " + ", ".join(sorted(ready_names)))
            st.caption("Needs more icons: " + ", ".join(blocked))

    built_info = detect_products_in_output(slug)

    with st.expander("Build diagnostics", expanded=bool(st.session_state.get(diag_key, False))):
        bd = find_book_dir(slug)
        outd = output_dir_for_book(slug)
        st.caption(f"Book folder: {str(bd) if bd else '(not found)'}")
        st.caption(f"OUTPUT folder: {str(outd) if outd else '(not found)'}")
        try:
            st.caption(f"OUTPUT exists: {bool(outd and outd.exists())}")
        except Exception:
            pass
        last = st.session_state.get("sf_last_build")
        if last and isinstance(last, dict):
            st.markdown(f"**Last build:** {'OK' if last.get('ok') else 'FAILED'} - {last.get('product','')} - {last.get('message','')}")
            if last.get("stderr_tail"):
                st.text_area("stderr (tail)", value=str(last.get("stderr_tail")), height=140)
            if last.get("stdout_tail"):
                st.text_area("stdout (tail)", value=str(last.get("stdout_tail")), height=140)
        else:
            st.caption("No build has run in this session yet.")

    # One at a time build lock
    building = st.session_state.get("sf_building", False)
    building_name = st.session_state.get("sf_building_product")

    # Persistent status panel
    if building:
        total_steps = int(st.session_state.get("sf_build_total", 0) or 0)
        idx_step = int(st.session_state.get("sf_build_index", 0) or 0)
        if total_steps > 0:
            st.info(f"Building {idx_step}/{total_steps}: {building_name or '...'}")
            try:
                st.progress(min(max(idx_step, 0), total_steps) / float(total_steps))
            except Exception:
                pass
        else:
            st.info(f"Building: {building_name or '...'}")

    st.subheader(f"Build products for {display_name}")
    pilot_names = [spec["name"] for spec in PRODUCT_SPECS if spec.get("build_enabled") and spec.get("production_status") == "pilot_review"]
    if pilot_names:
        st.info("Pilot products can be generated for visual review, but they are excluded from final customer packaging until you approve their launch status.")

    # ── Simple action bar ──
    _ab1, _ab2, _ab3, _ab4 = st.columns([2, 1, 1, 1])
    with _ab1:
        unlocked_tb = [s for s in PRODUCT_SPECS if s["name"] in ready_names]
        if st.button("Generate All", type="primary", key=f"tb_rebuild_all_{slug}", disabled=st.session_state.get("sf_building", False) or not unlocked_tb, help="Build all ready products" if unlocked_tb else "Complete icon review and QA first"):
            st.session_state.sf_building = True
            all_ok = True
            st.session_state.sf_build_total = len(unlocked_tb)
            st.session_state.sf_build_index = 0
            prog = st.progress(0.0)
            status = st.empty()
            for idx, spec in enumerate(unlocked_tb, 1):
                st.session_state.sf_building_product = spec["name"]
                st.session_state.sf_build_index = idx
                status.markdown(f"**Building {idx} of {len(unlocked_tb)}:** {spec['name']}")
                prog.progress((idx - 1) / float(len(unlocked_tb)))
                with st.spinner(f"Building {idx} of {len(unlocked_tb)}: {spec['name']}..."):
                    ok, msg = run_product_build(slug, spec["name"], display_name)
                if not ok:
                    show_toast("error", f"Stopped - {spec['name']} failed: {msg}")
                    all_ok = False
                    break
                prog.progress(idx / float(len(unlocked_tb)))
            st.session_state.sf_building = False
            st.session_state.sf_building_product = None
            st.session_state.sf_build_total = 0
            st.session_state.sf_build_index = 0
            try:
                status.empty()
            except Exception:
                pass
            if all_ok:
                show_toast("success", f"All {len(unlocked_tb)} products built.")
            qp_update(view="build", tab="build")
            safe_rerun()
    with _ab2:
        if st.button("Rebuild Stale", key=f"tb_rebuild_stale_{slug}", disabled=st.session_state.get("sf_building", False) or not unlocked_tb, help="Rebuild products older than latest icons"):
            built_now = detect_products_in_output(slug)
            to_build = []
            for spec in unlocked_tb:
                info = built_now.get(spec["name"], {})
                built = bool(info.get("built"))
                mtime = info.get("mtime") or 0
                if not built or (latest_kit_mtime and mtime and mtime < latest_kit_mtime):
                    to_build.append(spec)
            if not to_build:
                show_toast("info", "No stale products - all up to date.")
            else:
                st.session_state.sf_building = True
                all_ok = True
                st.session_state.sf_build_total = len(to_build)
                st.session_state.sf_build_index = 0
                prog = st.progress(0.0)
                status = st.empty()
                for idx, spec in enumerate(to_build, 1):
                    st.session_state.sf_building_product = spec["name"]
                    st.session_state.sf_build_index = idx
                    status.markdown(f"**Building {idx} of {len(to_build)}:** {spec['name']}")
                    prog.progress((idx - 1) / float(len(to_build)))
                    with st.spinner(f"Building {idx} of {len(to_build)}: {spec['name']}..."):
                        ok, msg = run_product_build(slug, spec["name"], display_name)
                    if not ok:
                        show_toast("error", f"Stopped - {spec['name']} failed: {msg}")
                        all_ok = False
                        break
                    prog.progress(idx / float(len(to_build)))
                st.session_state.sf_building = False
                st.session_state.sf_building_product = None
                st.session_state.sf_build_total = 0
                st.session_state.sf_build_index = 0
                try:
                    status.empty()
                except Exception:
                    pass
                if all_ok:
                    show_toast("success", f"Rebuilt {len(to_build)} stale products.")
                qp_update(view="build", tab="build")
                safe_rerun()
    with _ab3:
        if st.button("Open OUTPUT", key=f"tb_open_out_{slug}"):
            out = output_dir_for_book(slug)
            if out and out.exists():
                open_folder(out)
            else:
                show_toast("info", "OUTPUT folder not found")
    with _ab4:
        # Pack code editor
        pc_val = st.text_input("Pack code", value=pack_code, max_chars=12, key=f"tb_pack_{slug}", help="Short code used in output filenames")
        if st.button("Save pack", key=f"tb_pack_save_{slug}"):
            raw_pack_code = st.session_state.get(f"tb_pack_{slug}", pack_code)
            clean_pack_code = sanitise_pack_code(raw_pack_code)
            if not clean_pack_code:
                st.error("Enter at least one letter or number.")
            else:
                st_data = read_book_state(slug)
                b = st_data.get("build", {}) if isinstance(st_data.get("build"), dict) else {}
                b["pack_code"] = clean_pack_code
                st_data["build"] = b
                write_book_state(slug, st_data, toast_ok=True)
                show_toast("success", f"Pack code saved: {clean_pack_code}")
                safe_rerun()

    # Horizontal filmstrip of product thumbnails (preview-only)
    try:
        out_dir_fs = output_dir_for_book(slug)
        if out_dir_fs and out_dir_fs.exists():
            # Filmstrip metrics
            try:
                pass
            except Exception:
                pass
            # Filmstrip metrics
            try:
                names_built = [n for n, inf in built_info.items() if inf.get("built")]
                unbuilt_n = max(0, len(PRODUCT_SPECS) - len(names_built))
                total_pages = 0
                for n in names_built:
                    fs = _product_output_files(out_dir_fs, n)
                    pp = fs.get("color") or fs.get("bw")
                    if pp and pp.exists() and pp.suffix.lower() == ".pdf":
                        total_pages += (_pdf_page_count(pp) or 0)
                stale_n = 0
                try:
                    if latest_kit_mtime:
                        for n in names_built:
                            mt = built_info.get(n, {}).get("mtime") or 0
                            if mt and mt < latest_kit_mtime:
                                stale_n += 1
                except Exception:
                    stale_n = 0
                mc1, mc2, mc3, mc4 = st.columns(4)
                with mc1:
                    st.metric("Built", len(names_built))
                with mc2:
                    st.metric("Unbuilt", unbuilt_n)
                with mc3:
                    st.metric("Stale", stale_n)
                with mc4:
                    st.metric("Pages", f"{total_pages}+")
            except Exception:
                pass
            # Filmstrip controls
            fs_c1, fs_c2, fs_c3 = st.columns([1, 1, 2])
            with fs_c1:
                fs_filter = st.selectbox(
                    "Filter",
                    options=["All", "Built", "Unbuilt", "Stale"],
                    index=0,
                    key=f"fs_filter_{slug}",
                    help="Show only built, unbuilt, or stale products",
                )
            with fs_c2:
                fs_sort = st.selectbox(
                    "Sort",
                    options=["Name", "Recent"],
                    index=1,
                    key=f"fs_sort_{slug}",
                    help="Sort by product name or most recent build",
                )
            with fs_c3:
                st.text_input(
                    "Search",
                    value=st.session_state.get(f"fs_query_{slug}", ""),
                    key=f"fs_query_{slug}",
                    help="Filter by product name",
                )

            # Rebuild selected control
            rs1, rs2 = st.columns([3, 1])
            with rs1:
                st.multiselect(
                    "Rebuild selected",
                    options=[s["name"] for s in PRODUCT_SPECS],
                    key=f"fs_sel_{slug}",
                )
                qs1, qs2, qs3, qs4 = st.columns([1, 1, 1, 1])
                with qs1:
                    if st.button("Stale", key=f"fs_sel_btn_stale_{slug}", help="Select stale products"):
                        names_built = [n for n, inf in built_info.items() if inf.get("built")]
                        stale_names = []
                        try:
                            if latest_kit_mtime:
                                for n in names_built:
                                    mt = built_info.get(n, {}).get("mtime") or 0
                                    if mt and mt < latest_kit_mtime:
                                        stale_names.append(n)
                        except Exception:
                            pass
                        st.session_state[f"fs_sel_{slug}"] = stale_names
                        safe_rerun()
                with qs2:
                    if st.button("Built", key=f"fs_sel_btn_built_{slug}", help="Select built products"):
                        st.session_state[f"fs_sel_{slug}"] = [n for n, inf in built_info.items() if inf.get("built")]
                        safe_rerun()
                with qs3:
                    if st.button("Clear", key=f"fs_sel_btn_clear_{slug}", help="Clear selection"):
                        st.session_state[f"fs_sel_{slug}"] = []
                        safe_rerun()
                with qs4:
                    if st.button("Save selection", key=f"fs_sel_btn_save_{slug}", help="Save selection for this book"):
                        st_data = read_book_state(slug)
                        b = st_data.get("build", {}) if isinstance(st_data.get("build"), dict) else {}
                        b["rebuild_selected"] = list(st.session_state.get(f"fs_sel_{slug}", []))
                        st_data["build"] = b
                        write_book_state(slug, st_data, toast_ok=True)
                        show_toast("success", "Selection saved")
            with rs2:
                selected_names = list(st.session_state.get(f"fs_sel_{slug}", []))
                selected_ready = [name for name in selected_names if name in ready_names]
                dis_sel = bool(st.session_state.get("sf_building", False) or not selected_ready)
                if st.button("Rebuild Selected", key=f"tb_rebuild_selected_{slug}", disabled=dis_sel, help="Rebuild selected activities that have enough approved icons"):
                    names = list(st.session_state.get(f"fs_sel_{slug}", []))
                    unlocked_list = [s for s in PRODUCT_SPECS if s["name"] in names and s["name"] in ready_names]
                    if not unlocked_list:
                        show_toast("info", "No products selected")
                    else:
                        st.session_state.sf_building = True
                        all_ok = True
                        st.session_state.sf_build_total = len(unlocked_list)
                        st.session_state.sf_build_index = 0
                        prog = st.progress(0.0)
                        status = st.empty()
                        for idx, spec in enumerate(unlocked_list, 1):
                            st.session_state.sf_building_product = spec["name"]
                            st.session_state.sf_build_index = idx
                            status.markdown(f"**Building {idx} of {len(unlocked_list)}:** {spec['name']}")
                            prog.progress((idx - 1) / float(len(unlocked_list)))
                            with st.spinner(f"Building {idx} of {len(unlocked_list)}: {spec['name']}..."):
                                ok, msg = run_product_build(slug, spec["name"], display_name)
                            if not ok:
                                show_toast("error", f"Stopped - {spec['name']} failed: {msg}")
                                all_ok = False
                                break
                            prog.progress(idx / float(len(unlocked_list)))
                        st.session_state.sf_building = False
                        st.session_state.sf_building_product = None
                        st.session_state.sf_build_total = 0
                        st.session_state.sf_build_index = 0
                        try:
                            status.empty()
                        except Exception:
                            pass
                        if all_ok:
                            show_toast("success", f"Rebuilt {len(unlocked_list)} selected products.")
                        qp_update(view="build", tab="build")
                        safe_rerun()

            st.markdown(
                """
<style>
.sf-filmstrip { display: grid; grid-auto-flow: column; grid-auto-columns: 150px; overflow-x: auto; gap: var(--space-2); padding: var(--space-2) 2px var(--space-3) 2px; }
.sf-filmstrip .tile { position: relative; border: 1px solid var(--brd-color); border-radius: var(--brd-radius); padding: var(--space-2); background: #FFFFFF; }
.sf-filmstrip img { width: 100%; height: 90px; object-fit: contain; display: block; background: #F7F7F7; border-radius: calc(var(--brd-radius) - 2px); }
.sf-filmstrip .name { text-align: center; font-size: 12px; margin-top: var(--space-1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sf-filmstrip .badge { position: absolute; top: var(--space-1); left: var(--space-1); padding: 2px 6px; border-radius: 10px; font-size: 11px; }
.sf-filmstrip .time { text-align: center; font-size: 11px; color: #666; margin-top: 2px; }
.sf-filmstrip .act { position: absolute; top: var(--space-1); right: var(--space-1); text-decoration: none; font-size: 14px; background: #FFFFFF; border: 1px solid var(--brd-color); border-radius: 12px; padding: 0 6px; }
.sf-filmstrip .act2 { position: absolute; top: var(--space-1); right: 34px; text-decoration: none; font-size: 14px; background: #FFFFFF; border: 1px solid var(--brd-color); border-radius: 12px; padding: 0 6px; }
 .sf-filmstrip .act3 { position: absolute; top: var(--space-1); right: 62px; text-decoration: none; font-size: 14px; background: #FFFFFF; border: 1px solid var(--brd-color); border-radius: 12px; padding: 0 6px; }
.sf-filmstrip .pc { position: absolute; bottom: var(--space-1); right: var(--space-1); background: rgba(0,0,0,0.6); color: #fff; font-size: 11px; padding: 0 6px; border-radius: 10px; }
.sf-filmstrip .busy { position: absolute; inset: var(--space-1); background: rgba(255,255,255,0.7); border-radius: var(--brd-radius); display: flex; align-items: center; justify-content: center; font-size: 13px; color: #333; }
.sf-filmstrip .tile.stale { border-color: #FBBF24; }
.sf-filmstrip .badge2 { position: absolute; top: var(--space-1); left: 58px; padding: 2px 6px; border-radius: 10px; font-size: 11px; background:#FEF3C7;color:#92400E }
/* Hover zoom + smooth transition */
.sf-filmstrip .tile { overflow: visible; }
.sf-filmstrip img { transition: transform 0.12s ease; }
.sf-filmstrip .tile:hover img { transform: scale(1.6); box-shadow: 0 6px 16px rgba(0,0,0,0.2); }
</style>
                """,
                unsafe_allow_html=True,
            )
            # Prepare entries with metadata
            entries = []
            for spec in PRODUCT_SPECS:
                name = spec["name"]
                files = _product_output_files(out_dir_fs, name)
                p = files.get("color") or files.get("bw")
                built = bool(p and p.exists())
                mtime = None
                try:
                    mtime = p.stat().st_mtime if p and p.exists() else None
                except Exception:
                    mtime = None
                stale = bool(latest_kit_mtime and mtime and mtime < latest_kit_mtime)
                entries.append({"spec": spec, "name": name, "files": files, "p": p, "built": built, "mtime": mtime, "stale": stale})

            # Filter
            if fs_filter == "Built":
                entries = [e for e in entries if e["built"]]
            elif fs_filter == "Unbuilt":
                entries = [e for e in entries if not e["built"]]
            elif fs_filter == "Stale":
                entries = [e for e in entries if e.get("stale")]

            # Search filter then sort
            fs_q = str(st.session_state.get(f"fs_query_{slug}", "") or "").strip().lower()
            if fs_q:
                entries = [e for e in entries if fs_q in e["name"].lower()]
            # Sort
            if fs_sort == "Recent":
                entries.sort(key=lambda e: (e["mtime"] or 0), reverse=True)
            else:
                entries.sort(key=lambda e: e["name"].lower())

            # If no entries match the filter, show a friendly note
            if not entries:
                try:
                    st.info("No stale products - all up to date." if fs_filter == "Stale" else "No products match this filter.")
                except Exception:
                    pass

            html = ["<div class='sf-filmstrip'>"]
            for ent in entries:
                spec = ent["spec"]
                name = ent["name"]
                name_short = name if len(name) <= 18 else name[:17] + "..."
                files = ent["files"]
                p = ent["p"]
                img_tag = ""
                try:
                    if p and p.exists():
                        tp = _make_thumbnail(p)
                        if tp and tp.exists():
                            data = tp.read_bytes()
                            b64 = base64.b64encode(data).decode("ascii")
                            img_tag = f"<img src='data:image/png;base64,{b64}' alt='{name_short}'>"
                except Exception:
                    img_tag = ""
                info = built_info.get(name, {}) if 'built_info' in locals() else {}
                ts = None
                try:
                    ts = (p.stat().st_mtime if p and p.exists() else info.get("mtime"))
                except Exception:
                    ts = info.get("mtime")
                when = datetime.fromtimestamp(ts).strftime('%d/%m/%Y %H:%M') if ts else ""
                has_color = bool(files.get("color") and files.get("color").exists())
                has_bw = bool(files.get("bw") and files.get("bw").exists())
                if has_color and has_bw:
                    badge = "<div class='badge' title='Built: Color + B/W present' style='background:#D1FADF;color:#065F46'>Built</div>"
                elif p:
                    badge = "<div class='badge' title='Partial: Missing either Color or B/W' style='background:#FEF3C7;color:#92400E'>Partial</div>"
                else:
                    badge = "<div class='badge' title='Not built: No outputs yet' style='background:#EEE;color:#555'>Not built</div>"
                time_html = f"<div class='time'>{when}</div>" if when else ""
                href = Path(p).resolve().as_uri() if p and p.exists() else "#"
                q = f"active_book={urllib.parse.quote(str(slug))}&view=build&tab=build&rebuild={urllib.parse.quote(name)}"
                href_rebuild = f"?{q}"
                # Page count (for PDFs only)
                pages_html = ""
                try:
                    if p and p.exists() and p.suffix.lower() == ".pdf":
                        pc = _pdf_page_count(p)
                        if pc:
                            pages_html = f"<div class='pc'>{pc}p</div>"
                except Exception:
                    pages_html = ""
                # FINAL presence (for per-tile quick open)
                has_final = False
                try:
                    # sanitize product name for FINAL file name matching
                    safe_name = name.replace(" ", "_").replace("\n", "_").replace("/", "-")
                    fn_base = f"{pack_code}_{safe_name}_FINAL"
                    f_color = (out_dir_fs / "FINAL" / f"{fn_base}_COLOR.pdf") if out_dir_fs else None
                    f_bw = (out_dir_fs / "FINAL" / f"{fn_base}_BW.pdf") if out_dir_fs else None
                    has_final = bool((f_color and f_color.exists()) or (f_bw and f_bw.exists()))
                except Exception:
                    has_final = False
                is_stale = bool(latest_kit_mtime and ts and ts < latest_kit_mtime)
                stale_badge = "<div class='badge2' title='Stale: Icons newer than this build'>Stale</div>" if is_stale else ""
                busy = "<div class='busy'>Building...</div>" if (st.session_state.get("sf_building") and st.session_state.get("sf_building_product") == name) else ""
                cls = "tile stale" if is_stale else "tile"
                final_btn = ("<a class='act3' href='?openfinal=1' title='Open FINAL'>Final</a>" if has_final else "")
                tile = f"<div class='{cls}'>{badge}{stale_badge}<a class='act' href='{href_rebuild}' title='Rebuild {name}'>Rebuild</a><a class='act2' href='?openout=1' title='Open OUTPUT'>Output</a>{final_btn}<a href='{href}' target='_blank' title='{name}'>{img_tag}</a>{pages_html}{busy}<div class='name'>{name_short}</div>{time_html}</div>"
                html.append(tile)
            html.append("</div>")
            st.markdown("\n".join(html), unsafe_allow_html=True)
            # Keyboard navigation for filmstrip (Left/Right arrows)
            try:
                components.html(
                    """
<script>
(function(){
  if (window._sfFilmstripKeysBound) return; window._sfFilmstripKeysBound = true;
  window.addEventListener('keydown', function(e){
    var fs = document.querySelector('.sf-filmstrip'); if(!fs) return;
    if (e.key === 'ArrowRight') { fs.scrollBy({left: 180, behavior: 'smooth'}); }
    if (e.key === 'ArrowLeft') { fs.scrollBy({left: -180, behavior: 'smooth'}); }
  }, {passive: true});
})();
</script>
                    """,
                    height=0,
                )
            except Exception:
                pass
    except Exception:
        pass
    # Compact product actions (thumbnails + quick actions)
    try:
        out_dir_quick = output_dir_for_book(slug)
        if out_dir_quick and out_dir_quick.exists():
            with st.expander("Product actions", expanded=False):
                st.markdown(
                """
                <style>
                .sf-previews [data-testid="stImage"] img { width: 100% !important; height: 120px !important; object-fit: contain !important; background: #F7F7F7; border: 1px solid var(--brd-color); border-radius: var(--brd-radius); }
                .sf-previews .sf-prev-name { text-align: center; font-size: 12px; margin-top: var(--space-1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
                .sf-previews .sf-prev-actions .stButton>button { padding: 2px 6px !important; min-height: 28px !important; font-size: 14px !important; }
                .sf-previews .sf-prev-actions { margin-top: var(--space-1); }
                </style>
                """,
                unsafe_allow_html=True,
                )
                st.markdown('<div class="sf-previews">', unsafe_allow_html=True)
                cols_prev = st.columns(6)
                for i, spec in enumerate(PRODUCT_SPECS):
                    name = spec["name"]
                    name_short = name if len(name) <= 16 else name[:15] + "..."
                    files = _product_output_files(out_dir_quick, name)
                    p = files.get("color") or files.get("bw")
                    with cols_prev[i % 6]:
                        if p and p.exists():
                            try:
                                if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                                    st.image(str(p), width="stretch")
                                elif p.suffix.lower() == ".pdf" and fitz is not None:
                                    pg = fitz.open(str(p)).load_page(0)
                                    pix = pg.get_pixmap(matrix=fitz.Matrix(1.3, 1.3), alpha=False)
                                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                                    st.image(img, width="stretch")
                                else:
                                    pass
                            except Exception:
                                pass
                        else:
                            pass
                        # Name (truncated single line)
                        st.markdown(f"<div class='sf-prev-name'>{name_short}</div>", unsafe_allow_html=True)
                        # Quick tiny action buttons
                        st.markdown('<div class="sf-prev-actions">', unsafe_allow_html=True)
                        ac1, ac2, ac3 = st.columns([1, 1, 1])
                        with ac1:
                            if st.button("Rebuild", key=f"gal_rebuild_{i}_{slug}", help=f"Rebuild {name}", disabled=name not in ready_names) and not st.session_state.get("sf_building"):
                                st.session_state.sf_building = True
                                st.session_state.sf_building_product = name
                                with st.spinner(f"Building {name}..."):
                                    ok, msg = run_product_build(slug, name, display_name)
                                st.session_state.sf_building = False
                                st.session_state.sf_building_product = None
                                show_toast("success" if ok else "error", msg)
                                qp_update(view="build", tab="build")
                                safe_rerun()
                        with ac2:
                            if st.button("Output", key=f"gal_open_{i}_{slug}", help="Open OUTPUT"):
                                outp = output_dir_for_book(slug)
                                if outp and outp.exists():
                                    open_folder(outp)
                        with ac3:
                            if p and p.exists():
                                try:
                                    st.download_button("Download", data=p.read_bytes(), file_name=p.name, key=f"gal_dl_{i}_{slug}")
                                except Exception:
                                    pass
                        st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    except Exception:
        pass

    

    out_dir = output_dir_for_book(slug)
    if out_dir and out_dir.exists():
        exts = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
        outputs = [p for p in out_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts]
        outputs.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        if outputs:
            with st.expander("Preview outputs", expanded=bool(st.session_state.get(prev_key, False))):
                aac_only = st.checkbox("AAC only", value=True, key=f"out_prev_aac_{slug}")
                items = outputs
                if aac_only:
                    items = [p for p in items if any(tok in p.name.lower() for tok in ["aac", "board", "sentence", "strip", "core"]) ]
                if not items:
                    st.caption("No AAC outputs found yet. Build an AAC product first, or uncheck 'AAC only'.")
                else:
                    labels = [f"{p.name}  -  {datetime.fromtimestamp(p.stat().st_mtime).strftime('%d/%m/%Y %H:%M')}" for p in items[:50]]
                    idx = st.selectbox("File", options=list(range(len(labels))), format_func=lambda i: labels[i], key=f"out_prev_sel_{slug}")
                    chosen = items[int(idx)]
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        if st.button("Open OUTPUT folder", key=f"out_prev_open_{slug}"):
                            open_folder(out_dir)
                    with c2:
                        st.download_button("Download", data=chosen.read_bytes(), file_name=chosen.name)
                    if chosen.suffix.lower() == ".pdf":
                        if fitz is None:
                            st.info("PDF preview requires PyMuPDF (fitz). Use Download for now.")
                        else:
                            try:
                                doc = fitz.open(str(chosen))
                                pg = doc.load_page(0)
                                pix = pg.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                                st.image(img, caption=chosen.name)
                            except Exception as e:
                                st.info(f"Could not preview PDF: {e}")
                    else:
                        try:
                            st.image(str(chosen), caption=chosen.name)
                        except Exception:
                            pass

    available_specs = [spec for spec in PRODUCT_SPECS if spec.get("build_enabled", spec.get("production_status") == "active")]
    review_specs = [spec for spec in PRODUCT_SPECS if not spec.get("build_enabled", spec.get("production_status") == "active")]
    for spec in available_specs:
        name = spec["name"]
        info = built_info.get(name, {"built": False, "mtime": None})
        built = bool(info.get("built"))
        last = datetime.fromtimestamp(info["mtime"]).strftime("%d/%m/%Y %H:%M") if info.get("mtime") else None

        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            status = "Built" if built else ("Building..." if building and building_name == name else "Not built")
            release_label = "Canonical" if spec.get("production_status") == "active" else "Pilot - review output"
            st.markdown(f"**{name}**  |  {spec['pages']} pages  |  {status}  |  {release_label}{'  |  ' + last if last and built else ''}")
        with c2:
            ready = readiness[name]
            disabled = building or not ready["ready"]
            label = "Rebuild" if built else "Build"
            help_txt = None
            if disabled and not building:
                needs = []
                if not ready.get("build_enabled", True):
                    needs.append(ready.get("status_reason") or "generator review")
                if not ready.get("preflight_ok", True):
                    needs.append(ready.get("preflight_message") or "reviewed product content")
                if ready["missing_icons"]:
                    needs.append(f"{ready['missing_icons']} more approved icons")
                if not ready["qa_passed"]:
                    needs.append("workflow gates and visual QA")
                help_txt = "Complete " + " and ".join(needs) + " first."
            if st.button(label, key=f"build_{name}", disabled=disabled, help=help_txt):
                st.session_state.sf_building = True
                st.session_state.sf_building_product = name
                with st.spinner(f"Building {name}..."):
                    ok, msg = run_product_build(slug, name, display_name)
                st.session_state.sf_building = False
                st.session_state.sf_building_product = None
                if ok:
                    show_toast("success", msg)
                else:
                    show_toast("error", f"{name} failed - {msg}")
                qp_update(view="build", tab="build")
                safe_rerun()
        with c3:
            if built and info.get("path"):
                if st.button("Open Output", key=f"open_{name}"):
                    out = output_dir_for_book(slug)
                    if out and out.exists():
                        open_folder(out)
                    else:
                        show_toast("info", "OUTPUT folder not found")

    if review_specs:
        with st.expander(f"Products not available yet ({len(review_specs)})", expanded=False):
            st.caption("These generators remain disabled until their content and visual baselines are approved.")
            for spec in review_specs:
                st.markdown(f"**{spec['name']}** — {spec.get('status_reason', 'Canonical review required.')}")

    pass


    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Phase 5B â€” Covers section (Canva Bulk Create + merge helper)
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.divider()
    st.markdown("### TPT Marketing")
    st.info("Recommended order: generate the 4 automatic TPT pages, preview them, create an optional freebie, then Finalize & Package. Skip the Canva controls unless you specifically want the purchased Canva design.")

    out_dir = output_dir_for_book(slug)
    if not out_dir or not out_dir.exists():
        st.info("Build products first to enable Covers.")
        return

    pack_code = read_book_state(slug).get("build", {}).get("pack_code", default_pack_code(slug))
    built_info = detect_products_in_output(slug)

    # Show built products and page counts (actual PDF counts)
    total_pages = 0
    built_count = 0
    order = [
        "Book Participation Pieces",
        "Matching",
        "Find & Cover",
        "AAC Board",
        "Word Search",
        "AAC Sentence Building",
        "Sorting Cards",
        "Bingo",
        "Spin & Cover",
        "Yes/No Questions",
    ]
    for name in order:
        if built_info.get(name, {}).get("built"):
            pages = 0
            files = _product_output_files(out_dir, name)
            p = files.get("color") or files.get("bw")
            if p:
                pages = _pdf_page_count(p)
            st.success(f"**{name}** - {pages} pages")
            total_pages += max(0, int(pages))
            built_count += 1
        else:
            st.caption(f"{name} - not built")
    st.caption(f"Total: {total_pages} pages across {built_count} products")

    st.divider()
    st.markdown("#### Legacy Canva Bulk Create (optional)")
    csv_key = f"covers_csv_{slug}"
    if st.button("Generate Cover CSV", key=csv_key):
        try:
            title = display_name or decode_slug(slug)
            csv_content = build_cover_csv(slug, title, built_info, out_dir, pack_code)
            st.download_button(
                label="Download CSV",
                data=csv_content,
                file_name=f"{slug}_canva_covers.csv",
                mime="text/csv",
                key=f"dl_csv_{slug}",
            )
        except Exception as e:
            st.error(f"CSV generation failed: {e}")
    st.caption("Optional fallback: import this CSV into Canva Bulk Create if you want to use the purchased templates instead of StudioForge’s automatic pages.")

    st.divider()
    st.markdown("#### Optional Canva files")
    st.caption("Only use these checks if you choose the legacy Canva workflow.")
    cstate = load_cover_state(slug)
    all_done = True
    labels = [
        "Cover image (image 1) saved",
        "What's Included (image 2) saved",
        "Closer Look (image 3) saved",
        "How to Use (image 4) saved",
    ]
    for i, lbl in enumerate(labels):
        key = f"{slug}_cover_{i}"
        cur = bool(cstate.get(f"cover_{i}", False))
        val = st.checkbox(lbl, value=cur, key=key)
        cstate[f"cover_{i}"] = bool(val)
        if not val:
            all_done = False
    save_cover_state(slug, cstate)

    st.divider()
    # Show WARN for any missing Canva cover PDFs (do not block merge display)
    covers_root = project_root() / "covers" / slug
    expected = [
        f"{pack_code}_cover.pdf",
        f"{pack_code}_whats_included.pdf",
        f"{pack_code}_closer_look.pdf",
        f"{pack_code}_how_to_use.pdf",
    ]
    missing: list[str] = []
    try:
        for fn in expected:
            p = covers_root / fn
            if not p.exists():
                missing.append(str(p))
    except Exception:
        pass
    for m in missing:
        try:
            rel = os.path.relpath(m, start=str(project_root())) if project_root().exists() else m
        except Exception:
            rel = m
        st.caption(f"Optional Canva file not found: {rel.replace(chr(92), '/')}" )

    # Optional: Generate listing images (requires covers or content PDFs)
    st.markdown("#### Generate Final TPT Marketing Pages")
    st.caption("Creates the cover plus all three supporting thumbnails as upload-ready 1200 × 1200 PNG files.")
    if st.button("Generate 4 TPT Marketing Pages", key=f"gen_imgs_{slug}", type="primary"):
        try:
            title = display_name or decode_slug(slug)
            imgs = generate_tpt_marketing_pages(slug, pack_code, out_dir, built_info, title)
            if imgs:
                st.success(f"Created {len(imgs)} upload-ready images under TPT_UPLOAD/IMAGES/{pack_code}/")
                # Preview grid
                cols_prev = st.columns(3)
                for i, p in enumerate(imgs[:8]):
                    with cols_prev[i % 3]:
                        try:
                            st.image(str(p), caption=p.name)
                        except Exception:
                            pass
                # Offer downloads and open folder
                try:
                    images_dir_local = out_dir / "TPT_UPLOAD" / "IMAGES" / pack_code
                    cap_csv = images_dir_local / f"{pack_code}_captions.csv"
                    prev_pdf = images_dir_local / f"{pack_code}_preview.pdf"
                    dlc1, dlc2, dlc3 = st.columns([1,1,1])
                    with dlc1:
                        if cap_csv.exists():
                            st.download_button("Download captions CSV", data=cap_csv.read_bytes(), file_name=cap_csv.name, mime="text/csv", key=f"dl_caps_{slug}")
                    with dlc2:
                        if prev_pdf.exists():
                            st.download_button("Download preview PDF", data=prev_pdf.read_bytes(), file_name=prev_pdf.name, mime="application/pdf", key=f"dl_prev_{slug}")
                    with dlc3:
                        if st.button("Open Images Folder", key=f"open_imgs_{slug}"):
                            try:
                                if images_dir_local.exists():
                                    open_folder(images_dir_local)
                            except Exception:
                                pass
                except Exception:
                    pass
            else:
                st.info("No images created - ensure at least one product is built and covers are available.")
        except Exception as e:
            st.error(f"Listing image generation failed: {e}")

    # Pinterest CSV (uses listing + images dir if present)
    imgs_dir = out_dir / "TPT_UPLOAD" / "IMAGES" / pack_code
    if imgs_dir.exists():
        st.info("Pinterest and Tailwind campaigns are prepared in Step 8: Promote, after the exact published TPT product URL is available.")

    # Freebie Generator
    st.markdown("#### Freebie")
    built_names_for_freebie = [n for n, inf in built_info.items() if inf.get("built")]
    if built_names_for_freebie:
        sel_freebie = st.selectbox("Product for Freebie (uses sample pages)", options=built_names_for_freebie, key=f"freebie_sel_{slug}")
        if st.button("Generate Freebie ZIP", key=f"gen_freebie_{slug}"):
            try:
                ok, msg, zip_path = generate_freebie_zip(slug, sel_freebie, out_dir, pack_code)
                if ok and zip_path and zip_path.exists():
                    st.success(msg)
                    try:
                        st.download_button("Download Freebie ZIP", data=zip_path.read_bytes(), file_name=zip_path.name, key=f"dl_freebie_{slug}")
                    except Exception:
                        pass
                else:
                    st.error(msg or "Freebie generation failed.")
            except Exception as e:
                st.error(f"Freebie failed: {e}")
    else:
        st.info("Build at least one product to enable Freebie generation.")

    # Enable merge only when all cover checkboxes are done
    if st.button("Merge PDFs with Covers", type="primary", key=f"merge_{slug}", disabled=not all_done, help=(None if all_done else "Mark all cover items done first.")):
        book_dir = find_book_dir(slug)
        if not book_dir:
            show_toast("error", "Book folder not found")
            return
        final_dir = book_dir / "FINAL"
        try:
            final_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        # Build ordered list of available cover PDFs
        cover_order = [
            f"{pack_code}_cover.pdf",
            f"{pack_code}_whats_included.pdf",
            f"{pack_code}_closer_look.pdf",
            f"{pack_code}_how_to_use.pdf",
        ]
        cover_files = [covers_root / fn for fn in cover_order if (covers_root / fn).exists()]
        script = project_root() / "production" / "generators" / "generators" / "PDF_MERGER.py"
        merged = 0
        copied = 0
        errs: list[str] = []
        tmp_files: list[Path] = []
        # If multiple cover PDFs exist, chain-merge them into a single multi-page cover
        combined_cover: Path | None = None
        if cover_files:
            if len(cover_files) == 1:
                combined_cover = cover_files[0]
            else:
                prev = cover_files[0]
                for i, nxt in enumerate(cover_files[1:], start=1):
                    tmp = final_dir / f"_{pack_code}_covtmp_{i}.pdf"
                    try:
                        res = subprocess.run(
                            [sys.executable, str(script), str(prev), str(nxt), str(tmp)],
                            capture_output=True,
                            text=True,
                            encoding="utf-8",
                            errors="replace",
                        )
                        if tmp.exists():
                            tmp_files.append(tmp)
                            prev = tmp
                        else:
                            errs.append(f"Failed to combine covers step {i}: {nxt.name}\n{res.stderr.strip() if res.stderr else ''}")
                    except Exception as e:
                        errs.append(f"Error combining covers step {i}: {e}")
                combined_cover = prev if prev.exists() else None
        for name, info in built_info.items():
            if not info.get("built"):
                continue
            files = _product_output_files(out_dir, name)
            content = files.get("color") or files.get("bw")
            if not content or not content.exists():
                continue
            out_path = final_dir / f"{content.stem}_WITH_COVER.pdf"
            if combined_cover and combined_cover.exists():
                try:
                    res = subprocess.run(
                        [sys.executable, str(script), str(combined_cover), str(content), str(out_path)],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    if out_path.exists():
                        merged += 1
                    else:
                        errs.append(f"Failed merge: {content.name}\n{res.stderr.strip() if res.stderr else ''}")
                except Exception as e:
                    errs.append(f"Error merge: {content.name} - {e}")
            else:
                try:
                    shutil.copy2(str(content), str(out_path))
                    if out_path.exists():
                        copied += 1
                except Exception as e:
                    errs.append(f"Error copy: {content.name} - {e}")
        # Cleanup temporary combined cover steps
        for t in tmp_files:
            try:
                t.unlink(missing_ok=True)
            except Exception:
                pass
        summary = f"Merged {merged} product PDFs" + (f", copied {copied} without cover" if copied else "")
        if missing:
            try:
                miss_list = ", ".join([os.path.relpath(m, start=str(project_root())).replace('\\\\','/') if project_root().exists() else m for m in missing])
            except Exception:
                miss_list = ", ".join(missing)
            summary += f" - missing covers: {miss_list}"
        if errs:
            st.error("\n".join(errs))
        show_toast("success", summary)
        st.success(summary)


    st.divider()
    st.markdown("#### Finalize and Package")
    st.caption("Run this after reviewing products and marketing pages. It creates the final PDFs, upload ZIPs, and tracker records.")
    if st.button("Finalize & Package for TPT", type="primary", key=f"finalize_package_{slug}", disabled=built_count == 0):
        with st.spinner("Creating final files and upload packages..."):
            final_ok, final_message = finalize_and_package_book(slug)
        st.session_state[f"finalize_result_{slug}"] = {"ok": final_ok, "message": final_message}
    final_result = st.session_state.get(f"finalize_result_{slug}")
    if isinstance(final_result, dict):
        final_message = str(final_result.get("message") or "")
        if final_result.get("ok"):
            st.success(final_message)
        else:
            st.error(final_message or "Finalization failed.")
        if "warnings:" in final_message.lower():
            warning_text = "\n".join(final_message.splitlines()[1:]) or final_message
            st.warning("The package was created with warnings. Resolve these before uploading to TPT.")
            st.download_button("Download warnings", data=warning_text, file_name=f"{pack_code}_finalize_warnings.txt", key=f"finalize_warning_download_{slug}")
        f1, f2, f3 = st.columns(3)
        with f1:
            if st.button("Open FINAL", key=f"finalize_open_final_{slug}"):
                final_folder = out_dir / "FINAL"
                if final_folder.exists():
                    open_folder(final_folder)
        with f2:
            if st.button("Open TPT_UPLOAD", key=f"finalize_open_upload_{slug}"):
                upload_folder = out_dir / "TPT_UPLOAD"
                if upload_folder.exists():
                    open_folder(upload_folder)
        with f3:
            if st.button("Open Tracker", key=f"finalize_open_tracker_{slug}"):
                st.session_state.view = "tracker"
                qp_update(view="tracker")
                safe_rerun()

    # Post-Finalize Resolve Warnings helper
    st.divider()
    with st.expander("Resolve Warnings (post-finalize)", expanded=False):
        # Quick open folders
        oc1, oc2, oc3, oc4 = st.columns(4)
        with oc1:
            if st.button("Open OUTPUT", key=f"fix_open_out_{slug}"):
                try:
                    outp = output_dir_for_book(slug)
                    if outp and outp.exists():
                        open_folder(outp)
                except Exception:
                    pass
        with oc2:
            if st.button("Open FINAL", key=f"fix_open_final_{slug}"):
                try:
                    outp = output_dir_for_book(slug)
                    fi = (outp / "FINAL") if outp else None
                    if fi and fi.exists():
                        open_folder(fi)
                except Exception:
                    pass
        with oc3:
            if st.button("Open TPT_UPLOAD", key=f"fix_open_upload_{slug}"):
                try:
                    outp = output_dir_for_book(slug)
                    up = (outp / "TPT_UPLOAD") if outp else None
                    if up and up.exists():
                        open_folder(up)
                except Exception:
                    pass
        with oc4:
            if st.button("Open Covers", key=f"fix_open_covers_{slug}"):
                try:
                    open_folder(covers_root)
                except Exception:
                    pass

        # Suggest generating listing images if missing
        try:
            images_dir_local = out_dir / "TPT_UPLOAD" / "IMAGES" / pack_code
            have_imgs = images_dir_local.exists() and any(path.suffix.lower() in {".png", ".jpg", ".jpeg"} for path in images_dir_local.iterdir() if path.is_file())
            prev_pdf = images_dir_local / f"{pack_code}_preview.pdf"
            need_imgs = (not have_imgs) or (not prev_pdf.exists())
        except Exception:
            need_imgs = True
        if need_imgs:
            st.warning("Listing images or preview PDF missing.")
            if st.button("Generate 4 TPT Marketing Pages now", key=f"fix_gen_imgs_{slug}"):
                try:
                    title = display_name or decode_slug(slug)
                    imgs = generate_tpt_marketing_pages(slug, pack_code, out_dir, built_info, title)
                    if imgs:
                        show_toast("success", f"Created {len(imgs)} images under TPT_UPLOAD/IMAGES/{pack_code}/")
                        try:
                            images_dir_local = out_dir / "TPT_UPLOAD" / "IMAGES" / pack_code
                            cap_csv = images_dir_local / f"{pack_code}_captions.csv"
                            prev_pdf2 = images_dir_local / f"{pack_code}_preview.pdf"
                            dlc1, dlc2 = st.columns([1,1])
                            with dlc1:
                                if cap_csv.exists():
                                    st.download_button("Download captions CSV", data=cap_csv.read_bytes(), file_name=cap_csv.name, mime="text/csv", key=f"fix_dl_caps_{slug}")
                            with dlc2:
                                if prev_pdf2.exists():
                                    st.download_button("Download preview PDF", data=prev_pdf2.read_bytes(), file_name=prev_pdf2.name, mime="application/pdf", key=f"fix_dl_prev_{slug}")
                        except Exception:
                            pass
                    else:
                        st.info("No images created - ensure at least one product is built and covers are available.")
                except Exception as e:
                    st.error(f"Listing image generation failed: {e}")

        # Offer re-run merge if covers exist and products built
        can_merge = any((covers_root / fn).exists() for fn in [
            f"{pack_code}_cover.pdf",
            f"{pack_code}_whats_included.pdf",
            f"{pack_code}_closer_look.pdf",
            f"{pack_code}_how_to_use.pdf",
        ]) and any(inf.get("built") for inf in built_info.values())
        if can_merge:
            if st.button("Re-run Merge with Covers", key=f"fix_rerun_merge_{slug}"):
                try:
                    final_dir = find_book_dir(slug) / "FINAL"
                    final_dir.mkdir(parents=True, exist_ok=True)
                    script = project_root() / "production" / "generators" / "generators" / "PDF_MERGER.py"
                    # Build ordered list of available cover PDFs
                    cover_order = [
                        f"{pack_code}_cover.pdf",
                        f"{pack_code}_whats_included.pdf",
                        f"{pack_code}_closer_look.pdf",
                        f"{pack_code}_how_to_use.pdf",
                    ]
                    cover_files = [covers_root / fn for fn in cover_order if (covers_root / fn).exists()]
                    tmp_files: list[Path] = []
                    combined_cover: Path | None = None
                    if cover_files:
                        if len(cover_files) == 1:
                            combined_cover = cover_files[0]
                        else:
                            prev = cover_files[0]
                            for i, nxt in enumerate(cover_files[1:], start=1):
                                tmp = final_dir / f"_{pack_code}_covtmp_{i}.pdf"
                                res = subprocess.run(
                                    [sys.executable, str(script), str(prev), str(nxt), str(tmp)],
                                    capture_output=True,
                                    text=True,
                                    encoding="utf-8",
                                    errors="replace",
                                )
                                if tmp.exists():
                                    tmp_files.append(tmp)
                                    prev = tmp
                            combined_cover = prev if prev.exists() else None
                    merged = 0
                    copied = 0
                    errs2: list[str] = []
                    for name, info in built_info.items():
                        if not info.get("built"):
                            continue
                        files = _product_output_files(out_dir, name)
                        content = files.get("color") or files.get("bw")
                        if not content or not content.exists():
                            continue
                        out_path = final_dir / f"{content.stem}_WITH_COVER.pdf"
                        if combined_cover and combined_cover.exists():
                            res = subprocess.run(
                                [sys.executable, str(script), str(combined_cover), str(content), str(out_path)],
                                capture_output=True,
                                text=True,
                                encoding="utf-8",
                                errors="replace",
                            )
                            if out_path.exists():
                                merged += 1
                            else:
                                errs2.append(f"Failed merge: {content.name}\n{res.stderr.strip() if res.stderr else ''}")
                        else:
                            try:
                                shutil.copy2(str(content), str(out_path))
                                if out_path.exists():
                                    copied += 1
                            except Exception as e:
                                errs2.append(f"Error copy: {content.name} - {e}")
                    for t in tmp_files:
                        try:
                            t.unlink(missing_ok=True)
                        except Exception:
                            pass
                    summary2 = f"Merged {merged} product PDFs" + (f", copied {copied} without cover" if copied else "")
                    if errs2:
                        st.error("\n".join(errs2))
                    show_toast("success", summary2)
                    st.success(summary2)
                except Exception as e:
                    st.error(f"Merge failed: {e}")


def listing_state_key(slug: str) -> str:
    return f"sf_listing_{slug}"


def ensure_listing_state_from_book(slug: str):
    k = listing_state_key(slug)
    if k in st.session_state:
        return
    state = read_book_state(slug)
    saved = state.get("listing", {}) if isinstance(state, dict) else {}
    st.session_state[k] = {
        "tpt_title": saved.get("tpt_title", ""),
        "description": saved.get("description", ""),
        "bullets": saved.get("bullets", ["", "", "", "", "", ""]),
        "grade_tags": saved.get("grade_tags", ["Special Education", "Not Grade Specific"]),
        "subject_tags": saved.get("subject_tags", ["Special Education", "Speech Therapy", "Literacy"]),
        "price": float(saved.get("price", 8.00)),
        "seo_tags": saved.get("seo_tags", []),
        "seed_keywords": saved.get("seed_keywords", []),
        "draft_generated": bool(saved.get("draft_generated", False)),
        "saved_at": saved.get("saved_at"),
    }


def compute_built_products_and_pages(slug: str) -> tuple[list[str], int]:
    info = detect_products_in_output(slug)
    names = []
    total_pages = 0
    for spec in PRODUCT_SPECS:
        name = spec["name"]
        if info.get(name, {}).get("built"):
            names.append(name)
            total_pages += int(spec.get("pages", 0))
    return names, total_pages


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1].rstrip() + "..."


def generate_listing_template(book_title: str, built_products: list[str], total_pages: int) -> dict:
    # Title
    title = f"{book_title} Book Companion | SPED | Autism | AAC"
    title = _truncate(title, 80)

    # Description blocks
    if built_products:
        acts = ", ".join(built_products)
        opening = f"Engaging, low-prep book companion for {book_title}. Designed for special education and AAC learners."
        whats_included = f"What's included: {acts} - {total_pages} total pages across differentiated levels."
        who_for = "Perfect for SPED classrooms, speech therapy, autism programs, small groups, and independent tasks."
        how_use = "Print, laminate, and reuse all year. Use during read-alouds, centers, or therapy sessions."
    else:
        opening = f"Engaging, low-prep book companion for {book_title}."
        whats_included = "Includes multiple hands-on activities to build matching, vocabulary, and comprehension."
        who_for = "Ideal for SPED, AAC users, autism classrooms, and speech therapy."
        how_use = "Print, laminate, and use for centers, small groups, or independent practice."

    description = "\n\n".join([opening, whats_included, who_for, how_use])

    # Bullets - map ALL products to concise benefits with dynamic page counts
    pages_by_name = {s["name"]: s["pages"] for s in PRODUCT_SPECS}
    benefit_text = {
        "Matching": "across 4 levels for easy differentiation",
        "Find & Cover": "builds visual scanning and attention",
        "Word Search": "targets letter recognition and vocabulary",
        "AAC Sentence Building": "for core words and sentence building",
        "Sorting Cards": "for classification and category skills",
        "Bingo": "4 differentiated levels with calling cards",
        "Yes/No Questions": "with desk strip for pointing and eye gaze",
        "Sequencing": "for story retell and ordinal understanding",
        "AAC Board": "with high-visibility variants for print accessibility",
        "Book Participation Pieces": "for read-aloud engagement with Velcro pieces",
        "Vocabulary Snap": "with symbol, text, and combined decks plus extra copy cards",
        "Syllable Awareness": "for phonological awareness and segmentation",
        "Adapted Book": "for interactive reading with Velcro pieces",
        "Inferencing Cards": "for clue-based reasoning and discussion",
        "Vocabulary Word Wall": "for classroom display and word study",
        "Story Grammar & Retell": "for story elements and comprehension",
        "Print Detective": "for print concepts and letter knowledge",
        "CVC Decode & Build": "for phonics and word building",
        "IEP Monitoring Form": "for progress tracking and data collection (bonus inclusion)",
    }
    bullets = []
    for name in built_products:
        pages = pages_by_name.get(name)
        benefit = benefit_text.get(name)
        if pages is not None and benefit:
            page_word = "page" if pages == 1 else "pages"
            bullets.append(f"{name} ({pages} {page_word}) {benefit}")
        elif benefit:
            bullets.append(f"{name} {benefit}")
        else:
            bullets.append(f"Includes {name}")
    # Truncate each bullet to 120 chars
    bullets = [_truncate(b, 120) for b in bullets]

    return {"tpt_title": title, "description": description, "bullets": bullets}


def generate_listing_ai(book_title: str, built_products: list[str], total_pages: int, seed_keywords: list[str] | None = None) -> tuple[bool, dict | None, str | None]:
    """Call Anthropic to generate listing JSON. Returns (ok, data, error).
    On success, data is a dict with keys: tpt_title, description, bullets (len 6), grade_tags, subject_tags, price, seo_tags.
    On failure, returns (False, None, error_message) without modifying caller state.
    """
    if anthropic is None:
        return False, None, "Anthropic SDK not available"
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return False, None, "ANTHROPIC_API_KEY not set"
    try:
        client = anthropic.Anthropic(api_key=key)
        system_prompt = (
            "You are a TPT (Teachers Pay Teachers) listing copywriter specialising in special education resources. "
            "You write clear, keyword-rich listings that convert browsers into buyers. Your audience is SPED teachers, SLPs, and autism classroom teachers in the US. "
            "You never use jargon beyond common SPED terms. You write in plain text only — no markdown, no asterisks, no bullet symbols in the description body. "
            "Bullet points are returned as a JSON array only."
        )
        products_str = ", ".join(built_products or [])
        kw = ", ".join([k for k in (seed_keywords or []) if k])
        user_prompt = (
            f"Write a TPT product listing for the following resource.\n\n"
            f"Book title: {book_title}\n"
            f"Product type: Book Companion\n"
            f"Activities included: {products_str}\n"
            f"Total pages: {int(total_pages)}\n"
            + (f"Seed keywords to incorporate: {kw}\n" if kw else "") +
            f"Target audience: Students with autism, AAC users, special education classrooms, speech therapy\n\n"
            "Return your response as valid JSON only, with no preamble, no markdown fences, and no explanation. Use this exact schema:\n"
            "{\n"
            "  \"tpt_title\": \"string (max 80 chars, format: [Book Title] Book Companion | SPED | Autism | AAC)\",\n"
            "  \"description\": \"string (plain text, 3-4 paragraphs, no markdown)\",\n"
            "  \"bullets\": [\"string\", \"string\", \"string\", \"string\", \"string\", \"string\"],\n"
            "  \"grade_tags\": [\"string\", \"string\"],\n"
            "  \"subject_tags\": [\"string\", \"string\"],\n"
            "  \"seo_tags\": [\"string\", \"string\"],\n"
            "  \"price\": number\n"
            "}"
        )
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = (resp.content[0].text if getattr(resp, "content", None) else "").strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        try:
            data = json.loads(raw) if raw else {}
        except Exception as e:
            return False, None, raw or str(e)
        if not isinstance(data, dict):
            return False, None, raw or "Invalid JSON structure"
        # Normalize fields and enforce limits
        title = str(data.get("tpt_title", "")).strip()
        if not title:
            title = f"{book_title} Book Companion | SPED | Autism | AAC"
        if len(title) > 80:
            title = title[:80].rstrip()
        bullets = data.get("bullets") or []
        if not isinstance(bullets, list):
            bullets = []
        bullets = [str(b) for b in bullets][:6]
        norm_bul = []
        for b in bullets:
            bb = b if len(b) <= 120 else (b[:119].rstrip() + "…")
            norm_bul.append(bb)
        while len(norm_bul) < 6:
            norm_bul.append("")
        desc = str(data.get("description", "")).strip()
        grade_tags = data.get("grade_tags") if isinstance(data.get("grade_tags"), list) else []
        subject_tags = data.get("subject_tags") if isinstance(data.get("subject_tags"), list) else []
        seo_tags = data.get("seo_tags") if isinstance(data.get("seo_tags"), list) else []
        try:
            price = float(data.get("price", 8.00))
        except Exception:
            price = 8.00
        return True, {
            "tpt_title": title,
            "description": desc,
            "bullets": norm_bul[:6],
            "grade_tags": [str(x) for x in grade_tags][:8],
            "subject_tags": [str(x) for x in subject_tags][:8],
            "seo_tags": [str(x) for x in seo_tags][:15],
            "price": price,
        }, None
    except Exception as e:
        return False, None, str(e)


def save_listing(slug: str, data: dict):
    state = read_book_state(slug)
    listing = {
        "tpt_title": data.get("tpt_title", ""),
        "description": data.get("description", ""),
        "bullets": data.get("bullets", ["", "", "", "", "", ""]),
        "grade_tags": data.get("grade_tags", []),
        "subject_tags": data.get("subject_tags", []),
        "seo_tags": data.get("seo_tags", []),
        "price": float(data.get("price", 8.00)),
        "seed_keywords": data.get("seed_keywords", []),
        "draft_generated": bool(data.get("draft_generated", False)),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
    }
    state["listing"] = listing
    write_book_state(slug, state)
    clear_stage_caches(slug)

    # Write listing.md
    d = find_book_dir(slug)
    if d:
        cfg = d / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        md = cfg / "listing.md"
        bullets_md = "\n".join([f"- {b}" for b in listing.get("bullets", [])])
        md.write_text(
            f"# {listing['tpt_title']}\n\n## Description\n{listing['description']}\n\n## Bullet Points\n{bullets_md}\n\n## Tags\nGrades: {', '.join(listing['grade_tags'])}\nSubjects: {', '.join(listing['subject_tags'])}\nSEO Tags: {', '.join(listing.get('seo_tags', []))}\nPrice: ${listing['price']:.2f}\n\nSaved: {listing['saved_at']}\n",
            encoding="utf-8",
        )


def render_listing_tab(slug: str, display_name: str):
    stage_header("listing", display_name)
    ensure_listing_state_from_book(slug)
    k = listing_state_key(slug)
    lst = st.session_state[k]

    # Advisory gate if nothing built yet
    built_names, total_pages = compute_built_products_and_pages(slug)
    if not built_names:
        st.info("Build at least one product first so your listing accurately reflects what's included.")

    # Last saved line
    if lst.get("saved_at"):
        try:
            dt = datetime.fromisoformat(lst["saved_at"]).strftime("%d/%m/%Y %H:%M")
        except Exception:
            dt = lst["saved_at"]
        st.caption(f"Last saved {dt}")

    # Form
    st.subheader("Listing details")
    title = st.text_input("TPT Title (max 80)", value=lst["tpt_title"], key=f"tpt_title_{slug}")
    st.caption(f"{len(title)} / 80")

    desc = st.text_area("Description", value=lst["description"], key=f"desc_{slug}", height=200)
    st.caption(f"{len(desc)} characters")

    st.markdown("#### What's included (6 bullets)")
    bullets = []
    cols = st.columns(2)
    for i in range(6):
        with cols[i % 2]:
            b = st.text_input(f"Bullet {i+1}", value=lst["bullets"][i] if i < len(lst["bullets"]) else "", key=f"b_{i}_{slug}")
            st.caption(f"{len(b)} / 120")
            bullets.append(b)

    grade_opts = ["PreK", "Kindergarten", "1st Grade", "2nd Grade", "3rd Grade", "Special Education", "Not Grade Specific"]
    subj_opts = ["Special Education", "Speech Therapy", "Life Skills", "Reading", "Literacy", "ELA"]
    grades = st.multiselect("Grade / Level Tags", options=grade_opts, default=[value for value in lst.get("grade_tags", []) if value in grade_opts], key=f"listing_grades_{slug}")
    subjects = st.multiselect("Subject Tags", options=subj_opts, default=[value for value in lst.get("subject_tags", []) if value in subj_opts], key=f"listing_subjects_{slug}")
    price = st.number_input("Price (informational)", min_value=0.0, step=0.25, value=float(lst["price"]))
    seed_kw_raw = st.text_input("Seed keywords (comma-separated)", value=", ".join(lst.get("seed_keywords", [])), key=f"seed_kw_{slug}")
    seed_list = [t.strip() for t in str(seed_kw_raw or "").split(",") if t.strip()]
    seo_raw = st.text_input("SEO tags (comma-separated)", value=", ".join(lst.get("seo_tags", [])), key=f"seo_tags_{slug}")
    seo_list = [t.strip() for t in str(seo_raw or "").split(",") if t.strip()]

    # Actions row
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        gen_label = "Regenerate draft" if lst.get("draft_generated") else "Generate listing draft"
        regen_key = f"sf_regen_{slug}"
        api_ready = (anthropic is not None) and bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
        tooltip = "Add ANTHROPIC_API_KEY to your .env file to enable AI drafting."
        if not api_ready:
            st.button(gen_label, disabled=True, help=tooltip)
        elif st.session_state.get(regen_key):
            st.warning("This will replace your current draft. Continue?")
            cc1, cc2 = st.columns([1, 1])
            with cc1:
                if st.button("Confirm replace", key=f"confirm_regen_{slug}"):
                    book_title = decode_slug(slug)
                    with st.spinner("Drafting your listing..."):
                        ok, data, err = generate_listing_ai(book_title, built_names, total_pages, seed_keywords=seed_list)
                    if ok and data:
                        st.session_state[k].update({
                            "tpt_title": data["tpt_title"],
                            "description": data["description"],
                            "bullets": data["bullets"],
                            "seed_keywords": seed_list,
                            "draft_generated": True,
                        })
                        ai_grades = [g for g in (data.get("grade_tags") or []) if g in grade_opts]
                        ai_subjects = [s for s in (data.get("subject_tags") or []) if s in subj_opts]
                        ai_seo = [str(x) for x in (data.get("seo_tags") or [])]
                        st.session_state[k].update({
                            "grade_tags": ai_grades,
                            "subject_tags": ai_subjects,
                            "seo_tags": ai_seo,
                            "price": float(data.get("price", lst.get("price", 8.00))),
                            "grade_tags_missing": not bool(ai_grades),
                            "subject_tags_missing": not bool(ai_subjects),
                        })
                        st.session_state[regen_key] = False
                        show_toast("success", "Listing draft replaced.")
                        safe_rerun()
                    else:
                        show_toast("error", "Draft failed - check your API key or try again.")
                        if err:
                            try:
                                print(err)
                            except Exception:
                                pass
                        st.session_state[regen_key] = False
                        safe_rerun()
            with cc2:
                if st.button("Cancel", key=f"cancel_regen_{slug}"):
                    st.session_state[regen_key] = False
                    safe_rerun()
        else:
            if st.button(gen_label):
                if lst.get("draft_generated"):
                    st.session_state[regen_key] = True
                    safe_rerun()
                else:
                    book_title = decode_slug(slug)
                    with st.spinner("Drafting your listing..."):
                        ok, data, err = generate_listing_ai(book_title, built_names, total_pages, seed_keywords=seed_list)
                    if ok and data:
                        st.session_state[k].update({
                            "tpt_title": data["tpt_title"],
                            "description": data["description"],
                            "bullets": data["bullets"],
                            "seed_keywords": seed_list,
                            "draft_generated": True,
                        })
                        ai_grades = [g for g in (data.get("grade_tags") or []) if g in grade_opts]
                        ai_subjects = [s for s in (data.get("subject_tags") or []) if s in subj_opts]
                        ai_seo = [str(x) for x in (data.get("seo_tags") or [])]
                        st.session_state[k].update({
                            "grade_tags": ai_grades,
                            "subject_tags": ai_subjects,
                            "seo_tags": ai_seo,
                            "price": float(data.get("price", lst.get("price", 8.00))),
                            "grade_tags_missing": not bool(ai_grades),
                            "subject_tags_missing": not bool(ai_subjects),
                        })
                        show_toast("success", "Listing draft ready - review and edit before saving.")
                        safe_rerun()
                    else:
                        show_toast("error", "Draft failed - check your API key or try again.")
                        if err:
                            try:
                                print(err)
                            except Exception:
                                pass
    with c2:
        if st.button("Save listing"):
            # Gather latest values from inputs
            data = {
                "tpt_title": title,
                "description": desc,
                "bullets": bullets,
                "grade_tags": grades,
                "subject_tags": subjects,
                "price": price,
                "seo_tags": seo_list,
                "seed_keywords": seed_list,
                "draft_generated": lst.get("draft_generated", False),
            }
            # Validation
            if not data["tpt_title"]:
                st.error("Title is required.")
            elif not data["description"]:
                st.error("Description is required.")
            elif len(data["tpt_title"]) > 80:
                st.error("Title must be 80 characters or fewer.")
            elif any(len(b) > 120 for b in data["bullets"]):
                st.error("Each bullet must be 120 characters or fewer.")
            else:
                save_listing(slug, data)
                # refresh local state from file
                st.session_state.pop(k, None)
                ensure_listing_state_from_book(slug)
                show_toast("success", "Listing saved")
                safe_rerun()
    with c3:
        if st.button("Copy all to clipboard"):
            # Build plain-text block
            bullets_txt = "\n".join([f"- {b}" for b in bullets])
            clip = f"{title}\n\n{desc}\n\n{bullets_txt}"
            # Use a tiny HTML component to access the browser clipboard
            components.html(f"""
                <script>
                const txt = {json.dumps(clip)};
                navigator.clipboard.writeText(txt);
                </script>
            """, height=0)
            show_toast("success", "Copied to clipboard.")
        if st.button("Copy Title", key=f"copy_title_{slug}"):
            components.html(f"""
                <script>
                navigator.clipboard.writeText({json.dumps(title)});
                </script>
            """, height=0)
            show_toast("success", "Title copied.")
        if st.button("Copy Bullets", key=f"copy_bul_{slug}"):
            bullets_txt = "\n".join([f"- {b}" for b in bullets])
            components.html(f"""
                <script>
                navigator.clipboard.writeText({json.dumps(bullets_txt)});
                </script>
            """, height=0)
            show_toast("success", "Bullets copied.")
        if st.button("Copy SEO Tags", key=f"copy_seo_{slug}"):
            seo_txt = ", ".join(seo_list)
            components.html(f"""
                <script>
                navigator.clipboard.writeText({json.dumps(seo_txt)});
                </script>
            """, height=0)
            show_toast("success", "SEO tags copied.")
        if st.button("Copy Tags (Grades + Subjects)", key=f"copy_tags_{slug}"):
            tags_txt = "Grades: " + ", ".join(grades) + "\n" + "Subjects: " + ", ".join(subjects)
            components.html(f"""
                <script>
                navigator.clipboard.writeText({json.dumps(tags_txt)});
                </script>
            """, height=0)
            show_toast("success", "Tags copied.")
        if st.button("Copy TPT Paste Block", key=f"copy_tpt_block_{slug}"):
            bullets_txt = "\n".join([f"- {b}" for b in bullets])
            block = (
                f"{title}\n\n" +
                f"{desc}\n\n" +
                f"{bullets_txt}\n\n" +
                f"Grades: {', '.join(grades)}\n" +
                f"Subjects: {', '.join(subjects)}\n" +
                f"SEO Tags: {', '.join(seo_list)}\n" +
                f"Price: ${price:.2f}"
            )
            components.html(f"""
                <script>
                navigator.clipboard.writeText({json.dumps(block)});
                </script>
            """, height=0)
            show_toast("success", "TPT paste block copied.")


def render_aac_board_tab(slug: str, display_name: str):
    book_dir = find_book_dir(slug)
    if not book_dir:
        st.info("No book folder found. Set your Themes root in Settings.")
        return
    cfg = book_dir / "config" / "aac_board.json"
    if not cfg.exists():
        st.info("No AAC board config found for this book. Run aac_migrate_configs.py to generate configs for existing boards, or use the AAC generator to create a board first.")
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Create default 6x6 board", key=f"aac_create_{slug}"):
                try:
                    data = {
                        "grid_size": "6x6",
                        "cells": []
                    }
                    row0 = ["I", "you", "what", "more", "yes", "no"]
                    for i, lbl in enumerate(row0):
                        data["cells"].append({"row": 0, "col": i, "label": lbl, "symbol_filename": None, "locked": True, "core": True})
                    row1 = ["want", "see", "look", "help", "like", "don't like"]
                    for i, lbl in enumerate(row1):
                        data["cells"].append({"row": 1, "col": i, "label": lbl, "symbol_filename": None, "locked": True, "core": True})
                    row2 = ["uh oh", "finished", "all done", "don't know", "same", "different"]
                    for i, lbl in enumerate(row2):
                        data["cells"].append({"row": 2, "col": i, "label": lbl, "symbol_filename": None, "locked": True, "core": True})
                    for i in range(6):
                        data["cells"].append({"row": 3, "col": i, "label": "", "symbol_filename": None, "locked": False, "core": False})
                    row4 = ["", "", "", "colour", "choose", "read"]
                    for i, lbl in enumerate(row4):
                        data["cells"].append({"row": 4, "col": i, "label": lbl, "symbol_filename": None, "locked": bool(lbl), "core": False})
                    row5 = ["red", "blue", "green", "yellow", "orange", "purple"]
                    for i, lbl in enumerate(row5):
                        data["cells"].append({"row": 5, "col": i, "label": lbl, "symbol_filename": None, "locked": True, "core": True})
                    cfg.parent.mkdir(parents=True, exist_ok=True)
                    cfg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    show_toast("success", "Created aac_board.json with BoardReady defaults.")
                except Exception as e:
                    st.error(f"Failed to create default board: {e}")
                safe_rerun()
        with c2:
            st.button("Cancel", key=f"aac_create_cancel_{slug}")
        return
    # Load config and render a static grid (no interactions yet)
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except Exception as e:
        st.error(f"Invalid aac_board.json: {e}")
        return
    st.subheader("AAC Board")
    st.caption(f"Config: {cfg}")
    grid_sz = str(data.get("grid_size", "6x6"))
    try:
        rows, cols = [int(x) for x in grid_sz.lower().split("x")[:2]]
    except Exception:
        rows, cols = 6, 6
    cells = data.get("cells") or []
    by_rc: dict[tuple[int, int], dict] = {}
    for c in cells:
        try:
            by_rc[(int(c.get("row", 0)), int(c.get("col", 0)))] = c
        except Exception:
            continue

    # Legend
    lg1, lg2 = st.columns([1, 3])
    with lg2:
        st.caption("Teal = core/locked row; White = book-specific row")

    for r in range(rows):
        cols_ui = st.columns(cols)
        for cc in range(cols):
            cell = by_rc.get((r, cc), {})
            label = str(cell.get("label", "")).strip()
            is_yes = label.lower() == "yes"
            is_no = label.lower() == "no"
            if is_yes:
                bg = "var(--aac-yes)"
            elif is_no:
                bg = "var(--aac-no)"
            elif r == 0:
                bg = "var(--row-tint-core)"
            elif r in {3, 4}:
                bg = "var(--row-tint-book)"
            else:
                bg = "#FFFFFF"
            bd = "var(--brd-color)"
            lbl_col = "#FFFFFF" if (is_yes or is_no) else "#1A1A1A"
            html = f"""
<div style="height: 88px; border: 1.25px solid {bd}; background: {bg}; border-radius: var(--brd-radius); display:flex; align-items:center; justify-content:center; padding:4px;">
  <div style="font-size:12px; text-align:center; color:{lbl_col}; line-height:1.15; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; font-family: Arial, Helvetica, sans-serif; font-weight: 700;">
    {label or '&nbsp;'}
  </div>
</div>
"""
            with cols_ui[cc]:
                st.markdown(html, unsafe_allow_html=True)
                if st.button("Edit", key=f"aac_edit_{slug}_{r}_{cc}"):
                    st.session_state[f"aac_sel_{slug}"] = (r, cc)
                    safe_rerun()

    sel_key = f"aac_sel_{slug}"
    sel = st.session_state.get(sel_key)
    if sel is not None:
        r, cc = sel
        cell = by_rc.get((r, cc), {"row": r, "col": cc})
        is_locked = bool(cell.get("locked", False)) or bool(cell.get("core", False)) or (r in {0, 1, 5})
        st.subheader(f"Edit cell r{r+1}, c{cc+1}")
        if is_locked:
            st.info("This is a core/locked cell and cannot be edited in this phase.")
            if st.button("Close", key=f"aac_close_{slug}"):
                st.session_state.pop(sel_key, None)
                safe_rerun()
            return
        label_key = f"aac_lbl_{slug}_{r}_{cc}"
        symbol_key = f"aac_sym_{slug}_{r}_{cc}"
        new_label = st.text_input("Label", value=str(cell.get("label", "")), key=label_key)
        sym_root = symbols_root()
        sym_query = st.text_input("Search symbols", value="", key=f"aac_q_{slug}_{r}_{cc}")
        sym_files: list[str] = []
        if sym_root.exists():
            try:
                for p in sym_root.glob("**/*.png"):
                    nm = p.relative_to(sym_root).as_posix()
                    if (not sym_query) or (sym_query.lower() in nm.lower()):
                        sym_files.append(nm)
                        if len(sym_files) >= 200:
                            break
            except Exception:
                pass
        curr_sym = str(cell.get("symbol_filename") or "")
        opts = ["(none)"] + sym_files
        idx = 0
        if curr_sym and curr_sym in sym_files:
            idx = opts.index(curr_sym) if curr_sym in opts else 0
        sym_choice = st.selectbox("Symbol filename", options=opts, index=idx, key=symbol_key)
        pv1, pv2 = st.columns([1, 3])
        with pv1:
            if sym_choice != "(none)":
                pv = sym_root / sym_choice
                try:
                    if pv.exists():
                        st.image(str(pv), width=72)
                except Exception:
                    pass
        b1, b2, _ = st.columns([1, 1, 2])
        with b1:
            if st.button("Clear", key=f"aac_clear_{slug}_{r}_{cc}"):
                for idx2, ccx in enumerate(cells):
                    if int(ccx.get("row", -1)) == r and int(ccx.get("col", -1)) == cc:
                        cells[idx2]["label"] = ""
                        cells[idx2]["symbol_filename"] = None
                        break
                data["cells"] = cells
                try:
                    cfg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    show_toast("success", "AAC cell cleared.")
                except Exception as e:
                    st.error(f"Failed to save: {e}")
                st.session_state.pop(sel_key, None)
                safe_rerun()
        with b2:
            if st.button("Save", key=f"aac_save_{slug}_{r}_{cc}"):
                updated = False
                for idx2, ccx in enumerate(cells):
                    if int(ccx.get("row", -1)) == r and int(ccx.get("col", -1)) == cc:
                        cells[idx2]["label"] = new_label
                        cells[idx2]["symbol_filename"] = None if sym_choice == "(none)" else sym_choice
                        updated = True
                        break
                if not updated:
                    cells.append({
                        "row": r,
                        "col": cc,
                        "label": new_label,
                        "symbol_filename": None if sym_choice == "(none)" else sym_choice,
                        "locked": False,
                        "core": False,
                    })
                data["cells"] = cells
                try:
                    cfg.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    show_toast("success", "AAC cell saved.")
                except Exception as e:
                    st.error(f"Failed to save: {e}")
                st.session_state.pop(sel_key, None)
                safe_rerun()

    # Export AAC Board preview PNG (grid render)
    ex1, _ = st.columns([1, 3])
    with ex1:
        if st.button("Export preview PNG", key=f"aac_export_{slug}"):
            try:
                rows2, cols2 = rows, cols
                cell_size = 160
                gap = 8
                margin = 16
                label_h = 26  # reserved space for label at bottom of each cell
                footer_h = 28 # PCS footer area height
                w = cols2 * cell_size + (cols2 - 1) * gap + margin * 2
                h = rows2 * cell_size + (rows2 - 1) * gap + margin * 2 + footer_h
                img = Image.new("RGB", (w, h), (255, 255, 255))
                dr = ImageDraw.Draw(img)
                symroot = symbols_root()
                for rr in range(rows2):
                    for cc2 in range(cols2):
                        x = margin + cc2 * (cell_size + gap)
                        y = margin + rr * (cell_size + gap)
                        lbl_key = str(by_rc.get((rr, cc2), {}).get("label") or "").strip().lower()
                        if rr == 0:
                            bg = (235, 245, 255)
                        elif rr in {3, 4}:
                            bg = (255, 253, 231)
                        else:
                            bg = (255, 255, 255)
                        if lbl_key == "yes":
                            bg = (76, 175, 80)
                        if lbl_key == "no":
                            bg = (244, 67, 54)
                        bd = (204, 204, 204)
                        dr.rectangle([x, y, x + cell_size, y + cell_size], fill=bg, outline=bd, width=2)
                        cell = by_rc.get((rr, cc2), {})
                        lbl = str(cell.get("label") or "").strip()
                        sym = cell.get("symbol_filename")
                        # Draw symbol in the area above the label zone
                        if sym:
                            p = symroot / str(sym)
                            try:
                                if p.exists():
                                    im2 = Image.open(str(p)).convert("RGBA")
                                    maxw = cell_size - 24
                                    maxh = max(1, cell_size - 24 - label_h)
                                    try:
                                        im2.thumbnail((maxw, maxh), Image.LANCZOS)
                                    except Exception:
                                        im2.thumbnail((maxw, maxh))
                                    ox = x + (cell_size - im2.width) // 2
                                    oy = y + 12 + max(0, (maxh - im2.height) // 2)
                                    img.paste(im2, (ox, oy), im2)
                            except Exception:
                                pass
                        # Draw label in reserved bottom area (always, if present)
                        if lbl:
                            try:
                                fnt = None
                                try:
                                    fnt = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 14)
                                except Exception:
                                    fnt = ImageFont.load_default()
                                bbox = dr.textbbox((0, 0), lbl, font=fnt)
                                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                                tx = x + (cell_size - tw) // 2
                                ty = y + cell_size - label_h + (label_h - th) // 2
                                col = (255, 255, 255) if lbl_key in {"yes", "no"} else (26, 26, 26)
                                dr.text((tx, ty), lbl, fill=col, font=fnt, align="center")
                            except Exception:
                                pass
                # Footer — PCS license notice
                try:
                    foot_txt = "PCS symbols (C) Tobii Dynavox. Used under license."
                    try:
                        foot_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 12)
                    except Exception:
                        foot_font = ImageFont.load_default()
                    bbox = dr.textbbox((0, 0), foot_txt, font=foot_font)
                    ftw, fth = bbox[2] - bbox[0], bbox[3] - bbox[1]
                    fx = (w - ftw) // 2
                    fy = h - footer_h + (footer_h - fth) // 2
                    dr.text((fx, fy), foot_txt, fill=(120, 120, 120), font=foot_font)
                except Exception:
                    pass
                bd2 = find_book_dir(slug)
                if bd2:
                    outp = bd2 / "config" / "aac_board_preview.png"
                    outp.parent.mkdir(parents=True, exist_ok=True)
                    img.save(str(outp), format="PNG")
                    try:
                        img.convert("L").convert("RGB").save(str(bd2 / "config" / "aac_board_preview_bw.png"), format="PNG")
                    except Exception:
                        pass
                    st.image(str(outp), caption="AAC Board preview", width=480)
                    show_toast("success", "Preview exported.")
            except Exception as e:
                st.error(f"Export failed: {e}")

def qp_update(**kwargs):
    try:
        if hasattr(st, "query_params"):
            for k, v in kwargs.items():
                if v is None:
                    if k in st.query_params:
                        del st.query_params[k]
                else:
                    st.query_params[k] = v
        else:
            curr = st.experimental_get_query_params()
            flat = {k: (v[0] if isinstance(v, list) else v) for k, v in curr.items()}
            for k, v in kwargs.items():
                if v is None:
                    flat.pop(k, None)
                else:
                    flat[k] = v
            st.experimental_set_query_params(**flat)
    except Exception:
        pass


def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


def _prefs_file_path() -> Path:
    return project_root() / ".sw_app_prefs.json"


def load_global_prefs() -> dict:
    try:
        p = _prefs_file_path()
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"ui": {"readable_width": False, "large_text": False, "high_contrast": False, "show_tips": True, "home_planning": False}, "last_tool": "settings", "last_book": None, "recent_books": []}


def save_global_prefs(prefs: dict):
    try:
        _prefs_file_path().write_text(json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def ensure_global_prefs():
    if "sf_ui_prefs" not in st.session_state:
        data = load_global_prefs()
        ui = data.get("ui", {}) if isinstance(data, dict) else {}
        st.session_state.sf_ui_prefs = {
            "readable_width": bool(ui.get("readable_width", False)),
            "large_text": bool(ui.get("large_text", False)),
            "high_contrast": bool(ui.get("high_contrast", False)),
            "show_tips": bool(ui.get("show_tips", True)),
            "home_planning": bool(ui.get("home_planning", False)),
        }
    if "sf_last_tool" not in st.session_state:
        data = load_global_prefs()
        st.session_state.sf_last_tool = data.get("last_tool", "settings")
    if "sf_last_book" not in st.session_state:
        data = load_global_prefs()
        st.session_state.sf_last_book = data.get("last_book")
    if "sf_recent_books" not in st.session_state:
        data = load_global_prefs()
        st.session_state.sf_recent_books = list(data.get("recent_books") or [])[:5]


def persist_session_prefs():
    data = load_global_prefs()
    ui = st.session_state.get("sf_ui_prefs", data.get("ui", {}))
    data["ui"] = ui
    data["last_tool"] = st.session_state.get("sf_last_tool", data.get("last_tool", "settings"))
    data["last_book"] = st.session_state.get("sf_last_book", data.get("last_book"))
    data["recent_books"] = list(st.session_state.get("sf_recent_books", data.get("recent_books", [])))[:5]
    save_global_prefs(data)


# â”€â”€ Phase 2 helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def themes_root_candidates() -> list[Path]:
    """Candidate roots where per-book folders may exist."""
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


_icon_count_cache: dict[str, int] = {}


def count_icons_for_book(slug: str) -> int:
    if slug in _icon_count_cache:
        return _icon_count_cache[slug]
    """Approximate icon count from the canonical activity_images folder if present.
    Falls back to counting images under the book folder with 'activity' in parent name.
    """
    book_dir = find_book_dir(slug)
    if not book_dir:
        _icon_count_cache[slug] = 0
        return 0
    # Primary location
    ai = book_dir / "activity_images"
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    if ai.exists():
        result = sum(1 for p in ai.iterdir() if p.is_file() and p.suffix.lower() in exts)
        _icon_count_cache[slug] = result
        return result
    # Fallbacks
    count = 0
    for sub in book_dir.rglob("*"):
        try:
            if sub.is_file() and sub.suffix.lower() in exts and "activity" in sub.parent.name.lower():
                count += 1
        except Exception:
            continue
    _icon_count_cache[slug] = count
    return count


def _any_file_matches(base: Path, substrings: list[str], exts: set[str] | None = None) -> bool:
    if not base or not base.exists():
        return False
    subs = [s.lower() for s in substrings]
    for p in base.rglob("*"):
        try:
            if not p.is_file():
                continue
            if exts and p.suffix.lower() not in exts:
                continue
            name = p.name.lower()
            if all(s in name for s in subs):
                return True
        except Exception:
            continue
    return False


def detect_built_products(slug: str) -> dict:
    # Phase 5 tokens â€” scan the active book's OUTPUT folder only
    info = detect_products_in_output(slug)
    return {k: v["built"] for k, v in info.items()}


_qa_status_cache: dict[str, tuple[str, bool]] = {}


def read_qa_status(slug: str) -> tuple[str, bool]:
    if slug in _qa_status_cache:
        return _qa_status_cache[slug]
    # Prefer book_state.json written on QA pass (Phase 5)
    st_data = read_book_state(slug)
    try:
        if st_data.get("qa", {}).get("status") == "passed":
            _qa_status_cache[slug] = ("Passed", True)
            return ("Passed", True)
    except Exception:
        pass
    # Fallback to historical QA log files
    candidates = [
        project_root() / "BoardReady" / "boardready" / "data" / "qa_review_log.json",
        project_root() / "boardready" / "data" / "qa_review_log.json",
        project_root() / "boardready" / "qa_review_log.json",
        project_root() / "qa_review_log.json",
    ]
    for p in candidates:
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                info = data.get(slug)
                if info and isinstance(info, dict):
                    reviewed = bool(info.get("reviewed"))
                    result = ("Passed" if reviewed else "Partial"), reviewed
                    _qa_status_cache[slug] = result
                    return result
        except Exception:
            continue
    _qa_status_cache[slug] = ("Not run", False)
    return ("Not run", False)


_listing_status_cache: dict[str, str] = {}


def read_listing_status(slug: str) -> str:
    if slug in _listing_status_cache:
        return _listing_status_cache[slug]
    # Phase 6: read from book_state.json listing.saved_at
    try:
        state = read_book_state(slug)
        listing = state.get("listing", {})
        if listing.get("saved_at"):
            _listing_status_cache[slug] = "Saved"
            return "Saved"
    except Exception:
        pass
    _listing_status_cache[slug] = "Not started"
    return "Not started"


def read_zip_status(slug: str) -> str:
    roots = [project_root() / "tpt_upload_ready", project_root() / "production" / "final_products" / slug]
    for r in roots:
        if not r.exists():
            continue
        zips = [p for p in r.rglob("*.zip") if slug in p.name]
        if zips:
            latest = max(zips, key=lambda p: p.stat().st_mtime)
            dt = datetime.fromtimestamp(latest.stat().st_mtime).strftime("%d %b %Y")
            return f"Created - {dt}"
    return "Not created"


def compute_next_action(icon_count: int, qa_passed: bool, any_built: bool, listing_saved: bool) -> tuple[str, bool, str]:
    """Return (label, enabled, target_tab)."""
    if icon_count == 0:
        return ("Add icons to get started ->", True, "icons")
    if 1 <= icon_count <= 5 and not qa_passed:
        return (f"Add more icons - {icon_count} added, need {max(0, 6 - icon_count)} more ->", True, "icons")
    if icon_count >= 6 and not qa_passed:
        return ("Run QA to check your icon matches ->", True, "qa")
    if qa_passed and not any_built:
        return ("Build this kit ->", True, "build")
    if any_built and not listing_saved:
        return ("Write the TPT Listing ->", True, "listing")
    return ("Mark as done and pick next book ->", True, "today")


def season_au(dt: datetime) -> str:
    m = dt.month
    if m in (12, 1, 2):
        return "Summer"
    if m in (3, 4, 5):
        return "Autumn"
    if m in (6, 7, 8):
        return "Winter"
    return "Spring"


def season_us(dt: datetime) -> str:
    m = dt.month
    if m in (12, 1, 2):
        return "Winter"
    if m in (3, 4, 5):
        return "Spring"
    if m in (6, 7, 8):
        return "Summer"
    return "Autumn"


def season_recommendations(display_map: dict, season: str, limit: int = 3) -> list[str]:
    keys = list(display_map.keys())
    labels = {k: display_map[k] for k in keys}
    # Simple keyword picks
    kw = {
        "Spring": ["spring", "garden", "flower"],
        "Summer": ["ocean", "pond", "sun", "beach"],
        "Autumn": ["seed", "harvest", "leaf", "rainbow"],
        "Winter": ["snow", "cold", "bear"],
    }.get(season, [])
    picks = [k for k in keys if any(w in labels[k].lower() for w in kw)]
    if not picks:
        picks = keys[:]
    return [labels[k] for k in picks[:limit]]


def read_build_priorities(root: Path) -> dict:
    p = root / "assets" / "config" / "build_priorities.json"
    if not p.exists():
        return {"P1": [], "P2": []}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        p1 = [s for s in d.get("P1", []) if isinstance(s, str)]
        p2 = [s for s in d.get("P2", []) if isinstance(s, str)]
        return {"P1": p1, "P2": p2}
    except Exception:
        return {"P1": [], "P2": []}


def render_priorities_panel(display_map: dict):
    root = project_root()
    data = read_build_priorities(root)
    p1 = data.get("P1") or []
    p2 = data.get("P2") or []
    if not p1 and not p2:
        return

    def detect_priority_status(slug: str) -> str:
        try:
            icons = count_icons_for_book(slug)
            built = detect_built_products(slug)
            qa_label, qa_pass = read_qa_status(slug)
            listing_label = read_listing_status(slug)
            any_built = any((built or {}).values())
            is_done = bool(qa_pass) and bool(any_built) and bool(str(listing_label).startswith("Saved"))
            if is_done:
                return "done"
            if icons > 0 or (qa_label and qa_label != "Not started") or any_built:
                return "in_progress"
            return "not_started"
        except Exception:
            return "not_started"

    def render_priority_chip(title: str, priority: str, status: str = "not_started", href: str | None = None) -> str:
        colours = {
            "P1": {"bg": "#FAECE7", "border": "#C0392B", "text": "#C0392B", "dot": "*"},
            "P2": {"bg": "#FAEEDA", "border": "#E07B00", "text": "#E07B00", "dot": "*"},
            "P3": {"bg": "#FAFADA", "border": "#C8960C", "text": "#C8960C", "dot": "*"},
        }
        done_style = {"bg": "#EEFFEE", "border": "#2D8A00", "text": "#2D8A00", "dot": "*"}
        c = done_style if status == "done" else colours.get(priority, colours["P3"])
        status_label = {"done": "Done", "in_progress": "In progress...", "not_started": ""}.get(status, "")
        chip_body = f"""
    <div style="
        display: inline-block;
        background: {c['bg']};
        border: 1px solid {c['border']};
        border-radius: 20px;
        padding: 6px 14px;
        margin: 4px 4px 4px 0;
        cursor: pointer;
        font-size: 13px;
        font-weight: 500;
        color: {c['text']};
        white-space: nowrap;
    ">
        {c['dot']} {title}
        {"&nbsp;<span style='font-size:11px;opacity:0.8;'>" + status_label + "</span>" if status_label else ""}
    </div>
        """
        if href:
            return f"<a href=\"{href}\" style=\"text-decoration:none;\">{chip_body}</a>"
        return chip_body

    st.markdown("### Next 20 Books to Build")
    st.caption("September 2026 back-to-school SPED/AAC focus — ranked by TPT opportunity and classroom fit")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "<p style='font-size:11px;font-weight:600;color:#C0392B;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:8px;'>Priority 1 - Build first (6 books)</p>",
            unsafe_allow_html=True,
        )
        chips_html = ""
        for slug in p1:
            label = display_map.get(slug, decode_slug(slug))
            status = detect_priority_status(slug)
            href = f"?active_book={slug}&view=build&tab=icons"
            chips_html += render_priority_chip(label, "P1", status, href=href)
        st.markdown(chips_html, unsafe_allow_html=True)

    with col2:
        st.markdown(
            "<p style='font-size:11px;font-weight:600;color:#E07B00;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:8px;'>Priority 2 - Build next (14 books)</p>",
            unsafe_allow_html=True,
        )
        chips_html = ""
        for slug in p2:
            label = display_map.get(slug, decode_slug(slug))
            status = detect_priority_status(slug)
            href = f"?active_book={slug}&view=build&tab=icons"
            chips_html += render_priority_chip(label, "P2", status, href=href)
        st.markdown(chips_html, unsafe_allow_html=True)


_next_stage_cache: dict[str, str] = {}


def next_required_stage_for_slug(slug: str) -> str:
    if slug in _next_stage_cache:
        return _next_stage_cache[slug]
    icons = count_icons_for_book(slug)
    built = detect_built_products(slug)
    _qa_label, qa_pass = read_qa_status(slug)
    listing_saved = read_listing_status(slug).startswith("Saved")
    review = icon_review_summary(slug)
    gates = workflow_gate_status(slug)
    result = next_production_stage(icons, qa_pass, built, listing_saved, review["complete"], gates["setup"], gates["content"], gates["boardready"], marketing_campaign_ready(slug))
    _next_stage_cache[slug] = result
    return result


def clear_stage_caches(slug: str | None = None) -> None:
    """Clear all per-render caches for build-stage data. Call after any state mutation."""
    if slug:
        _icon_count_cache.pop(slug, None)
        _products_cache.pop(slug, None)
        _marketing_cache.pop(slug, None)
        _qa_status_cache.pop(slug, None)
        _listing_status_cache.pop(slug, None)
        _next_stage_cache.pop(slug, None)
    else:
        _icon_count_cache.clear()
        _products_cache.clear()
        _marketing_cache.clear()
        _qa_status_cache.clear()
        _listing_status_cache.clear()
        _next_stage_cache.clear()


def book_last_activity_label(slug: str) -> str:
    path = book_state_path(slug)
    try:
        if path and path.exists():
            changed = datetime.fromtimestamp(path.stat().st_mtime)
            return changed.strftime("%d %b %Y at %H:%M")
    except Exception:
        pass
    return "No saved activity yet"


def render_start_here(slug: str, display_name: str):
    next_stage = next_required_stage_for_slug(slug)
    labels = dict(BUILD_STAGES)
    next_label = "Tracker" if next_stage == "tracker" else labels[next_stage]
    guidance = production_stage_guidance(next_stage if next_stage != "tracker" else "listing")
    gates = workflow_gate_status(slug)
    review = icon_review_summary(slug)
    _qa_label, qa_passed = read_qa_status(slug)
    built = detect_built_products(slug)
    listing_saved = read_listing_status(slug).startswith("Saved")
    stage_done = [gates["setup"], gates["content"], review["complete"], gates["boardready"], qa_passed, required_builds_complete(built), listing_saved, marketing_campaign_ready(slug)]
    completed = sum(bool(value) for value in stage_done)

    # ── HEADER: Book name + progress ──
    st.markdown(f"## {display_name}")
    _pc, _nc = st.columns([3, 1])
    with _pc:
        st.progress(completed / len(BUILD_STAGES), text=f"{completed} of {len(BUILD_STAGES)} production steps complete")
    with _nc:
        if st.button("All steps →", type="primary", use_container_width=True, key=f"start_continue_{slug}"):
            if next_stage == "tracker":
                st.session_state.view = "tracker"
                qp_update(view="tracker", tab=None)
            else:
                open_build_screen(slug, next_stage)
            safe_rerun()

    # ── IMMEDIATELY: Show the icon kit ──
    if gates["content"]:
        ensure_kit(slug)
        kit_key = get_kit_key(slug)
        hero_key = get_hero_key(slug)
        ensure_vocab_state(slug)
        vstate = st.session_state[vocab_state_key(slug)]
        _render_kit_grid(slug, display_name, kit_key, hero_key, vstate, True, 245, 0.06, 512)
    else:
        st.warning("Content review needed before icons can be shown.")
        if st.button("Go to Content review →", type="primary", key=f"start_to_content_{slug}"):
            open_build_screen(slug, "content")
            safe_rerun()

    st.divider()

    # ── NEXT STEPS: What to do next ──
    with st.container(border=True):
        st.markdown(f"### Next step: {next_label}")
        st.write(guidance["purpose"] if next_stage != "tracker" else "This project is ready to review in the upload tracker.")
        if next_stage != "tracker":
            st.info(f"Do this now: {guidance['action']}\n\nYou are finished when: {guidance['done']}")
        _c1, _c2, _c3 = st.columns(3)
        with _c1:
            if st.button("→ Continue", type="primary", use_container_width=True, key=f"start_go_{slug}"):
                if next_stage == "tracker":
                    st.session_state.view = "tracker"
                    qp_update(view="tracker", tab=None)
                else:
                    open_build_screen(slug, next_stage)
                safe_rerun()
        with _c2:
            if st.button("Icons tab", use_container_width=True, key=f"start_icons_{slug}"):
                open_build_screen(slug, "icons")
                safe_rerun()
        with _c3:
            if st.button("All steps", use_container_width=True, key=f"start_all_{slug}"):
                open_build_screen(slug, next_stage if next_stage != "tracker" else "listing")
                safe_rerun()


def render_status_card(slug: str, display_name: str):
    # Compute basic stats
    icons = count_icons_for_book(slug)
    built = detect_built_products(slug)
    qa_label, qa_pass = read_qa_status(slug)
    listing_label = read_listing_status(slug)
    zip_label = read_zip_status(slug)

    # Gates bar thresholds: 6 (Matching etc.), 8 (Word Search), 20 (Bingo)
    gates = workflow_gate_status(slug)
    readiness = product_readiness(icons, qa_pass and gates["setup"] and gates["content"] and gates["boardready"])
    review = icon_review_summary(slug)
    icon_ready = sum(1 for info in readiness.values() if info.get("build_enabled") and info["missing_icons"] == 0)
    active_product_count = sum(1 for spec in PRODUCT_SPECS if spec.get("build_enabled", spec.get("production_status") == "active"))
    quality_goal = 15

    with st.container(border=True):
        st.markdown(f"### {display_name}")
        # Icon gates
        st.markdown("Icons")
        st.progress(min(icons, quality_goal) / quality_goal, text=f"{icons} approved icons - {icon_ready} of {active_product_count} available activities have enough icons")
        st.caption(f"Topic review: {len(review['approved'])} approved, {len(review['skipped'])} intentionally skipped, {len(review['unresolved'])} still to review")

        # Built products row
        cols = st.columns(5)
        prods = list(built.items())
        for idx, (name, ok) in enumerate(prods):
            with cols[idx % 5]:
                st.markdown(f"{'[x]' if ok else '-'} {name}")

        # Badges: QA, Listing, ZIP
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**QA:** {qa_label}")
        with c2:
            st.markdown(f"**Listing:** {listing_label}")
        with c3:
            st.markdown(f"**ZIP:** {zip_label}")

        # Next Action
        target = next_production_stage(icons, qa_pass, built, listing_label.startswith("Saved"), review["complete"], gates["setup"], gates["content"], gates["boardready"], marketing_campaign_ready(slug))
        labels = dict(BUILD_STAGES)
        label = "Open Tracker" if target == "tracker" else f"Continue to {labels[target]}"
        if st.button(label, type="primary", use_container_width=True):
            if target == "tracker":
                st.session_state.view = "tracker"
                qp_update(view="tracker", tab=None)
            else:
                open_build_screen(slug, target)


def render_recent_books_chips(active_slug: str, display_map: dict):
    # Maintain a simple MRU in session state
    recent: list[str] = st.session_state.get("sf_recent_books", [])
    if active_slug and (not recent or recent[0] != active_slug):
        # update MRU
        recent = [active_slug] + [s for s in recent if s != active_slug]
        st.session_state.sf_recent_books = recent[:5]
        persist_session_prefs()
    if not recent:
        return
    st.markdown("#### Recent books")
    cols = st.columns(min(5, len(recent)))
    for i, slug in enumerate(recent[:5]):
        with cols[i]:
            label = display_map.get(slug, decode_slug(slug))
            if st.button(label, key=f"sf_recent_{i}"):
                st.session_state.active_book = slug
                qp_update(active_book=slug)
                show_toast("success", f"Working on: {label}")


# â”€â”€ Phase 3: Build screen & routing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def open_build_screen(slug: str, tab: str = "setup"):
    stage = normalize_build_stage(tab)
    st.session_state.active_book = slug
    st.session_state.view = "build"
    st.session_state.build_tab = stage
    st.session_state[f"sf_requested_stage_{slug}"] = stage
    qp_update(active_book=slug, view="build", tab=stage)


def get_build_tab_from_qp() -> str:
    return normalize_build_stage(qp_get("tab"))


def load_suggestions(slug: str, limit: int = 60) -> list[Path]:
    """Vocab-driven suggestions from symbols library; fallback to existing activity_images."""
    # Primary: vocab list â†’ symbol matches
    vocab = parse_vocab_for_slug(slug)
    if vocab:
        matches = find_symbol_matches(vocab, limit=limit)
        if matches:
            return matches
    # Fallback: icons already in activity_images
    ai = (find_book_dir(slug) or Path("")) / "activity_images"
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    if ai.exists():
        items = [p for p in ai.iterdir() if p.is_file() and p.suffix.lower() in exts]
        return items[:limit]
    return []


def qa_candidates(slug: str, limit: int = 60) -> list[Path]:
    """QA should only consider actual product images in activity_images."""
    ai = (find_book_dir(slug) or Path("")) / "activity_images"
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    if ai.exists():
        items = [p for p in ai.iterdir() if p.is_file() and p.suffix.lower() in exts]
        return items[:limit]
    return []


def get_kit_key(slug: str) -> str:
    return f"sf_kit_{slug}"


def get_hero_key(slug: str) -> str:
    return f"sf_hero_{slug}"


def is_icon_noise(stem: str) -> bool:
    """Heuristic to identify screenshot, untitled, and artifact files."""
    if len(stem) > 50 or stem.startswith("word_"):
        return True
    if stem.lower().startswith("screenshot_"):
        return True
    if stem.lower().startswith("untitled_"):
        return True
    return False


def _norm_word(w: str) -> str:
    """Normalise a vocab word to a file-stem style."""
    return w.strip().lower().replace(" ", "_").replace("-", "_")


def missing_words_for_book(slug: str) -> list[str]:
    """Return vocab words that do not have a matching icon file in activity_images.

    These are words you still need to source an icon for.
    """
    try:
        base = images_dir_for_book(slug)
        vocab_path = base.parent / "book_vocab.json"
        if not base or not base.exists() or not vocab_path.exists():
            return []
        vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
        vocab_words = set(_norm_word(w) for w in (vocab.get("vocab_words") or []))
        activity = set(vocab.get("activity_images") or [])
        # Also respect words explicitly marked as skipped/not needed
        state = read_book_state(slug)
        skipped = set()
        for it in (state.get("qa", {}) or {}).get("items", []) or []:
            if it.get("decision") == "not_needed":
                skipped.add(_norm_word(Path(it.get("filename", "")).stem))
        return sorted([w for w in vocab_words if w not in activity and w not in skipped])
    except Exception:
        return []


def sync_vocab_with_images(slug: str) -> bool:
    """Keep book_state icons_kit and book_vocab.json in sync with the activity_images folder.

    - New .png files are added to icons_kit and QA; real icons start as unreviewed.
    - Suspected noise (screenshots, untitled, long grounding artifacts) is auto-quarantined.
    - Disappeared files are removed from icons_kit and activity_images; the vocab word is preserved.
    - book_vocab.json activity_images is updated to the set of real, non-quarantined icon stems.
    - vocab_words is preserved; new real icon stems are added to it so the word list stays current.
    - Missing words (vocab words without icons) are shown separately in the UI, not as hidden QA items.
    """
    try:
        base = images_dir_for_book(slug)
        if not base or not base.exists():
            return False

        pngs = sorted(base.glob("*.png"))
        all_names = [p.name for p in pngs]
        all_items = [(p.name, p.stem, is_icon_noise(p.stem)) for p in pngs]

        # Update book_state: preserve previously accepted kit, add only new non-noise files
        state = read_book_state(slug)
        saved_kit = set(state.get("icons_kit") or [])

        new_kit = [fn for fn in saved_kit if fn in all_names]
        for fn, stem, noise in all_items:
            if fn in saved_kit:
                continue
            if not noise:
                new_kit.append(fn)
        state["icons_kit"] = sorted(set(new_kit))

        qa = state.get("qa", {}) or {}
        qa_items = qa.get("items", []) or []
        existing_qa = {it.get("filename"): it for it in qa_items if it.get("filename")}
        new_qa = []
        for fn in all_names:
            is_noise = is_icon_noise(Path(fn).stem)
            if fn in existing_qa:
                item = existing_qa.pop(fn)
                # Preserve any user-overridden decision; only default noise to quarantine if still unreviewed
                if item.get("decision") is None or (item.get("decision") == "unreviewed" and is_noise):
                    item["decision"] = "quarantine" if is_noise else (item.get("decision") or "unreviewed")
                new_qa.append(item)
            else:
                new_qa.append({
                    "filename": fn,
                    "decision": "quarantine" if is_noise else "unreviewed",
                    "replacement": None,
                    "confidence": 0.0,
                    "notes": "auto-detected from activity_images" + (" (suspected noise)" if is_noise else ""),
                })
        # Anything left in existing_qa has disappeared from the folder; drop it from active QA
        # The word itself is preserved in book_vocab vocab_words and shown as 'missing' if no icon exists
        qa["items"] = new_qa
        qa["status"] = "in_progress"
        state["qa"] = qa
        write_book_state(slug, state)

        # Update book_vocab.json activity_images to match the current kit
        kit_stems = sorted({Path(fn).stem for fn in new_kit})
        vocab_path = base.parent / "book_vocab.json"
        if vocab_path.exists():
            vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
            if set(vocab.get("activity_images", [])) != set(kit_stems):
                vocab["activity_images"] = kit_stems
                vocab_path.write_text(json.dumps(vocab, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def ensure_kit(slug: str):
    """Ensure the session kit is up to date with the actual activity_images folder."""
    k = get_kit_key(slug)
    sync_vocab_with_images(slug)
    base = images_dir_for_book(slug)
    if base and base.exists():
        state = read_book_state(slug)
        names = state.get("icons_kit") or []
        st.session_state[k] = [str(base / fn) for fn in names if (base / fn).exists()]
    else:
        st.session_state[k] = []


def vocab_state_key(slug: str) -> str:
    return f"sf_vocab_{slug}"


def ensure_vocab_state(slug: str):
    k = vocab_state_key(slug)
    if k not in st.session_state:
        decisions = read_book_state(slug).get("icon_decisions") or {}
        skipped = {word for word, info in decisions.items() if isinstance(info, dict) and info.get("status") == "skipped"}
        if icon_qa_logic is not None:
            try:
                qa_words = ((icon_qa_logic.load_qa_log().get(slug) or {}).get("words") or {})
                skipped.update(word for word, info in qa_words.items() if isinstance(info, dict) and info.get("status") == "skip")
            except Exception:
                pass
        st.session_state[k] = {"skipped": skipped, "show_skipped": False, "swap_word": None, "uploaded": set(), "ban_candidate": None}


def find_symbol_for_word(word: str, slug: str | None = None) -> Path | None:
    if icon_qa_logic is not None:
        try:
            candidates = icon_qa_logic.search_png_library(word, book_key=slug, top_k=1)
            if candidates:
                return Path(str(candidates[0]["path"]))
        except Exception:
            pass
    root = symbols_root()
    if not root.exists():
        return None
    w = _tokenize(word)
    # Exact stem match
    cand = root / f"{w}.png"
    if cand.exists():
        return cand
    # Startswith or contains
    by_stem: dict[str, Path] = {}
    for p in library_png_paths():
        steme = p.stem.lower().replace(" ", "_").replace("-", "_")
        if steme not in by_stem:
            by_stem[steme] = p
    if w in by_stem:
        return by_stem[w]
    for stem, p in by_stem.items():
        if stem.startswith(w + "_") or stem.startswith(w) or (w.replace("_", "") in stem.replace("_", "")):
            return p
    return None


_vocab_source_cache: dict[str, tuple[str | None, dict]] = {}


def theme_vocab_source(slug: str) -> tuple[Path | None, dict]:
    cached = _vocab_source_cache.get(slug)
    if cached is not None:
        path_str, data = cached
        return (Path(path_str) if path_str else None), data
    book_dir = find_book_dir(slug)
    if not book_dir:
        return None, {}
    for path in (book_dir / "book_vocab.json", book_dir / "config" / "book_vocab.json"):
        try:
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    _vocab_source_cache[slug] = (str(path), data)
                    return path, data
        except Exception:
            continue
    return None, {}


def clear_vocab_source_cache(slug: str | None = None) -> None:
    if slug:
        _vocab_source_cache.pop(slug, None)
    else:
        _vocab_source_cache.clear()


def theme_vocab_words(data: dict) -> list[str]:
    """Extract the vocabulary word list from book_vocab.json.

    - fringe_11 / fringe_12 / aac_extras / book_words are plain strings.
    - aac_fringe_vocab is a list of dicts: use the 'word' field.
    - activity_images are icon file stems, not vocabulary words.
    """
    words = []
    for key in ("fringe_12", "fringe_11", "aac_fringe_vocab", "aac_extras", "book_words"):
        values = data.get(key)
        if not isinstance(values, list):
            continue
        for value in values:
            if key == "aac_fringe_vocab" and isinstance(value, dict):
                word = str(value.get("word") or "").strip()
            else:
                word = str(value).strip()
            if word:
                words.append(word)
    seen = set()
    result = []
    for word in words:
        normalized = word.casefold()
        if normalized not in seen:
            seen.add(normalized)
            result.append(word)
    return result


def theme_ambiguous_words(data: dict) -> set[str]:
    result = set()
    for item in data.get("ambiguous") or []:
        if isinstance(item, dict):
            word = str(item.get("word") or "").strip()
        else:
            word = str(item or "").strip()
        if word:
            result.add(word.casefold())
    return result


_icon_review_summary_cache: dict[str, dict] = {}


def icon_review_summary(slug: str) -> dict:
    cached = _icon_review_summary_cache.get(slug)
    if cached is not None:
        return cached
    vocab = extract_book_vocab(slug)
    words = list((vocab or {}).get("book_words") or [])
    approved = []
    skipped = []
    unresolved = []
    for word in words:
        info = icon_word_decision(slug, word)
        if accepted_icon_for_word(slug, word) is not None:
            approved.append(word)
        elif info.get("status") == "skipped":
            skipped.append(word)
        else:
            unresolved.append(word)
    if not words:
        state = read_book_state(slug)
        kit = [str(name) for name in (state.get("icons_kit") or []) if str(name).strip()]
        if not kit:
            image_dir = images_dir_for_book(slug)
            kit = [path.name for path in image_dir.glob("*.png")] if image_dir and image_dir.exists() else []
        approved = kit
    result = {
        "total": len(words) if words else len(approved),
        "approved": approved,
        "skipped": skipped,
        "unresolved": unresolved,
        "complete": bool(approved) and not unresolved,
    }
    _icon_review_summary_cache[slug] = result
    return result


def clear_icon_review_summary_cache(slug: str | None = None) -> None:
    if slug:
        _icon_review_summary_cache.pop(slug, None)
    else:
        _icon_review_summary_cache.clear()


def replace_theme_vocab_word(slug: str, old_word: str, new_word: str) -> tuple[bool, str]:
    old_value = str(old_word or "").strip()
    new_value = str(new_word or "").strip()
    if not old_value or not new_value:
        return False, "Both the current and replacement words are required."
    path, data = theme_vocab_source(slug)
    if path is None:
        return False, "No editable book vocabulary file was found."
    changed = False
    for key in ("fringe_12", "fringe_11", "aac_fringe_vocab", "activity_images", "aac_extras", "book_words"):
        values = data.get(key)
        if not isinstance(values, list):
            continue
        revised = [new_value if str(value).strip().casefold() == old_value.casefold() else value for value in values]
        if revised != values:
            data[key] = revised
            changed = True
    terms = data.get("icon_search_terms")
    if isinstance(terms, dict):
        matched_key = next((key for key in terms if str(key).strip().casefold() == old_value.casefold()), None)
        if matched_key is not None:
            terms.pop(matched_key, None)
            terms[new_value] = new_value
            changed = True
    ambiguous = data.get("ambiguous")
    if isinstance(ambiguous, list):
        for item in ambiguous:
            if isinstance(item, dict) and str(item.get("word", "")).strip().casefold() == old_value.casefold():
                item["word"] = new_value
                changed = True
    if not changed:
        return False, f"{old_value} was not found in the book vocabulary."
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        clear_vocab_source_cache(slug)
        clear_book_vocab_cache(slug)
        return True, f"Changed {old_value} to {new_value}."
    except Exception as exc:
        return False, f"Could not update vocabulary: {exc}"


_book_vocab_cache: dict[str, dict | None] = {}


def clear_book_vocab_cache(slug: str | None = None) -> None:
    if slug:
        _book_vocab_cache.pop(slug, None)
    else:
        _book_vocab_cache.clear()


def extract_book_vocab(slug: str) -> dict | None:
    """Extract vocab words from the AAC board PDF (ZIP) if present for this book.
    Returns dict with keys: book_title, core_words, book_words, all_words, source_file; or None.
    """
    if slug in _book_vocab_cache:
        return _book_vocab_cache[slug]
    # Check manual vocab first
    try:
        source, data = theme_vocab_source(slug)
        if source is not None:
            bwords = theme_vocab_words(data)
            if bwords:
                result = {
                    "book_title": str(data.get("title") or decode_slug(data.get("slug", slug))),
                    "core_words": [],
                    "book_words": bwords,
                    "all_words": bwords,
                    "source_file": str(source),
                }
                _book_vocab_cache[slug] = result
                return result
    except Exception:
        pass
    # Canonical source: BoardReady/boardready/vocab/book_vocab.json (activity_images + aac_extras)
    diag = {"slug": slug, "method": "canonical_json", "found": False, "found_path": None, "parse": None, "key": None}
    try:
        src = project_root() / "BoardReady" / "boardready" / "vocab" / "book_vocab.json"
        diag["found_path"] = str(src)
        if src.exists():
            try:
                data = json.loads(src.read_text(encoding="utf-8"))
            except Exception:
                data = {}
            key = slug if slug in data else None
            if not key and data:
                want = set(_tokenize(slug).split("_"))
                best_k, best_score = None, -1
                for k in data.keys():
                    toks = set(_tokenize(k).split("_"))
                    sc = len(want & toks)
                    if sc > best_score:
                        best_k, best_score = k, sc
                key = best_k
            rec = data.get(key) if key else None
            if rec:
                words = []
                for arr_name in ("activity_images", "aac_extras"):
                    arr = rec.get(arr_name, [])
                    if isinstance(arr, list):
                        words.extend([str(w).strip() for w in arr if str(w).strip()])
                # Dedupe preserving order
                seen = set()
                dedup = []
                for w in words:
                    wl = w.lower()
                    if wl not in seen:
                        seen.add(wl)
                        dedup.append(w)
                diag["found"] = True
                diag["parse"] = "ok"
                diag["key"] = key
                st.session_state[f"sf_aac_diag_{slug}"] = diag
                result = {
                    "book_title": rec.get("title", decode_slug(slug)),
                    "core_words": [],
                    "book_words": dedup,
                    "all_words": dedup,
                    "source_file": str(src),
                }
                _book_vocab_cache[slug] = result
                return result
            else:
                diag["parse"] = "missing_key"
                st.session_state[f"sf_aac_diag_{slug}"] = diag
        else:
            diag["parse"] = "no_file"
            st.session_state[f"sf_aac_diag_{slug}"] = diag
    except Exception:
        diag["parse"] = "exception"
        st.session_state[f"sf_aac_diag_{slug}"] = diag
    # Fallback to Essential words master
    words = parse_vocab_for_slug(slug)
    if words:
        result = {
            "book_title": decode_slug(slug),
            "core_words": [],
            "book_words": words,
            "all_words": words,
            "source_file": "ESSENTIALS_MASTER",
        }
        _book_vocab_cache[slug] = result
        return result
    _book_vocab_cache[slug] = None
    return None


def _render_kit_grid(slug: str, display_name: str, kit_key: str, hero_key: str, vstate: dict, auto_norm: bool, auto_norm_white: int, auto_norm_margin: float, auto_norm_size: int):
    """Render the approved icon kit with actions: Remove, Delete, Rename, Replace, Ban, Hero.
    This is extracted so it can be rendered at the TOP of the icons tab for immediate visibility."""
    kit: list[str] = st.session_state.get(kit_key, [])
    st.markdown("### Your chosen icons")
    st.caption(f"**{len(kit)} approved icons** for {display_name}. The bold name above each icon is the vocabulary word it represents. The hero image is used on the product cover.")
    # Show the required vocabulary words so the user knows what should be there
    _vocab = extract_book_vocab(slug)
    _vocab_words = _vocab.get("vocab_words", []) if _vocab else []
    if _vocab_words:
        with st.expander(f"Required vocabulary words ({len(_vocab_words)}): {', '.join(_vocab_words)}", expanded=False):
            _state = read_book_state(slug)
            _decisions = _state.get("icon_decisions", {})
            _approved_words = set()
            _skipped_words = set()
            _missing_words = []
            for _w in _vocab_words:
                _d = _decisions.get(_w, {})
                _s = str(_d.get("status") or "").lower()
                if _s == "approved":
                    _approved_words.add(_w)
                elif _s == "skipped":
                    _skipped_words.add(_w)
                else:
                    _missing_words.append(_w)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Approved", len(_approved_words))
            with c2:
                st.metric("Skipped", len(_skipped_words))
            with c3:
                st.metric("Missing", len(_missing_words))
            if _missing_words:
                st.warning(f"**Still need icons for:** {', '.join(_missing_words)}")
            if _skipped_words:
                st.caption(f"Skipped: {', '.join(_skipped_words)}")
    cadd1, cadd2, cadd3 = st.columns([3, 1, 1])
    with cadd2:
        if st.button("+ Add icon", key=f"add_icon_{slug}"):
            st.session_state[f"sf_add_icon_{slug}"] = True
    with cadd3:
        if st.button("Clear all", key=f"clear_all_icons_{slug}", help="Remove all icons from the kit and reset decisions"):
            st.session_state[f"clear_all_conf_{slug}"] = True
            safe_rerun()
    with cadd1:
        pass

    # Clear all confirmation
    if st.session_state.get(f"clear_all_conf_{slug}"):
        st.warning("This will remove ALL icons from the kit and reset all icon decisions. The word list will reappear for review.")
        del_files = st.checkbox("Also delete icon files from activity_images folder", value=False, key=f"clear_del_files_{slug}", help="If checked, the PNG files are permanently deleted. If unchecked, they stay on disk but are removed from the kit.")
        cc1, cc2 = st.columns([1, 1])
        with cc1:
            if st.button("Confirm clear all", type="primary", key=f"clear_all_do_{slug}"):
                kit_to_clear = list(st.session_state.get(kit_key, []))
                st.session_state[kit_key] = []
                st.session_state[hero_key] = None
                if del_files:
                    for p in kit_to_clear:
                        try:
                            Path(p).unlink(missing_ok=True)
                        except Exception:
                            pass
                state = read_book_state(slug)
                decisions = state.get("icon_decisions", {})
                for word in list(decisions.keys()):
                    decisions[word] = {"status": "pending", "updated_at": datetime.now().isoformat(timespec="seconds")}
                state["icon_decisions"] = decisions
                state["icons_kit"] = []
                state.pop("hero_icon", None)
                write_book_state(slug, state)
                vkey = vocab_state_key(slug)
                if vkey in st.session_state:
                    st.session_state[vkey]["skipped"] = set()
                st.session_state["sf_extract_files"] = []
                st.session_state.pop(f"clear_all_conf_{slug}", None)
                clear_icon_candidate_cache()
                clear_accepted_icon_cache(slug)
                clear_icon_review_summary_cache(slug)
                show_toast("success", "All icons cleared. Words are back in the review list.")
                safe_rerun()
        with cc2:
            if st.button("Cancel", key=f"clear_all_cancel_{slug}"):
                st.session_state.pop(f"clear_all_conf_{slug}", None)
                safe_rerun()
    if st.session_state.get(f"sf_add_icon_{slug}"):
        cont = st.container()
        with cont:
            up = st.file_uploader("Upload PNG/JPG/WEBP", type=["png","jpg","jpeg","webp"], key=f"add_icon_up_{slug}")
            default_label = ""
            if up is not None:
                default_label = sanitise_symbol_name(Path(up.name).stem)
            label = st.text_input("Label (filename)", value=default_label, key=f"add_icon_lbl_{slug}")
            set_hero = st.checkbox("Set as hero", value=False, key=f"add_icon_hero_{slug}")
            _add_overwrite = st.checkbox("Overwrite if exists", value=False, key=f"add_icon_ow_{slug}", help="Replace an existing library icon with the same name")
            ac1, ac2 = st.columns([1, 1])
            with ac1:
                if st.button("Add to kit", key=f"add_icon_do_{slug}") and up is not None and label.strip():
                    try:
                        stem = sanitise_symbol_name(label)
                        lib = symbols_root() / f"{stem}.png"
                        if lib.exists() and not _add_overwrite:
                            show_toast("warning", f"An icon named '{stem}' already exists. Enable 'Overwrite' to replace it.")
                        else:
                            lib.parent.mkdir(parents=True, exist_ok=True)
                            img = Image.open(io.BytesIO(up.read())).convert("RGBA")
                            img.save(str(lib))
                            dest_dir = images_dir_for_book(slug) or Path("")
                            dest_dir.mkdir(parents=True, exist_ok=True)
                            dest = dest_dir / lib.name
                            if not dest.exists():
                                shutil.copy2(str(lib), str(dest))
                            if auto_norm and dest.exists():
                                try:
                                    normalize_icon_file(dest, target_px=int(auto_norm_size), margin=float(auto_norm_margin), white_cutoff=int(auto_norm_white))
                                except Exception:
                                    pass
                            k = st.session_state.get(kit_key, [])
                            if str(dest) not in k:
                                was_empty = len(k) == 0
                                k.append(str(dest))
                                st.session_state[kit_key] = k
                                if set_hero or was_empty:
                                    st.session_state[hero_key] = dest.name
                                persist_icons_hero(slug, toast_ok=True)
                            st.session_state[f"sf_add_icon_{slug}"] = False
                            safe_rerun()
                    except Exception as e:
                        show_toast("error", f"Add failed: {e}")
            with ac2:
                if st.button("Cancel", key=f"add_icon_cancel_{slug}"):
                    st.session_state[f"sf_add_icon_{slug}"] = False
                    safe_rerun()
    if not kit:
        st.info("No icons in the kit yet. Use 'Review required words' or 'Quick upload' below to add icons.")
    else:
        # If replace mode is active, show the replace panel at the TOP and skip the grid
        rep_state = st.session_state.get(f"kit_replace_target_{slug}")
        if rep_state:
            st.markdown("#### Replace selected icon")
            old_name = Path(rep_state.get("old_path", "")).stem
            old_path = rep_state.get("old_path", "")
            # Show the icon being replaced
            try:
                col_old, col_new = st.columns([1, 3])
                with col_old:
                    st.image(old_path, width=150)
                    st.caption(f"**Replacing:** {old_name}")
                with col_new:
                    del_old = st.checkbox("Delete old file after replace", value=False, key=f"repl_del_old_{slug}")
                    st.markdown("**Option 1:** Search the library for a replacement")
                    q = st.text_input("Search library symbols... (type to search)", value="", key=f"repl_q_{slug}", placeholder="e.g. bed, cry, mama...")
                    if q.strip():
                        files = library_png_paths()
                        files = sorted(files, key=lambda p: p.stem.lower())
                        files = [p for p in files if q.lower() in p.stem.lower()]
                        if not files:
                            st.info("No matching icons found. Try a different search term.")
                        cols_r = st.columns(6)
                        for i, p in enumerate(files[:60]):
                            with cols_r[i % 6]:
                                try:
                                    st.image(str(p), caption=p.stem[:12], width=100)
                                except Exception:
                                    st.write(p.stem)
                                if st.button("Use", key=f"repl_use_lib_{i}"):
                                    dest_dir = images_dir_for_book(slug) or Path("")
                                    try:
                                        dest_dir.mkdir(parents=True, exist_ok=True)
                                        dest = dest_dir / Path(p).name
                                        # Always overwrite — this is a replace operation
                                        shutil.copy2(str(p), str(dest))
                                        try:
                                            normalize_icon_file(dest, target_px=int(auto_norm_size), margin=float(auto_norm_margin), white_cutoff=int(auto_norm_white))
                                        except Exception:
                                            pass
                                        k = list(st.session_state.get(kit_key, []))
                                        idx = k.index(old_path) if old_path in k else rep_state.get("index", 0)
                                        if str(dest) in k and k.index(str(dest)) != idx:
                                            k = [pp for pp in k if pp != old_path]
                                        else:
                                            if 0 <= idx < len(k):
                                                k[idx] = str(dest)
                                            else:
                                                k.append(str(dest))
                                            k = [pp for pp in k if pp != old_path or pp == str(dest)]
                                        if hero_key in st.session_state and st.session_state[hero_key] == Path(old_path).name:
                                            st.session_state[hero_key] = dest.name
                                        st.session_state[kit_key] = k
                                        if del_old:
                                            try:
                                                Path(old_path).unlink(missing_ok=True)
                                            except Exception:
                                                pass
                                        persist_icons_hero(slug)
                                        st.session_state.pop(f"kit_replace_target_{slug}", None)
                                        show_toast("success", "Replaced icon")
                                        safe_rerun()
                                    except Exception as e:
                                        show_toast("error", f"Replace failed: {e}")
                    st.markdown("**Option 2:** Upload a new icon file")
                    up = st.file_uploader("Upload replacement (PNG/JPG/WEBP)", type=["png","jpg","jpeg","webp"], key=f"repl_up_{slug}")
                    _use_uploaded = st.button("Use uploaded file as replacement", key=f"repl_use_up_{slug}", type="primary", disabled=(up is None))
                    if _use_uploaded and up is not None:
                        try:
                            stem = sanitise_symbol_name(Path(up.name).stem)
                            if not stem:
                                show_toast("error", "Invalid filename. Use letters, numbers, and underscores.")
                            else:
                                # Save to library (always overwrite — this is a replace operation)
                                lib = symbols_root() / f"{stem}.png"
                                lib.parent.mkdir(parents=True, exist_ok=True)
                                img = Image.open(io.BytesIO(up.read())).convert("RGBA")
                                img.save(str(lib))
                                # Save to book's activity_images (always overwrite)
                                dest_dir = images_dir_for_book(slug) or Path("")
                                dest_dir.mkdir(parents=True, exist_ok=True)
                                dest = dest_dir / f"{stem}.png"
                                shutil.copy2(str(lib), str(dest))
                                # Update kit: replace old path with new path
                                k = list(st.session_state.get(kit_key, []))
                                old_path = rep_state.get("old_path", "")
                                idx = k.index(old_path) if old_path in k else rep_state.get("index", 0)
                                if 0 <= idx < len(k):
                                    k[idx] = str(dest)
                                else:
                                    k.append(str(dest))
                                # Remove old path from kit if it's different from new
                                k = [pp for pp in k if pp != old_path or pp == str(dest)]
                                # Update hero if needed
                                if hero_key in st.session_state and st.session_state[hero_key] == Path(old_path).name:
                                    st.session_state[hero_key] = dest.name
                                st.session_state[kit_key] = k
                                # Delete old file if requested AND it's different from the new one
                                if del_old and str(dest) != old_path:
                                    try:
                                        Path(old_path).unlink(missing_ok=True)
                                    except Exception:
                                        pass
                                # Update icon decision with new filename
                                state = read_book_state(slug)
                                decisions = state.get("icon_decisions") or {}
                                for word, info in decisions.items():
                                    if isinstance(info, dict) and str(info.get("filename") or "") == Path(old_path).name:
                                        decisions[word]["filename"] = dest.name
                                        decisions[word]["label"] = stem
                                        decisions[word]["source_path"] = str(dest)
                                        decisions[word]["updated_at"] = datetime.now().isoformat(timespec="seconds")
                                        break
                                state["icon_decisions"] = decisions
                                write_book_state(slug, state)
                                persist_icons_hero(slug)
                                clear_accepted_icon_cache(slug)
                                clear_icon_review_summary_cache(slug)
                                st.session_state.pop(f"kit_replace_target_{slug}", None)
                                show_toast("success", f"Replaced with '{stem}'")
                                safe_rerun()
                        except Exception as e:
                            show_toast("error", f"Upload replace failed: {e}")
            except Exception:
                pass
            if st.button("Cancel replace", key=f"repl_cancel_{slug}"):
                st.session_state.pop(f"kit_replace_target_{slug}", None)
                safe_rerun()
            # Skip rendering the grid while replace is active
            return
        # Build reverse mapping: filename -> word (from icon decisions)
        # Build reverse mapping: filename -> word (from icon decisions)
        _state = read_book_state(slug)
        _decisions = _state.get("icon_decisions", {})
        _file_to_word: dict[str, str] = {}
        for _word, _dec in _decisions.items():
            _fn = str(_dec.get("filename") or "").strip()
            if _fn:
                _file_to_word[_fn] = _word
        # Hero indicator on the first icon
        current_hero = st.session_state.get(hero_key)
        # Scoped styling for consistent, unclipped thumbnails and tight spacing
        st.markdown(
            """
<style>
.sf-icons-grid [data-testid="stImage"] img { width: 100% !important; height: 120px !important; object-fit: contain !important; background: #F7F7F7; border: 1px solid rgba(0,0,0,0.06); border-radius: 6px; }
.sf-icons-grid .sf-icon-name { text-align: center; font-size: 12px; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sf-icons-grid .stButton>button { padding: 4px 8px !important; min-height: 32px !important; font-size: 13px !important; width: 100% !important; }
.sf-icons-grid .sf-actions { margin-top: 4px; }
</style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sf-icons-grid">', unsafe_allow_html=True)
        cols2 = st.columns(3)
        for i, path in enumerate(kit):
            with cols2[i % 3]:
                try:
                    nm = Path(path).stem
                    st.image(path, width="stretch")
                except Exception:
                    nm = Path(path).stem
                # Hero badge
                if current_hero and Path(path).name == current_hero:
                    st.markdown(
                        '<div style="text-align:center;font-size:11px;font-weight:700;color:#E1B42D;background:#FFF8E1;border-radius:4px;padding:2px 6px;margin-top:2px">★ HERO</div>',
                        unsafe_allow_html=True,
                    )
                # Show the vocabulary word this icon is approved for (if any)
                _word_label = _file_to_word.get(Path(path).name)
                try:
                    if _word_label:
                        st.markdown(f"<div class='sf-icon-name' style='font-weight:700;color:#0D2545'>{_word_label}</div><div style='font-size:10px;color:#888'>{nm}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='sf-icon-name'>{nm}</div>", unsafe_allow_html=True)
                except Exception:
                    pass
                # Compact inline actions: 2x2 grid + hero button
                # Row 1: Remove | Delete
                a1, a2 = st.columns([1, 1])
                with a1:
                    if st.button("Remove", key=f"rm_{i}", help="Remove from kit (keep file)"):
                        st.session_state[kit_key] = [p for p in kit if p != path]
                        persist_icons_hero(slug)
                        safe_rerun()
                with a2:
                    if st.button("Delete", key=f"rm_file_{i}", help="Delete file and reset word"):
                        st.session_state[f"rm_conf_{i}"] = path
                        safe_rerun()
                # Row 2: Rename | Replace
                a3, a4 = st.columns([1, 1])
                with a3:
                    if st.button("Rename", key=f"rn_{i}", help="Rename this icon file"):
                        st.session_state[f"rn_target_{i}"] = path
                        safe_rerun()
                with a4:
                    if st.button("Replace", key=f"repl_{i}", help="Replace this icon with one from the library or an upload"):
                        st.session_state[f"kit_replace_target_{slug}"] = {"index": i, "old_path": path}
                        safe_rerun()
                # Row 3: Hero button (full width)
                _is_hero = bool(current_hero and Path(path).name == current_hero)
                if st.button("★ Set as hero" if not _is_hero else "★ Current hero", key=f"hero_set_{i}", help="Set as hero image" if not _is_hero else "Current hero", disabled=_is_hero, use_container_width=True):
                    st.session_state[hero_key] = Path(path).name
                    persist_icons_hero(slug, toast_ok=True)
                    show_toast("success", f"Set '{Path(path).stem}' as hero image")
                    safe_rerun()
                # Rename panel
                if st.session_state.get(f"rn_target_{i}") == path:
                    cur_name = Path(path).stem
                    new_name = st.text_input("New name", value=cur_name, key=f"rn_input_{i}", help="Only letters, numbers, underscores")
                    # Check if target name already exists
                    _target_p = Path(path).parent / f"{sanitise_symbol_name(new_name)}.png" if new_name.strip() else None
                    _target_exists = _target_p and _target_p.exists() and _target_p != Path(path)
                    if _target_exists:
                        st.warning(f"A file named '{sanitise_symbol_name(new_name)}.png' already exists. Renaming will overwrite it.")
                    rn1, rn2 = st.columns([1, 1])
                    with rn1:
                        if st.button("Confirm rename", key=f"rn_do_{i}", type="primary") and new_name.strip():
                            try:
                                stem = sanitise_symbol_name(new_name)
                                if not stem:
                                    show_toast("error", "Invalid name. Use letters, numbers, and underscores only.")
                                else:
                                    old_p = Path(path)
                                    new_p = old_p.parent / f"{stem}.png"
                                    if old_p == new_p:
                                        st.session_state.pop(f"rn_target_{i}", None)
                                        safe_rerun()
                                    else:
                                        # If target exists, overwrite it (delete first, then rename)
                                        if new_p.exists():
                                            new_p.unlink(missing_ok=True)
                                        old_p.rename(new_p)
                                        # Update kit paths
                                        st.session_state[kit_key] = [str(new_p) if kp == path else kp for kp in st.session_state.get(kit_key, [])]
                                        # Remove duplicate if the old name was also in the kit
                                        st.session_state[kit_key] = [kp for kp in st.session_state[kit_key] if kp != str(new_p) or kp == str(new_p)]
                                        # Update hero if needed
                                        if hero_key in st.session_state and st.session_state[hero_key] == old_p.name:
                                            st.session_state[hero_key] = new_p.name
                                        # Update icon decision with new filename
                                        state = read_book_state(slug)
                                        decisions = state.get("icon_decisions") or {}
                                        for word, info in decisions.items():
                                            if isinstance(info, dict) and str(info.get("filename") or "") == old_p.name:
                                                decisions[word]["filename"] = new_p.name
                                                decisions[word]["label"] = stem
                                                decisions[word]["updated_at"] = datetime.now().isoformat(timespec="seconds")
                                                break
                                        state["icon_decisions"] = decisions
                                        write_book_state(slug, state)
                                        persist_icons_hero(slug)
                                        clear_accepted_icon_cache(slug)
                                        clear_icon_review_summary_cache(slug)
                                        show_toast("success", f"Renamed to '{stem}'")
                                        st.session_state.pop(f"rn_target_{i}", None)
                                        safe_rerun()
                            except Exception as e:
                                show_toast("error", f"Rename failed: {e}")
                    with rn2:
                        if st.button("Cancel", key=f"rn_cancel_{i}"):
                            st.session_state.pop(f"rn_target_{i}", None)
                            safe_rerun()
                # Delete confirm row
                if st.session_state.get(f"rm_conf_{i}") == path:
                    st.warning("Delete permanently? This removes the icon file and resets the word so you can choose a different icon.")
                    dc1, dc2, dc3 = st.columns([1, 1, 1])
                    with dc1:
                        if st.button("Confirm delete", key=f"rm_conf_do_{i}"):
                            try:
                                Path(path).unlink(missing_ok=True)
                            except Exception:
                                pass
                            st.session_state[kit_key] = [p for p in st.session_state.get(kit_key, []) if p != path]
                            st.session_state.pop(f"rm_conf_{i}", None)
                            stem_name = Path(path).stem
                            _reset_icon_decision(slug, stem_name)
                            persist_icons_hero(slug)
                            clear_accepted_icon_cache(slug)
                            clear_icon_review_summary_cache(slug)
                            show_toast("success", "Icon deleted. The word is back in the review list.")
                            safe_rerun()
                    with dc2:
                        if st.button("Ban + delete", key=f"rm_conf_ban_{i}", help="Delete this icon AND ban it from future searches"):
                            try:
                                Path(path).unlink(missing_ok=True)
                            except Exception:
                                pass
                            st.session_state[kit_key] = [p for p in st.session_state.get(kit_key, []) if p != path]
                            st.session_state.pop(f"rm_conf_{i}", None)
                            stem_name = Path(path).stem
                            _reset_icon_decision(slug, stem_name)
                            _ban_icon_from_library(path)
                            persist_icons_hero(slug)
                            clear_accepted_icon_cache(slug)
                            clear_icon_review_summary_cache(slug)
                            show_toast("success", "Icon deleted and banned from future searches.")
                            safe_rerun()
                    with dc3:
                        if st.button("Cancel", key=f"rm_conf_ca_{i}"):
                            st.session_state.pop(f"rm_conf_{i}", None)
                            safe_rerun()
        st.markdown('</div>', unsafe_allow_html=True)



def _icon_progress_sidebar(slug: str, review_summary: dict):
    """Render a color-coded progress panel showing live icon review counts."""
    total = max(int(review_summary.get("total") or 0), 1)
    approved = len(review_summary.get("approved") or [])
    skipped = len(review_summary.get("skipped") or [])
    unresolved = len(review_summary.get("unresolved") or [])
    pct = int((approved / total) * 100) if total else 0
    st.markdown(
        f"""
        <div style="position:sticky;top:10px;z-index:5;background:#fff;border:1px solid #ccd8df;
        border-radius:12px;padding:14px 18px;margin:10px 0;box-shadow:0 2px 8px #16304712">
        <div style="font-weight:700;font-size:14px;color:#0D2545;margin-bottom:8px">Icon Review Progress</div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:10px">
            <span style="background:#dcfce7;color:#166534;padding:4px 10px;border-radius:8px;font-weight:700;font-size:12px">ACCEPTED: {approved}</span>
            <span style="background:#fee2e2;color:#991b1b;padding:4px 10px;border-radius:8px;font-weight:700;font-size:12px">MISSING: {unresolved}</span>
            <span style="background:#e0eef0;color:#587080;padding:4px 10px;border-radius:8px;font-weight:700;font-size:12px">SKIPPED: {skipped}</span>
            <span style="background:#f0f9ff;color:#0D2545;padding:4px 10px;border-radius:8px;font-weight:700;font-size:12px">TOTAL: {total}</span>
        </div>
        <div style="background:#e8f8f8;border-radius:6px;overflow:hidden;height:22px">
            <div style="background:#31A8A0;height:100%;width:{pct}%;transition:width 0.3s;
            display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:11px">
            {pct}%</div>
        </div>
        <div style="margin-top:8px;font-size:12px;color:#587080">
        {"All icons approved - ready for next step!" if unresolved == 0 else f"Next: review {unresolved} word(s) below - click Accept, Choose another, Upload, or Not needed."}
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_icons_tab(slug: str, display_name: str):
    stage_header("icons", display_name)
    gates = workflow_gate_status(slug)
    if not gates["content"]:
        st.warning("Complete and approve the human content or vocabulary review before selecting production icons.")
        if st.button("Go to Content review", type="primary", key=f"icons_to_content_{slug}"):
            open_build_screen(slug, "content")
            safe_rerun()
        return
    ensure_kit(slug)
    kit_key = get_kit_key(slug)
    hero_key = get_hero_key(slug)
    kit: list[str] = st.session_state[kit_key]
    ensure_vocab_state(slug)
    vstate = st.session_state[vocab_state_key(slug)]
    st.markdown("### Icons")
    # Dynamic "Next best action" panel — context-aware, always at the top
    _review_for_nba = icon_review_summary(slug)
    _nba_total = _review_for_nba.get("total", 0)
    _nba_approved = len(_review_for_nba.get("approved", []))
    _nba_unresolved = len(_review_for_nba.get("unresolved", []))
    _nba_skipped = len(_review_for_nba.get("skipped", []))
    _nba_hero = st.session_state.get(hero_key)
    if _nba_total == 0:
        _nba_msg = "No vocabulary words found. Enter words manually or generate them from the Content step."
        _nba_color = "#fef3c7"
        _nba_fg = "#b45309"
    elif _nba_unresolved > 0:
        _nba_msg = f"Review {_nba_unresolved} unresolved word(s) below — Accept suggestions, Choose another, Upload, or Skip."
        _nba_color = "#fee2e2"
        _nba_fg = "#991b1b"
    elif not _nba_hero and _nba_approved > 0:
        _nba_msg = f"All {_nba_total} words resolved. Choose a hero image below to continue."
        _nba_color = "#dcfce7"
        _nba_fg = "#166534"
    elif _nba_hero and _nba_unresolved == 0:
        _nba_msg = f"Icons complete — {_nba_approved} approved, {_nba_skipped} skipped, hero selected. Continue to BoardReady."
        _nba_color = "#dcfce7"
        _nba_fg = "#166534"
    else:
        _nba_msg = f"Progress: {_nba_approved} of {_nba_total} words approved."
        _nba_color = "#e0eef0"
        _nba_fg = "#0D2545"
    st.markdown(
        f"""<div style="background:{_nba_color};color:{_nba_fg};border-radius:10px;
        padding:12px 16px;margin:8px 0 16px 0;font-weight:600;font-size:14px;
        border-left:4px solid {_nba_fg}">
        <span style="font-size:16px">→</span> {_nba_msg}
        </div>""",
        unsafe_allow_html=True,
    )

    # MISSING ICONS — vocab words that have no matching icon file yet
    _missing_words = missing_words_for_book(slug)
    if _missing_words:
        with st.expander(f"⚠️ {_missing_words.__len__()} word(s) need an icon", expanded=True):
            st.markdown("These words are in your vocabulary but have no icon file yet. Upload or find a symbol for them, or remove the word from the vocab list.")
            for _mword in _missing_words:
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.markdown(f"**{_mword.replace('_', ' ').title()}**")
                with c2:
                    if st.button("Find symbol", key=f"missing_find_{_mword}"):
                        found = find_symbol_for_word(_mword.replace("_", " "), slug)
                        if found and found.exists():
                            dest = images_dir_for_book(slug) / f"{_mword}.png"
                            shutil.copy2(str(found), str(dest))
                            sync_vocab_with_images(slug)
                            ensure_kit(slug)
                            show_toast("success", f"Icon added for {_mword}")
                            safe_rerun()
                        else:
                            show_toast("error", f"No symbol found for {_mword}")
                with c3:
                    if st.button("Not needed", key=f"missing_skip_{_mword}"):
                        state = read_book_state(slug)
                        qa = state.setdefault("qa", {})
                        qa.setdefault("items", []).append({
                            "filename": f"{_mword}.png",
                            "decision": "not_needed",
                            "replacement": None,
                            "confidence": 0.0,
                            "notes": "Word marked as not needing an icon",
                        })
                        write_book_state(slug, state)
                        show_toast("info", f"{_mword} marked as not needed")
                        safe_rerun()

    # KIT GRID — rendered FIRST so the user immediately sees chosen icons with actions
    # (approve/delete/rename/replace/bin/hero) without waiting for the library search.
    auto_norm = True
    auto_norm_white = 245
    auto_norm_margin = 0.06
    auto_norm_size = 512
    _render_kit_grid(slug, display_name, kit_key, hero_key, vstate, auto_norm, auto_norm_white, auto_norm_margin, auto_norm_size)

    st.divider()

    # Quick upload zone — always visible at top so you can skip the slow review
    # if you already have icons ready
    with st.expander("Quick upload — drop PNG icons here (skip the review if you already have icons)", expanded=False):
        st.caption("**Saves to:** this book's `activity_images` folder and adds to the kit.  **Also copies to:** the shared Symbol Library so future books can reuse them.")
        uploaded_files = st.file_uploader(
            "Upload PNG icons",
            type=["png"],
            accept_multiple_files=True,
            key=f"quick_upload_{slug}",
            help="Files are named after the uploaded filename and saved to this book's activity_images folder.",
        )
        if uploaded_files:
            dest_dir = images_dir_for_book(slug)
            if dest_dir:
                dest_dir.mkdir(parents=True, exist_ok=True)
                added_count = 0
                for uf in uploaded_files:
                    safe_name = sanitise_symbol_name(Path(uf.name).stem) + ".png"
                    dest = dest_dir / safe_name
                    try:
                        img = Image.open(uf).convert("RGBA")
                        img.save(str(dest), "PNG")
                        normalize_icon_file(dest, target_px=512, margin=0.06, white_cutoff=245)
                        # Also copy to shared library for reuse
                        lib_copy = symbols_root() / safe_name
                        if not lib_copy.exists():
                            try:
                                shutil.copy2(str(dest), str(lib_copy))
                            except Exception:
                                pass
                        target_path = str(dest)
                        if target_path not in kit:
                            st.session_state[kit_key] = kit + [target_path]
                            if not st.session_state.get(hero_key):
                                st.session_state[hero_key] = safe_name
                            kit = st.session_state[kit_key]
                            added_count += 1
                    except Exception as e:
                        st.error(f"Could not save {uf.name}: {e}")
                if added_count:
                    persist_icons_hero(slug)
                    clear_icon_candidate_cache()
                    show_toast("success", f"Added {added_count} icon(s) to the kit and shared library")
                    safe_rerun()
    workspace_key = f"icon_workspace_{slug}"
    requested_workspace = st.session_state.pop(f"icon_workspace_request_{slug}", None)
    if requested_workspace in {"review", "extract", "library"}:
        st.session_state[workspace_key] = requested_workspace
    workspace = st.radio(
        "Icon workspace",
        options=["review", "library", "extract"],
        format_func=lambda value: {
            "review": "Review required words",
            "library": "Browse full library (14k+ icons)",
            "extract": "Extract from Boardmaker PDF",
        }[value],
        horizontal=True,
        key=workspace_key,
    )
    if workspace in {"extract", "library"}:
        ready, message = ensure_icon_labeler_running()
        if not ready:
            st.error(message)
            if st.button("Try starting Icon Labeller again", key=f"retry_icon_labeler_{slug}"):
                safe_rerun()
            return
        route = "/pdf" if workspace == "extract" else "/"
        st.caption("This is the canonical Icon Labeller embedded inside StudioForge. Saved icons go to this book's `activity_images` folder. Click **Sync & return to review** below after saving icons in the labeller.")
        components.iframe(icon_labeler_url(route, slug), height=1050, scrolling=True)

        # Show current kit status below the iframe so user can see what's been saved
        current_kit = st.session_state.get(get_kit_key(slug), [])
        ai_dir = images_dir_for_book(slug)
        ai_count = 0
        if ai_dir and ai_dir.exists():
            try:
                ai_count = len(list(ai_dir.glob("*.png")))
            except Exception:
                pass
        st.markdown(f"**Icon status:** {len(current_kit)} in kit | {ai_count} files in activity_images")
        needs_sync = len(current_kit) != ai_count and ai_count > 0
        if needs_sync:
            st.warning(f"activity_images has {ai_count} PNGs but kit only shows {len(current_kit)}. New icons detected — click **Sync & return to review**.")

        sync1, sync2, sync3 = st.columns([2, 1, 1])
        with sync1:
            _sync_label = "Sync & return to review →" if needs_sync else "Sync icons from activity_images"
            if st.button(_sync_label, key=f"sync_icons_{slug}", help="Scan the activity_images folder, rebuild the kit from all PNGs found there, and return to the required-words review", type="primary" if needs_sync else "secondary"):
                if ai_dir and ai_dir.exists():
                    try:
                        pngs = sorted(ai_dir.glob("*.png"))
                        # Filter out artifact files with very long names
                        clean = [str(p) for p in pngs if len(p.stem) <= 50 and not p.stem.startswith("word_")]
                        st.session_state[get_kit_key(slug)] = clean
                        # Persist to book state
                        state = read_book_state(slug)
                        state["icons_kit"] = [Path(p).name for p in clean]
                        write_book_state(slug, state)
                        # Clear vocab state so words re-evaluate
                        st.session_state.pop(vocab_state_key(slug), None)
                        clear_accepted_icon_cache(slug)
                        clear_icon_review_summary_cache(slug)
                        clear_icon_candidate_cache()
                        if icon_qa_logic is not None:
                            try:
                                icon_qa_logic._PNG_DIR_CACHE.clear()
                            except Exception:
                                pass
                        show_toast("success", f"Synced {len(clean)} icons from activity_images. Returning to review.")
                        # Auto-return to review workspace
                        st.session_state[workspace_key] = "review"
                        safe_rerun()
                    except Exception as e:
                        st.error(f"Sync failed: {e}")
                else:
                    st.error("No activity_images folder found for this book")
        with sync2:
            if st.button("Refresh icon status", key=f"refresh_integrated_icons_{slug}"):
                st.session_state.pop(vocab_state_key(slug), None)
                clear_accepted_icon_cache(slug)
                clear_icon_review_summary_cache(slug)
                if icon_qa_logic is not None:
                    try:
                        icon_qa_logic._PNG_DIR_CACHE.clear()
                    except Exception:
                        pass
                safe_rerun()
        with sync3:
            if st.button("← Back to review", key=f"back_to_review_{slug}", help="Return to the required-words review without syncing"):
                st.session_state[workspace_key] = "review"
                safe_rerun()
        return
    if st.session_state.get(f"sf_add_icon_{slug}") or st.session_state.get(f"kit_replace_target_{slug}") or vstate.get("swap_word"):
        if st.button("Back to icons", key=f"icons_back_{slug}"):
            st.session_state[f"sf_add_icon_{slug}"] = False
            st.session_state.pop(f"kit_replace_target_{slug}", None)
            vstate["swap_word"] = None
            safe_rerun()
    # Gate indicator — simplified, the next-best-action panel above has the detail
    icons_count = len(kit)
    review_summary = icon_review_summary(slug)
    if review_summary["complete"]:
        st.success(f"All {review_summary['total']} vocabulary words have icons or were intentionally skipped.")
    else:
        st.warning(f"{len(review_summary['unresolved'])} word(s) still need an icon. Review them below.")

    # SECTION 1 — Review required vocabulary words
    st.markdown(f"### Review required words")
    st.caption("Each word below needs an icon. Accept a suggestion, choose another from the library, upload one, or skip if not needed.")
    vocab_data = extract_book_vocab(slug)
    words: list[str] = []
    _vocab_path, topic_vocab = theme_vocab_source(slug)
    ambiguous_words = theme_ambiguous_words(topic_vocab)
    src_path_lc = str((vocab_data or {}).get("source_file", "")).lower()
    manual_cfg = bool(vocab_data and ("/config/book_vocab.json" in src_path_lc or "\\config\\book_vocab.json" in src_path_lc))
    aac_src = (vocab_data or {}).get("source_file") if vocab_data else None
    if not vocab_data:
        st.warning("No AAC board found for this book")
        ta_key = f"sf_vocab_text_{slug}"
        txt = st.text_area("Enter the key vocabulary words for this book (one per line)", key=ta_key, height=140)
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Use these words", key=f"voc_use_{slug}"):
                arr = [t.strip() for t in str(txt or "").splitlines() if t.strip()]
                arr = list(dict.fromkeys(arr))
                d = find_book_dir(slug)
                if d:
                    cfg = d / "config" / "book_vocab.json"
                    try:
                        cfg.parent.mkdir(parents=True, exist_ok=True)
                        payload = {"slug": slug, "source": "manual", "book_words": arr, "saved_at": datetime.now().isoformat(timespec="seconds")}
                        cfg.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                        show_toast("success", "Saved manual vocab")
                        safe_rerun()
                    except Exception as e:
                        show_toast("error", f"Save failed: {e}")
        with c2:
            can_suggest = (anthropic is not None) and bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
            if can_suggest and st.button("Suggest vocab for this book", key=f"voc_suggest_{slug}"):
                title = display_name or decode_slug(slug)
                with st.spinner("Asking Claude..."):
                    sugs = suggest_vocab_for_book(title)
                if sugs:
                    st.session_state[ta_key] = "\n".join(sugs)
                    show_toast("success", "Suggestions added - review before saving")
                    safe_rerun()
                else:
                    show_toast("warning", "No suggestions available")
        st.markdown("#### Or search existing symbols")
        qry = st.text_input("Search symbols by word...", value="")
        if qry.strip():
            files = [p for p in library_png_paths() if qry.lower() in p.stem.lower()]
            files = sorted(files, key=lambda p: p.stem.lower())[:60]
            cols = st.columns(6)
            for i, p in enumerate(files):
                with cols[i % 6]:
                    try:
                        st.image(str(p), caption=p.stem[:12], width=120)
                    except Exception:
                        st.write(p.stem)
                    if st.button("Add to kit", key=f"ms_add_{i}"):
                        dest_dir = images_dir_for_book(slug) or Path("")
                        try:
                            dest_dir.mkdir(parents=True, exist_ok=True)
                            dest = dest_dir / Path(p).name
                            if not dest.exists():
                                shutil.copy2(str(p), str(dest))
                            if auto_norm and dest.exists():
                                try:
                                    normalize_icon_file(dest, target_px=int(auto_norm_size), margin=float(auto_norm_margin), white_cutoff=int(auto_norm_white))
                                except Exception:
                                    pass
                            target_path = str(dest)
                            if target_path not in kit:
                                was_empty = len(kit) == 0
                                st.session_state[kit_key] = kit + [target_path]
                                if was_empty:
                                    st.session_state[hero_key] = Path(dest).name
                                persist_icons_hero(slug)
                        except Exception as e:
                            show_toast("error", f"Could not add: {e}")
        return
    if vocab_data and vocab_data.get("book_words"):
        words = vocab_data["book_words"]
        if manual_cfg:
            st.caption(f"Vocabulary entered manually ({len(words)} words)")
            if st.button("Edit words", key=f"voc_edit_{slug}"):
                st.session_state[f"sf_edit_vocab_{slug}"] = True
        else:
            st.caption(f"Book vocabulary from AAC board ({len(words)} words)")
    else:
        words = parse_vocab_for_slug(slug)
        if words:
            st.caption(f"Vocabulary from master file ({len(words)} words)")
    # Edit vocab panel
    if vocab_data and manual_cfg and st.session_state.get(f"sf_edit_vocab_{slug}"):
        d = find_book_dir(slug)
        cfg = (d / "config" / "book_vocab.json") if d else None
        existing = "\n".join(words) if words else ""
        ta_key2 = f"voc_edit_ta_{slug}"
        ta = st.text_area("Edit vocab words (one per line)", value=existing, key=ta_key2, height=140)
        ec1, ec2, ec3 = st.columns([1, 1, 1])
        with ec1:
            if st.button("Save words", key=f"voc_save_{slug}") and cfg is not None:
                arr = [t.strip() for t in str(ta or "").splitlines() if t.strip()]
                arr = list(dict.fromkeys(arr))
                try:
                    cfg.parent.mkdir(parents=True, exist_ok=True)
                    payload = {"slug": slug, "source": "manual", "book_words": arr, "saved_at": datetime.now().isoformat(timespec="seconds")}
                    cfg.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                    st.session_state[f"sf_edit_vocab_{slug}"] = False
                    show_toast("success", "Vocab updated")
                    safe_rerun()
                except Exception as e:
                    show_toast("error", f"Save failed: {e}")
        with ec2:
            if st.button("Cancel", key=f"voc_cancel_{slug}"):
                st.session_state[f"sf_edit_vocab_{slug}"] = False
                safe_rerun()
        with ec3:
            can_suggest2 = (anthropic is not None) and bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
            if can_suggest2 and st.button("Suggest vocab", key=f"voc_edit_suggest_{slug}"):
                title = display_name or decode_slug(slug)
                with st.spinner("Asking Claude..."):
                    sugs = suggest_vocab_for_book(title)
                if sugs:
                    st.session_state[ta_key2] = "\n".join(sugs)
                    show_toast("success", "Suggestions added - review before saving")
                    safe_rerun()
                else:
                    show_toast("warning", "No suggestions available")
    if not words:
        st.info("No vocabulary words found for this book. Go to the Content step to generate vocabulary, or use Quick upload above to add icons manually.")
    else:
        # If swap panel is active, skip the expensive candidate map computation
        # The swap panel itself is rendered later via the fast-path return
        if vstate.get("swap_word"):
            candidate_map = {}  # Empty placeholder — swap panel doesn't need it
        else:
            # Normal path: full review with candidate map
            unresolved_words = tuple(word for word in words if word not in vstate["skipped"] and accepted_icon_for_word(slug, word) is None)
            # Lazy-load the candidate map: only search if there are unresolved words
            # AND the user opens the review section (or auto-accept hasn't run yet)
            auto_accept_key = f"sf_auto_accepted_{slug}"
            _need_candidates = bool(unresolved_words) and not st.session_state.get(auto_accept_key)
            if _need_candidates:
                with st.spinner(f"Searching the icon library for {len(unresolved_words)} required words. The first search can take a little longer; later searches are cached."):
                    candidate_map = cached_icon_candidate_map(slug, unresolved_words, 6)
            else:
                candidate_map = cached_icon_candidate_map(slug, unresolved_words, 6) if unresolved_words else {}
            # Batch action bar: refresh + accept all high-confidence
            batch_col1, batch_col2, batch_col3 = st.columns([1, 2, 2])
            with batch_col1:
                if st.button("↻ Refresh suggestions", key=f"refresh_icon_candidates_{slug}", help="Re-scan the icon library for new matches"):
                    clear_icon_candidate_cache()
                    if icon_qa_logic is not None:
                        try:
                            icon_qa_logic._PNG_DIR_CACHE.clear()
                        except Exception:
                            pass
                    safe_rerun()
            high_confidence = []
            medium_confidence = []
            for word in words:
                if word in vstate["skipped"] or word.casefold() in ambiguous_words or accepted_icon_for_word(slug, word) is not None:
                    continue
                matches = candidate_map.get(word, [])
                if matches and float(matches[0].get("score", 0)) >= ICON_AUTO_ACCEPT_SCORE:
                    high_confidence.append((word, matches[0]))
                elif matches and float(matches[0].get("score", 0)) >= ICON_SUGGEST_SCORE:
                    medium_confidence.append((word, matches[0]))

            # Auto-accept high-confidence matches on first load (only once per session)
            auto_accept_key = f"sf_auto_accepted_{slug}"
            if high_confidence and not st.session_state.get(auto_accept_key):
                st.session_state[auto_accept_key] = True
                added = 0
                for word, candidate in high_confidence:
                    accepted_ok, _message = accept_icon_candidate(slug, word, str(candidate.get("path") or ""), word)
                    added += int(accepted_ok)
                if added:
                    show_toast("success", f"Auto-approved {added} high-confidence icon(s). Review the rest below.")
                    safe_rerun()

            with batch_col2:
                _hc_label = f"Accept {len(high_confidence)} high-confidence" if high_confidence else "No high-confidence matches"
                if st.button(_hc_label, disabled=not high_confidence, type="primary", help=f"Accept all icons with ≥{int(ICON_AUTO_ACCEPT_SCORE*100)}% match confidence"):
                    added = 0
                    for word, candidate in high_confidence:
                        accepted_ok, _message = accept_icon_candidate(slug, word, str(candidate.get("path") or ""), word)
                        added += int(accepted_ok)
                    show_toast("success", f"Approved {added} high-confidence icons. Lower-confidence matches remain for review.")
                    safe_rerun()
            with batch_col3:
                _mc_label = f"Accept {len(medium_confidence)} suggested" if medium_confidence else "No suggested matches"
                if st.button(_mc_label, disabled=not medium_confidence, help=f"Accept all icons with ≥{int(ICON_SUGGEST_SCORE*100)}% match confidence (requires manual review)"):
                    added = 0
                    for word, candidate in medium_confidence:
                        accepted_ok, _message = accept_icon_candidate(slug, word, str(candidate.get("path") or ""), word)
                        added += int(accepted_ok)
                    show_toast("success", f"Approved {added} suggested icons.")
                    safe_rerun()

        def _row_status(word: str) -> str:
            if vstate.get("swap_word"):
                return "missing"  # Skip expensive lookups during swap
            is_accepted = accepted_icon_for_word(slug, word) is not None
            is_skipped = word in vstate["skipped"]
            if is_accepted:
                return "accepted"
            if is_skipped:
                return "skipped"
            if word.casefold() in ambiguous_words:
                return "ambiguous"
            candidates = candidate_map.get(word, [])
            if candidates and float(candidates[0].get("score", 0)) >= ICON_SUGGEST_SCORE:
                return "suggested"
            return "missing"

        # Skip the expensive word-by-word loop when swap panel is active
        if vstate.get("swap_word"):
            # Just render the swap panel directly — fast path
            active_word = str(vstate.get("swap_word") or "").strip()
            word_key = sanitise_symbol_name(active_word)
            st.markdown(f"#### Swap icon for: **{active_word}**")
            bc1, bc2 = st.columns([1, 4])
            with bc1:
                if st.button("← Back to all words", key="swap_close", use_container_width=True):
                    vstate["swap_word"] = None
                    safe_rerun()
            with bc2:
                st.caption("Search the library below, then click 'Use this icon' to replace.")
            controls = st.columns(2)
            with controls[0]:
                q = st.text_input("Search the complete icon library", value=active_word, key=f"swap_q_{slug}_{word_key}")
            with controls[1]:
                target_label = st.text_input("Save selected icon as", value=active_word, key=f"swap_label_{slug}_{word_key}")
            st.caption("Changing the saved label renames the copy used by this topic. It does not rename the shared library file.")
            with st.spinner("Searching icon library..."):
                candidates = icon_candidates_for_word(q.strip() or active_word, slug, limit=12)
            if not candidates:
                st.info("No library candidates found. Try another search phrase, upload a PNG, or extract icons from a Boardmaker PDF.")
            cols = st.columns(4)
            for i, candidate in enumerate(candidates):
                p = Path(str(candidate.get("path") or ""))
                with cols[i % 4]:
                    try:
                        st.image(str(p), caption=str(candidate.get("label") or p.stem).replace("_", " "), width=120)
                    except Exception:
                        st.write(str(candidate.get("label") or p.stem))
                    st.caption(f"Match {round(float(candidate.get('score', 0)) * 100)}%")
                    if st.button("Use this icon", key=f"swap_use_{i}_{slug}", use_container_width=True, type="primary"):
                        ok, message = accept_icon_candidate(slug, active_word, str(p), target_label)
                        show_toast("success" if ok else "error", message)
                        if ok:
                            vstate["swap_word"] = None
                            safe_rerun()
                    try:
                        is_library_image = p.resolve().is_relative_to(symbols_root().resolve())
                    except Exception:
                        is_library_image = False
                    if is_library_image and st.button("Bin library image", key=f"swap_bin_{i}_{slug}", use_container_width=True):
                        vstate["ban_candidate"] = {"word": active_word, "path": str(p)}
                        safe_rerun()
            pending_ban = vstate.get("ban_candidate")
            if isinstance(pending_ban, dict) and pending_ban.get("path"):
                ban_path = Path(str(pending_ban["path"]))
                st.warning(f"Ban and quarantine {ban_path.name}? It will disappear from future searches but can be restored from Studioforge/_QUARANTINE/icons.")
                confirm_col, cancel_col = st.columns(2)
                with confirm_col:
                    if st.button("Confirm ban and quarantine", type="primary", use_container_width=True, key=f"swap_bin_confirm_{slug}"):
                        ok, message, _destination = quarantine_library_icon(str(ban_path))
                        vstate["ban_candidate"] = None
                        show_toast("success" if ok else "error", message)
                        safe_rerun()
                with cancel_col:
                    if st.button("Cancel", use_container_width=True, key=f"swap_bin_cancel_{slug}"):
                        vstate["ban_candidate"] = None
                        safe_rerun()
            with st.expander("Use from extracted selection"):
                elist = [Path(p) for p in st.session_state.get("sf_extract_files", []) if Path(p).exists()]
                if q.strip():
                    elist = [p for p in elist if q.lower() in p.stem.lower()]
                if not elist:
                    st.caption("No extracted tiles found. Use PDF Extractor to add some.")
                else:
                    ecols = st.columns(6)
                    for j, ep in enumerate(elist[:60]):
                        with ecols[j % 6]:
                            try:
                                st.image(str(ep), caption=ep.stem[:12], width=100)
                            except Exception:
                                st.write(ep.stem)
                            if st.button("Use", key=f"swap_ex_use_{j}"):
                                ok, message = accept_icon_candidate(slug, active_word, str(ep), target_label)
                                show_toast("success" if ok else "error", message)
                                if ok:
                                    vstate["swap_word"] = None
                                    safe_rerun()
            # Multi-file upload also available during swap
            with st.expander("Upload an icon for this word"):
                up = st.file_uploader(f"Upload an icon for '{active_word}'", type=["png","jpg","jpeg","webp"], key=f"swap_up_{slug}_{word_key}")
                if up is not None:
                    try:
                        preview_img = Image.open(io.BytesIO(up.getvalue()))
                        st.image(preview_img, width=150, caption="Preview")
                    except Exception:
                        pass
                    default_lbl = sanitise_symbol_name(Path(up.name).stem) or sanitise_symbol_name(active_word)
                    cur_lbl = st.text_input("Save as", value=default_lbl, key=f"swap_up_lbl_{slug}_{word_key}")
                    _swap_overwrite = st.checkbox("Overwrite if exists", value=False, key=f"swap_ow_{slug}_{word_key}", help="Replace an existing library icon with the same name")
                    if st.button("Save upload", key=f"swap_up_save_{slug}_{word_key}", type="primary") and cur_lbl.strip():
                        try:
                            stem = sanitise_symbol_name(cur_lbl)
                            out = symbols_root() / f"{stem}.png"
                            if out.exists() and not _swap_overwrite:
                                show_toast("warning", f"An icon named '{stem}' already exists. Enable 'Overwrite' to replace it.")
                            else:
                                out.parent.mkdir(parents=True, exist_ok=True)
                                img = Image.open(io.BytesIO(up.getvalue())).convert("RGBA")
                                img.save(str(out))
                                normalize_icon_file(out, target_px=512, margin=0.06, white_cutoff=245)
                                ok, message = accept_icon_candidate(slug, active_word, str(out), cur_lbl)
                                if not ok:
                                    raise RuntimeError(message)
                                vstate["swap_word"] = None
                                show_toast("success", f"Saved '{cur_lbl}' and approved it for '{active_word}'")
                                safe_rerun()
                        except Exception as e:
                            show_toast("error", f"Upload failed: {e}")
            return  # Skip the rest of the icons tab — user is in swap mode

        statuses = {w: _row_status(w) for w in words}
        counts = {
            "accepted": sum(1 for s in statuses.values() if s == "accepted"),
            "suggested": sum(1 for s in statuses.values() if s == "suggested"),
            "missing": sum(1 for s in statuses.values() if s == "missing"),
            "ambiguous": sum(1 for s in statuses.values() if s == "ambiguous"),
            "skipped": sum(1 for s in statuses.values() if s == "skipped"),
        }
        total = max(len(words), 1)
        pct = int(100 * (counts["accepted"] + counts["skipped"]) / total)
        st.markdown(
            f"**Icons progress — {pct}% done**  "
            f"✅ Accepted: {counts['accepted']} | "
            f"💡 Suggested: {counts['suggested']} | "
            f"❓ Missing: {counts['missing']} | "
            f"⚠️ Ambiguous: {counts['ambiguous']} | "
            f"⏭️ Skipped: {counts['skipped']}  "
            f"(Total: {len(words)})"
        )
        st.progress((counts["accepted"] + counts["skipped"]) / total, text=f"{counts['accepted'] + counts['skipped']} of {len(words)} resolved")

        # Next action prompt — large, clear, always visible
        if counts["missing"] > 0:
            st.warning(f"**👉 Next: {counts['missing']} word(s) have no icon match.** Upload a PNG for each, or click 'Not needed' to skip. Scroll down to the missing words.")
        elif counts["suggested"] > 0:
            st.warning(f"**👉 Next: {counts['suggested']} word(s) have suggestions ready.** Review each below and click 'Accept' or 'Choose another'.")
        elif counts["ambiguous"] > 0:
            st.warning(f"**👉 Next: {counts['ambiguous']} word(s) need manual review.** Click 'Choose another' to search the library for each.")
        elif counts["accepted"] + counts["skipped"] == len(words):
            st.success(f"**✅ All {len(words)} words resolved!** Choose your hero image below, then go to BoardReady (step 4).")
            # Inline hero picker at the top so the user doesn't have to scroll to the bottom
            hero_options_top = [Path(p).name for p in st.session_state[kit_key]]
            if hero_options_top:
                _cur_idx = 0
                if hero_key in st.session_state and st.session_state[hero_key] in hero_options_top:
                    _cur_idx = hero_options_top.index(st.session_state[hero_key])
                _chosen_hero = st.selectbox("Choose hero image", options=hero_options_top, index=_cur_idx, key=f"hero_top_{slug}")
                st.session_state[hero_key] = _chosen_hero
                persist_icons_hero(slug)
                _hero_col, _cta_col = st.columns([3, 2])
                with _cta_col:
                    if st.button("Continue to BoardReady →", type="primary", use_container_width=True, key=f"hero_done_{slug}"):
                        open_build_screen(slug, "boardready")
                        safe_rerun()
        else:
            st.info("Review any remaining words below.")

        view_mode = st.radio(
            "Show required words",
            options=["Needs review", "All required", "Accepted"],
            index=0,
            horizontal=True,
            key=f"icons_view_mode_{slug}",
        )
        vstate["show_skipped"] = st.checkbox("Show skipped words (with undo)", value=bool(vstate.get("show_skipped", False)))
        # Compact skipped-words summary with undo, always visible if any are skipped
        skipped_words = [w for w in words if w in vstate["skipped"]]
        if skipped_words and not vstate.get("show_skipped"):
            skip_chips = "  ".join(f"`{w}`" for w in skipped_words)
            st.caption(f"**Skipped ({len(skipped_words)}):** {skip_chips}  —  enable 'Show skipped words' above to undo individual skips.")

        missing_words = [w for w, s in statuses.items() if s == "missing"]
        if missing_words:
            with st.expander(f"Missing words list ({len(missing_words)})", expanded=False):
                txt = "\n".join(missing_words)
                st.text_area("Missing vocabulary words", value=txt, height=160, key=f"missing_words_ta_{slug}", label_visibility="collapsed")
                st.download_button(
                    "Download missing words (.txt)",
                    data=txt.encode("utf-8"),
                    file_name=f"{slug}_missing_words.txt",
                    mime="text/plain",
                    key=f"missing_words_dl_{slug}",
                )
        # Rows per vocab word
        for idx, w in enumerate(words):
            if vstate.get("swap_word") and w != vstate.get("swap_word"):
                continue
            stt = statuses.get(w) or "missing"
            if (stt == "skipped") and (not vstate["show_skipped"]):
                continue
            if view_mode == "Needs review" and stt in ("accepted", "skipped"):
                continue
            if view_mode == "Accepted" and stt != "accepted":
                continue
            cols = st.columns([1, 2, 3])
            row_candidates = candidate_map.get(w, [])
            match = Path(str(row_candidates[0]["path"])) if row_candidates and float(row_candidates[0].get("score", 0)) >= ICON_SUGGEST_SCORE else None
            accepted_path = accepted_icon_for_word(slug, w)
            accepted = accepted_path is not None
            display_icon = accepted_path or match
            skipped = w in vstate["skipped"]
            uploaded_set = vstate.get("uploaded", set())
            uploaded = w in uploaded_set

            with cols[0]:
                # Color-coded status badge
                status_colors = {
                    "accepted": ("#166534", "#dcfce7", "ACCEPTED"),
                    "suggested": ("#b45309", "#fef3c7", "SUGGESTED"),
                    "missing": ("#991b1b", "#fee2e2", "MISSING"),
                    "ambiguous": ("#7c2d12", "#fed7aa", "REVIEW"),
                    "skipped": ("#587080", "#e0eef0", "SKIPPED"),
                }
                badge_fg, badge_bg, badge_label = status_colors.get(stt, status_colors["missing"])
                st.markdown(
                    f'<div style="display:inline-block;padding:4px 10px;border-radius:8px;'
                    f'background:{badge_bg};color:{badge_fg};font-weight:700;font-size:11px;'
                    f'letter-spacing:0.5px;margin-bottom:6px">{badge_label}</div>',
                    unsafe_allow_html=True,
                )
                if display_icon and Path(display_icon).exists():
                    try:
                        st.image(str(display_icon), caption="", width=120)
                    except Exception:
                        st.write(" ")

            with cols[1]:
                st.markdown(f"**{w}**")
                if uploaded:
                    st.caption("Uploaded")
                elif accepted:
                    st.caption("Ready")
                elif skipped:
                    st.caption("Ignored for now")
                else:
                    st.caption("Choose an icon")

            with cols[2]:
                a1, a2, a3, a4 = st.columns([1, 1, 1, 1])
                with a1:
                    if accepted and st.button("Reject", key=f"voc_rej_{idx}", help="Remove this icon approval"):
                        _rej_path = accepted_icon_for_word(slug, w)
                        state = read_book_state(slug)
                        state["icon_decisions"].pop(w, None)
                        st.session_state[kit_key] = [p for p in st.session_state.get(kit_key, []) if (_rej_path is None or str(_rej_path) != p)]
                        state["icons_kit"] = [fn for fn in (state.get("icons_kit") or []) if (_rej_path is None or (_rej_path.name != fn))]
                        state["hero_icon"] = None if state.get("hero_icon") == (_rej_path.name if _rej_path else None) else state.get("hero_icon")
                        vstate["skipped"].discard(w)
                        write_book_state(slug, state)
                        clear_accepted_icon_cache(slug)
                        clear_icon_review_summary_cache(slug)
                        persist_icons_hero(slug)
                        show_toast("info", f"Rejected icon for '{w}'")
                        safe_rerun()
                    show_accept = (not accepted) and (not skipped) and (match is not None)
                    if show_accept and st.button("Accept", key=f"voc_acc_{idx}"):
                        ok, message = accept_icon_candidate(slug, w, str(match), w)
                        show_toast("success" if ok else "error", message)
                        if ok:
                            safe_rerun()
                with a2:
                    show_replace = (not skipped)
                    if show_replace and st.button("Choose another", key=f"voc_swap_{idx}"):
                        vstate["swap_word"] = w
                        safe_rerun()
                with a3:
                    show_skip = (not accepted) and (not skipped)
                    if show_skip and st.button("Not needed", key=f"voc_skip_{idx}"):
                        vstate["skipped"].add(w)
                        set_icon_word_status(slug, w, "skipped")
                        safe_rerun()
                    if skipped and vstate.get("show_skipped"):
                        if st.button("↩ Undo skip", key=f"voc_unskip_{idx}"):
                            vstate["skipped"].discard(w)
                            set_icon_word_status(slug, w, "pending")
                            safe_rerun()
                with a4:
                    up_key = f"voc_up_{idx}"
                    if st.button("Upload PNG", key=f"voc_btn_up_{idx}"):
                        vstate["uploading"] = w
                        safe_rerun()
                    if vstate.get("uploading") == w:
                        up = st.file_uploader(f"Upload an icon for '{w}'", type=["png","jpg","jpeg","webp"], key=up_key, label_visibility="collapsed")
                        if up is not None:
                            # Show preview of uploaded image
                            try:
                                preview_img = Image.open(io.BytesIO(up.getvalue()))
                                st.image(preview_img, width=150, caption="Preview")
                            except Exception:
                                pass
                            try:
                                default_lbl = sanitise_symbol_name(Path(up.name).stem) or sanitise_symbol_name(w)
                            except Exception:
                                default_lbl = sanitise_symbol_name(w)
                            lbl_key = f"voc_up_lbl_{idx}"
                            st.markdown(f"**Save as:** (this becomes the icon file name in the library)")
                            cur_lbl = st.text_input(f"Icon label for '{w}'", value=default_lbl, key=lbl_key, help="Edit this to rename the icon. Only letters, numbers, and underscores.")
                            _voc_overwrite = st.checkbox("Overwrite if exists", value=False, key=f"voc_ow_{idx}", help="Replace an existing library icon with the same name")
                            csa, csb = st.columns([1, 1])
                            with csa:
                                if st.button("Save upload", key=f"voc_up_save_{idx}", type="primary") and cur_lbl.strip():
                                    try:
                                        stem = sanitise_symbol_name(cur_lbl)
                                        out = symbols_root() / f"{stem}.png"
                                        if out.exists() and not _voc_overwrite:
                                            show_toast("warning", f"An icon named '{stem}' already exists. Enable 'Overwrite' to replace it.")
                                        else:
                                            out.parent.mkdir(parents=True, exist_ok=True)
                                            img = Image.open(io.BytesIO(up.getvalue())).convert("RGBA")
                                            img.save(str(out))
                                            normalize_icon_file(out, target_px=int(auto_norm_size), margin=float(auto_norm_margin), white_cutoff=int(auto_norm_white))
                                            ok, message = accept_icon_candidate(slug, w, str(out), cur_lbl)
                                            if not ok:
                                                raise RuntimeError(message)
                                            vstate.setdefault("uploaded", set()).add(w)
                                            vstate["uploading"] = None
                                            show_toast("success", f"Saved '{cur_lbl}' to the library and approved it for '{w}'")
                                            safe_rerun()
                                    except Exception as e:
                                        show_toast("error", f"Upload failed: {e}")
                            with csb:
                                if st.button("Cancel", key=f"voc_up_cancel_{idx}"):
                                    vstate["uploading"] = None
                                    safe_rerun()

            # Inline suggestions (quick swap) under this row
            if not accepted and candidate_map.get(w):
                st.caption("Select Choose another to compare the best library alternatives.")

        # Multi-file upload — adds to shared library only (use Quick upload at top for kit)
        with st.expander("Add icons to the shared Symbol Library (not book-specific)"):
            st.caption("**Saves to:** the shared Symbol Library only. These icons become searchable candidates for **all** books. To add icons directly to this book's kit, use the **Quick upload** at the top of this page.")
            _multi_overwrite = st.checkbox("Overwrite existing icons with same name", value=False, key=f"voc_multi_ow_{slug}", help="If unchecked, files with existing names are skipped")
            ups = st.file_uploader(
                "Upload PNG/JPG/WEBP files",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                key=f"voc_multi_{slug}",
            )
            if ups:
                added_n = 0
                skipped_n = 0
                for f in ups:
                    try:
                        stem = sanitise_symbol_name(Path(f.name).stem)
                        lib = symbols_root() / f"{stem}.png"
                        if lib.exists() and not _multi_overwrite:
                            skipped_n += 1
                            continue
                        lib.parent.mkdir(parents=True, exist_ok=True)
                        img = Image.open(io.BytesIO(f.read())).convert("RGBA")
                        img.save(str(lib))
                        normalize_icon_file(lib, target_px=512, margin=0.06, white_cutoff=245)
                        added_n += 1
                    except Exception:
                        continue
                if added_n or skipped_n:
                    clear_icon_candidate_cache()
                    if icon_qa_logic is not None:
                        try:
                            icon_qa_logic._PNG_DIR_CACHE.clear()
                        except Exception:
                            pass
                    _msg = f"Added {added_n} icons to the shared Symbol Library."
                    if skipped_n:
                        _msg += f" Skipped {skipped_n} existing icon(s) — enable 'Overwrite' to replace them."
                    show_toast("success", _msg)
                    safe_rerun()

        with st.expander("Import icons from a Boardmaker PDF", expanded=False):
            st.caption("Upload the PDF, match the row and column count, then preview every cell. Check or edit the detected labels before saving anything.")
            if fitz is None:
                st.info("PDF import requires PyMuPDF (fitz).")
            else:
                pending_batches = boardmaker_batches_waiting_for_labels(slug)
                if pending_batches:
                    with st.container(border=True):
                        st.markdown(f"#### Waiting for labels ({len(pending_batches)} saved batch{'es' if len(pending_batches) != 1 else ''})")
                        st.caption("These cells were extracted earlier but have not entered the shared icon library.")
                        pending_by_id = {str(batch["batch_id"]): batch for batch in pending_batches}
                        pending_id = st.selectbox(
                            "Choose a saved extraction",
                            options=list(pending_by_id),
                            format_func=lambda value: f"{pending_by_id[value].get('source_name', 'Boardmaker PDF')} - {pending_by_id[value].get('created_at', value)}",
                            key=f"bm_pending_batch_{slug}",
                        )
                        pending_manifest = pending_by_id[pending_id]
                        pending_tiles = load_boardmaker_pending_tiles(pending_manifest)
                        pending_labels = []
                        pending_cols = st.columns(min(int(pending_manifest.get("cols") or 4), 6))
                        for index, tile in enumerate(pending_tiles):
                            with pending_cols[index % len(pending_cols)]:
                                st.image(tile["image"], width="stretch")
                                pending_label = st.text_input(
                                    f"Saved cell {index + 1}",
                                    value=str(tile.get("label") or ""),
                                    key=f"bm_pending_label_{slug}_{pending_id}_{index}",
                                    placeholder="Type a label or leave blank",
                                )
                                pending_labels.append(sanitise_symbol_name(pending_label))
                        pending_labelled = sum(bool(label) for label in pending_labels)
                        st.write(f"**{pending_labelled} of {len(pending_tiles)} cells currently have labels.**")
                        pending_progress, pending_finish = st.columns(2)
                        with pending_progress:
                            if st.button("Save label progress", use_container_width=True, key=f"bm_pending_progress_{slug}_{pending_id}"):
                                save_boardmaker_batch_labels(str(pending_manifest["manifest_path"]), pending_labels)
                                show_toast("success", "Label progress saved. You can safely return later.")
                                safe_rerun()
                        with pending_finish:
                            if st.button(
                                f"Finish and save {pending_labelled} labelled icon{'s' if pending_labelled != 1 else ''}",
                                type="primary",
                                use_container_width=True,
                                disabled=pending_labelled == 0,
                                key=f"bm_pending_finish_{slug}_{pending_id}",
                            ):
                                saved, approved = save_labelled_boardmaker_tiles(slug, pending_tiles, pending_labels, True)
                                save_boardmaker_batch_labels(str(pending_manifest["manifest_path"]), pending_labels, complete=True)
                                show_toast("success", f"Saved {saved} icons to the library and approved {approved} for this book. Blank cells were ignored.")
                                safe_rerun()
                        st.divider()

                pdf = st.file_uploader("Boardmaker PDF", type=["pdf"], key=f"bm_pdf_{slug}")
                c_bm1, c_bm2, c_bm3, c_bm4 = st.columns([1, 1, 1, 1])
                with c_bm1:
                    bm_rows = st.number_input("Rows", min_value=1, max_value=10, value=4, step=1, key=f"bm_rows_{slug}")
                with c_bm2:
                    bm_cols = st.number_input("Columns", min_value=1, max_value=10, value=4, step=1, key=f"bm_cols_{slug}")
                with c_bm3:
                    bm_pad = st.number_input("Inner padding %", min_value=0.0, max_value=20.0, value=2.0, step=0.5, key=f"bm_pad_{slug}")
                with c_bm4:
                    add_to_kit = st.checkbox("Approve labelled icons for this book", value=True, key=f"bm_addkit_{slug}")

                preview_key = f"bm_preview_{slug}"
                if pdf is None:
                    st.info("Choose a PDF to begin.")
                else:
                    pdf_data = pdf.getvalue()
                    signature = hashlib.sha1(pdf_data + f"{bm_rows}:{bm_cols}:{bm_pad}".encode("utf-8")).hexdigest()[:12]
                    if st.button("Preview grid", type="primary", key=f"bm_preview_btn_{slug}"):
                        try:
                            with st.spinner(f"Creating a {int(bm_rows)} by {int(bm_cols)} preview..."):
                                tiles = extract_boardmaker_grid(pdf_data, int(bm_rows), int(bm_cols), float(bm_pad))
                            st.session_state[preview_key] = {"signature": signature, "tiles": tiles}
                            show_toast("success", f"Previewed {len(tiles)} cells. Check the labels below before saving.")
                        except Exception as exc:
                            st.session_state.pop(preview_key, None)
                            show_toast("error", f"Could not preview this PDF: {exc}")

                    preview = st.session_state.get(preview_key) or {}
                    if preview.get("signature") != signature:
                        preview = {}
                    tiles = list(preview.get("tiles") or [])
                    if tiles:
                        st.markdown(f"#### Check {len(tiles)} extracted cells")
                        st.caption("Detected text is only a starting point. Correct each label, and leave decorative or unwanted cells blank.")
                        labels = []
                        preview_cols = st.columns(min(int(bm_cols), 6))
                        for index, tile in enumerate(tiles):
                            with preview_cols[index % len(preview_cols)]:
                                st.image(tile["image"], width="stretch")
                                detected = sanitise_symbol_name(tile.get("label") or tile.get("detected_label") or "")
                                label = st.text_input(
                                    f"Page {tile['page']}, row {tile['row']}, column {tile['col']}",
                                    value=detected,
                                    key=f"bm_tile_label_{slug}_{signature}_{index}",
                                    placeholder="Leave blank to skip",
                                )
                                labels.append(sanitise_symbol_name(label))

                        labelled_count = sum(bool(label) for label in labels)
                        st.write(f"**{labelled_count} of {len(tiles)} cells are labelled and ready to save.**")
                        if labelled_count == 0:
                            st.warning("Nothing will be saved yet. Enter at least one label beneath a preview image.")
                        save_now, save_later = st.columns(2)
                        with save_now:
                            if st.button(
                                f"Save {labelled_count} labelled icon{'s' if labelled_count != 1 else ''}",
                                type="primary",
                                disabled=labelled_count == 0,
                                key=f"bm_save_{slug}_{signature}",
                                use_container_width=True,
                            ):
                                saved, approved = save_labelled_boardmaker_tiles(slug, tiles, labels, add_to_kit)
                                show_toast("success", f"Saved {saved} icons to the library." + (f" Approved {approved} for this book." if add_to_kit else ""))
                                st.session_state.pop(preview_key, None)
                                safe_rerun()
                        with save_later:
                            if st.button("Save all cells for labelling later", key=f"bm_later_{slug}_{signature}", use_container_width=True):
                                ok, message, _batch_dir = save_boardmaker_tiles_for_later(slug, pdf.name, tiles, int(bm_rows), int(bm_cols), labels)
                                show_toast("success" if ok else "error", message)
                                if ok:
                                    st.session_state.pop(preview_key, None)
                                    safe_rerun()

    # Hero direct upload (the hero star button is in the kit grid above)
    with st.expander("Upload a hero image directly", expanded=False):
        hup = st.file_uploader("Choose a hero image file", type=["png","jpg","jpeg","webp"], key=f"hero_up_{slug}")
        if hup is not None:
            h_default = sanitise_symbol_name(Path(hup.name).stem)
            h_label = st.text_input("Label", value=h_default, key=f"hero_lbl_{slug}")
            add_lib = st.checkbox("Add to Symbol Library", value=True, key=f"hero_addlib_{slug}")
            set_hero2 = st.checkbox("Set as hero", value=True, key=f"hero_set_{slug}")
            _hero_overwrite = st.checkbox("Overwrite if exists", value=False, key=f"hero_ow_{slug}", help="Replace an existing library icon with the same name")
            _hero_save_btn = st.button("Save hero image", type="primary", key=f"hero_save_btn_{slug}")
            if _hero_save_btn and h_label.strip():
                try:
                    stem = sanitise_symbol_name(h_label)
                    lib = symbols_root() / f"{stem}.png"
                    if add_lib and lib.exists() and not _hero_overwrite:
                        show_toast("warning", f"An icon named '{stem}' already exists in the library. Enable 'Overwrite' to replace it.")
                    else:
                        if add_lib:
                            lib.parent.mkdir(parents=True, exist_ok=True)
                            img = Image.open(io.BytesIO(hup.read())).convert("RGBA")
                            img.save(str(lib))
                        ddir = images_dir_for_book(slug) or Path("")
                        ddir.mkdir(parents=True, exist_ok=True)
                        dest = ddir / f"{stem}.png"
                        if add_lib and lib.exists() and not dest.exists():
                            shutil.copy2(str(lib), str(dest))
                        if not add_lib:
                            img = Image.open(io.BytesIO(hup.getbuffer())).convert("RGBA")
                            img.save(str(dest))
                            d = find_book_dir(slug)
                            if d:
                                (d / "config").mkdir(parents=True, exist_ok=True)
                                (d / "config" / "hero_image.png").write_bytes(dest.read_bytes())
                        k = st.session_state.get(kit_key, [])
                        if str(dest) not in k:
                            k.append(str(dest))
                            st.session_state[kit_key] = k
                        if set_hero2:
                            st.session_state[hero_key] = dest.name
                        persist_icons_hero(slug, toast_ok=True)
                        show_toast("success", "Hero image set")
                        safe_rerun()
                except Exception as e:
                    show_toast("error", f"Hero upload failed: {e}")


def qa_state_key(slug: str) -> str:
    return f"sf_qa_{slug}"


def ensure_qa_state(slug: str, candidates: list[Path]):
    k = qa_state_key(slug)
    if k not in st.session_state:
        st.session_state[k] = {}
    state: dict = st.session_state[k]
    # Preload from persisted book_state if available
    persisted = {i.get("filename"): i.get("decision") for i in read_book_state(slug).get("qa", {}).get("items", [])}
    for p in candidates:
        sp = str(p)
        if sp not in state:
            fname = Path(sp).name
            prior = persisted.get(fname)
            state[sp] = {"status": prior or "pending", "confidence": 0.9, "replacement": None}
    # prune removed candidates
    keys = set(str(p) for p in candidates)
    for sp in list(state.keys()):
        if sp not in keys:
            del state[sp]


def update_qa_log(slug: str, reviewed: bool):
    paths = [
        project_root() / "BoardReady" / "boardready" / "data" / "qa_review_log.json",
        project_root() / "qa_review_log.json",
    ]
    p = None
    for cand in paths:
        try:
            if cand.exists() or cand.parent.exists():
                p = cand
                break
        except Exception:
            continue
    if not p:
        return
    data = {}
    try:
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    data[slug] = {"reviewed": bool(reviewed)}
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def render_qa_tab(slug: str, display_name: str):
    stage_header("qa", display_name)
    gates = workflow_gate_status(slug)
    if gates["strict"] and not gates["boardready"]:
        st.warning("Confirm the canonical BoardReady vocabulary and output before final visual QA.")
        if st.button("Go to BoardReady review", type="primary", key=f"qa_to_boardready_{slug}"):
            open_build_screen(slug, "boardready")
            safe_rerun()
        return
    saved_qa = read_book_state(slug).get("qa") or {}
    unlock_key = f"qa_unlocked_{slug}"
    if saved_qa.get("status") == "passed" and not st.session_state.get(unlock_key):
        reviewed_at = str(saved_qa.get("reviewed_at") or "previously")
        st.success(f"Visual QA passed {reviewed_at}. The decisions are locked to prevent accidental changes.")
        continue_col, reopen_col = st.columns(2)
        with continue_col:
            if st.button("Continue to Activities", type="primary", use_container_width=True, key=f"qa_continue_build_{slug}"):
                open_build_screen(slug, "build")
                safe_rerun()
        with reopen_col:
            if st.button("Reopen QA review", use_container_width=True, key=f"qa_reopen_{slug}"):
                st.session_state[unlock_key] = True
                safe_rerun()
        return
    ensure_vocab_state(slug)
    vstate = st.session_state[vocab_state_key(slug)]
    kit_key = get_kit_key(slug)
    kit: list[str] = st.session_state.get(kit_key, [])
    review = icon_review_summary(slug)
    if review["total"] and not review["complete"]:
        st.warning(f"Review all topic icons before QA. {len(review['unresolved'])} vocabulary items still need an approved icon or an intentional Skip decision.")
        if st.button("Return to icon exceptions", type="primary", key=f"qa_return_icons_{slug}"):
            open_build_screen(slug, "icons")
            safe_rerun()
        return

    vocab_data = extract_book_vocab(slug)
    words: list[str] = []
    if vocab_data and vocab_data.get("book_words"):
        words = list(vocab_data.get("book_words") or [])
    missing_words: list[str] = []
    suggested_words: list[str] = []
    if words:
        skipped_set = set(vstate.get("skipped", set()) or set())
        for w in words:
            if w in skipped_set:
                continue
            accepted = accepted_icon_for_word(slug, w) is not None
            if accepted:
                continue
            candidates = icon_candidates_for_word(w, slug, limit=1)
            if candidates and float(candidates[0].get("score", 0)) >= ICON_SUGGEST_SCORE:
                suggested_words.append(w)
            else:
                missing_words.append(w)
        st.markdown(
            f"**Vocab icons checklist** - "
            f"Missing: {len(missing_words)} | "
            f"Suggested: {len(suggested_words)}"
        )
        with st.expander("What icons are we still looking for?", expanded=False):
            if missing_words:
                txt = "\n".join(missing_words)
                st.caption("Missing")
                st.text_area("Missing QA items", value=txt, height=140, key=f"qa_missing_words_{slug}", label_visibility="collapsed")
                st.download_button(
                    "Download missing words (.txt)",
                    data=txt.encode("utf-8"),
                    file_name=f"{slug}_missing_words.txt",
                    mime="text/plain",
                    key=f"qa_missing_words_dl_{slug}",
                )
            if suggested_words:
                txt2 = "\n".join(suggested_words)
                st.caption("Suggested")
                st.text_area("Suggested QA items", value=txt2, height=140, key=f"qa_suggested_words_{slug}", label_visibility="collapsed")
                st.download_button(
                    "Download suggested words (.txt)",
                    data=txt2.encode("utf-8"),
                    file_name=f"{slug}_suggested_words.txt",
                    mime="text/plain",
                    key=f"qa_suggested_words_dl_{slug}",
                )
            if st.button("Go to Icons tab", key=f"qa_to_icons_{slug}"):
                qp_update(view="build", tab="icons")
                safe_rerun()

    candidates = qa_candidates(slug, limit=48)
    ensure_qa_state(slug, candidates)
    state: dict = st.session_state[qa_state_key(slug)]

    total = len(state)
    resolved = sum(1 for v in state.values() if v.get("status") in {"accepted", "missing", "replaced"})
    if total == 0:
        st.info("No approved icons are available for visual QA yet. Return to Icons and approve, upload, or extract at least one image.")
        if st.button("Return to Icons", type="primary", key=f"qa_empty_to_icons_{slug}"):
            open_build_screen(slug, "icons")
            safe_rerun()
        return
    st.markdown(f"**QA Progress:** {resolved}/{total}")
    st.progress((resolved / total) if total else 0.0)

    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("Accept all pending icons"):
            n = 0
            for sp, v in state.items():
                if v.get("status") == "pending":
                    v["status"] = "accepted"
                    n += 1
            try:
                persist_qa_draft(slug)
            except Exception:
                pass
            show_toast("success", f"Accepted {n} icons")
            safe_rerun()
    with c2:
        st.caption("Preview and resolve each icon: Accept, Replace, or mark Missing.")

    cols = st.columns(4)
    items = list(state.items())
    for i, (sp, v) in enumerate(items):
        with cols[i % 4]:
            try:
                st.image(sp, caption=Path(sp).stem[:20], width=160)
            except Exception:
                st.write(Path(sp).name)
            st.caption(str(v.get("status") or "pending").replace("_", " ").title())
            a_key = f"qa_acc_{i}"
            m_key = f"qa_miss_{i}"
            r_key = f"qa_rep_{i}"
            up_key = f"qa_up_{i}"
            rs_key = f"qa_reset_{i}"
            if st.button("Accept", key=a_key, disabled=v.get("status") == "accepted"):
                v["status"] = "accepted"
                try:
                    persist_qa_draft(slug)
                except Exception:
                    pass
                safe_rerun()
            if st.button("Missing", key=m_key, disabled=v.get("status") == "missing"):
                v["status"] = "missing"
                try:
                    persist_qa_draft(slug)
                except Exception:
                    pass
                safe_rerun()
            if st.button("Reset", key=rs_key, disabled=v.get("status") == "pending"):
                v["status"] = "pending"
                v["replacement"] = None
                try:
                    persist_qa_draft(slug)
                except Exception:
                    pass
                safe_rerun()
            file = st.file_uploader("Replace", type=["png", "jpg", "jpeg", "webp"], key=up_key)
            if file is not None and st.button("Use replacement", key=r_key):
                try:
                    dest = Path(sp)
                    raw = file.getvalue() if hasattr(file, "getvalue") else file.read()
                    if not raw:
                        raise ValueError("Upload was empty. Try selecting the file again.")
                    img = Image.open(io.BytesIO(raw)).convert("RGBA")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if dest.exists():
                        backup_dir = dest.parent / "_backup" / "qa_replacements"
                        backup_dir.mkdir(parents=True, exist_ok=True)
                        backup = backup_dir / f"{dest.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{dest.suffix}"
                        shutil.copy2(str(dest), str(backup))
                    img.save(str(dest))
                    try:
                        normalize_icon_file(dest, target_px=512, margin=0.06, white_cutoff=245)
                    except Exception:
                        pass
                    v["status"] = "replaced"
                    v["replacement"] = dest.name
                    show_toast("success", "Replacement saved")
                except Exception as e:
                    show_toast("error", f"Replacement failed: {e}")
                try:
                    persist_qa_draft(slug)
                except Exception:
                    pass
                safe_rerun()

    if total and resolved == total:
        st.success("QA passed for this book.")
        if st.button("Mark QA as Passed and go to Build"):
            persist_qa_pass(slug)
            update_qa_log(slug, True)
            st.session_state[f"qa_unlocked_{slug}"] = False
            show_toast("success", "QA marked as passed")
            open_build_screen(slug, "build")


def render_new_topic_panel():
    with st.expander("Create a new topic or student-interest project", expanded=False):
        st.caption("Creates an anonymous project profile first. Grounded content generation and human review happen in the next stages.")
        with st.form("new_topic_project"):
            topic = st.text_input("Topic or student interest", placeholder="e.g. Motorsport pit stops")
            keywords = st.text_input("Optional search keywords", placeholder="teamwork, safety, communication")
            age_band = st.selectbox("Chronological age band", ["Years 7–10 (teen SPED)", "Upper primary", "Post-school transition / adult"])
            reading_level = st.selectbox("Instructional reading level", ["Emergent to functional literacy", "Early reader", "Developing reader"])
            communication_modes = st.multiselect("Communication access", ["Speech", "AAC", "Pointing", "Eye gaze", "Typing", "Writing"], default=["Speech", "AAC", "Pointing"])
            support_level = st.selectbox("Support profile", ["Differentiated", "Highly supported", "Developing independence", "Independent"])
            targets = st.text_area("Learning targets", placeholder="One target per line; do not enter a student name")
            curriculum = st.text_input("Curriculum or functional framework", placeholder="Optional")
            sensitive = st.checkbox("This topic includes sensitive, safeguarding, personal-care, legal, clinical, or sexual-safety content")
            safeguarding = st.text_area("Safeguarding notes", placeholder="Required for sensitive topics") if sensitive else ""
            submitted = st.form_submit_button("Create topic project", type="primary")
        if submitted:
            profile = {
                "topic": topic,
                "title": topic,
                "age_band": age_band,
                "instructional_reading_level": reading_level,
                "communication_modes": communication_modes,
                "support_level": support_level,
                "learning_targets": [line.strip() for line in targets.splitlines() if line.strip()],
                "curriculum_framework": curriculum.strip(),
                "sensitive_content": sensitive,
                "sensitive_review_notes": safeguarding.strip(),
                "seed_keywords": [value.strip() for value in keywords.split(",") if value.strip()],
            }
            errors = validate_project_profile({**default_project_profile("topic_new"), **profile, "pathway": "topic"})
            if errors:
                st.error("Please fix: " + "; ".join(errors))
            else:
                created, message, slug = create_topic_project(profile)
                if created and slug:
                    st.session_state.active_book = slug
                    st.session_state.view = "build"
                    st.session_state[f"sf_requested_stage_{slug}"] = "setup"
                    show_toast("success", message)
                    safe_rerun()
                else:
                    st.error(message)


def render_setup_stage(slug: str, display_name: str):
    stage_header("setup", display_name)
    profile = load_project_profile(slug)
    st.caption("Store only anonymous access needs—never a student name, date of birth, school, or other identifying information.")
    with st.form(f"project_setup_{slug}"):
        pathway = st.selectbox("Project pathway", ["book_companion", "topic", "teen_dignity"], index=["book_companion", "topic", "teen_dignity"].index(profile.get("pathway", "book_companion")))
        topic = st.text_input("Book, topic, or student interest", value=str(profile.get("topic") or display_name))
        age_band = st.text_input("Chronological age band", value=str(profile.get("age_band") or ""))
        reading_level = st.text_input("Instructional reading level", value=str(profile.get("instructional_reading_level") or ""))
        modes = st.multiselect("Communication access", ["Speech", "AAC", "Pointing", "Eye gaze", "Typing", "Writing"], default=[value for value in profile.get("communication_modes", []) if value in {"Speech", "AAC", "Pointing", "Eye gaze", "Typing", "Writing"}])
        support = st.selectbox("Support profile", ["Differentiated", "Highly supported", "Developing independence", "Independent"], index=["Differentiated", "Highly supported", "Developing independence", "Independent"].index(profile.get("support_level", "Differentiated")) if profile.get("support_level") in ["Differentiated", "Highly supported", "Developing independence", "Independent"] else 0)
        targets = st.text_area("Learning targets", value="\n".join(profile.get("learning_targets", [])))
        curriculum = st.text_input("Curriculum or functional framework", value=str(profile.get("curriculum_framework") or ""))
        sensitive = st.checkbox("Sensitive-content safeguards required", value=bool(profile.get("sensitive_content")))
        sensitive_notes = st.text_area("Safeguarding and implementation notes", value=str(profile.get("sensitive_review_notes") or ""))
        save_setup = st.form_submit_button("Save setup", type="primary")
    if save_setup:
        revised = {
            **profile,
            "pathway": pathway,
            "topic": topic.strip(),
            "age_band": age_band.strip(),
            "instructional_reading_level": reading_level.strip(),
            "communication_modes": modes,
            "support_level": support,
            "learning_targets": [line.strip() for line in targets.splitlines() if line.strip()],
            "curriculum_framework": curriculum.strip(),
            "sensitive_content": sensitive,
            "sensitive_review_notes": sensitive_notes.strip(),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        critical_fields = ("pathway", "topic", "age_band", "instructional_reading_level", "communication_modes", "support_level", "learning_targets", "curriculum_framework", "sensitive_content", "sensitive_review_notes")
        if any(revised.get(key) != profile.get(key) for key in critical_fields) and revised.get("pathway") in {"topic", "teen_dignity"}:
            revised["content_review"] = {"status": "pending", "reason": "Project setup changed"}
            revised["boardready_review"] = {"status": "pending", "reason": "Project setup changed"}
        errors = validate_project_profile(revised)
        if errors:
            st.error("Please fix: " + "; ".join(errors))
        elif save_project_profile(slug, revised):
            show_toast("success", "Project setup saved")
            safe_rerun()
    if profile.get("pathway") in {"topic", "teen_dignity"}:
        st.divider()
        st.markdown("#### Grounded content draft")
        if topic_content_ready(slug):
            st.success("A structured content draft is available.")
        else:
            st.warning("The topic scaffold exists, but grounded teaching content has not been generated yet.")
        if st.button("Generate grounded content draft", type="primary", key=f"generate_topic_content_{slug}"):
            with st.spinner("Researching sources and generating structured content..."):
                ok, message = run_topic_content_builder(slug)
            show_toast("success" if ok else "error", message)
            if ok:
                st.session_state[f"sf_requested_stage_{slug}"] = "content"
                safe_rerun()


def render_content_review_stage(slug: str, display_name: str):
    stage_header("content", display_name)
    profile = load_project_profile(slug)
    strict = workflow_gate_status(slug)["strict"]
    if profile.get("pathway") == "book_companion":
        render_vocabulary_queue(slug)
        if book_vocab_review_required(slug):
            return
        st.divider()
    if not strict:
        st.info("This existing book companion is grandfathered into the production workflow. Use this review when revising source content or claims.")
    book_dir = find_book_dir(slug)
    vocab_path = (book_dir / "book_vocab.json") if book_dir else None
    needs_path = (book_dir / "needs_review.json") if book_dir else None
    research_path = (book_dir / "config" / "topic_research.json") if book_dir else None
    evidence_ready = not strict
    if not topic_content_ready(slug) and strict:
        st.warning("Generate a grounded content draft in Setup before approving this stage.")
        if st.button("Return to Setup and generate the draft", type="primary", key=f"content_to_setup_{slug}"):
            open_build_screen(slug, "setup")
            safe_rerun()
        return
    if research_path and research_path.exists():
        try:
            research = json.loads(research_path.read_text(encoding="utf-8"))
            evidence_ready = len(research.get("facts", [])) >= 3 and bool(research.get("sources"))
            st.markdown(f"**Evidence:** {len(research.get('facts', []))} grounded facts from {len(research.get('sources', []))} sources")
            with st.expander("Review evidence and sources"):
                for index, source in enumerate(research.get("sources", []), start=1):
                    st.write(f"{index}. {source}")
        except Exception:
            st.warning("The research evidence file could not be read.")
    if strict and not evidence_ready:
        st.error("At least three grounded facts and one recorded source are required before approval.")
    if vocab_path and vocab_path.exists():
        with st.expander("Review structured content"):
            st.json(json.loads(vocab_path.read_text(encoding="utf-8")))
    if needs_path and needs_path.exists():
        try:
            flagged = json.loads(needs_path.read_text(encoding="utf-8"))
        except Exception:
            flagged = {}
        if any(flagged.values()) if isinstance(flagged, dict) else bool(flagged):
            st.warning("Some generated items were not sufficiently grounded and remain excluded unless manually amended.")
            with st.expander("Review excluded or flagged items"):
                st.json(flagged)
    checks = content_review_checks(profile)
    saved_review = profile.get("content_review") if isinstance(profile.get("content_review"), dict) else {}
    saved_checks = saved_review.get("checks") if isinstance(saved_review.get("checks"), dict) else {}
    saved_values = {key: bool(saved_checks.get(key)) for key, _label in checks}
    values = {}
    for key, label in checks:
        values[key] = st.checkbox(label, value=saved_values[key], key=f"content_review_{slug}_{key}")
    if values != saved_values:
        profile["content_review"] = {
            **saved_review,
            "status": "pending",
            "checks": values,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        save_project_profile(slug, profile)
    can_approve = all(values.values()) and (topic_content_ready(slug) or not strict) and evidence_ready
    if st.button("Approve content for production", type="primary", disabled=not can_approve, key=f"approve_content_{slug}"):
        reviewed_at = datetime.now().isoformat(timespec="seconds")
        profile["content_review"] = {"status": "approved", "reviewed_at": reviewed_at, "reviewer": "human", "checks": values}
        save_project_profile(slug, profile)
        if vocab_path and vocab_path.exists():
            vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
            vocab["review_status"] = "human_approved"
            vocab["reviewed_at"] = reviewed_at
            vocab_path.write_text(json.dumps(vocab, ensure_ascii=False, indent=2), encoding="utf-8")
        show_toast("success", "Content review approved")
        st.session_state[f"sf_requested_stage_{slug}"] = "icons"
        safe_rerun()


def render_boardready_stage(slug: str, display_name: str):
    stage_header("boardready", display_name)
    profile = load_project_profile(slug)
    strict = workflow_gate_status(slug)["strict"]
    fringe = topic_fringe_words(slug)
    boardready_review = profile.get("boardready_review") if isinstance(profile.get("boardready_review"), dict) else {}
    draft_fringe = boardready_review.get("draft_fringe") if isinstance(boardready_review.get("draft_fringe"), list) else fringe
    st.caption("Core-word positions stay fixed. Review exactly twelve topic words, then generate and inspect the canonical BoardReady files.")
    fringe_text = st.text_area("Twelve fringe words - one per line", value="\n".join(draft_fringe), height=220, key=f"boardready_fringe_{slug}")
    edited_fringe = list(dict.fromkeys(line.strip() for line in fringe_text.splitlines() if line.strip()))
    if edited_fringe != draft_fringe:
        profile["boardready_review"] = {
            **boardready_review,
            "draft_fringe": edited_fringe,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        save_project_profile(slug, profile)
    st.markdown(f"**Topic fringe vocabulary:** {len(edited_fringe)}/12")
    if len(edited_fringe) != 12:
        st.error("Exactly 12 unique fringe words are required.")
    if st.button("Save fringe vocabulary", disabled=len(edited_fringe) != 12, key=f"save_boardready_fringe_{slug}"):
        path, data = theme_vocab_source(slug)
        if path is None:
            st.error("No editable topic vocabulary file was found.")
        else:
            data["fringe_12"] = edited_fringe
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            profile["boardready_review"] = {"status": "pending"}
            save_project_profile(slug, profile)
            show_toast("success", "Fringe vocabulary saved")
            safe_rerun()
    outputs = boardready_output_files(slug)
    if st.button("Generate canonical BoardReady files", type="primary", disabled=len(edited_fringe) != 12, key=f"generate_boardready_{slug}"):
        with st.spinner("Generating the fixed 6×6 BoardReady board..."):
            ok, message = run_boardready_generator(slug)
        show_toast("success" if ok else "error", message)
        safe_rerun()
    if outputs:
        st.success(f"Found {len(outputs)} BoardReady PDF output(s).")
        with st.expander("BoardReady output files"):
            for output in outputs:
                st.write(output.name)
    else:
        st.warning("No BoardReady PDF output has been detected yet.")
    with st.expander("Edit or preview the board layout", expanded=True):
        render_aac_board_tab(slug, display_name)
    ready = (not strict) or (len(fringe) == 12 and bool(outputs))
    if st.button("Confirm BoardReady vocabulary and output", type="primary", disabled=not ready, key=f"confirm_boardready_{slug}"):
        profile["boardready_review"] = {"status": "approved", "reviewed_at": datetime.now().isoformat(timespec="seconds"), "fringe_12": fringe, "layout": "6x6", "preserve_core_positions": True, "outputs": [str(path) for path in outputs]}
        save_project_profile(slug, profile)
        show_toast("success", "BoardReady review confirmed")
        st.session_state[f"sf_requested_stage_{slug}"] = "qa"
        safe_rerun()


def _run_dignity_generator(spec: dict, images_folder: str, pack_code: str, theme_name: str) -> tuple[bool, str]:
    """Run a single Dignity generator by importing its module and calling its function."""
    try:
        module_name = spec["module"]
        func_name = spec["func"]
        mod = importlib.import_module(module_name)
        func = getattr(mod, func_name)
        ok = func(images_folder, pack_code=pack_code, theme_name=theme_name)
        return bool(ok), f"{spec['name']}: {'OK' if ok else 'FAILED'}"
    except Exception as exc:
        return False, f"{spec['name']}: {exc}"


def render_dignity_stage(slug: str, display_name: str):
    """Dignity-specific build stage — separate from book companion activities.

    Only shown for the 'teen_dignity' pathway. Builds Dignity products
    (social story, scenario activity, choice board, visual supports,
    dignity cover) from the enriched Dignity topic JSON.
    """
    stage_header("dignity", display_name)
    profile = load_project_profile(slug)
    pathway = profile.get("pathway", "")
    if pathway != "teen_dignity":
        st.info("Dignity products are only available for the Teen Dignity pathway.")
        if st.button("Go to Setup to change pathway", key=f"dignity_to_setup_{slug}"):
            st.session_state[f"sf_requested_stage_{slug}"] = "setup"
            safe_rerun()
        return

    st.caption("Dignity products are built from the enriched topic JSON and are separate from book companion activities.")

    # Check for enriched topic JSON
    bd = find_book_dir(slug)
    images_folder = str(bd / "activity_images") if bd else str(Path("assets/themes") / slug / "activity_images")
    pack_code = default_pack_code(slug)

    # Try to locate the enriched JSON
    dignity_json_found = False
    dignity_json_path = None
    candidates = []
    if bd:
        candidates.append(bd / "config" / f"{slug}_ENRICHED.json")
        candidates.append(bd / f"{slug}_ENRICHED.json")
    candidates.append(project_root() / "01_ACTIVE_FACTORY" / "pipeline_products" / f"{slug}_ENRICHED_DRAFT_v1.json")
    candidates.append(project_root() / "Dignity" / "topics" / f"{slug}_ENRICHED_v1.json")
    for p in candidates:
        if p.exists():
            dignity_json_found = True
            dignity_json_path = p
            break

    if not dignity_json_found:
        st.warning("No enriched Dignity topic JSON found. Generate content first (Setup → Content stages).")
        if st.button("Go to Content stage", type="primary", key=f"dignity_to_content_{slug}"):
            st.session_state[f"sf_requested_stage_{slug}"] = "content"
            safe_rerun()
        return

    st.success(f"Enriched topic JSON: {dignity_json_path.name}")

    # Detect existing Dignity outputs
    out_dir = bd / "OUTPUT" if bd else Path("assets/themes") / slug / "OUTPUT"
    dignity_outputs = []
    if out_dir.exists():
        dignity_outputs = sorted(out_dir.glob(f"{pack_code}_*.pdf"))

    # Dignity product list
    st.markdown("#### Dignity products")
    st.caption("These are separate from book companion activities. Each product reads from the enriched Dignity topic JSON.")

    # Build individual products
    for spec in DIGNITY_PRODUCT_SPECS:
        product_name = spec["name"]
        display = spec.get("display_name", product_name)
        with st.expander(f"{display}", expanded=False):
            st.caption(spec.get("status_reason", ""))
            st.caption(f"Pages: ~{spec.get('pages', '?')} | Min icons: {spec.get('min_icons', 0)}")
            if st.button(f"Build {product_name}", type="primary", key=f"dignity_build_{product_name}_{slug}",
                        disabled=st.session_state.get("sf_building", False)):
                st.session_state.sf_building = True
                st.session_state.sf_building_product = product_name
                safe_rerun()
            # Check if output exists
            existing = [p for p in dignity_outputs if product_name.replace(" ", "_").replace("/", "_") in p.name]
            if existing:
                st.success(f"Built: {existing[0].name}")

    st.divider()

    # Build all Dignity products
    if st.button("Build All Dignity Products", type="primary", key=f"dignity_build_all_{slug}",
                disabled=st.session_state.get("sf_building", False)):
        st.session_state.sf_building = True
        all_ok = True
        progress = st.progress(0.0)
        status = st.empty()
        for i, spec in enumerate(DIGNITY_PRODUCT_SPECS):
            status.write(f"Building {spec['name']}...")
            ok, msg = _run_dignity_generator(spec, images_folder, pack_code, display_name)
            if not ok:
                all_ok = False
            progress.progress((i + 1) / len(DIGNITY_PRODUCT_SPECS))
        st.session_state.sf_building = False
        st.session_state.sf_building_product = None
        if all_ok:
            show_toast("success", "All Dignity products built")
        else:
            show_toast("error", "Some Dignity products failed — check output above")
        safe_rerun()

    # Show existing outputs
    if dignity_outputs:
        st.markdown("#### Existing Dignity outputs")
        with st.expander(f"{len(dignity_outputs)} Dignity PDF(s) in OUTPUT", expanded=False):
            for p in dignity_outputs:
                st.write(p.name)

    # Confirm stage
    if dignity_outputs:
        if st.button("Confirm Dignity products built", type="primary", key=f"confirm_dignity_{slug}"):
            profile["dignity_review"] = {
                "status": "approved",
                "reviewed_at": datetime.now().isoformat(timespec="seconds"),
                "outputs": [str(p) for p in dignity_outputs],
            }
            save_project_profile(slug, profile)
            show_toast("success", "Dignity products confirmed")
            st.session_state[f"sf_requested_stage_{slug}"] = "listing"
            safe_rerun()


def render_promote_stage(slug: str, display_name: str):
    stage_header("promote", display_name)
    state = read_book_state(slug)
    listing = state.get("listing") if isinstance(state.get("listing"), dict) else {}
    if not listing.get("saved_at"):
        st.warning("Save the approved TPT listing before preparing a campaign.")
        if st.button("Return to Listing", type="primary", key=f"promote_to_listing_{slug}"):
            open_build_screen(slug, "listing")
            safe_rerun()
        return
    out_dir = output_dir_for_book(slug)
    if out_dir is None:
        st.error("The book output folder is unavailable.")
        return
    pack_code = str((state.get("build") or {}).get("pack_code") or default_pack_code(slug))
    images_dir = out_dir / "TPT_UPLOAD" / "IMAGES" / pack_code
    records = read_upload_tracker()
    tracked_urls = [
        str(record.get("tpt_url") or "").strip()
        for record in records
        if isinstance(record, dict) and record.get("book_slug") == slug and is_tpt_product_url(str(record.get("tpt_url") or ""))
    ]
    default_url = tracked_urls[0] if tracked_urls else ""

    st.subheader("Guided Pinterest and Tailwind campaign")
    st.caption("This creates local draft files only. StudioForge will not connect to, schedule, or publish on any external account.")
    destination_url = st.text_input(
        "Exact published TPT product URL",
        value=default_url,
        key=f"promote_tpt_url_{slug}",
        placeholder="https://www.teacherspayteachers.com/Product/...",
    )
    default_board = st.text_input(
        "Preferred Pinterest board (optional)",
        value="",
        key=f"promote_board_{slug}",
        placeholder="Leave blank to use an angle-specific suggestion",
    )
    if destination_url and not is_tpt_product_url(destination_url):
        st.error("Use the exact HTTPS product listing URL. A general store URL is too broad for an effective campaign.")

    if not images_dir.exists() or not any(path.suffix.lower() in {".png", ".jpg", ".jpeg"} for path in images_dir.glob("*")):
        st.info("Generate the four TPT marketing pages before creating vertical Pinterest designs.")
        if st.button("Generate TPT marketing pages", type="primary", key=f"promote_generate_images_{slug}"):
            built_info = detect_products_in_output(slug)
            images = generate_tpt_marketing_pages(slug, pack_code, out_dir, built_info, display_name)
            show_toast("success" if images else "error", f"Created {len(images)} marketing pages." if images else "No marketing pages could be created. Build and preview a product first.")
            safe_rerun()
    else:
        if st.button(
            "Generate six reviewed Pin drafts",
            type="primary",
            disabled=not is_tpt_product_url(destination_url),
            key=f"promote_generate_{slug}",
        ):
            ok, message, _campaign_dir = generate_guided_pinterest_campaign(
                slug,
                pack_code,
                out_dir,
                listing,
                images_dir,
                destination_url,
                default_board,
            )
            show_toast("success" if ok else "error", message)
            safe_rerun()

    campaign_root = out_dir / "TPT_UPLOAD" / "PROMOTE" / pack_code
    manifest_path = campaign_root / f"{pack_code}_campaign.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        st.success(f"Campaign ready for review: {len(manifest.get('pins') or [])} fresh Pin drafts")
        st.caption("Review every title, description, board and link. Then upload the PNG files through Tailwind's Pin Scheduler as drafts.")
        pin_paths = [campaign_root / str(row.get("filename") or "") for row in manifest.get("pins") or []]
        cols = st.columns(3)
        for index, (row, pin_path) in enumerate(zip(manifest.get("pins") or [], pin_paths)):
            with cols[index % 3]:
                if pin_path.exists():
                    st.image(str(pin_path), width="stretch")
                st.markdown(f"**{row.get('creative_angle', 'Pin')}**")
                st.caption(str(row.get("pin_title") or ""))
                st.caption(f"Board: {row.get('suggested_board') or 'Choose in Tailwind'}")
        zip_path = campaign_root / f"{pack_code}_guided_tailwind_upload.zip"
        csv_path = campaign_root / f"{pack_code}_guided_upload_review.csv"
        dl_zip, dl_csv, open_review = st.columns(3)
        with dl_zip:
            if zip_path.exists():
                st.download_button("Download complete campaign", data=zip_path.read_bytes(), file_name=zip_path.name, mime="application/zip", use_container_width=True)
        with dl_csv:
            if csv_path.exists():
                st.download_button("Download review CSV", data=csv_path.read_bytes(), file_name=csv_path.name, mime="text/csv", use_container_width=True)
        with open_review:
            if st.button("Open campaign folder", use_container_width=True, key=f"promote_open_{slug}"):
                open_folder(campaign_root)
        st.info("Tailwind: open Pin Scheduler, choose Upload, select the six PNG files, keep them as drafts, then use the review CSV to copy the approved title, description, board and product link.")
        if manifest.get("status") == "approved":
            st.success(f"Campaign approved {manifest.get('reviewed_at', '')}. You can continue to Tracker.")
        elif st.button("Mark campaign reviewed", type="primary", key=f"promote_approve_{slug}"):
            manifest["status"] = "approved"
            manifest["reviewed_at"] = datetime.now().isoformat(timespec="seconds")
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            show_toast("success", "Campaign marked as reviewed.")
            safe_rerun()


def render_build_screen(slug: str, display_name: str):
    icons = count_icons_for_book(slug)
    built = detect_built_products(slug)
    _qa_label, qa_passed = read_qa_status(slug)
    listing_saved = read_listing_status(slug).startswith("Saved")
    review = icon_review_summary(slug)
    gates = workflow_gate_status(slug)
    next_stage = next_production_stage(icons, qa_passed, built, listing_saved, review["complete"], gates["setup"], gates["content"], gates["boardready"], marketing_campaign_ready(slug))
    requested_key = f"sf_requested_stage_{slug}"
    stage_key = f"sf_build_stage_{slug}"
    requested = st.session_state.pop(requested_key, None)
    if requested is not None:
        st.session_state[stage_key] = normalize_build_stage(requested)
    elif stage_key not in st.session_state:
        st.session_state[stage_key] = normalize_build_stage(st.session_state.get("build_tab"))

    st.header(display_name)
    stage_done = {
        "setup": bool(gates["setup"]),
        "content": bool(gates["content"]),
        "icons": bool(review["complete"]),
        "boardready": bool(gates["boardready"]),
        "qa": bool(qa_passed),
        "build": required_builds_complete(built),
        "listing": bool(listing_saved),
        "promote": marketing_campaign_ready(slug),
    }
    complete = sum(stage_done.values())
    # Compact progress bar + next step indicator
    _pc, _nc = st.columns([4, 1])
    with _pc:
        st.progress(complete / len(BUILD_STAGES), text=f"{complete} of {len(BUILD_STAGES)} steps complete")
    with _nc:
        next_label = "Tracker" if next_stage == "tracker" else dict(BUILD_STAGES)[next_stage]
        if st.button(f"→ {next_label}", type="primary", use_container_width=True, key=f"sf_continue_{slug}"):
            if next_stage == "tracker":
                st.session_state.view = "tracker"
                qp_update(view="tracker", tab=None)
            else:
                st.session_state[requested_key] = next_stage
                st.session_state.build_tab = next_stage
                qp_update(active_book=slug, view="build", tab=next_stage)
            safe_rerun()

    # Tab labels with status indicators
    def _tab_label(key: str) -> str:
        label = dict(BUILD_STAGES)[key].split("  ", 1)[-1]
        if stage_done.get(key):
            return f"✓ {label}"
        if key == next_stage:
            return f"→ {label}"
        return label

    stage_keys = [key for key, _label in BUILD_STAGES]
    tab_labels = [_tab_label(k) for k in stage_keys]
    tabs = st.tabs(tab_labels)
    # Determine which tab to show
    current_stage = normalize_build_stage(st.session_state.get(stage_key, "icons"))
    current_idx = stage_keys.index(current_stage) if current_stage in stage_keys else 0

    # Render each tab
    for idx, (tab, stage) in enumerate(zip(tabs, stage_keys)):
        with tab:
            if st.session_state.get("build_tab") != stage:
                st.session_state.build_tab = stage
                st.session_state[stage_key] = stage
                qp_update(active_book=slug, view="build", tab=stage)
            if book_vocab_review_required(slug) and stage not in {"setup", "content"}:
                st.warning("Complete the Content review first.")
                if st.button("Go to Content review →", type="primary", key=f"locked_to_content_{slug}"):
                    st.session_state[requested_key] = "content"
                    st.session_state[stage_key] = "content"
                    qp_update(tab="content")
                    safe_rerun()
                continue
            if stage == "setup":
                render_setup_stage(slug, display_name)
            elif stage == "content":
                render_content_review_stage(slug, display_name)
            elif stage == "icons":
                render_icons_tab(slug, display_name)
            elif stage == "boardready":
                render_boardready_stage(slug, display_name)
            elif stage == "qa":
                render_qa_tab(slug, display_name)
            elif stage == "build":
                render_build_tab(slug, display_name)
            elif stage == "dignity":
                render_dignity_stage(slug, display_name)
            elif stage == "listing":
                render_listing_tab(slug, display_name)
            else:
                render_promote_stage(slug, display_name)


def render_top_bar(display_map: dict, active_slug: str | None) -> str | None:
    prefs = st.session_state.get("sf_ui_prefs", {})
    readable_width = 800 if prefs.get("readable_width") else 1180
    large_text_px = "18px" if prefs.get("large_text") else "16px"
    hc = bool(prefs.get("high_contrast"))
    topbar_bg = "#1E3A5F"
    dim = "0.35" if st.session_state.get("sf_tools_open") else "1.0"
    css = f"""
        <style>
        :root {{
            --brd-radius: 6px;
            --brd-color: #DDDDDD;
            --brd-color-strong: #BBBBBB;
            --space-1: 4px;
            --space-2: 8px;
            --space-3: 12px;
            --space-4: 16px;
            --row-tint-core: #EBF5FF;
            --row-tint-book: #FFFDE7;
            --aac-yes: #4CAF50;
            --aac-no: #F44336;
        }}
        .sf-shell {{background:#F3F3F3; padding:0;}}
        .sf-topbar-accent {{height:6px; background:{topbar_bg}; border-radius:6px 6px 0 0; margin-bottom:10px;}}
        .sf-topbar-divider {{height:1px; background:#D8E0E5; margin:8px 0 14px;}}
        .sf-brand {{font-weight:800; color:#0D2545; font-size:24px; letter-spacing:0.2px; margin-top:8px;}}
        .sf-logo img {{display:block;}}
        .sf-content {{max-width:{readable_width}px; margin:8px auto 16px auto; opacity:{dim}; transition:opacity 120ms ease;}}
        html, body, [data-testid="stAppViewContainer"] * {{font-size:{large_text_px};}}
        .sf-tools-btn {{opacity:1;}}
        @media (max-width: 900px) {{
            .sf-brand {{font-size:20px;}}
            .sf-content {{margin-top:4px; padding:0 8px;}}
        }}
        </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    chosen_slug_val = active_slug
    with st.container():
        st.markdown('<div class="sf-topbar-accent"></div>', unsafe_allow_html=True)
        cols = st.columns([1.5, 4.5, 4])
        with cols[0]:
            logo_path = project_root() / "assets" / "branding" / "logos" / "small_wins_logo_with_text.png"
            lc1, lc2 = st.columns([1, 2])
            with lc1:
                if logo_path.exists():
                    st.markdown('<div class="sf-logo">', unsafe_allow_html=True)
                    st.image(str(logo_path), width=120)
                    st.markdown('</div>', unsafe_allow_html=True)
            with lc2:
                st.markdown('<div class="sf-brand">StudioForge</div>', unsafe_allow_html=True)
        with cols[1]:
            # Quick UI toggles row (synced with Settings  UI preferences)
            try:
                ensure_global_prefs()
            except Exception:
                pass
            _prefs = dict(st.session_state.get("sf_ui_prefs", {}))
            # toggles moved to right column to reduce crowding
            st.empty()
            options = [display_map[s] for s in display_map.keys()]
            if not options:
                st.selectbox("Working on:", options=["No themes found"], index=0, disabled=True)
            else:
                labels = {display_map[s]: s for s in display_map.keys()}
                current_label = display_map.get(active_slug) if active_slug in display_map else options[0]
                chosen = st.selectbox("Working on:", options=options, index=options.index(current_label))
                chosen_slug_val = labels[chosen]
        with cols[2]:
            # Right rail: nav + AI + Tools (left) and compact vertical UI toggles (right)
            ncol = st.container()
            with ncol:
                ai_on = (anthropic is not None) and bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())

                # Primary nav
                nav1, nav2, nav3 = st.columns(3)
                with nav1:
                    if st.button("Home", key="sf_nav_today", use_container_width=True):
                        st.session_state.view = "today"
                        qp_update(view="today")
                        safe_rerun()
                with nav2:
                    if st.button("Continue", type="primary", key="sf_nav_build", use_container_width=True) and chosen_slug_val:
                        target = next_required_stage_for_slug(chosen_slug_val)
                        if target == "tracker":
                            st.session_state.view = "tracker"
                            qp_update(view="tracker")
                        else:
                            open_build_screen(chosen_slug_val, target)
                        safe_rerun()
                with nav3:
                    if st.button("Icons", key="sf_nav_icons", use_container_width=True) and chosen_slug_val:
                        open_build_screen(chosen_slug_val, "icons")
                        safe_rerun()
                def render_ai_badge(api_key_present: bool) -> str:
                    if api_key_present:
                        return """<a href=\"?tools=1\" style=\"text-decoration:none;\"><span style="
                background: #EEFFEE; color: #2D8A00;
                font-size: 11px; font-weight: 500;
                padding: 3px 10px; border-radius: 20px;
                border: 1px solid #2D8A00;
                cursor: pointer;" title="Click to open AI settings">
                AI: Ready
            </span></a>"""
                    return """<a href=\"?tools=1\" style=\"text-decoration:none;\"><span style="
                background: #FAEEDA; color: #E07B00;
                font-size: 11px; font-weight: 500;
                padding: 3px 10px; border-radius: 20px;
                border: 1px solid #E07B00;
                cursor: pointer;" title="Click to set up API key">
                AI: Off
            </span></a>"""

                tracker_col, settings_col = st.columns(2)
                with tracker_col:
                    if st.button("Tracker", key="sf_nav_tracker", use_container_width=True):
                        st.session_state.view = "tracker"
                        qp_update(view="tracker")
                        safe_rerun()
                with settings_col:
                    if st.button("Settings", key="sf_open_tools", use_container_width=True):
                        st.session_state.sf_tools_open = True
                        qp_update(tools="1")
            st.markdown('<div class="sf-topbar-divider"></div>', unsafe_allow_html=True)
    return chosen_slug_val


# ---------------------------------------------------------------------------
# Grouped left navigation (ported from the retired Tool Launcher's NAV_GROUPS).
# Maps StudioForge views + build stages into the same wayfinding groups Fiona
# already knows: Start / Set up / Build assets / Review / Generate / Finish.
# Renders into st.sidebar ONLY when the Tools drawer is closed (the drawer
# reuses the sidebar when open).
# ---------------------------------------------------------------------------
NAV_GROUPS_SF = [
    ("Start", [
        ("Today", "today"),
        ("New Topic", "new_topic"),
    ]),
    ("Set up", [
        ("Setup", "build:setup"),
        ("Content", "build:content"),
    ]),
    ("Build assets", [
        ("Icons", "build:icons"),
        ("BoardReady", "build:boardready"),
    ]),
    ("Review", [
        ("Visual QA", "build:qa"),
        ("Tracker", "tracker"),
    ]),
    ("Generate", [
        ("Activities", "build:build"),
        ("Dignity", "build:dignity"),
    ]),
    ("Finish & publish", [
        ("Listing", "build:listing"),
        ("Promote", "build:promote"),
        ("Tools", "tools"),
    ]),
]

# "New" badges fade out NEW_WINDOW_DAYS after the added date.
NAV_NEW_WINDOW_DAYS = 45
NAV_ADDED_DATES = {
    "Dignity": "2026-09-01",
    "New Topic": "2026-08-15",
    "Promote": "2026-09-05",
}

# Seed last-used timestamps from the retired Tool Launcher's log so the new
# sidebar starts populated rather than empty.
_NAV_LOG_PATH = project_root() / "Studioforge" / "_tool_launcher_log.json"
_NAV_LOG_KEY_MAP = {
    "Icons": "icon_labeler",
    "BoardReady": "board_ready",
    "Activities": "matching",
    "Listing": "listing_generator",
}


def _nav_is_new(label: str) -> bool:
    try:
        added = NAV_ADDED_DATES.get(label)
        if not added:
            return False
        from datetime import date, timedelta
        d = date.fromisoformat(added)
        return (date.today() - d).days <= NAV_NEW_WINDOW_DAYS
    except Exception:
        return False


def _nav_last_used(label: str) -> str:
    try:
        if _NAV_LOG_PATH.exists():
            data = json.loads(_NAV_LOG_PATH.read_text(encoding="utf-8"))
            key = _NAV_LOG_KEY_MAP.get(label)
            if key and data.get(key):
                ts = str(data[key])[:16].replace("T", " ")
                return f"Last used: {ts}"
    except Exception:
        pass
    return ""


def _nav_active_key() -> str | None:
    """Return the nav key that is currently active, or None."""
    try:
        view = st.session_state.get("view", "today")
        if view == "tracker":
            return "tracker"
        if view == "today":
            return "new_topic" if st.session_state.get("sf_nav_new_topic") else "today"
        if view == "build":
            stage = normalize_build_stage(st.session_state.get("build_tab", "setup"))
            return f"build:{stage}"
    except Exception:
        pass
    return None


def render_nav_sidebar():
    """Grouped left navigation in st.sidebar (shown only when Tools drawer is closed)."""
    if st.session_state.get("sf_tools_open"):
        return  # Tools drawer owns the sidebar
    active = _nav_active_key()
    slug = st.session_state.get("active_book")
    with st.sidebar:
        try:
            st.markdown("#### StudioForge")
        except Exception:
            pass
        for grp, items in NAV_GROUPS_SF:
            try:
                st.caption(grp.upper())
            except Exception:
                pass
            for label, key in items:
                try:
                    is_active = (key == active)
                    needs_book = key.startswith("build:") or key == "new_topic"
                    disabled = needs_book and not slug
                    badge = "  · New" if _nav_is_new(label) else ""
                    marker = "▸ " if is_active else "   "
                    btn_label = f"{marker}{label}{badge}"
                    if st.button(btn_label, key=f"sf_nav_{key}", use_container_width=True, disabled=disabled):
                        if key == "today":
                            st.session_state.view = "today"
                            st.session_state.sf_nav_new_topic = False
                            qp_update(view="today", tab=None)
                        elif key == "tracker":
                            st.session_state.view = "tracker"
                            qp_update(view="tracker", tab=None)
                        elif key == "tools":
                            st.session_state.sf_tools_open = True
                            qp_update(tools="1")
                        elif key == "new_topic":
                            st.session_state.view = "today"
                            st.session_state.sf_nav_new_topic = True
                            qp_update(view="today", tab=None)
                        elif key.startswith("build:") and slug:
                            stage = key.split(":", 1)[1]
                            open_build_screen(slug, stage)
                        safe_rerun()
                    lu = _nav_last_used(label)
                    if lu and not is_active:
                        try:
                            st.caption(lu)
                        except Exception:
                            pass
                except Exception:
                    pass
        try:
            st.divider()
            if slug:
                st.caption(f"Working on: {decode_slug(slug)}")
            else:
                st.caption("Pick a book from the top bar to enable build stages.")
        except Exception:
            pass


def main():
    st.set_page_config(page_title="StudioForge", layout="wide")
    drawer_css = (
        """
/* Backdrop */
.sf-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 998; }
/* Style Streamlit sidebar as a right-hand overlay drawer */
[data-testid="stSidebar"] { position: fixed !important; right: 0; top: 0; bottom: 0; width: 520px !important; max-width: 92vw !important; z-index: 999 !important; box-shadow: -8px 0 24px rgba(0,0,0,0.2); border-left: 1px solid #E0E0E0; }
[data-testid="stSidebar"] > div { padding-top: 10px !important; }
/* Hide Streamlit's collapse control (drawer should close via Close button / backdrop / Esc) */
button[kind="header"] { display: none !important; }
/* â”€â”€ TOOLS DRAWER SHELL â”€â”€ */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 0.5px solid #E0E0E0 !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.12) !important;
}
section[data-testid="stSidebar"] > div { padding-top: 0 !important; }
/* Drawer header â€” navy bar at top of sidebar */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2:first-of-type {
    background: #1E3A5F !important;
    color: white !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    margin: 0 -1rem 1rem -1rem !important;
    padding: 16px 20px !important;
    border-radius: 0 !important;
}
/* Tool nav radio items */
section[data-testid="stSidebar"] .stRadio label {
    display: block !important;
    padding: 10px 16px !important;
    font-size: 13px !important;
    color: #595959 !important;
    border-left: 3px solid transparent !important;
    cursor: pointer !important;
    transition: all 150ms ease !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: #E8F8F8 !important;
    color: #006379 !important;
    border-left-color: #006379 !important;
}
/* Active tool nav item */
section[data-testid="stSidebar"] .stRadio [aria-checked="true"] + label,
section[data-testid="stSidebar"] .stRadio input:checked + label {
    background: #E8F8F8 !important;
    color: #006379 !important;
    font-weight: 500 !important;
    border-left: 3px solid #006379 !important;
}
/* Section dividers inside drawer */
section[data-testid="stSidebar"] hr {
    border-top: 0.5px solid #E0E0E0 !important;
    margin: 0.75rem 0 !important;
}
/* Expander headers inside drawer */
section[data-testid="stSidebar"] .streamlit-expanderHeader {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #1A1A1A !important;
    background: #F3F3F3 !important;
    border-radius: 6px !important;
    padding: 8px 12px !important;
}
section[data-testid="stSidebar"] [data-testid="stToggle"] label {
    font-size: 12px !important;
    line-height: 1.1 !important;
    white-space: normal !important;
}
        """
        if st.session_state.get("sf_tools_open")
        else ""
    )
    # UI preference CSS (readable width, large text, high contrast)
    prefs = st.session_state.get("sf_ui_prefs", {})
    ui_parts = []
    if prefs.get("readable_width", False):
        ui_parts.append(
            """
.sf-content { max-width: 800px; margin-left: auto; margin-right: auto; }
"""
        )
    if prefs.get("large_text", False):
        ui_parts.append(
            """
.sf-content { font-size: 1.08em; }
"""
        )
    if prefs.get("high_contrast", False):
        ui_parts.append(
            """
/* High contrast mode */
.sf-content, body { color: #0A0A0A !important; }
.stApp { background: #FFFFFF !important; }
hr { border-top: 1.2px solid #000 !important; }
section[data-testid="stSidebar"] .streamlit-expanderHeader { background: #E0F7FF !important; color: #003344 !important; }
"""
        )
    ui_css = "\n".join(ui_parts)

    css_block = """
<style>

/* â”€â”€ HIDE STREAMLIT DEFAULT HEADER / TOOLBAR (use custom top bar) â”€â”€ */
header[data-testid="stHeader"] { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }


/* â”€â”€ TOP BAR â”€â”€ */
header[data-testid="stHeader"] {
    background-color: #1E3A5F !important;
    height: 56px !important;
}
header[data-testid="stHeader"] * {
    color: white !important;
}
/* Hide default Streamlit deploy button area styling */
.stDeployButton { display: none; }

/* â”€â”€ PAGE BACKGROUND â”€â”€ */
.stApp {
    background-color: #F3F3F3 !important;
}
.main .block-container {
    padding-top: 0.75rem;
    padding-bottom: 2rem;
    max-width: 1280px;
}

/* â”€â”€ CARDS â€” white surfaces on grey background â”€â”€ */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
    background: #FFFFFF;
    border-radius: 12px;
    border: 0.5px solid #E0E0E0;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

/* â”€â”€ HEADINGS â”€â”€ */
h1 { font-size: 30px !important; line-height: 1.2 !important; font-weight: 750 !important; color: #0D2545 !important; }
h2 { font-size: 24px !important; line-height: 1.25 !important; font-weight: 700 !important; color: #0D2545 !important; }
h3 { font-size: 19px !important; line-height: 1.3 !important; font-weight: 650 !important; color: #163A59 !important; }

/* â”€â”€ PRIMARY BUTTONS â”€â”€ */
.stButton > button {
    background-color: #FFFFFF !important;
    color: #0D2545 !important;
    border: 1px solid #AFC4C7 !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    min-height: 42px !important;
    padding: 0.5rem 0.85rem !important;
    white-space: nowrap !important;
    transition: background 150ms ease, border-color 150ms ease !important;
}
.stButton > button:hover {
    background-color: #E8F5F4 !important;
    border-color: #31A8A0 !important;
}
.stButton > button[kind="primary"] {
    background-color: #006379 !important;
    color: #FFFFFF !important;
    border-color: #006379 !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #005268 !important;
    border-color: #005268 !important;
}
.stButton > button:disabled {
    background-color: #F2F4F5 !important;
    color: #879398 !important;
    border-color: #D9E0E2 !important;
}

/* â”€â”€ SELECTBOX (book selector) â”€â”€ */
div[data-testid="stSelectbox"] > div {
    border: 1px solid #CCCCCC !important;
    border-radius: 6px !important;
}
div[data-testid="stSelectbox"] > div:focus-within {
    border-color: #006379 !important;
    box-shadow: 0 0 0 3px rgba(0,99,121,0.15) !important;
}

/* â”€â”€ METRIC / STATUS BADGES â”€â”€ */
div[data-testid="stMetric"] {
    background: #F3F3F3 !important;
    border-radius: 8px !important;
    padding: 12px !important;
}

/* â”€â”€ TABS â”€â”€ */
.stTabs [data-baseweb="tab-list"] {
    background: white !important;
    border-bottom: 1px solid #E0E0E0 !important;
    gap: 6px !important;
    overflow-x: auto !important;
}
.stTabs [data-baseweb="tab"] {
    min-width: 128px !important;
    height: 48px !important;
    color: #425466 !important;
    font-weight: 600 !important;
    border-bottom: 3px solid transparent !important;
    padding: 0 18px !important;
    white-space: nowrap !important;
    justify-content: center !important;
}
.stTabs [aria-selected="true"] {
    color: #006379 !important;
    font-weight: 500 !important;
    border-bottom: 2px solid #006379 !important;
    background: white !important;
}

/* â”€â”€ SIDEBAR / TOOLS DRAWER â”€â”€ */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 0.5px solid #E0E0E0 !important;
}
section[data-testid="stSidebar"] h2 {
    color: #1E3A5F !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 8px 0 4px !important;
    border-bottom: 0.5px solid #E0E0E0 !important;
    margin-bottom: 8px !important;
}

/* â”€â”€ GROUPED NAV SIDEBAR (ported from Tool Launcher) â”€â”€ */
/* Only applies when Tools drawer is closed; drawer CSS overrides when open */
section[data-testid="stSidebar"] .stButton > button {
    text-align: left !important;
    justify-content: flex-start !important;
    background-color: transparent !important;
    border: 0 !important;
    border-left: 3px solid transparent !important;
    border-radius: 0 !important;
    color: #0D2545 !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    min-height: 36px !important;
    padding: 4px 10px !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #E6FFFB !important;
    border-left-color: #31A8A0 !important;
}
/* Group headers (st.caption rendered as small uppercase labels) */
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.6px !important;
    color: #64748B !important;
    text-transform: uppercase !important;
    padding: 10px 10px 2px !important;
}

{drawer_css}
{ui_css}

/* â”€â”€ PROGRESS BARS â”€â”€ */
div[data-testid="stProgressBar"] > div {
    background-color: #006379 !important;
    border-radius: 4px !important;
}
div[data-testid="stProgressBar"] {
    background-color: #E0E0E0 !important;
    border-radius: 4px !important;
    height: 6px !important;
}

/* â”€â”€ DIVIDERS â”€â”€ */
hr {
    border: none !important;
    border-top: 0.5px solid #E0E0E0 !important;
    margin: 1rem 0 !important;
}

</style>
"""
    st.markdown(css_block.replace("{drawer_css}", drawer_css).replace("{ui_css}", ui_css), unsafe_allow_html=True)
    # Phase 9 — Encoding cleanup: client-side fix for common mojibake sequences
    try:
        components.html(
            """
            <script>
            (function(){
              try {
                const repl = {
                  'â€”':'—','Â·':'·','â€¦':'…','â€“':'–','â€‘':'‑','Ã—':'×','â€˜':'‘','â€™':'’','â€œ':'“','â€�':'”',
                  'âœ“':'✓','âœ•':'✕','âœ…':'✅','â—‹':'○','â—':'◐','â—':'●','â¸':'⏸','â³':'⏳','â–¶':'▶','â—€':'◀',
                  'â„¹':'ℹ','âš ':'⚠','â˜€ï¸':'☀️','â„ï¸':'❄️','ðŸŒ±':'🌱','ðŸ‚':'🍂','ðŸ“Œ':'📌','ðŸ“‚':'📂','ðŸ’¾':'💾','ðŸ—‘':'🗑',
                  'ðŸ”':'🔁','ðŸ—‚ï¸':'🗂️','ðŸ§ª':'🧪','ðŸ“¦':'📦','âœ•':'✖','âœŽ':'✎','â‹¯':'⋯',
                  '6Ã—6':'6×6','4Ã—4':'4×4','8Ã—':'8×','20Ã—':'20×'
                };
                function fixNode(node){
                  if(node.nodeType===Node.TEXT_NODE){
                    let t=node.nodeValue;
                    let changed=false;
                    for(const k in repl){ if(t.indexOf(k)!==-1){ t=t.split(k).join(repl[k]); changed=true; } }
                    if(changed) node.nodeValue=t;
                  } else if(node.childNodes) {
                    node.childNodes.forEach(fixNode);
                  }
                }
                function run(){ fixNode(document.body); }
                const mo = new MutationObserver((muts)=>{
                  for(const m of muts){
                    if(m.type==='characterData'){ fixNode(m.target); }
                    if(m.addedNodes){ m.addedNodes.forEach(fixNode); }
                  }
                });
                if(document.body){
                  run();
                  mo.observe(document.body,{subtree:true,childList:true,characterData:true});
                } else {
                  document.addEventListener('DOMContentLoaded', function(){ run(); mo.observe(document.body,{subtree:true,childList:true,characterData:true}); });
                }
              } catch(e) { /* no-op */ }
            })();
            </script>
            """,
            height=0,
        )
    except Exception:
        pass
    # Load persisted UI preferences and last tool
    try:
        ensure_global_prefs()
    except Exception:
        pass
    # Load optional environment variables (e.g., future AI providers); harmless if .env missing
    try:
        # Explicitly load .env from the project root to avoid CWD ambiguity
        load_dotenv(dotenv_path=str(project_root() / ".env"))
    except Exception:
        pass
    root = project_root()
    titles_map = load_theme_titles(root)
    slugs = discover_books()
    display_map = get_display_map(slugs, titles_map)

    qp_book = qp_get("active_book")
    qp_view = qp_get("view")
    qp_tab = qp_get("tab")
    qp_tools = qp_get("tools")
    if "active_book" not in st.session_state:
        pref_book = st.session_state.get("sf_last_book")
        st.session_state.active_book = (
            qp_book
            if (qp_book and qp_book in display_map)
            else (pref_book if (pref_book and pref_book in display_map) else (slugs[0] if slugs else None))
        )
        if st.session_state.active_book:
            qp_update(active_book=st.session_state.active_book)
            show_toast("info", f"Restored last book: {display_map.get(st.session_state.active_book, '')}")
            st.session_state.sf_last_book = st.session_state.active_book
            try:
                persist_session_prefs()
            except Exception:
                pass
            # Hydrate persisted state for initial book
            hydrate_book_session_from_state(st.session_state.active_book)
    # View routing (today/build/tracker)
    if "view" not in st.session_state:
        st.session_state.view = qp_view if qp_view in {"today", "build", "tracker"} else "today"
    if "build_tab" not in st.session_state:
        st.session_state.build_tab = qp_tab if qp_tab in BUILD_STAGE_KEYS else "setup"
    # Tools drawer auto-open via query param
    if qp_tools and str(qp_tools).lower() in {"1", "true", "yes"}:
        st.session_state.sf_tools_open = True
    if qp_tools and str(qp_tools).lower() in {"0", "false", "no"}:
        st.session_state.sf_tools_open = False

    prev_book = st.session_state.get("active_book")
    chosen_slug = render_top_bar(display_map, prev_book)
    if chosen_slug and chosen_slug != prev_book:
        if prev_book:
            flush_current_book_state(prev_book)
        st.session_state.active_book = chosen_slug
        qp_update(active_book=chosen_slug)
        st.session_state.sf_last_book = chosen_slug
        try:
            persist_session_prefs()
        except Exception:
            pass
        hydrate_book_session_from_state(chosen_slug)
        show_toast("success", f"Working on: {display_map.get(chosen_slug, '')}")

    st.markdown('<div class="sf-content">', unsafe_allow_html=True)
    if not slugs:
        st.warning("No themes found. Set your Themes root in Settings later.")
    else:
        if st.session_state.view == "tracker":
            render_tracker_screen(display_map)
        elif st.session_state.view == "build" and st.session_state.active_book:
            render_build_screen(st.session_state.active_book, display_map.get(st.session_state.active_book, ""))
        else:
            # Today Screen — simplified: book name, icons, next steps
            active = st.session_state.active_book
            render_start_here(active, display_map.get(active, decode_slug(active)))
            # Optional sections collapsed at the bottom
            with st.expander("Switch book / recent projects", expanded=False):
                render_recent_books_chips(active, display_map)
            with st.expander("Detailed project status", expanded=False):
                render_status_card(active, display_map.get(active, decode_slug(active)))
            with st.expander("Focus priorities & planning", expanded=False):
                render_priorities_panel(display_map)
                planning_default = bool(st.session_state.get("sf_ui_prefs", {}).get("home_planning", False))
                planning_visible = st.toggle("Show future planning and new-project tools", value=planning_default, key="sf_home_planning")
                if planning_visible != planning_default:
                    st.session_state.sf_ui_prefs["home_planning"] = planning_visible
                    persist_session_prefs()
                if planning_visible:
                    render_new_topic_panel()
                    season = season_us(datetime.now())
                    c1, c2 = st.columns([3, 1])
                    with c2:
                        if st.button("Refresh picks"):
                            try:
                                _ = get_today_recommendations(display_map, season, force=True)
                            except Exception:
                                pass
                            safe_rerun()
                    recs = get_today_recommendations(display_map, season)
                    ai_on = (anthropic is not None) and bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
                    season_icon = {"Spring": "", "Summer": "", "Autumn": "", "Winter": ""}.get(season, "")
                    picks_label = f"{season} picks:" if season else "Picks:"
                    picks = " | ".join(recs)
                    st.markdown(
                        f"""
<div style="
    background: #FFF8E0;
    border: 1px solid #F5C518;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
    color: #595959;
    margin-bottom: 1rem;
">
    {season_icon} <strong style="color:#854F0B;">{picks_label}</strong>
    {picks}
</div>
""",
                        unsafe_allow_html=True,
                    )
                    if not ai_on:
                        try:
                            st.caption("AI off: showing seasonal picks. Add ANTHROPIC_API_KEY in Settings to enable intelligent recommendations.")
                        except Exception:
                            pass
    st.markdown('</div>', unsafe_allow_html=True)

    # Phase 1/7 â€” Tools drawer overlay (best-effort without pushing content)
    if st.session_state.get("sf_tools_open"):
        st.markdown(
            """
            <div class="sf-backdrop" onclick="(function(){try{const u=new URL(window.top.location.href);u.searchParams.set('tools','0');window.top.location.href=u.toString();}catch(e){}})()"></div>
            """,
            unsafe_allow_html=True,
        )
        components.html(
            """
            <script>
            (function(){
              function closeTools(){
                try{
                  const url = new URL(window.top.location.href);
                  url.searchParams.set('tools','0');
                  window.top.location.href = url.toString();
                }catch(e){ /* no-op */ }
              }
              document.addEventListener('keydown', function(e){ if(e.key==='Escape'){ closeTools(); }});
            })();
            </script>
            """,
            height=0,
        )
    def ensure_ui_prefs():
        if "sf_ui_prefs" not in st.session_state:
            st.session_state.sf_ui_prefs = {
                "readable_width": False,
                "large_text": False,
                "high_contrast": False,
                "show_tips": True,
            }

    def render_tool_settings():
        root_local = project_root()
        st.markdown("## Settings")

        with st.expander("Book title overrides", expanded=False):
            titles = load_theme_titles(root_local)
            slugs_local = discover_books()
            edited: dict[str, str] = {}
            cols = st.columns(2)
            with cols[0]:
                st.caption("Slug")
            with cols[1]:
                st.caption("Display name")
            for s in slugs_local:
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.text_input("slug", s, key=f"ttl_slug_{s}", disabled=True)
                with c2:
                    edited[s] = st.text_input(
                        f"name_{s}",
                        value=titles.get(s) or decode_slug(s),
                        key=f"ttl_name_{s}",
                    )
            if st.button("Save titles"):
                compact = {s: v for s, v in edited.items() if v and v != decode_slug(s)}
                write_theme_titles(root_local, compact)
                safe_rerun()

        with st.expander("Themes root folder", expanded=False):
            current_root = os.environ.get("SF_THEMES_ROOT", str(project_root() / "assets" / "themes"))
            new_root = st.text_input("Path to themes root", value=current_root, key="sf_themes_root")
            if st.button("Save themes root"):
                if new_root and Path(new_root).exists():
                    os.environ["SF_THEMES_ROOT"] = new_root
                    show_toast("success", "Themes root updated. Rescanning books...")
                    safe_rerun()
                else:
                    show_toast("warning", "Path does not exist.")

        with st.expander("Symbols folder", expanded=False):
            current_symbols = os.environ.get("SF_SYMBOLS_ROOT", str(project_root() / "assets" / "symbols"))
            new_symbols = st.text_input("Path to symbols folder", value=current_symbols, key="sf_symbols_root")
            if st.button("Save symbols folder"):
                if new_symbols and Path(new_symbols).exists():
                    os.environ["SF_SYMBOLS_ROOT"] = new_symbols
                    show_toast("success", "Symbols folder updated.")
                    safe_rerun()
                else:
                    show_toast("warning", "Path does not exist.")

        with st.expander("AI / API diagnostics", expanded=True):
            env_path = project_root() / ".env"
            key_raw = os.environ.get("ANTHROPIC_API_KEY", "").strip()
            masked = (f"{key_raw[:6]}...{key_raw[-4:]}" if len(key_raw) >= 10 else ("(set)" if key_raw else "(empty)"))
            ai_pkg = (anthropic is not None)
            ai_on_flag = ai_pkg and bool(key_raw)
            cols_ai = st.columns([2, 2, 2])
            with cols_ai[0]:
                st.caption(f".env at project root: {'found' if env_path.exists() else 'missing'}")
            with cols_ai[1]:
                st.caption(f"Anthropic package: {'installed' if ai_pkg else 'not installed'}")
            with cols_ai[2]:
                st.caption(f"Computed status: {'AI: Ready' if ai_on_flag else 'AI: Off'}")
            st.caption(f"ANTHROPIC_API_KEY: {masked}")
            if st.button("Reload .env", key="sf_reload_env"):
                try:
                    load_dotenv(dotenv_path=str(env_path), override=True)
                    show_toast("success", ".env reloaded")
                except Exception:
                    show_toast("warning", "Failed to reload .env")
                safe_rerun()

        with st.expander("UI preferences", expanded=False):
            try:
                ensure_global_prefs()
            except Exception:
                pass
            prefs = st.session_state.get("sf_ui_prefs", {})
            c1, c2 = st.columns(2)
            with c1:
                prefs["readable_width"] = st.toggle("Readable width", value=prefs.get("readable_width", False))
                prefs["high_contrast"] = st.toggle("High contrast", value=prefs.get("high_contrast", False))
            with c2:
                prefs["large_text"] = st.toggle("Large text", value=prefs.get("large_text", False))
                prefs["show_tips"] = st.toggle("Show tips", value=prefs.get("show_tips", True))
            st.session_state.sf_ui_prefs = prefs
            try:
                persist_session_prefs()
            except Exception:
                pass

        with st.expander("About", expanded=False):
            st.markdown("""**StudioForge** - Small Wins Studio  
April 2026""")

            st.markdown("#### Exports & audits")
            ec1, ec2, ec3 = st.columns([1, 1, 1])
            with ec1:
                if st.button("Export P1 audit CSV", key="exp_p1_csv"):
                    p = root_local / "tools" / "export_missing_icons_p1.py"
                    if p.exists():
                        subprocess.run([sys.executable, str(p)], capture_output=True, text=True)
                        show_toast("success", "P1 audit exported")
            with ec2:
                if st.button("Export P2 audit CSV", key="exp_p2_csv"):
                    p = root_local / "tools" / "export_missing_icons_p2.py"
                    if p.exists():
                        subprocess.run([sys.executable, str(p)], capture_output=True, text=True)
                        show_toast("success", "P2 audit exported")
            with ec3:
                if st.button("Export vocab CSV", key="exp_vocab_csv"):
                    p = root_local / "tools" / "export_book_vocab.py"
                    if p.exists():
                        subprocess.run([sys.executable, str(p)], capture_output=True, text=True)
                        show_toast("success", "Vocab CSV exported")

            p1_csv = root_local / "output" / "qa_audit" / "p1_missing.csv"
            p2_csv = root_local / "output" / "qa_audit" / "p2_missing.csv"
            vocab_csv = root_local / "exports" / "book_vocab_flat.csv"
            dc1, dc2, dc3, dc4 = st.columns([1, 1, 1, 1])
            with dc1:
                if p1_csv.exists():
                    st.download_button("Download P1 CSV", data=p1_csv.read_bytes(), file_name="p1_missing.csv", mime="text/csv")
            with dc2:
                if p2_csv.exists():
                    st.download_button("Download P2 CSV", data=p2_csv.read_bytes(), file_name="p2_missing.csv", mime="text/csv")
            with dc3:
                if vocab_csv.exists():
                    st.download_button("Download vocab CSV", data=vocab_csv.read_bytes(), file_name="book_vocab_flat.csv", mime="text/csv")
            with dc4:
                if st.button("Open audits folder", key="open_aud_folder"):
                    d = root_local / "output" / "qa_audit"
                    open_folder(d)

            st.markdown("#### Progress report")
            active_slug = st.session_state.get("active_book")

        def _build_report_for_slug(slug: str) -> str:
            try:
                title = decode_slug(slug)
                built = detect_built_products(slug)
                listing = read_listing_status(slug)
                rootp = project_root()
                vocab_p = rootp / "BoardReady" / "boardready" / "vocab" / "book_vocab.json"
                words: list[str] = []
                if vocab_p.exists():
                    data = json.loads(vocab_p.read_text(encoding="utf-8"))
                    rec = data.get(slug) or {}
                    arr = rec.get("activity_images") or []
                    words = [str(w).strip() for w in arr if str(w).strip()]
                dest_dir = images_dir_for_book(slug) or Path("")
                have: set[str] = set()
                if dest_dir.exists():
                    for p in dest_dir.glob("*.png"):
                        have.add(p.stem.lower())
                missing = [w for w in words if sanitise_symbol_name(w) not in have]
                use_ai = (anthropic is not None) and bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
                lines = []
                lines.append(f"# Progress - {title} ({slug})")
                lines.append("")
                lines.append(f"AI: {'Ready' if use_ai else 'Off'}")
                lines.append("")
                lines.append("## Icons")
                lines.append(f"Have: {len(words) - len(missing)} / {len(words)}")
                if missing:
                    lines.append("Missing: " + ", ".join(missing))
                lines.append("")
                lines.append("## Built products")
                for k, v in built.items():
                    lines.append(f"- {'OK' if v else '-'} {k}")
                lines.append("")
                lines.append(f"## Listing: {listing}")
                return "\n".join(lines)
            except Exception as e:
                return f"# Progress - {slug}\nError building report: {e}"

        pr1, pr2 = st.columns([1, 1])
        with pr1:
            if active_slug:
                content = _build_report_for_slug(active_slug)
                st.download_button(
                    "Download active book report",
                    data=content.encode("utf-8"),
                    file_name=f"{active_slug}_progress.md",
                    mime="text/markdown",
                )
        with pr2:
            try:
                prio = read_build_priorities(project_root())
                all_slugs = list((prio.get("P1") or []) + (prio.get("P2") or []))
                if all_slugs:
                    parts = [
                        "# Priorities Progress",
                        "",
                        f"Updated: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                        "",
                    ]
                    for s in all_slugs:
                        parts.append(_build_report_for_slug(s))
                        parts.append("")
                    blob = "\n".join(parts)
                    st.download_button(
                        "Download P1/P2 report",
                        data=blob.encode("utf-8"),
                        file_name="priorities_progress.md",
                        mime="text/markdown",
                    )
            except Exception:
                pass

        

    def symbols_dir() -> Path:
        env = os.environ.get("SF_SYMBOLS_ROOT", "").strip()
        if env and Path(env).exists():
            return Path(env)
        expanded = project_root() / "assets" / "symbols" / "png"
        if expanded.exists():
            return expanded
        return project_root() / "assets" / "symbols"

    def render_tool_symbol_library():
        st.subheader("Symbol Library")
        sym_root = symbols_dir()
        if not sym_root.exists():
            st.info("No symbols found. Set your Symbols folder in Settings or use the PDF Extractor.")
            return

        st.caption(f"Library: {sym_root}")

        scope = st.selectbox(
            "Browse",
            options=["All", "Alpha (A-Z)", "Categories"],
            index=0,
            key="symlib_scope",
        )

        browse_root = sym_root
        if scope == "Alpha (A-Z)" and (sym_root / "Alpha").exists():
            alpha_root = sym_root / "Alpha"
            letter = st.selectbox(
                "Letter",
                options=["#"] + [chr(c) for c in range(ord("a"), ord("z") + 1)],
                index=1,
                key="symlib_alpha_letter",
            )
            browse_root = alpha_root / str(letter).lower()
        elif scope == "Categories" and (sym_root / "Categories").exists():
            cat_root = sym_root / "Categories"
            top = [p.name for p in cat_root.iterdir() if p.is_dir()]
            top = sorted(top, key=lambda s: s.lower())
            top_choice = st.selectbox("Category group", options=top or ["(none)"], key="symlib_cat_top")
            browse_root = cat_root / top_choice if top_choice and top_choice != "(none)" else cat_root
            if browse_root.exists():
                subs = [p.name for p in browse_root.iterdir() if p.is_dir()]
                subs = sorted(subs, key=lambda s: s.lower())
                if subs:
                    sub_choice = st.selectbox("Subcategory", options=["(all)"] + subs, key="symlib_cat_sub")
                    if sub_choice and sub_choice != "(all)":
                        browse_root = browse_root / sub_choice
        active = st.session_state.get("active_book")
        if active:
            try:
                vocab_p = project_root() / "BoardReady" / "boardready" / "vocab" / "book_vocab.json"
                words = []
                if vocab_p.exists():
                    data = json.loads(vocab_p.read_text(encoding="utf-8"))
                    rec = data.get(active) or {}
                    arr = rec.get("activity_images") or []
                    words = [str(w).strip() for w in arr if str(w).strip()]
                    ctx_map = rec.get("word_context") or {}
                if words:
                    # Derive missing list vs what's already in the book's activity_images folder
                    dest_dir = images_dir_for_book(active)
                    have_stems: set[str] = set()
                    if dest_dir and dest_dir.parent.exists():
                        try:
                            for q in (dest_dir.glob("*.png") if dest_dir.exists() else []):
                                have_stems.add(Path(q).stem.lower())
                        except Exception:
                            pass
                    miss = [w for w in words if sanitise_symbol_name(w) not in have_stems]
                    filt_missing = st.checkbox("Show missing only", value=bool(miss), key="symlib_show_missing")
                    opts = (miss if filt_missing else words) or words
                    st.markdown(f"#### Needed for {decode_slug(active)}")
                    w1, w2 = st.columns([2, 1])
                    with w1:
                        st.selectbox("Target word", options=opts, key="symlib_target")
                    with w2:
                        if st.button("Search in library", key="symlib_find_target") and st.session_state.get("symlib_target"):
                            st.session_state.symlib_q = sanitise_symbol_name(st.session_state.symlib_target).replace("_", " ")
                            safe_rerun()
                    tgt = st.session_state.get("symlib_target")
                    if tgt and isinstance(ctx_map, dict) and ctx_map.get(tgt):
                        st.caption(f"Context: {ctx_map.get(tgt)}")
                    up_tgt = st.file_uploader("Upload icon for target", type=["png", "jpg", "jpeg", "webp"], key="symlib_up_target")
                    if up_tgt is not None and st.button("Add icon for target", key="symlib_add_target"):
                        try:
                            stem = sanitise_symbol_name(st.session_state.get("symlib_target") or Path(up_tgt.name).stem)
                            lib = symbols_dir() / f"{stem}.png"
                            lib.parent.mkdir(parents=True, exist_ok=True)
                            img = Image.open(io.BytesIO(up_tgt.read())).convert("RGBA")
                            img.save(str(lib))
                            dest_dir = images_dir_for_book(active)
                            if dest_dir:
                                dest_dir.mkdir(parents=True, exist_ok=True)
                                dest = dest_dir / lib.name
                                if not dest.exists():
                                    shutil.copy2(str(lib), str(dest))
                                ensure_kit(active)
                                kit_key = get_kit_key(active)
                                k = st.session_state.get(kit_key, [])
                                if str(dest) not in k:
                                    st.session_state[kit_key] = k + [str(dest)]
                                    persist_icons_hero(active, toast_ok=True)
                            else:
                                show_toast("info", "Saved to Symbol Library. Set Themes root in Settings to add to book kit.")
                            show_toast("success", "Icon added")
                            safe_rerun()
                        except Exception as e:
                            show_toast("error", f"Add failed: {e}")
            except Exception:
                pass
        query = st.text_input("Search symbols...", value=st.session_state.get("symlib_q", ""), key="symlib_q")

        with st.expander("Upload new icons to library"):
            ow = st.checkbox("Overwrite existing on name clash", value=False, key="symlib_ow")
            ups = st.file_uploader(
                "Upload PNG/JPG/WEBP files",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                key="symlib_new_multi",
            )
            if ups:
                added, replaced = 0, 0
                for f in ups:
                    try:
                        stem = sanitise_symbol_name(Path(f.name).stem)
                        target = sym_root / f"{stem}.png"
                        img = Image.open(io.BytesIO(f.read())).convert("RGBA")
                        if target.exists() and not ow:
                            base = stem
                            n = 2
                            while True:
                                cand = sym_root / f"{base}_{n}.png"
                                if not cand.exists():
                                    target = cand
                                    break
                                n += 1
                        elif target.exists() and ow:
                            replaced += 1
                        target.parent.mkdir(parents=True, exist_ok=True)
                        img.save(str(target))
                        added += 1
                    except Exception:
                        continue
                msg = f"Added {added} icon(s)"
                if replaced:
                    msg += f" - replaced {replaced}"
                show_toast("success", msg)
                safe_rerun()

        with st.expander("Library filters", expanded=False):
            fb1, fb2, fb3 = st.columns([1, 1, 1])
            with fb1:
                hide_blanks_lib = st.checkbox("Hide suspected blanks", value=True, key="symlib_hide_blanks")
            with fb2:
                symlib_white_cutoff = st.number_input("White cutoff", min_value=200, max_value=255, value=250, step=1, key="symlib_white_cutoff")
            with fb3:
                symlib_min_nonwhite = st.number_input("Min non-white", min_value=0.0, max_value=1.0, value=0.005, step=0.001, format="%.3f", key="symlib_min_nonwhite")
        # Deduplicate by stem so variants in subfolders don't repeat
        if browse_root.exists():
            all_files = [p for p in browse_root.rglob("*.png")]
        else:
            all_files = [p for p in sym_root.rglob("*.png")]
        by_stem: dict[str, Path] = {}
        for p in all_files:
            steme = p.stem.lower()
            if steme not in by_stem:
                by_stem[steme] = p
        files = list(by_stem.values())
        files.sort(key=lambda p: p.stem.lower())
        if query.strip():
            q = query.lower().strip()
            files = [p for p in files if q in p.stem.lower()]

        # Optional: blank detection helper
        def _is_blank_icon(pp: Path) -> bool:
            try:
                g = Image.open(str(pp)).convert("L")
                hist = g.histogram()
                total = g.width * g.height
                nonwhite = sum(hist[:int(st.session_state.get("symlib_white_cutoff", 250))])
                ratio = (nonwhite / total) if total else 0.0
                return ratio < float(st.session_state.get("symlib_min_nonwhite", 0.005))
            except Exception:
                return False
        # Build filtered list and page it
        filtered = [p for p in files if not _is_blank_icon(p)] if st.session_state.get("symlib_hide_blanks", True) else list(files)
        total = len(filtered)
        page_size = 80
        max_page = max(1, (total + page_size - 1) // page_size)
        cur_page = int(st.session_state.get("symlib_page", 1))
        cur_page = max(1, min(cur_page, max_page))
        start = (cur_page - 1) * page_size
        end = start + page_size
        page_files = filtered[start:end]

        pc1, pc2, pc3 = st.columns([1, 1, 2])
        with pc1:
            if st.button("< Prev", disabled=cur_page <= 1, key="symlib_prev"):
                st.session_state.symlib_page = cur_page - 1
                safe_rerun()
        with pc2:
            if st.button("Next >", disabled=cur_page >= max_page, key="symlib_next"):
                st.session_state.symlib_page = cur_page + 1
                safe_rerun()
        with pc3:
            st.caption(f"Page {cur_page}/{max_page} - {total} symbols")

        with st.expander("Normalize visible symbols", expanded=False):
            if st.button("Normalize this page", key="symlib_norm_page"):
                done = 0
                for p in page_files:
                    try:
                        if normalize_icon_file(p):
                            done += 1
                    except Exception:
                        pass
                show_toast("success", f"Normalized {done}/{len(page_files)} icons")
                safe_rerun()

        if not page_files:
            st.caption("No matching symbols.")
            return
        cols = st.columns(4)
        active_slug = st.session_state.get("active_book")
        for i, p in enumerate(page_files):
            with cols[i % 4]:
                try:
                    st.image(str(p), caption=p.stem.replace('_',' ')[:18], width=120)
                except Exception:
                    st.write(p.stem.replace('_',' '))
                # Inline rename/edit
                gi = start + i
                ed_key = f"sym_edit_{gi}"
                if st.session_state.get(ed_key):
                    new_name = st.text_input("Rename", value=p.stem, key=f"sym_edit_in_{gi}")
                    r1, r2 = st.columns([1, 1])
                    with r1:
                        if st.button("Save", key=f"sym_edit_sv_{gi}"):
                            try:
                                stem = sanitise_symbol_name(new_name)
                                target = p.with_name(f"{stem}.png")
                                if target.exists() and target != p:
                                    show_toast("warning", f"{target.name} already exists")
                                else:
                                    p.rename(target)
                                    show_toast("success", f"Renamed to {target.name}")
                                    st.session_state[ed_key] = False
                                    safe_rerun()
                            except Exception as e:
                                show_toast("error", f"Rename failed: {e}")
                    with r2:
                        if st.button("Cancel", key=f"sym_edit_ca_{gi}"):
                            st.session_state[ed_key] = False
                            safe_rerun()
                else:
                    if st.button("Rename", key=f"sym_rename_{gi}", help="Rename"):
                        st.session_state[ed_key] = True
                        safe_rerun()
                # Compact action: add to kit
                disabled = active_slug is None
                help_txt = None if active_slug else "Select a book first."
                if st.button("+ Kit", key=f"add_sym_{gi}", disabled=disabled, help=help_txt):
                        # Copy into the book's activity_images and add to kit
                        dest_dir = images_dir_for_book(active_slug) if active_slug else None
                        if not dest_dir:
                            show_toast("warning", "No activity_images folder for this book")
                        else:
                            try:
                                dest_dir.mkdir(parents=True, exist_ok=True)
                                dest = dest_dir / p.name
                                if not dest.exists():
                                    shutil.copy2(str(p), str(dest))
                                kit_key = get_kit_key(active_slug)
                                kit_list: list[str] = st.session_state.get(kit_key, [])
                                if str(dest) not in kit_list:
                                    was_empty = len(kit_list) == 0
                                    st.session_state[kit_key] = kit_list + [str(dest)]
                                    if was_empty:
                                        st.session_state[get_hero_key(active_slug)] = dest.name
                                persist_icons_hero(active_slug, toast_ok=True)
                                show_toast("success", f"Added {p.stem} to kit")
                            except Exception as e:
                                show_toast("error", f"Failed to add: {e}")
                if st.button("Select", key=f"sym_sel_{gi}", help="Select"):
                    st.session_state.symlib_selected_path = str(p)
                    safe_rerun()

        sel_path = st.session_state.get("symlib_selected_path")
        if sel_path:
            sp = Path(sel_path)
            if sp.exists():
                with st.expander("Selected symbol actions", expanded=True):
                    st.caption(sp.name)
                    try:
                        st.image(str(sp), width=120)
                    except Exception:
                        pass
                    rp = st.file_uploader("Replace", type=["png", "jpg", "jpeg", "webp"], key="symlib_sel_rep_up")
                    if rp is not None:
                        if st.button("Save replace", key="symlib_sel_rep_do"):
                            try:
                                img = Image.open(io.BytesIO(rp.read())).convert("RGBA")
                                img.save(str(sp))
                                show_toast("success", f"Replaced {sp.name}")
                                safe_rerun()
                            except Exception as e:
                                show_toast("error", f"Replace failed: {e}")
                    confirm = st.checkbox("Confirm delete", value=False, key="symlib_sel_del_confirm")
                    if st.button("Delete", key="symlib_sel_del", disabled=not confirm):
                        try:
                            sp.unlink(missing_ok=True)
                            st.session_state.symlib_selected_path = None
                            show_toast("success", f"Deleted {sp.name}")
                            safe_rerun()
                        except Exception as e:
                            show_toast("error", f"Delete failed: {e}")
            else:
                st.session_state.symlib_selected_path = None

    def render_tool_import_icons():
        st.subheader("Import Icons")
        active_slug = st.session_state.get("active_book")
        if not active_slug:
            st.info("Select a book in the top bar to import into its activity_images.")
            return
        dest_dir = images_dir_for_book(active_slug)
        if not dest_dir:
            st.warning("activity_images folder not found for this book. Set Themes root in Settings.")
            return
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        cols = st.columns(4)
        with cols[0]:
            overwrite = st.checkbox("Overwrite duplicates", value=False, key="imp_ow")
        with cols[1]:
            norm = st.checkbox("Normalize (quick crop)", value=True, key="imp_norm")
        with cols[2]:
            target_px = st.number_input("Target px", min_value=128, max_value=1024, value=512, step=64, key="imp_px")
        with cols[3]:
            white_cut = st.number_input("White cutoff", min_value=200, max_value=255, value=245, step=1, key="imp_white")
        c2 = st.columns(3)
        with c2[0]:
            promote = st.checkbox("Promote to Library", value=True, key="imp_promote")
        with c2[1]:
            add_to_kit = st.checkbox("Add to Kit", value=True, key="imp_add_kit")
        with c2[2]:
            st.caption(f"Saving to: {str(dest_dir)}")

        ups = st.file_uploader(
            "Upload PNG/JPG/WEBP/SVG",
            type=["png", "jpg", "jpeg", "webp", "svg"],
            accept_multiple_files=True,
            key="imp_multi",
        )
        if not ups:
            st.caption("Drag and drop files to begin.")
            return

        def _norm_preview(img: Image.Image) -> Image.Image:
            try:
                rgba = img.convert("RGBA")
                alpha = rgba.split()[-1]
                mn, mx = alpha.getextrema() if hasattr(alpha, 'getextrema') else (255, 255)
                if mn < 255:
                    mask = alpha.point(lambda p: 255 if p > 1 else 0)
                else:
                    gray = rgba.convert("L")
                    mask = gray.point(lambda p: 255 if int(p) < int(white_cut) else 0)
                bbox = mask.getbbox()
                if not bbox:
                    return rgba
                cropped = rgba.crop(bbox)
                w, h = cropped.size
                side = max(w, h)
                pad = int(round(side * 0.06))
                canvas_side = side + pad * 2
                canvas = Image.new("RGBA", (canvas_side, canvas_side), (0, 0, 0, 0))
                ox = (canvas_side - w) // 2
                oy = (canvas_side - h) // 2
                canvas.paste(cropped, (ox, oy))
                if target_px and int(target_px) != canvas_side:
                    canvas = canvas.resize((int(target_px), int(target_px)), Image.LANCZOS)
                return canvas
            except Exception:
                return img

        staged = []
        exist_stems = set(p.stem.lower() for p in dest_dir.glob("*.png"))
        for f in ups:
            name = Path(f.name).name
            stem = sanitise_symbol_name(Path(name).stem)
            ext = Path(name).suffix.lower().lstrip('.')
            if ext == 'svg':
                staged.append({"name": name, "stem": stem, "ext": ext, "warn": "SVG conversion not available", "img": None, "dpi": None, "size": None})
                continue
            try:
                data = f.read()
                im = Image.open(io.BytesIO(data))
                size = (im.width, im.height)
                dpi = None
                try:
                    dp = im.info.get("dpi")
                    if isinstance(dp, tuple) and len(dp) >= 1:
                        dpi = int(dp[0])
                except Exception:
                    dpi = None
                warn = None
                if min(size) < 256:
                    warn = "Small (<256px)"
                staged.append({"name": name, "stem": stem, "ext": ext, "warn": warn, "img": im.convert("RGBA"), "dpi": dpi, "size": size})
            except Exception:
                staged.append({"name": name, "stem": stem, "ext": ext, "warn": "Unreadable image", "img": None, "dpi": None, "size": None})

        st.markdown("### Review")
        cols_prev = st.columns(3)
        for i, it in enumerate(staged[:6]):
            with cols_prev[i % 3]:
                try:
                    if it["img"] is not None:
                        st.image(it["img"], caption=f"Before: {it['name']}")
                        if norm:
                            st.image(_norm_preview(it["img"]), caption=f"After: {it['stem']}.png")
                    else:
                        st.caption(it["warn"] or it["name"])
                except Exception:
                    pass

        bad_svg = [it for it in staged if it["ext"] == "svg"]
        if bad_svg:
            st.warning(f"{len(bad_svg)} SVG file(s) will be skipped (converter not installed).")

        if st.button(f"Import {len(staged) - len(bad_svg)} icon(s)", type="primary", key="imp_go"):
            added = 0
            replaced = 0
            kit_key = get_kit_key(active_slug)
            hero_key = get_hero_key(active_slug)
            kit_list: list[str] = st.session_state.get(kit_key, [])
            for it in staged:
                if it["img"] is None:
                    continue
                stem = it["stem"] or Path(it["name"]).stem
                target = dest_dir / f"{stem}.png"
                if target.exists():
                    if overwrite:
                        replaced += 1
                    else:
                        base = stem
                        n = 2
                        while True:
                            cand = dest_dir / f"{base}_{n}.png"
                            if not cand.exists():
                                target = cand
                                break
                            n += 1
                try:
                    out_im = it["img"]
                    if norm:
                        try:
                            out_im = _norm_preview(out_im)
                        except Exception:
                            pass
                    out_im.save(str(target))
                    if norm:
                        try:
                            normalize_icon_file(target, target_px=int(target_px), margin=0.06, white_cutoff=int(white_cut))
                        except Exception:
                            pass
                    if promote:
                        try:
                            promote_symbol_to_alpha_library(target)
                        except Exception:
                            pass
                    if add_to_kit:
                        if str(target) not in kit_list:
                            kit_list.append(str(target))
                    added += 1
                except Exception:
                    continue
            st.session_state[kit_key] = kit_list
            if not st.session_state.get(hero_key) and kit_list:
                st.session_state[hero_key] = Path(kit_list[0]).name
            persist_icons_hero(active_slug, toast_ok=True)
            try:
                flush_current_book_state(active_slug)
            except Exception:
                pass
            msg = f"Imported {added} icon(s)"
            if replaced:
                msg += f" - replaced {replaced}"
            show_toast("success", msg)
            safe_rerun()

    def render_tool_pdf_extractor():
        st.subheader("PDF Extractor")
        st.markdown(
            """
<style>
/* Compact PDF Extractor controls inside Tools drawer */
[data-testid="stSidebar"] .stButton > button { padding: 0.35rem 0.6rem !important; min-height: 2.0rem !important; font-size: 0.9rem !important; }
[data-testid="stSidebar"] .stCheckbox { margin-top: -6px !important; margin-bottom: -6px !important; }
[data-testid="stSidebar"] [data-testid="stTextInput"] input { padding-top: 0.35rem !important; padding-bottom: 0.35rem !important; }
[data-testid="stSidebar"] [data-testid="stTextArea"] textarea { padding-top: 0.35rem !important; padding-bottom: 0.35rem !important; }
</style>
            """,
            unsafe_allow_html=True,
        )
        if fitz is None:
            st.error("PyMuPDF (fitz) not installed. Add 'pymupdf' to requirements and install.")
            return
        if st.session_state.get("sf_show_extract_review"):
            files = [Path(p) for p in st.session_state.get("sf_extract_files", []) if Path(p).exists()]
            if not files:
                st.caption("No extracted symbols to review.")
                if st.button("Back"):
                    st.session_state.sf_show_extract_review = False
                    safe_rerun()
                return
            st.markdown("### Review extracted symbols")
            # Quick action: extract more pages from the same PDF
            if st.session_state.get("sf_last_pdf_bytes"):
                pdf_name = st.session_state.get("sf_last_pdf_name", "PDF")
                ex_more1, ex_more2 = st.columns([1, 2])
                with ex_more1:
                    if st.button("Extract more pages", key="ex_more_pages", help=f"Go back to the extraction form. The PDF ({pdf_name}) is still loaded."):
                        st.session_state.sf_show_extract_review = False
                        st.session_state.sf_use_stored_pdf = True
                        # Reset page selector to page 1 for the next extraction
                        st.session_state.pop("pdfext_start_page", None)
                        st.session_state.pop("pdfext_end_page", None)
                        safe_rerun()
                with ex_more2:
                    st.caption(f"PDF loaded: {pdf_name} - {len(files)} tiles from previous extraction(s)")
            sel_set = set(st.session_state.get("sf_extract_selected", []))
            # Paging controls
            total = len(files)
            page_size = 200
            max_page = max(1, (total + page_size - 1) // page_size)
            page = int(st.session_state.get("ex_page", 1))
            page = max(1, min(page, max_page))
            start = (page - 1) * page_size
            end = start + page_size
            page_files = files[start:end]
            pc1, pc2, pc3 = st.columns([1, 1, 2])
            with pc1:
                if st.button("< Prev", disabled=page <= 1, key="ex_prev"):
                    st.session_state.ex_page = page - 1
                    safe_rerun()
            with pc2:
                if st.button("Next >", disabled=page >= max_page, key="ex_next"):
                    st.session_state.ex_page = page + 1
                    safe_rerun()
            st.caption(f"Page {page}/{max_page} - {total} tiles")
            # Duplicate awareness (by stem) relative to the active book images
            active_slug = st.session_state.get("active_book")
            dest_dir = images_dir_for_book(active_slug) if active_slug else None
            existing_stems: set[str] = set()
            if dest_dir and dest_dir.exists():
                try:
                    for q in dest_dir.glob("*.png"):
                        existing_stems.add(q.stem.lower())
                except Exception:
                    pass
            # Helper to reflect current selection to checkbox widget keys
            def _sync_cb_from_sel():
                cur_sel = set(st.session_state.get("sf_extract_selected", []))
                for i, p in enumerate(page_files):
                    gi = start + i
                    st.session_state[f"ex_sel_{gi}"] = str(p) in cur_sel

            c1, c2, c3, _ = st.columns([1, 1, 1, 2])
            with c1:
                if st.button("Select all (page)"):
                    st.session_state.sf_extract_selected = [str(p) for p in page_files]
                    _sync_cb_from_sel()
                    safe_rerun()
            with c2:
                if st.button("Select all (all)"):
                    st.session_state.sf_extract_selected = [str(p) for p in files]
                    _sync_cb_from_sel()
                    safe_rerun()
            with c3:
                if st.button("Clear selection"):
                    st.session_state.sf_extract_selected = []
                    _sync_cb_from_sel()
                    safe_rerun()

            with st.form("ex_review_form"):
                # Grid of previews with selection + rename inputs
                cols = st.columns(4)
                for i, p in enumerate(page_files):
                    with cols[i % 4]:
                        try:
                            st.image(str(p), caption=p.stem[:18], width=92)
                        except Exception:
                            st.write(p.stem)
                        gi = start + i
                        ck = f"ex_sel_{gi}"
                        checked = str(p) in sel_set
                        st.checkbox("Select", key=ck, value=checked, label_visibility="collapsed")
                        rn_key = f"ex_rename_{gi}"
                        st.text_input("Rename", value=p.stem, key=rn_key, label_visibility="collapsed")
                        if p.stem.lower() in existing_stems:
                            st.caption("Duplicate in book")

                # Sync selected list with checkbox states, preserving off-page selections
                prev_sel: set[str] = set(st.session_state.get("sf_extract_selected", []))
                for i, p in enumerate(page_files):
                    sp = str(p)
                    gi = start + i
                    if bool(st.session_state.get(f"ex_sel_{gi}", sp in sel_set)):
                        prev_sel.add(sp)
                    else:
                        prev_sel.discard(sp)
                st.session_state.sf_extract_selected = list(prev_sel)

                # Save renames comes first so Enter triggers it
                b1, b1b = st.columns([1, 1])
                save_clicked = b1.form_submit_button("Save renames")
                apply_sel_clicked = b1b.form_submit_button("Apply selection")

                # Batch prefix/suffix helpers
                bf1, bf2, bf3, bf4 = st.columns([1, 1, 1, 1])
                with bf1:
                    st.text_input("Prefix", value=st.session_state.get("ex_batch_prefix", ""), key="ex_batch_prefix")
                with bf2:
                    st.text_input("Suffix", value=st.session_state.get("ex_batch_suffix", ""), key="ex_batch_suffix")
                with bf3:
                    st.checkbox("Selected only", value=bool(st.session_state.get("ex_batch_sel_only", True)), key="ex_batch_sel_only")
                apply_ps = bf4.form_submit_button("Apply prefix/suffix")

                # Skip duplicates toggle and mini log
                g1, g2 = st.columns([1, 3])
                with g1:
                    st.checkbox("Skip duplicates", value=bool(st.session_state.get("ex_skip_dups", True)), key="ex_skip_dups")
                with g2:
                    log: list[str] = st.session_state.get("sf_extract_ren_log", [])
                    if log:
                        st.caption("Last renames: " + "; ".join(log[-5:]))

                st.checkbox("Normalize on add", value=bool(st.session_state.get("ex_norm_on_add", True)), key="ex_norm_on_add")
                st.checkbox("Also save to Symbol Library (searchable)", value=bool(st.session_state.get("ex_promote_on_add", True)), key="ex_promote_on_add")

                active_slug = st.session_state.get("active_book")
                if active_slug:
                    st.caption(f"Adding to book: {decode_slug(active_slug)}")
                else:
                    st.caption("Adding to book: (none selected)")
                disabled_add = not active_slug or not st.session_state.get("sf_extract_selected")
                help_txt = None if active_slug else "Select a book first."
                ab1, ab2, ab3, ab4 = st.columns([1, 1, 1, 1])
                add_clicked = ab1.form_submit_button("Add selected to current kit", disabled=disabled_add, help=help_txt)
                add_close_clicked = ab2.form_submit_button("Add selected and close", disabled=disabled_add, help=help_txt)
                undo_clicked = ab3.form_submit_button("Undo last rename")
                done_clicked = ab4.form_submit_button("Done")

                ab5, ab6 = st.columns([1, 3])
                delete_clicked = ab5.form_submit_button("Delete extracted files")
                delete_confirmed = ab6.checkbox("Confirm delete", value=False, key="sf_extract_delete_confirm")

                # Handle actions
                if apply_ps:
                    pref = st.session_state.get("ex_batch_prefix", "")
                    suf = st.session_state.get("ex_batch_suffix", "")
                    only = bool(st.session_state.get("ex_batch_sel_only", True))
                    tgt_set = set(st.session_state.get("sf_extract_selected", [])) if only else set(str(p) for p in page_files)
                    changed = 0
                    for i, p in enumerate(page_files):
                        sp = str(p)
                        gi = start + i
                        if sp in tgt_set:
                            cur = st.session_state.get(f"ex_rename_{gi}", p.stem)
                            new = sanitise_symbol_name(f"{pref}{cur}{suf}")
                            if new != cur:
                                st.session_state[f"ex_rename_{gi}"] = new
                                changed += 1
                    if changed:
                        show_toast("success", f"Applied to {changed} item(s)")
                    safe_rerun()

                if save_clicked:
                    changed = 0
                    new_files: list[str] = []
                    new_sel: set[str] = set()
                    ops: list[tuple[str, str]] = []
                    for i, p in enumerate(page_files):
                        gi = start + i
                        new_stem = sanitise_symbol_name(st.session_state.get(f"ex_rename_{gi}", p.stem))
                        target = p.with_name(f"{new_stem}.png")
                        if target != p:
                            if target.exists():
                                base = new_stem
                                n = 2
                                while True:
                                    cand = p.with_name(f"{base}_{n}.png")
                                    if not cand.exists():
                                        target = cand
                                        break
                                    n += 1
                            try:
                                old_path = str(p)
                                p.rename(target)
                                changed += 1
                                if old_path in set(st.session_state.get("sf_extract_selected", [])):
                                    new_sel.add(str(target))
                                ops.append((old_path, str(target)))
                            except Exception:
                                target = p
                        else:
                            if str(p) in set(st.session_state.get("sf_extract_selected", [])):
                                new_sel.add(str(p))
                        new_files.append(str(target))
                    st.session_state.sf_extract_files = new_files
                    st.session_state.sf_extract_selected = list(new_sel)
                    if ops:
                        st.session_state.sf_extract_last_renames = ops
                        # Append to mini log
                        log = st.session_state.get("sf_extract_ren_log", [])
                        for a, b in ops:
                            log.append(f"{Path(a).name} â†’ {Path(b).name}")
                        st.session_state.sf_extract_ren_log = log[-50:]
                    if changed:
                        show_toast("success", f"Renamed {changed} file(s)")
                    safe_rerun()

                if apply_sel_clicked:
                    # Selection was already synced from checkboxes above on submit
                    show_toast("success", "Selection updated")
                    safe_rerun()

                if undo_clicked:
                    ops = list(st.session_state.get("sf_extract_last_renames", []))
                    if not ops:
                        show_toast("warning", "Nothing to undo")
                    else:
                        reverted = 0
                        files_map = {str(Path(p).resolve()): i for i, p in enumerate(st.session_state.get("sf_extract_files", []))}
                        try:
                            for old, new in reversed(ops):
                                np = Path(new)
                                if np.exists():
                                    tgt = Path(old)
                                    # Avoid collisions when reverting
                                    if tgt.exists():
                                        base = tgt.stem + "_revert"
                                        n = 2
                                        while True:
                                            cand = tgt.with_name(f"{base}_{n}.png")
                                            if not cand.exists():
                                                tgt = cand
                                                break
                                            n += 1
                                    np.rename(tgt)
                                    reverted += 1
                                    # Update lists in session
                                    files = [str(Path(x)) for x in st.session_state.get("sf_extract_files", [])]
                                    files = [str(tgt) if x == new else x for x in files]
                                    st.session_state.sf_extract_files = files
                                    sel = [str(tgt) if x == new else x for x in st.session_state.get("sf_extract_selected", [])]
                                    st.session_state.sf_extract_selected = sel
                            st.session_state.sf_extract_last_renames = []
                            if reverted:
                                show_toast("success", f"Reverted {reverted} rename(s)")
                        except Exception as e:
                            show_toast("error", f"Undo failed: {e}")
                        safe_rerun()

                def _do_add_and_maybe_close(close_after: bool):
                    slist = list(st.session_state.get("sf_extract_selected", []))
                    added = 0
                    dest_dir = images_dir_for_book(active_slug) if active_slug else None
                    if dest_dir:
                        try:
                            dest_dir.mkdir(parents=True, exist_ok=True)
                            kit_key = get_kit_key(active_slug)
                            hero_key = get_hero_key(active_slug)
                            kit_list: list[str] = st.session_state.get(kit_key, [])
                            before = len(kit_list)
                            skip_dups = bool(st.session_state.get("ex_skip_dups", True))
                            norm_on_add = bool(st.session_state.get("ex_norm_on_add", True))
                            promote_on_add = bool(st.session_state.get("ex_promote_on_add", True))
                            # refresh existing stems
                            exist_stems = set()
                            try:
                                for q in dest_dir.glob("*.png"):
                                    exist_stems.add(q.stem.lower())
                            except Exception:
                                pass
                            for sp in slist:
                                try:
                                    src = Path(sp)
                                    dest = dest_dir / src.name
                                    # Skip if duplicate by stem and configured to skip
                                    if skip_dups and src.stem.lower() in exist_stems:
                                        continue
                                    if not dest.exists():
                                        shutil.copy2(str(src), str(dest))
                                    if norm_on_add:
                                        try:
                                            normalize_icon_file(dest)
                                        except Exception:
                                            pass
                                    if promote_on_add:
                                        try:
                                            promote_symbol_to_alpha_library(dest)
                                        except Exception:
                                            pass
                                    if str(dest) not in kit_list:
                                        kit_list.append(str(dest))
                                        added += 1
                                        exist_stems.add(dest.stem.lower())
                                except Exception:
                                    continue
                            st.session_state[kit_key] = kit_list
                            if before == 0 and kit_list:
                                st.session_state[hero_key] = Path(kit_list[0]).name
                            persist_icons_hero(active_slug, toast_ok=True)
                            try:
                                flush_current_book_state(active_slug)
                            except Exception:
                                pass
                            show_toast("success", f"Added {added} icon(s) to kit")
                        except Exception as e:
                            show_toast("error", f"Add failed: {e}")
                        if close_after:
                            st.session_state.sf_show_extract_review = False
                        safe_rerun()

                if add_clicked:
                    _do_add_and_maybe_close(False)
                if add_close_clicked:
                    _do_add_and_maybe_close(True)

                if done_clicked:
                    st.session_state.sf_show_extract_review = False
                    safe_rerun()
            return

        # Use stored PDF if returning from "Extract more pages"
        use_stored = st.session_state.pop("sf_use_stored_pdf", False)
        uploaded = st.file_uploader("Upload a Boardmaker PDF", type=["pdf"], accept_multiple_files=False)
        if not uploaded and not use_stored:
            st.caption("Upload a PDF to begin.")
            return
        if not uploaded and use_stored:
            # Use the stored PDF bytes from the previous extraction
            stored_bytes = st.session_state.get("sf_last_pdf_bytes")
            stored_name = st.session_state.get("sf_last_pdf_name", "previous PDF")
            if not stored_bytes:
                st.caption("Upload a PDF to begin.")
                return
            st.info(f"Using previously uploaded: {stored_name}")
            if st.button("Upload a different PDF", key="ex_new_pdf"):
                st.session_state.pop("sf_last_pdf_bytes", None)
                st.session_state.pop("sf_last_pdf_name", None)
                safe_rerun()
            pdf_bytes = stored_bytes
        else:
            # Store the uploaded PDF for future "Extract more pages"
            pdf_bytes = uploaded.getvalue()
            st.session_state.sf_last_pdf_bytes = pdf_bytes
            st.session_state.sf_last_pdf_name = uploaded.name

        # Get page count for page selector
        try:
            _doc_pages = fitz.open(stream=pdf_bytes, filetype="pdf").page_count
        except Exception:
            _doc_pages = 1

        # Page range selector
        pg1, pg2, pg3 = st.columns([1, 1, 2])
        with pg1:
            start_page = st.number_input("Start page", min_value=1, max_value=_doc_pages, value=1, step=1, key="pdfext_start_page")
        with pg2:
            end_page = st.number_input("End page", min_value=1, max_value=_doc_pages, value=_doc_pages, step=1, key="pdfext_end_page")
        with pg3:
            append_mode = st.checkbox("Append to previous extraction", value=False, key="pdfext_append", help="If checked, new tiles are added to the previous extraction list. If unchecked, the previous list is cleared first.")

        # Clear previous extraction button
        if st.session_state.get("sf_extract_files"):
            if st.button("Clear previous extraction", key="pdfext_clear_prev"):
                st.session_state.sf_extract_files = []
                st.session_state.sf_extract_selected = []
                st.session_state.sf_show_extract_review = False
                show_toast("success", "Cleared previous extraction")
                safe_rerun()

        # Options
        out_root = str(symbols_root())
        out_dir = st.text_input("Output folder", value=out_root, key="pdfext_out")
        try:
            out_path_check = Path(out_dir)
            lib_root_check = symbols_root()
            if out_path_check.resolve() != lib_root_check.resolve() and lib_root_check.resolve() not in out_path_check.resolve().parents:
                st.info(f"Tip: set Output folder inside your Symbol Library to make extracted icons searchable. Library: {lib_root_check}")
        except Exception:
            pass
        dpi = st.selectbox("DPI", options=[150, 200, 300], index=0)
        strip_labels = st.checkbox("Strip labels (crop bottom of each cell)", value=True)

        # --- Grid layout ---
        st.markdown("##### Grid layout")

        # Boardmaker presets
        BM_PRESETS = {
            "Custom": {"rows": 6, "cols": 6, "mt": 2.0, "mb": 2.0, "ml": 2.0, "mr": 2.0, "pad": 2},
            "Boardmaker 6x6": {"rows": 6, "cols": 6, "mt": 2.0, "mb": 2.0, "ml": 2.0, "mr": 2.0, "pad": 2},
            "Boardmaker 4x4": {"rows": 4, "cols": 4, "mt": 2.0, "mb": 2.0, "ml": 2.0, "mr": 2.0, "pad": 2},
            "Boardmaker 3x3": {"rows": 3, "cols": 3, "mt": 2.0, "mb": 2.0, "ml": 2.0, "mr": 2.0, "pad": 2},
            "Boardmaker 2x8": {"rows": 2, "cols": 8, "mt": 2.0, "mb": 2.0, "ml": 2.0, "mr": 2.0, "pad": 2},
            "Boardmaker 8x2": {"rows": 8, "cols": 2, "mt": 2.0, "mb": 2.0, "ml": 2.0, "mr": 2.0, "pad": 2},
            "Boardmaker 1x12 (strip)": {"rows": 1, "cols": 12, "mt": 2.0, "mb": 2.0, "ml": 2.0, "mr": 2.0, "pad": 2},
        }
        preset_cols, auto_cols = st.columns([2, 1])
        with preset_cols:
            preset = st.selectbox("Preset", options=list(BM_PRESETS.keys()), key="pdfext_preset")
        with auto_cols:
            auto_detect_clicked = st.button("Auto-detect", key="pdfext_autodetect", help="Analyse the preview page for dark grid lines and set rows/cols/margins automatically")

        _preset = BM_PRESETS.get(preset, BM_PRESETS["Custom"])

        # Auto-detect grid from dark lines
        if auto_detect_clicked:
            try:
                _doc_ad = fitz.open(stream=pdf_bytes, filetype="pdf")
                _prev_page_ad = int(st.session_state.get("pdfext_prev_page", start_page))
                _pg_ad = _doc_ad.load_page(max(0, _prev_page_ad - 1))
                _zoom_ad = int(dpi) / 72.0
                _mat_ad = fitz.Matrix(_zoom_ad, _zoom_ad)
                _pix_ad = _pg_ad.get_pixmap(matrix=_mat_ad, alpha=False)
                _img_ad = Image.frombytes("RGB", [_pix_ad.width, _pix_ad.height], _pix_ad.samples)
                _gray_ad = _img_ad.convert("L")
                _W_ad, _H_ad = _gray_ad.size
                import numpy as np
                _arr = np.array(_gray_ad)
                _row_darkness = (_arr < 128).mean(axis=1)
                _col_darkness = (_arr < 128).mean(axis=0)
                _row_lines = [i for i in range(_H_ad) if _row_darkness[i] > 0.3]
                _col_lines = [i for i in range(_W_ad) if _col_darkness[i] > 0.3]
                def _group_lines(lines, min_gap=5):
                    if not lines:
                        return []
                    groups = [lines[0]]
                    for p in lines[1:]:
                        if p - groups[-1] > min_gap:
                            groups.append(p)
                    return groups
                _row_groups = _group_lines(_row_lines)
                _col_groups = _group_lines(_col_lines)
                _detected_rows = max(1, len(_row_groups) - 1)
                _detected_cols = max(1, len(_col_groups) - 1)
                if _col_groups:
                    _ml = round(100.0 * _col_groups[0] / _W_ad, 1)
                    _mr = round(100.0 * (_W_ad - _col_groups[-1]) / _W_ad, 1)
                else:
                    _ml, _mr = 2.0, 2.0
                if _row_groups:
                    _mt = round(100.0 * _row_groups[0] / _H_ad, 1)
                    _mb = round(100.0 * (_H_ad - _row_groups[-1]) / _H_ad, 1)
                else:
                    _mt, _mb = 2.0, 2.0
                st.session_state["pdfext_rows"] = _detected_rows
                st.session_state["pdfext_cols"] = _detected_cols
                st.session_state["pdfext_mt"] = _mt
                st.session_state["pdfext_mb"] = _mb
                st.session_state["pdfext_ml"] = _ml
                st.session_state["pdfext_mr"] = _mr
                show_toast("success", f"Detected {_detected_rows}r x {_detected_cols}c, margins T{_mt}% B{_mb}% L{_ml}% R{_mr}%")
                safe_rerun()
            except Exception as e:
                st.error(f"Auto-detect failed: {e}")

        rc1, rc2 = st.columns(2)
        with rc1:
            rows = st.number_input("Rows", min_value=1, max_value=20, value=_preset["rows"], step=1, key="pdfext_rows")
        with rc2:
            cols = st.number_input("Columns", min_value=1, max_value=20, value=_preset["cols"], step=1, key="pdfext_cols")

        with st.expander("Margins (trim page edges)", expanded=False):
            mg1, mg2, mg3, mg4 = st.columns(4)
            with mg1:
                m_top = st.number_input("Top %", min_value=0.0, max_value=30.0, value=_preset["mt"], step=0.5, format="%.1f", key="pdfext_mt")
            with mg2:
                m_bottom = st.number_input("Bottom %", min_value=0.0, max_value=30.0, value=_preset["mb"], step=0.5, format="%.1f", key="pdfext_mb")
            with mg3:
                m_left = st.number_input("Left %", min_value=0.0, max_value=30.0, value=_preset["ml"], step=0.5, format="%.1f", key="pdfext_ml")
            with mg4:
                m_right = st.number_input("Right %", min_value=0.0, max_value=30.0, value=_preset["mr"], step=0.5, format="%.1f", key="pdfext_mr")

        pad1, pad2 = st.columns([1, 2])
        with pad1:
            cell_pad = st.number_input("Cell padding (px)", min_value=0, max_value=50, value=_preset["pad"], step=1, key="pdfext_pad", help="Trims this many pixels from each side of every cell to remove border lines")
        with pad2:
            st.caption("Increase padding if tiles have dark border lines around the edges")

        auto_select = st.checkbox(
            "Auto-select all after extraction",
            value=bool(st.session_state.get("sf_extract_auto_select_all", True)),
        )
        st.session_state.sf_extract_auto_select_all = bool(auto_select)

        sb1, sb2, sb3 = st.columns(3)
        with sb1:
            skip_blanks = st.checkbox("Skip blank tiles", value=True)
        with sb2:
            white_cutoff = st.number_input("Blank white cutoff (0-255)", min_value=200, max_value=255, value=250, step=1)
        with sb3:
            min_nonwhite_ratio = st.number_input("Min non-white ratio (0-1)", min_value=0.0, max_value=1.0, value=0.005, step=0.001, format="%.3f")

        def extract(pdf_bytes: bytes, out: Path, r: int, c: int, dpi_val: int, crop_labels: bool, do_skip_blanks: bool, white_thr: int, min_nonwhite: float, mt: float, mb: float, ml: float, mr: float, page_start: int = 1, page_end: int | None = None, pad: int = 0) -> tuple[list[str], int]:
            out.mkdir(parents=True, exist_ok=True)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            saved: list[str] = []
            skipped = 0
            zoom = dpi_val / 72.0
            mat = fitz.Matrix(zoom, zoom)
            p_start = max(1, min(page_start, doc.page_count)) - 1
            p_end = doc.page_count if page_end is None else min(page_end, doc.page_count)
            for pi in range(p_start, p_end):
                pg = doc.load_page(pi)
                pix = pg.get_pixmap(matrix=mat, alpha=False)
                img = Image.open(fitz.Pixmap(pix, 0).pil_save("PNG")[1]) if False else Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                W, H = img.width, img.height
                top_px = int(H * (float(mt) / 100.0))
                bottom_px = int(H * (float(mb) / 100.0))
                left_px = int(W * (float(ml) / 100.0))
                right_px = int(W * (float(mr) / 100.0))
                usable_w = max(1, W - left_px - right_px)
                usable_h = max(1, H - top_px - bottom_px)
                cw = usable_w // c
                ch = usable_h // r
                for rr in range(r):
                    for cc in range(c):
                        left = left_px + (cc * cw) + pad
                        top = top_px + (rr * ch) + pad
                        right = left_px + ((cc + 1) * cw) - pad
                        bottom = top_px + ((rr + 1) * ch) - pad
                        if crop_labels:
                            bottom = top + int((bottom - top) * 0.85)
                        if right <= left or bottom <= top:
                            skipped += 1
                            continue
                        box = (max(0, left), max(0, top), min(W, right), min(H, bottom))
                        tile = img.crop(box)
                        # Skip near-blank tiles
                        if do_skip_blanks:
                            try:
                                g = tile.convert("L")
                                hist = g.histogram()
                                total = g.width * g.height
                                nonwhite = sum(hist[:int(white_thr)])
                                ratio = (nonwhite / total) if total else 0.0
                                if ratio < float(min_nonwhite):
                                    skipped += 1
                                    continue
                            except Exception:
                                pass
                        name = f"p{pi+1}_r{rr+1}_c{cc+1}.png"
                        dest = out / name
                        tile.save(str(dest))
                        saved.append(str(dest))
            return saved, skipped

        # Live preview with grid overlay (expanded by default)
        with st.expander("Preview page with grid overlay", expanded=True):
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                if doc.page_count:
                    prev_page = st.number_input("Preview page", min_value=1, max_value=doc.page_count, value=int(start_page), step=1, key="pdfext_prev_page")
                    pg = doc.load_page(prev_page - 1)
                    zoom = int(dpi) / 72.0
                    mat = fitz.Matrix(zoom, zoom)
                    pix = pg.get_pixmap(matrix=mat, alpha=False)
                    prev_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    show_grid = st.checkbox("Show grid overlay", value=True, key="pdfext_prev_grid")
                    if show_grid:
                        W, H = prev_img.width, prev_img.height
                        top_px = int(H * (float(m_top) / 100.0))
                        bottom_px = int(H * (float(m_bottom) / 100.0))
                        left_px = int(W * (float(m_left) / 100.0))
                        right_px = int(W * (float(m_right) / 100.0))
                        usable_w = max(1, W - left_px - right_px)
                        usable_h = max(1, H - top_px - bottom_px)
                        r = max(1, int(rows))
                        c = max(1, int(cols))
                        cw = max(1, usable_w // c)
                        ch = max(1, usable_h // r)
                        overlay = prev_img.copy()
                        draw = ImageDraw.Draw(overlay)
                        draw.rectangle([left_px, top_px, left_px + usable_w, top_px + usable_h], outline=(255, 0, 0), width=4)
                        for i in range(1, c):
                            x = left_px + (i * cw)
                            draw.line([x, top_px, x, top_px + usable_h], fill=(0, 200, 0), width=3)
                        for j in range(1, r):
                            y = top_px + (j * ch)
                            draw.line([left_px, y, left_px + usable_w, y], fill=(0, 200, 0), width=3)
                        if cell_pad > 0:
                            c0_left = left_px + cell_pad
                            c0_top = top_px + cell_pad
                            c0_right = left_px + cw - cell_pad
                            c0_bottom = top_px + ch - cell_pad
                            if c0_right > c0_left and c0_bottom > c0_top:
                                draw.rectangle([c0_left, c0_top, c0_right, c0_bottom], outline=(255, 200, 0), width=2)
                        prev_img = overlay
                    st.image(prev_img, caption=f"Page {prev_page} - red=margin, green=grid lines, yellow=cell padding (first cell)", use_container_width=True)
            except Exception:
                pass

        if st.button("Extract symbols", type="primary"):
            try:
                out_path = Path(out_dir)
                if not out_path.exists():
                    out_path.mkdir(parents=True, exist_ok=True)
                with st.spinner("Extracting... this may take a minute"):
                    files, skipped = extract(
                        pdf_bytes,
                        out_path,
                        int(rows),
                        int(cols),
                        int(dpi),
                        bool(strip_labels),
                        bool(skip_blanks),
                        int(white_cutoff),
                        float(min_nonwhite_ratio),
                        float(m_top),
                        float(m_bottom),
                        float(m_left),
                        float(m_right),
                        int(start_page),
                        int(end_page),
                        int(cell_pad),
                    )
                msg = f"Extracted {len(files)} symbols from pages {start_page}-{end_page} to {str(out_path)}"
                if skipped:
                    msg += f" (skipped {skipped} blank)"
                show_toast("success", msg)
                if append_mode:
                    prev = list(st.session_state.get("sf_extract_files", []))
                    st.session_state.sf_extract_files = prev + files
                    prev_sel = list(st.session_state.get("sf_extract_selected", []))
                    if st.session_state.get("sf_extract_auto_select_all", True):
                        st.session_state.sf_extract_selected = prev_sel + files
                else:
                    st.session_state.sf_extract_files = files
                    st.session_state.sf_extract_selected = list(files) if st.session_state.get("sf_extract_auto_select_all", True) else []
                st.session_state.sf_extract_dir = str(out_path)
                st.session_state.sf_show_extract_review = True
                safe_rerun()
            except Exception as e:
                st.error(f"Extraction failed: {e}")
                show_toast("error", "PDF extraction failed")

    def render_tool_pipeline():
        st.subheader("Pipeline (Batch Runner)")
        all_books = discover_books()
        if not all_books:
            st.info("No books found. Set Themes root in Settings.")
            return
        labels = {s: decode_slug(s) for s in all_books}
        book_labels = [labels[s] for s in all_books]
        # Manage selection in session for Select all / Clear support
        if "pl_books_select" not in st.session_state:
            st.session_state.pl_books_select = []
        st.multiselect("Books", options=book_labels, default=st.session_state.pl_books_select, key="pl_books_select")
        bc1, bc2 = st.columns([1, 1])
        with bc1:
            if st.button("Select all"):
                st.session_state.pl_books_select = book_labels
                safe_rerun()
        with bc2:
            if st.button("Clear"):
                st.session_state.pl_books_select = []
                safe_rerun()
        rev = {v: k for k, v in labels.items()}
        chosen_books = [rev[l] for l in st.session_state.pl_books_select]

        prods = [s["name"] for s in PRODUCT_SPECS]
        chosen_prods = []
        cols = st.columns(3)
        for i, name in enumerate(prods):
            with cols[i % 3]:
                if st.checkbox(name, key=f"pl_chk_{i}"):
                    chosen_prods.append(name)

        # Non-blocking QA gate warning
        if chosen_books:
            not_passed = 0
            for b in chosen_books:
                _, ok = read_qa_status(b)
                if not ok:
                    not_passed += 1
            if not_passed:
                st.info(f"{not_passed} of {len(chosen_books)} selected books have not passed QA. Their products will still build but won't be marked as QA-verified.")

        running = st.session_state.get("sf_pipeline_running", False)
        stop_flag = st.session_state.get("sf_pipeline_stop", False)
        status: dict = st.session_state.get("sf_pipeline_status", {})

        c1, c2 = st.columns([1, 1])
        with c1:
            disabled = running or not (chosen_books and chosen_prods)
            if st.button("Run pipeline", disabled=disabled):
                st.session_state.sf_pipeline_confirm = True
                st.session_state.sf_pipeline_sel = {
                    "books": chosen_books,
                    "labels": [labels[b] for b in chosen_books],
                    "prods": chosen_prods,
                }
                safe_rerun()
        with c2:
            if running and st.button("Stop after current"):
                st.session_state.sf_pipeline_stop = True

        # Confirm dialog
        if st.session_state.get("sf_pipeline_confirm"):
            sel = st.session_state.get("sf_pipeline_sel", {})
            books_lbl = ", ".join(sel.get("labels", []))
            prods_lbl = ", ".join(sel.get("prods", []))
            st.warning(f"Build {prods_lbl} for {len(sel.get('labels', []))} book(s): {books_lbl}. This may take several minutes.")
            cc1, cc2 = st.columns([1, 1])
            with cc1:
                if st.button("Confirm start", key="pl_confirm_start"):
                    ch_books = sel.get("books", [])
                    ch_prods = sel.get("prods", [])
                    st.session_state.sf_pipeline_running = True
                    st.session_state.sf_pipeline_stop = False
                    st.session_state.sf_pipeline_status = {b: {p: "Queued" for p in ch_prods} for b in ch_books}
                    st.session_state.sf_pipeline_confirm = False
                    safe_rerun()
            with cc2:
                if st.button("Cancel", key="pl_confirm_cancel"):
                    st.session_state.sf_pipeline_confirm = False
                    st.session_state.sf_pipeline_sel = {}
                    safe_rerun()

        # Runner loop
        if st.session_state.get("sf_pipeline_running", False):
            status = st.session_state.get("sf_pipeline_status", {})
            for b in list(status.keys()):
                for p in list(status[b].keys()):
                    if status[b][p] in {"Done", "Failed"}:
                        continue
                    status[b][p] = "Building..."
                    st.session_state.sf_pipeline_status = status
                    with st.spinner(f"Building {labels[b]} - {p}..."):
                        ok, msg = run_product_build(b, p, labels[b])
                    status[b][p] = "Done" if ok else "Failed"
                    st.session_state.sf_pipeline_status = status
                    if st.session_state.get("sf_pipeline_stop"):
                        break
                if st.session_state.get("sf_pipeline_stop"):
                    break
            st.session_state.sf_pipeline_running = False
            st.session_state.sf_pipeline_stop = False
            st.session_state.sf_pipeline_status = status

        # Status panel
        status = st.session_state.get("sf_pipeline_status", {})
        if status:
            st.markdown("#### Progress")
            for b, progd in status.items():
                st.markdown(f"**{labels.get(b, b)}**")
                cols = st.columns(3)
                items = list(progd.items())
                for i, (p, stt) in enumerate(items):
                    with cols[i % 3]:
                        st.write(f"{p}: {stt}")
            failed = [(b, p) for b, progd in status.items() for p, stt in progd.items() if stt == "Failed"]
            if failed and st.button("Retry failed"):
                st.session_state.sf_pipeline_running = True
                st.session_state.sf_pipeline_stop = False
                for b, p in failed:
                    st.session_state.sf_pipeline_status[b][p] = "Queued"
                safe_rerun()

    def render_tools_drawer():
        if not st.session_state.get("sf_tools_open"):
            return
        with st.sidebar:
            c_close, c_title = st.columns([1, 4])
            with c_close:
                if st.button("Close", key="sf_tools_close_top"):
                    st.session_state.sf_tools_open = False
                    qp_update(tools=None)
                    safe_rerun()
            with c_title:
                st.header("Tools")
            # Nav
            try:
                ensure_global_prefs()
            except Exception:
                pass
            last = st.session_state.get("sf_last_tool", "settings")
            tool = st.radio(
                "Choose a tool",
                options=["symbol_library", "import_icons", "pipeline", "settings"],
                format_func=lambda k: {
                    "symbol_library": "Symbol Library",
                    "import_icons": "Import Icons",
                    "pipeline": "Pipeline",
                    "settings": "Settings",
                }[k],
                index=["symbol_library", "import_icons", "pipeline", "settings"].index(last) if last in {"symbol_library","import_icons","pipeline","settings"} else 3,
            )
            st.session_state.sf_last_tool = tool
            try:
                persist_session_prefs()
            except Exception:
                pass

            st.divider()
            if tool == "settings":
                render_tool_settings()
            elif tool == "symbol_library":
                render_tool_symbol_library()
            elif tool == "import_icons":
                render_tool_import_icons()
            elif tool == "pipeline":
                render_tool_pipeline()

            st.divider()
            if st.button("Close"):
                st.session_state.sf_tools_open = False
                qp_update(tools=None)
                safe_rerun()

    # Grouped left navigation (ported from the retired Tool Launcher).
    # Shown only when the Tools drawer is closed (drawer reuses st.sidebar).
    try:
        render_nav_sidebar()
    except Exception:
        pass

    render_tools_drawer()


if __name__ == "__main__":
    main()

