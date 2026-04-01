from datetime import date, datetime, timezone
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

ADMIN_ONLY_CATEGORIES = {"hotel", "uber"}
XERO_SYNC_FEATURE_FLAG_ENV = "ADAPSYS_XERO_SYNC_ENABLED"
XERO_SYNC_STUB_MODE_ENV = "ADAPSYS_XERO_SYNC_STUB_MODE"
XERO_REQUIRED_ENV_KEYS = (
    "XERO_CLIENT_ID",
    "XERO_CLIENT_SECRET",
    "XERO_REFRESH_TOKEN",
    "XERO_TENANT_ID",
)
EMAIL_INTAKE_ALLOWED_CATEGORIES = {"flight", "flights", "hotel", "uber"}
CONSULTANT_ALLOWED_CATEGORIES = {
    "accommodation",
    "breakfast",
    "dinner",
    "flight",
    "flights",
    "lunch",
    "misc",
    "per_diem",
    "taxi",
    "train",
}

PAID_BY_OPTIONS = {"company_card", "personal_reimbursable", "personal_non_reimbursable"}


def _persist_expense(expense: "ExpenseOut") -> "ExpenseOut":
    supabase = _get_supabase()
    if supabase is not None:
        try:
            response = supabase.table("expenses").insert(expense.model_dump(mode="json")).execute()
        except Exception:
            payload = expense.model_dump(mode="json")
            payload.pop("paid_by", None)
            try:
                response = supabase.table("expenses").insert(payload).execute()
            except Exception:
                raise HTTPException(
                    status_code=422,
                    detail="Unable to save expense. Confirm trip_id exists and required fields are valid.",
                )
        if response.data:
            return ExpenseOut(**response.data[0])
        raise HTTPException(status_code=500, detail="Expense could not be saved.")

    _EXPENSES.append(expense)
    _save_local_expenses()
    return expense


def _get_supabase() -> Client | None:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_EXPENSES_CACHE_FILE = _DATA_DIR / "expenses.json"
_EXPENSE_XERO_SYNC_CACHE_FILE = _DATA_DIR / "expense_xero_sync.json"


