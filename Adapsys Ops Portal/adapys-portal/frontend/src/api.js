const browserHost = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
const isLocalBrowserHost = browserHost === 'localhost' || browserHost === '127.0.0.1';
const envApiBase = typeof import.meta !== 'undefined' ? String(import.meta.env?.VITE_API_BASE || '').trim() : '';
const sameOriginApiBase = typeof window !== 'undefined' ? window.location.origin : '';
const apiBaseOverrideRaw =
  typeof window !== 'undefined' ? String(localStorage.getItem('adapsys_api_base') || '').trim() : '';
const isLikelyFrontendOriginOverride =
  Boolean(apiBaseOverrideRaw) &&
  Boolean(sameOriginApiBase) &&
  apiBaseOverrideRaw.replace(/\/$/, '') === sameOriginApiBase.replace(/\/$/, '') &&
  isLocalBrowserHost;
const apiBaseOverride = isLikelyFrontendOriginOverride ? '' : apiBaseOverrideRaw;
const API_BASE =
  apiBaseOverride || envApiBase || (isLocalBrowserHost ? 'http://127.0.0.1:8000' : sameOriginApiBase);
const API_BASE_CANDIDATES = Array.from(
  new Set([
    API_BASE,
    envApiBase,
    sameOriginApiBase,
    `${window.location.protocol}//${browserHost}:8000`,
    'http://127.0.0.1:8000',
    'http://localhost:8000',
  ].filter(Boolean))
);
let resolvedApiBase = API_BASE_CANDIDATES[0];
const DEFAULT_ADMIN_EMAIL = 'admin@adapsysgroup.com';

function normalizeEmailIdentity(email) {
  return String(email || '')
    .trim()
    .toLowerCase()
    .replace('@adapsygroup.com', '@adapsysgroup.com');
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
      const response = await fetch(`${base}${path}`, options);
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

  const fallbackMessage = [
    'API connection failed.',
    `Tried: ${attemptedUrls.join(', ')}`,
    'Ensure backend is running on http://127.0.0.1:8000 (or set localStorage.adapsys_api_base).',
  ].join(' ');

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
  if (!res.ok) throw new Error('Failed to load expense report preview');
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
  if (!res.ok) throw new Error('Failed to generate expense report PDF');
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
  if (!res.ok) throw new Error('Failed to log coaching session');
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
  if (!res.ok) throw new Error('Failed to load coaching report preview');
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
  if (!res.ok) throw new Error('Failed to generate coaching report PDF');
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
