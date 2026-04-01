import json
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.backup_sync import persist_backup_snapshot
from backend.routers.security import RequestActor, get_request_actor, require_roles

router = APIRouter()


class AtoRate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    country: str
    daily_rate_aud: float
    breakfast_aud: float
    lunch_aud: float
    dinner_aud: float
    incidental_midpoint_aud: float = 0.0
    tax_year: str
    active: bool = True


class AtoRateUpdate(BaseModel):
    daily_rate_aud: float | None = None
    breakfast_aud: float | None = None
    lunch_aud: float | None = None
    dinner_aud: float | None = None
    incidental_midpoint_aud: float | None = None
    tax_year: str | None = None
    active: bool | None = None


# Option 1: fixed in-app table (editable later)
_ATO_RATES: list[AtoRate] = [
    AtoRate(
        country="Australia",
        daily_rate_aud=120,
        breakfast_aud=24,
        lunch_aud=36,
        dinner_aud=60,
        incidental_midpoint_aud=0.0,
        tax_year="2025-26",
    ),
    AtoRate(
        country="Papua New Guinea",
        daily_rate_aud=180,
        breakfast_aud=36,
        lunch_aud=54,
        dinner_aud=90,
        incidental_midpoint_aud=0.0,
        tax_year="2025-26",
    ),
    AtoRate(
        country="Fiji",
        daily_rate_aud=170,
        breakfast_aud=34,
        lunch_aud=51,
        dinner_aud=85,
        incidental_midpoint_aud=0.0,
        tax_year="2025-26",
    ),
    AtoRate(
        country="Solomon Islands",
        daily_rate_aud=165,
        breakfast_aud=33,
        lunch_aud=49.5,
        dinner_aud=82.5,
        incidental_midpoint_aud=0.0,
        tax_year="2025-26",
    ),
    AtoRate(
        country="Samoa",
        daily_rate_aud=160,
        breakfast_aud=32,
        lunch_aud=48,
        dinner_aud=80,
        incidental_midpoint_aud=0.0,
        tax_year="2025-26",
    ),
    AtoRate(
        country="New Caledonia",
        daily_rate_aud=175,
        breakfast_aud=35,
        lunch_aud=52.5,
        dinner_aud=87.5,
        incidental_midpoint_aud=0.0,
        tax_year="2025-26",
    ),
]


_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_ATO_RATES_CACHE_FILE = _DATA_DIR / "ato_rates.json"


def _load_local_ato_rates() -> list[AtoRate]:
    if not _ATO_RATES_CACHE_FILE.exists():
        return _ATO_RATES
    try:
        rows = json.loads(_ATO_RATES_CACHE_FILE.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            return _ATO_RATES
        migrated_rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            daily = float(row.get("daily_rate_aud") or 0)
            if "breakfast_aud" not in row and "breakfast_pct" in row:
                pct = float(row.get("breakfast_pct") or 0)
                row["breakfast_aud"] = round(daily * pct if pct <= 1 else pct, 2)
            if "lunch_aud" not in row and "lunch_pct" in row:
                pct = float(row.get("lunch_pct") or 0)
                row["lunch_aud"] = round(daily * pct if pct <= 1 else pct, 2)
            if "dinner_aud" not in row and "dinner_pct" in row:
                pct = float(row.get("dinner_pct") or 0)
                row["dinner_aud"] = round(daily * pct if pct <= 1 else pct, 2)
            row.pop("breakfast_pct", None)
            row.pop("lunch_pct", None)
            row.pop("dinner_pct", None)
            migrated_rows.append(row)

        loaded = [AtoRate(**row) for row in migrated_rows]
        return loaded or _ATO_RATES
    except Exception:
        return _ATO_RATES


def _save_local_ato_rates() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = [rate.model_dump(mode="json") for rate in _ATO_RATES]
    _ATO_RATES_CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    persist_backup_snapshot("ato_rates", payload)


_ATO_RATES = _load_local_ato_rates()


@router.get("")
def list_ato_rates() -> list[AtoRate]:
    return _ATO_RATES


@router.put("/{rate_id}")
def update_ato_rate(
    rate_id: UUID,
    payload: AtoRateUpdate,
    actor: RequestActor = Depends(get_request_actor),
) -> AtoRate:
    require_roles(actor, {"admin", "finance"})
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="No update fields were provided.")

    for idx, rate in enumerate(_ATO_RATES):
        if rate.id == rate_id:
            updated = rate.model_copy(update=updates)
            _ATO_RATES[idx] = updated
            _save_local_ato_rates()
            return updated

    raise HTTPException(status_code=404, detail="ATO rate not found")


def get_daily_rate_for_country(country: str) -> float:
    for rate in _ATO_RATES:
        if rate.active and rate.country == country:
            return rate.daily_rate_aud
    return 0.0


def get_incidental_midpoint_for_country(country: str) -> float:
    for rate in _ATO_RATES:
        if rate.active and rate.country == country:
            return rate.incidental_midpoint_aud
    return 0.0