def _load_local_expenses() -> list["ExpenseOut"]:
    if not _EXPENSES_CACHE_FILE.exists():
        return []
    try:
        rows = json.loads(_EXPENSES_CACHE_FILE.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            return []
        return [ExpenseOut(**row) for row in rows]
    except Exception:
        return []


def _save_local_expenses() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = [expense.model_dump(mode="json") for expense in _EXPENSES]
    _EXPENSES_CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    persist_backup_snapshot("expenses", payload)


class ExpenseCreate(BaseModel):
    trip_id: UUID
    submitted_by_email: str
    submitted_by_role: str = "consultant"
    expense_date: date
    category: str
    amount_local: float
    reimbursable_amount_local: float | None = None
    currency_local: str
    exchange_rate: float = 1.0
    gst_applicable: bool = True
    paid_by: str | None = None
    description: str | None = None
    supplier: str | None = None
    receipt_url: str | None = None
    receipt_thumb_url: str | None = None
    receipt_kind: str | None = None
    receipt_group_key: str | None = None
    no_receipt_reason: str | None = None
    notes: str | None = None


class ExpenseOut(ExpenseCreate):
    id: UUID = Field(default_factory=uuid4)
    amount_aud: float
    reimbursable_amount_aud: float | None = None
    status: str = "submitted"


class ExpenseXeroSyncState(BaseModel):
    expense_id: UUID
    sync_status: str = "not_synced"
    attempts: int = 0
    last_attempted_at: str | None = None
    last_synced_at: str | None = None
    xero_reference: str | None = None
    error: str | None = None


class ExpenseXeroSyncResult(BaseModel):
    expense_id: UUID
    sync: ExpenseXeroSyncState
    message: str


class ExpenseXeroSyncIntegrationStatus(BaseModel):
    enabled: bool
    mode: str
    credentials_configured: bool


class ExpenseReceiptUpdate(BaseModel):
    receipt_url: str
    receipt_thumb_url: str | None = None


class ExpenseTripUpdate(BaseModel):
    trip_id: UUID


class EmailReceiptIntake(BaseModel):
    trip_id: UUID
    received_from_email: str
    category: str
    receipt_url: str
    receipt_thumb_url: str | None = None
    expense_date: date | None = None
    amount_local: float = 0.0
    reimbursable_amount_local: float | None = None
    currency_local: str = "AUD"
    exchange_rate: float = 1.0
    gst_applicable: bool = True
    paid_by: str | None = None
    description: str | None = None
    supplier: str | None = None
    receipt_kind: str | None = None
    receipt_group_key: str | None = None
    notes: str | None = None


_EXPENSES: list[ExpenseOut] = _load_local_expenses()


def _load_xero_sync_state() -> dict[str, ExpenseXeroSyncState]:
    if not _EXPENSE_XERO_SYNC_CACHE_FILE.exists():
        return {}
    try:
        rows = json.loads(_EXPENSE_XERO_SYNC_CACHE_FILE.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            return {}
        parsed: dict[str, ExpenseXeroSyncState] = {}
        for row in rows:
            state = ExpenseXeroSyncState(**row)
            parsed[str(state.expense_id)] = state
        return parsed
    except Exception:
        return {}


def _save_xero_sync_state() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = [row.model_dump(mode="json") for row in _EXPENSE_XERO_SYNC_BY_ID.values()]
    _EXPENSE_XERO_SYNC_CACHE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    persist_backup_snapshot("expense_xero_sync", payload)


_EXPENSE_XERO_SYNC_BY_ID: dict[str, ExpenseXeroSyncState] = _load_xero_sync_state()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_env_truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _is_xero_sync_enabled() -> bool:
    return _is_env_truthy(os.getenv(XERO_SYNC_FEATURE_FLAG_ENV))


def _is_xero_stub_mode() -> bool:
    configured = os.getenv(XERO_SYNC_STUB_MODE_ENV)
    if configured is None:
        return True
    return _is_env_truthy(configured)


def _has_xero_credentials() -> bool:
    return all(str(os.getenv(key) or "").strip() for key in XERO_REQUIRED_ENV_KEYS)


def _find_expense_by_id(expense_id: UUID) -> ExpenseOut | None:
    supabase = _get_supabase()
    if supabase is not None:
        try:
            response = (
                supabase.table("expenses")
                .select("*")
                .eq("id", str(expense_id))
                .limit(1)
                .execute()
            )
            if response.data:
                return ExpenseOut(**response.data[0])
        except Exception:
            pass

    for expense in _EXPENSES:
        if expense.id == expense_id:
            return expense
    return None


def _get_or_create_xero_state(expense_id: UUID) -> ExpenseXeroSyncState:
    key = str(expense_id)
    existing = _EXPENSE_XERO_SYNC_BY_ID.get(key)
    if existing:
        return existing
    created = ExpenseXeroSyncState(expense_id=expense_id)
    _EXPENSE_XERO_SYNC_BY_ID[key] = created
    return created


def _upsert_xero_state(expense_id: UUID, **updates) -> ExpenseXeroSyncState:
    current = _get_or_create_xero_state(expense_id)
    updated = current.model_copy(update=updates)
    _EXPENSE_XERO_SYNC_BY_ID[str(expense_id)] = updated
    _save_xero_sync_state()
    return updated


def _trip_exists(trip_id: UUID) -> bool:
    from backend.routers.trips import list_trips

    return any(trip.id == trip_id for trip in list_trips())


@router.get("")
def list_expenses(actor: RequestActor = Depends(get_request_actor)) -> list[ExpenseOut]:
    supabase = _get_supabase()
    rows: list[ExpenseOut]
    if supabase is not None:
        try:
            response = supabase.table("expenses").select("*").execute()
            rows = [ExpenseOut(**row) for row in (response.data or [])]
        except Exception:
            rows = _EXPENSES
    else:
        rows = _EXPENSES

    if isinstance(actor, RequestActor) and actor.role == "consultant":
        return [row for row in rows if str(row.submitted_by_email or "").strip().lower() == actor.email]
    return rows


@router.post("")
def create_expense(payload: ExpenseCreate, actor: RequestActor = Depends(get_request_actor)) -> ExpenseOut:
    category = payload.category.strip().lower()
    role = payload.submitted_by_role.strip().lower()

    amount_local = float(payload.amount_local or 0)
    if amount_local <= 0:
        raise HTTPException(status_code=422, detail="amount_local must be greater than 0.")

    currency_local = str(payload.currency_local or "").strip().upper() or "AUD"
    exchange_rate = float(payload.exchange_rate or 0)
    if currency_local != "AUD" and exchange_rate <= 0:
        raise HTTPException(
            status_code=422,
            detail="exchange_rate must be greater than 0 when currency_local is not AUD.",
        )

    if not _trip_exists(payload.trip_id):
        raise HTTPException(status_code=422, detail="Trip not found for supplied trip_id.")

    if actor.role == "consultant" and payload.submitted_by_email.strip().lower() != actor.email:
        raise HTTPException(status_code=403, detail="Consultants can only submit expenses as themselves.")

    if role in {"admin", "finance"}:
        require_roles(actor, {"admin", "finance"})

    if role == "consultant" and category not in CONSULTANT_ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail=(
                "Consultants can only submit accommodation, breakfast, dinner, flight, flights, "
                "lunch, misc, per_diem, taxi, or train expenses."
            ),
        )

    if category in ADMIN_ONLY_CATEGORIES and role not in {"admin", "finance"}:
        raise HTTPException(
            status_code=422,
            detail="Hotel and Uber expenses are Fi/finance-only categories.",
        )

    paid_by_raw = str(payload.paid_by or "").strip().lower()
    if not paid_by_raw:
        paid_by_raw = "company_card" if role in {"admin", "finance"} else "personal_reimbursable"
    if paid_by_raw not in PAID_BY_OPTIONS:
        raise HTTPException(
            status_code=422,
            detail="paid_by must be one of company_card, personal_reimbursable, personal_non_reimbursable.",
        )

    has_receipt = bool(payload.receipt_url and payload.receipt_url.strip())
    has_reason = bool(payload.no_receipt_reason and payload.no_receipt_reason.strip())
    resolved_no_receipt_reason = payload.no_receipt_reason
    if not has_receipt and not has_reason:
        resolved_no_receipt_reason = "Receipt pending upload"

    reimbursable_local = payload.reimbursable_amount_local
    if reimbursable_local is None:
        reimbursable_local = payload.amount_local
    if reimbursable_local < 0:
        raise HTTPException(status_code=422, detail="reimbursable_amount_local cannot be negative.")
    if reimbursable_local > payload.amount_local:
        raise HTTPException(
            status_code=422,
            detail="reimbursable_amount_local cannot be greater than amount_local.",
        )

    amount_aud = round(amount_local * exchange_rate, 2)
    reimbursable_amount_aud = round(reimbursable_local * exchange_rate, 2)
    expense_data = payload.model_dump()
    expense_data["category"] = category
    expense_data["submitted_by_role"] = role
    expense_data["currency_local"] = currency_local
    expense_data["exchange_rate"] = exchange_rate
    expense_data["amount_local"] = amount_local
    expense_data["paid_by"] = paid_by_raw
    expense_data["description"] = str(payload.description or "").strip() or None
    expense_data["supplier"] = str(payload.supplier or "").strip() or None
    expense_data["receipt_kind"] = str(payload.receipt_kind or "").strip().lower() or None
    expense_data["receipt_group_key"] = None
    expense_data["no_receipt_reason"] = resolved_no_receipt_reason
    expense_data["reimbursable_amount_local"] = reimbursable_local
    expense_data["amount_aud"] = amount_aud
    expense_data["reimbursable_amount_aud"] = reimbursable_amount_aud
    expense = ExpenseOut(**expense_data)
    return _persist_expense(expense)


@router.post("/intake-email")
def intake_email_receipt(
    payload: EmailReceiptIntake,
    actor: RequestActor = Depends(get_request_actor),
) -> ExpenseOut:
    require_roles(actor, {"admin", "finance"})

    category = payload.category.strip().lower()
    if category not in EMAIL_INTAKE_ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail="Email receipt intake is reserved for flight, flights, uber, or hotel categories.",
        )

    if not payload.receipt_url.strip():
        raise HTTPException(status_code=422, detail="Receipt URL is required for email intake.")

    paid_by_raw = str(payload.paid_by or "").strip().lower() or "company_card"
    if paid_by_raw not in PAID_BY_OPTIONS:
        raise HTTPException(
            status_code=422,
            detail="paid_by must be one of company_card, personal_reimbursable, personal_non_reimbursable.",
        )

    amount_local = float(payload.amount_local or 0)
    if amount_local < 0:
        raise HTTPException(status_code=422, detail="amount_local cannot be negative for email intake.")

    currency_local = str(payload.currency_local or "").strip().upper() or "AUD"
    exchange_rate = float(payload.exchange_rate or 0)
    if currency_local != "AUD" and exchange_rate <= 0:
        raise HTTPException(
            status_code=422,
            detail="exchange_rate must be greater than 0 when currency_local is not AUD.",
        )

    reimbursable_local = payload.reimbursable_amount_local
    if reimbursable_local is None:
        reimbursable_local = payload.amount_local
    if reimbursable_local < 0:
        raise HTTPException(status_code=422, detail="reimbursable_amount_local cannot be negative.")
    if reimbursable_local > payload.amount_local:
        raise HTTPException(
            status_code=422,
            detail="reimbursable_amount_local cannot be greater than amount_local.",
        )

    expense_date = payload.expense_date or date.today()
    amount_aud = round(amount_local * exchange_rate, 2)
    reimbursable_amount_aud = round(reimbursable_local * exchange_rate, 2)
    expense = ExpenseOut(
        trip_id=payload.trip_id,
        submitted_by_email="fi@adapsysgroup.com",
        submitted_by_role="admin",
        expense_date=expense_date,
        category=category,
        amount_local=amount_local,
        reimbursable_amount_local=reimbursable_local,
        currency_local=currency_local,
        exchange_rate=exchange_rate,
        gst_applicable=payload.gst_applicable,
        paid_by=paid_by_raw,
        description=str(payload.description or "").strip() or None,
        supplier=str(payload.supplier or "").strip() or None,
        receipt_url=payload.receipt_url,
        receipt_thumb_url=payload.receipt_thumb_url or payload.receipt_url,
        receipt_kind=str(payload.receipt_kind or "").strip().lower() or "invoice",
        receipt_group_key=None,
        no_receipt_reason=None,
        notes=(f"Forwarded from: {payload.received_from_email}. {payload.notes or ''}").strip(),
        amount_aud=amount_aud,
        reimbursable_amount_aud=reimbursable_amount_aud,
        status="draft_email",
    )
    return _persist_expense(expense)


