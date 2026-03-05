from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib import error, request

API_BASE_DEFAULT = "https://api-v1.tailwind.ai/v1"
DEFAULT_MANIFEST = Path("production/marketing/tailwind/tailwind_pin_manifest_ask_for_help.csv")
DEFAULT_RESULTS = Path("production/marketing/tailwind/tailwind_api_schedule_results.csv")
DEFAULT_ACCOUNT_ID = "1627745"
DEFAULT_BOARD_IDS = [
    "341007071725005189",  # Period/Menstrual Hygiene Social Stories
    "341007071725005188",  # Personal Hygiene Social Stories
    "341007071725005183",  # Life Skills Social Stories
    "341007071725005185",  # Autism Support Social Stories
]


@dataclass
class ManifestRow:
    image_path: str
    title: str
    description: str
    destination_url: str
    board: str
    template: str
    product_folder: str


class TailwindApiClient:
    def __init__(self, *, api_base: str, api_key: str) -> None:
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key

    def _request(self, *, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.api_base}{path}"
        body: bytes | None = None
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url, data=body, method=method, headers=headers)
        try:
            with request.urlopen(req, timeout=30) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data) if data else {}
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method} {url} failed ({exc.code}): {raw}") from exc

    def create_post(self, *, account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(method="POST", path=f"/accounts/{account_id}/posts", payload=payload)


def _parse_manifest(path: Path) -> list[ManifestRow]:
    rows: list[ManifestRow] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                ManifestRow(
                    image_path=(row.get("image_path") or "").strip(),
                    title=(row.get("title") or "").strip(),
                    description=(row.get("description") or "").strip(),
                    destination_url=(row.get("destination_url") or "").strip(),
                    board=(row.get("board") or "").strip(),
                    template=(row.get("template") or "").strip(),
                    product_folder=(row.get("product_folder") or "").strip(),
                )
            )
    return rows


def _resolve_media_url(*, image_path: str, media_root: Path | None, media_url_prefix: str | None) -> str | None:
    if image_path.lower().startswith(("http://", "https://")):
        return image_path

    if media_root is None or not media_url_prefix:
        return None

    try:
        img = Path(image_path)
        rel = img.resolve().relative_to(media_root.resolve())
    except Exception:
        return None

    rel_url = str(rel).replace("\\", "/")
    return f"{media_url_prefix.rstrip('/')}/{rel_url}"


def _build_send_time(*, start: datetime, index: int, pins_per_day: int) -> str:
    interval_minutes = max(1, int((24 * 60) / max(1, pins_per_day)))
    send_at = start + timedelta(minutes=index * interval_minutes)
    return send_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _board_for_row(index: int, board_ids: list[str]) -> str:
    if not board_ids:
        raise ValueError("At least one board ID is required")
    return board_ids[index % len(board_ids)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Schedule Tailwind Pinterest posts from a manifest CSV")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--results-out", default=str(DEFAULT_RESULTS))
    parser.add_argument("--account-id", default=DEFAULT_ACCOUNT_ID)
    parser.add_argument("--board-ids", default=",".join(DEFAULT_BOARD_IDS))
    parser.add_argument("--pins-per-day", type=int, default=3)
    parser.add_argument("--start-at-utc", default="", help="ISO datetime in UTC, e.g. 2026-03-06T02:00:00Z")
    parser.add_argument("--limit", type=int, default=0, help="Only schedule first N rows (0 = all)")
    parser.add_argument("--media-root", default=str(Path.cwd()))
    parser.add_argument(
        "--media-url-prefix",
        default="",
        help="Public URL prefix for locally generated pin files. Required unless image_path values are already public URLs.",
    )
    parser.add_argument("--api-base", default=API_BASE_DEFAULT)
    parser.add_argument("--live", action="store_true", help="Actually create posts in Tailwind (default is dry-run)")
    args = parser.parse_args()

    api_key = os.getenv("TAILWIND_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("TAILWIND_API_KEY is not set. Use: setx TAILWIND_API_KEY \"<key>\"")

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")

    board_ids = [x.strip() for x in str(args.board_ids).split(",") if x.strip()]
    media_root = Path(args.media_root) if str(args.media_root).strip() else None
    media_url_prefix = args.media_url_prefix.strip() or None

    rows = _parse_manifest(manifest_path)
    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    if args.start_at_utc:
        start = datetime.fromisoformat(args.start_at_utc.replace("Z", "+00:00")).astimezone(UTC)
    else:
        start = datetime.now(UTC) + timedelta(minutes=20)

    client = TailwindApiClient(api_base=args.api_base, api_key=api_key)
    results: list[dict[str, str]] = []

    for idx, row in enumerate(rows):
        media_url = _resolve_media_url(
            image_path=row.image_path,
            media_root=media_root,
            media_url_prefix=media_url_prefix,
        )
        board_id = _board_for_row(idx, board_ids)
        send_at = _build_send_time(start=start, index=idx, pins_per_day=args.pins_per_day)

        if not media_url:
            results.append(
                {
                    "index": str(idx),
                    "status": "skipped",
                    "reason": "No public media URL. Provide --media-url-prefix or use image_path URLs.",
                    "board_id": board_id,
                    "send_at": send_at,
                    "title": row.title,
                    "image_path": row.image_path,
                    "post_id": "",
                }
            )
            continue

        payload = {
            "mediaUrl": media_url,
            "title": row.title,
            "description": row.description,
            "url": row.destination_url,
            "boardId": board_id,
            "altText": row.title,
            "sendAt": send_at,
        }

        if not args.live:
            results.append(
                {
                    "index": str(idx),
                    "status": "dry_run",
                    "reason": "",
                    "board_id": board_id,
                    "send_at": send_at,
                    "title": row.title,
                    "image_path": row.image_path,
                    "post_id": "",
                }
            )
            continue

        try:
            resp = client.create_post(account_id=args.account_id, payload=payload)
            post_id = (
                str(resp.get("data", {}).get("post", {}).get("id", ""))
                if isinstance(resp, dict)
                else ""
            )
            results.append(
                {
                    "index": str(idx),
                    "status": "scheduled",
                    "reason": "",
                    "board_id": board_id,
                    "send_at": send_at,
                    "title": row.title,
                    "image_path": row.image_path,
                    "post_id": post_id,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "index": str(idx),
                    "status": "error",
                    "reason": str(exc),
                    "board_id": board_id,
                    "send_at": send_at,
                    "title": row.title,
                    "image_path": row.image_path,
                    "post_id": "",
                }
            )

    out_path = Path(args.results_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "index",
            "status",
            "reason",
            "board_id",
            "send_at",
            "title",
            "image_path",
            "post_id",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    total = len(results)
    scheduled = sum(1 for r in results if r["status"] == "scheduled")
    dry = sum(1 for r in results if r["status"] == "dry_run")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"] == "error")

    print(f"Manifest rows processed: {total}")
    print(f"Scheduled: {scheduled} | Dry run: {dry} | Skipped: {skipped} | Errors: {errors}")
    print(f"Results CSV: {out_path}")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
