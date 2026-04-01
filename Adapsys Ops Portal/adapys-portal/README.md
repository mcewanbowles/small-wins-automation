# Adapsys Ops Portal (Standalone)

Expense-first standalone build for Adapsys Australia Pacific.

## Scope in this repo phase

- Expense Hub first (trip setup, per diem, receipt submission, approval)
- Coaching Hub next as a separate module/page
- Separate expense invoicing from coaching invoicing for now

## Stack

- Frontend: React + Tailwind (mobile-first)
- Backend: FastAPI
- Data + Storage + Auth: Supabase
- PDF: WeasyPrint (phase-2 in this scaffold)

## Project structure

- `backend/` FastAPI API
- `frontend/` React app

## Run (local)

### Easy start links (Windows)

- Friendly backend start page: `http://localhost:8000/start`
- One-click full launcher (backend + frontend): `START_ADAPSYS_ALL.cmd`
- One-click backend launcher: `START_ADAPSYS_BACKEND.cmd`
- One-click open start page: `OPEN_ADAPSYS_START.cmd`

### Fast phone test flow

1. Double-click `START_ADAPSYS_ALL.cmd`
2. On phone (same Wi-Fi), open: `http://<YOUR-PC-IP>:8000/start`
3. Tap **Open Consultant Session**

### Concise run (PC + phone)

1. Start everything: double-click `START_ADAPSYS_ALL.cmd`
2. PC admin link: `http://localhost:8000/start`
3. Phone consultant link: `http://<YOUR-PC-IP>:8000/start`

### Coaching data-entry ready when these 3 checks pass

1. Consultant link opens and session locks correctly
2. One coaching engagement can be created (admin/finance)
3. One coaching session can be logged (consultant/admin)

If all 3 pass, begin loading real coaching data.

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### Backend env (recommended)

Set these environment variables before starting backend:

- `SUPABASE_URL=https://<your-project-ref>.supabase.co`
- `SUPABASE_SERVICE_KEY=<service-role-key>`
- `SUPABASE_ANON_KEY=<anon-key>` (optional fallback)
- `ONEDRIVE_BACKUP_DIR=C:\Users\<you>\OneDrive\AdapsysBackups\backend-data`
- `ADAPSYS_XERO_SYNC_ENABLED=1` (enable expense->Xero scaffold endpoints)
- `ADAPSYS_XERO_SYNC_STUB_MODE=1` (default-safe demo mode; no live Xero call)

`ONEDRIVE_BACKUP_DIR` mirrors each local backup snapshot into a OneDrive-synced folder.
Backups are still written locally under `backend/data/backups`.

### Xero expense sync scaffold (demo-safe)

This repo includes a one-way Xero sync scaffold intended for demo-first rollout.

- Endpoint status list: `GET /expenses/xero-sync-status`
- Integration mode/config: `GET /expenses/xero-sync-config`
- Manual push/retry: `POST /expenses/{expense_id}/xero-sync`
- Allowed roles: `admin`, `finance`
- Allowed expense status before push: `approved` or `invoiced`

If `ADAPSYS_XERO_SYNC_STUB_MODE=1`, pushes return a safe stub success payload (`synced_stub`) and persist sync metadata without requiring any Xero credentials.

To expose the Expense Review sync controls in frontend, set localStorage key:

- `adapsys_xero_sync_enabled = 1`

### Admin savings snapshot tuning (optional)

Admin Console now includes a monthly Savings Snapshot panel. You can tune assumptions in localStorage:

- `adapsys_savings_hourly_rate_aud` (default `95`)
- `adapsys_savings_report_before_minutes` (default `45`)
- `adapsys_savings_report_after_minutes` (default `12`)
- `adapsys_savings_report_count_monthly` (default `12`)
- `adapsys_savings_workbook_followup_before_minutes` (default `30`)
- `adapsys_savings_workbook_followup_after_minutes` (default `8`)
- `adapsys_savings_workshop_count_monthly` (default `6`)
- `adapsys_savings_expense_double_entry_before_minutes` (default `6`)
- `adapsys_savings_expense_double_entry_after_minutes` (default `2`)

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

### One-time data migration to Supabase

After Supabase env vars are set, you can migrate local JSON cache data:

```powershell
python backend/scripts/migrate_local_json_to_supabase.py
```

Optional scope and batching:

```powershell
python backend/scripts/migrate_local_json_to_supabase.py --dry-run
python backend/scripts/migrate_local_json_to_supabase.py --datasets trips expenses
python backend/scripts/migrate_local_json_to_supabase.py --datasets all --batch-size 200
```

Current migration covers local datasets:

- `trips.json` -> `trips`
- `expenses.json` -> `expenses`
- `coaching_engagements.json` -> `engagements`
- `coaching_sessions.json` -> `sessions`
- `tenders.json` -> `tenders`

## Notes

Environment variables and full architecture are documented in:

- `../ADAPYS_PORTAL_ARCHITECTURE.md`
- `../ADAPYS_OPS_PORTAL_BRIEF.md`
- `../ADAPYS_BRAND_STYLE_GUIDE.md`

Demo and UX governance runbooks:

- `docs/DEMO_WEEK_PLAYBOOK.md`
- `docs/UX_ARCHITECTURE_CHECKPOINT_TEMPLATE.md`

## Production domain (adapsysauspac.com)

Set these values in your production hosting platform:

- Backend env
  - `APP_URL=https://adapsysauspac.com`
  - `CORS_ALLOWED_ORIGINS=https://adapsysauspac.com,https://www.adapsysauspac.com`
- Frontend env (if frontend is hosted separately)
  - `VITE_API_BASE=https://adapsysauspac.com`

If backend and frontend are served from the same origin, `VITE_API_BASE` can be left empty and the app will use same-origin API calls.
