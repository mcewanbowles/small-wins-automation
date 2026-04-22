const browserHost = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
const isLocalBrowserHost = browserHost === 'localhost' || browserHost === '127.0.0.1';
const isAdapsysPagesHost =
  typeof window !== 'undefined' &&
  ['adapsys-auspac.pages.dev', 'main.adapsys-auspac.pages.dev', 'adapsysauspac.com', 'www.adapsysauspac.com'].some((h) =>
    String(window.location.hostname || '').endsWith(h)
  );
const PROD_DEFAULT_API_BASE = 'https://adapsys-portal-production.up.railway.app';
const envApiBase =
  typeof import.meta !== 'undefined'
    ? String(import.meta.env?.VITE_API_BASE || import.meta.env?.VITE_API_URL || '').trim()
    : '';
const sameOriginApiBase = typeof window !== 'undefined' ? window.location.origin : '';
const envApiKey = typeof import.meta !== 'undefined' ? String(import.meta.env?.VITE_API_KEY || '').trim() : '';
const apiBaseOverrideRaw =
  typeof window !== 'undefined' ? String(localStorage.getItem('adapsys_api_base') || '').trim() : '';
const apiKeyOverrideRaw = typeof window !== 'undefined' ? String(localStorage.getItem('adapsys_api_key') || '').trim() : '';
const isHttpsPage = typeof window !== 'undefined' && String(window.location.protocol || '') === 'https:';
const apiBaseOverrideSanitized = (() => {
  if (!apiBaseOverrideRaw) return '';
  try {
    const base = sameOriginApiBase || 'https://adapsys-portal-production.up.railway.app';
    const url = new URL(apiBaseOverrideRaw, base);
    if (isHttpsPage && url.protocol === 'http:') {
      url.protocol = 'https:';
    }
    return url.origin.replace(/\/$/, '');
  } catch {
    return apiBaseOverrideRaw.replace(/^http:/, 'https:').replace(/\/$/, '');
  }
})();
const isLikelyFrontendOriginOverride =
  Boolean(apiBaseOverrideRaw) &&
  Boolean(sameOriginApiBase) &&
  apiBaseOverrideRaw.replace(/\/$/, '') === sameOriginApiBase.replace(/\/$/, '') &&
  isLocalBrowserHost;
const apiBaseOverride = isLikelyFrontendOriginOverride ? '' : apiBaseOverrideSanitized;
const API_BASE =
  apiBaseOverride ||
  envApiBase ||
  (isLocalBrowserHost ? 'http://127.0.0.1:8000' : (isAdapsysPagesHost ? PROD_DEFAULT_API_BASE : sameOriginApiBase));
const PROD_DEFAULT_API_KEY = '';
const API_KEY = apiKeyOverrideRaw || envApiKey || PROD_DEFAULT_API_KEY;
// Build API base candidates.
// - On Cloudflare Pages or any non-local host, DO NOT attempt localhost/port fallbacks to avoid
//   Mixed Content and cross-origin port errors. Prefer explicit overrides and the prod default.
// - When the page is HTTPS, auto-upgrade any non-local http candidates to https.
const DEV_CANDIDATES = isLocalBrowserHost
  ? [
      `${window.location.protocol}//${browserHost}:8010`,
      `${window.location.protocol}//${browserHost}:8000`,
      'http://127.0.0.1:8010',
      'http://127.0.0.1:8000',
      'http://localhost:8010',
      'http://localhost:8000',
    ]
  : [];

const RAW_CANDIDATES = [
  API_BASE,
  envApiBase,
  'https://api.adapsysauspac.com',
  PROD_DEFAULT_API_BASE,
  ...DEV_CANDIDATES,
].filter(Boolean);

const API_BASE_CANDIDATES = Array.from(new Set(RAW_CANDIDATES)).map((base) => {
  try {
    const u = new URL(base, sameOriginApiBase || PROD_DEFAULT_API_BASE);
    // If this page is HTTPS and the target is not a localhost-style host, force HTTPS.
    if (isHttpsPage && u.protocol === 'http:' && !/^(localhost|127\.0\.0\.1)$/i.test(u.hostname)) {
      u.protocol = 'https:';
      u.port = '';
    }
    return u.origin.replace(/\/$/, '');
  } catch {
    return base.replace(/^http:/, 'https:').replace(/\/$/, '');
  }
});
let resolvedApiBase = API_BASE_CANDIDATES[0];
const DEFAULT_ADMIN_EMAIL = 'admin@adapsysgroup.com';

function normalizeEmailIdentity(email) {
  return String(email || '')
    .trim()
    .toLowerCase()
    .replace('@adapsygroup.com', '@adapsysgroup.com');
}

export async function validatePerDiemForTrip(tripId, { start_date, end_date } = {}) {
  const query = new URLSearchParams({
    trip_id: String(tripId || ''),
    ...(start_date ? { start_date } : {}),
    ...(end_date ? { end_date } : {}),
  });
  const suffix = `?${query.toString()}`;
  const res = await apiFetch(`/expenses/per-diem/validate${suffix}`, {
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    try {
      const body = await res.json();
      const detail = String(body?.detail || '').trim();
      throw new Error(detail || `Per-diem validation failed (HTTP ${res.status})`);
    } catch {
      throw new Error(`Per-diem validation failed (HTTP ${res.status})`);
    }
  }
  return res.json();
}

export async function bulkLogCoachingSessions(payload) {
  const res = await apiFetch('/coaching/sessions/bulk', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to bulk upload coaching sessions');
  }
  return res.json();
}

export async function xeroImportExpenses(payload = {}) {
  const res = await apiFetch('/expenses/xero-import', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload || {}),
  });
  if (!res.ok) {
    try {
      const body = await res.json();
      const detail = String(body?.detail || '').trim();
      throw new Error(detail || `Xero import failed (HTTP ${res.status})`);
    } catch {
      throw new Error(`Xero import failed (HTTP ${res.status})`);
    }
  }
  return res.json();
}

