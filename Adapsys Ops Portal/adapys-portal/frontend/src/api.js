const browserHost = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
const defaultApiHost =
  browserHost === 'localhost' || browserHost === '127.0.0.1' ? '127.0.0.1' : browserHost;
const apiBaseOverride =
  typeof window !== 'undefined' ? localStorage.getItem('adapsys_api_base') : null;
const API_BASE = apiBaseOverride || `http://${defaultApiHost}:8000`;
const API_BASE_CANDIDATES = Array.from(
  new Set([API_BASE, `http://${browserHost}:8000`, 'http://127.0.0.1:8000', 'http://localhost:8000'])
);
let resolvedApiBase = API_BASE_CANDIDATES[0];

async function apiFetch(path, options = {}) {
  let lastError = null;
  const orderedBases = [resolvedApiBase, ...API_BASE_CANDIDATES.filter((base) => base !== resolvedApiBase)];

  for (const base of orderedBases) {
    try {
      const response = await fetch(`${base}${path}`, options);
      resolvedApiBase = base;
      return response;
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError || new Error('Failed to fetch');
}

function getActorHeaders(json = false) {
  const role = localStorage.getItem('adapsys_user_role') || 'admin';
  const email = localStorage.getItem('adapsys_user_email') || 'fi@adapsysgroup.com';
  return {
    ...(json ? { 'Content-Type': 'application/json' } : {}),
    'X-User-Role': role,
    'X-User-Email': email,
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
  if (!res.ok) throw new Error('Failed to delete expense');
  return res.json();
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

export async function runReminderAutomation(payload = { dry_run: true }) {
  const res = await apiFetch('/automations/reminders/run', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to run reminder automation');
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

export async function bulkCreateCoachingEngagements(payload) {
  const res = await apiFetch('/coaching/engagements/bulk', {
    method: 'POST',
    headers: getActorHeaders(true),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to bulk upload coaching engagements');
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
