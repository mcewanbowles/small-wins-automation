# ListingLift by EasyPrep

Minimal local MVP for digital product sellers:
- Platform selector (TPT, Etsy, Gumroad)
- Customer-friendly listing draft workflow with profile questions
- Niche Engine (high-demand/low-competition finder, currently TPT-only)
- Winnable Right Now filtering by your current store review band (TPT-only)
- Listing Generator (Claude model: `claude-sonnet-4-20250514`) with platform-specific title/tag limits
- Basic Listing Audit (TPT/Etsy/Gumroad, score /100 + recommended fixes)

## 1) One-time setup (Windows)

From this folder (`ListingList`), run:

```powershell
.\setup_local.ps1
```

This script will:
- Create `backend/.venv`
- Install backend requirements
- Install frontend packages
- Copy `.env.example` files to `.env` if missing

## 2) Add your API key

Open `backend/.env` and set:

```env
ANTHROPIC_API_KEY=your_key_here
```

## 3) Add EasyPrep logo

Place your logo at:

`frontend/public/easyprep-logo.png`

If missing, the app uses an EP fallback monogram.

## 4) Run app locally

```powershell
.\run_local.ps1
```

This opens two PowerShell windows:
- Frontend: first available from http://127.0.0.1:5173-5176
- Backend: first available from http://127.0.0.1:8000-8003

## 5) Browser extension (Chrome / Edge)

A lightweight extension scaffold is included at:

`browser-extension/`

### Load extension locally

1. Open Chrome `chrome://extensions` (or Edge `edge://extensions`).
2. Turn on **Developer mode**.
3. Click **Load unpacked**.
4. Select the `ListingList/browser-extension` folder.

### What it does

- Quick keyword check (TPT endpoint)
- Quick listing draft (title + tags)
- One-click **Open full app**
- Stores API URL and App URL in browser extension storage

Default local URLs:
- API: `http://localhost:8000`
- App: `http://localhost:5173`

If you deploy ListingLift, update those two settings in the extension popup.

## MVP notes

- Listing Generator supports these stores: **TPT, Etsy, Gumroad**.
- Niche Engine + Winnable are currently **TPT-only** and clearly labeled in-app.
- Listing Audit supports **TPT, Etsy, Gumroad**.
- Keyword suggestions keep **Google API order first**.
- Gold-only filter shows only `MAKE_THIS` rows.
- Winnable toggle defaults ON and uses your selected store level.
- Keyword table includes estimated page-1 review competitiveness fields.
- Listing Generator returns title, tags (if platform uses tags), description opener, snippet, and full description.
- Listing Audit scores title, description, tags, and SEO coverage with prioritized fixes.
- TPT supply thresholds:
  - 0-50: MAKE THIS
  - 51-200: WORTH A SHOT
  - 200+: CROWDED
