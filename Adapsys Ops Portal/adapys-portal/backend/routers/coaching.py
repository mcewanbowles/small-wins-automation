from datetime import date, datetime
import json
import os
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from supabase import Client, create_client

from backend.backup_sync import persist_backup_snapshot
from backend.routers.security import RequestActor, get_request_actor, require_roles

router = APIRouter()


class EngagementCreate(BaseModel):
    name: str
    job_title: str | None = None
    client_org: str
    coach_email: str
    total_sessions: int = 5
    sessions_used: int = 0
    lcp_debrief_enabled: bool = False
    lcp_debrief_total_sessions: int = 0
    lcp_debrief_sessions_used: int = 0
    session_rate: float | None = None
    associate_cost_per_session: float | None = None
    contract_start: date | None = None
    contract_end: date | None = None


class EngagementOut(EngagementCreate):
    id: UUID = Field(default_factory=uuid4)
    status: str = "active"


class SessionCreate(BaseModel):
    engagement_id: UUID
    session_date: date
    session_type: str  # completed | no_show_chargeable | cancelled | postponed
    lcp_debrief: bool = False
    lcp_debrief_date: date | None = None
    duration_mins: int = 60
    delivery_mode: str = "video"
    invoiced_to_adapsys: bool = False
    associate_cost_per_session: float | None = None
    associate_cost_amount: float | None = None
    associate_claim_ref: str | None = None
    associate_claimed_at: str | None = None
    notes: str | None = None


class SessionOut(SessionCreate):
    id: UUID = Field(default_factory=uuid4)


class AssociateSessionClaimRequest(BaseModel):
    session_ids: list[UUID]
    claim_ref: str


class AssociateSessionClaimResult(BaseModel):
    claim_ref: str
    claimed: int


class EngagementBulkCreate(BaseModel):
    items: list[EngagementCreate]


_ENGAGEMENTS: list[EngagementOut] = []
_SESSIONS: list[SessionOut] = []

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_ENGAGEMENTS_CACHE_FILE = _DATA_DIR / "coaching_engagements.json"
_SESSIONS_CACHE_FILE = _DATA_DIR / "coaching_sessions.json"
_ENGAGEMENTS_BACKUP_FILE = _DATA_DIR / "coaching_engagements.latest.bak.json"
_SESSIONS_BACKUP_FILE = _DATA_DIR / "coaching_sessions.latest.bak.json"


def _get_supabase() -> Client | None:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


def _load_local_cache() -> None:
    global _ENGAGEMENTS, _SESSIONS
    try:
        if _ENGAGEMENTS_CACHE_FILE.exists():
            engagement_rows = json.loads(_ENGAGEMENTS_CACHE_FILE.read_text(encoding="utf-8"))
            if isinstance(engagement_rows, list):
                _ENGAGEMENTS = [EngagementOut(**row) for row in engagement_rows]
    except Exception:
        pass

    try:
        if _SESSIONS_CACHE_FILE.exists():
            session_rows = json.loads(_SESSIONS_CACHE_FILE.read_text(encoding="utf-8"))
            if isinstance(session_rows, list):
                _SESSIONS = [SessionOut(**row) for row in session_rows]
    except Exception:
        pass


def _save_local_cache() -> None:
    engagements_to_store = list(_ENGAGEMENTS)
    sessions_to_store = list(_SESSIONS)

    supabase = _get_supabase()
    if supabase is not None:
        try:
            engagement_rows = supabase.table("engagements").select("*").execute().data or []
            session_rows = supabase.table("sessions").select("*").execute().data or []
            engagements_to_store = [EngagementOut(**row) for row in engagement_rows]
            sessions_to_store = [SessionOut(**row) for row in session_rows]
        except Exception:
            # Keep local in-memory fallback if Supabase is temporarily unavailable.
            pass

    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    engagements_json = json.dumps([row.model_dump(mode="json") for row in engagements_to_store], indent=2)
    sessions_json = json.dumps([row.model_dump(mode="json") for row in sessions_to_store], indent=2)

    _ENGAGEMENTS_CACHE_FILE.write_text(engagements_json, encoding="utf-8")
    _SESSIONS_CACHE_FILE.write_text(sessions_json, encoding="utf-8")
    _ENGAGEMENTS_BACKUP_FILE.write_text(engagements_json, encoding="utf-8")
    _SESSIONS_BACKUP_FILE.write_text(sessions_json, encoding="utf-8")
    persist_backup_snapshot(
        "coaching_engagements",
        [row.model_dump(mode="json") for row in engagements_to_store],
    )
    persist_backup_snapshot(
        "coaching_sessions",
        [row.model_dump(mode="json") for row in sessions_to_store],
    )


