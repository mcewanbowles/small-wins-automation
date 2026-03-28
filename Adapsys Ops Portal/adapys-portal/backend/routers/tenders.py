from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from supabase import Client, create_client

from backend.backup_sync import persist_backup_snapshot
from backend.routers.security import RequestActor, get_request_actor, require_roles

router = APIRouter()

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TENDERS_CACHE_FILE = _DATA_DIR / "tenders.json"


class TenderTriageIn(BaseModel):
    source: str = "manual"
    title: str
    issuer: str = ""
    location: str = ""
    summary: str = ""
    contract_value: str = ""
    tender_url: str = ""
    eoi_deadline: date | None = None
    registration_deadline: date | None = None
    mandatory_briefing_date: date | None = None
    question_deadline: date | None = None
    official_close_date: date | None = None


class TenderDecisionIn(BaseModel):
    decision: str


class TenderOut(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source: str
    title: str
    issuer: str
    location: str
    summary: str
    contract_value: str
    tender_url: str
    fit_score: int
    recommendation: str
    strategic_value: str
    go_no_go_score: int
    win_probability: int
    status: str = "new"
    lead_consultant_email: str | None = None
    consultant_interest: dict[str, str] = Field(default_factory=dict)
    eoi_deadline: date | None = None
    registration_deadline: date | None = None
    mandatory_briefing_date: date | None = None
    question_deadline: date | None = None
    official_close_date: date | None = None
    urgent: bool = False
    hidden_deadline_warning: str | None = None
    duplicate_hash: str
    previously_seen: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def _load_local_tenders() -> list[TenderOut]:
    if not _TENDERS_CACHE_FILE.exists():
        return []
    try:
        rows = json.loads(_TENDERS_CACHE_FILE.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            return []
        return [TenderOut(**row) for row in rows]
    except Exception:
        return []


def _save_local_tenders(rows: list[TenderOut] | None = None) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows_to_store = rows if rows is not None else _TENDERS
    payload = [tender.model_dump(mode="json") for tender in rows_to_store]
    _TENDERS_CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    persist_backup_snapshot("tenders", payload)


def _get_supabase() -> Client | None:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


def _list_tenders_source() -> list[TenderOut]:
    supabase = _get_supabase()
    if supabase is not None:
        try:
            response = supabase.table("tenders").select("*").execute()
            rows = [TenderOut(**row) for row in (response.data or [])]
            _save_local_tenders(rows)
            _TENDERS[:] = rows
            return rows
        except Exception:
            pass
    return list(_TENDERS)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")


def _duplicate_hash(source: str, issuer: str, title: str, official_close_date: date | None) -> str:
    raw = "|".join([
        _slug(source),
        _slug(issuer),
        _slug(title),
        str(official_close_date or ""),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _days_until(value: date | None) -> int | None:
    if value is None:
        return None
    return (value - date.today()).days


def _score_tender(payload: TenderTriageIn) -> tuple[int, str, str]:
    text = " ".join([payload.title, payload.summary, payload.issuer, payload.location]).lower()

    score = 5
    high_fit = ["leadership", "coaching", "dfat", "pacific", "capacity", "panel", "organisational development"]
    medium_fit = ["public sector", "government", "workforce", "wellbeing", "training"]
    low_fit = ["infrastructure", "equipment", "construction", "school", "curriculum", "grant"]
    au_pacific_tokens = ["australia", "australian", "au", "pacific", "png", "fiji", "samoa", "solomon", "vanuatu", "timor"]
    asia_europe_tokens = ["asia", "europe", "singapore", "indonesia", "philippines", "uk", "eu"]

    score += sum(1 for token in high_fit if token in text)
    score += sum(0.5 for token in medium_fit if token in text)
    score -= sum(1.5 for token in low_fit if token in text)
    if any(token in text for token in au_pacific_tokens):
        score += 1.5
    elif any(token in text for token in asia_europe_tokens):
        score += 0.5
    score = max(1, min(10, int(round(score))))

    if score >= 8:
        recommendation = "PURSUE"
    elif score >= 5:
        recommendation = "MONITOR"
    else:
        recommendation = "IGNORE"

    strategic_mc = ["palladium", "coffey", "tetra", "ghd", "abt", "cardno"]
    if any(mc in text for mc in strategic_mc):
        strategic_value = "High strategic value: managing contractor relationship signal."
    elif "panel" in text:
        strategic_value = "Panel opportunity: lower-effort pathway to recurring call-down work."
    elif "pacific" in text or "dfat" in text:
        strategic_value = "Strong Adapsys positioning fit in Pacific/DFAT development context."
    else:
        strategic_value = "General opportunity: review against current capacity and timelines."

    return score, recommendation, strategic_value


def _go_no_go_score(payload: TenderTriageIn, fit_score: int, strategic_value: str) -> int:
    score = 0
    if fit_score >= 7:
        score += 1
    close_days = _days_until(payload.official_close_date)
    if close_days is not None and close_days >= 10:
        score += 1
    if payload.location and any(token in payload.location.lower() for token in ["australia", "pacific", "png", "fiji", "samoa", "solomon", "timor"]):
        score += 1
    if payload.contract_value and re.search(r"\d", payload.contract_value):
        score += 1
    if "strategic" in strategic_value.lower() or "panel" in strategic_value.lower():
        score += 1
    return score


def _is_urgent(payload: TenderTriageIn) -> bool:
    windows = [
        _days_until(payload.eoi_deadline),
        _days_until(payload.registration_deadline),
        _days_until(payload.official_close_date),
    ]
    return any(days is not None and 0 <= days <= 14 for days in windows)


def _hidden_deadline_warning(payload: TenderTriageIn) -> str | None:
    if not payload.eoi_deadline or not payload.official_close_date:
        return None
    delta = (payload.official_close_date - payload.eoi_deadline).days
    if delta >= 5:
        return f"EOI closes {delta} day(s) before official close date."
    return None


_TENDERS: list[TenderOut] = _load_local_tenders()


@router.get("")
def list_tenders() -> list[TenderOut]:
    rows = _list_tenders_source()
    return sorted(rows, key=lambda row: row.updated_at, reverse=True)


@router.get("/summary")
def tender_summary() -> dict:
    rows = list_tenders()
    return {
        "total": len(rows),
        "urgent": sum(1 for row in rows if row.urgent),
        "pursue": sum(1 for row in rows if row.status == "pursue"),
        "monitor": sum(1 for row in rows if row.status == "monitor"),
        "ignore": sum(1 for row in rows if row.status == "ignore"),
        "led": sum(1 for row in rows if bool(row.lead_consultant_email)),
    }


@router.post("/triage")
def triage_tender(
    payload: TenderTriageIn,
    actor: RequestActor = Depends(get_request_actor),
) -> TenderOut:
    require_roles(actor, {"admin", "finance"})

    rows = _list_tenders_source()
    fit_score, recommendation, strategic_value = _score_tender(payload)
    duplicate_hash = _duplicate_hash(payload.source, payload.issuer, payload.title, payload.official_close_date)

    for idx, tender in enumerate(rows):
        if tender.duplicate_hash == duplicate_hash:
            updated = tender.model_copy(
                update={
                    "summary": payload.summary or tender.summary,
                    "contract_value": payload.contract_value or tender.contract_value,
                    "tender_url": payload.tender_url or tender.tender_url,
                    "eoi_deadline": payload.eoi_deadline,
                    "registration_deadline": payload.registration_deadline,
                    "mandatory_briefing_date": payload.mandatory_briefing_date,
                    "question_deadline": payload.question_deadline,
                    "official_close_date": payload.official_close_date,
                    "fit_score": fit_score,
                    "recommendation": recommendation,
                    "strategic_value": strategic_value,
                    "go_no_go_score": _go_no_go_score(payload, fit_score, strategic_value),
                    "win_probability": min(95, max(5, fit_score * 10)),
                    "urgent": _is_urgent(payload),
                    "hidden_deadline_warning": _hidden_deadline_warning(payload),
                    "previously_seen": True,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            supabase = _get_supabase()
            if supabase is not None:
                try:
                    response = (
                        supabase.table("tenders")
                        .update(updated.model_dump(mode="json"))
                        .eq("id", str(tender.id))
                        .execute()
                    )
                    if response.data:
                        persisted = TenderOut(**response.data[0])
                        rows[idx] = persisted
                        _TENDERS[:] = rows
                        _save_local_tenders(rows)
                        return persisted
                except Exception:
                    pass

            rows[idx] = updated
            _TENDERS[:] = rows
            _save_local_tenders(rows)
            return updated

    tender = TenderOut(
        source=payload.source,
        title=payload.title,
        issuer=payload.issuer,
        location=payload.location,
        summary=payload.summary,
        contract_value=payload.contract_value,
        tender_url=payload.tender_url,
        fit_score=fit_score,
        recommendation=recommendation,
        strategic_value=strategic_value,
        go_no_go_score=_go_no_go_score(payload, fit_score, strategic_value),
        win_probability=min(95, max(5, fit_score * 10)),
        status=recommendation.lower(),
        eoi_deadline=payload.eoi_deadline,
        registration_deadline=payload.registration_deadline,
        mandatory_briefing_date=payload.mandatory_briefing_date,
        question_deadline=payload.question_deadline,
        official_close_date=payload.official_close_date,
        urgent=_is_urgent(payload),
        hidden_deadline_warning=_hidden_deadline_warning(payload),
        duplicate_hash=duplicate_hash,
    )
    supabase = _get_supabase()
    if supabase is not None:
        try:
            response = supabase.table("tenders").insert(tender.model_dump(mode="json")).execute()
            if response.data:
                persisted = TenderOut(**response.data[0])
                rows.append(persisted)
                _TENDERS[:] = rows
                _save_local_tenders(rows)
                return persisted
        except Exception:
            pass

    rows.append(tender)
    _TENDERS[:] = rows
    _save_local_tenders(rows)
    return tender


@router.post("/{tender_id}/decision")
def set_tender_decision(
    tender_id: UUID,
    payload: TenderDecisionIn,
    actor: RequestActor = Depends(get_request_actor),
) -> TenderOut:
    decision = payload.decision.strip().lower()
    allowed_admin = {"pursue", "monitor", "ignore"}
    allowed_consultant = {"lead", "watching", "pass"}

    if actor.role in {"admin", "finance"}:
        if decision not in allowed_admin and decision not in allowed_consultant:
            raise HTTPException(status_code=422, detail="Unsupported decision")
    else:
        if decision not in allowed_consultant:
            raise HTTPException(status_code=403, detail="Consultants can only set lead/watching/pass")

    rows = _list_tenders_source()
    for idx, tender in enumerate(rows):
        if tender.id != tender_id:
            continue

        interest = {**tender.consultant_interest}
        updates: dict = {"updated_at": datetime.now(timezone.utc)}

        if decision in allowed_admin:
            updates["status"] = decision

        if decision == "lead":
            interest[actor.email] = "lead"
            updates["lead_consultant_email"] = actor.email
            updates["status"] = "pursue"
        elif decision in {"watching", "pass"}:
            interest[actor.email] = decision

        updates["consultant_interest"] = interest
        updated = tender.model_copy(update=updates)

        supabase = _get_supabase()
        if supabase is not None:
            try:
                response = (
                    supabase.table("tenders")
                    .update(updated.model_dump(mode="json"))
                    .eq("id", str(tender.id))
                    .execute()
                )
                if response.data:
                    persisted = TenderOut(**response.data[0])
                    rows[idx] = persisted
                    _TENDERS[:] = rows
                    _save_local_tenders(rows)
                    return persisted
            except Exception:
                pass

        rows[idx] = updated
        _TENDERS[:] = rows
        _save_local_tenders(rows)
        return updated

    raise HTTPException(status_code=404, detail="Tender not found")
