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
    """Return up to 3 recommended picks for the Today screen, daily cached.
    If Anthropic API key is present, prefer AI-generated picks; otherwise use seasonal heuristics.
    """
    try:
        today = _now_iso_date()
        ai_on = (anthropic is not None) and bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())
        if not force:
            data = load_today_cache()
            if (
                isinstance(data, dict)
                and data.get("date") == today
                and data.get("season") == season
                and bool(data.get("ai")) == bool(ai_on)
                and isinstance(data.get("picks"), list)
            ):
                return [str(x) for x in data.get("picks")][:3]
        if ai_on:
            picks = ai_today_recommendations(display_map, season)
            if not picks:
                picks = season_recommendations(display_map, season)
        else:
            picks = season_recommendations(display_map, season)
        save_today_cache({"date": today, "season": season, "ai": ai_on, "picks": picks})
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
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Uploaded", stats.get("uploaded", 0))
    with c2:
        st.metric("Ready", stats.get("ready", 0))
    with c3:
        st.metric("Not started", stats.get("not_started", 0))

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
            a, b, c, d, e = st.columns([3, 1, 2, 2, 2])
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
                if st.button(
                    {"not_started": "o", "ready": ">", "uploaded": "*", "needs_update": "!", "paused": "||"}.get(status, "o"),
                    key=f"trk_cycle_{rid}",
                    help="Cycle status",
                ):
                    new_s = tracker_status_cycle(status)
                    patch = {"status": new_s}
                    if new_s == "uploaded" and not r.get("uploaded_date"):
                        patch["uploaded_date"] = _now_iso_date()
                    update_tracker_record(rid, patch)
                    show_toast("success", f"Status -> {new_s}")
                    safe_rerun()
                st.caption(status)
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


def get_display_map(slugs: list[str], titles_map: dict) -> dict:
    disp = {}
    for s in slugs:
        disp[s] = titles_map.get(s) or decode_slug(s)
    return disp


def show_toast(kind: str, msg: str, duration: int | None = None):
    if hasattr(st, "toast"):
        st.toast(msg)
    else:
        if kind == "success":
            st.success(msg)
        elif kind == "warning":
            st.warning(msg)
        elif kind == "error":
            st.error(msg)
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


def symbols_root() -> Path:
    env = os.environ.get("SF_SYMBOLS_ROOT", "").strip()
    if env and Path(env).exists():
        return Path(env)
    # Prefer the expanded symbol library if present
    expanded = project_root() / "assets" / "symbols" / "png"
    if expanded.exists():
        return expanded
    return project_root() / "assets" / "symbols"


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
    files = list(root.rglob("*.png"))
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
    "Adapted Book":       ["adaptedbook", "AdaptedBook", "adapted_book", "Adapted_Book"],
    "Matching":            ["matching", "Matching"],
    "Find & Cover":        ["find_and_cover", "Find_and_Cover", "FindCover", "find-and-cover", "FindAndCover"],
    "Word Search":         ["word_search", "Word_Search", "WordSearch"],
    "AAC Sentence Strips": ["sentence_strips", "AAC_Sentence", "aac_strips", "AAC_SentenceStrips"],
    "AAC Board":           ["aac_board", "aacboard", "AAC_Board", "AACBoard"],
    "Sequencing":          ["sequencing", "sequence", "story_strip", "storystrips", "story_strips"],
    "Sorting Cards":       ["sorting_cards", "Sorting_Cards", "SortingCards"],
    "Bingo":               ["bingo", "Bingo"],
    "Spin & Cover":         ["spincov", "spincover", "spin_cover", "spin-cover", "SpinCover", "SpinCover"],
    "Yes/No Questions":    ["yesno", "yes_no", "yes-no", "YesNo", "YesNoQuestions"],
}

PRODUCT_SPECS = [
    {"name": "Adapted Book", "module": "generators.ADAPTED_BOOK_ADAPTER", "func": "generate_adapted_book_pack", "pages": 13},
    {"name": "Matching", "module": "generators.MATCHING_GENERATOR", "func": "generate_matching_pack", "pages": 19},
    {"name": "Find & Cover", "module": "generators.FIND_AND_COVER_GENERATOR", "func": "generate_find_and_cover_pack", "pages": 15},
    {"name": "Word Search", "module": "generators.WORD_SEARCH_GENERATOR", "func": "generate_word_search", "pages": 5},
    {"name": "AAC Sentence Strips", "module": "generators.SENTENCE_STRIPS_AAC", "func": "generate_aac_pack", "pages": 10},
    {"name": "AAC Board", "module": "generators.aac_book_board", "func": "generate_aac_board_pack", "pages": 1},
    {"name": "Sequencing", "module": "generators.STORY_STRIPS_SEQUENCE", "func": "generate_story_strips", "pages": 7},
    {"name": "Sorting Cards", "module": "generators.SORTING_CARDS", "func": "generate_sorting_cards", "pages": 2},
    {"name": "Bingo", "module": "generators.BINGO_GENERATOR", "func": "generate_bingo_pack", "pages": 36},
    {"name": "Spin & Cover", "module": "generators.SPIN_COVER_GENERATOR", "func": "generate_spin_cover_pack", "pages": 10},
    {"name": "Yes/No Questions", "module": "generators.YES_NO_GENERATOR", "func": "generate_yes_no_pack", "pages": 4},
]


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


def read_book_state(slug: str) -> dict:
    p = book_state_path(slug)
    if not p:
        return _book_state_defaults(slug)
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
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
        if toast_ok:
            show_toast("success", "Config saved")
    except Exception:
        show_toast("warning", "Could not save book state - changes are session-only.")


def default_pack_code(slug: str) -> str:
    name = decode_slug(slug)
    parts = [w for w in name.split() if w]
    abbr = "".join(p[0] for p in parts)[:3].upper() or slug[:3].upper()
    return f"{abbr}01"


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

    missing: set[str] = set()
    try:
        for it in (state.get("qa", {}) or {}).get("items", []) or []:
            if (it or {}).get("decision") == "missing":
                fn = (it or {}).get("filename")
                if fn:
                    missing.add(str(fn))
    except Exception:
        pass

    out: list[str] = []
    seen: set[str] = set()
    for n in names:
        if not n or n in missing or n in seen:
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
            pref = ["Adapted Book", "Matching", "Find & Cover", "AAC Board", "Word Search", "AAC Sentence Strips", "Sorting Cards", "Bingo", "Spin & Cover", "Yes/No Questions"]
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
        "Adapted Book": "[x] Adapted Book - {pages} pages",
        "Matching": "[x] Matching Activities - {pages} pages (4 levels)",
        "Find & Cover": "[x] Find & Cover - {pages} pages (3 levels)",
        "AAC Board": "[x] AAC Communication Board - {pages} pages",
        "Word Search": "[x] Word Search - {pages} pages",
        "AAC Sentence Strips": "[x] AAC Sentence Strips - {pages} pages",
        "Sorting Cards": "[x] Sorting Cards - {pages} pages",
    }
    bullets: list[str] = []
    for name in [
        "Adapted Book",
        "Matching",
        "Find & Cover",
        "AAC Board",
        "Word Search",
        "AAC Sentence Strips",
        "Sorting Cards",
    ]:
        if built_info.get(name, {}).get("built") and name in bullet_templates:
            pages = _pages_for_product(name)
            if pages > 0:
                bullets.append(bullet_templates[name].format(pages=pages))
    while len(bullets) < 7:
        bullets.append("")

    total_pages = 0
    built_count = 0
    for n in ["Adapted Book", "Matching", "Find & Cover", "AAC Board", "Word Search", "AAC Sentence Strips", "Sorting Cards", "Bingo", "Spin & Cover", "Yes/No Questions"]:
        if built_info.get(n, {}).get("built"):
            built_count += 1
            total_pages += _pages_for_product(n)
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
    sample_targets = ["Matching", "AAC Sentence Strips", "Word Search"]
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
                tw, th = dr.textsize(txt, font=fnt)
                dr.text(((1200 - tw) // 2, (1200 - th) // 2), txt, fill=(0x00, 0x63, 0x79), font=fnt)
        else:
            dr = ImageDraw.Draw(end)
            txt = "Small Wins Studios"
            try:
                fnt = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 64)
            except Exception:
                fnt = ImageFont.load_default()
            tw, th = dr.textsize(txt, font=fnt)
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
        tw, th = d.textsize(txt, font=fnt)
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
        script = project_root() / "generators" / "PDF_MERGER.py"
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


def _terms_of_use_pdf() -> Path | None:
    p = project_root() / "assets" / "global" / "tpt_support_docs" / "Terms of Use.pdf"
    return p if p.exists() else None


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
        mod = importlib.import_module("generators.generate_quick_start_professional")
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
        "Adapted Book": ["Read-aloud companion", "Velcro-friendly pieces", "Color + black & white"],
        "Matching": ["Differentiated activity pages", "Print & go", "Color + black & white"],
        "Find & Cover": ["Differentiated levels", "Interactive covers", "Color + black & white"],
        "Word Search": ["Vocabulary practice", "Printable pages", "Preview included"],
        "AAC Sentence Strips": ["Sentence building", "Core + book vocabulary", "Color + black & white"],
        "AAC Board": ["Core + book vocabulary", "BoardReady layout", "Color + black & white"],
        "Sequencing": ["Beginning/Middle/End + 4-step + 5-step", "Cut-out cards included", "Color + black & white"],
        "Sorting Cards": ["Interchangeable headers", "Sort and discuss", "Print & cut"],
        "Bingo": ["4 differentiated levels", "Calling cards included", "Color + black & white"],
        "Spin & Cover": ["Spinner + mats", "Cut-out arrow included", "Color + black & white"],
        "Yes/No Questions": ["Yes/No choice cards", "Cut-out tokens included", "Color + black & white"],
    }

    merged_any = False
    warnings: list[str] = []

    for spec in PRODUCT_SPECS:
        product_name = spec["name"]
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
            from generators.PDF_MERGER import merge_pdfs  # type: ignore
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
                mod_g = importlib.import_module("generators.generate_quick_start_instructions")
                if hasattr(mod_g, "generate_quick_start_pdf"):
                    mod_g.generate_quick_start_pdf(quick_start_pdf, pack_code=pack_code, theme_name=theme_name)
                    generated_qs = quick_start_pdf.exists()
                if not generated_qs:
                    warnings.append(f"{product_name}: no Quick Start template found")
            except Exception as e:
                warnings.append(f"{product_name}: fallback Quick Start failed: {e}")

        # ZIP per product
        zip_path = upload_dir / f"{pack_code}_{product_name.replace(' ', '_')}_TPT.zip"
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
                z.write(merged_color, merged_color.name)
                if merged_bw.exists():
                    z.write(merged_bw, merged_bw.name)
                if preview_pdf and preview_pdf.exists():
                    z.write(preview_pdf, preview_pdf.name)
                z.write(tou, "Terms of Use.pdf")
                if quick_start_pdf.exists():
                    z.write(quick_start_pdf, quick_start_pdf.name)
        except Exception as e:
            warnings.append(f"{product_name}: zip failed: {e}")

    if not merged_any:
        return False, "No built products found to finalize"

    # Seed Upload Tracker records for this pack (built products only)
    tracker_created = 0
    try:
        product_types = [spec["name"] for spec in PRODUCT_SPECS if built_info.get(spec["name"], {}).get("built")]
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