def _list_engagements_source() -> list[EngagementOut]:
    supabase = _get_supabase()
    if supabase is not None:
        response = supabase.table("engagements").select("*").execute()
        return [EngagementOut(**row) for row in (response.data or [])]
    return _ENGAGEMENTS


def _list_sessions_source() -> list[SessionOut]:
    supabase = _get_supabase()
    if supabase is not None:
        response = supabase.table("sessions").select("*").execute()
        return [SessionOut(**row) for row in (response.data or [])]
    return _SESSIONS


def list_all_engagements_for_reports() -> list[EngagementOut]:
    return _list_engagements_source()


def list_all_sessions_for_reports() -> list[SessionOut]:
    return _list_sessions_source()


def _is_chargeable_session(session_type: str) -> bool:
    return session_type in {"completed", "no_show_chargeable"}


def _normalize_text(value: str | None) -> str:
    return str(value or "").strip().lower()


def _engagement_identity(payload: EngagementCreate | EngagementOut) -> tuple:
    return (
        _normalize_text(payload.name),
        _normalize_text(payload.client_org),
        _normalize_text(payload.coach_email),
        _normalize_text(payload.job_title),
        int(payload.total_sessions or 0),
        int(payload.sessions_used or 0),
        bool(payload.lcp_debrief_enabled),
        int(payload.lcp_debrief_total_sessions or 0),
        int(payload.lcp_debrief_sessions_used or 0),
        str(payload.contract_start or ""),
        str(payload.contract_end or ""),
    )


def _existing_engagement_identity_set(rows: list[EngagementOut]) -> set[tuple]:
    return {
        _engagement_identity(row)
        for row in rows
        if _normalize_text(getattr(row, "status", "active")) != "archived"
    }


def _apply_engagement_counter_delta(engagement_id: UUID, field: str, delta: int, supabase: Client | None) -> None:
    if delta == 0:
        return

    if supabase is not None:
        engagement = next((row for row in _list_engagements_source() if row.id == engagement_id), None)
        if engagement is None:
            return
        next_used = max(0, int(getattr(engagement, field, 0) or 0) + delta)
        supabase.table("engagements").update({field: next_used}).eq("id", str(engagement_id)).execute()
        return

    for idx, row in enumerate(_ENGAGEMENTS):
        if row.id != engagement_id:
            continue
        next_used = max(0, int(getattr(row, field, 0) or 0) + delta)
        _ENGAGEMENTS[idx] = row.model_copy(update={field: next_used})
        break


def _apply_sessions_used_delta(engagement_id: UUID, delta: int, supabase: Client | None) -> None:
    _apply_engagement_counter_delta(engagement_id, "sessions_used", delta, supabase)


def _apply_lcp_sessions_used_delta(engagement_id: UUID, delta: int, supabase: Client | None) -> None:
    _apply_engagement_counter_delta(engagement_id, "lcp_debrief_sessions_used", delta, supabase)


