import base64
from collections import defaultdict
from datetime import date
import os
from pathlib import Path
import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel

from backend.routers.coaching import list_all_engagements_for_reports, list_all_sessions_for_reports
from backend.routers.expenses import ExpenseOut, list_expenses
from backend.routers.lookups import list_coaches, list_consultants
from backend.routers.security import RequestActor, get_request_actor, require_roles
from backend.routers.trips import TripOut, list_trips

router = APIRouter()

REPORT_ISSUER_NAME = "Adapsys Australia Pacific"
REPORT_ISSUER_ABN = "ABN 56 623 973 446"
REPORT_ISSUER_ADDRESS = "Unit 3, 18 Woodlands Way, Parkwood, Queensland 4214"
CLIENT_REPORTS_FEATURE_FLAG_ENV = "ADAPSYS_CLIENT_REPORTS_ENABLED"


class ClientCoachingSummaryRow(BaseModel):
    coachee: str
    coach_name: str
    entitled_sessions: int
    sessions_taken: int
    sessions_left: int
    no_show_count: int
    session_dates: list[str]
    lcp_available: bool
    lcp_entitled: int | None = None
    lcp_taken: int | None = None


def _normalize_scope_text(value: str | None) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _client_matches_scope(client_value: str | None, scope_value: str | None) -> bool:
    normalized_client = _normalize_scope_text(client_value)
    normalized_scope = _normalize_scope_text(scope_value)
    if not normalized_client or not normalized_scope:
        return False
    if normalized_client == normalized_scope:
        return True
    return normalized_client.startswith(f"{normalized_scope} /") or normalized_scope.startswith(
        f"{normalized_client} /"
    )


def _is_client_reports_enabled() -> bool:
    return str(os.getenv(CLIENT_REPORTS_FEATURE_FLAG_ENV, "")).strip().lower() in {"1", "true", "yes", "on"}


def _format_date_au(value: date | str) -> str:
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    raw = str(value or "").strip()
    parts = raw.split("-")
    if len(parts) == 3 and all(parts):
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return raw


def _find_trip(trip_id: UUID) -> TripOut:
    for trip in list_trips():
        if trip.id == trip_id:
            return trip
    raise HTTPException(status_code=404, detail="Trip not found")


def _trip_expenses(trip_id: UUID) -> list[ExpenseOut]:
    return [expense for expense in list_expenses() if expense.trip_id == trip_id]


def _display_name_from_email(email: str | None, consultant_name_by_email: dict[str, str]) -> str:
    normalized = str(email or "").strip().lower()
    if not normalized:
        return "Unspecified"
    if normalized in consultant_name_by_email:
        return consultant_name_by_email[normalized]

    local_part = normalized.split("@", 1)[0].replace(".", " ").replace("_", " ").strip()
    if not local_part:
        return normalized
    return " ".join(token.capitalize() for token in local_part.split())


def _expense_within_range(expense: ExpenseOut, start_date: date | None, end_date: date | None) -> bool:
    raw_date = expense.expense_date
    expense_date = raw_date if isinstance(raw_date, date) else date.fromisoformat(str(raw_date))
    if start_date and expense_date < start_date:
        return False
    if end_date and expense_date > end_date:
        return False
    return True


def _find_logo_path(context: str = "portal") -> Path | None:
    here = Path(__file__).resolve()

    context_key = str(context or "portal").strip().lower()
    context_candidates: dict[str, list[str]] = {
        "report": ["Adapsys_Logo_2.png"],
        "portal": ["Adapsys_Logo_1.png", "Adapsys_Logo_4 .png", "Adapsys_Logo_4.png", "Adapsys_Logo_5.png"],
    }
    fallback_candidates = [
        "Adapsys_Logo_2.png",
        "Adapsys_Logo_1.png",
        "Adapsys_Logo_3.png",
        "Adapsys_Logo_4 .png",
        "Adapsys_Logo_4.png",
        "Adapsys_Logo_5.png",
        "Adapsysgroup logo.png",
        "Adapsys Group Logo.png",
        "adapsysgroup logo.png",
        "adapsys-logo.png",
    ]
    candidate_files = [
        *context_candidates.get(context_key, []),
        *fallback_candidates,
    ]

    candidate_paths: list[Path] = []
    for parent in here.parents:
        for file_name in candidate_files:
            candidate_paths.append(parent / "Adapsys Logo" / file_name)
            candidate_paths.append(parent / file_name)

    return next((path for path in candidate_paths if path.exists()), None)


def _logo_data_uri(context: str = "report") -> str | None:
    logo_path = _find_logo_path(context=context)
    if logo_path is None:
        return None

    try:
        encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    except Exception:
        return None

    return f"data:image/png;base64,{encoded}"


def _per_diem_thumbnail_html(expense: ExpenseOut) -> str:
    if expense.category != "per_diem":
        return ""

    notes = expense.notes or ""
    meal_rows: list[str] = []
    for meal in ("Breakfast", "Lunch", "Dinner", "Misc"):
        match = re.search(
            rf"{meal} claimed:\s*(Yes|No)(?:\s*\(AUD\s*([0-9]+(?:\.[0-9]+)?)\))?",
            notes,
            flags=re.IGNORECASE,
        )
        if not match:
            continue

        claimed = match.group(1).strip().lower() == "yes"
        amount = float(match.group(2)) if match.group(2) else 0.0
        checkbox = "&#9745;" if claimed else "&#9744;"
        meal_rows.append(
            f"<tr><td>{checkbox} {meal}</td><td style='text-align:right;'>AUD {amount:.2f}</td></tr>"
        )

    incidental_match = re.search(
        r"Incidental midpoint applied:\s*(Yes|No)\s*\(AUD\s*([0-9]+(?:\.[0-9]+)?)\)",
        notes,
        flags=re.IGNORECASE,
    )
    if incidental_match:
        incidental_applied = incidental_match.group(1).strip().lower() == "yes"
        incidental_amount = float(incidental_match.group(2))
        checkbox = "&#9745;" if incidental_applied else "&#9744;"
        meal_rows.append(
            f"<tr><td>{checkbox} Incidental</td><td style='text-align:right;'>AUD {incidental_amount:.2f}</td></tr>"
        )

    entry_total_match = re.search(
        r"Per diem entry total:\s*AUD\s*([0-9]+(?:\.[0-9]+)?)",
        notes,
        flags=re.IGNORECASE,
    )
    total_match = re.search(r"Claim total:\s*AUD\s*([0-9]+(?:\.[0-9]+)?)", notes, flags=re.IGNORECASE)
    incidental_days_match = re.search(r"Incidental eligible days:\s*([0-9]+)", notes, flags=re.IGNORECASE)
    incidental_subtotal_match = re.search(
        r"Incidental subtotal:\s*AUD\s*([0-9]+(?:\.[0-9]+)?)",
        notes,
        flags=re.IGNORECASE,
    )
    claim_total = (
        float(entry_total_match.group(1))
        if entry_total_match
        else float(total_match.group(1))
        if total_match
        else float(expense.amount_aud)
    )

    if incidental_days_match:
        days = int(incidental_days_match.group(1))
        subtotal = (
            float(incidental_subtotal_match.group(1))
            if incidental_subtotal_match
            else 0.0
        )
        meal_rows.append(
            f"<tr><td>Incidental days in range</td><td style='text-align:right;'>{days} (AUD {subtotal:.2f})</td></tr>"
        )

    if not meal_rows:
        meal_rows.append(
            f"<tr><td colspan='2'>Per diem claim submitted</td></tr>"
        )

    breakdown_date = _format_date_au(expense.expense_date)

    return (
        "<div class='per-diem-thumb'>"
        f"<div class='per-diem-thumb-title'>Per Diem Breakdown — {breakdown_date}</div>"
        "<table>"
        f"{''.join(meal_rows)}"
        f"<tr class='per-diem-thumb-total'><td>Total</td><td style='text-align:right;'>AUD {claim_total:.2f}</td></tr>"
        "</table>"
        "</div>"
    )


