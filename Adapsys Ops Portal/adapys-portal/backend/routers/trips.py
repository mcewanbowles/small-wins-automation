from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response
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
    program_name: str | None = None
    project_start_date: date | None = None
    project_end_date: date | None = None
    destination_country: str
    destination_city: str | None = None
    departure_date: date | None = None
    return_date: date | None = None
    expense_report_required: bool = False
    travel_booking_required: bool = False
    travel_request_status: str = "not_required"  # not_required | requested | booked | cancelled
    travel_needs_flight: bool = False
    travel_needs_accommodation: bool = False
    travel_outbound_preference: str | None = None  # arrive_by | leave_after
    travel_outbound_target_date: date | None = None
    travel_return_preference: str | None = None  # arrive_before | leave_after
    travel_return_target_date: date | None = None
    travel_admin_notes: str | None = None
    travel_booked_add_expense_prompted: bool = False


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
    expense_report_required: bool | None = None
    travel_booking_required: bool | None = None
    travel_request_status: str | None = None
    travel_needs_flight: bool | None = None
    travel_needs_accommodation: bool | None = None
    travel_outbound_preference: str | None = None
    travel_outbound_target_date: date | None = None
    travel_return_preference: str | None = None
    travel_return_target_date: date | None = None
    travel_admin_notes: str | None = None
    travel_booked_add_expense_prompted: bool | None = None


class TripTravelRequestUpdate(BaseModel):
    travel_booking_required: bool = True
    travel_needs_flight: bool = False
    travel_needs_accommodation: bool = False
    travel_outbound_preference: str | None = None
    travel_outbound_target_date: date | None = None
    travel_return_preference: str | None = None
    travel_return_target_date: date | None = None
    travel_admin_notes: str | None = None


class TravelBookingQueueSummary(BaseModel):
    total_required: int = 0
    outstanding_to_book: int = 0
    booked: int = 0
    need_expense_prompt: int = 0


class TripTravelBookedResult(BaseModel):
    trip_id: UUID
    travel_request_status: str
    should_prompt_add_expense: bool
    detail: str


class BookedTravelExpenseDraftResult(BaseModel):
    trip_id: UUID
    travel_request_status: str
    travel_booked_add_expense_prompted: bool
    detail: str
    draft_payload: dict


_COUNTRY_CURRENCY_MAP = {
    "australia": "AUD",
    "new zealand": "NZD",
    "singapore": "SGD",
    "united states": "USD",
    "united states of america": "USD",
    "united kingdom": "GBP",
    "japan": "JPY",
    "canada": "CAD",
    "india": "INR",
    "indonesia": "IDR",
    "malaysia": "MYR",
    "philippines": "PHP",
    "thailand": "THB",
    "vietnam": "VND",
    "china": "CNY",
    "hong kong": "HKD",
    "united arab emirates": "AED",
    "uae": "AED",
}


def _currency_for_country(country: str | None) -> str:
    key = str(country or "").strip().lower()
    return _COUNTRY_CURRENCY_MAP.get(key, "AUD")


def _booked_travel_preferred_category(trip: TripOut) -> str:
    if bool(trip.travel_needs_flight):
        return "flights"
    if bool(trip.travel_needs_accommodation):
        return "accommodation"
    return "misc"


def _normalize_trip_travel_fields(merged: dict) -> None:
    merged["travel_request_status"] = str(merged.get("travel_request_status") or "not_required").strip().lower()
    if merged["travel_request_status"] not in {"not_required", "requested", "booked", "cancelled"}:
        raise HTTPException(status_code=422, detail="travel_request_status must be not_required, requested, booked, or cancelled")

    outbound_pref = str(merged.get("travel_outbound_preference") or "").strip().lower()
    return_pref = str(merged.get("travel_return_preference") or "").strip().lower()

    merged["travel_outbound_preference"] = outbound_pref or None
    merged["travel_return_preference"] = return_pref or None

    if merged["travel_outbound_preference"] and merged["travel_outbound_preference"] not in {"arrive_by", "leave_after"}:
        raise HTTPException(status_code=422, detail="travel_outbound_preference must be arrive_by or leave_after")
    if merged["travel_return_preference"] and merged["travel_return_preference"] not in {"arrive_before", "leave_after"}:
        raise HTTPException(status_code=422, detail="travel_return_preference must be arrive_before or leave_after")

    merged["travel_admin_notes"] = str(merged.get("travel_admin_notes") or "").strip() or None