def _validate_engagement_payload(payload: EngagementCreate) -> None:
    total_sessions = int(payload.total_sessions or 0)
    sessions_used = int(payload.sessions_used or 0)
    if total_sessions <= 0:
        raise HTTPException(status_code=422, detail="total_sessions must be 1 or greater")
    if sessions_used < 0:
        raise HTTPException(status_code=422, detail="sessions_used must be 0 or greater")
    if sessions_used > total_sessions:
        raise HTTPException(status_code=422, detail="sessions_used cannot be greater than total_sessions")

    if bool(payload.lcp_debrief_enabled):
        lcp_total = int(payload.lcp_debrief_total_sessions or 0)
        lcp_used = int(payload.lcp_debrief_sessions_used or 0)
        if lcp_total < 0:
            raise HTTPException(status_code=422, detail="lcp_debrief_total_sessions must be 0 or greater")
        if lcp_used < 0:
            raise HTTPException(status_code=422, detail="lcp_debrief_sessions_used must be 0 or greater")
        if lcp_used > lcp_total:
            raise HTTPException(
                status_code=422,
                detail="lcp_debrief_sessions_used cannot be greater than lcp_debrief_total_sessions",
            )
    else:
        if int(payload.lcp_debrief_total_sessions or 0) != 0 or int(payload.lcp_debrief_sessions_used or 0) != 0:
            raise HTTPException(
                status_code=422,
                detail="LCP sessions must be 0 when lcp_debrief_enabled is false",
            )

    if payload.associate_cost_per_session is not None and float(payload.associate_cost_per_session) < 0:
        raise HTTPException(status_code=422, detail="associate_cost_per_session cannot be negative")


def _validate_session_payload(payload: SessionCreate) -> None:
    session_type = str(payload.session_type or "").strip().lower()
    if not session_type:
        raise HTTPException(status_code=422, detail="session_type is required")
    if bool(payload.lcp_debrief) and payload.lcp_debrief_date is None:
        raise HTTPException(status_code=422, detail="lcp_debrief_date is required when lcp_debrief is true")
    duration = int(payload.duration_mins or 0)
    if duration <= 0:
        raise HTTPException(status_code=422, detail="duration_mins must be 1 or greater")

    if payload.associate_cost_per_session is not None and float(payload.associate_cost_per_session) < 0:
        raise HTTPException(status_code=422, detail="associate_cost_per_session cannot be negative")
    if payload.associate_cost_amount is not None and float(payload.associate_cost_amount) < 0:
        raise HTTPException(status_code=422, detail="associate_cost_amount cannot be negative")


def _safe_supabase_insert(table: str, payload: dict, drop_fields: set[str]) -> dict | None:
    supabase = _get_supabase()
    if supabase is None:
        return None
    try:
        response = supabase.table(table).insert(payload).execute()
        return (response.data or [None])[0]
    except Exception:
        cleaned = dict(payload)
        for field in drop_fields:
            cleaned.pop(field, None)
        try:
            response = supabase.table(table).insert(cleaned).execute()
            return (response.data or [None])[0]
        except Exception:
            return None


def _safe_supabase_update(table: str, row_id: UUID, payload: dict, drop_fields: set[str]) -> dict | None:
    supabase = _get_supabase()
    if supabase is None:
        return None
    try:
        response = supabase.table(table).update(payload).eq("id", str(row_id)).execute()
        return (response.data or [None])[0]
    except Exception:
        cleaned = dict(payload)
        for field in drop_fields:
            cleaned.pop(field, None)
        try:
            response = supabase.table(table).update(cleaned).eq("id", str(row_id)).execute()
            return (response.data or [None])[0]
        except Exception:
            return None


_load_local_cache()


@router.get("/engagements")
def list_engagements(actor: RequestActor = Depends(get_request_actor)) -> list[EngagementOut]:
    if actor.role == "client_viewer":
        raise HTTPException(status_code=403, detail="Client viewer access is restricted to client report endpoints")
    rows = _list_engagements_source()
    if actor.role == "consultant":
        return [row for row in rows if row.coach_email.strip().lower() == actor.email]
    return rows


@router.post("/engagements")
def create_engagement(
    payload: EngagementCreate,
    actor: RequestActor = Depends(get_request_actor),
) -> EngagementOut:
    require_roles(actor, {"admin", "finance"})

    _validate_engagement_payload(payload)

    existing_rows = _list_engagements_source()
    target_identity = _engagement_identity(payload)
    existing_match = next(
        (
            row
            for row in existing_rows
            if _engagement_identity(row) == target_identity and _normalize_text(getattr(row, "status", "active")) != "archived"
        ),
        None,
    )
    if existing_match is not None:
        return existing_match

    engagement = EngagementOut(**payload.model_dump())
    supabase = _get_supabase()
    if supabase is not None:
        inserted = _safe_supabase_insert(
            "engagements",
            engagement.model_dump(mode="json"),
            {"associate_cost_per_session"},
        )
        if inserted:
            _save_local_cache()
            return EngagementOut(**inserted)
    _ENGAGEMENTS.append(engagement)
    _save_local_cache()
    return engagement


