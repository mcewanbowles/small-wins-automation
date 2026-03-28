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

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

## Notes

Environment variables and full architecture are documented in:

- `../ADAPYS_PORTAL_ARCHITECTURE.md`
- `../ADAPYS_OPS_PORTAL_BRIEF.md`
- `../ADAPYS_BRAND_STYLE_GUIDE.md`

## Production domain (adapsysauspac.com)

Set these values in your production hosting platform:

- Backend env
  - `APP_URL=https://adapsysauspac.com`
  - `CORS_ALLOWED_ORIGINS=https://adapsysauspac.com,https://www.adapsysauspac.com`
- Frontend env (if frontend is hosted separately)
  - `VITE_API_BASE=https://adapsysauspac.com`

If backend and frontend are served from the same origin, `VITE_API_BASE` can be left empty and the app will use same-origin API calls.