def _trip_legacy_supabase_payload(payload: dict) -> dict:
    legacy_columns = {
        "id",
        "name",
        "consultant_email",
        "assigned_consultants",
        "client_name",
        "program_name",
        "project_start_date",
        "project_end_date",
        "destination_country",
        "destination_city",
        "departure_date",
        "return_date",
        "expense_report_required",
        "created_at",
        "nights",
        "per_diem_rate_daily",
        "per_diem_total",
        "per_diem_adjusted",
        "status",
    }
    return {key: value for key, value in payload.items() if key in legacy_columns}


def _find_trip_record(trip_id: UUID) -> TripOut:
    supabase = _get_supabase()
    if supabase is not None:
        found = supabase.table("trips").select("*").eq("id", str(trip_id)).limit(1).execute()
        rows = found.data or []
        if rows:
            return TripOut(**rows[0])
    existing = next((trip for trip in _TRIPS if trip.id == trip_id), None)
    if existing is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return existing


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


@router.get("/travel-booking-summary", response_model=TravelBookingQueueSummary)
def travel_booking_summary(actor: RequestActor = Depends(get_request_actor)) -> TravelBookingQueueSummary:
    require_roles(actor, {"admin", "finance"})
    trips = list_trips()
    summary = TravelBookingQueueSummary()
    for trip in trips:
        if not bool(getattr(trip, "travel_booking_required", False)):
            continue
        summary.total_required += 1
        status = str(getattr(trip, "travel_request_status", "requested") or "requested").strip().lower()
        if status == "booked":
            summary.booked += 1
            needs_prompt = bool(trip.expense_report_required) and not bool(
                getattr(trip, "travel_booked_add_expense_prompted", False)
            )
            if needs_prompt:
                summary.need_expense_prompt += 1
        elif status in {"requested", "not_required"}:
            summary.outstanding_to_book += 1
    return summary