@router.put("/engagements/{engagement_id}")
def update_engagement(
    engagement_id: UUID,
    payload: EngagementCreate,
    actor: RequestActor = Depends(get_request_actor),
) -> EngagementOut:
    if actor.role not in {"admin", "finance", "consultant"}:
        raise HTTPException(status_code=403, detail="Access denied")

    current = next((row for row in _list_engagements_source() if row.id == engagement_id), None)
    if current is None:
        raise HTTPException(status_code=404, detail="Engagement not found")

    if actor.role == "consultant":
        actor_email = actor.email.strip().lower()
        if current.coach_email.strip().lower() != actor_email or payload.coach_email.strip().lower() != actor_email:
            raise HTTPException(status_code=403, detail="Consultants can only edit their own engagements")
        if payload.associate_cost_per_session != current.associate_cost_per_session:
            raise HTTPException(status_code=403, detail="Consultants cannot change associate cost defaults")

    _validate_engagement_payload(payload)

    updated = current.model_copy(update=payload.model_dump())
    supabase = _get_supabase()
    if supabase is not None:
        updated_row = _safe_supabase_update(
            "engagements",
            engagement_id,
            updated.model_dump(mode="json", exclude={"id"}),
            {"associate_cost_per_session"},
        )
        if updated_row:
            _save_local_cache()
            return EngagementOut(**updated_row)
        _save_local_cache()
        return updated

    for idx, row in enumerate(_ENGAGEMENTS):
        if row.id == engagement_id:
            _ENGAGEMENTS[idx] = updated
            _save_local_cache()
            return updated

    raise HTTPException(status_code=404, detail="Engagement not found")


@router.post("/engagements/bulk")
def bulk_create_engagements(
    payload: EngagementBulkCreate,
    actor: RequestActor = Depends(get_request_actor),
) -> list[EngagementOut]:
    require_roles(actor, {"admin", "finance"})
    if not payload.items:
        raise HTTPException(status_code=422, detail="Provide at least one engagement item")

    for item in payload.items:
        _validate_engagement_payload(item)

    existing_identities = _existing_engagement_identity_set(_list_engagements_source())
    items_to_create: list[EngagementCreate] = []
    for item in payload.items:
        identity = _engagement_identity(item)
        if identity in existing_identities:
            continue
        existing_identities.add(identity)
        items_to_create.append(item)

    if not items_to_create:
        return []

    created: list[EngagementOut] = [EngagementOut(**item.model_dump()) for item in items_to_create]

    supabase = _get_supabase()
    if supabase is not None:
        try:
            response = (
                supabase.table("engagements").insert([row.model_dump(mode="json") for row in created]).execute()
            )
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Bulk engagement upload failed: {exc}")
        if response.data:
            _save_local_cache()
            return [EngagementOut(**row) for row in response.data]
        _save_local_cache()
        return created

    _ENGAGEMENTS.extend(created)
    _save_local_cache()
    return created


@router.delete("/engagements/{engagement_id}")
def delete_engagement(
    engagement_id: UUID,
    actor: RequestActor = Depends(get_request_actor),
) -> dict:
    require_roles(actor, {"admin", "finance"})

    supabase = _get_supabase()
    if supabase is not None:
      try:
          # Remove linked sessions first to avoid dangling foreign references.
          supabase.table("sessions").delete().eq("engagement_id", str(engagement_id)).execute()
          response = supabase.table("engagements").delete().eq("id", str(engagement_id)).execute()
      except Exception as exc:
          raise HTTPException(status_code=422, detail=f"Delete engagement failed: {exc}")

      if not response.data:
          raise HTTPException(status_code=404, detail="Engagement not found")

      _save_local_cache()
      return {"deleted": True, "engagement_id": str(engagement_id)}

    global _ENGAGEMENTS, _SESSIONS
    before = len(_ENGAGEMENTS)
    _ENGAGEMENTS = [row for row in _ENGAGEMENTS if row.id != engagement_id]
    _SESSIONS = [row for row in _SESSIONS if row.engagement_id != engagement_id]
    if len(_ENGAGEMENTS) == before:
        raise HTTPException(status_code=404, detail="Engagement not found")

    _save_local_cache()
    return {"deleted": True, "engagement_id": str(engagement_id)}