def _looks_like_image_reference(value: str | None) -> bool:
    if not value:
        return False
    raw = str(value).strip().lower()
    if raw.startswith("data:image/"):
        return True
    return raw.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".tif", ".tiff"))


@router.get("/brand-logo")
def report_brand_logo(context: str = "portal") -> FileResponse:
    logo_path = _find_logo_path(context=context)
    if logo_path is None:
        raise HTTPException(status_code=404, detail="Logo file not found")
    return FileResponse(str(logo_path), media_type="image/png")


def _build_report_html(
    trip: TripOut,
    expenses: list[ExpenseOut],
    start_date: date | None = None,
    end_date: date | None = None,
) -> str:
    consultant_name_by_email = {
        str(consultant.email or "").strip().lower(): str(consultant.name or "").strip()
        for consultant in list_consultants()
        if str(consultant.email or "").strip() and str(consultant.name or "").strip()
    }

    category_icon_meta = {
        "flight": ("&#9992;", "cat-flight"),
        "flights": ("&#9992;", "cat-flight"),
        "accommodation": ("AC", "cat-accommodation"),
        "hotel": ("AC", "cat-accommodation"),
        "uber": ("&#128663;", "cat-transport"),
        "taxi": ("&#128663;", "cat-transport"),
        "train": ("&#128663;", "cat-transport"),
        "dinner": ("ML", "cat-meals"),
        "lunch": ("ML", "cat-meals"),
        "breakfast": ("ML", "cat-meals"),
        "per_diem": ("PD", "cat-perdiem"),
        "misc": ("MS", "cat-misc"),
    }

    def _category_badge(category_value: str | None) -> str:
        key = str(category_value or "").strip().lower()
        label = key.replace("_", " ").title() if key else "Unspecified"
        icon_text, css_class = category_icon_meta.get(key, ("OT", "cat-default"))
        return (
            f"<span class='category-chip {css_class}'>"
            f"<span class='category-chip-icon'>{icon_text}</span>"
            f"<span>{label}</span>"
            "</span>"
        )

    def _category_icon_token(category_value: str | None) -> str:
        key = str(category_value or "").strip().lower()
        label = key.replace("_", " ").title() if key else "Unspecified"
        icon_text, css_class = category_icon_meta.get(key, ("OT", "cat-default"))
        return f"<span class='category-token {css_class}' title='{label}'>{icon_text}</span>"

    def _receipt_image_ref(expense_row: ExpenseOut) -> str:
        thumb_ref = str(expense_row.receipt_thumb_url or "").strip()
        full_ref = str(expense_row.receipt_url or "").strip()
        if _looks_like_image_reference(thumb_ref):
            return thumb_ref
        if _looks_like_image_reference(full_ref):
            return full_ref
        return ""

    def _gst_amount(expense_row: ExpenseOut) -> float:
        if not expense_row.gst_applicable:
            return 0.0
        if str(expense_row.currency_local or "").strip().upper() != "AUD":
            return 0.0
        return round(float(expense_row.amount_aud) / 11.0, 2)

    sorted_expenses = sorted(expenses, key=lambda row: (str(row.expense_date), str(row.category), str(row.id)))

    totals_by_category: dict[str, float] = defaultdict(float)
    for expense in sorted_expenses:
        reimbursable_aud = (
            float(expense.reimbursable_amount_aud)
            if expense.reimbursable_amount_aud is not None
            else float(expense.amount_aud)
        )
        totals_by_category[str(expense.category or "")] += reimbursable_aud

    category_rows = "".join(
        f"<tr><td>{_category_badge(str(category))}</td><td style='text-align:right;'>AUD {round(total, 2):.2f}</td></tr>"
        for category, total in sorted(totals_by_category.items())
    )

    expense_rows: list[str] = []
    for expense in sorted_expenses:
        description = str(expense.description or "").strip() or "—"
        supplier = str(expense.supplier or "").strip() or "—"
        expense_rows.append(
            "<tr>"
            f"<td>{_format_date_au(expense.expense_date)}</td>"
            f"<td class='cat-icon'>{_category_icon_token(str(expense.category))}</td>"
            f"<td>{description}</td>"
            f"<td>{supplier}</td>"
            f"<td class='num'>AUD {expense.amount_aud:.2f}</td>"
            f"<td class='num'>AUD {_gst_amount(expense):.2f}</td>"
            "</tr>"
        )

    def _invoice_header_block(supplier: str, expense_date: date | str, amount_aud: float) -> str:
        return (
            "<div class='receipt-card-head receipt-card-head-meta'>"
            f"<span><strong>Supplier:</strong> {supplier}</span>"
            f"<span><strong>Date:</strong> {_format_date_au(expense_date)}</span>"
            f"<span><strong>Amount:</strong> AUD {amount_aud:.2f}</span>"
            "</div>"
        )

    def _single_receipt_card(expense_row: ExpenseOut) -> str:
        supplier = str(expense_row.supplier or "").strip() or "Unspecified supplier"
        image_ref = _receipt_image_ref(expense_row)
        if image_ref:
            image_html = f"<img class='receipt-image' src='{image_ref}' alt='Receipt image' />"
        elif expense_row.receipt_url:
            image_html = "<div class='receipt-placeholder'>Receipt linked (preview unavailable)</div>"
        else:
            image_html = (
                "<div class='receipt-placeholder'>"
                f"No receipt uploaded<br/><small>{expense_row.no_receipt_reason or ''}</small>"
                "</div>"
            )

        return (
            "<article class='receipt-card invoice-card'>"
            f"{_invoice_header_block(supplier, expense_row.expense_date, float(expense_row.amount_aud))}"
            f"{image_html}"
            "</article>"
        )

    def _flight_invoice_card(invoice_row: ExpenseOut) -> str:
        image_ref = _receipt_image_ref(invoice_row)
        image_html = (
            f"<img class='receipt-image' src='{image_ref}' alt='Flight Invoice' />"
            if image_ref
            else "<div class='receipt-placeholder'>Invoice linked (preview unavailable)</div>"
        )
        supplier = str(invoice_row.supplier or "").strip() or "Unspecified supplier"
        return (
            "<article class='receipt-card flight-receipt-card invoice-card'>"
            f"{_invoice_header_block(supplier, invoice_row.expense_date, float(invoice_row.amount_aud))}"
            f"{image_html}"
            "</article>"
        )

    def _flight_boarding_card(consultant_label: str, boarding_rows: list[ExpenseOut]) -> str:
        if not boarding_rows:
            return (
                "<article class='receipt-card flight-receipt-card boarding-card'>"
                f"<div class='receipt-card-head'>Boarding Passes • {consultant_label}</div>"
                "<div class='receipt-blank'></div>"
                "</article>"
            )

        image_blocks: list[str] = []
        for row in boarding_rows[:2]:
            image_ref = _receipt_image_ref(row)
            if image_ref:
                image_blocks.append(f"<img class='receipt-image boarding-pass-image' src='{image_ref}' alt='Boarding pass' />")
            else:
                image_blocks.append("<div class='receipt-placeholder'>Boarding pass linked (preview unavailable)</div>")

        total_aud = round(sum(float(row.amount_aud) for row in boarding_rows[:2]), 2)
        dates = ", ".join(_format_date_au(row.expense_date) for row in boarding_rows[:2])
        return (
            "<article class='receipt-card flight-receipt-card boarding-card'>"
            f"<div class='receipt-card-head'>Boarding Passes • {consultant_label}</div>"
            "<div class='boarding-pass-stack'>"
            + "".join(image_blocks)
            + "</div>"
            f"<div class='receipt-card-sub receipt-meta-small'>{dates} • AUD {total_aud:.2f}</div>"
            "</article>"
        )

    def _is_flight(expense_row: ExpenseOut) -> bool:
        return str(expense_row.category or "").strip().lower() in {"flight", "flights"}

    def _flight_date_key(expense_row: ExpenseOut) -> str:
        return str(expense_row.expense_date or "")

    def _receipt_kind_key(expense_row: ExpenseOut) -> str:
        return str(expense_row.receipt_kind or "").strip().lower()

    receipt_cards: list[str] = []
    used_ids: set[str] = set()
    flight_rows = [expense for expense in sorted_expenses if _is_flight(expense)]
    flight_rows_by_consultant: dict[str, list[ExpenseOut]] = defaultdict(list)
    for row in flight_rows:
        consultant_key = str(row.submitted_by_email or "").strip().lower()
        flight_rows_by_consultant[consultant_key].append(row)

    for consultant_key in sorted(flight_rows_by_consultant):
        consultant_rows = sorted(
            flight_rows_by_consultant[consultant_key],
            key=lambda row: (_flight_date_key(row), str(row.id)),
        )
        invoice_rows = [
            row
            for row in consultant_rows
            if _receipt_kind_key(row) in {"invoice", "tax_invoice", "itinerary"}
        ]
        remaining_boarding_rows = [
            row
            for row in consultant_rows
            if _receipt_kind_key(row) in {"boarding_pass", "boarding"}
        ]
        consultant_label = _display_name_from_email(consultant_key, consultant_name_by_email)

        for invoice_row in invoice_rows:
            matched_boarding_rows: list[ExpenseOut] = []
            if remaining_boarding_rows:
                invoice_date_key = _flight_date_key(invoice_row)
                same_date_boarding = [
                    row for row in remaining_boarding_rows if _flight_date_key(row) == invoice_date_key
                ]
                if same_date_boarding:
                    matched_boarding_rows = same_date_boarding[:2]
                    matched_ids = {str(row.id) for row in matched_boarding_rows}
                    remaining_boarding_rows = [
                        row for row in remaining_boarding_rows if str(row.id) not in matched_ids
                    ]
                else:
                    matched_boarding_rows = remaining_boarding_rows[:2]
                    remaining_boarding_rows = remaining_boarding_rows[2:]

            receipt_cards.append(_flight_invoice_card(invoice_row))
            receipt_cards.append(_flight_boarding_card(consultant_label, matched_boarding_rows))
            used_ids.add(str(invoice_row.id))
            for boarding_row in matched_boarding_rows:
                used_ids.add(str(boarding_row.id))

        for boarding_row in remaining_boarding_rows:
            receipt_cards.append(_flight_boarding_card(consultant_label, [boarding_row]))
            used_ids.add(str(boarding_row.id))

    for expense in sorted_expenses:
        if str(expense.id) in used_ids:
            continue
        receipt_cards.append(_single_receipt_card(expense))

    receipt_cards_per_page = 4
    receipt_grid_class = "receipt-grid"

    receipt_pages: list[str] = []
    for index in range(0, len(receipt_cards), receipt_cards_per_page):
        chunk = "".join(receipt_cards[index:index + receipt_cards_per_page])
        is_last = index + receipt_cards_per_page >= len(receipt_cards)
        receipt_pages.append(
            "<section class='receipt-page" + (" is-last" if is_last else "") + "'>"
            "<h2>Receipt Evidence</h2>"
            f"<div class='{receipt_grid_class}'>"
            f"{chunk}"
            "</div>"
            "</section>"
        )

    total_reimbursable_aud = round(
        sum(
            float(expense.reimbursable_amount_aud)
            if expense.reimbursable_amount_aud is not None
            else float(expense.amount_aud)
            for expense in sorted_expenses
        ),
        2,
    )
    total_amount_aud = round(sum(float(expense.amount_aud) for expense in sorted_expenses), 2)
    total_gst_aud = round(sum(_gst_amount(expense) for expense in sorted_expenses), 2)
    generated_on = _format_date_au(date.today())
    if start_date and end_date:
        date_range_label = f"{_format_date_au(start_date)} to {_format_date_au(end_date)}"
    elif start_date:
        date_range_label = f"From {_format_date_au(start_date)}"
    elif end_date:
        date_range_label = f"Up to {_format_date_au(end_date)}"
    else:
        date_range_label = "All dates"

    logo_data_uri = _logo_data_uri(context="report")
    logo_html = f"<img class='brand-logo' src='{logo_data_uri}' alt='Adapsys logo' />" if logo_data_uri else ""
    date_range_html = f"<div class='meta'><strong>Date Range:</strong> {date_range_label}</div>"

    program_label = str(trip.program_name or "").strip()
    client_program_label = f"{trip.client_name} / {program_label}" if program_label else str(trip.client_name)
    report_title = f"Reimbursable Expense Report - {trip.client_name}"
    receipt_pages_html = "".join(receipt_pages)

    return f"""
<!doctype html>
<html>
  <head>
    <meta charset='utf-8' />
    <title>Adapsys Australia Pacific - Expenses Report</title>
    <style>
      @page {{ size: A4; margin: 12mm; }}
      :root {{
        --brand-teal: #006379;
        --brand-cyan: #00b8b8;
        --brand-pink: #ef2b97;
        --ink-main: #183a42;
        --ink-muted: #4b6a72;
        --line-soft: #d2e6e9;
        --surface-soft: #f4fbfc;
      }}
      body {{ font-family: Poppins, Arial, sans-serif; color: var(--ink-main); margin: 0; background: #f5f8f9; position: relative; }}
      .page-frame {{ position: fixed; top: 2.5mm; right: 2.5mm; bottom: 2.5mm; left: 2.5mm; border: 1px solid rgba(0, 99, 121, 0.18); border-radius: 10px; box-shadow: inset 0 0 0 1px rgba(0, 184, 184, 0.07); pointer-events: none; z-index: -1; }}
      .report-shell {{ border: 0; border-radius: 12px; padding: 12px; background: #ffffff; box-shadow: none; position: relative; z-index: 1; }}
      .brand-bar {{ height: 8px; background: linear-gradient(90deg, #00b8b8, #006379, #ef2b97); border-radius: 999px; margin-bottom: 18px; }}
      h1 {{ margin: 0 0 2px; color: var(--brand-teal); font-size: 29px; line-height: 1.05; letter-spacing: 0.01em; }}
      .report-subtitle {{ margin: 6px 0 10px; font-size: 15px; color: #0c7f93; font-weight: 700; letter-spacing: 0.02em; text-transform: uppercase; }}
      h2 {{ margin: 0 0 9px; color: var(--brand-teal); font-size: 17px; }}
      .meta {{ color: var(--ink-muted); margin-bottom: 8px; font-size: 11px; }}
      .meta-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 16px; margin: 8px 0 10px; }}
      .meta-grid .meta {{ margin: 0; }}
      .report-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 6px; }}
      .report-title-block {{ flex: 1; }}
      .brand-logo {{ max-height: 54px; max-width: 220px; object-fit: contain; }}
      .issuer-card {{ width: 100%; box-sizing: border-box; border: 1px solid #cde7e7; border-radius: 10px; padding: 11px 12px; background: linear-gradient(170deg, #f4fcfd, #ffffff); margin-bottom: 10px; }}
      .issuer-name {{ font-size: 13px; font-weight: 700; color: var(--brand-teal); margin-bottom: 4px; }}
      .issuer-line {{ font-size: 11.5px; color: var(--ink-muted); line-height: 1.4; }}
      .summary-strip {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 10px 0 12px; }}
      .summary-pill {{ border: 1px solid #00b8b8; border-radius: 10px; background:
        radial-gradient(115% 145% at -14% 118%, rgba(0, 184, 184, 0.17) 0 36%, transparent 37%),
        radial-gradient(92% 130% at 112% -18%, rgba(0, 99, 121, 0.13) 0 34%, transparent 35%),
        linear-gradient(175deg, #e8fdfd, #f8ffff);
        padding: 10px 12px; color: #00586a; font-weight: 700; }}
      .summary-pill.secondary {{ border-color: #cde7e7; background:
        radial-gradient(120% 140% at -12% 116%, rgba(0, 184, 184, 0.11) 0 34%, transparent 35%),
        radial-gradient(95% 132% at 112% -18%, rgba(239, 43, 151, 0.09) 0 33%, transparent 34%),
        #f4fbfb;
        font-weight: 600; color: #335861; }}
      .section-card {{ border: 1px solid var(--line-soft); border-radius: 10px; padding: 8px 9px 10px; background:
        radial-gradient(150% 165% at -14% 116%, rgba(0, 184, 184, 0.09) 0 34%, transparent 35%),
        radial-gradient(92% 130% at 112% -18%, rgba(239, 43, 151, 0.07) 0 33%, transparent 34%),
        #fff;
        margin-top: 12px; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
      th, td {{ border: 1px solid #d6e3e3; padding: 7px; vertical-align: top; }}
      th {{ background: linear-gradient(180deg, #ecf8f9, #e3f3f4); text-align: left; color: #1b4d57; font-weight: 700; }}
      th.num {{ text-align: right; }}
      tbody tr:nth-child(even) td {{ background: var(--surface-soft); }}
      .line-items-table {{ table-layout: fixed; font-size: 9.6px; }}
      .line-items-table th, .line-items-table td {{ padding: 5px 6px; overflow-wrap: anywhere; word-break: break-word; line-height: 1.2; }}
      .line-items-table .num {{ text-align: right; white-space: nowrap; }}
      .line-items-table .cat-icon {{ text-align: center; padding-left: 10px; padding-right: 10px; }}
      .category-chip {{ display: inline-flex; align-items: center; justify-content: flex-start; gap: 8px; width: 132px; border-radius: 999px; border: 1px solid #b7d5da; padding: 1px 9px 1px 4px; font-weight: 600; font-size: 9.2px; white-space: nowrap; max-width: 100%; box-sizing: border-box; }}
      .category-chip-icon {{ display: inline-flex; align-items: center; justify-content: center; min-width: 17px; height: 17px; padding: 0 2px 0 1px; margin-right: 1px; border-radius: 0; background: transparent; font-size: 10.2px; font-weight: 700; color: currentColor; letter-spacing: 0.01em; }}
      .category-token {{ display: inline-flex; align-items: center; justify-content: center; min-width: auto; height: auto; padding: 0; border-radius: 0; background: transparent; font-size: 11px; font-weight: 700; color: #2f5d66; letter-spacing: 0.01em; }}
      .category-chip.cat-flight {{ color: #00586a; background: #e9f9ff; border-color: #9bd7ee; }}
      .category-chip.cat-accommodation {{ color: #1f4f5c; background: #eafdf7; border-color: #95dbc9; }}
      .category-chip.cat-transport {{ color: #4c3a62; background: #f2ecff; border-color: #cab8f6; }}
      .category-chip.cat-meals {{ color: #6b3e28; background: #fff3eb; border-color: #f2c9a9; }}
      .category-chip.cat-perdiem {{ color: #70493a; background: #fff8ea; border-color: #e7c88f; }}
      .category-chip.cat-misc {{ color: #5a4f6e; background: #f7eefb; border-color: #d8bde8; }}
      .category-chip.cat-default {{ color: #365258; background: #edf5f6; border-color: #bfd2d6; }}
      .totals {{ margin-top: 11px; margin-left: auto; min-width: 260px; font-weight: 700; color: var(--brand-teal); border-top: 1px dashed #bcd8dd; padding-top: 8px; display: grid; gap: 2px; justify-items: end; text-align: right; }}
      .receipt-page {{ page-break-before: always; page-break-after: always; margin-top: 4px; }}
      .receipt-page.is-last {{ page-break-after: auto; }}
      .receipt-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
      .receipt-card {{ border: 1px solid #cfe1e1; border-radius: 9px; padding: 0; min-height: 118mm; break-inside: avoid; background: #fff; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 1px 0 rgba(0, 99, 121, 0.08); }}
      .receipt-card-head {{ font-weight: 700; color: #006379; margin-bottom: 0; font-size: 10px; line-height: 1.2; }}
      .receipt-card-head-meta {{ display: grid; grid-template-columns: 1.45fr 0.9fr 1fr; border-bottom: 1px solid #d6e3e3; font-size: 7.6px; color: #375860; background: linear-gradient(180deg, #eef8f9, #f8fcfc); }}
      .receipt-card-head-meta span {{ padding: 6px 6px; border-right: 1px solid #d6e3e3; }}
      .receipt-card-head-meta span:last-child {{ border-right: 0; }}
      .receipt-card-sub {{ color: #3d5d63; font-size: 8px; margin-top: 3px; line-height: 1.25; }}
      .receipt-meta-small {{ color: #587378; font-size: 7px; }}
      .receipt-image {{ width: 100%; flex: 1; min-height: 88mm; max-height: 98mm; object-fit: contain; border: 0; border-radius: 0; margin-top: 0; background: #fff; }}
      .receipt-placeholder {{ margin-top: 0; border: 1px dashed #c9d7d7; border-radius: 0; padding: 6px; font-size: 8.6px; color: #547074; flex: 1; }}
      .receipt-blank {{ margin-top: 4px; border: 1px dashed #dce9ea; border-radius: 6px; min-height: 88mm; background: #fbfdfd; flex: 1; }}
      .boarding-pass-stack {{ display: grid; grid-template-rows: 1fr 1fr; gap: 6px; min-height: 88mm; flex: 1; }}
      .boarding-pass-image {{ min-height: 0; max-height: none; height: 100%; }}
      .receipt-page h2 {{ margin-bottom: 6px; }}
      .report-footer {{ position: fixed; bottom: 6mm; left: 14mm; right: 14mm; display: flex; justify-content: space-between; align-items: center; font-size: 9px; color: #5d797f; }}
      .report-footer-page::after {{ content: 'Page ' counter(page) ' of ' counter(pages); }}
      @media print {{
        .report-footer {{ position: fixed; bottom: 6mm; left: 14mm; right: 14mm; }}
      }}
    </style>
  </head>
  <body>
    <div class='page-frame'></div>
    <div class='report-shell'>
    <div class='brand-bar'></div>
    <div class='report-header'>
      <div class='report-title-block'>
        <h1>{report_title}</h1>
      </div>
      <div>{logo_html}</div>
    </div>
    <div class='issuer-card'>
      <div class='issuer-name'>{REPORT_ISSUER_NAME}</div>
      <div class='issuer-line'>{REPORT_ISSUER_ABN}</div>
      <div class='issuer-line'>{REPORT_ISSUER_ADDRESS}</div>
    </div>
    <div class='summary-strip'>
      <div class='summary-pill'>Total Expenses: AUD {total_amount_aud:.2f}</div>
      <div class='summary-pill secondary'>Total GST: AUD {total_gst_aud:.2f}</div>
    </div>
    <div class='meta-grid'>
      <div class='meta'><strong>Activity:</strong> {trip.name}</div>
      <div class='meta'><strong>Client / Program:</strong> {client_program_label}</div>
      {date_range_html}
      <div class='meta'><strong>Generated:</strong> {generated_on}</div>
    </div>

    <section class='section-card'>
      <h2>Summary by Category</h2>
      <table>
        <thead><tr><th>Category</th><th style='text-align:right;'>Total (AUD)</th></tr></thead>
        <tbody>{category_rows or "<tr><td colspan='2'>No expenses</td></tr>"}</tbody>
      </table>
    </section>

    <section class='section-card'>
      <h2>Expense Items</h2>
      <table class='line-items-table'>
      <colgroup>
        <col style='width: 10%;' />
        <col style='width: 11%;' />
        <col style='width: 40%;' />
        <col style='width: 12%;' />
        <col style='width: 15%;' />
        <col style='width: 12%;' />
      </colgroup>
      <thead>
        <tr>
          <th>Date</th><th>Category</th><th>Description</th><th>Supplier</th><th class='num'>Amount</th><th class='num'>GST</th>
        </tr>
      </thead>
      <tbody>{''.join(expense_rows) or "<tr><td colspan='6'>No expenses</td></tr>"}</tbody>
      </table>
    </section>

    <div class='totals'>
      <div>Total: AUD {total_amount_aud:.2f}</div>
      <div>Total GST: AUD {total_gst_aud:.2f}</div>
    </div>
    {receipt_pages_html}
    <div class='report-footer'>
      <div>Adapsys Australia Pacific</div>
      <div class='report-footer-page'></div>
    </div>
    </div>
  </body>
</html>
"""


