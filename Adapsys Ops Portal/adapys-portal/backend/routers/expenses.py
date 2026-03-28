from datetime import date
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

ADMIN_ONLY_CATEGORIES = {"flights", "uber", "hotel"}
CONSULTANT_ALLOWED_CATEGORIES = {"taxi", "dinner", "per_diem", "misc"}


def _persist_expense(expense: "ExpenseOut") -> "ExpenseOut":
    supabase = _get_supabase()
    if supabase is not None:
        try:
            response = supabase.table("expenses").insert(expense.model_dump(mode="json")).execute()
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
    currency_local: str
    exchange_rate: float = 1.0
    gst_applicable: bool = True
    receipt_url: str | None = None
    receipt_thumb_url: str | None = None
    no_receipt_reason: str | None = None
    notes: str | None = None


class ExpenseOut(ExpenseCreate):
    id: UUID = Field(default_factory=uuid4)
    amount_aud: float
    status: str = "submitted"


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
    currency_local: str = "AUD"
    exchange_rate: float = 1.0
    gst_applicable: bool = True
    notes: str | None = None


_EXPENSES: list[ExpenseOut] = _load_local_expenses()


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

    if not _trip_exists(payload.trip_id):
        raise HTTPException(status_code=422, detail="Trip not found for supplied trip_id.")

    if actor.role == "consultant" and payload.submitted_by_email.strip().lower() != actor.email:
        raise HTTPException(status_code=403, detail="Consultants can only submit expenses as themselves.")

    if role in {"admin", "finance"}:
        require_roles(actor, {"admin", "finance"})

    if role == "consultant" and category not in CONSULTANT_ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail="Consultants can only submit taxi, dinner, per_diem, or misc expenses.",
        )

    if category in ADMIN_ONLY_CATEGORIES and role not in {"admin", "finance"}:
        raise HTTPException(
            status_code=422,
            detail="Flights, Uber, and hotel expenses are Fi/finance-only categories.",
        )

    has_receipt = bool(payload.receipt_url and payload.receipt_url.strip())
    has_reason = bool(payload.no_receipt_reason and payload.no_receipt_reason.strip())
    resolved_no_receipt_reason = payload.no_receipt_reason
    if not has_receipt and not has_reason:
        resolved_no_receipt_reason = "Receipt pending upload"

    amount_aud = round(payload.amount_local * payload.exchange_rate, 2)
    expense_data = payload.model_dump()
    expense_data["category"] = category
    expense_data["submitted_by_role"] = role
    expense_data["no_receipt_reason"] = resolved_no_receipt_reason
    expense_data["amount_aud"] = amount_aud
    expense = ExpenseOut(**expense_data)
    return _persist_expense(expense)


@router.post("/intake-email")
def intake_email_receipt(
    payload: EmailReceiptIntake,
    actor: RequestActor = Depends(get_request_actor),
) -> ExpenseOut:
    require_roles(actor, {"admin", "finance"})

    category = payload.category.strip().lower()
    if category not in ADMIN_ONLY_CATEGORIES:
        raise HTTPException(
            status_code=422,
            detail="Email receipt intake is reserved for flights, uber, or hotel categories.",
        )

    if not payload.receipt_url.strip():
        raise HTTPException(status_code=422, detail="Receipt URL is required for email intake.")

    expense_date = payload.expense_date or date.today()
    amount_aud = round(payload.amount_local * payload.exchange_rate, 2)
    expense = ExpenseOut(
        trip_id=payload.trip_id,
        submitted_by_email="fi@adapsysgroup.com",
        submitted_by_role="admin",
        expense_date=expense_date,
        category=category,
        amount_local=payload.amount_local,
        currency_local=payload.currency_local,
        exchange_rate=payload.exchange_rate,
        gst_applicable=payload.gst_applicable,
        receipt_url=payload.receipt_url,
        receipt_thumb_url=payload.receipt_thumb_url or payload.receipt_url,
        no_receipt_reason=None,
        notes=(f"Forwarded from: {payload.received_from_email}. {payload.notes or ''}").strip(),
        amount_aud=amount_aud,
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
        response = supabase.table("expenses").delete().eq("id", str(expense_id)).execute()
        if response.data:
            return ExpenseOut(**response.data[0])
        raise HTTPException(status_code=404, detail="Expense not found")

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