@router.get("/sessions")
def list_sessions(actor: RequestActor = Depends(get_request_actor)) -> list[SessionOut]:
    if actor.role == "client_viewer":
        raise HTTPException(status_code=403, detail="Client viewer access is restricted to client report endpoints")
    sessions = _list_sessions_source()
    if actor.role != "consultant":
        return sessions

    consultant_engagement_ids = {
        row.id for row in _list_engagements_source() if row.coach_email.strip().lower() == actor.email
    }
    return [row for row in sessions if row.engagement_id in consultant_engagement_ids]


@router.post("/sessions")
def log_session(
    payload: SessionCreate,
    actor: RequestActor = Depends(get_request_actor),
) -> SessionOut:
    if actor.role not in {"admin", "finance", "consultant"}:
        raise HTTPException(status_code=403, detail="Access denied")

    _validate_session_payload(payload)

    engagement = next(
        (row for row in _list_engagements_source() if row.id == payload.engagement_id),
        None,
    )
    if engagement is None:
        raise HTTPException(status_code=404, detail="Engagement not found")

    if actor.role == "consultant" and engagement.coach_email.strip().lower() != actor.email:
        raise HTTPException(status_code=403, detail="Consultants can only log sessions for their own engagements")
    if payload.lcp_debrief and not bool(engagement.lcp_debrief_enabled):
        raise HTTPException(status_code=422, detail="This engagement does not include LCP de-brief entitlement")

    if actor.role == "consultant" and (payload.associate_claim_ref or payload.associate_claimed_at):
        raise HTTPException(status_code=403, detail="Consultants cannot set claim reference fields")

    if _is_chargeable_session(payload.session_type):
        current_used = int(getattr(engagement, "sessions_used", 0) or 0)
        entitled = int(getattr(engagement, "total_sessions", 0) or 0)
        if entitled > 0 and current_used >= entitled:
            raise HTTPException(status_code=422, detail="This engagement has no remaining sessions available")

    if payload.lcp_debrief:
        current_lcp_used = int(getattr(engagement, "lcp_debrief_sessions_used", 0) or 0)
        lcp_entitled = int(getattr(engagement, "lcp_debrief_total_sessions", 0) or 0)
        if current_lcp_used >= lcp_entitled:
            raise HTTPException(status_code=422, detail="This engagement has no remaining LCP sessions available")

    session_payload = payload.model_dump()
    if actor.role in {"admin", "finance"} and payload.associate_cost_per_session is not None:
        cost_per_session = float(payload.associate_cost_per_session)
    else:
        cost_per_session = float(engagement.associate_cost_per_session or 0)
    session_payload["associate_cost_per_session"] = cost_per_session
    session_payload["associate_cost_amount"] = float(payload.associate_cost_amount) if payload.associate_cost_amount is not None else cost_per_session
    session_payload["associate_claim_ref"] = None
    session_payload["associate_claimed_at"] = None
    session = SessionOut(**session_payload)
    supabase = _get_supabase()
    if supabase is not None:
        inserted = _safe_supabase_insert(
            "sessions",
            session.model_dump(mode="json"),
            {"associate_cost_per_session", "associate_cost_amount", "associate_claim_ref", "associate_claimed_at"},
        )
        if inserted:
            session = SessionOut(**inserted)
    _SESSIONS.append(session)

    if _is_chargeable_session(payload.session_type):
        _apply_sessions_used_delta(payload.engagement_id, 1, supabase)
    if payload.lcp_debrief:
        _apply_lcp_sessions_used_delta(payload.engagement_id, 1, supabase)

    _save_local_cache()

    return session