@router.post("/{expense_id}/approve")
def approve_expense(
    expense_id: UUID,
    actor: RequestActor = Depends(get_request_actor),
) -> ExpenseOut:
    require_roles(actor, {"admin", "finance"})

    supabase = _get_supabase()
    if supabase is not None:
        response = (
            supabase.table("expenses")
            .update({"status": "approved"})
            .eq("id", str(expense_id))
            .execute()
        )
        if response.data:
            return ExpenseOut(**response.data[0])
        raise HTTPException(status_code=404, detail="Expense not found")

    for idx, expense in enumerate(_EXPENSES):
        if expense.id == expense_id:
            updated = expense.model_copy(update={"status": "approved"})
            _EXPENSES[idx] = updated
            _save_local_expenses()
            return updated

    raise HTTPException(status_code=404, detail="Expense not found")


@router.get("/xero-sync-status")
def list_expense_xero_sync_status(
    actor: RequestActor = Depends(get_request_actor),
) -> list[ExpenseXeroSyncState]:
    require_roles(actor, {"admin", "finance"})
    expenses = list_expenses(actor)
    rows: list[ExpenseXeroSyncState] = []
    for expense in expenses:
        rows.append(_EXPENSE_XERO_SYNC_BY_ID.get(str(expense.id), ExpenseXeroSyncState(expense_id=expense.id)))
    return rows