@router.post("")
def create_trip(payload: TripCreate, actor: RequestActor = Depends(get_request_actor)) -> TripOut:
    require_roles(actor, {"admin", "finance"})

    if payload.project_start_date and payload.project_end_date:
        if payload.project_end_date < payload.project_start_date:
            raise HTTPException(status_code=422, detail="Activity end date cannot be before start date.")

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
            detail="At least one assigned consultant is required.",
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
    trip_data["program_name"] = str(payload.program_name or "").strip() or None
    trip_data["departure_date"] = resolved_departure
    trip_data["return_date"] = resolved_return
    trip_data["consultant_email"] = resolved_lead
    trip_data["assigned_consultants"] = roster
    trip_data["nights"] = nights
    trip_data["per_diem_rate_daily"] = daily_rate
    trip_data["per_diem_total"] = per_diem_total
    trip_data["per_diem_adjusted"] = per_diem_total
    _normalize_trip_travel_fields(trip_data)
    trip = TripOut(**trip_data)

    supabase = _get_supabase()
    if supabase is not None:
        supabase_payload = trip.model_dump(mode="json")
        try:
            response = supabase.table("trips").insert(supabase_payload).execute()
            if response.data:
                return TripOut(**response.data[0])
        except Exception:
            fallback_payload = _trip_legacy_supabase_payload(supabase_payload)
            try:
                response = supabase.table("trips").insert(fallback_payload).execute()
                if response.data:
                    row = dict(response.data[0])
                    row.setdefault("expense_report_required", trip.expense_report_required)
                    row.setdefault("travel_booking_required", trip.travel_booking_required)
                    row.setdefault("travel_request_status", trip.travel_request_status)
                    row.setdefault("travel_needs_flight", trip.travel_needs_flight)
                    row.setdefault("travel_needs_accommodation", trip.travel_needs_accommodation)
                    row.setdefault("travel_outbound_preference", trip.travel_outbound_preference)
                    row.setdefault("travel_outbound_target_date", trip.travel_outbound_target_date)
                    row.setdefault("travel_return_preference", trip.travel_return_preference)
                    row.setdefault("travel_return_target_date", trip.travel_return_target_date)
                    row.setdefault("travel_admin_notes", trip.travel_admin_notes)
                    row.setdefault("travel_booked_add_expense_prompted", trip.travel_booked_add_expense_prompted)
                    return TripOut(**row)
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
    require_roles(actor, {"admin", "finance", "consultant"})

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="No update fields were provided.")

    is_consultant_actor = str(actor.role or "").strip().lower() == "consultant"
    consultant_allowed_fields = {
        "travel_booking_required",
        "travel_request_status",
        "travel_needs_flight",
        "travel_needs_accommodation",
        "travel_outbound_preference",
        "travel_outbound_target_date",
        "travel_return_preference",
        "travel_return_target_date",
        "travel_admin_notes",
        "travel_booked_add_expense_prompted",
    }
    if is_consultant_actor:
        invalid_update_fields = [key for key in updates if key not in consultant_allowed_fields]
        if invalid_update_fields:
            raise HTTPException(status_code=403, detail="Consultants can only update travel-request fields.")

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

    if is_consultant_actor:
        actor_email = str(actor.email or "").strip().lower()
        trip_consultants = {
            str(existing_trip.consultant_email or "").strip().lower(),
            *[str(email or "").strip().lower() for email in (existing_trip.assigned_consultants or [])],
        }
        trip_consultants.discard("")
        if actor_email not in trip_consultants:
            raise HTTPException(status_code=403, detail="Consultant can only update their own travel requests.")

    merged = existing_trip.model_dump()
    merged.update(updates)

    if merged.get("project_start_date") and merged.get("project_end_date"):
        if merged["project_end_date"] < merged["project_start_date"]:
            raise HTTPException(status_code=422, detail="Activity end date cannot be before start date.")

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
    _normalize_trip_travel_fields(merged)

    updated_trip = TripOut(**merged)

    if supabase is not None:
        supabase_payload = updated_trip.model_dump(mode="json")
        try:
            response = (
                supabase.table("trips")
                .update(supabase_payload)
                .eq("id", str(trip_id))
                .execute()
            )
        except Exception:
            fallback_payload = _trip_legacy_supabase_payload(supabase_payload)
            response = (
                supabase.table("trips")
                .update(fallback_payload)
                .eq("id", str(trip_id))
                .execute()
            )
        if response.data:
            row = dict(response.data[0])
            row.setdefault("expense_report_required", updated_trip.expense_report_required)
            row.setdefault("travel_booking_required", updated_trip.travel_booking_required)
            row.setdefault("travel_request_status", updated_trip.travel_request_status)
            row.setdefault("travel_needs_flight", updated_trip.travel_needs_flight)
            row.setdefault("travel_needs_accommodation", updated_trip.travel_needs_accommodation)
            row.setdefault("travel_outbound_preference", updated_trip.travel_outbound_preference)
            row.setdefault("travel_outbound_target_date", updated_trip.travel_outbound_target_date)
            row.setdefault("travel_return_preference", updated_trip.travel_return_preference)
            row.setdefault("travel_return_target_date", updated_trip.travel_return_target_date)
            row.setdefault("travel_admin_notes", updated_trip.travel_admin_notes)
            row.setdefault("travel_booked_add_expense_prompted", updated_trip.travel_booked_add_expense_prompted)
            return TripOut(**row)

    for idx, trip in enumerate(_TRIPS):
        if trip.id == trip_id:
            _TRIPS[idx] = updated_trip
            _save_local_trips()
            return updated_trip

    _TRIPS.append(updated_trip)
    _save_local_trips()
    return updated_trip


@router.post("/{trip_id}/travel-request", response_model=TripOut)
def submit_trip_travel_request(
    trip_id: UUID,
    payload: TripTravelRequestUpdate,
    actor: RequestActor = Depends(get_request_actor),
) -> TripOut:
    require_roles(actor, {"admin", "finance", "consultant"})
    trip = _find_trip_record(trip_id)
    update_payload = TripUpdate(
        travel_booking_required=bool(payload.travel_booking_required),
        travel_request_status="requested" if payload.travel_booking_required else "not_required",
        travel_needs_flight=bool(payload.travel_needs_flight),
        travel_needs_accommodation=bool(payload.travel_needs_accommodation),
        travel_outbound_preference=payload.travel_outbound_preference,
        travel_outbound_target_date=payload.travel_outbound_target_date,
        travel_return_preference=payload.travel_return_preference,
        travel_return_target_date=payload.travel_return_target_date,
        travel_admin_notes=payload.travel_admin_notes,
        travel_booked_add_expense_prompted=False,
    )
    return update_trip(trip.id, update_payload, actor)


