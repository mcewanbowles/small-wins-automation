import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from backend.routers import ato_rates, auth, automations, coaching, expenses, health, lookups, portal, reports, tenders, trips

app = FastAPI(title="Adapsys Australia Pacific API", version="0.1.0")

APP_URL = (os.getenv("APP_URL") or "http://localhost:5173").strip().rstrip("/")


def _cors_origins() -> list[str]:
    configured = [
        origin.strip().rstrip("/")
        for origin in (os.getenv("CORS_ALLOWED_ORIGINS") or "").split(",")
        if origin.strip()
    ]
    default_origins = [
        APP_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    return list(dict.fromkeys(configured + default_origins))

COACH_ONLY_EMAILS = {"tony.liston@adapsysgroup.com"}
COACH_ONLY_ALLOWED_PREFIXES = (
    "/coaching",
    "/lookups/coaches",
    "/lookups/client-programs",
    "/reports/coaching",
    "/reports/brand-logo",
    "/health",
    "/auth",
)
COACH_ONLY_ALLOWED_EXACT = {"/", "/start"}


@app.middleware("http")
async def restrict_coach_only_access(request: Request, call_next):
    email = (request.headers.get("x-user-email") or "").strip().lower()
    path = request.url.path or ""
    if email in COACH_ONLY_EMAILS:
        if path not in COACH_ONLY_ALLOWED_EXACT and not any(
            path.startswith(prefix) for prefix in COACH_ONLY_ALLOWED_PREFIXES
        ):
            return JSONResponse(
                status_code=403,
                content={"detail": "Coach-only account. Access is limited to coaching pages."},
            )
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(portal.router, prefix="/portal", tags=["portal"])
app.include_router(lookups.router, prefix="/lookups", tags=["lookups"])
app.include_router(trips.router, prefix="/trips", tags=["trips"])
app.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
app.include_router(coaching.router, prefix="/coaching", tags=["coaching"])
app.include_router(ato_rates.router, prefix="/ato-rates", tags=["ato-rates"])
app.include_router(automations.router, prefix="/automations", tags=["automations"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(tenders.router, prefix="/tenders", tags=["tenders"])


@app.get("/", response_class=HTMLResponse)
@app.get("/start", response_class=HTMLResponse)
def start_page() -> str:
    return """
    <html>
      <head><title>Adapsys Australia Pacific Start</title></head>
      <body style=\"font-family: Segoe UI, Arial, sans-serif; margin: 2rem;\">
        <h1>Adapsys Australia Pacific - Start Page</h1>
        <p>Use these links to open the app:</p>
        <ul>
          <li><a href=\"/docs\">Backend API Docs (CEO sign-off test lives here)</a></li>
          <li><a href=\"{APP_URL}\" target=\"_blank\">Frontend App</a></li>
          <li><a href=\"/health\">Backend Health Check</a></li>
        </ul>
        <p><strong>Phone quick launch (same Wi-Fi):</strong></p>
        <label for="consultant-email">Consultant email:</label>
        <input id="consultant-email" type="email" value="cameron@adapsysgroup.com" style="margin-left: 8px; min-width: 280px;" />
        <div style="margin-top: 10px;">
          <a id="phone-launch" href="#" target="_blank" style="font-weight: 600;">Open Consultant Session</a>
        </div>
        <div style="margin-top: 6px;">
          <code id="phone-url">http://&lt;YOUR-PC-IP&gt;:5173/?role=consultant&amp;email=&lt;consultant_email&gt;&amp;lock_session=1</code>
        </div>
        <div style="margin-top: 12px;">
          <img id="phone-qr" alt="Consultant session QR" width="220" height="220" style="border: 1px solid #d5d5d5; border-radius: 8px; padding: 6px; background: #fff;" />
        </div>
        <script>
          const appUrl = '{APP_URL}';
          const host = window.location.hostname;
          const appOrigin = (() => {
            try {
              return new URL(appUrl).origin;
            } catch {
              return appUrl;
            }
          })();
          const node = document.getElementById('phone-url');
          const launch = document.getElementById('phone-launch');
          const emailInput = document.getElementById('consultant-email');
          const qr = document.getElementById('phone-qr');

          const buildUrl = () => {
            const email = (emailInput?.value || '').trim() || 'consultant@adapsysgroup.com';
            const localOrigin = `http://${host}:5173`;
            const origin = host === 'localhost' || host === '127.0.0.1' ? localOrigin : appOrigin;
            return `${origin}/?role=consultant&email=${encodeURIComponent(email)}&lock_session=1`;
          };

          const renderUrl = () => {
            const phoneUrl = buildUrl();
            if (node && host && host !== 'localhost' && host !== '127.0.0.1') {
              node.textContent = phoneUrl;
            }
            if (launch) {
              launch.href = phoneUrl;
            }
            if (qr) {
              qr.src = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(phoneUrl)}`;
            }
          };

          renderUrl();
          emailInput?.addEventListener('input', renderUrl);

          if (host === 'localhost' || host === '127.0.0.1') {
            node.textContent = 'Use http://<YOUR-PC-IP>:8000/start on your phone, then tap Open Consultant Session.';
            if (qr) {
              qr.alt = 'Open start page from phone using PC IP first';
            }
          }
        </script>
      </body>
    </html>
    """
