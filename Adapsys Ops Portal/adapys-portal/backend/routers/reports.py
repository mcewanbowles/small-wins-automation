import base64
from collections import defaultdict
from datetime import date
from pathlib import Path
import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response

from backend.routers.coaching import list_all_engagements_for_reports, list_all_sessions_for_reports
from backend.routers.expenses import ExpenseOut, list_expenses
from backend.routers.security import RequestActor, get_request_actor, require_roles
from backend.routers.trips import TripOut, list_trips

router = APIRouter()

REPORT_ISSUER_NAME = "Adapsys Australia Pacific Pty Ltd"
REPORT_ISSUER_ABN = "ABN: [TO BE PROVIDED]"
REPORT_ISSUER_ADDRESS = "Unit 3, 18 Woodlands Way, Parkwood, Queensland 4214"


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


def _expense_within_range(expense: ExpenseOut, start_date: date | None, end_date: date | None) -> bool:
    raw_date = expense.expense_date
    expense_date = raw_date if isinstance(raw_date, date) else date.fromisoformat(str(raw_date))
    if start_date and expense_date < start_date:
        return False
    if end_date and expense_date > end_date:
        return False
    return True


def _find_logo_path() -> Path | None:
    here = Path(__file__).resolve()
    candidate_files = [
        "Adapsysgroup logo.png",
        "Adapsys Group Logo.png",
        "adapsysgroup logo.png",
        "adapsys-logo.png",
    ]

    candidate_paths: list[Path] = []
    for parent in here.parents:
        for file_name in candidate_files:
            candidate_paths.append(parent / file_name)

    return next((path for path in candidate_paths if path.exists()), None)


def _logo_data_uri() -> str | None:
    logo_path = _find_logo_path()
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
def report_brand_logo() -> FileResponse:
    logo_path = _find_logo_path()
    if logo_path is None:
        raise HTTPException(status_code=404, detail="Logo file not found")
    return FileResponse(str(logo_path), media_type="image/png")