@router.put("/sessions/{session_id}")
def update_session(
    session_id: UUID,
    payload: SessionCreate,
    actor: RequestActor = Depends(get_request_actor),
) -> SessionOut:
    if actor.role not in {"admin", "finance", "consultant"}:
        raise HTTPException(status_code=403, detail="Access denied")

    _validate_session_payload(payload)

    sessions = _list_sessions_source()
    current_session = next((row for row in sessions if row.id == session_id), None)
    if current_session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    source_engagement = next(
        (row for row in _list_engagements_source() if row.id == current_session.engagement_id),
        None,
    )
    target_engagement = next(
        (row for row in _list_engagements_source() if row.id == payload.engagement_id),
        None,
    )
    if source_engagement is None or target_engagement is None:
        raise HTTPException(status_code=404, detail="Engagement not found")
    if payload.lcp_debrief and not bool(target_engagement.lcp_debrief_enabled):
        raise HTTPException(status_code=422, detail="Target engagement does not include LCP de-brief entitlement")

    old_chargeable = _is_chargeable_session(current_session.session_type)
    new_chargeable = _is_chargeable_session(payload.session_type)
    old_lcp = bool(current_session.lcp_debrief)
    new_lcp = bool(payload.lcp_debrief)

    if current_session.engagement_id == payload.engagement_id:
        if new_chargeable and not old_chargeable:
            current_used = int(getattr(source_engagement, "sessions_used", 0) or 0)
            entitled = int(getattr(source_engagement, "total_sessions", 0) or 0)
            if entitled > 0 and current_used >= entitled:
                raise HTTPException(status_code=422, detail="This engagement has no remaining sessions available")
        if new_lcp and not old_lcp:
            current_lcp_used = int(getattr(source_engagement, "lcp_debrief_sessions_used", 0) or 0)
            lcp_entitled = int(getattr(source_engagement, "lcp_debrief_total_sessions", 0) or 0)
            if current_lcp_used >= lcp_entitled:
                raise HTTPException(status_code=422, detail="This engagement has no remaining LCP sessions available")
    else:
        if new_chargeable:
            current_used = int(getattr(target_engagement, "sessions_used", 0) or 0)
            entitled = int(getattr(target_engagement, "total_sessions", 0) or 0)
            if entitled > 0 and current_used >= entitled:
                raise HTTPException(status_code=422, detail="Target engagement has no remaining sessions available")
        if new_lcp:
            current_lcp_used = int(getattr(target_engagement, "lcp_debrief_sessions_used", 0) or 0)
            lcp_entitled = int(getattr(target_engagement, "lcp_debrief_total_sessions", 0) or 0)
            if current_lcp_used >= lcp_entitled:
                raise HTTPException(status_code=422, detail="Target engagement has no remaining LCP sessions available")

    if actor.role == "consultant":
        actor_email = actor.email.strip().lower()
        if source_engagement.coach_email.strip().lower() != actor_email:
            raise HTTPException(status_code=403, detail="Consultants can only edit their own sessions")
        if target_engagement.coach_email.strip().lower() != actor_email:
            raise HTTPException(status_code=403, detail="Consultants can only move sessions within their engagements")
        if payload.associate_claim_ref != current_session.associate_claim_ref or payload.associate_claimed_at != current_session.associate_claimed_at:
            raise HTTPException(status_code=403, detail="Consultants cannot change claim reference fields")

    update_payload = payload.model_dump()
    if actor.role in {"admin", "finance"} and payload.associate_cost_per_session is not None:
        cost_per_session = float(payload.associate_cost_per_session)
    else:
        cost_per_session = float(target_engagement.associate_cost_per_session or 0)
    update_payload["associate_cost_per_session"] = cost_per_session
    update_payload["associate_cost_amount"] = float(payload.associate_cost_amount) if payload.associate_cost_amount is not None else cost_per_session
    updated_session = current_session.model_copy(update=update_payload)
    supabase = _get_supabase()
    if supabase is not None:
        updated_row = _safe_supabase_update(
            "sessions",
            session_id,
            updated_session.model_dump(mode="json", exclude={"id"}),
            {"associate_cost_per_session", "associate_cost_amount", "associate_claim_ref", "associate_claimed_at"},
        )
        if updated_row:
            updated_session = SessionOut(**updated_row)
    else:
        for idx, row in enumerate(_SESSIONS):
            if row.id == session_id:
                _SESSIONS[idx] = updated_session
                break

    old_chargeable = _is_chargeable_session(current_session.session_type)
    new_chargeable = _is_chargeable_session(updated_session.session_type)
    old_lcp = bool(current_session.lcp_debrief)
    new_lcp = bool(updated_session.lcp_debrief)
    source_engagement_id = current_session.engagement_id
    target_engagement_id = updated_session.engagement_id
    if source_engagement_id == target_engagement_id:
        delta = int(new_chargeable) - int(old_chargeable)
        _apply_sessions_used_delta(source_engagement_id, delta, supabase)
        lcp_delta = int(new_lcp) - int(old_lcp)
        _apply_lcp_sessions_used_delta(source_engagement_id, lcp_delta, supabase)
    else:
        _apply_sessions_used_delta(source_engagement_id, -int(old_chargeable), supabase)
        _apply_sessions_used_delta(target_engagement_id, int(new_chargeable), supabase)
        _apply_lcp_sessions_used_delta(source_engagement_id, -int(old_lcp), supabase)
        _apply_lcp_sessions_used_delta(target_engagement_id, int(new_lcp), supabase)

    _save_local_cache()
    return updated_session