async function apiFetch(path, options = {}) {
  let lastError = null;
  const orderedBases = [resolvedApiBase, ...API_BASE_CANDIDATES.filter((base) => base !== resolvedApiBase)];
  const attemptedUrls = [];

  const mayReturnHtmlIntentionally =
    path.includes('/reports/') && (path.includes('/expense-pack') || path.includes('/coaching/summary'));

  for (const base of orderedBases) {
    attemptedUrls.push(`${base}${path}`);
    try {
      const mergedOptions = { ...options };
      const existingHeaders = options && options.headers ? options.headers : {};
      const token = typeof window !== 'undefined' ? String(localStorage.getItem('adapsys_jwt') || '').trim() : '';
      const mergedHeaders = {
        ...(typeof existingHeaders === 'object' && !(existingHeaders instanceof Headers) ? existingHeaders : {}),
        ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      };
      mergedOptions.headers = mergedHeaders;
      const response = await fetch(`${base}${path}`, mergedOptions);
      const contentType = String(response.headers.get('content-type') || '').toLowerCase();

      if (!mayReturnHtmlIntentionally && response.ok && contentType.includes('text/html')) {
        // This is usually the frontend app shell (wrong base), so continue to next API base candidate.
        continue;
      }

      resolvedApiBase = base;
      return response;
    } catch (error) {
      lastError = error;
    }
  }

  const fallbackLines = isLocalBrowserHost
    ? [
        'API connection failed.',
        `Tried: ${attemptedUrls.join(', ')}`,
        'Ensure backend is running on http://127.0.0.1:8000 or http://127.0.0.1:8010 (or set localStorage.adapsys_api_base).',
      ]
    : [
        'API connection failed.',
        `Tried: ${attemptedUrls.join(', ')}`,
        'If this persists, ensure the Railway backend is running and CORS allows this domain.',
      ];
  const fallbackMessage = fallbackLines.join(' ');

  if (lastError instanceof Error) {
    const lowLevel = String(lastError.message || '').trim();
    throw new Error(lowLevel ? `${fallbackMessage} Browser error: ${lowLevel}` : fallbackMessage);
  }

  throw new Error(fallbackMessage);
}

function getActorHeaders(json = false) {
  const role = localStorage.getItem('adapsys_user_role') || 'admin';
  const email = normalizeEmailIdentity(localStorage.getItem('adapsys_user_email') || DEFAULT_ADMIN_EMAIL);
  const clientOrg = String(localStorage.getItem('adapsys_client_org') || '').trim();
  return {
    ...(json ? { 'Content-Type': 'application/json' } : {}),
    'X-User-Role': role,
    'X-User-Email': email,
    ...(clientOrg ? { 'X-Client-Org': clientOrg } : {}),
  };
}

