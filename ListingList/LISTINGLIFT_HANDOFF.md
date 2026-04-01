# ListingLift Handoff (Current Source of Truth)

## Product positioning
- Main web app is primary.
- Browser extension is secondary/add-on for quick actions.
- Brand direction: EasyPrep / ListingLift, teal `#2D6E6E`, white CTA text.

## Current strategy focus
- TPT-first launch.
- Core differentiator: unserved niches (demand signals + low/weak supply), with beginner-safe guidance.
- Market messaging: "Opportunity score" + transparent confidence (do not claim exact search volume).

## Implemented features

### Main app (frontend + backend)
- Non-technical UX copy and onboarding flow (Wizard-lite).
- Platform-aware listing generation flow with customer profile inputs.
- Clear TPT-only messaging for features that are limited.
- Session save/load (Session menu).
- Export actions (keyword CSV, listing TXT).
- One-click actions:
  - Use keyword in draft
  - Use audit suggested title in draft
- Audit before/after title preview now includes:
  - current title
  - suggested title
  - reason
  - copy/apply action

### Niche Engine (TPT-first)
- Store-stage onboarding:
  - user selects TPT store stage (reviews band)
  - confirm/change flow
  - guidance defaults tailored (beginner-safe)
- Intent selector:
  - "I need an idea" vs "I have a theme/product"
- Cleaner controls:
  - example seed chips
  - Start Here filter visible
  - advanced filters behind "Advanced options" drawer
- Results hierarchy:
  - Top 3 recommendations shown first
  - full table moved into "All keyword results" collapsible
- Trust signals:
  - confidence indicator (High/Medium/Low)
  - source signal (Seen on TPT / Google / TPT + Google)
- Reverse Seller Intel (v0):
  - scans top TPT listing titles for a keyword
  - extracts recurring phrases + suggested angles
  - endpoint: `POST /api/reverse-intel`

### Browser extension scaffold
- Folder: `browser-extension/`
- Files: `manifest.json`, `popup.html`, `popup.css`, `popup.js`
- Features:
  - Save API URL + App URL
  - Quick keyword check
  - Quick listing draft
  - Copy results
  - Open full app
  - Improved status/error hints

## Key files changed
- `frontend/src/App.jsx`
- `frontend/src/styles.css`
- `frontend/src/api.js`
- `frontend/src/constants.js`
- `backend/app/keyword_service.py`
- `backend/app/reverse_intel_service.py`
- `backend/app/listing_service.py`
- `backend/app/models.py`
- `browser-extension/manifest.json`
- `browser-extension/popup.html`
- `browser-extension/popup.css`
- `browser-extension/popup.js`
- `README.md`

## Environment status
- Python exists and works.
- Node.js exists and frontend builds successfully (`npm run build`).
- Backend compiles successfully (`python -m compileall app`).

## Next operator steps
1. In `ListingList` PowerShell:
   - `node -v`
   - `npm -v`
2. Then run:
   - `./setup_local.ps1`
   - `./run_local.ps1`
3. Open app:
   - `http://localhost:5173`
4. Extension load path:
   - `ListingList/browser-extension`

## Deferred items
- Usage tiers / limits for cost control.
- Final visual brand polish pass (main app first, extension second).
- Reverse Seller Intel (top-seller long-tail extraction) to strengthen angle selection.
