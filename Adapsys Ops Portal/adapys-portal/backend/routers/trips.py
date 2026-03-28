from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from supabase import Client, create_client

from backend.backup_sync import persist_backup_snapshot
from backend.routers.ato_rates import get_daily_rate_for_country
from backend.routers.security import RequestActor, get_request_actor, require_roles

router = APIRouter()


def _get_supabase() -> Client | None:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


class TripCreate(BaseModel):
    name: str
    consultant_email: str | None = None
    assigned_consultants: list[str] = Field(default_factory=list)
    client_name: str
    program_name: str
    project_start_date: date | None = None
    project_end_date: date | None = None
    destination_country: str
    destination_city: str | None = None
    departure_date: date | None = None
    return_date: date | None = None


class TripOut(TripCreate):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    nights: int
    per_diem_rate_daily: float
    per_diem_total: float
    per_diem_adjusted: float
    status: str = "draft"


_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TRIPS_CACHE_FILE = _DATA_DIR / "trips.json"


def _load_local_trips() -> list["TripOut"]:
    if not _TRIPS_CACHE_FILE.exists():
        return []
    try:
        rows = json.loads(_TRIPS_CACHE_FILE.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            return []
        return [TripOut(**row) for row in rows]
    except Exception:
        return []


def _save_local_trips() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = [trip.model_dump(mode="json") for trip in _TRIPS]
    _TRIPS_CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    persist_backup_snapshot("trips", payload)


_TRIPS: list[TripOut] = _load_local_trips()


class TripUpdate(BaseModel):
    name: str | None = None
    consultant_email: str | None = None
    assigned_consultants: list[str] | None = None
    client_name: str | None = None
    program_name: str | None = None
    project_start_date: date | None = None
    project_end_date: date | None = None
    destination_country: str | None = None
    destination_city: str | None = None
    departure_date: date | None = None
    return_date: date | None = None


@router.get("")
def list_trips() -> list[TripOut]:
    supabase = _get_supabase()
    if supabase is not None:
        try:
            response = supabase.table("trips").select("*").execute()
            return [TripOut(**row) for row in (response.data or [])]
        except Exception:
            return _TRIPS
    return _TRIPS


@router.post("")
def create_trip(payload: TripCreate, actor: RequestActor = Depends(get_request_actor)) -> TripOut:
    require_roles(actor, {"admin", "finance"})

    if payload.project_start_date and payload.project_end_date:
        if payload.project_end_date < payload.project_start_date:
            raise HTTPException(status_code=422, detail="Project end date cannot be before start date.")

    lead_email = (payload.consultant_email or "").strip().lower()
    roster = list(
        dict.fromkeys(
            [
                email.strip().lower()
                for email in [lead_email, *payload.assigned_consultants]
                if email and email.strip()
            ]
        )
    )
    if not roster:
        raise HTTPException(
            status_code=422,
            detail="At least one consultant is required in the assigned roster.",
        )

    resolved_lead = lead_email or roster[0]
    resolved_departure = payload.departure_date or payload.project_start_date
    resolved_return = payload.return_date or payload.project_end_date

    if resolved_departure and resolved_return:
        nights = max((resolved_return - resolved_departure).days, 0)
    else:
        nights = 0
    daily_rate = get_daily_rate_for_country(payload.destination_country)
    per_diem_total = round(daily_rate * nights, 2)
    trip_data = payload.model_dump()
    trip_data["departure_date"] = resolved_departure
    trip_data["return_date"] = resolved_return
    trip_data["consultant_email"] = resolved_lead
    trip_data["assigned_consultants"] = roster
    trip_data["nights"] = nights
    trip_data["per_diem_rate_daily"] = daily_rate
    trip_data["per_diem_total"] = per_diem_total
    trip_data["per_diem_adjusted"] = per_diem_total
    trip = TripOut(**trip_data)

    supabase = _get_supabase()
    if supabase is not None:
        try:
            response = supabase.table("trips").insert(trip.model_dump(mode="json")).execute()
            if response.data:
                return TripOut(**response.data[0])
        except Exception:
            pass

    _TRIPS.append(trip)
    _save_local_trips()
    return trip


@router.put("/{trip_id}")
def update_trip(
    trip_id: UUID,
    payload: TripUpdate,
    actor: RequestActor = Depends(get_request_actor),
) -> TripOut:
    require_roles(actor, {"admin", "finance"})

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="No update fields were provided.")

    supabase = _get_supabase()
    existing_trip: TripOut | None = None

    if supabase is not None:
        found = supabase.table("trips").select("*").eq("id", str(trip_id)).limit(1).execute()
        rows = found.data or []
        if not rows:
            raise HTTPException(status_code=404, detail="Trip not found")
        existing_trip = TripOut(**rows[0])
    else:
        existing_trip = next((trip for trip in _TRIPS if trip.id == trip_id), None)
        if existing_trip is None:
            raise HTTPException(status_code=404, detail="Trip not found")

    merged = existing_trip.model_dump()
    merged.update(updates)

    if merged.get("project_start_date") and merged.get("project_end_date"):
        if merged["project_end_date"] < merged["project_start_date"]:
            raise HTTPException(status_code=422, detail="Project end date cannot be before start date.")

    lead_email = str(merged.get("consultant_email") or "").strip().lower()
    assigned = [str(email).strip().lower() for email in (merged.get("assigned_consultants") or []) if str(email).strip()]
    roster = list(dict.fromkeys([lead_email, *assigned])) if lead_email else list(dict.fromkeys(assigned))
    if not roster:
        raise HTTPException(
            status_code=422,
            detail="At least one consultant is required in the assigned roster.",
        )

    resolved_lead = lead_email or roster[0]
    resolved_departure = merged.get("departure_date") or merged.get("project_start_date")
    resolved_return = merged.get("return_date") or merged.get("project_end_date")

    if resolved_departure and resolved_return:
        nights = max((resolved_return - resolved_departure).days, 0)
    else:
        nights = 0

    destination_country = merged.get("destination_country")
    if not destination_country:
        raise HTTPException(status_code=422, detail="destination_country is required.")

    daily_rate = get_daily_rate_for_country(destination_country)
    per_diem_total = round(daily_rate * nights, 2)

    merged["consultant_email"] = resolved_lead
    merged["assigned_consultants"] = roster
    merged["departure_date"] = resolved_departure
    merged["return_date"] = resolved_return
    merged["nights"] = nights
    merged["per_diem_rate_daily"] = daily_rate
    merged["per_diem_total"] = per_diem_total
    merged["per_diem_adjusted"] = per_diem_total

    updated_trip = TripOut(**merged)

    if supabase is not None:
        response = (
            supabase.table("trips")
            .update(updated_trip.model_dump(mode="json"))
            .eq("id", str(trip_id))
            .execute()
        )
        if response.data:
            return TripOut(**response.data[0])

    for idx, trip in enumerate(_TRIPS):
        if trip.id == trip_id:
            _TRIPS[idx] = updated_trip
            _save_local_trips()
            return updated_trip

    _TRIPS.append(updated_trip)
    _save_local_trips()
    return updated_trip