@router.get("/xero-sync-config")
def get_expense_xero_sync_config(
    actor: RequestActor = Depends(get_request_actor),
) -> ExpenseXeroSyncIntegrationStatus:
    require_roles(actor, {"admin", "finance"})
    enabled = _is_xero_sync_enabled()
    stub_mode = _is_xero_stub_mode()
    return ExpenseXeroSyncIntegrationStatus(
        enabled=enabled,
        mode="stub" if stub_mode else "live",
        credentials_configured=_has_xero_credentials(),
    )


@router.post("/{expense_id}/xero-sync")
def push_expense_to_xero(
    expense_id: UUID,
    actor: RequestActor = Depends(get_request_actor),
) -> ExpenseXeroSyncResult:
    require_roles(actor, {"admin", "finance"})
    if not _is_xero_sync_enabled():
        raise HTTPException(
            status_code=403,
            detail=f"Xero sync is disabled. Set {XERO_SYNC_FEATURE_FLAG_ENV}=1 to enable the scaffold.",
        )

    expense = _find_expense_by_id(expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.status not in {"approved", "invoiced"}:
        raise HTTPException(status_code=422, detail="Only approved or invoiced expenses can be pushed to Xero.")

    current = _get_or_create_xero_state(expense_id)
    attempts = int(current.attempts or 0) + 1
    attempted_at = _utc_now_iso()

    if _is_xero_stub_mode():
        synced_at = _utc_now_iso()
        state = _upsert_xero_state(
            expense_id,
            sync_status="synced_stub",
            attempts=attempts,
            last_attempted_at=attempted_at,
            last_synced_at=synced_at,
            xero_reference=f"stub-{str(expense_id)[:8]}-{attempts}",
            error=None,
        )
        return ExpenseXeroSyncResult(
            expense_id=expense_id,
            sync=state,
            message="Stub sync complete. Disable ADAPSYS_XERO_SYNC_STUB_MODE once live Xero API credentials are wired.",
        )

    if not _has_xero_credentials():
        state = _upsert_xero_state(
            expense_id,
            sync_status="failed_config",
            attempts=attempts,
            last_attempted_at=attempted_at,
            error="Xero credentials are not configured.",
        )
        return ExpenseXeroSyncResult(
            expense_id=expense_id,
            sync=state,
            message="Xero credentials missing. Configure XERO_CLIENT_ID, XERO_CLIENT_SECRET, XERO_REFRESH_TOKEN, and XERO_TENANT_ID.",
        )

    state = _upsert_xero_state(
        expense_id,
        sync_status="pending_live",
        attempts=attempts,
        last_attempted_at=attempted_at,
        error="Live Xero API call not wired yet. Enable stub mode until API implementation is added.",
    )
    return ExpenseXeroSyncResult(
        expense_id=expense_id,
        sync=state,
        message="Credentials detected but live Xero API push is not yet wired.",
    )


@router.put("/{expense_id}/trip")
def reassign_expense_trip(
    expense_id: UUID,
    payload: ExpenseTripUpdate,
    actor: RequestActor = Depends(get_request_actor),
) -> ExpenseOut:
    require_roles(actor, {"admin", "finance"})

    supabase = _get_supabase()
    if supabase is not None:
        response = (
            supabase.table("expenses")
            .update({"trip_id": str(payload.trip_id)})
            .eq("id", str(expense_id))
            .execute()
        )
        if response.data:
            return ExpenseOut(**response.data[0])
        raise HTTPException(status_code=404, detail="Expense not found")

    for idx, expense in enumerate(_EXPENSES):
        if expense.id == expense_id:
            updated = expense.model_copy(update={"trip_id": payload.trip_id})
            _EXPENSES[idx] = updated
            _save_local_expenses()
            return updated

    raise HTTPException(status_code=404, detail="Expense not found")


@router.put("/{expense_id}/receipt")
def attach_expense_receipt(
    expense_id: UUID,
    payload: ExpenseReceiptUpdate,
    actor: RequestActor = Depends(get_request_actor),
) -> ExpenseOut:
    require_roles(actor, {"admin", "finance"})

    resolved_receipt_url = (payload.receipt_url or "").strip()
    if not resolved_receipt_url:
        raise HTTPException(status_code=422, detail="receipt_url is required")

    resolved_thumb = (payload.receipt_thumb_url or "").strip() or resolved_receipt_url

    supabase = _get_supabase()
    if supabase is not None:
        response = (
            supabase.table("expenses")
            .update(
                {
                    "receipt_url": resolved_receipt_url,
                    "receipt_thumb_url": resolved_thumb,
                    "no_receipt_reason": None,
                }
            )
            .eq("id", str(expense_id))
            .execute()
        )
        if response.data:
            return ExpenseOut(**response.data[0])
        raise HTTPException(status_code=404, detail="Expense not found")

    for idx, expense in enumerate(_EXPENSES):
        if expense.id == expense_id:
            updated = expense.model_copy(
                update={
                    "receipt_url": resolved_receipt_url,
                    "receipt_thumb_url": resolved_thumb,
                    "no_receipt_reason": None,
                }
            )
            _EXPENSES[idx] = updated
            _save_local_expenses()
            return updated

    raise HTTPException(status_code=404, detail="Expense not found")


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: UUID,
    actor: RequestActor = Depends(get_request_actor),
) -> ExpenseOut:
    require_roles(actor, {"admin", "finance"})

    supabase = _get_supabase()
    if supabase is not None:
        existing = (
            supabase.table("expenses")
            .select("*")
            .eq("id", str(expense_id))
            .limit(1)
            .execute()
        )
        if not existing.data:
            raise HTTPException(status_code=404, detail="Expense not found")

        # Supabase delete can silently fail when using restricted keys/RLS.
        # Execute delete, then verify the row no longer exists.
        supabase.table("expenses").delete().eq("id", str(expense_id)).execute()
        verify = (
            supabase.table("expenses")
            .select("id")
            .eq("id", str(expense_id))
            .limit(1)
            .execute()
        )
        if verify.data:
            raise HTTPException(
                status_code=403,
                detail="Expense delete was blocked by Supabase permissions (RLS/key policy).",
            )

        return ExpenseOut(**existing.data[0])

    for idx, expense in enumerate(_EXPENSES):
        if expense.id == expense_id:
            deleted = _EXPENSES.pop(idx)
            _save_local_expenses()
            return deleted

    raise HTTPException(status_code=404, detail="Expense not found")


@router.post("/{expense_id}/mark-invoiced")
def mark_expense_invoiced(
    expense_id: UUID,
    actor: RequestActor = Depends(get_request_actor),
) -> ExpenseOut:
    require_roles(actor, {"admin", "finance"})

    supabase = _get_supabase()
    if supabase is not None:
        response = (
            supabase.table("expenses")
            .update({"status": "invoiced"})
            .eq("id", str(expense_id))
            .execute()
        )
        if response.data:
            return ExpenseOut(**response.data[0])
        raise HTTPException(status_code=404, detail="Expense not found")

    for idx, expense in enumerate(_EXPENSES):
        if expense.id == expense_id:
            updated = expense.model_copy(update={"status": "invoiced"})
            _EXPENSES[idx] = updated
            _save_local_expenses()
            return updated

    raise HTTPException(status_code=404, detail="Expense not found")