@router.post("/{trip_id}/mark-travel-booked", response_model=TripTravelBookedResult)
def mark_trip_travel_booked(
    trip_id: UUID,
    actor: RequestActor = Depends(get_request_actor),
) -> TripTravelBookedResult:
    require_roles(actor, {"admin", "finance"})
    updated = update_trip(
        trip_id,
        TripUpdate(
            travel_booking_required=True,
            travel_request_status="booked",
            travel_booked_add_expense_prompted=False,
        ),
        actor,
    )
    should_prompt = bool(updated.expense_report_required)
    detail = (
        "Travel marked as booked. Prompt admin to add booked travel costs into expense reporting."
        if should_prompt
        else "Travel marked as booked."
    )
    return TripTravelBookedResult(
        trip_id=updated.id,
        travel_request_status=str(updated.travel_request_status or "booked"),
        should_prompt_add_expense=should_prompt,
        detail=detail,
    )


@router.post("/{trip_id}/booked-travel-expense-draft", response_model=BookedTravelExpenseDraftResult)
def create_booked_travel_expense_draft(
    trip_id: UUID,
    actor: RequestActor = Depends(get_request_actor),
) -> BookedTravelExpenseDraftResult:
    require_roles(actor, {"admin", "finance"})
    trip = _find_trip_record(trip_id)

    travel_status = str(trip.travel_request_status or "not_required").strip().lower()
    if travel_status != "booked":
        raise HTTPException(
            status_code=422,
            detail="Travel must be marked booked before creating a booked-travel expense draft.",
        )

    expense_date = trip.travel_outbound_target_date or trip.departure_date or trip.project_start_date or date.today()
    outbound_pref = str(trip.travel_outbound_preference or "").strip()
    return_pref = str(trip.travel_return_preference or "").strip()
    travel_notes = str(trip.travel_admin_notes or "").strip()

    helper_lines = [
        "Booked travel helper draft",
        f"Consultant: {trip.consultant_email or 'Unknown consultant'}",
        f"Needs flight: {'Yes' if trip.travel_needs_flight else 'No'}",
        f"Needs accommodation: {'Yes' if trip.travel_needs_accommodation else 'No'}",
    ]
    if outbound_pref:
        helper_lines.append(f"Outbound preference: {outbound_pref}")
    if return_pref:
        helper_lines.append(f"Return preference: {return_pref}")
    if travel_notes:
        helper_lines.append(f"Travel notes: {travel_notes}")

    draft_payload = {
        "trip_id": str(trip.id),
        "submitted_by_role": "admin",
        "submitted_by_email": str(trip.consultant_email or "").strip().lower(),
        "expense_date": expense_date.isoformat(),
        "category": _booked_travel_preferred_category(trip),
        "currency_local": _currency_for_country(trip.destination_country),
        "exchange_rate": "1",
        "descriptor_activity": str(trip.name or "").strip(),
        "notes": "\n".join(helper_lines),
        "no_receipt": True,
        "no_receipt_reason": "Booked travel cost to be entered by admin",
    }

    updated = update_trip(
        trip.id,
        TripUpdate(travel_booked_add_expense_prompted=True),
        actor,
    )
    detail = (
        "Booked-travel expense draft generated. Review amount, supplier, and receipt details before submitting."
    )

    return BookedTravelExpenseDraftResult(
        trip_id=updated.id,
        travel_request_status=str(updated.travel_request_status or "booked"),
        travel_booked_add_expense_prompted=bool(updated.travel_booked_add_expense_prompted),
        detail=detail,
        draft_payload=draft_payload,
    )


@router.delete("/{trip_id}", status_code=204, response_class=Response, response_model=None)
def delete_trip(trip_id: UUID, actor: RequestActor = Depends(get_request_actor)) -> Response:
    require_roles(actor, {"admin", "finance"})

    from backend.routers.expenses import list_expenses

    linked_expenses = [expense for expense in list_expenses() if expense.trip_id == trip_id]
    if linked_expenses:
        raise HTTPException(
            status_code=422,
            detail=(
                "Cannot delete activity while expenses are linked to it. "
                "Move or delete linked expenses first."
            ),
        )

    supabase = _get_supabase()
    if supabase is not None:
        found = supabase.table("trips").select("id").eq("id", str(trip_id)).limit(1).execute()
        rows = found.data or []
        if not rows:
            raise HTTPException(status_code=404, detail="Trip not found")
        supabase.table("trips").delete().eq("id", str(trip_id)).execute()
        return Response(status_code=204)

    before = len(_TRIPS)
    _TRIPS[:] = [trip for trip in _TRIPS if trip.id != trip_id]
    if len(_TRIPS) == before:
        raise HTTPException(status_code=404, detail="Trip not found")
    _save_local_trips()
    return Response(status_code=204)