def _build_report_html(
    trip: TripOut,
    expenses: list[ExpenseOut],
    start_date: date | None = None,
    end_date: date | None = None,
) -> str:
    totals_by_category: dict[str, float] = defaultdict(float)
    totals_by_person: dict[str, float] = defaultdict(float)

    for expense in expenses:
        totals_by_category[expense.category] += expense.amount_aud
        person = expense.submitted_by_email or "Unspecified"
        totals_by_person[person] += expense.amount_aud

    category_rows = "".join(
        f"<tr><td>{category}</td><td style='text-align:right;'>AUD {round(total, 2):.2f}</td></tr>"
        for category, total in sorted(totals_by_category.items())
    )

    person_rows = "".join(
        f"<tr><td>{person}</td><td style='text-align:right;'>AUD {round(total, 2):.2f}</td></tr>"
        for person, total in sorted(totals_by_person.items())
    )

    expense_rows = []
    for expense in sorted(expenses, key=lambda row: (row.expense_date, row.category)):
        per_diem_thumb_html = _per_diem_thumbnail_html(expense)
        if expense.receipt_url:
            thumbnail_ref = expense.receipt_thumb_url or ""
            full_ref = expense.receipt_url or ""
            image_ref = (
                thumbnail_ref
                if _looks_like_image_reference(thumbnail_ref)
                else full_ref
                if _looks_like_image_reference(full_ref)
                else ""
            )
            image_html = (
                f"<img src='{image_ref}' "
                "style='max-width:220px;max-height:160px;object-fit:contain;border:1px solid #d6e3e3;border-radius:6px;' />"
                if image_ref
                else "<div style='padding:6px 8px;border:1px dashed #d6e3e3;border-radius:6px;'>Receipt attached</div>"
            )
            receipt_html = f"{image_html}<div><a href='{expense.receipt_url}'>Open full receipt</a></div>"
        else:
            receipt_html = f"No receipt<br/><em>{expense.no_receipt_reason or ''}</em>"

        receipt_block_html = f"{per_diem_thumb_html}{receipt_html}"

        expense_rows.append(
            "<tr>"
            f"<td>{_format_date_au(expense.expense_date)}</td>"
            f"<td>{expense.category}</td>"
            f"<td>AUD {expense.amount_aud:.2f}</td>"
            f"<td>{expense.status}</td>"
            f"<td>{expense.submitted_by_email or 'Unspecified'}</td>"
            f"<td>{receipt_block_html}</td>"
            "</tr>"
        )

    total_aud = round(sum(expense.amount_aud for expense in expenses), 2)
    generated_on = _format_date_au(date.today())
    if start_date and end_date:
        date_range_label = f"{_format_date_au(start_date)} to {_format_date_au(end_date)}"
    elif start_date:
        date_range_label = f"From {_format_date_au(start_date)}"
    elif end_date:
        date_range_label = f"Up to {_format_date_au(end_date)}"
    else:
        date_range_label = "All dates"
    logo_data_uri = _logo_data_uri()
    logo_html = (
        f"<img class='brand-logo' src='{logo_data_uri}' alt='Adapsys logo' />"
        if logo_data_uri
        else ""
    )

    return f"""
<!doctype html>
<html>
  <head>
    <meta charset='utf-8' />
    <title>Adapsys Expense Pack</title>
    <style>
      body {{ font-family: Poppins, Arial, sans-serif; color: #16343a; margin: 28px; }}
      .brand-bar {{ height: 8px; background: linear-gradient(90deg, #00b8b8, #006379, #ef2b97); border-radius: 999px; margin-bottom: 18px; }}
      h1 {{ margin: 0 0 6px; color: #006379; }}
      h2 {{ margin: 18px 0 8px; color: #006379; font-size: 18px; }}
      .meta {{ color: #3d5d63; margin-bottom: 8px; }}
      .report-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 8px; }}
      .report-title-block {{ flex: 1; }}
      .brand-logo {{ max-height: 54px; max-width: 220px; object-fit: contain; }}
      .issuer-card {{ border: 1px solid #d6e3e3; border-radius: 8px; padding: 10px 12px; background: #f9fdfd; min-width: 320px; }}
      .issuer-name {{ font-size: 13px; font-weight: 700; color: #006379; margin-bottom: 4px; }}
      .issuer-line {{ font-size: 12px; color: #3d5d63; line-height: 1.4; }}
      .per-diem-thumb {{ border: 1px solid #d6e3e3; border-radius: 6px; padding: 6px; margin-bottom: 8px; background: #f8fcfc; }}
      .per-diem-thumb-title {{ font-size: 11px; font-weight: 700; color: #006379; margin-bottom: 4px; }}
      .per-diem-thumb table {{ margin-top: 0; font-size: 11px; }}
      .per-diem-thumb td {{ border: 1px solid #d6e3e3; padding: 4px 6px; }}
      .per-diem-thumb-total td {{ font-weight: 700; background: #e8f7f7; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
      th, td {{ border: 1px solid #d6e3e3; padding: 8px; vertical-align: top; }}
      th {{ background: #e8f7f7; text-align: left; }}
      .totals {{ margin-top: 10px; font-weight: 700; color: #006379; }}
    </style>
  </head>
  <body>
    <div class='brand-bar'></div>
    <div class='report-header'>
      <div class='report-title-block'>
        <h1>Adapsys Australia Pacific Ops Portal — Expense Pack</h1>
        <div class='issuer-card'>
          <div class='issuer-name'>{REPORT_ISSUER_NAME}</div>
          <div class='issuer-line'>{REPORT_ISSUER_ABN}</div>
          <div class='issuer-line'>{REPORT_ISSUER_ADDRESS}</div>
        </div>
      </div>
      <div>{logo_html}</div>
    </div>
    <div class='meta'><strong>Generated:</strong> {generated_on}</div>
    <div class='meta'><strong>Project:</strong> {trip.name}</div>
    <div class='meta'><strong>Client/Program:</strong> {trip.client_name} / {trip.program_name}</div>
    <div class='meta'><strong>Date Range:</strong> {date_range_label}</div>
    <div class='meta'><strong>Primary Consultant:</strong> {trip.consultant_email}</div>

    <h2>Summary by Category</h2>
    <table>
      <thead><tr><th>Category</th><th style='text-align:right;'>Total (AUD)</th></tr></thead>
      <tbody>{category_rows or "<tr><td colspan='2'>No expenses</td></tr>"}</tbody>
    </table>

    <h2>Summary by Person</h2>
    <table>
      <thead><tr><th>Expense For</th><th style='text-align:right;'>Total (AUD)</th></tr></thead>
      <tbody>{person_rows or "<tr><td colspan='2'>No expenses</td></tr>"}</tbody>
    </table>

    <h2>Line Items</h2>
    <table>
      <thead>
        <tr>
          <th>Date</th><th>Category</th><th>Amount</th><th>Status</th><th>Expense For</th><th>Receipt</th>
        </tr>
      </thead>
      <tbody>{''.join(expense_rows) or "<tr><td colspan='6'>No expenses</td></tr>"}</tbody>
    </table>

    <div class='totals'>Grand Total: AUD {total_aud:.2f}</div>
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
        "Content-Disposition": f"attachment; filename=adapsys-expense-pack-{trip_id}.pdf",
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


def _build_coaching_report_html(
    report_by: str,
    report_value: str,
    start_date: date | None,
    end_date: date | None,
) -> str:
    report_by_norm = report_by.strip().lower()
    report_value_norm = report_value.strip().lower()
    engagements_source = list_all_engagements_for_reports()
    if report_by_norm == "coach":
        engagements = [
            row
            for row in engagements_source
            if str(row.coach_email or "").strip().lower() == report_value_norm
        ]
        report_by_label = "Coach"
    elif report_by_norm == "coachee":
        engagements = [
            row
            for row in engagements_source
            if str(row.name or "").strip().lower() == report_value_norm
        ]
        report_by_label = "Coachee"
    else:
        engagements = [
            row
            for row in engagements_source
            if str(row.client_org or "").strip().lower() == report_value_norm
        ]
        report_by_label = "Client"
    engagement_by_id = {row.id: row for row in engagements}

    sessions = [
        row
        for row in list_all_sessions_for_reports()
        if row.engagement_id in engagement_by_id
        and (start_date is None or row.session_date >= start_date)
        and (end_date is None or row.session_date <= end_date)
    ]

    totals_by_coach: dict[str, dict[str, float]] = defaultdict(lambda: {"sessions": 0.0, "revenue": 0.0})
    sessions_by_engagement: dict = defaultdict(list)
    total_revenue = 0.0
    chargeable_sessions = 0
    completed_sessions_total = 0
    no_show_sessions_total = 0

    for session in sessions:
        engagement = engagement_by_id.get(session.engagement_id)
        if not engagement:
            continue
        sessions_by_engagement[session.engagement_id].append(session)
        session_rate = float(engagement.session_rate or 0)
        is_chargeable = session.session_type in {"completed", "no_show_chargeable"}
        if session.session_type == "completed":
            completed_sessions_total += 1
        if session.session_type == "no_show_chargeable":
            no_show_sessions_total += 1
        if is_chargeable:
            chargeable_sessions += 1
            total_revenue += session_rate
        coach_key = engagement.coach_email or "Unspecified"
        totals_by_coach[coach_key]["sessions"] += 1
        totals_by_coach[coach_key]["revenue"] += session_rate if is_chargeable else 0.0

    coachee_rows = "".join(
        "<tr>"
        f"<td>{engagement.name}</td>"
        f"<td>{engagement.coach_email or 'Unspecified'}</td>"
        f"<td style='text-align:right;'>{int(engagement.total_sessions or 0)}</td>"
        f"<td style='text-align:right;'>{sum(1 for row in sessions_by_engagement.get(engagement.id, []) if row.session_type == 'completed')}</td>"
        f"<td style='text-align:right;'>{sum(1 for row in sessions_by_engagement.get(engagement.id, []) if row.session_type == 'no_show_chargeable')}</td>"
        "</tr>"
        for engagement in sorted(engagements, key=lambda row: (str(row.name or "").lower(), str(row.coach_email or "").lower()))
    )

    coach_rows = "".join(
        "<tr>"
        f"<td>{coach}</td>"
        f"<td style='text-align:right;'>{int(values['sessions'])}</td>"
        f"<td style='text-align:right;'>AUD {values['revenue']:.2f}</td>"
        "</tr>"
        for coach, values in sorted(totals_by_coach.items())
    )

    session_rows = "".join(
        "<tr>"
        f"<td>{_format_date_au(session.session_date)}</td>"
        f"<td>{engagement_by_id.get(session.engagement_id).name if engagement_by_id.get(session.engagement_id) else 'Unknown'}</td>"
        f"<td>{engagement_by_id.get(session.engagement_id).coach_email if engagement_by_id.get(session.engagement_id) else 'Unknown'}</td>"
        f"<td>{session.session_type}</td>"
        f"<td>{session.duration_mins}</td>"
        "</tr>"
        for session in sorted(sessions, key=lambda row: row.session_date)
    )

    logo_data_uri = _logo_data_uri()
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
    <title>Coaching Report - Adapsys Australia Pacific</title>
    <style>
      body {{ font-family: Poppins, Arial, sans-serif; color: #16343a; margin: 28px; }}
      .brand-bar {{ height: 8px; background: linear-gradient(90deg, #00b8b8, #006379, #ef2b97); border-radius: 999px; margin-bottom: 18px; }}
      h1 {{ margin: 0 0 6px; color: #006379; }}
      h2 {{ margin: 18px 0 8px; color: #006379; font-size: 18px; }}
      .meta {{ color: #3d5d63; margin-bottom: 8px; }}
      .report-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 8px; }}
      .report-title-block {{ flex: 1; }}
      .brand-logo {{ max-height: 54px; max-width: 220px; object-fit: contain; }}
      .issuer-card {{ border: 1px solid #d6e3e3; border-radius: 8px; padding: 10px 12px; background: #f9fdfd; min-width: 320px; }}
      .issuer-name {{ font-size: 13px; font-weight: 700; color: #006379; margin-bottom: 4px; }}
      .issuer-line {{ font-size: 12px; color: #3d5d63; line-height: 1.4; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
      th, td {{ border: 1px solid #d6e3e3; padding: 8px; vertical-align: top; }}
      th {{ background: #e8f7f7; text-align: left; }}
      .totals {{ margin-top: 10px; font-weight: 700; color: #006379; }}
    </style>
  </head>
  <body>
    <div class='brand-bar'></div>
    <div class='report-header'>
      <div class='report-title-block'>
        <h1>Coaching Report - Adapsys Australia Pacific</h1>
        <div class='issuer-card'>
          <div class='issuer-name'>{REPORT_ISSUER_NAME}</div>
          <div class='issuer-line'>{REPORT_ISSUER_ABN}</div>
          <div class='issuer-line'>{REPORT_ISSUER_ADDRESS}</div>
        </div>
      </div>
      <div>{logo_html}</div>
    </div>
    <div class='meta'><strong>Report By:</strong> {report_by_label}</div>
    <div class='meta'><strong>Selection:</strong> {report_value}</div>
    <div class='meta'><strong>Date Range:</strong> {range_label}</div>
    <div class='meta'><strong>Generated:</strong> {_format_date_au(date.today())}</div>

    <h2>Coachee Session Progress</h2>
    <table>
      <thead><tr><th>Coachee</th><th>Coach</th><th style='text-align:right;'>Sessions Entitled</th><th style='text-align:right;'>Completed Sessions</th><th style='text-align:right;'>Chargeable No-Shows</th></tr></thead>
      <tbody>{coachee_rows or "<tr><td colspan='5'>No engagements in selected range</td></tr>"}</tbody>
    </table>

    <h2>Summary by Coach</h2>
    <table>
      <thead><tr><th>Coach</th><th style='text-align:right;'>Sessions Logged</th><th style='text-align:right;'>Chargeable Revenue</th></tr></thead>
      <tbody>{coach_rows or "<tr><td colspan='3'>No sessions in selected range</td></tr>"}</tbody>
    </table>

    <h2>Session Detail</h2>
    <table>
      <thead><tr><th>Date</th><th>Coachee</th><th>Coach</th><th>Type</th><th>Duration (mins)</th></tr></thead>
      <tbody>{session_rows or "<tr><td colspan='5'>No sessions in selected range</td></tr>"}</tbody>
    </table>

    <div class='totals'>Completed Sessions: {completed_sessions_total} | Chargeable No-Shows: {no_show_sessions_total} | Chargeable Sessions: {chargeable_sessions} | Estimated Revenue: AUD {total_revenue:.2f}</div>
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
        "Content-Disposition": f"attachment; filename=adapsys-coaching-report-{report_by_norm}-{safe_target}.pdf",
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
