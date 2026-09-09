# -*- coding: utf-8 -*-
"""Tracker logic for StudioForge — extracted from studioforge_app.py.

Pure data logic (no Streamlit UI). The UI rendering stays in studioforge_app.py
and calls these functions.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sf_shared import project_root, _read_json_safe


def upload_tracker_path() -> Path:
    return project_root() / "upload_tracker.json"


def upload_tracker_audit_path() -> Path:
    return project_root() / "upload_tracker_audit.jsonl"


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


def tracker_record_id(book_slug: str, pack_code: str, product_type: str) -> str:
    return f"{book_slug}__{pack_code}__{product_type}".lower()


def tracker_status_cycle(status: str) -> str:
    order = ["not_started", "ready", "uploaded"]
    s = (status or "not_started").strip().lower()
    if s not in order:
        return "not_started"
    return order[(order.index(s) + 1) % len(order)]


def init_tracker_pack(*, book_slug: str, book_title: str, pack_code: str, product_types: list[str]) -> int:
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
    out: dict[str, int] = {"uploaded": 0, "ready": 0, "not_started": 0, "needs_update": 0, "paused": 0}
    for r in records:
        if not isinstance(r, dict):
            continue
        s = str(r.get("status") or "not_started").strip().lower()
        if s not in out:
            continue
        out[s] += 1
    return out


def export_tracker_csv(records: list[dict]) -> bytes:
    buf = io.StringIO()
    wr = csv.writer(buf)
    wr.writerow(["id", "book_title", "book_slug", "pack_code", "product_type", "status", "uploaded_date", "tpt_url", "tpt_listing_id", "notes", "updated_at"])
    for r in records:
        if not isinstance(r, dict):
            continue
        wr.writerow([
            r.get("id"), r.get("book_title"), r.get("book_slug"), r.get("pack_code"),
            r.get("product_type"), r.get("status"), r.get("uploaded_date"),
            r.get("tpt_url"), r.get("tpt_listing_id"),
            (r.get("notes") or "").replace("\n", " ").strip(),
            r.get("updated_at"),
        ])
    return buf.getvalue().encode("utf-8-sig")