export async function createTrip(payload) {
  const res = await apiFetch('/trips', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create trip');
  return res.json();
}

export async function updateTrip(tripId, payload) {
  const res = await apiFetch(`/trips/${tripId}`, {
    method: 'PUT',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update project');
  return res.json();
}

export async function deleteTrip(tripId) {
  const res = await apiFetch(`/trips/${tripId}`, {
    method: 'DELETE',
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to delete activity');
  }
  return null;
}

export async function listTrips() {
  const res = await apiFetch('/trips');
  if (!res.ok) throw new Error('Failed to load trips');
  return res.json();
}

export async function createExpense(payload) {
  const res = await apiFetch('/expenses', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create expense');
  return res.json();
}

export async function intakeEmailReceipt(payload) {
  const res = await apiFetch('/expenses/intake-email', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to intake emailed receipt');
  return res.json();
}

export async function listExpenses() {
  const res = await apiFetch('/expenses', {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load expenses');
  return res.json();
}

export async function listAtoRates() {
  const res = await apiFetch('/ato-rates');
  if (!res.ok) throw new Error('Failed to load ATO rates');
  return res.json();
}

export async function updateAtoRate(rateId, payload) {
  const res = await apiFetch(`/ato-rates/${rateId}`, {
    method: 'PUT',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update ATO rate');
  return res.json();
}

export async function approveExpense(expenseId) {
  const res = await apiFetch(`/expenses/${expenseId}/approve`, {
    method: 'POST',
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to approve expense');
  return res.json();
}

export async function markExpenseInvoiced(expenseId) {
  const res = await apiFetch(`/expenses/${expenseId}/mark-invoiced`, {
    method: 'POST',
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to mark expense as invoiced');
  return res.json();
}

export async function deleteExpense(expenseId) {
  const res = await apiFetch(`/expenses/${expenseId}`, {
    method: 'DELETE',
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to delete expense');
  }

  if (res.status === 204) return null;
  const contentType = String(res.headers.get('content-type') || '').toLowerCase();
  if (!contentType.includes('application/json')) return null;
  try {
    return await res.json();
  } catch {
    return null;
  }
}

export async function updateExpenseReceipt(expenseId, payload) {
  const res = await apiFetch(`/expenses/${expenseId}/receipt`, {
    method: 'PUT',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to attach receipt');
  return res.json();
}

export async function updateExpenseTrip(expenseId, payload) {
  const res = await apiFetch(`/expenses/${expenseId}/trip`, {
    method: 'PUT',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to move expense to project');
  return res.json();
}

export async function listExpenseXeroSyncStatus() {
  const res = await apiFetch('/expenses/xero-sync-status', {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load Xero sync status');
  return res.json();
}

export async function getExpenseXeroSyncConfig() {
  const res = await apiFetch('/expenses/xero-sync-config', {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load Xero sync configuration');
  return res.json();
}

export async function pushExpenseToXero(expenseId) {
  const res = await apiFetch(`/expenses/${expenseId}/xero-sync`, {
    method: 'POST',
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to sync expense to Xero');
  }
  return res.json();
}

export async function claimCoachingSessions(payload) {
  const res = await apiFetch('/coaching/sessions/claim', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to claim coaching sessions');
  return res.json();
}

export async function runReminderAutomation(payload = { dry_run: true }) {
  const res = await apiFetch('/automations/reminders/run', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to run reminder automation');
  return res.json();
}

export async function listReminderLastSent() {
  const res = await apiFetch('/automations/reminders/last-sent', {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load reminder last-sent summary');
  return res.json();
}

export async function runCeoSignoffAutomation(payload = { dry_run: true }) {
  const res = await apiFetch('/automations/ceo-signoff/run', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to run CEO sign-off automation');
  return res.json();
}

export async function fetchExpensePackPreview(tripId, { start_date, end_date } = {}) {
  const query = new URLSearchParams({
    ...(start_date ? { start_date } : {}),
    ...(end_date ? { end_date } : {}),
  });
  const suffix = query.toString() ? `?${query.toString()}` : '';
  const res = await apiFetch(`/reports/${tripId}/expense-pack${suffix}`, {
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    try {
      const body = await res.json();
      const detail = String(body?.detail || '').trim();
      throw new Error(detail || `Failed to load expense report preview (HTTP ${res.status})`);
    } catch {
      throw new Error(`Failed to load expense report preview (HTTP ${res.status})`);
    }
  }
  return res.text();
}

export async function downloadExpensePackPdf(tripId, { start_date, end_date } = {}) {
  const query = new URLSearchParams({
    ...(start_date ? { start_date } : {}),
    ...(end_date ? { end_date } : {}),
  });
  const suffix = query.toString() ? `?${query.toString()}` : '';
  const res = await apiFetch(`/reports/${tripId}/final-expense-pack.pdf${suffix}`, {
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    try {
      const body = await res.json();
      const detail = String(body?.detail || '').trim();
      throw new Error(detail || `Failed to generate expense report PDF (HTTP ${res.status})`);
    } catch {
      throw new Error(`Failed to generate expense report PDF (HTTP ${res.status})`);
    }
  }
  return res.blob();
}

export async function downloadCoachingRowsCsv({ report_by, client_org, coach_email, coachee_name, start_date, end_date }) {
  const query = new URLSearchParams({
    report_by,
    ...(client_org ? { client_org } : {}),
    ...(coach_email ? { coach_email } : {}),
    ...(coachee_name ? { coachee_name } : {}),
    ...(start_date ? { start_date } : {}),
    ...(end_date ? { end_date } : {}),
  });
  try {
    const res = await apiFetch(`/reports/coaching/rows.csv?${query.toString()}`, {
      headers: getActorHeaders(),
    });
    if (res.ok) {
      return res.blob();
    }
    return await buildCoachingRowsCsvClientSide({ report_by, client_org, coach_email, coachee_name, start_date, end_date });
  } catch (err) {
    try {
      return await buildCoachingRowsCsvClientSide({ report_by, client_org, coach_email, coachee_name, start_date, end_date });
    } catch (fallbackErr) {
      const primary = err instanceof Error ? err.message : String(err || 'Failed to download coaching CSV');
      const secondary = fallbackErr instanceof Error ? fallbackErr.message : String(fallbackErr || '');
      throw new Error([primary, secondary ? `(Client-side fallback failed: ${secondary})` : ''].filter(Boolean).join(' '));
    }
  }
}

function normalizeScopeText(value) {
  const raw = String(value || '').trim().toLowerCase().replace(/[\-\u2012-\u2015]+/g, ' ');
  return raw.split(/\s+/).filter(Boolean).join(' ');
}

function clientMatchesScope(clientValue, scopeValue) {
  const normalized_client = normalizeScopeText(clientValue);
  const normalized_scope = normalizeScopeText(scopeValue);
  if (!normalized_client || !normalized_scope) return false;
  if (normalized_client === normalized_scope) return true;
  if (normalized_client.startsWith(`${normalized_scope} /`) || normalized_scope.startsWith(`${normalized_client} /`)) return true;
  const ct = new Set(normalized_client.split(' '));
  const st = new Set(normalized_scope.split(' '));
  const isSubset = (a, b) => { for (const x of a) { if (!b.has(x)) return false; } return true; };
  if (isSubset(st, ct) || isSubset(ct, st)) return true;
  const nc = normalized_client.replace(/\s+/g, '');
  const ns = normalized_scope.replace(/\s+/g, '');
  if (ns.includes(nc) || nc.includes(ns)) return true;
  return false;
}

async function buildCoachingRowsCsvClientSide({ report_by, client_org, coach_email, coachee_name, start_date, end_date }) {
  const by = String(report_by || 'client').trim().toLowerCase();
  let reportValue = '';
  let requiredField = '';
  if (by === 'coach') { reportValue = String(coach_email || '').trim(); requiredField = 'coach_email'; }
  else if (by === 'coachee') { reportValue = String(coachee_name || '').trim(); requiredField = 'coachee_name'; }
  else { reportValue = String(client_org || '').trim(); requiredField = 'client_org'; }
  if (!reportValue) throw new Error(`${requiredField} is required`);

  const [engRes, sessRes, coachRes, consRes] = await Promise.all([
    apiFetch('/coaching/engagements', { headers: getActorHeaders() }),
    apiFetch('/coaching/sessions', { headers: getActorHeaders() }),
    apiFetch('/lookups/coaches'),
    apiFetch('/lookups/consultants'),
  ]);
  if (!engRes.ok || !sessRes.ok) {
    throw new Error(`Failed to load source data for CSV (${!engRes.ok ? `engagements ${engRes.status}` : ''} ${!sessRes.ok ? `sessions ${sessRes.status}` : ''})`);
  }
  const engagements = await engRes.json();
  const sessions = await sessRes.json();
  let coaches = [];
  let consultants = [];
  try { if (coachRes.ok) coaches = await coachRes.json(); } catch {}
  try { if (consRes.ok) consultants = await consRes.json(); } catch {}

  const coachNameByEmail = {};
  [...coaches, ...consultants].forEach((row) => {
    const email = String(row?.email || '').trim().toLowerCase();
    const name = String(row?.name || '').trim();
    if (email && name) coachNameByEmail[email] = name;
  });
  const reportValueNorm = normalizeScopeText(reportValue);

  let engagementsFiltered = [];
  if (by === 'coach') engagementsFiltered = engagements.filter((row) => normalizeScopeText(row.coach_email) === reportValueNorm);
  else if (by === 'coachee') engagementsFiltered = engagements.filter((row) => normalizeScopeText(row.name) === reportValueNorm);
  else engagementsFiltered = engagements.filter((row) => clientMatchesScope(row.client_org, reportValueNorm));

  const engagementById = Object.fromEntries(engagementsFiltered.map((e) => [String(e.id), e]));

  const start = start_date ? new Date(start_date) : null;
  const end = end_date ? new Date(end_date) : null;
  const formatDateAu = (d) => {
    try {
      const obj = d instanceof Date ? d : (d ? new Date(d) : null);
      if (!obj || Number.isNaN(obj.getTime())) return '';
      const dd = String(obj.getDate()).padStart(2, '0');
      const mm = String(obj.getMonth() + 1).padStart(2, '0');
      const yyyy = obj.getFullYear();
      return `${dd}/${mm}/${yyyy}`;
    } catch {
      return '';
    }
  };

  const filteredSessions = sessions.filter((s) => {
    if (!engagementById[String(s.engagement_id)]) return false;
    const d = s.session_date ? new Date(s.session_date) : null;
    if (start && d && d < start) return false;
    if (end && d && d > end) return false;
    const norm = String(s.session_type || '').trim().toLowerCase();
    if (norm === 'lcp_debrief' || norm === 'lcp' || norm === 'debrief') return false;
    return true;
  });

  const byEng = {};
  filteredSessions.forEach((s) => {
    const k = String(s.engagement_id);
    (byEng[k] ||= []).push(s);
  });
  Object.values(byEng).forEach((list) => list.sort((a, b) => {
    const da = String(a.session_date || '');
    const db = String(b.session_date || '');
    if (da < db) return -1; if (da > db) return 1;
    const ia = String(a.id || ''); const ib = String(b.id || '');
    return ia < ib ? -1 : ia > ib ? 1 : 0;
  }));
  const sessionIndex = {};
  Object.keys(byEng).forEach((engId) => {
    const list = byEng[engId] || [];
    list.forEach((s, idx) => { sessionIndex[String(s.id)] = idx + 1; });
  });

  const minsToHours = (val) => { const m = Number.isFinite(Number(val)) ? Number(val) : 60; return Math.max(0, m / 60); };
  const coachLabel = (email) => {
    const norm = String(email || '').trim().toLowerCase();
    return coachNameByEmail[norm] || norm || '';
  };
  const fmtHours = (x) => {
    const s = Number(x);
    if (!Number.isFinite(s)) return '0';
    return s.toFixed(2).replace(/\.0+$/, '').replace(/\.$/, '') || '0';
  };

  const header = [
    'Client', 'Coachee', 'Coach', 'Session Date', 'Entitled Sessions', 'Session #', 'Status', 'No Show', 'Postponed', 'Invoice Hours',
  ];
  const lines = [header.join(',')];
  const engagementsSorted = engagementsFiltered.slice().sort((a, b) => {
    const ac = String(a.client_org || '').toLowerCase();
    const bc = String(b.client_org || '').toLowerCase();
    if (ac < bc) return -1; if (ac > bc) return 1;
    const an = String(a.name || '').toLowerCase();
    const bn = String(b.name || '').toLowerCase();
    return an < bn ? -1 : an > bn ? 1 : 0;
  });
  engagementsSorted.forEach((eng) => {
    const list = byEng[String(eng.id)] || [];
    list.forEach((s) => {
      const norm = String(s.session_type || '').trim().toLowerCase();
      const status = norm === 'completed' ? 'Completed' : (norm.startsWith('no_show') ? 'No Show' : (norm.startsWith('postponed') ? 'Postponed' : String(s.session_type || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())));
      const noShowFlag = norm.startsWith('no_show') ? 1 : 0;
      const postponedFlag = norm.startsWith('postponed') ? 1 : 0;
      const baseHours = minsToHours(s.duration_mins);
      const noShowRate = eng.no_show_charge_rate == null ? 0.5 : Number(eng.no_show_charge_rate);
      const invoiceHours = norm === 'completed' ? baseHours : (['no_show_chargeable', 'postponed_late'].includes(norm) ? baseHours * noShowRate : 0.0);
      const row = [
        String(eng.client_org || 'Unspecified').replace(/,/g, ' '),
        String(eng.name || 'Unknown').replace(/,/g, ' '),
        String(coachLabel(eng.coach_email)).replace(/,/g, ' '),
        formatDateAu(s.session_date || ''),
        String(parseInt(eng.total_sessions || 0, 10) || 0),
        String(parseInt(sessionIndex[String(s.id)] || 0, 10) || 0),
        status,
        String(noShowFlag),
        String(postponedFlag),
        fmtHours(invoiceHours),
      ];
      lines.push(row.join(','));
    });
  });

  return new Blob([lines.join('\n')], { type: 'text/csv; charset=utf-8' });
}

export async function downloadCoachingDetailedCsv({ report_by, client_org, coach_email, coachee_name, start_date, end_date, columns }) {
  return buildCoachingDetailedCsvClientSide({ report_by, client_org, coach_email, coachee_name, start_date, end_date, columns });
}

async function buildCoachingDetailedCsvClientSide({ report_by, client_org, coach_email, coachee_name, start_date, end_date, columns }) {
  const by = String(report_by || 'client').trim().toLowerCase();
  let reportValue = '';
  if (by === 'coach') reportValue = String(coach_email || '').trim();
  else if (by === 'coachee') reportValue = String(coachee_name || '').trim();
  else if (by === 'all') reportValue = '';
  else reportValue = String(client_org || '').trim();
  if (by !== 'all' && !reportValue) throw new Error(`${by === 'coach' ? 'coach_email' : by === 'coachee' ? 'coachee_name' : 'client_org'} is required`);

  const [engRes, sessRes, coachRes, consRes, cfgRes] = await Promise.all([
    apiFetch('/coaching/engagements', { headers: getActorHeaders() }),
    apiFetch('/coaching/sessions', { headers: getActorHeaders() }),
    apiFetch('/lookups/coaches'),
    apiFetch('/lookups/consultants'),
    apiFetch('/lookups/admin-config', { headers: getActorHeaders() }),
  ]);
  if (!engRes.ok || !sessRes.ok) throw new Error('Failed to load source data for detailed CSV');
  const engagements = await engRes.json();
  const sessions = await sessRes.json();
  let coaches = []; let consultants = [];
  try { if (coachRes.ok) coaches = await coachRes.json(); } catch {}
  try { if (consRes.ok) consultants = await consRes.json(); } catch {}
  let adminConfig = {};
  try { if (cfgRes.ok) adminConfig = await cfgRes.json(); } catch {}

  const coachNameByEmail = {};
  [...coaches, ...consultants].forEach((row) => {
    const email = String(row?.email || '').trim().toLowerCase();
    const name = String(row?.name || '').trim();
    if (email && name) coachNameByEmail[email] = name;
  });

  const reportValueNorm = normalizeScopeText(reportValue);
  let engagementsFiltered = [];
  if (by === 'coach') engagementsFiltered = engagements.filter((row) => normalizeScopeText(row.coach_email) === reportValueNorm);
  else if (by === 'coachee') engagementsFiltered = engagements.filter((row) => normalizeScopeText(row.name) === reportValueNorm);
  else if (by === 'all') engagementsFiltered = engagements.slice();
  else engagementsFiltered = engagements.filter((row) => clientMatchesScope(row.client_org, reportValueNorm));

  const engagementById = Object.fromEntries(engagementsFiltered.map((e) => [String(e.id), e]));
  const allSessionsByEng = {};
  (sessions || []).forEach((s) => {
    const k = String(s.engagement_id || '');
    if (!k) return;
    (allSessionsByEng[k] ||= []).push(s);
  });

  const start = start_date ? new Date(start_date) : null;
  const end = end_date ? new Date(end_date) : null;
  const filteredSessions = sessions.filter((s) => {
    if (!engagementById[String(s.engagement_id)]) return false;
    const d = s.session_date ? new Date(s.session_date) : null;
    if (start && d && d < start) return false;
    if (end && d && d > end) return false;
    const norm = String(s.session_type || '').trim().toLowerCase();
    if (norm === 'lcp_debrief' || norm === 'lcp' || norm === 'debrief') return false;
    return true;
  });

  const byEng = {};
  filteredSessions.forEach((s) => { (byEng[String(s.engagement_id)] ||= []).push(s); });
  Object.values(byEng).forEach((list) => list.sort((a, b) => {
    const da = String(a.session_date || '');
    const db = String(b.session_date || '');
    if (da < db) return -1; if (da > db) return 1;
    const ia = String(a.id || ''); const ib = String(b.id || '');
    return ia < ib ? -1 : ia > ib ? 1 : 0;
  }));
  const sessionIndex = {};
  Object.keys(byEng).forEach((engId) => {
    const list = byEng[engId] || [];
    list.forEach((s, idx) => { sessionIndex[String(s.id)] = idx + 1; });
  });

  const duplicateKey = (s) => `${String(s.engagement_id)}|${String(s.session_date || '')}|${String(s.session_type || '').trim().toLowerCase()}`;
  const dupCounts = {};
  (sessions || []).forEach((s) => { const k = duplicateKey(s); dupCounts[k] = (dupCounts[k] || 0) + 1; });

  const minsToHours = (val) => { const m = Number.isFinite(Number(val)) ? Number(val) : 60; return Math.max(0, m / 60); };
  const coachLabel = (email) => { const norm = String(email || '').trim().toLowerCase(); return coachNameByEmail[norm] || norm || ''; };
  const fmtHours = (x) => { const s = Number(x); if (!Number.isFinite(s)) return '0'; return s.toFixed(2).replace(/\.0+$/, '').replace(/\.$/, '') || '0'; };
  const formatDateAu = (d) => { try { const obj = d instanceof Date ? d : (d ? new Date(d) : null); if (!obj || Number.isNaN(obj.getTime())) return ''; const dd = String(obj.getDate()).padStart(2, '0'); const mm = String(obj.getMonth() + 1).padStart(2, '0'); const yyyy = obj.getFullYear(); return `${dd}/${mm}/${yyyy}`; } catch { return ''; } };
  const formatDateYmd = (d) => { try { const obj = d instanceof Date ? d : (d ? new Date(d) : null); if (!obj || Number.isNaN(obj.getTime())) return ''; const dd = String(obj.getDate()).padStart(2, '0'); const mm = String(obj.getMonth() + 1).padStart(2, '0'); const yyyy = obj.getFullYear(); return `${yyyy}${mm}${dd}`; } catch { return ''; } };
  const coacheeKey = (name) => String(name || '').trim().toLowerCase().replace(/\s+/g, ' ').replace(/[^a-z0-9\s]/g, '');

  // Duplicate detection for coachee names within the current scope
  const coacheeDupCounts = {};
  (engagementsFiltered || []).forEach((eng) => {
    const k = coacheeKey(eng.name);
    if (k) coacheeDupCounts[k] = (coacheeDupCounts[k] || 0) + 1;
  });

  const clientNameMap = (adminConfig && adminConfig.client_name_map) || {};
  const fullClientName = (shortName) => {
    const key = String(shortName || '').trim();
    return clientNameMap[key] || key;
  };

  const allHeaders = [
    'Engagement ID', 'Session ID', 'Client', 'Client Full Name', 'Coachee', 'Coach', 'Coach Email', 'Session Date', 'Status', 'Entitled Sessions', 'Total Sessions Logged', 'Session #', 'Over Entitlement', 'No Show', 'Postponed', 'Invoice Hours', 'Invoiced To Adapsys', 'Invoice Number', 'Cost Amount', 'Notes', 'Coachee Name Key', 'Coachee Duplicate Count', 'Cross-Ref Key', 'Duplicate Key', 'Duplicate Count',
  ];
  const headers = Array.isArray(columns) && columns.length
    ? columns.filter((h) => allHeaders.includes(h))
    : allHeaders;
  const lines = [headers.join(',')];

  const engagementsSorted = engagementsFiltered.slice().sort((a, b) => {
    const ac = String(a.client_org || '').toLowerCase();
    const bc = String(b.client_org || '').toLowerCase();
    if (ac < bc) return -1; if (ac > bc) return 1;
    const an = String(a.name || '').toLowerCase();
    const bn = String(b.name || '').toLowerCase();
    return an < bn ? -1 : an > bn ? 1 : 0;
  });
  engagementsSorted.forEach((eng) => {
    const list = byEng[String(eng.id)] || [];
    const totalLogged = (allSessionsByEng[String(eng.id)] || []).length;
    const over = Number.isFinite(Number(eng.total_sessions)) && totalLogged > Number(eng.total_sessions);
    list.forEach((s) => {
      const norm = String(s.session_type || '').trim().toLowerCase();
      const status = norm === 'completed' ? 'Completed' : (norm.startsWith('no_show') ? 'No Show' : (norm.startsWith('postponed') ? 'Postponed' : String(s.session_type || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())));
      const noShowFlag = norm.startsWith('no_show') ? 1 : 0;
      const postponedFlag = norm.startsWith('postponed') ? 1 : 0;
      const baseHours = minsToHours(s.duration_mins);
      const noShowRate = eng.no_show_charge_rate == null ? 0.5 : Number(eng.no_show_charge_rate);
      const invoiceHours = norm === 'completed' ? baseHours : (['no_show_chargeable', 'postponed_late'].includes(norm) ? baseHours * noShowRate : 0.0);
      const dupKey = duplicateKey(s);
      const values = {
        'Engagement ID': String(eng.id),
        'Session ID': String(s.id || ''),
        'Client': String(eng.client_org || 'Unspecified').replace(/,/g, ' '),
        'Client Full Name': String(fullClientName(eng.client_org || 'Unspecified')).replace(/,/g, ' '),
        'Coachee': String(eng.name || 'Unknown').replace(/,/g, ' '),
        'Coach': String(coachLabel(eng.coach_email)).replace(/,/g, ' '),
        'Coach Email': String(eng.coach_email || '').replace(/,/g, ' '),
        'Session Date': formatDateAu(s.session_date || ''),
        'Status': status,
        'Entitled Sessions': String(parseInt(eng.total_sessions || 0, 10) || 0),
        'Total Sessions Logged': String(totalLogged || 0),
        'Session #': String(parseInt(sessionIndex[String(s.id)] || 0, 10) || 0),
        'Over Entitlement': over ? 'Y' : 'N',
        'No Show': String(noShowFlag),
        'Postponed': String(postponedFlag),
        'Invoice Hours': fmtHours(invoiceHours),
        'Invoiced To Adapsys': (s.invoiced_to_adapsys ? 'Y' : 'N'),
        'Invoice Number': String(s.associate_claim_ref || '').replace(/,/g, ' '),
        'Cost Amount': String(s.associate_cost_amount ?? '').replace(/,/g, ' '),
        'Notes': String(s.notes ?? '').replace(/,/g, ' '),
        'Coachee Name Key': coacheeKey(eng.name),
        'Coachee Duplicate Count': String(coacheeDupCounts[coacheeKey(eng.name)] || 0),
        'Cross-Ref Key': `${String(eng.client_org || '').trim()}|${coacheeKey(eng.name)}|${formatDateYmd(s.session_date || '')}`,
        'Duplicate Key': dupKey,
        'Duplicate Count': String(dupCounts[dupKey] || 0),
      };
      lines.push(headers.map((h) => values[h] ?? '').join(','));
    });
  });

  return new Blob([lines.join('\n')], { type: 'text/csv; charset=utf-8' });
}

export async function downloadCoachingRowsXlsx({ report_by, client_org, coach_email, coachee_name, start_date, end_date }) {
  const query = new URLSearchParams({
    report_by,
    ...(client_org ? { client_org } : {}),
    ...(coach_email ? { coach_email } : {}),
    ...(coachee_name ? { coachee_name } : {}),
    ...(start_date ? { start_date } : {}),
    ...(end_date ? { end_date } : {}),
  });
  const res = await apiFetch(`/reports/coaching/rows.xlsx?${query.toString()}`, {
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    try {
      const body = await res.json();
      const detail = String(body?.detail || '').trim();
      throw new Error(detail || `Failed to download coaching XLSX (HTTP ${res.status})`);
    } catch {
      throw new Error(`Failed to download coaching XLSX (HTTP ${res.status})`);
    }
  }
  return res.blob();
}

export async function listConsultants() {
  const res = await apiFetch('/lookups/consultants');
  if (!res.ok) throw new Error('Failed to load consultants');
  return res.json();
}

export async function listCoaches() {
  const res = await apiFetch('/lookups/coaches');
  if (!res.ok) throw new Error('Failed to load coaches');
  return res.json();
}

export async function listClientPrograms() {
  const res = await apiFetch('/lookups/client-programs');
  if (!res.ok) throw new Error('Failed to load client programs');
  return res.json();
}

export async function listClientChargePolicies() {
  const res = await apiFetch('/lookups/client-charge-policies');
  if (!res.ok) throw new Error('Failed to load client charge policies');
  return res.json();
}

export async function getLookupAdminConfig() {
  const res = await apiFetch('/lookups/admin-config', {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load lookup admin config');
  return res.json();
}

export async function updateLookupConsultants(payload) {
  const res = await apiFetch('/lookups/consultants', {
    method: 'PUT',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update consultants list');
  return res.json();
}

export async function updateLookupCoaches(payload) {
  const res = await apiFetch('/lookups/coaches', {
    method: 'PUT',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update coaches list');
  return res.json();
}

export async function updateLookupClientPrograms(payload) {
  const res = await apiFetch('/lookups/client-programs', {
    method: 'PUT',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update client programs list');
  return res.json();
}

export async function updateClientChargePolicies(payload) {
  const res = await apiFetch('/lookups/client-charge-policies', {
    method: 'PUT',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update client charge policies');
  return res.json();
}

export async function updateLookupAdminConfig(payload) {
  const res = await apiFetch('/lookups/admin-config', {
    method: 'PUT',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update lookup admin config');
  return res.json();
}

export async function listCoachingEngagements() {
  const res = await apiFetch('/coaching/engagements', {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load coaching engagements');
  return res.json();
}

export async function createCoachingEngagement(payload) {
  const res = await apiFetch('/coaching/engagements', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create coaching engagement');
  return res.json();
}

export async function updateCoachingEngagement(engagementId, payload) {
  const res = await apiFetch(`/coaching/engagements/${engagementId}`, {
    method: 'PUT',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update coaching engagement');
  return res.json();
}

export async function deleteCoachingEngagement(engagementId) {
  const res = await apiFetch(`/coaching/engagements/${engagementId}`, {
    method: 'DELETE',
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to delete coaching engagement');
  }
  return res.json();
}

export async function listContracts() {
  const res = await apiFetch('/contracts', {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load contracts');
  return res.json();
}

export async function getContractMergeFields() {
  const res = await apiFetch('/contracts/merge-fields', {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load contract merge fields');
  return res.json();
}

export async function createContract(payload) {
  const res = await apiFetch('/contracts', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create contract');
  return res.json();
}

export async function updateContract(contractId, payload) {
  const res = await apiFetch(`/contracts/${contractId}`, {
    method: 'PUT',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update contract');
  return res.json();
}

export async function deleteContract(contractId) {
  const res = await apiFetch(`/contracts/${contractId}`, {
    method: 'DELETE',
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to delete contract');
  }
  return null;
}

export async function listProfiles() {
  const res = await apiFetch('/profiles', {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load consultant profiles');
  return res.json();
}

export async function upsertProfile(payload) {
  const res = await apiFetch('/profiles', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to save consultant profile');
  return res.json();
}

export async function updateProfile(profileId, payload) {
  const res = await apiFetch(`/profiles/${profileId}`, {
    method: 'PUT',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update consultant profile');
  return res.json();
}

export async function uploadProfilePhoto(profileId, file) {
  const form = new FormData();
  form.append('file', file);
  const res = await apiFetch(`/profiles/${profileId}/photo`, {
    method: 'POST',
    headers: getActorHeaders(false),
    body: form,
  });
  if (!res.ok) throw new Error('Failed to upload profile photo');
  return res.json();
}

export async function getTravelBookingSummary() {
  const res = await apiFetch('/trips/travel-booking-summary', {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load travel booking summary');
  return res.json();
}

export async function submitTripTravelRequest(tripId, payload) {
  const res = await apiFetch(`/trips/${tripId}/travel-request`, {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to submit travel request');
  return res.json();
}

export async function markTripTravelBooked(tripId) {
  const res = await apiFetch(`/trips/${tripId}/mark-travel-booked`, {
    method: 'POST',
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to mark travel as booked');
  return res.json();
}

export async function createBookedTravelExpenseDraft(tripId) {
  const res = await apiFetch(`/trips/${tripId}/booked-travel-expense-draft`, {
    method: 'POST',
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to generate booked-travel expense draft');
  }
  return res.json();
}

export async function bulkCreateCoachingEngagements(payload) {
  const res = await apiFetch('/coaching/engagements/bulk', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to bulk upload coaching engagements');
  }
  return res.json();
}

export async function listCoachingSessions() {
  const res = await apiFetch('/coaching/sessions', {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load coaching sessions');
  return res.json();
}

export async function logCoachingSession(payload) {
  const res = await apiFetch('/coaching/sessions', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    try {
      const ct = String(res.headers.get('content-type') || '').toLowerCase();
      if (ct.includes('application/json')) {
        const body = await res.json();
        let detail = '';
        const raw = body?.detail ?? body?.message ?? '';
        if (Array.isArray(raw)) {
          // FastAPI validation errors come as an array
          const first = raw[0] || {};
          const loc = Array.isArray(first.loc) ? first.loc.join('.') : String(first.loc || '');
          const msg = String(first.msg || '').trim();
          detail = [msg, loc ? `(${loc})` : ''].filter(Boolean).join(' ');
        } else if (raw && typeof raw === 'object') {
          // Generic object; stringify succinctly
          detail = JSON.stringify(raw);
        } else {
          detail = String(raw || '').trim();
        }
        if (detail) throw new Error(detail);
      }
      // Fallback to plain text error body if JSON was not provided
      const text = await res.text();
      const detail = String(text || '').trim();
      if (detail) throw new Error(detail);
    } catch {}
    throw new Error(`Failed to log coaching session (HTTP ${res.status})`);
  }
  return res.json();
}

export async function updateCoachingSession(sessionId, payload) {
  const res = await apiFetch(`/coaching/sessions/${sessionId}`, {
    method: 'PUT',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update coaching session');
  return res.json();
}

export async function deleteCoachingSession(sessionId) {
  const res = await apiFetch(`/coaching/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to delete coaching session');
  }
  return res.json();
}

export async function fetchCoachingReportPreview({ report_by, client_org, coach_email, coachee_name, start_date, end_date }) {
  const query = new URLSearchParams({
    report_by,
    ...(client_org ? { client_org } : {}),
    ...(coach_email ? { coach_email } : {}),
    ...(coachee_name ? { coachee_name } : {}),
    ...(start_date ? { start_date } : {}),
    ...(end_date ? { end_date } : {}),
  });
  const res = await apiFetch(`/reports/coaching/summary?${query.toString()}`, {
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    try {
      const body = await res.json();
      const detail = String(body?.detail || '').trim();
      throw new Error(detail || `Failed to load coaching report preview (HTTP ${res.status})`);
    } catch {
      throw new Error(`Failed to load coaching report preview (HTTP ${res.status})`);
    }
  }
  return res.text();
}

export async function downloadCoachingReportPdf({ report_by, client_org, coach_email, coachee_name, start_date, end_date }) {
  const query = new URLSearchParams({
    report_by,
    ...(client_org ? { client_org } : {}),
    ...(coach_email ? { coach_email } : {}),
    ...(coachee_name ? { coachee_name } : {}),
    ...(start_date ? { start_date } : {}),
    ...(end_date ? { end_date } : {}),
  });
  const res = await apiFetch(`/reports/coaching/summary.pdf?${query.toString()}`, {
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    try {
      const body = await res.json();
      const detail = String(body?.detail || '').trim();
      throw new Error(detail || `Failed to generate coaching report PDF (HTTP ${res.status})`);
    } catch {
      throw new Error(`Failed to generate coaching report PDF (HTTP ${res.status})`);
    }
  }
  return res.blob();
}

export async function fetchClientCoachingSummary({ client_org, start_date, end_date } = {}) {
  const query = new URLSearchParams({
    ...(client_org ? { client_org } : {}),
    ...(start_date ? { start_date } : {}),
    ...(end_date ? { end_date } : {}),
  });
  const res = await apiFetch(`/reports/coaching/client-summary?${query.toString()}`, {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load client coaching summary');
  return res.json();
}

export async function listTenders() {
  const res = await apiFetch('/tenders', {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load tenders');
  return res.json();
}

export async function getTenderSummary() {
  const res = await apiFetch('/tenders/summary', {
    headers: getActorHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load tender summary');
  return res.json();
}

export async function triageTender(payload) {
  const res = await apiFetch('/tenders/triage', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to triage tender');
  return res.json();
}

export async function setTenderDecision(tenderId, payload) {
  const res = await apiFetch(`/tenders/${tenderId}/decision`, {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to save tender decision');
  return res.json();
}

export async function sendContractForSignature(payload) {
  const res = await apiFetch('/contracts/send-for-signature', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to send contract for signature');
  }
  return res.json();
}

export async function fetchContractPreview(contractId) {
  const res = await apiFetch(`/contracts/${contractId}/preview`, {
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to load contract preview');
  }
  return res.text();
}

export async function downloadContractPreviewPdf(contractId) {
  const res = await apiFetch(`/contracts/${contractId}/preview.pdf`, {
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to generate contract preview PDF');
  }
  return res.blob();
}

export async function queueContractSignatureReminder(contractId, payload = {}) {
  const res = await apiFetch(`/contracts/${contractId}/signature-reminder`, {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to queue contract reminder');
  }
  return res.json();
}

export async function getContractSignatureStatus(contractId) {
  const res = await apiFetch(`/contracts/${contractId}/signature-status`, {
    headers: getActorHeaders(),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to load contract signature status');
  }
  return res.json();
}

export async function generateContractPdf(contractId) {
  const res = await apiFetch(`/contracts/${contractId}/generate-pdf`, {
    method: 'POST',
    headers: getActorHeaders(true),
  });
  if (!res.ok) {
    let detail = '';
    try {
      const body = await res.json();
      detail = String(body?.detail || '').trim();
    } catch {
      detail = '';
    }
    throw new Error(detail || 'Failed to generate contract PDF');
  }
  return res.blob();
}

export async function fetchWhoAmI() {
  const res = await apiFetch('/auth/whoami');
  if (!res.ok) throw new Error('Failed to load whoami');
  return res.json();
}

export async function loginWithPassword(email, password) {
  const res = await apiFetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    try {
      const body = await res.json();
      const detail = String(body?.detail || '').trim();
      throw new Error(detail || `Login failed (HTTP ${res.status})`);
    } catch {
      throw new Error(`Login failed (HTTP ${res.status})`);
    }
  }
  const data = await res.json();
  if (data?.access_token) {
    try { localStorage.setItem('adapsys_jwt', String(data.access_token)); } catch {}
    try { localStorage.setItem('adapsys_user_email', String(data.email || '')); } catch {}
    try { localStorage.setItem('adapsys_user_role', String(data.role || 'consultant')); } catch {}
    try {
      const org = String(data.client_org || '').trim();
      if (org) localStorage.setItem('adapsys_client_org', org);
    } catch {}
  }
  return data;
}

export function logout() {
  try { localStorage.removeItem('adapsys_jwt'); } catch {}
}
