import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

_BASE_DIR = Path(__file__).resolve().parent
_BACKUP_DIR = _BASE_DIR / "data" / "backups"


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _post_google_backup(dataset: str, payload: Any) -> None:
    webhook_url = (os.getenv("GOOGLE_BACKUP_WEBHOOK_URL") or "").strip()
    if not webhook_url:
        return

    body = {
        "dataset": dataset,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }

    token = (os.getenv("GOOGLE_BACKUP_WEBHOOK_TOKEN") or "").strip()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Backup-Token"] = token

    timeout = float(os.getenv("GOOGLE_BACKUP_TIMEOUT_SECONDS") or "8")
    data = json.dumps(body, default=str).encode("utf-8")
    req = request.Request(webhook_url, data=data, headers=headers, method="POST")

    try:
        with request.urlopen(req, timeout=timeout):
            return
    except (error.URLError, TimeoutError, ValueError):
        return


def persist_backup_snapshot(dataset: str, payload: Any) -> None:
    """
    Writes local rolling + timestamped backups and optionally posts to a
    Google webhook endpoint (Apps Script / Cloud Function) when configured.
    """
    try:
        rendered = json.dumps(payload, indent=2, default=str)
    except Exception:
        rendered = json.dumps({"error": "Unable to serialize payload"}, indent=2)

    try:
        _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        safe_dataset = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in dataset).strip("_")
        if not safe_dataset:
            safe_dataset = "dataset"

        latest_path = _BACKUP_DIR / f"{safe_dataset}.latest.json"
        stamped_path = _BACKUP_DIR / f"{safe_dataset}.{_iso_now()}.json"

        latest_path.write_text(rendered, encoding="utf-8")
        stamped_path.write_text(rendered, encoding="utf-8")
    except Exception:
        # Local backup write should never crash business operations.
        pass

    _post_google_backup(dataset=dataset, payload=payload)