@router.post("/sessions/claim")
def claim_sessions(
    payload: AssociateSessionClaimRequest,
    actor: RequestActor = Depends(get_request_actor),
) -> AssociateSessionClaimResult:
    if actor.role not in {"admin", "finance", "consultant"}:
        raise HTTPException(status_code=403, detail="Access denied")

    claim_ref = str(payload.claim_ref or "").strip()
    if not claim_ref:
        raise HTTPException(status_code=422, detail="claim_ref is required")
    if not payload.session_ids:
        raise HTTPException(status_code=422, detail="Provide at least one session_id")

    sessions = _list_sessions_source()
    engagements = _list_engagements_source()
    engagement_by_id = {row.id: row for row in engagements}

    claimed_count = 0
    supabase = _get_supabase()
    claim_timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    for session_id in payload.session_ids:
        current = next((row for row in sessions if row.id == session_id), None)
        if current is None:
            continue
        engagement = engagement_by_id.get(current.engagement_id)
        if engagement is None:
            continue
        if actor.role == "consultant" and engagement.coach_email.strip().lower() != actor.email:
            continue
        if current.associate_claim_ref:
            continue

        updated = current.model_copy(update={"associate_claim_ref": claim_ref, "associate_claimed_at": claim_timestamp})

        if supabase is not None:
            updated_row = _safe_supabase_update(
                "sessions",
                session_id,
                {"associate_claim_ref": claim_ref, "associate_claimed_at": claim_timestamp},
                set(),
            )
            if updated_row is None:
                continue
        else:
            for idx, row in enumerate(_SESSIONS):
                if row.id == session_id:
                    _SESSIONS[idx] = updated
                    break

            else:
                continue

        claimed_count += 1

    _save_local_cache()
    return AssociateSessionClaimResult(claim_ref=claim_ref, claimed=claimed_count)


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: UUID,
    actor: RequestActor = Depends(get_request_actor),
) -> dict:
    if actor.role not in {"admin", "finance", "consultant"}:
        raise HTTPException(status_code=403, detail="Access denied")

    sessions = _list_sessions_source()
    current_session = next((row for row in sessions if row.id == session_id), None)
    if current_session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    engagement = next(
        (row for row in _list_engagements_source() if row.id == current_session.engagement_id),
        None,
    )
    if engagement is None:
        raise HTTPException(status_code=404, detail="Engagement not found")

    if actor.role == "consultant" and engagement.coach_email.strip().lower() != actor.email:
        raise HTTPException(status_code=403, detail="Consultants can only delete their own sessions")

    supabase = _get_supabase()
    if supabase is not None:
        response = supabase.table("sessions").delete().eq("id", str(session_id)).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        global _SESSIONS
        before = len(_SESSIONS)
        _SESSIONS = [row for row in _SESSIONS if row.id != session_id]
        if len(_SESSIONS) == before:
            raise HTTPException(status_code=404, detail="Session not found")

    if _is_chargeable_session(current_session.session_type):
        _apply_sessions_used_delta(current_session.engagement_id, -1, supabase)
    if current_session.lcp_debrief:
        _apply_lcp_sessions_used_delta(current_session.engagement_id, -1, supabase)

    _save_local_cache()
    return {"deleted": True, "session_id": str(session_id)}