@router.get("/{trip_id}/expense-pack", response_class=HTMLResponse)
def expense_pack_preview(
    trip_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    actor: RequestActor = Depends(get_request_actor),
) -> str:
    require_roles(actor, {"admin", "finance"})
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")
    trip = _find_trip(trip_id)
    expenses = [
        expense
        for expense in _trip_expenses(trip_id)
        if _expense_within_range(expense, start_date=start_date, end_date=end_date)
    ]
    return _build_report_html(trip, expenses, start_date=start_date, end_date=end_date)


@router.get("/{trip_id}/final-expense-pack.pdf")
def expense_pack_pdf(
    trip_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    actor: RequestActor = Depends(get_request_actor),
) -> Response:
    require_roles(actor, {"admin", "finance"})
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")
    trip = _find_trip(trip_id)
    expenses = [
        expense
        for expense in _trip_expenses(trip_id)
        if _expense_within_range(expense, start_date=start_date, end_date=end_date)
    ]
    html = _build_report_html(trip, expenses, start_date=start_date, end_date=end_date)

    try:
        from weasyprint import HTML
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=503,
            detail=f"PDF engine unavailable. Install weasyprint to enable PDF export. ({exc})",
        )

    pdf_bytes = HTML(string=html).write_pdf()
    headers = {
        "Content-Disposition": f"attachment; filename=adapsys-australia-pacific-expenses-report-{trip_id}.pdf",
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


def _build_coaching_report_html(
    report_by: str,
    report_value: str,
    start_date: date | None,
    end_date: date | None,
) -> str:
    coach_name_by_email = {
        str(row.email or "").strip().lower(): str(row.name or "").strip()
        for row in [*list_coaches(), *list_consultants()]
        if str(row.email or "").strip() and str(row.name or "").strip()
    }

    def _coach_label_from_email(email: str | None) -> str:
        normalized = str(email or "").strip().lower()
        return _display_name_from_email(normalized, coach_name_by_email)

    report_by_norm = report_by.strip().lower()
    report_value_norm = _normalize_scope_text(report_value)
    engagements_source = list_all_engagements_for_reports()
    if report_by_norm == "coach":
        engagements = [
            row
            for row in engagements_source
            if _normalize_scope_text(row.coach_email) == report_value_norm
        ]
        report_by_label = "Coach"
        scope_label = _coach_label_from_email(report_value)
    elif report_by_norm == "coachee":
        engagements = [
            row
            for row in engagements_source
            if _normalize_scope_text(row.name) == report_value_norm
        ]
        report_by_label = "Coachee"
        scope_label = report_value
    else:
        engagements = [
            row
            for row in engagements_source
            if _client_matches_scope(row.client_org, report_value_norm)
        ]
        report_by_label = "Client"
        scope_label = report_value
    engagement_by_id = {row.id: row for row in engagements}

    sessions = [
        row
        for row in list_all_sessions_for_reports()
        if row.engagement_id in engagement_by_id
        and (start_date is None or row.session_date >= start_date)
        and (end_date is None or row.session_date <= end_date)
    ]

    sessions_by_engagement_id: dict[UUID, list] = defaultdict(list)
    completed_sessions_total = 0
    no_show_sessions_total = 0

    for session in sessions:
        sessions_by_engagement_id[session.engagement_id].append(session)
        if session.session_type == "completed":
            completed_sessions_total += 1
        if str(session.session_type or "").strip().lower().startswith("no_show"):
            no_show_sessions_total += 1

    client_names = sorted(
        {
            str(engagement.client_org or "").strip()
            for engagement in engagements
            if str(engagement.client_org or "").strip()
        }
    )
    client_scope_label = ", ".join(client_names) if client_names else "Unspecified"

    def _engagement_row_html(engagement) -> str:
        return (
            "<tr>"
            f"<td>{str(engagement.name or '').strip() or 'Unknown'}</td>"
            f"<td>{_coach_label_from_email(engagement.coach_email)}</td>"
            f"<td class='num'>{int(engagement.total_sessions or 0)}</td>"
            f"<td class='num'>{sum(1 for session in sessions_by_engagement_id.get(engagement.id, []) if str(session.session_type or '').strip().lower() == 'completed')}</td>"
            f"<td class='num'>{sum(1 for session in sessions_by_engagement_id.get(engagement.id, []) if str(session.session_type or '').strip().lower().startswith('no_show'))}</td>"
            f"<td class='num'>{sum(1 for session in sessions_by_engagement_id.get(engagement.id, []) if bool(getattr(session, 'lcp_debrief', False)))}</td>"
            "<td>"
            + (
                "".join(
                    "<div class='session-log-line'>"
                    f"{_format_date_au(session.session_date)} - {('Completed' if str(session.session_type or '').strip().lower() == 'completed' else ('No Show' if str(session.session_type or '').strip().lower().startswith('no_show') else str(session.session_type or '').replace('_', ' ').title()))}{(' · LCP de-brief ' + _format_date_au(getattr(session, 'lcp_debrief_date')) if bool(getattr(session, 'lcp_debrief', False)) and getattr(session, 'lcp_debrief_date', None) else (' · LCP de-brief (date not set)' if bool(getattr(session, 'lcp_debrief', False)) else ''))}"
                    "</div>"
                    for session in sorted(
                        sessions_by_engagement_id.get(engagement.id, []),
                        key=lambda row: (str(row.session_date or ""), str(row.id)),
                    )
                )
                or "<div class='session-log-line muted'>No sessions logged</div>"
            )
            + "</td>"
            "</tr>"
        )

    if report_by_norm == "coach":
        grouped_engagements: dict[str, list[EngagementOut]] = defaultdict(list)
        for engagement in engagements:
            client_label = str(engagement.client_org or "").strip() or "Unspecified"
            grouped_engagements[client_label].append(engagement)

        coaching_session_rows_parts: list[str] = []
        for client_label in sorted(grouped_engagements, key=lambda value: value.lower()):
            coaching_session_rows_parts.append(
                f"<tr class='client-group-row'><td colspan='7'><strong>Client:</strong> {client_label}</td></tr>"
            )
            for engagement in sorted(
                grouped_engagements[client_label],
                key=lambda row: str(row.name or "").strip().lower(),
            ):
                coaching_session_rows_parts.append(_engagement_row_html(engagement))
        coaching_session_rows = "".join(coaching_session_rows_parts)
    else:
        coaching_session_rows = "".join(
            _engagement_row_html(engagement)
            for engagement in sorted(
                engagements,
                key=lambda row: (
                    str(row.name or "").strip().lower(),
                    _coach_label_from_email(row.coach_email).lower(),
                ),
            )
        )

    logo_data_uri = _logo_data_uri(context="report")
    logo_html = (
        f"<img class='brand-logo' src='{logo_data_uri}' alt='Adapsys logo' />"
        if logo_data_uri
        else ""
    )

    if start_date and end_date:
        range_label = f"{_format_date_au(start_date)} to {_format_date_au(end_date)}"
    elif start_date:
        range_label = f"From {_format_date_au(start_date)}"
    elif end_date:
        range_label = f"Up to {_format_date_au(end_date)}"
    else:
        range_label = "All dates"

    return f"""
<!doctype html>
<html>
  <head>
    <meta charset='utf-8' />
    <title>Adapsys Australia Pacific Coaching Report</title>
    <style>
      @page {{ size: A4; margin: 12mm; }}
      :root {{
        --brand-teal: #006379;
        --brand-cyan: #00b8b8;
        --brand-pink: #ef2b97;
        --ink-main: #183a42;
        --ink-muted: #4b6a72;
        --line-soft: #d2e6e9;
        --surface-soft: #f4fbfc;
      }}
      body {{ font-family: Poppins, Arial, sans-serif; color: var(--ink-main); margin: 0; background: #f5f8f9; }}
      .report-shell {{ border: 1px solid var(--line-soft); border-radius: 12px; padding: 12px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 99, 121, 0.08); }}
      .brand-bar {{ height: 8px; background: linear-gradient(90deg, #00b8b8, #006379, #ef2b97); border-radius: 999px; margin-bottom: 16px; }}
      h1 {{ margin: 0 0 2px; color: var(--brand-teal); font-size: 28px; line-height: 1.04; letter-spacing: 0.01em; }}
      h2 {{ margin: 0 0 8px; color: var(--brand-teal); font-size: 17px; }}
      .report-subtitle {{ margin: 6px 0 10px; font-size: 12px; color: #0c7f93; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase; }}
      .meta {{ color: var(--ink-muted); margin: 0; font-size: 11px; }}
      .meta-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 16px; margin: 8px 0 10px; }}
      .report-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; margin-bottom: 8px; }}
      .report-title-block {{ flex: 1; }}
      .brand-logo {{ max-height: 52px; max-width: 210px; object-fit: contain; }}
      .issuer-card {{ width: 100%; box-sizing: border-box; border: 1px solid #cde7e7; border-radius: 10px; padding: 11px 12px; background: linear-gradient(170deg, #f4fcfd, #ffffff); margin-bottom: 10px; }}
      .issuer-name {{ font-size: 13px; font-weight: 700; color: var(--brand-teal); margin-bottom: 4px; }}
      .issuer-line {{ font-size: 11px; color: var(--ink-muted); line-height: 1.35; }}
      .kpi-strip {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 10px 0 12px; }}
      .kpi-card {{ border: 1px solid #bfe9e9; border-radius: 10px; background:
        radial-gradient(125% 150% at -14% 116%, rgba(0, 184, 184, 0.14) 0 34%, transparent 35%),
        radial-gradient(95% 128% at 112% -16%, rgba(239, 43, 151, 0.09) 0 32%, transparent 33%),
        linear-gradient(180deg, #f1fdfd, #fbffff);
        padding: 8px 10px; }}
      .kpi-label {{ font-size: 10px; color: #4d7076; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 2px; }}
      .kpi-value {{ font-size: 16px; font-weight: 700; color: var(--brand-teal); }}
      .section-card {{ border: 1px solid var(--line-soft); border-radius: 10px; padding: 8px 9px 10px; background:
        radial-gradient(150% 160% at -14% 116%, rgba(0, 184, 184, 0.09) 0 34%, transparent 35%),
        radial-gradient(94% 130% at 112% -18%, rgba(239, 43, 151, 0.07) 0 33%, transparent 34%),
        #fff;
        margin-top: 12px; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 7px; table-layout: fixed; }}
      th, td {{ border: 1px solid #d6e3e3; padding: 6px 7px; vertical-align: top; overflow-wrap: anywhere; word-break: break-word; font-size: 10px; line-height: 1.25; }}
      th {{ background: linear-gradient(180deg, #ecf8f9, #e3f3f4); text-align: left; color: #1c5661; font-weight: 700; }}
      tbody tr:nth-child(even) td {{ background: var(--surface-soft); }}
      .num {{ text-align: right; white-space: nowrap; }}
      .session-table col:nth-child(1) {{ width: 18%; }}
      .session-table col:nth-child(2) {{ width: 15%; }}
      .session-table col:nth-child(3) {{ width: 12%; }}
      .session-table col:nth-child(4) {{ width: 12%; }}
      .session-table col:nth-child(5) {{ width: 9%; }}
      .session-table col:nth-child(6) {{ width: 9%; }}
      .session-table col:nth-child(7) {{ width: 25%; }}
      .session-table thead th {{
        padding-top: 12px;
        padding-bottom: 12px;
        line-height: 1.3;
        white-space: normal;
      }}
      .client-group-row td {{ background: #eaf7f8; color: #1f5f69; font-weight: 700; }}
      .session-log-line {{ margin: 0 0 2px; }}
      .session-log-line:last-child {{ margin-bottom: 0; }}
      .session-log-line.muted {{ color: #6e878d; }}
      .report-footer {{ margin-top: 10px; font-size: 10px; color: #5d797f; text-align: right; }}
    </style>
  </head>
  <body>
    <div class='report-shell'>
      <div class='brand-bar'></div>
      <div class='report-header'>
        <div class='report-title-block'>
          <h1>Adapsys Australia Pacific</h1>
          <div class='report-subtitle'>Coaching Session Report</div>
        </div>
        <div>{logo_html}</div>
      </div>
      <div class='issuer-card'>
        <div class='issuer-name'>{REPORT_ISSUER_NAME}</div>
        <div class='issuer-line'>{REPORT_ISSUER_ABN}</div>
        <div class='issuer-line'>{REPORT_ISSUER_ADDRESS}</div>
      </div>
      <div class='meta-grid'>
        <div class='meta'><strong>Report Scope:</strong> {scope_label}</div>
        <div class='meta'><strong>Client(s):</strong> {client_scope_label}</div>
        <div class='meta'><strong>Date Range:</strong> {range_label}</div>
        <div class='meta'><strong>Generated:</strong> {_format_date_au(date.today())}</div>
      </div>

      <div class='kpi-strip'>
        <div class='kpi-card'>
          <div class='kpi-label'>Sessions Logged</div>
          <div class='kpi-value'>{len(sessions)}</div>
        </div>
        <div class='kpi-card'>
          <div class='kpi-label'>Completed Sessions</div>
          <div class='kpi-value'>{completed_sessions_total}</div>
        </div>
        <div class='kpi-card'>
          <div class='kpi-label'>No-Show Sessions</div>
          <div class='kpi-value'>{no_show_sessions_total}</div>
        </div>
      </div>

      <section class='section-card'>
        <h2>Coaching Sessions</h2>
        <table class='session-table'>
          <colgroup><col /><col /><col /><col /><col /><col /><col /></colgroup>
          <thead><tr><th>Coachee</th><th>Coach</th><th class='num'>Sessions Entitled</th><th class='num'>Sessions Completed</th><th class='num'>No Show</th><th class='num'>LCP de-brief</th><th>Session Dates</th></tr></thead>
          <tbody>{coaching_session_rows or "<tr><td colspan='7'>No sessions in selected range</td></tr>"}</tbody>
        </table>
      </section>

      <div class='report-footer'>Generated: {_format_date_au(date.today())}</div>
    </div>
  </body>
</html>
"""


@router.get("/coaching/summary", response_class=HTMLResponse)
def coaching_report_preview(
    report_by: str = "client",
    client_org: str | None = None,
    coach_email: str | None = None,
    coachee_name: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    actor: RequestActor = Depends(get_request_actor),
) -> str:
    require_roles(actor, {"admin", "finance"})
    report_by_norm = report_by.strip().lower()
    if report_by_norm not in {"client", "coach", "coachee"}:
        raise HTTPException(status_code=422, detail="report_by must be one of 'client', 'coach', or 'coachee'")
    if report_by_norm == "client":
        report_value = (client_org or "").strip()
        required_field = "client_org"
    elif report_by_norm == "coach":
        report_value = (coach_email or "").strip()
        required_field = "coach_email"
    else:
        report_value = (coachee_name or "").strip()
        required_field = "coachee_name"
    if not report_value:
        raise HTTPException(status_code=422, detail=f"{required_field} is required")
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")
    return _build_coaching_report_html(
        report_by=report_by_norm,
        report_value=report_value,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/coaching/summary.pdf")
def coaching_report_pdf(
    report_by: str = "client",
    client_org: str | None = None,
    coach_email: str | None = None,
    coachee_name: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    actor: RequestActor = Depends(get_request_actor),
) -> Response:
    require_roles(actor, {"admin", "finance"})
    report_by_norm = report_by.strip().lower()
    if report_by_norm not in {"client", "coach", "coachee"}:
        raise HTTPException(status_code=422, detail="report_by must be one of 'client', 'coach', or 'coachee'")
    if report_by_norm == "client":
        report_value = (client_org or "").strip()
        required_field = "client_org"
    elif report_by_norm == "coach":
        report_value = (coach_email or "").strip()
        required_field = "coach_email"
    else:
        report_value = (coachee_name or "").strip()
        required_field = "coachee_name"
    if not report_value:
        raise HTTPException(status_code=422, detail=f"{required_field} is required")

    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")

    html = _build_coaching_report_html(
        report_by=report_by_norm,
        report_value=report_value,
        start_date=start_date,
        end_date=end_date,
    )

    try:
        from weasyprint import HTML
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=503,
            detail=f"PDF engine unavailable. Install weasyprint to enable PDF export. ({exc})",
        )

    safe_target = re.sub(r"[^a-z0-9]+", "-", report_value.strip().lower()).strip("-") or "report"
    pdf_bytes = HTML(string=html).write_pdf()
    headers = {
        "Content-Disposition": f"attachment; filename=adapsys-australia-pacific-coaching-report-{report_by_norm}-{safe_target}.pdf",
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get("/coaching/client-summary", response_model=list[ClientCoachingSummaryRow])
def coaching_client_summary(
    client_org: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    actor: RequestActor = Depends(get_request_actor),
) -> list[ClientCoachingSummaryRow]:
    if not _is_client_reports_enabled():
        raise HTTPException(status_code=404, detail="Client coaching reports are not enabled")

    require_roles(actor, {"admin", "finance", "client_viewer"})
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")

    if actor.role == "client_viewer":
        if not actor.client_org:
            raise HTTPException(status_code=403, detail="Client account is missing client_org scope")
        target_client_org = actor.client_org
    else:
        target_client_org = str(client_org or "").strip()
        if not target_client_org:
            raise HTTPException(status_code=422, detail="client_org is required")

    engagements = [
        row
        for row in list_all_engagements_for_reports()
        if _client_matches_scope(row.client_org, target_client_org)
    ]
    engagement_by_id = {row.id: row for row in engagements}

    sessions_by_engagement_id: dict[UUID, list] = defaultdict(list)
    for row in list_all_sessions_for_reports():
        if row.engagement_id not in engagement_by_id:
            continue
        if start_date is not None and row.session_date < start_date:
            continue
        if end_date is not None and row.session_date > end_date:
            continue
        sessions_by_engagement_id[row.engagement_id].append(row)

    coach_name_by_email = {
        str(entry.email or "").strip().lower(): str(entry.name or "").strip()
        for entry in [*list_coaches(), *list_consultants()]
        if str(entry.email or "").strip() and str(entry.name or "").strip()
    }

    rows: list[ClientCoachingSummaryRow] = []
    for engagement in sorted(
        engagements,
        key=lambda row: (
            str(row.name or "").strip().lower(),
            _display_name_from_email(str(row.coach_email or "").strip().lower(), coach_name_by_email).lower(),
        ),
    ):
        sessions = sorted(
            sessions_by_engagement_id.get(engagement.id, []),
            key=lambda row: (str(row.session_date or ""), str(row.id)),
        )
        sessions_taken = sum(
            1
            for session in sessions
            if str(session.session_type or "").strip().lower() in {"completed", "no_show_chargeable"}
        )
        no_show_count = sum(
            1
            for session in sessions
            if str(session.session_type or "").strip().lower().startswith("no_show")
        )
        lcp_taken = sum(1 for session in sessions if bool(getattr(session, "lcp_debrief", False)))
        lcp_available = bool(getattr(engagement, "lcp_debrief_enabled", False))

        rows.append(
            ClientCoachingSummaryRow(
                coachee=str(engagement.name or "").strip() or "Unknown",
                coach_name=_display_name_from_email(str(engagement.coach_email or "").strip().lower(), coach_name_by_email),
                entitled_sessions=int(engagement.total_sessions or 0),
                sessions_taken=sessions_taken,
                sessions_left=max(int(engagement.total_sessions or 0) - sessions_taken, 0),
                no_show_count=no_show_count,
                session_dates=[_format_date_au(session.session_date) for session in sessions],
                lcp_available=lcp_available,
                lcp_entitled=int(engagement.lcp_debrief_total_sessions or 0) if lcp_available else None,
                lcp_taken=lcp_taken if lcp_available else None,
            )
        )

    return rows