def detect_products_in_output(slug: str) -> dict:
    out = output_dir_for_book(slug)
    result: dict[str, dict] = {}
    for name, tokens in BUILT_PRODUCT_TOKENS.items():
        result[name] = {"built": False, "path": None, "mtime": None}
    if not out or not out.exists():
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
    spec = next((s for s in PRODUCT_SPECS if s["name"] == product_name), None)
    if not spec:
        return False, f"Unknown product: {product_name}"

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


def render_build_tab(slug: str, display_name: str):
    # Gates
    state = read_book_state(slug)
    kit = st.session_state.get(get_kit_key(slug)) or [str((images_dir_for_book(slug) or Path('')) / fn) for fn in state.get("icons_kit", [])]
    icons_gate = len(kit) >= 6
    qa_label, qa_pass = read_qa_status(slug)
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

    # Handle rebuild action from query param
    try:
        rb = qp_get("rebuild")
    except Exception:
        rb = None
    if rb:
        try:
            if not st.session_state.get("sf_building") and icons_gate and qa_pass:
                st.session_state.sf_building = True
                name = str(rb)
                with st.spinner(f"Building {name}..."):
                    ok, msg = run_product_build(slug, name, display_name)
                st.session_state.sf_building = False
                show_toast("success" if ok else "error", msg)
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

    # If QA is fully resolved but not yet marked as passed, offer an unlock button here.
    if not qa_pass:
        try:
            candidates = qa_candidates(slug, limit=48)
            ensure_qa_state(slug, candidates)
            qstate: dict = st.session_state.get(qa_state_key(slug), {})
            total = len(qstate)
            resolved = sum(1 for v in qstate.values() if v.get("status") in {"accepted", "missing", "replaced"})
            if total and resolved == total:
                st.warning("QA is complete but not yet marked as passed. Click below to unlock builds.")
                if st.button("Mark QA as Passed (unlock builds)", key=f"build_unlock_qa_{slug}"):
                    persist_qa_pass(slug)
                    update_qa_log(slug, True)
                    show_toast("success", "QA marked as passed")
                    qp_update(view="build", tab="build")
                    safe_rerun()
        except Exception:
            pass

    if not (icons_gate and qa_pass):
        missing = []
        if not icons_gate:
            missing.append("Icons (>=6)")
        if not qa_pass:
            missing.append("QA")
        st.info("Complete before building: " + ", ".join(missing))

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

    # Build toolbar - compact actions
    st.markdown(
        """
<style>
.sf-build-toolbar .stButton>button { padding: 4px 10px !important; min-height: 30px !important; font-size: 14px !important; }
.sf-build-toolbar { margin-bottom: 6px; }
</style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sf-build-toolbar">', unsafe_allow_html=True)
    tb0, tb1, tb2, tb3, tb4, tb5 = st.columns([1,1,1,1,1,1])
    with tb0:
        # Pack code inline editor with save
        pc_val = st.text_input("Pack", value=pack_code, max_chars=12, key=f"tb_pack_{slug}")
        sc1, sc2 = st.columns([4, 1])
        with sc2:
            if st.button("Save", key=f"tb_pack_save_{slug}", help="Save pack code"):
                st_data = read_book_state(slug)
                b = st_data.get("build", {}) if isinstance(st_data.get("build"), dict) else {}
                b["pack_code"] = st.session_state.get(f"tb_pack_{slug}", pack_code)
                st_data["build"] = b
                write_book_state(slug, st_data, toast_ok=True)
                show_toast("success", "Pack code saved")
                safe_rerun()
    with tb1:
        # Rebuild all (top)
        unlocked_tb = [s for s in PRODUCT_SPECS if (icons_gate and qa_pass)]
        if st.button("Rebuild all", key=f"tb_rebuild_all_{slug}", disabled=st.session_state.get("sf_building", False) or not unlocked_tb, help=(None if unlocked_tb else "Complete Icons and QA first.")):
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
        # Rebuild only stale or unbuilt
        if st.button("Rebuild Stale", key=f"tb_rebuild_stale_{slug}", disabled=st.session_state.get("sf_building", False) or not unlocked_tb, help="Rebuild products that are unbuilt or older than latest icons"):
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
    with tb2:
        if st.button("Open OUTPUT", key=f"tb_open_out_{slug}"):
            out = output_dir_for_book(slug)
            if out and out.exists():
                open_folder(out)
            else:
                show_toast("info", "OUTPUT folder not found")
    with tb3:
        pv = bool(st.session_state.get(prev_key, False))
        if st.button("Preview" + (" (ON)" if pv else ""), key=f"tb_prev_{slug}", help=("Hide preview outputs" if pv else "Show preview outputs")):
            st.session_state[prev_key] = not pv
            safe_rerun()
    with tb4:
        dg = bool(st.session_state.get(diag_key, False))
        if st.button("Diagnostics" + (" (ON)" if dg else ""), key=f"tb_diag_{slug}", help=("Hide build diagnostics" if dg else "Show build diagnostics")):
            st.session_state[diag_key] = not dg
            safe_rerun()
    if ok:
                show_toast("success", "Finalize complete")
                st.success(msg)
                try:
                    if isinstance(msg, str) and msg.startswith("Finalize complete with warnings:"):
                        warn_text = "\n".join(msg.split("\n")[1:])
                        with st.expander("Warnings", expanded=False):
                            st.text_area("Warnings", value=warn_text, height=180)
                            try:
                                st.download_button("Download warnings", data=warn_text, file_name=f"{pack_code}_finalize_warnings.txt", key=f"tb_dl_warn_{slug}")
                            except Exception:
                                pass
                except Exception:
                    pass
                with c1:
                    if st.button("Open Tracker", key=f"tb_fin_open_trk_{slug}"):
                        st.session_state.view = "tracker"
                        qp_update(view="tracker")
                        safe_rerun()
                with c2:
                    if st.button("Open TPT_UPLOAD", key=f"tb_fin_open_upload_{slug}"):
                        out = output_dir_for_book(slug)
                        up = (out / "TPT_UPLOAD") if out else None
                        if up and up.exists():
                            open_folder(up)
                        else:
                            show_toast("info", "TPT_UPLOAD not found")
                    if st.button("Open FINAL", key=f"tb_fin_open_final_{slug}"):
                        out = output_dir_for_book(slug)
                        fi = (out / "FINAL") if out else None
                        if fi and fi.exists():
                            open_folder(fi)
                        else:
                            show_toast("info", "FINAL not found")
    st.markdown('</div>', unsafe_allow_html=True)

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
                    default=st.session_state.get(f"fs_sel_{slug}", []),
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
                dis_sel = bool(st.session_state.get("sf_building", False) or not (icons_gate and qa_pass) or not st.session_state.get(f"fs_sel_{slug}", []))
                if st.button("Rebuild Selected", key=f"tb_rebuild_selected_{slug}", disabled=dis_sel, help="Rebuild only the selected products"):
                    names = list(st.session_state.get(f"fs_sel_{slug}", []))
                    unlocked_list = [s for s in PRODUCT_SPECS if s["name"] in names]
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
                                    st.image(str(p), use_column_width=True)
                                elif p.suffix.lower() == ".pdf" and fitz is not None:
                                    pg = fitz.open(str(p)).load_page(0)
                                    pix = pg.get_pixmap(matrix=fitz.Matrix(1.3, 1.3), alpha=False)
                                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                                    st.image(img, use_column_width=True)
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
                            if st.button("Rebuild", key=f"gal_rebuild_{i}_{slug}", help=f"Rebuild {name}") and (icons_gate and qa_pass) and not st.session_state.get("sf_building"):
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

    for spec in PRODUCT_SPECS:
        name = spec["name"]
        info = built_info.get(name, {"built": False, "mtime": None})
        built = bool(info.get("built"))
        last = datetime.fromtimestamp(info["mtime"]).strftime("%d/%m/%Y %H:%M") if info.get("mtime") else None

        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            status = "Built" if built else ("Building..." if building and building_name == name else "Not built")
            st.markdown(f"**{name}**  -  {spec['pages']} pages  -  {status}{'  -  ' + last if last and built else ''}")
        with c2:
            disabled = building or (not icons_gate) or (not qa_pass)
            label = "Rebuild" if built else "Build"
            help_txt = None
            if disabled and not building and (not icons_gate or not qa_pass):
                needs = []
                if not icons_gate:
                    needs.append("Icons (>=6)")
                if not qa_pass:
                    needs.append("QA")
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

    pass


    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # Phase 5B â€” Covers section (Canva Bulk Create + merge helper)
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    st.divider()
    st.markdown("### Covers")

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
        "Adapted Book",
        "Matching",
        "Find & Cover",
        "AAC Board",
        "Word Search",
        "AAC Sentence Strips",
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
    st.markdown("#### Canva Bulk Create")
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
    st.info("Import this CSV into Canva Bulk Create using your 4 cover templates to generate all 4 cover images at once.")

    st.divider()
    st.markdown("#### Covers built?")
    st.caption("Check each box once you've exported from Canva and saved to the covers/ folder.")
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
        st.warning(f"Missing: {rel.replace('\\\\', '/')}" )

    # Optional: Generate listing images (requires covers or content PDFs)
    st.markdown("#### Generate Listing Images")
    if st.button("Generate Listing Images (1200x1200)", key=f"gen_imgs_{slug}"):
        try:
            imgs = generate_listing_images(slug, pack_code, out_dir, built_info)
            if imgs:
                st.success(f"Created {len(imgs)} images under TPT_UPLOAD/IMAGES/{pack_code}/")
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
        lst = (read_book_state(slug).get("listing") or {}) if isinstance(read_book_state(slug), dict) else {}
        # Defaults per user preference
        pin_board_default = st.text_input("Pinterest Board", value="SmallWinsStudios", key=f"pin_board_{slug}")
        # Try prefill from Upload Tracker if a TPT URL exists for this pack
        try:
            recs = read_upload_tracker()
            tpt_urls = [str(r.get("tpt_url")) for r in recs if isinstance(r, dict) and (r.get("book_slug") == slug) and (str(r.get("pack_code")) == str(pack_code)) and r.get("tpt_url")]
            prefill_link = tpt_urls[0] if tpt_urls else "https://www.teacherspayteachers.com/Store/SmallWinsStudios"
        except Exception:
            prefill_link = "https://www.teacherspayteachers.com/Store/SmallWinsStudios"
        pin_link_default = st.text_input("Link base (TPT Store/Product URL)", value=prefill_link, key=f"pin_link_{slug}")
        if st.button("Generate Pinterest CSV (5 pins)", key=f"gen_pin_{slug}"):
            try:
                pth = generate_pinterest_csv(slug, pack_code, out_dir, lst, imgs_dir, default_board=pin_board_default, link_base=pin_link_default)
                if pth and pth.exists():
                    st.success(f"Pinterest CSV ready: {pth.name}")
                    try:
                        st.download_button("Download CSV", data=pth.read_bytes(), file_name=pth.name, mime="text/csv", key=f"dl_pin_{slug}")
                    except Exception:
                        pass
            except Exception as e:
                st.error(f"Pinterest CSV failed: {e}")

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
        script = project_root() / "generators" / "PDF_MERGER.py"
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
            have_imgs = images_dir_local.exists() and any(images_dir_local.glob("*.jpg"))
            prev_pdf = images_dir_local / f"{pack_code}_preview.pdf"
            need_imgs = (not have_imgs) or (not prev_pdf.exists())
        except Exception:
            need_imgs = True
        if need_imgs:
            st.warning("Listing images or preview PDF missing.")
            if st.button("Generate Listing Images now", key=f"fix_gen_imgs_{slug}"):
                try:
                    imgs = generate_listing_images(slug, pack_code, out_dir, built_info)
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
                    script = project_root() / "generators" / "PDF_MERGER.py"
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

    # Bullets â€” map known products to concise benefits with dynamic page counts
    pages_by_name = {s["name"]: s["pages"] for s in PRODUCT_SPECS}
    benefit_text = {
        "Matching": "across 4 levels for easy differentiation",
        "Find & Cover": "builds visual scanning and attention",
        "Word Search": "targets letter recognition and vocabulary",
        "AAC Sentence Strips": "for core words and sentence building",
        "Sorting Cards": "for classification and category skills",
    }
    bullets = []
    for name in built_products:
        pages = pages_by_name.get(name)
        if pages is not None and name in benefit_text:
            bullets.append(f"{name} ({pages} pages) {benefit_text[name]}")
        else:
            bullets.append(f"Includes {name}")
    # Ensure exactly 6 bullets, pad with general benefits
    pads = [
        "Low-prep: print, laminate, and go",
        "Clear visuals for emergent learners",
        "Perfect for IEP goals and data collection",
        "Flexible for whole-group, small-group, or stations",
        "Supports AAC users with consistent visuals",
        "Teacher-friendly: consistent formatting across pages",
    ]
    for p in pads:
        if len(bullets) >= 6:
            break
        if p not in bullets:
            bullets.append(p)
    bullets = bullets[:6]
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
    grades = st.multiselect("Grade / Level Tags", options=grade_opts, default=lst["grade_tags"]) if not lst.get("grade_tags_missing") else st.multiselect("Grade / Level Tags", options=grade_opts)
    subjects = st.multiselect("Subject Tags", options=subj_opts, default=lst["subject_tags"]) if not lst.get("subject_tags_missing") else st.multiselect("Subject Tags", options=subj_opts)
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
        if st.button("Save to listing.json"):
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
        new_label = st.text_input("Label", value=str(cell.get("label", "")), key=f"aac_lbl_{slug}")
        sym_root = symbols_root()
        sym_query = st.text_input("Search symbols", value="", key=f"aac_q_{slug}")
        sym_files: list[str] = []
        if sym_root.exists():
            try:
                for p in sym_root.glob("**/*.png"):
                    nm = p.name
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
        sym_choice = st.selectbox("Symbol filename", options=opts, index=idx, key=f"aac_sym_{slug}")
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
            if st.button("Clear", key=f"aac_clear_{slug}"):
                new_label = ""
                sym_choice = "(none)"
                st.session_state[f"aac_lbl_{slug}"] = new_label
                st.session_state[f"aac_sym_{slug}"] = sym_choice
        with b2:
            if st.button("Save", key=f"aac_save_{slug}"):
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
                                tw, th = dr.textsize(lbl, font=fnt)
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
                    ftw, fth = dr.textsize(foot_txt, font=foot_font)
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
    return {"ui": {"readable_width": False, "large_text": False, "high_contrast": False, "show_tips": True}, "last_tool": "settings", "last_book": None}


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
        }
    if "sf_last_tool" not in st.session_state:
        data = load_global_prefs()
        st.session_state.sf_last_tool = data.get("last_tool", "settings")
    if "sf_last_book" not in st.session_state:
        data = load_global_prefs()
        st.session_state.sf_last_book = data.get("last_book")


def persist_session_prefs():
    data = load_global_prefs()
    ui = st.session_state.get("sf_ui_prefs", data.get("ui", {}))
    data["ui"] = ui
    data["last_tool"] = st.session_state.get("sf_last_tool", data.get("last_tool", "settings"))
    data["last_book"] = st.session_state.get("sf_last_book", data.get("last_book"))
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


def find_book_dir(slug: str) -> Path | None:
    for base in themes_root_candidates():
        d = base / slug
        if d.exists():
            return d
    return None


def count_icons_for_book(slug: str) -> int:
    """Approximate icon count from the canonical activity_images folder if present.
    Falls back to counting images under the book folder with 'activity' in parent name.
    """
    book_dir = find_book_dir(slug)
    if not book_dir:
        return 0
    # Primary location
    ai = book_dir / "activity_images"
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    if ai.exists():
        return sum(1 for p in ai.iterdir() if p.is_file() and p.suffix.lower() in exts)
    # Fallbacks
    count = 0
    for sub in book_dir.rglob("*"):
        try:
            if sub.is_file() and sub.suffix.lower() in exts and "activity" in sub.parent.name.lower():
                count += 1
        except Exception:
            continue
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


def read_qa_status(slug: str) -> tuple[str, bool]:
    # Prefer book_state.json written on QA pass (Phase 5)
    st_data = read_book_state(slug)
    try:
        if st_data.get("qa", {}).get("status") == "passed":
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
                    return ("Passed" if reviewed else "Partial"), reviewed
        except Exception:
            continue
    return ("Not run", False)


def read_listing_status(slug: str) -> str:
    # Phase 6: read from book_state.json listing.saved_at
    try:
        state = read_book_state(slug)
        listing = state.get("listing", {})
        if listing.get("saved_at"):
            return "Saved"
    except Exception:
        pass
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

    st.markdown("### This Week's Priorities")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "<p style='font-size:11px;font-weight:600;color:#C0392B;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:8px;'>P1 - Build this week</p>",
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
            "<p style='font-size:11px;font-weight:600;color:#E07B00;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:8px;'>P2 - Next 2 weeks</p>",
            unsafe_allow_html=True,
        )
        chips_html = ""
        for slug in p2:
            label = display_map.get(slug, decode_slug(slug))
            status = detect_priority_status(slug)
            href = f"?active_book={slug}&view=build&tab=icons"
            chips_html += render_priority_chip(label, "P2", status, href=href)
        st.markdown(chips_html, unsafe_allow_html=True)


def render_status_card(slug: str, display_name: str):
    # Compute basic stats
    icons = count_icons_for_book(slug)
    built = detect_built_products(slug)
    qa_label, qa_pass = read_qa_status(slug)
    listing_label = read_listing_status(slug)
    zip_label = read_zip_status(slug)
    any_built = any(built.values())

    # Gates bar thresholds: 6 (Matching etc.), 8 (Word Search), 20 (Bingo)
    gate_6 = min(icons, 6) / 20.0 * 100
    gate_8 = min(max(icons, 6), 8) / 20.0 * 100
    gate_20 = min(icons, 20) / 20.0 * 100

    with st.container(border=True):
        st.markdown(f"### {display_name}")
        # Icon gates
        st.markdown("Icons")
        pb = st.progress(min(icons, 20) / 20.0, text=f"{icons} icons - gates: 6, 8, 20")

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
        label, enabled, target = compute_next_action(icons, qa_pass, any_built, listing_label.startswith("Saved"))
        if st.button(label, disabled=not enabled):
            if target in {"icons", "qa", "build", "listing"}:
                open_build_screen(slug, target)
            else:
                show_toast("success", "Marked done - pick next book from the selector above")


def render_recent_books_chips(active_slug: str, display_map: dict):
    # Maintain a simple MRU in session state
    recent: list[str] = st.session_state.get("sf_recent_books", [])
    if active_slug and (not recent or recent[0] != active_slug):
        # update MRU
        recent = [active_slug] + [s for s in recent if s != active_slug]
        st.session_state.sf_recent_books = recent[:5]
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

def open_build_screen(slug: str, tab: str = "icons"):
    st.session_state.active_book = slug
    st.session_state.view = "build"
    st.session_state.build_tab = tab
    qp_update(active_book=slug, view="build", tab=tab)


def get_build_tab_from_qp() -> str:
    t = qp_get("tab") or "icons"
    return t if t in {"icons", "qa", "build", "listing", "aac"} else "icons"


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


def ensure_kit(slug: str):
    k = get_kit_key(slug)
    if k not in st.session_state:
        st.session_state[k] = []


def vocab_state_key(slug: str) -> str:
    return f"sf_vocab_{slug}"


def ensure_vocab_state(slug: str):
    k = vocab_state_key(slug)
    if k not in st.session_state:
        st.session_state[k] = {"skipped": set(), "show_skipped": False, "swap_word": None, "uploaded": set()}


def find_symbol_for_word(word: str) -> Path | None:
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
    for p in root.rglob("*.png"):
        steme = p.stem.lower().replace(" ", "_").replace("-", "_")
        if steme not in by_stem:
            by_stem[steme] = p
    if w in by_stem:
        return by_stem[w]
    for stem, p in by_stem.items():
        if stem.startswith(w + "_") or stem.startswith(w) or (w.replace("_", "") in stem.replace("_", "")):
            return p
    return None


def extract_book_vocab(slug: str) -> dict | None:
    """Extract vocab words from the AAC board PDF (ZIP) if present for this book.
    Returns dict with keys: book_title, core_words, book_words, all_words, source_file; or None.
    """
    # Check manual vocab first
    try:
        d0 = find_book_dir(slug)
        if d0:
            cfg = d0 / "config" / "book_vocab.json"
            if cfg.exists():
                try:
                    data = json.loads(cfg.read_text(encoding="utf-8"))
                    bwords = [w.strip() for w in data.get("book_words", []) if str(w).strip()]
                    return {
                        "book_title": decode_slug(data.get("slug", slug)),
                        "core_words": [],
                        "book_words": bwords,
                        "all_words": bwords,
                        "source_file": str(cfg),
                    }
                except Exception:
                    pass
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
                return {
                    "book_title": rec.get("title", decode_slug(slug)),
                    "core_words": [],
                    "book_words": dedup,
                    "all_words": dedup,
                    "source_file": str(src),
                }
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
        return {
            "book_title": decode_slug(slug),
            "core_words": [],
            "book_words": words,
            "all_words": words,
            "source_file": "ESSENTIALS_MASTER",
        }
    return None


def render_icons_tab(slug: str, display_name: str):
    ensure_kit(slug)
    kit_key = get_kit_key(slug)
    hero_key = get_hero_key(slug)
    kit: list[str] = st.session_state[kit_key]
    ensure_vocab_state(slug)
    vstate = st.session_state[vocab_state_key(slug)]
    if st.session_state.get(f"sf_add_icon_{slug}") or st.session_state.get(f"kit_replace_target_{slug}") or vstate.get("swap_word"):
        if st.button("Back to icons", key=f"icons_back_{slug}"):
            st.session_state[f"sf_add_icon_{slug}"] = False
            st.session_state.pop(f"kit_replace_target_{slug}", None)
            vstate["swap_word"] = None
            safe_rerun()
    # Always normalize new icons (no toggle)
    auto_norm = True
    auto_norm_white = 245
    auto_norm_margin = 0.06
    auto_norm_size = 512

    # Gate indicator
    icons_count = len(kit)
    st.markdown(f"**{icons_count} icons** - gates: 6, 8, 20")
    st.progress(min(icons_count, 20) / 20.0)

    # SECTION 1 â€” Book vocabulary icons (AAC/manual preferred)
    st.markdown(f"### Icons for {display_name}")
    vocab_data = extract_book_vocab(slug)
    words: list[str] = []
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
            files = [p for p in symbols_root().rglob("*.png") if qry.lower() in p.stem.lower()]
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
            st.caption("Vocab entered manually.")
            if st.button("Edit words", key=f"voc_edit_{slug}"):
                st.session_state[f"sf_edit_vocab_{slug}"] = True
        else:
            src_lbl = f" - {Path(aac_src).name}" if aac_src else ""
            st.caption(f"Book-specific vocabulary from AAC board{src_lbl}")
            # AAC board preview (only for PDFs)
            if aac_src and str(aac_src).lower().endswith(".pdf"):
                with st.expander("AAC Board Preview"):
                    if fitz is None:
                        st.info("PyMuPDF not installed.")
                    else:
                        try:
                            doc = fitz.open(aac_src)
                            pg = doc.load_page(0)
                            pix = pg.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            st.image(img, use_column_width=True)
                        except Exception:
                            st.caption("Could not preview PDF")
    else:
        words = parse_vocab_for_slug(slug)
        if words:
            if aac_src and not manual_cfg:
                src_lbl = f" - {Path(aac_src).name}"
                st.caption(f"AAC board detected{src_lbl} but no embedded vocab; using Essential words from master file")
                if str(aac_src).lower().endswith(".pdf"):
                    with st.expander("AAC Board Preview"):
                        if fitz is None:
                            st.info("PyMuPDF not installed.")
                        else:
                            try:
                                doc = fitz.open(aac_src)
                                pg = doc.load_page(0)
                                pix = pg.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                                st.image(img, use_column_width=True)
                            except Exception:
                                st.caption("Could not preview PDF")
            else:
                st.caption("Fallback: Essential words from vocab master file")
    # AAC diagnostics panel
    with st.expander("AAC Diagnostics"):
        diag = st.session_state.get(f"sf_aac_diag_{slug}")
        if diag:
            st.write({
                "found": diag.get("found"),
                "method": diag.get("method"),
                "found_path": diag.get("found_path"),
                "parse": diag.get("parse"),
            })
            st.caption("Roots searched:")
            st.code("\n".join(diag.get("roots", [])))
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
        st.info("No AAC board or vocab found for this book. Use search below to add icons manually.")
        qry = st.text_input("Search symbols by word...", value="")
        if qry.strip():
            files = [p for p in symbols_root().rglob("*.png") if qry.lower() in p.stem.lower()]
            files = sorted(files, key=lambda p: p.stem.lower())[:60]
            cols = st.columns(6)
            for i, p in enumerate(files):
                with cols[i % 6]:
                    try:
                        st.image(str(p), caption=p.stem[:12], width=120)
                    except Exception:
                        st.write(p.stem)
                    if st.button("Add to kit", key=f"ms_add2_{i}"):
                        dest_dir = images_dir_for_book(slug) or Path("")
                        try:
                            dest_dir.mkdir(parents=True, exist_ok=True)
                            dest = dest_dir / Path(p).name
                            if not dest.exists():
                                shutil.copy2(str(p), str(dest))
                            target_path = str(dest)
                            if target_path not in kit:
                                was_empty = len(kit) == 0
                                st.session_state[kit_key] = kit + [target_path]
                                if was_empty:
                                    st.session_state[hero_key] = Path(dest).name
                                persist_icons_hero(slug)
                        except Exception as e:
                            show_toast("error", f"Could not add: {e}")
    else:
        # Accept all matched
        if st.button("Accept all matched icons"):
            added = 0
            dest_dir = images_dir_for_book(slug) or Path("")
            dest_dir.mkdir(parents=True, exist_ok=True)
            before_count = len(kit)
            for w in words:
                if w in vstate["skipped"]:
                    continue
                match = find_symbol_for_word(w)
                if not match:
                    continue
                dest = dest_dir / Path(match).name
                try:
                    if not dest.exists():
                        shutil.copy2(str(match), str(dest))
                    if auto_norm and dest.exists():
                        try:
                            normalize_icon_file(dest, target_px=int(auto_norm_size), margin=float(auto_norm_margin), white_cutoff=int(auto_norm_white))
                        except Exception:
                            pass
                    target_path = str(dest)
                    if target_path not in kit:
                        kit.append(target_path)
                        added += 1
                        if before_count == 0 and added == 1:
                            st.session_state[hero_key] = Path(dest).name
                except Exception:
                    continue
            st.session_state[kit_key] = kit
            persist_icons_hero(slug, toast_ok=True)
            show_toast("success", f"Accepted {added} matched icons")

        def _row_status(word: str) -> str:
            desired = sanitise_symbol_name(word)
            is_accepted = bool(desired) and any(Path(p).stem.lower() == desired for p in kit)
            is_skipped = word in vstate["skipped"]
            if is_accepted:
                return "accepted"
            if is_skipped:
                return "skipped"
            m = find_symbol_for_word(word)
            if m:
                return "suggested"
            return "missing"

        statuses = {w: _row_status(w) for w in words}
        counts = {
            "accepted": sum(1 for s in statuses.values() if s == "accepted"),
            "suggested": sum(1 for s in statuses.values() if s == "suggested"),
            "missing": sum(1 for s in statuses.values() if s == "missing"),
            "skipped": sum(1 for s in statuses.values() if s == "skipped"),
        }
        total = max(len(words), 1)
        st.markdown(
            f"**Icons progress** - "
            f"Accepted: {counts['accepted']} | "
            f"Suggested: {counts['suggested']} | "
            f"Missing: {counts['missing']} | "
            f"Skipped: {counts['skipped']}  "
            f"(Total: {len(words)})"
        )

        view_mode = st.radio(
            "Show",
            options=["Missing", "Missing + Suggested", "All"],
            index=0,
            horizontal=True,
            key=f"icons_view_mode_{slug}",
        )
        vstate["show_skipped"] = st.checkbox("Show skipped words", value=bool(vstate.get("show_skipped", False)))

        missing_words = [w for w, s in statuses.items() if s == "missing"]
        if missing_words:
            with st.expander(f"Missing words list ({len(missing_words)})", expanded=False):
                txt = "\n".join(missing_words)
                st.text_area("", value=txt, height=160, key=f"missing_words_ta_{slug}")
                st.download_button(
                    "Download missing words (.txt)",
                    data=txt.encode("utf-8"),
                    file_name=f"{slug}_missing_words.txt",
                    mime="text/plain",
                    key=f"missing_words_dl_{slug}",
                )
        # Rows per vocab word
        for idx, w in enumerate(words):
            stt = statuses.get(w) or "missing"
            if (stt == "skipped") and (not vstate["show_skipped"]):
                continue
            if view_mode == "Missing" and stt != "missing":
                continue
            if view_mode == "Missing + Suggested" and stt not in ("missing", "suggested"):
                continue
            cols = st.columns([1, 2, 3])
            match = find_symbol_for_word(w)
            desired_stem = sanitise_symbol_name(w)
            accepted = bool(desired_stem) and any(Path(p).stem.lower() == desired_stem for p in kit)
            skipped = w in vstate["skipped"]
            uploaded_set = vstate.get("uploaded", set())
            uploaded = w in uploaded_set

            with cols[0]:
                if accepted:
                    st.caption("Accepted")
                elif skipped:
                    st.caption("Skipped")
                elif match:
                    st.caption("Suggested")
                else:
                    st.caption("Missing")
                if match and Path(match).exists():
                    try:
                        st.image(str(match), caption="", width=60)
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
                    show_accept = (not accepted) and (not skipped) and (match is not None)
                    if show_accept and st.button("Accept", key=f"voc_acc_{idx}"):
                        dest_dir = images_dir_for_book(slug) or Path("")
                        try:
                            dest_dir.mkdir(parents=True, exist_ok=True)
                            dest = dest_dir / Path(match).name
                            if not dest.exists():
                                shutil.copy2(str(match), str(dest))
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
                with a2:
                    show_replace = (not skipped)
                    if show_replace and st.button("Replace", key=f"voc_swap_{idx}"):
                        vstate["swap_word"] = w
                        safe_rerun()
                with a3:
                    show_skip = (not accepted) and (not skipped)
                    if show_skip and st.button("Skip", key=f"voc_skip_{idx}"):
                        vstate["skipped"].add(w)
                        safe_rerun()
                with a4:
                    up_key = f"voc_up_{idx}"
                    if st.button("Upload", key=f"voc_btn_up_{idx}"):
                        vstate["uploading"] = w
                        safe_rerun()
                    if vstate.get("uploading") == w:
                        up = st.file_uploader("", type=["png","jpg","jpeg","webp"], key=up_key)
                        if up is not None:
                            try:
                                default_lbl = sanitise_symbol_name(Path(up.name).stem) or sanitise_symbol_name(w)
                            except Exception:
                                default_lbl = sanitise_symbol_name(w)
                            lbl_key = f"voc_up_lbl_{idx}"
                            cur_lbl = st.text_input("Label", value=default_lbl, key=lbl_key)
                            csa, csb = st.columns([1, 1])
                            with csa:
                                if st.button("Save upload", key=f"voc_up_save_{idx}") and cur_lbl.strip():
                                    try:
                                        stem = sanitise_symbol_name(cur_lbl)
                                        out = symbols_root() / f"{stem}.png"
                                        out.parent.mkdir(parents=True, exist_ok=True)
                                        img = Image.open(io.BytesIO(up.read())).convert("RGBA")
                                        img.save(str(out))
                                        dest_dir = images_dir_for_book(slug) or Path("")
                                        dest_dir.mkdir(parents=True, exist_ok=True)
                                        dest = dest_dir / out.name
                                        if not dest.exists():
                                            shutil.copy2(str(out), str(dest))
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
                                        vstate.setdefault("uploaded", set()).add(w)
                                        vstate["uploading"] = None
                                        show_toast("success", f"Saved {out.name} to Symbol Library")
                                        safe_rerun()
                                    except Exception as e:
                                        show_toast("error", f"Upload failed: {e}")
                            with csb:
                                if st.button("Cancel", key=f"voc_up_cancel_{idx}"):
                                    vstate["uploading"] = None
                                    safe_rerun()

            # Inline suggestions (quick swap) under this row
            if (not accepted) and view_mode != "Missing":
                try:
                    token = sanitise_symbol_name(w).replace("_", " ")
                    if token:
                        cands = [p for p in symbols_root().rglob("*.png") if token in p.stem.lower()]
                        cands = sorted(cands, key=lambda p: p.stem.lower())[:3]
                    else:
                        cands = []
                except Exception:
                    cands = []
                if cands:
                    scols = st.columns(len(cands))
                    for jj, pp in enumerate(cands):
                        with scols[jj]:
                            try:
                                st.image(str(pp), caption=pp.stem.replace('_',' ')[:14], width=90)
                            except Exception:
                                st.write(pp.stem.replace('_',' '))
                            if st.button("Use", key=f"voc_sug_use_{idx}_{jj}"):
                                dest_dir = images_dir_for_book(slug) or Path("")
                                try:
                                    dest_dir.mkdir(parents=True, exist_ok=True)
                                    dest = dest_dir / Path(pp).name
                                    if not dest.exists():
                                        shutil.copy2(str(pp), str(dest))
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
                                    show_toast("success", f"Added {pp.stem} to kit")
                                    safe_rerun()
                                except Exception as e:
                                    show_toast("error", f"Could not add: {e}")

        # Swap panel
        if vstate.get("swap_word"):
            def _swap_ui():
                q = st.text_input("Search symbols...", value="", key="swap_q")
                files = [p for p in symbols_root().rglob("*.png")]
                files = sorted(files, key=lambda p: p.stem.lower())
                if q.strip():
                    files = [p for p in files if q.lower() in p.stem.lower()]
                cols = st.columns(6)
                for i, p in enumerate(files[:60]):
                    with cols[i % 6]:
                        try:
                            st.image(str(p), caption=p.stem[:12], width=100)
                        except Exception:
                            st.write(p.stem)
                        if st.button("Use", key=f"swap_use_{i}"):
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
                                vstate["swap_word"] = None
                                show_toast("success", "Swapped and added to kit")
                                safe_rerun()
                            except Exception as e:
                                show_toast("error", f"Swap failed: {e}")

                # Also allow choosing from recently extracted files
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
                                    dest_dir = images_dir_for_book(slug) or Path("")
                                    try:
                                        dest_dir.mkdir(parents=True, exist_ok=True)
                                        dest = dest_dir / Path(ep).name
                                        if not dest.exists():
                                            shutil.copy2(str(ep), str(dest))
                                        if bool(st.session_state.get("ex_norm_on_add", True)):
                                            try:
                                                normalize_icon_file(dest)
                                            except Exception:
                                                pass
                                        target_path = str(dest)
                                        if target_path not in kit:
                                            was_empty = len(kit) == 0
                                            st.session_state[kit_key] = kit + [target_path]
                                            if was_empty:
                                                st.session_state[hero_key] = Path(dest).name
                                            persist_icons_hero(slug)
                                        vstate["swap_word"] = None
                                        show_toast("success", "Used extracted icon and added to kit")
                                        safe_rerun()
                                    except Exception as e:
                                        show_toast("error", f"Use failed: {e}")

            # Inline swap panel for broad Streamlit compatibility
            st.markdown(f"#### Swap icon for: {vstate['swap_word']}")
            if st.button("Close", key="swap_close"):
                vstate["swap_word"] = None
                safe_rerun()
            _swap_ui()

        # Multi-file upload for efficiency
        st.markdown("Or upload multiple icons at once ->")
        with st.expander("Upload multiple icons"):
            ups = st.file_uploader(
                "Upload PNG/JPG/WEBP files",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                key=f"voc_multi_{slug}",
            )
            if ups:
                added_n = 0
                for f in ups:
                    try:
                        stem = sanitise_symbol_name(Path(f.name).stem)
                        lib = symbols_root() / f"{stem}.png"
                        lib.parent.mkdir(parents=True, exist_ok=True)
                        img = Image.open(io.BytesIO(f.read())).convert("RGBA")
                        img.save(str(lib))
                        added_n += 1
                    except Exception:
                        continue
                if added_n:
                    show_toast("success", f"Added {added_n} icons to Symbol Library")
                    safe_rerun()

        with st.expander("Import Boardmaker PDF icons (4x4 grid)", expanded=False):
            st.caption("Upload a Boardmaker PDF with a 4x4 grid. Provide 16 labels per page (row-major). Extracted icons are saved to the Symbol Library and can be added to this book's kit.")
            if fitz is None:
                st.info("PDF import requires PyMuPDF (fitz).")
            else:
                pdf = st.file_uploader("Boardmaker PDF", type=["pdf"], key=f"bm_pdf_{slug}")
                c_bm1, c_bm2, c_bm3, c_bm4 = st.columns([1, 1, 1, 1])
                with c_bm1:
                    bm_rows = st.number_input("Rows", min_value=1, max_value=10, value=4, step=1, key=f"bm_rows_{slug}")
                with c_bm2:
                    bm_cols = st.number_input("Cols", min_value=1, max_value=10, value=4, step=1, key=f"bm_cols_{slug}")
                with c_bm3:
                    bm_pad = st.number_input("Inner padding %", min_value=0.0, max_value=20.0, value=2.0, step=0.5, key=f"bm_pad_{slug}")
                with c_bm4:
                    add_to_kit = st.checkbox("Also add to this book's kit", value=True, key=f"bm_addkit_{slug}")

                st.caption("Labels (one per line). Use 16 labels per page. Leave a line blank to skip a cell.")
                labels_raw = st.text_area("", value="", height=140, key=f"bm_labels_{slug}")

                if pdf is not None and st.button("Extract icons", key=f"bm_extract_{slug}"):
                    try:
                        data = pdf.read()
                        doc = fitz.open(stream=data, filetype="pdf")
                        labels = [sanitise_symbol_name(t.strip()) for t in str(labels_raw or "").splitlines()]
                        labels = [t for t in labels if t is not None]

                        dest_dir = images_dir_for_book(slug) or Path("")
                        if add_to_kit:
                            dest_dir.mkdir(parents=True, exist_ok=True)

                        extracted = 0
                        saved = 0
                        k = list(st.session_state.get(kit_key, []))

                        zoom = 2.0
                        pad_frac = float(bm_pad) / 100.0
                        per_page = int(bm_rows) * int(bm_cols)

                        for page_idx in range(doc.page_count):
                            page = doc.load_page(page_idx)
                            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            w_px, h_px = img.size
                            cell_w = w_px / float(bm_cols)
                            cell_h = h_px / float(bm_rows)

                            for r in range(int(bm_rows)):
                                for c in range(int(bm_cols)):
                                    cell_idx = page_idx * per_page + (r * int(bm_cols) + c)
                                    if cell_idx >= len(labels):
                                        continue
                                    stem = labels[cell_idx]
                                    if not stem:
                                        continue
                                    left = int(c * cell_w)
                                    top = int(r * cell_h)
                                    right = int((c + 1) * cell_w)
                                    bottom = int((r + 1) * cell_h)
                                    pad_x = int((right - left) * pad_frac)
                                    pad_y = int((bottom - top) * pad_frac)
                                    crop = img.crop((left + pad_x, top + pad_y, right - pad_x, bottom - pad_y))

                                    lib_root = symbols_root() / "Alpha"
                                    first = stem[0].lower() if stem else "#"
                                    bucket = first if ("a" <= first <= "z") else "#"
                                    out_dir = lib_root / bucket
                                    out_dir.mkdir(parents=True, exist_ok=True)
                                    out_path = out_dir / f"{stem}.png"

                                    crop_rgba = crop.convert("RGBA")
                                    crop_rgba.save(str(out_path))
                                    try:
                                        normalize_icon_file(out_path, target_px=512, margin=0.06, white_cutoff=245)
                                    except Exception:
                                        pass

                                    saved += 1
                                    extracted += 1

                                    if add_to_kit and dest_dir and dest_dir.exists():
                                        dest = dest_dir / out_path.name
                                        try:
                                            if not dest.exists():
                                                shutil.copy2(str(out_path), str(dest))
                                            try:
                                                normalize_icon_file(dest, target_px=512, margin=0.06, white_cutoff=245)
                                            except Exception:
                                                pass
                                            if str(dest) not in k:
                                                k.append(str(dest))
                                        except Exception:
                                            pass

                        if add_to_kit:
                            st.session_state[kit_key] = k
                            if len(k) == 1:
                                st.session_state[hero_key] = Path(k[0]).name
                            persist_icons_hero(slug, toast_ok=True)
                        show_toast("success", f"Extracted {extracted} icons. Saved {saved} to Symbol Library." + (" Added to kit." if add_to_kit else ""))
                        safe_rerun()
                    except Exception as e:
                        show_toast("error", f"PDF extract failed: {e}")

    # Current kit grid
    st.markdown("### Icons in this kit")
    cadd1, cadd2 = st.columns([3, 1])
    with cadd2:
        if st.button("+ Add icon", key=f"add_icon_{slug}"):
            st.session_state[f"sf_add_icon_{slug}"] = True
    with cadd1:
        pass
    if st.session_state.get(f"sf_add_icon_{slug}"):
        cont = st.container()
        with cont:
            up = st.file_uploader("Upload PNG/JPG/WEBP", type=["png","jpg","jpeg","webp"], key=f"add_icon_up_{slug}")
            default_label = ""
            if up is not None:
                default_label = sanitise_symbol_name(Path(up.name).stem)
            label = st.text_input("Label (filename)", value=default_label, key=f"add_icon_lbl_{slug}")
            set_hero = st.checkbox("Set as hero", value=False, key=f"add_icon_hero_{slug}")
            ac1, ac2 = st.columns([1, 1])
            with ac1:
                if st.button("Add to kit", key=f"add_icon_do_{slug}") and up is not None and label.strip():
                    try:
                        stem = sanitise_symbol_name(label)
                        lib = symbols_root() / f"{stem}.png"
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
        st.info("No icons yet - accept suggestions or add from library in a later phase.")
    else:
        # Scoped styling for consistent, unclipped thumbnails and tight spacing
        st.markdown(
            """
<style>
.sf-icons-grid [data-testid="stImage"] img { width: 100% !important; height: 120px !important; object-fit: contain !important; background: #F7F7F7; border: 1px solid rgba(0,0,0,0.06); border-radius: 6px; }
.sf-icons-grid .sf-icon-name { text-align: center; font-size: 12px; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sf-icons-grid .stButton>button { padding: 2px 6px !important; min-height: 28px !important; font-size: 14px !important; }
.sf-icons-grid .sf-actions { margin-top: 4px; }
</style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sf-icons-grid">', unsafe_allow_html=True)
        cols2 = st.columns(6)
        for i, path in enumerate(kit):
            with cols2[i % 6]:
                try:
                    nm = Path(path).stem
                    st.image(path, use_column_width=True)
                except Exception:
                    nm = Path(path).stem
                # Name under thumbnail
                try:
                    st.markdown(f"<div class='sf-icon-name'>{nm}</div>", unsafe_allow_html=True)
                except Exception:
                    pass
                # Compact inline actions: Remove, Delete file, Replace
                st.markdown('<div class="sf-actions">', unsafe_allow_html=True)
                a1, a2, a3 = st.columns([1, 1, 1])
                with a1:
                    if st.button("Remove", key=f"rm_{i}", help="Remove from kit"):
                        st.session_state[kit_key] = [p for p in kit if p != path]
                        persist_icons_hero(slug)
                        safe_rerun()
                with a2:
                    if st.button("Delete file", key=f"rm_file_{i}", help="Delete file from book"):
                        st.session_state[f"rm_conf_{i}"] = path
                        safe_rerun()
                with a3:
                    if st.button("Replace", key=f"repl_{i}", help="Replace icon"):
                        st.session_state[f"kit_replace_target_{slug}"] = {"index": i, "old_path": path}
                        safe_rerun()
                # Delete confirm row
                if st.session_state.get(f"rm_conf_{i}") == path:
                    st.warning("Delete permanently? This removes the icon file from this book.")
                    dc1, dc2 = st.columns([1, 1])
                    with dc1:
                        if st.button("Confirm", key=f"rm_conf_do_{i}"):
                            try:
                                Path(path).unlink(missing_ok=True)
                            except Exception:
                                pass
                            st.session_state[kit_key] = [p for p in st.session_state.get(kit_key, []) if p != path]
                            st.session_state.pop(f"rm_conf_{i}", None)
                            persist_icons_hero(slug)
                            show_toast("success", "Icon deleted from book")
                            safe_rerun()
                    with dc2:
                        if st.button("Cancel", key=f"rm_conf_ca_{i}"):
                            st.session_state.pop(f"rm_conf_{i}", None)
                            safe_rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Replace panel for a selected kit item
    rep_state = st.session_state.get(f"kit_replace_target_{slug}")
    if rep_state:
        st.markdown("#### Replace selected icon")
        del_old = st.checkbox("Delete old file after replace", value=False, key=f"repl_del_old_{slug}")
        # Search library
        q = st.text_input("Search library symbols...", value="", key=f"repl_q_{slug}")
        files = [p for p in symbols_root().rglob("*.png")]
        files = sorted(files, key=lambda p: p.stem.lower())
        if q.strip():
            files = [p for p in files if q.lower() in p.stem.lower()]
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
                        if not dest.exists():
                            shutil.copy2(str(p), str(dest))
                        # Always normalize on replace
                        try:
                            normalize_icon_file(dest, target_px=int(auto_norm_size), margin=float(auto_norm_margin), white_cutoff=int(auto_norm_white))
                        except Exception:
                            pass
                        k = list(st.session_state.get(kit_key, []))
                        old_path = rep_state.get("old_path")
                        idx = k.index(old_path) if old_path in k else rep_state.get("index", 0)
                        # Replace entry
                        if str(dest) in k and k.index(str(dest)) != idx:
                            # if target already present elsewhere, just drop the old
                            k = [pp for pp in k if pp != old_path]
                        else:
                            if 0 <= idx < len(k):
                                k[idx] = str(dest)
                            else:
                                k.append(str(dest))
                            # remove any duplicate of old_path if present elsewhere
                            k = [pp for pp in k if pp != old_path or pp == str(dest)]
                        # Update hero if needed
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
        # Upload replacement
        up = st.file_uploader("Upload replacement (PNG/JPG/WEBP)", type=["png","jpg","jpeg","webp"], key=f"repl_up_{slug}")
        if up is not None and st.button("Use uploaded", key=f"repl_use_up_{slug}"):
            try:
                stem = sanitise_symbol_name(Path(up.name).stem)
                lib = symbols_root() / f"{stem}.png"
                lib.parent.mkdir(parents=True, exist_ok=True)
                img = Image.open(io.BytesIO(up.read())).convert("RGBA")
                img.save(str(lib))
                dest_dir = images_dir_for_book(slug) or Path("")
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / lib.name
                if not dest.exists():
                    shutil.copy2(str(lib), str(dest))
                k = list(st.session_state.get(kit_key, []))
                old_path = rep_state.get("old_path")
                idx = k.index(old_path) if old_path in k else rep_state.get("index", 0)
                if 0 <= idx < len(k):
                    k[idx] = str(dest)
                else:
                    k.append(str(dest))
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
                show_toast("success", "Replaced with uploaded icon")
                safe_rerun()
            except Exception as e:
                show_toast("error", f"Upload replace failed: {e}")
        if st.button("Cancel replace", key=f"repl_cancel_{slug}"):
            st.session_state.pop(f"kit_replace_target_{slug}", None)
            safe_rerun()

    # Hero picker
    st.markdown("### Hero icon")
    hero_options = [Path(p).name for p in st.session_state[kit_key]]
    current_idx = 0
    if hero_options:
        if hero_key in st.session_state and st.session_state[hero_key] in hero_options:
            current_idx = hero_options.index(st.session_state[hero_key])
        chosen = st.selectbox("Choose hero", options=hero_options, index=current_idx if hero_options else 0)
        st.session_state[hero_key] = chosen
        persist_icons_hero(slug)
    else:
        st.caption("No icons yet to select as hero.")
    st.caption("- or -")
    hup = st.file_uploader("Upload a hero image directly", type=["png","jpg","jpeg","webp"], key=f"hero_up_{slug}")
    if hup is not None:
        h_default = sanitise_symbol_name(Path(hup.name).stem)
        h_label = st.text_input("Label", value=h_default, key=f"hero_lbl_{slug}")
        add_lib = st.checkbox("Add to Symbol Library", value=True, key=f"hero_addlib_{slug}")
        set_hero2 = st.checkbox("Set as hero", value=True, key=f"hero_set_{slug}")
        if h_label.strip():
            try:
                stem = sanitise_symbol_name(h_label)
                lib = symbols_root() / f"{stem}.png"
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
    ensure_vocab_state(slug)
    vstate = st.session_state[vocab_state_key(slug)]
    kit_key = get_kit_key(slug)
    kit: list[str] = st.session_state.get(kit_key, [])

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
            desired = sanitise_symbol_name(w)
            accepted = bool(desired) and any(Path(p).stem.lower() == desired for p in kit)
            if accepted:
                continue
            if find_symbol_for_word(w):
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
                st.text_area("", value=txt, height=140, key=f"qa_missing_words_{slug}")
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
                st.text_area(" ", value=txt2, height=140, key=f"qa_suggested_words_{slug}")
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
    st.markdown(f"**QA Progress:** {resolved}/{total}")
    st.progress((resolved / total) if total else 0.0)

    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("Accept all high-confidence (>= 0.85)"):
            n = 0
            for sp, v in state.items():
                if v.get("status") == "pending" and float(v.get("confidence", 0)) >= 0.85:
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
            st.caption(f"conf {float(v.get('confidence', 0)):.2f} - {v.get('status')}")
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
            show_toast("success", "QA marked as passed")
            open_build_screen(slug, "build")


def render_build_screen(slug: str, display_name: str):
    st.header(f"Build - {display_name}")
    tab_names = ["Icons", "QA", "Build", "Listing", "AAC Board"]
    default_tab = {"icons": 0, "qa": 1, "build": 2, "listing": 3, "aac": 4}.get(st.session_state.get("build_tab", "icons"), 0)
    tabs = st.tabs(tab_names)

    with tabs[0]:
        render_icons_tab(slug, display_name)

    with tabs[1]:
        render_qa_tab(slug, display_name)

    with tabs[2]:
        render_build_tab(slug, display_name)

    with tabs[3]:
        render_listing_tab(slug, display_name)

    with tabs[4]:
        render_aac_board_tab(slug, display_name)


def render_top_bar(display_map: dict, active_slug: str | None) -> str | None:
    prefs = st.session_state.get("sf_ui_prefs", {})
    readable_width = 800 if prefs.get("readable_width") else 960
    large_text_px = "18px" if prefs.get("large_text") else "16px"
    hc = bool(prefs.get("high_contrast"))
    topbar_bg = "#1E3A5F"
    brand_col = "#F5C518"
    txt_col = "white"
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
        .sf-topbar-wrap {{position:fixed; top:0; left:0; right:0; z-index:999; background:{topbar_bg}; border-bottom:1px solid #0f2947;}}
        .sf-topbar-inner {{max-width:{readable_width}px; margin:0 auto; padding:6px 16px 8px 16px;}}
        .sf-topbar-inner * {{color:{txt_col} !important;}}
        .sf-brand {{font-weight:800; color:{brand_col}; font-size:18px; letter-spacing:0.2px; text-shadow: 0 1px 1px rgba(0,0,0,0.35); margin-top:2px;}}
        .sf-logo {{margin-top:-6px; margin-bottom:-6px;}}
        .sf-logo img {{display:block;}}
        .sf-topbar-inner [data-testid="stImage"] {{margin-top:-8px !important; margin-bottom:-8px !important;}}
        .sf-topbar-inner [data-testid="stSelectbox"] label {{display:none;}}
        .sf-topbar-inner [data-testid="stSelectbox"] > div {{background: rgba(255,255,255,0.10) !important; border: 1px solid rgba(255,255,255,0.25) !important;}}
        .sf-topbar-inner [data-testid="stSelectbox"] svg {{color:white !important;}}
        .sf-topbar-inner .stButton > button {{background: rgba(255,255,255,0.10) !important; border: 1px solid rgba(255,255,255,0.25) !important; white-space: nowrap !important; padding: 6px 12px !important; min-width: 76px !important; font-size: 12px !important;}}
        .sf-topbar-inner .stButton > button:hover {{background: rgba(255,255,255,0.16) !important;}}
        .sf-topbar-inner [data-testid="stToggle"] label, .sf-topbar-inner .stCheckbox label {{font-size:12px !important; line-height:1.1 !important; white-space: normal !important;}}
        .sf-content {{max-width:{readable_width}px; margin:120px auto 16px auto; opacity:{dim}; transition: opacity 120ms ease;}}
        html, body, [data-testid="stAppViewContainer"] * {{font-size:{large_text_px};}}
        .sf-tools-btn {{opacity:1;}}
        </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    chosen_slug_val = active_slug
    with st.container():
        st.markdown('<div class="sf-topbar-wrap"><div class="sf-topbar-inner">', unsafe_allow_html=True)
        cols = st.columns([2, 4, 4])
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
            ncol, tcol = st.columns([3, 1])
            with ncol:
                ai_on = (anthropic is not None) and bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())

                # Primary nav
                nav1, nav2, nav3 = st.columns(3)
                with nav1:
                    if st.button("Today", key="sf_nav_today"):
                        st.session_state.view = "today"
                        qp_update(view="today")
                        safe_rerun()
                with nav2:
                    if st.button("Build", key="sf_nav_build"):
                        st.session_state.view = "build"
                        qp_update(view="build")
                        safe_rerun()
                with nav3:
                    if st.button("Tracker", key="sf_nav_tracker"):
                        st.session_state.view = "tracker"
                        qp_update(view="tracker")
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

                st.markdown(render_ai_badge(ai_on), unsafe_allow_html=True)
                if st.button("Tools", key="sf_open_tools"):
                    st.session_state.sf_tools_open = True
                    qp_update(tools="1")
            with tcol:
                _prefs = dict(st.session_state.get("sf_ui_prefs", {}))
                _prefs["readable_width"] = st.toggle("Readable width", value=_prefs.get("readable_width", False), key="sf_tb_rw")
                _prefs["large_text"] = st.toggle("Large text", value=_prefs.get("large_text", False), key="sf_tb_lt")
                _prefs["high_contrast"] = st.toggle("High contrast", value=_prefs.get("high_contrast", False), key="sf_tb_hc")
                st.session_state.sf_ui_prefs = _prefs
                try:
                    persist_session_prefs()
                except Exception:
                    pass
            st.markdown('</div></div>', unsafe_allow_html=True)
    return chosen_slug_val


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
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 960px;
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
h1 { font-size: 22px !important; font-weight: 700 !important; color: #1A1A1A !important; }
h2 { font-size: 16px !important; font-weight: 600 !important; color: #1A1A1A !important; }
h3 { font-size: 14px !important; font-weight: 500 !important; color: #1A1A1A !important; }

/* â”€â”€ PRIMARY BUTTONS â”€â”€ */
.stButton > button[kind="primary"],
.stButton > button {
    background-color: #006379 !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    height: 36px !important;
    transition: background 150ms ease !important;
}
.stButton > button:hover {
    background-color: #005268 !important;
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
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    height: 44px !important;
    color: #595959 !important;
    font-weight: 400 !important;
    border-bottom: 2px solid transparent !important;
    padding: 0 20px !important;
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
        st.session_state.build_tab = qp_tab if qp_tab in {"icons", "qa", "build", "listing", "aac"} else "icons"
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
            # Today Screen
            season = season_us(datetime.now())
            # Phase 11 (stub): daily-cached heuristic recommendations; refresh button to force recalc
            c1, c2 = st.columns([3, 1])
            with c2:
                if st.button("Refresh picks"):
                    try:
                        # Force recompute and cache update
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
            render_priorities_panel(display_map)
            active = st.session_state.active_book
            render_status_card(active, display_map.get(active, decode_slug(active)))
            render_recent_books_chips(active, display_map)
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
                st.experimental_rerun() if hasattr(st, "experimental_rerun") else None

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

        with st.expander("Advanced normalisation", expanded=False):
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

        with st.expander("Advanced normalisation", expanded=False):
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

        uploaded = st.file_uploader("Upload a Boardmaker PDF", type=["pdf"], accept_multiple_files=False)
        if not uploaded:
            st.caption("Upload a PDF to begin.")
            return
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
        mg1, mg2, mg3, mg4 = st.columns(4)
        with mg1:
            m_top = st.number_input("Top margin %", min_value=0.0, max_value=30.0, value=2.0, step=0.5, format="%.1f")
        with mg2:
            m_bottom = st.number_input("Bottom margin %", min_value=0.0, max_value=30.0, value=2.0, step=0.5, format="%.1f")
        with mg3:
            m_left = st.number_input("Left margin %", min_value=0.0, max_value=30.0, value=2.0, step=0.5, format="%.1f")
        with mg4:
            m_right = st.number_input("Right margin %", min_value=0.0, max_value=30.0, value=2.0, step=0.5, format="%.1f")
        auto_select = st.checkbox(
            "Auto-select all after extraction",
            value=bool(st.session_state.get("sf_extract_auto_select_all", True)),
        )
        st.session_state.sf_extract_auto_select_all = bool(auto_select)
        cols1, cols2 = st.columns(2)
        with cols1:
            rows = st.number_input("Rows per page", min_value=1, max_value=12, value=6, step=1)
        with cols2:
            cols = st.number_input("Columns per page", min_value=1, max_value=12, value=6, step=1)

        sb1, sb2, sb3 = st.columns(3)
        with sb1:
            skip_blanks = st.checkbox("Skip blank tiles", value=True)
        with sb2:
            white_cutoff = st.number_input("Blank white cutoff (0-255)", min_value=200, max_value=255, value=250, step=1)
        with sb3:
            min_nonwhite_ratio = st.number_input("Min non-white ratio (0-1)", min_value=0.0, max_value=1.0, value=0.005, step=0.001, format="%.3f")

        def extract(pdf_bytes: bytes, out: Path, r: int, c: int, dpi_val: int, crop_labels: bool, do_skip_blanks: bool, white_thr: int, min_nonwhite: float, mt: float, mb: float, ml: float, mr: float) -> tuple[list[str], int]:
            out.mkdir(parents=True, exist_ok=True)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            saved: list[str] = []
            skipped = 0
            zoom = dpi_val / 72.0
            mat = fitz.Matrix(zoom, zoom)
            for pi in range(doc.page_count):
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
                        left = left_px + (cc * cw)
                        top = top_px + (rr * ch)
                        right = left + cw
                        bottom = top + ch
                        if crop_labels:
                            bottom = top + int(ch * 0.85)
                        box = (left, top, right, bottom)
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

        # Lightweight preview (first page)
        with st.expander("Preview (first page)", expanded=False):
            try:
                doc = fitz.open(stream=uploaded.getvalue(), filetype="pdf")
                if doc.page_count:
                    pg = doc.load_page(0)
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
                            draw.line([x, top_px, x, top_px + usable_h], fill=(255, 0, 0), width=3)
                        for j in range(1, r):
                            y = top_px + (j * ch)
                            draw.line([left_px, y, left_px + usable_w, y], fill=(255, 0, 0), width=3)
                        prev_img = overlay
                    st.image(prev_img, caption="Preview at selected DPI (overlay uses margins + rows/cols)", use_container_width=True)
            except Exception:
                pass

        if st.button("Extract symbols", type="primary"):
            try:
                out_path = Path(out_dir)
                if not out_path.exists():
                    out_path.mkdir(parents=True, exist_ok=True)
                with st.spinner("Extracting... this may take a minute"):
                    files, skipped = extract(
                        uploaded.getvalue(),
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
                    )
                msg = f"Extracted {len(files)} symbols to {str(out_path)}"
                if skipped:
                    msg += f" (skipped {skipped} blank)"
                show_toast("success", msg)
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
                "",
                options=["symbol_library", "import_icons", "pdf_extractor", "pipeline", "settings"],
                format_func=lambda k: {
                    "symbol_library": "Symbol Library",
                    "import_icons": "Import Icons",
                    "pdf_extractor": "PDF Extractor",
                    "pipeline": "Pipeline",
                    "settings": "Settings",
                }[k],
                index=["symbol_library", "import_icons", "pdf_extractor", "pipeline", "settings"].index(last) if last in {"symbol_library","import_icons","pdf_extractor","pipeline","settings"} else 4,
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
            elif tool == "pdf_extractor":
                render_tool_pdf_extractor()
            elif tool == "pipeline":
                render_tool_pipeline()

            st.divider()
            if st.button("Close"):
                st.session_state.sf_tools_open = False
                qp_update(tools=None)
                safe_rerun()

    render_tools_drawer()


if __name__ == "__main__":
    main()

