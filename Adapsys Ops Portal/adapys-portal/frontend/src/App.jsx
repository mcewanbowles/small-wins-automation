import { useEffect, useMemo, useRef, useState } from 'react';
import {
  approveExpense,
  bulkCreateCoachingEngagements,
  claimCoachingSessions,
  createContract,
  createCoachingEngagement,
  deleteCoachingEngagement,
  deleteContract,
  deleteCoachingSession as deleteCoachingSessionApi,
  createExpense,
  createTrip,
  deleteExpense,
  deleteTrip,
  downloadCoachingReportPdf,
  downloadExpensePackPdf,
  fetchClientCoachingSummary,
  fetchCoachingReportPreview,
  fetchExpensePackPreview,
  getExpenseXeroSyncConfig,
  getTravelBookingSummary,
  getContractMergeFields,
  intakeEmailReceipt,
  listContracts,
  getTenderSummary,
  listAtoRates,
  listCoaches,
  listClientPrograms,
  listCoachingEngagements,
  listCoachingSessions,
  listConsultants,
  listExpenses,
  listReminderLastSent,
  listTenders,
  logCoachingSession,
  markExpenseInvoiced,
  listExpenseXeroSyncStatus,
  listTrips,
  pushExpenseToXero,
  runCeoSignoffAutomation,
  runReminderAutomation,
  sendContractForSignature,
  queueContractSignatureReminder,
  markTripTravelBooked,
  createBookedTravelExpenseDraft,
  setTenderDecision,
  triageTender,
  updateAtoRate,
  updateCoachingEngagement,
  updateCoachingSession,
  updateExpenseReceipt,
  updateExpenseTrip,
  updateLookupClientPrograms,
  updateLookupCoaches,
  updateLookupConsultants,
  fetchContractPreview,
  downloadContractPreviewPdf,
  updateContract,
  updateTrip,
} from './api';
import { POLICY_LIBRARY, defaultPolicyIds } from './policies/policyLibrary';

function nightsBetween(departureDate, returnDate) {
  const start = new Date(departureDate);
  const end = new Date(returnDate);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 0;
  const msPerDay = 1000 * 60 * 60 * 24;
  const raw = Math.floor((end - start) / msPerDay);
  return Math.max(raw, 0);
}

function formatFinancialYearLabel(startYear) {
  const year = Number(startYear);
  if (!Number.isInteger(year) || year < 2000) return '';
  return `${year}-${year + 1}`;
}

function currentFinancialYearLabel(referenceDate = new Date()) {
  const now = referenceDate instanceof Date ? referenceDate : new Date(referenceDate);
  if (Number.isNaN(now.getTime())) return '';
  const year = now.getFullYear();
  const month = now.getMonth();
  const startYear = month >= 6 ? year : year - 1;
  return formatFinancialYearLabel(startYear);
}

function normalizeFinancialYearLabel(value) {
  const raw = String(value || '').trim();
  if (!raw) return '';
  const match = raw.match(/^(\d{4})\s*[-/]\s*(\d{2}|\d{4})$/);
  if (!match) return raw;
  const startYear = Number(match[1]);
  let endYear = Number(match[2]);
  if (match[2].length === 2) {
    endYear = Number(`${String(startYear).slice(0, 2)}${match[2]}`);
  }
  if (!Number.isInteger(startYear) || !Number.isInteger(endYear)) return raw;
  return `${startYear}-${endYear}`;
}

async function fetchTodayAudExchangeRateFor(currencyCode) {
  const code = String(currencyCode || '').trim().toUpperCase();
  if (!code || code === 'AUD') return 1;
  const response = await fetch(`https://open.er-api.com/v6/latest/${encodeURIComponent(code)}`);
  if (!response.ok) throw new Error('Unable to load today\'s exchange rate.');
  const payload = await response.json();
  const audRate = Number(payload?.rates?.AUD);
  if (!Number.isFinite(audRate) || audRate <= 0) {
    throw new Error('Exchange-rate service returned an invalid AUD rate.');
  }
  return Number(audRate.toFixed(6));
}

function formatClientProgramLabel(clientName, programName) {
  const client = String(clientName || '').trim() || 'Unknown Client';
  const program = String(programName || '').trim();
  return program ? `${client} / ${program}` : client;
}

function toNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function readLocalStorageNumber(key, fallbackValue) {
  if (typeof window === 'undefined') return fallbackValue;
  const raw = String(localStorage.getItem(key) || '').trim();
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : fallbackValue;
}

function formatAud(value) {
  return `AUD ${toNumber(value).toFixed(2)}`;
}

function formatDateAu(value) {
  const raw = String(value || '').trim();
  const candidate = raw.length >= 10 ? raw.slice(0, 10) : raw;
  const match = candidate.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return raw;
  return `${match[3]}/${match[2]}/${match[1]}`;
}

function formatDateTimeAu(value) {
  const raw = String(value || '').trim();
  if (!raw) return '—';
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return raw;
  const day = String(parsed.getDate()).padStart(2, '0');
  const month = String(parsed.getMonth() + 1).padStart(2, '0');
  const year = String(parsed.getFullYear());
  const hours = String(parsed.getHours()).padStart(2, '0');
  const minutes = String(parsed.getMinutes()).padStart(2, '0');
  return `${day}/${month}/${year} ${hours}:${minutes}`;
}

function daysUntilIso(value) {
  const raw = String(value || '').trim();
  if (!raw) return null;
  const target = new Date(`${raw}T00:00:00`);
  if (Number.isNaN(target.getTime())) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

function deriveDisplayNameFromEmail(email) {
  return String(email || '')
    .split('@')[0]
    .split(/[._-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function normalizeEmailIdentity(email) {
  return String(email || '')
    .trim()
    .toLowerCase()
    .replace('@adapsygroup.com', '@adapsysgroup.com');
}

function formatTokenLabel(value) {
  return String(value || '')
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function toAirportOption(value) {
  const raw = String(value || '').trim();
  if (!raw) return '';
  if (/\b[A-Z]{3}\s+Airport$/i.test(raw)) return raw;
  if (/^[A-Z]{3}$/i.test(raw)) return `${raw.toUpperCase()} Airport`;
  const cityOnly = raw.replace(/\s+airport$/i, '').trim();
  const airportCode = TRAVEL_POINT_CODE_MAP[cityOnly] || TRAVEL_POINT_CODE_MAP[raw];
  if (airportCode) return `${cityOnly} ${airportCode} Airport`;
  if (/airport$/i.test(raw)) return raw;
  return `${raw} Airport`;
}

const CONSULTANT_CATEGORY_OPTIONS = ['accommodation', 'breakfast', 'dinner', 'flights', 'lunch', 'misc', 'per_diem', 'taxi', 'train'];
const ADMIN_CATEGORY_OPTIONS = ['accommodation', 'breakfast', 'dinner', 'flights', 'hotel', 'lunch', 'misc', 'per_diem', 'taxi', 'train', 'uber'];
const EMAIL_INTAKE_CATEGORIES = ['flights', 'hotel', 'uber'];
const EXPENSE_DESCRIPTION_OPTIONS = [
  'Taxi fare',
  'Uber fare',
  'Accommodation charge',
  'Dinner',
  'Breakfast',
  'Lunch',
  'Flight invoice',
  'Flight boarding pass',
  'Per diem claim',
  'Misc purchase',
];
const EXPENSE_RECEIPT_KIND_OPTIONS = ['general', 'invoice', 'tax_invoice', 'itinerary', 'boarding_pass'];
const EXPENSE_SUPPLIER_OPTIONS = ['Uber', 'Virgin', 'Qantas', 'Adina', 'Meriton'];
const EXPENSE_ROUTE_PRESET_OPTIONS = [
  'Adelaide ADL Airport',
  'Gold Coast OOL Airport',
  'Melbourne MEL Airport',
  'Sydney SYD Airport',
  'Home',
  'Hotel',
];
const REIMBURSABLE_PERCENT_OPTIONS = ['100', '75', '50', '25', '0', 'custom'];
const STANDARD_DESCRIPTOR_ACTIVITY_OPTIONS = ['workshop', 'airport transfer', 'client meeting', 'site visit', 'delivery'];
const TRAVEL_POINT_CODE_MAP = {
  'Gold Coast': 'OOL',
  Sydney: 'SYD',
  Melbourne: 'MEL',
  Brisbane: 'BNE',
  Canberra: 'CBR',
  Perth: 'PER',
  Adelaide: 'ADL',
  Nadi: 'NAN',
  Apia: 'APW',
  Noumea: 'NOU',
  Honiara: 'HIR',
  'Port Moresby': 'POM',
};
const COACHING_SESSION_OUTCOMES = ['completed', 'no_show_chargeable', 'cancelled', 'postponed'];
const CONSULTANT_PRIORITY_ORDER = ['cameron bowles', 'collette brown'];
const COACH_ONLY_EMAILS = new Set(['tony.liston@adapsysgroup.com']);
const DEFAULT_CLIENT_ORGS = ['ARTC', 'ATI', 'MHC', 'Mindaroo', 'NSW Dept of HDA', 'PFLP', 'SILA', 'SPC'];
const DEFAULT_COACH_ROSTER = [
  { name: 'Megan Streeter', email: 'megan.streeter@adapsysgroup.com' },
  { name: 'Cameron Bowles', email: 'cameron.bowles@adapsysgroup.com' },
  { name: 'Diana Renner', email: 'diana.renner@adapsysgroup.com' },
  { name: 'Kate Tucker', email: 'kate.tucker@adapsysgroup.com' },
  { name: 'Diego Rodriguez', email: 'diego.rodriguez@adapsysgroup.com' },
  { name: 'Collette Brown', email: 'collette.brown@adapsysgroup.com' },
  { name: 'Tony Liston', email: 'tony.liston@adapsysgroup.com' },
];
const FLIGHT_LOCATION_OPTIONS = [
  'Adelaide ADL Airport',
  'Apia APW Airport',
  'Brisbane BNE Airport',
  'Canberra CBR Airport',
  'Gold Coast OOL Airport',
  'Honiara HIR Airport',
  'Melbourne MEL Airport',
  'Nadi NAN Airport',
  'Noumea NOU Airport',
  'Perth PER Airport',
  'Port Moresby POM Airport',
  'Sydney SYD Airport',
];
const COUNTRY_ACRONYM_LABELS = {
  Australia: 'AU',
  Fiji: 'FJ',
  'New Caledonia': 'NC',
  'Papua New Guinea': 'PNG',
  Samoa: 'WS',
  'Solomon Islands': 'SB',
};
const CONTRACT_DOCUMENT_TYPE_OPTIONS = ['internal_admin_contract', 'new_subcontract', 'variation_amendment'];
const CONTRACT_LIFECYCLE_STATUS_OPTIONS = ['awaiting_signature', 'draft', 'signed'];
const COACHING_PLANNER_INVOICE_TICK_STORAGE_KEY = 'COACHING_PLANNER_INVOICE_TICK_BY_ENGAGEMENT';
const COACHING_RECENT_GROUP_OPEN_STORAGE_KEY = 'COACHING_RECENT_GROUP_OPEN_BY_KEY';
const COUNTRY_CURRENCY_MAP = {
  Australia: 'AUD',
  'Papua New Guinea': 'PGK',
  Fiji: 'FJD',
  Samoa: 'WST',
  'New Caledonia': 'XPF',
  'Solomon Islands': 'SBD',
};
const CAMERON_BOWLES_EMAIL = 'cameron.bowles@adapsysgroup.com';
const COLLETTE_BROWN_EMAIL = 'collette.brown@adapsysgroup.com';
const DEFAULT_ADMIN_EMAIL = 'admin@adapsysgroup.com';
const FIONA_MCEWAN_EMAIL = 'fiona.mcewan@adapsysgroup.com';
const SAMANTHA_WILCKENS_EMAIL = 'samantha.wilckens@adapsysgroup.com';
const PHASE2_MANAGER_EMAILS = new Set([FIONA_MCEWAN_EMAIL]);
const DEMO_CORE_TAB_IDS = new Set(['session-mode', 'help', 'submit-expense', 'coaching-module', 'reports', 'admin-console']);
const PHASE2_TAB_IDS = new Set(['create-project', 'tender-intelligence', 'reports', 'expense-review', 'ato-rates']);
const CLIENT_REPORTS_FEATURE_FLAG_STORAGE_KEY = 'adapsys_client_reports_enabled';
const XERO_SYNC_FEATURE_FLAG_STORAGE_KEY = 'adapsys_xero_sync_enabled';
const XERO_EXPENSE_LINK_STORAGE_KEY = 'adapsys_xero_expense_url';
const XERO_ADMIN_LINK_STORAGE_KEY = 'adapsys_xero_admin_url';
const CTM_TRAVEL_LINK_STORAGE_KEY = 'adapsys_ctm_travel_url';
const GOOGLE_CHAT_LINK_STORAGE_KEY = 'adapsys_google_chat_url';
const CLIENT_REPORTS_CORE_TAB_IDS = new Set(['session-mode', 'help', 'reports']);
const DEMO_ADMIN_EMAIL_PRESETS = [
  CAMERON_BOWLES_EMAIL,
  COLLETTE_BROWN_EMAIL,
  FIONA_MCEWAN_EMAIL,
  SAMANTHA_WILCKENS_EMAIL,
];
const SESSION_PROFILE_OPTIONS = [
  { id: 'cameron-admin', label: 'Cameron Bowles (Admin)', role: 'admin', email: CAMERON_BOWLES_EMAIL },
  { id: 'collette-admin', label: 'Collette Brown (Admin)', role: 'admin', email: COLLETTE_BROWN_EMAIL },
  { id: 'consultant-auto', label: 'Consultant (Auto: first roster email)', role: 'consultant', email: '' },
  { id: 'fiona-builder', label: 'Fiona McEwan (Builder - Full Access)', role: 'admin', email: FIONA_MCEWAN_EMAIL },
  { id: 'samantha-admin', label: 'Samantha Wilckens (Admin)', role: 'admin', email: SAMANTHA_WILCKENS_EMAIL },
];

const SCREEN_TABS = [
  { id: 'session-mode', label: 'Session' },
  { id: 'help', label: 'Help' },
  { id: 'create-project', label: 'Activities' },
  { id: 'submit-expense', label: 'Expenses' },
  { id: 'coaching-module', label: 'Coaching' },
  { id: 'tender-intelligence', label: 'Tenders' },
  { id: 'reports', label: 'Reports' },
  { id: 'expense-review', label: 'Review' },
  { id: 'admin-console', label: 'Admin Console' },
  { id: 'ato-rates', label: 'ATO' },
];

const QUICK_HELP_BY_TAB_ID = {
  'session-mode': {
    title: 'Quick help: choose your session mode',
    steps: [
      'Pick role first (Admin or Consultant).',
      'Confirm email identity before applying session.',
      'Use quick buttons for demo switching when presenting.',
    ],
  },
  'submit-expense': {
    title: 'Quick help: submit an expense',
    steps: [
      'Complete Context first (consultant + activity).',
      'Enter claim details (category, date, amount).',
      'Upload receipt evidence, then finalise and submit.',
    ],
  },
  'coaching-module': {
    title: 'Quick help: log coaching',
    steps: [
      'Open the coaching form path for your role.',
      'Enter date, outcome, and attendance details.',
      'Check Recent Sessions to confirm or edit.',
    ],
  },
  'admin-console': {
    title: 'Quick help: admin console',
    steps: [
      'Use this area for controlled setup and maintenance.',
      'Keep changes small and save one section at a time.',
      'Return to core tabs to validate workflow outcomes.',
    ],
  },
};

const DEFAULT_QUICK_HELP = {
  title: 'Quick help: this screen',
  steps: ['Work top-to-bottom.', 'Complete required fields first.', 'Use Help tab for full walkthroughs and examples.'],
};

function findSessionProfileId(role, email) {
  const normalizedRole = String(role || '').trim().toLowerCase();
  const normalizedEmail = normalizeEmailIdentity(email);
  const matchedProfile = SESSION_PROFILE_OPTIONS.find(
    (profile) => profile.role === normalizedRole && profile.email && normalizeEmailIdentity(profile.email) === normalizedEmail
  );
  return matchedProfile ? matchedProfile.id : '';
}

function currencyForCountry(country) {
  return COUNTRY_CURRENCY_MAP[country] || 'AUD';
}

function sanitizeExternalUrl(value) {
  const raw = String(value || '').trim();
  if (!raw) return '';
  if (/^https?:\/\//i.test(raw)) return raw;
  return '';
}

function listIsoDatesInclusive(startIso, endIso) {
  if (!startIso || !endIso) return [];
  const [sy, sm, sd] = String(startIso).split('-').map(Number);
  const [ey, em, ed] = String(endIso).split('-').map(Number);
  if (!sy || !sm || !sd || !ey || !em || !ed) return [];

  const start = new Date(Date.UTC(sy, sm - 1, sd));
  const end = new Date(Date.UTC(ey, em - 1, ed));
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end < start) return [];

  const days = [];
  const cursor = new Date(start);
  while (cursor <= end) {
    days.push(cursor.toISOString().slice(0, 10));
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }
  return days;
}

function parseIsoDateList(rawValue) {
  const tokens = String(rawValue || '')
    .split(/[\n,;]+/)
    .map((token) => token.trim())
    .filter(Boolean);
  const unique = Array.from(new Set(tokens));
  const validDates = [];
  unique.forEach((token) => {
    const isoToken = /^\d{4}-\d{2}-\d{2}$/.test(token)
      ? token
      : /^\d{2}\/\d{2}\/\d{4}$/.test(token)
        ? `${token.slice(6, 10)}-${token.slice(3, 5)}-${token.slice(0, 2)}`
        : '';
    if (!isoToken) return;
    const parsed = new Date(`${isoToken}T00:00:00Z`);
    if (Number.isNaN(parsed.getTime())) return;
    if (parsed.toISOString().slice(0, 10) !== isoToken) return;
    validDates.push(isoToken);
  });
  return validDates.sort((a, b) => a.localeCompare(b));
}

const INITIAL_EXPENSE_FORM = {
  trip_id: '',
  submitted_by_role: 'admin',
  submitted_by_email: '',
  expense_date: '',
  category: 'taxi',
  amount_local: '',
  reimbursement_override_enabled: false,
  reimbursable_amount_local: '',
  reimbursable_percent: '100',
  currency_local: 'AUD',
  exchange_rate: '1',
  gst_applicable: true,
  paid_by: '',
  description: '',
  supplier: '',
  receipt_url: '',
  receipt_thumb_url: '',
  receipt_kind: 'general',
  receipt_group_key: '',
  descriptor_from: '',
  descriptor_to: '',
  descriptor_activity: '',
  no_receipt: false,
  no_receipt_reason: '',
  notes: '',
  per_diem_bulk_mode: false,
  per_diem_start_date: '',
  per_diem_end_date: '',
  flight_route_from: '',
  flight_route_to: '',
  flight_return_from: '',
  flight_return_to: '',
  flight_is_return_ticket: false,
  flight_boarding_pass_count: '1',
};

const INITIAL_TENDER_FORM = {
  source: 'manual',
  title: '',
  issuer: '',
  location: '',
  summary: '',
  contract_value: '',
  tender_url: '',
  eoi_deadline: '',
  official_close_date: '',
};

const COACHING_BATCH_DRAFT_STORAGE_KEY = 'adapsys_coaching_batch_draft_v1';

function createEmptyCoachingBatchRow() {
  return {
    name: '',
    job_title: '',
    client_org: '',
    coach_input: '',
    coach_email: '',
    total_sessions: '5',
    sessions_used: '0',
    lcp_debrief_enabled: false,
    lcp_debrief_total_sessions: '0',
    lcp_debrief_sessions_used: '0',
  };
}

function createEmptyAdminActivityBulkRow() {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    client_name: '',
    program_name: '',
    name: '',
    consultant_email: '',
    assigned_consultants: [],
    destination_country: 'Australia',
    destination_city: '',
    project_start_date: '',
    project_end_date: '',
    expense_report_required: false,
  };
}

function parseLookupDraftArray(raw) {
  try {
    const parsed = JSON.parse(String(raw || '[]'));
    if (!Array.isArray(parsed)) {
      return { items: [], error: 'JSON must be an array.' };
    }
    return { items: parsed, error: '' };
  } catch {
    return { items: [], error: 'Invalid JSON format.' };
  }
}

export default function App() {
  const coachingLcpDateRef = useRef(null);
  const adminLcpDateRef = useRef(null);
  const [tripForm, setTripForm] = useState({
    name: '',
    consultant_email: '',
    assigned_consultants: [],
    client_name: '',
    program_name: '',
    project_start_date: '',
    project_end_date: '',
    destination_country: 'Australia',
    destination_city: '',
    departure_date: '',
    return_date: '',
    expense_report_required: false,
  });
  const [expenseForm, setExpenseForm] = useState(INITIAL_EXPENSE_FORM);
  const [perDiemMealsByDate, setPerDiemMealsByDate] = useState({});
  const [emailIntakeForm, setEmailIntakeForm] = useState({
    trip_id: '',
    received_from_email: '',
    category: 'flights',
    receipt_url: '',
    receipt_thumb_url: '',
    expense_date: '',
    amount_local: '',
    currency_local: 'AUD',
    exchange_rate: '1',
    gst_applicable: true,
    description: '',
    supplier: '',
    receipt_kind: 'invoice',
    receipt_group_key: '',
    notes: '',
  });
  const [coachingEngagementForm, setCoachingEngagementForm] = useState({
    name: '',
    job_title: '',
    client_org: '',
    coach_email: '',
    total_sessions: '5',
    sessions_used: '0',
    lcp_debrief_enabled: false,
    lcp_debrief_total_sessions: '0',
    lcp_debrief_sessions_used: '0',
    associate_cost_per_session: '',
  });
  const [coachingSessionForm, setCoachingSessionForm] = useState({
    engagement_id: '',
    session_date: '',
    session_type: 'completed',
    lcp_debrief: false,
    lcp_debrief_date: '',
    duration_mins: '60',
    delivery_mode: 'video',
    invoiced_to_adapsys: false,
    notes: '',
  });
  const [trips, setTrips] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [tenders, setTenders] = useState([]);
  const [tenderSummary, setTenderSummary] = useState({
    total: 0,
    urgent: 0,
    pursue: 0,
    monitor: 0,
    ignore: 0,
    led: 0,
  });
  const [coachingEngagements, setCoachingEngagements] = useState([]);
  const [coachingSessions, setCoachingSessions] = useState([]);
  const [atoRates, setAtoRates] = useState([]);
  const [consultants, setConsultants] = useState([]);
  const [coaches, setCoaches] = useState([]);
  const [clientPrograms, setClientPrograms] = useState([]);
  const [status, setStatus] = useState('');
  const [tripStatus, setTripStatus] = useState('');
  const [expenseStatus, setExpenseStatus] = useState('');
  const [coachingStatus, setCoachingStatus] = useState('');
  const [coachingEngagementSearch, setCoachingEngagementSearch] = useState({
    name: '',
    client: '',
  });
  const [coachingSessionEngagementSearch, setCoachingSessionEngagementSearch] = useState({
    coachee: '',
    client: '',
  });
  const [plannerScheduleDraftByEngagementId, setPlannerScheduleDraftByEngagementId] = useState({});
  const [schedulingPlannerEngagementId, setSchedulingPlannerEngagementId] = useState('');
  const [plannerInvoiceTickByEngagementId, setPlannerInvoiceTickByEngagementId] = useState(() => {
    if (typeof window === 'undefined') return {};
    try {
      const raw = localStorage.getItem(COACHING_PLANNER_INVOICE_TICK_STORAGE_KEY);
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch {
      return {};
    }
  });
  const [openRecentCoachingGroupByKey, setOpenRecentCoachingGroupByKey] = useState(() => {
    if (typeof window === 'undefined') return {};
    try {
      const raw = localStorage.getItem(COACHING_RECENT_GROUP_OPEN_STORAGE_KEY);
      if (!raw) return {};
      const parsed = JSON.parse(raw);
      return parsed && typeof parsed === 'object' ? parsed : {};
    } catch {
      return {};
    }
  });
  const [consultantCoachingReportFilters, setConsultantCoachingReportFilters] = useState({
    start_date: '',
    end_date: '',
  });
  const [isCreatingTrip, setIsCreatingTrip] = useState(false);
  const [isSubmittingExpense, setIsSubmittingExpense] = useState(false);
  const [isCreatingCoachingEngagement, setIsCreatingCoachingEngagement] = useState(false);
  const [editingCoachingEngagementId, setEditingCoachingEngagementId] = useState('');
  const [coachingBatchRows, setCoachingBatchRows] = useState(() => {
    if (typeof window === 'undefined') return [createEmptyCoachingBatchRow()];
    try {
      const raw = localStorage.getItem(COACHING_BATCH_DRAFT_STORAGE_KEY);
      if (!raw) return [createEmptyCoachingBatchRow()];
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed) || parsed.length === 0) return [createEmptyCoachingBatchRow()];
      return parsed.map((row) => ({
        ...createEmptyCoachingBatchRow(),
        ...row,
      }));
    } catch {
      return [createEmptyCoachingBatchRow()];
    }
  });
  const [isSubmittingCoachingBatch, setIsSubmittingCoachingBatch] = useState(false);
  const [isSubmittingCoachingSession, setIsSubmittingCoachingSession] = useState(false);
  const [editingCoachingSessionId, setEditingCoachingSessionId] = useState('');
  const [deletingCoachingSessionId, setDeletingCoachingSessionId] = useState('');
  const [isSubmittingTender, setIsSubmittingTender] = useState(false);
  const [activeScreenTabId, setActiveScreenTabId] = useState('submit-expense');
  const [tenderFilter, setTenderFilter] = useState('all');
  const [tenderForm, setTenderForm] = useState(INITIAL_TENDER_FORM);
  const [editingProjectId, setEditingProjectId] = useState('');
  const [dashboardLogoIndex, setDashboardLogoIndex] = useState(0);
  const [sessionRole, setSessionRole] = useState(
    (localStorage.getItem('adapsys_user_role') || 'admin').trim().toLowerCase()
  );
  const [sessionEmail, setSessionEmail] = useState(
    normalizeEmailIdentity(localStorage.getItem('adapsys_user_email') || DEFAULT_ADMIN_EMAIL)
  );
  const [automationDryRun, setAutomationDryRun] = useState(true);
  const [reminderLastSentByTripId, setReminderLastSentByTripId] = useState({});
  const [selectedReportClient, setSelectedReportClient] = useState('');
  const [selectedReportTripId, setSelectedReportTripId] = useState('');
  const [expenseContextClientFilter, setExpenseContextClientFilter] = useState('');
  const [expenseContextConsultantFilter, setExpenseContextConsultantFilter] = useState('');
  const [expenseReportFilters, setExpenseReportFilters] = useState({
    start_date: '',
    end_date: '',
  });
  const [reportPreviewHtml, setReportPreviewHtml] = useState('');
  const [reportPreviewStatus, setReportPreviewStatus] = useState('');
  const [isPreviewingExpensePack, setIsPreviewingExpensePack] = useState(false);
  const [isDownloadingExpensePackPdf, setIsDownloadingExpensePackPdf] = useState(false);
  const [coachingReportFilters, setCoachingReportFilters] = useState({
    report_by: 'coach',
    client_org: '',
    coach_email: '',
    coachee_name: '',
    start_date: '',
    end_date: '',
  });
  const [coachingReportPreviewHtml, setCoachingReportPreviewHtml] = useState('');
  const [coachingReportStatus, setCoachingReportStatus] = useState('');
  const [isPreviewingCoachingReport, setIsPreviewingCoachingReport] = useState(false);
  const [isDownloadingCoachingReportPdf, setIsDownloadingCoachingReportPdf] = useState(false);
  const [clientReportFilters, setClientReportFilters] = useState({
    start_date: '',
    end_date: '',
  });
  const [clientCoachingSummaryRows, setClientCoachingSummaryRows] = useState([]);
  const [clientCoachingSummaryStatus, setClientCoachingSummaryStatus] = useState('');
  const [isLoadingClientCoachingSummary, setIsLoadingClientCoachingSummary] = useState(false);
  const [receiptDropActive, setReceiptDropActive] = useState(false);
  const [expenseValidationActive, setExpenseValidationActive] = useState(false);
  const [sessionLockedFromLink, setSessionLockedFromLink] = useState(false);
  const [receiptDraftByExpenseId, setReceiptDraftByExpenseId] = useState({});
  const [attachingReceiptExpenseId, setAttachingReceiptExpenseId] = useState('');
  const [tripDraftByExpenseId, setTripDraftByExpenseId] = useState({});
  const [movingExpenseId, setMovingExpenseId] = useState('');
  const [deletingExpenseId, setDeletingExpenseId] = useState('');
  const [syncingExpenseId, setSyncingExpenseId] = useState('');
  const [expenseXeroSyncById, setExpenseXeroSyncById] = useState({});
  const [expenseXeroIntegrationStatus, setExpenseXeroIntegrationStatus] = useState(null);
  const [adminEngagementDraftById, setAdminEngagementDraftById] = useState({});
  const [adminSessionDraftById, setAdminSessionDraftById] = useState({});
  const [adminEngagementSearch, setAdminEngagementSearch] = useState({
    name: '',
    client_org: '',
    coach_email: '',
  });
  const [adminSessionQuickSearch, setAdminSessionQuickSearch] = useState({
    coach: '',
    consultant: '',
    client: '',
  });
  const [adminSessionQuickForm, setAdminSessionQuickForm] = useState({
    engagement_id: '',
    next_date: '',
    session_dates_text: '',
    session_type: 'completed',
    lcp_debrief: false,
    lcp_debrief_date: '',
    duration_mins: '60',
    delivery_mode: 'video',
    invoiced_to_adapsys: false,
    notes: '',
  });
  const [adminEngagementSort, setAdminEngagementSort] = useState({
    key: 'name',
    direction: 'asc',
  });
  const [selectedAdminEngagementId, setSelectedAdminEngagementId] = useState('');
  const [savingAdminEngagementId, setSavingAdminEngagementId] = useState('');
  const [deletingAdminEngagementId, setDeletingAdminEngagementId] = useState('');
  const [savingAdminSessionId, setSavingAdminSessionId] = useState('');
  const [isSavingAdminSessionBatch, setIsSavingAdminSessionBatch] = useState(false);
  const [isSavingAllAdminSessions, setIsSavingAllAdminSessions] = useState(false);
  const [adminTripDraftById, setAdminTripDraftById] = useState({});
  const [savingAdminTripId, setSavingAdminTripId] = useState('');
  const [deletingAdminTripId, setDeletingAdminTripId] = useState('');
  const [adminTripSaveNoteById, setAdminTripSaveNoteById] = useState({});
  const [adminBulkActivityRows, setAdminBulkActivityRows] = useState([createEmptyAdminActivityBulkRow()]);
  const [isSubmittingAdminBulkActivities, setIsSubmittingAdminBulkActivities] = useState(false);
  const [adminBulkActivityStatus, setAdminBulkActivityStatus] = useState('');
  const [adminLookupDrafts, setAdminLookupDrafts] = useState({
    consultants: '[]',
    coaches: '[]',
    clientPrograms: '[]',
  });
  const [savingAdminLookupKey, setSavingAdminLookupKey] = useState('');
  const [adminLookupSaveNoteByKind, setAdminLookupSaveNoteByKind] = useState({});
  const [atoRateDraftById, setAtoRateDraftById] = useState({});
  const [savingAtoRateId, setSavingAtoRateId] = useState('');
  const [selectedPerDiemFinancialYear, setSelectedPerDiemFinancialYear] = useState(() => currentFinancialYearLabel());
  const [perDiemUseInternationalCurrency, setPerDiemUseInternationalCurrency] = useState(false);
  const [isResolvingPerDiemFx, setIsResolvingPerDiemFx] = useState(false);
  const [adminEngagementSaveNoteById, setAdminEngagementSaveNoteById] = useState({});
  const [adminConsoleSection, setAdminConsoleSection] = useState('projects');

  const [associateInvoicePrep, setAssociateInvoicePrep] = useState({
    start_date: '',
    end_date: '',
    claim_ref: '',
    selected_ids: {},
  });
  const [associateInvoicePrepStatus, setAssociateInvoicePrepStatus] = useState('');
  const [isClaimingAssociateSessions, setIsClaimingAssociateSessions] = useState(false);

  const associateClaimableSessions = useMemo(() => {
    if (!isConsultantSession) return [];
    const startDate = String(associateInvoicePrep.start_date || '').trim();
    const endDate = String(associateInvoicePrep.end_date || '').trim();
    const rangeStart = startDate ? new Date(`${startDate}T00:00:00Z`) : null;
    const rangeEnd = endDate ? new Date(`${endDate}T23:59:59Z`) : null;

    return coachingSessions
      .filter((session) => !String(session.associate_claim_ref || '').trim())
      .filter((session) => session.session_type === 'completed' || session.session_type === 'no_show_chargeable')
      .filter((session) => {
        if (!rangeStart && !rangeEnd) return true;
        const iso = String(session.session_date || '').slice(0, 10);
        if (!iso) return false;
        const d = new Date(`${iso}T12:00:00Z`);
        if (rangeStart && d < rangeStart) return false;
        if (rangeEnd && d > rangeEnd) return false;
        return true;
      })
      .sort((a, b) => String(a.session_date || '').localeCompare(String(b.session_date || '')));
  }, [associateInvoicePrep.end_date, associateInvoicePrep.start_date, coachingSessions, isConsultantSession]);

  const associateSelectedClaimSessionIds = useMemo(
    () => Object.keys(associateInvoicePrep.selected_ids || {}).filter((key) => associateInvoicePrep.selected_ids[key]),
    [associateInvoicePrep.selected_ids]
  );

  const associateSelectedClaimSummary = useMemo(() => {
    const byId = new Map(associateClaimableSessions.map((row) => [String(row.id), row]));
    const selectedRows = associateSelectedClaimSessionIds
      .map((key) => byId.get(String(key)) || null)
      .filter(Boolean);

    const missingCostRows = selectedRows.filter((row) => {
      const amount = Number(row.associate_cost_amount ?? row.associate_cost_per_session ?? 0);
      return !Number.isFinite(amount) || amount <= 0;
    });

    const total = selectedRows.reduce((sum, row) => {
      const amount = Number(row.associate_cost_amount ?? row.associate_cost_per_session ?? 0);
      if (!Number.isFinite(amount) || amount <= 0) return sum;
      return sum + amount;
    }, 0);

    return {
      selectedRows,
      missingCostCount: missingCostRows.length,
      total,
    };
  }, [associateClaimableSessions, associateSelectedClaimSessionIds]);

  async function onCopyAssociateClaimSummary() {
    const claimRef = String(associateInvoicePrep.claim_ref || '').trim();
    const lines = [];
    if (claimRef) lines.push(`Claim ref: ${claimRef}`);
    lines.push(`Selected sessions: ${associateSelectedClaimSummary.selectedRows.length}`);
    lines.push(`Total: $${associateSelectedClaimSummary.total.toFixed(2)}`);
    lines.push('');
    lines.push('Date\tCoachee\tClient\tType\tCost');
    associateSelectedClaimSummary.selectedRows.forEach((session) => {
      const engagement = coachingEngagementById[String(session.engagement_id)] || null;
      const cost = Number(session.associate_cost_amount ?? session.associate_cost_per_session ?? 0);
      lines.push(
        [
          formatDateAu(session.session_date),
          engagement?.name || String(session.engagement_id),
          engagement?.client_org || '',
          formatTokenLabel(session.session_type),
          Number.isFinite(cost) ? cost.toFixed(2) : '',
        ].join('\t')
      );
    });
    const text = lines.join('\n');

    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        setAssociateInvoicePrepStatus('Copied selected session summary to clipboard.');
        return;
      }
    } catch {
      // ignore and fallback below
    }

    try {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', '');
      textarea.style.position = 'absolute';
      textarea.style.left = '-9999px';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setAssociateInvoicePrepStatus('Copied selected session summary to clipboard.');
    } catch {
      setAssociateInvoicePrepStatus('Could not copy automatically. Please select and copy manually.');
    }
  }

  async function onClaimAssociateSessions() {
    const claimRef = String(associateInvoicePrep.claim_ref || '').trim();
    if (!claimRef) {
      setAssociateInvoicePrepStatus('Enter a claim reference (e.g. KT001) before marking sessions as claimed.');
      return;
    }
    if (!associateSelectedClaimSessionIds.length) {
      setAssociateInvoicePrepStatus('Select at least one session to claim.');
      return;
    }
    if (associateSelectedClaimSummary.missingCostCount > 0) {
      setAssociateInvoicePrepStatus(
        'Some selected sessions have no cost configured. Ask admin to set Cost/Session on the engagement before claiming.'
      );
      return;
    }

    setIsClaimingAssociateSessions(true);
    setAssociateInvoicePrepStatus('Marking selected sessions as claimed...');
    try {
      await claimCoachingSessions({
        session_ids: associateSelectedClaimSessionIds,
        claim_ref: claimRef,
      });
      setAssociateInvoicePrep((prev) => ({
        ...prev,
        selected_ids: {},
      }));
      setAssociateInvoicePrepStatus(`Claim saved. Reference: ${claimRef}.`);
      await refresh();
    } catch (error) {
      setAssociateInvoicePrepStatus(error.message);
    } finally {
      setIsClaimingAssociateSessions(false);
    }
  }
  const [contractScaffoldForm, setContractScaffoldForm] = useState({
    consultant_email: '',
    contract_party_name: '',
    document_type: 'new_subcontract',
    parent_contract_id: '',
    project_name: '',
    start_date: '',
    end_date: '',
    daily_rate: '',
    estimated_days: '',
    variation_reason: '',
    variation_value_delta: '',
    policy_ids: defaultPolicyIds(),
    policy_acknowledged: false,
    policy_notes: '',
    lifecycle_status: 'draft',
    attachments: [],
  });
  const [contractScaffoldRows, setContractScaffoldRows] = useState([]);
  const [contractMergeTemplates, setContractMergeTemplates] = useState([]);
  const [selectedPolicyId, setSelectedPolicyId] = useState(POLICY_LIBRARY[0]?.id || '');
  const [contractScaffoldStatus, setContractScaffoldStatus] = useState('');
  const [contractPreviewHtml, setContractPreviewHtml] = useState('');
  const [contractPreviewRowId, setContractPreviewRowId] = useState('');
  const [isPreviewingContract, setIsPreviewingContract] = useState(false);
  const [isDownloadingContractPdfRowId, setIsDownloadingContractPdfRowId] = useState('');
  const [contractDropActive, setContractDropActive] = useState(false);
  const [travelBookingSummary, setTravelBookingSummary] = useState({
    total_required: 0,
    outstanding_to_book: 0,
    booked: 0,
    need_expense_prompt: 0,
  });
  const [markingTravelBookedTripId, setMarkingTravelBookedTripId] = useState('');
  const [profileScaffoldForm, setProfileScaffoldForm] = useState({
    consultant_email: '',
    title: '',
    expertise_tags: '',
    pacific_countries: '',
    summary: '',
  });
  const [profileScaffoldRows, setProfileScaffoldRows] = useState([]);
  const [profileScaffoldStatus, setProfileScaffoldStatus] = useState('');
  const [layoutMode, setLayoutMode] = useState(() => {
    if (typeof window === 'undefined') return 'tabs';
    const saved = localStorage.getItem('adapsys_layout_mode');
    if (saved === 'tabs' || saved === 'scroll') return saved;
    return window.innerWidth >= 980 ? 'tabs' : 'scroll';
  });
  const [showPhase2Modules, setShowPhase2Modules] = useState(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem('adapsys_show_phase2_modules') === '1';
  });
  const [isQuickHelpOpen, setIsQuickHelpOpen] = useState(false);
  const [helpImageAvailable, setHelpImageAvailable] = useState({ expense: true, coaching: true });
  const [selectedSessionProfileId, setSelectedSessionProfileId] = useState(() => {
    if (typeof window === 'undefined') return '';
    return findSessionProfileId(
      (localStorage.getItem('adapsys_user_role') || 'admin').trim().toLowerCase(),
      normalizeEmailIdentity(localStorage.getItem('adapsys_user_email') || DEFAULT_ADMIN_EMAIL)
    );
  });
  const headerRef = useRef(null);
  const quickHelpRef = useRef(null);
  const expenseProjectRef = useRef(null);
  const expenseConsultantRef = useRef(null);
  const expenseCategoryRef = useRef(null);
  const expenseFlightFromRef = useRef(null);
  const expenseFlightToRef = useRef(null);
  const expenseDateRef = useRef(null);
  const expensePerDiemSingleDateRef = useRef(null);
  const expenseAmountRef = useRef(null);
  const expenseExchangeRateRef = useRef(null);
  const expensePerDiemStartRef = useRef(null);
  const expensePerDiemEndRef = useRef(null);
  const expenseReceiptFileRef = useRef(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem(COACHING_BATCH_DRAFT_STORAGE_KEY, JSON.stringify(coachingBatchRows));
    } catch {
      // Ignore storage failures to avoid blocking data entry.
    }
  }, [coachingBatchRows]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem(
        COACHING_PLANNER_INVOICE_TICK_STORAGE_KEY,
        JSON.stringify(plannerInvoiceTickByEngagementId)
      );
    } catch {
      // Ignore storage failures to avoid blocking session logging.
    }
  }, [plannerInvoiceTickByEngagementId]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem(
        COACHING_RECENT_GROUP_OPEN_STORAGE_KEY,
        JSON.stringify(openRecentCoachingGroupByKey)
      );
    } catch {
      // Ignore storage failures to avoid blocking session logging.
    }
  }, [openRecentCoachingGroupByKey]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem('adapsys_show_phase2_modules', showPhase2Modules ? '1' : '0');
    } catch {
      // Ignore storage failures to avoid blocking UI mode selection.
    }
  }, [showPhase2Modules]);

  useEffect(() => {
    setSelectedSessionProfileId(findSessionProfileId(sessionRole, sessionEmail));
  }, [sessionEmail, sessionRole]);

  useEffect(() => {
    if (!isQuickHelpOpen || typeof window === 'undefined') return;

    function onDocumentPointerDown(event) {
      if (!quickHelpRef.current) return;
      if (!quickHelpRef.current.contains(event.target)) {
        setIsQuickHelpOpen(false);
      }
    }

    function onDocumentKeyDown(event) {
      if (event.key === 'Escape') {
        setIsQuickHelpOpen(false);
      }
    }

    window.addEventListener('mousedown', onDocumentPointerDown);
    window.addEventListener('touchstart', onDocumentPointerDown);
    window.addEventListener('keydown', onDocumentKeyDown);
    return () => {
      window.removeEventListener('mousedown', onDocumentPointerDown);
      window.removeEventListener('touchstart', onDocumentPointerDown);
      window.removeEventListener('keydown', onDocumentKeyDown);
    };
  }, [isQuickHelpOpen]);

  const consultantLookupPreview = useMemo(
    () => parseLookupDraftArray(adminLookupDrafts.consultants),
    [adminLookupDrafts.consultants]
  );
  const coachLookupPreview = useMemo(
    () => parseLookupDraftArray(adminLookupDrafts.coaches),
    [adminLookupDrafts.coaches]
  );
  const clientProgramLookupPreview = useMemo(
    () => parseLookupDraftArray(adminLookupDrafts.clientPrograms),
    [adminLookupDrafts.clientPrograms]
  );

  const adminLookupCanonicalDrafts = useMemo(
    () => ({
      consultants: JSON.stringify(consultants, null, 2),
      coaches: JSON.stringify(coaches, null, 2),
      clientPrograms: JSON.stringify(clientPrograms, null, 2),
    }),
    [clientPrograms, coaches, consultants]
  );

  const adminLookupDirtyByKind = useMemo(
    () => ({
      consultants: adminLookupDrafts.consultants !== adminLookupCanonicalDrafts.consultants,
      coaches: adminLookupDrafts.coaches !== adminLookupCanonicalDrafts.coaches,
      clientPrograms: adminLookupDrafts.clientPrograms !== adminLookupCanonicalDrafts.clientPrograms,
    }),
    [adminLookupCanonicalDrafts, adminLookupDrafts]
  );

  const adminTripDirtyCount = useMemo(() => Object.keys(adminTripDraftById).length, [adminTripDraftById]);
  const adminEngagementDirtyCount = useMemo(
    () => Object.keys(adminEngagementDraftById).length,
    [adminEngagementDraftById]
  );
  const adminLookupDirtyCount = useMemo(
    () => Object.values(adminLookupDirtyByKind).filter(Boolean).length,
    [adminLookupDirtyByKind]
  );

  const contractScaffoldEstimate = useMemo(
    () => toNumber(contractScaffoldForm.daily_rate) * toNumber(contractScaffoldForm.estimated_days),
    [contractScaffoldForm.daily_rate, contractScaffoldForm.estimated_days]
  );

  const contractParentOptions = useMemo(
    () =>
      [...contractScaffoldRows]
        .sort((a, b) => String(a.project_name || '').localeCompare(String(b.project_name || '')))
        .map((row) => ({
          id: row.id,
          label: `${row.project_name || 'Untitled activity'} — ${displayNameFromEmail(row.consultant_email)}`,
        })),
    [contractScaffoldRows]
  );

  const policyLibraryById = useMemo(() => {
    const map = {};
    POLICY_LIBRARY.forEach((policy) => {
      const key = String(policy?.id || '').trim();
      if (!key) return;
      map[key] = policy;
    });
    return map;
  }, []);

  function buildPolicyAttachments(policyIds) {
    const attachedAt = new Date().toISOString();
    return (policyIds || [])
      .map((policyId) => {
        const key = String(policyId || '').trim();
        if (!key) return null;
        const policy = policyLibraryById[key];
        if (!policy) return null;
        return {
          id: `policy-${key}`,
          name: String(policy.attachmentName || `${policy.title || key}.html`),
          size_bytes: 0,
          mime_type: 'text/html',
          attached_at: attachedAt,
          source: 'policy_library',
          policy_id: key,
          policy_title: String(policy.title || ''),
          policy_version: String(policy.version || ''),
          policy_path: String(policy.attachmentSourcePath || ''),
        };
      })
      .filter(Boolean);
  }

  function mergePolicyAttachments(existingAttachments, policyIds) {
    const selectedPolicyIds = (policyIds || []).map((value) => String(value || '').trim()).filter(Boolean);
    const manualAttachments = (existingAttachments || []).filter(
      (attachment) => String(attachment?.source || '').trim().toLowerCase() !== 'policy_library'
    );
    return [...manualAttachments, ...buildPolicyAttachments(selectedPolicyIds)];
  }

  const contractMergeFieldMap = useMemo(() => {
    const map = {};
    (contractMergeTemplates || []).forEach((template) => {
      const key = String(template?.document_type || '').trim();
      if (!key) return;
      map[key] = Array.isArray(template?.merge_fields) ? template.merge_fields : [];
    });
    return map;
  }, [contractMergeTemplates]);

  const mergeFieldsForSelectedContractType = useMemo(
    () => contractMergeFieldMap[contractScaffoldForm.document_type] || [],
    [contractMergeFieldMap, contractScaffoldForm.document_type]
  );

  const contractPoliciesForSelectedType = useMemo(
    () =>
      POLICY_LIBRARY.filter(
        (policy) =>
          !Array.isArray(policy.requiredFor) ||
          !policy.requiredFor.length ||
          policy.requiredFor.includes(contractScaffoldForm.document_type)
      ),
    [contractScaffoldForm.document_type]
  );

  const activePolicyDetail = useMemo(() => {
    if (!contractPoliciesForSelectedType.length) return null;
    return (
      contractPoliciesForSelectedType.find((policy) => policy.id === selectedPolicyId) ||
      contractPoliciesForSelectedType[0]
    );
  }, [contractPoliciesForSelectedType, selectedPolicyId]);

  useEffect(() => {
    if (!contractPoliciesForSelectedType.length) {
      if (selectedPolicyId) setSelectedPolicyId('');
      return;
    }
    const stillExists = contractPoliciesForSelectedType.some((policy) => policy.id === selectedPolicyId);
    if (!stillExists) {
      setSelectedPolicyId(contractPoliciesForSelectedType[0].id);
    }
  }, [contractPoliciesForSelectedType, selectedPolicyId]);

  const contractGenerationReadiness = useMemo(() => {
    const projectReady = Boolean(contractScaffoldForm.project_name.trim());
    const hasConsultant = Boolean(contractScaffoldForm.consultant_email);
    const hasPartyName = Boolean(contractScaffoldForm.contract_party_name.trim());
    const baseReady =
      contractScaffoldForm.document_type === 'internal_admin_contract'
        ? projectReady && hasPartyName
        : projectReady && hasConsultant;
    if (!baseReady) {
      return {
        ready: false,
        message:
          contractScaffoldForm.document_type === 'internal_admin_contract'
            ? 'Set contract party name and activity to generate an internal admin contract draft.'
            : 'Set consultant and activity to generate a contract draft.',
      };
    }
    if (contractScaffoldForm.document_type === 'variation_amendment') {
      if (!contractScaffoldForm.parent_contract_id) {
        return {
          ready: false,
          message: 'Variation amendments need a linked parent contract.',
        };
      }
      if (!contractScaffoldForm.variation_reason.trim()) {
        return {
          ready: false,
          message: 'Variation amendments need a reason/summary of change.',
        };
      }
    }
    return {
      ready: true,
      message:
        contractScaffoldForm.document_type === 'variation_amendment'
          ? 'Variation amendment is ready for template merge.'
          : contractScaffoldForm.document_type === 'internal_admin_contract'
            ? 'Internal admin contract is ready for template merge.'
            : 'Subcontract draft is ready for template merge.',
    };
  }, [
    contractScaffoldForm.contract_party_name,
    contractScaffoldForm.consultant_email,
    contractScaffoldForm.document_type,
    contractScaffoldForm.parent_contract_id,
    contractScaffoldForm.project_name,
    contractScaffoldForm.variation_reason,
  ]);

  const contractOpsSummary = useMemo(() => {
    const summary = {
      total: contractScaffoldRows.length,
      awaitingSignature: 0,
      internalAdmin: 0,
      variation: 0,
      withAttachments: 0,
      overdueSignature: 0,
    };

    contractScaffoldRows.forEach((row) => {
      if (row.lifecycle_status === 'awaiting_signature') {
        summary.awaitingSignature += 1;
        const sentDays = daysUntilIso(String(row.sent_date || '').slice(0, 10));
        if (sentDays !== null && sentDays <= -8) {
          summary.overdueSignature += 1;
        }
      }
      if (row.document_type === 'internal_admin_contract') summary.internalAdmin += 1;
      if (row.document_type === 'variation_amendment') summary.variation += 1;
      if (Array.isArray(row.attachments) && row.attachments.length) summary.withAttachments += 1;
    });

    return summary;
  }, [contractScaffoldRows]);

  async function onCreateContractScaffold() {
    if (!contractGenerationReadiness.ready) {
      setContractScaffoldStatus(contractGenerationReadiness.message);
      return;
    }
    if ((contractScaffoldForm.policy_ids || []).length && !contractScaffoldForm.policy_acknowledged) {
      setContractScaffoldStatus('Tick policy acknowledgement before adding this contract scaffold row.');
      return;
    }
    const normalizedProject = contractScaffoldForm.project_name.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-');
    const generatedDocumentName =
      contractScaffoldForm.document_type === 'variation_amendment'
        ? `variation-${normalizedProject || 'draft'}.docx`
        : contractScaffoldForm.document_type === 'internal_admin_contract'
          ? `internal-admin-${normalizedProject || 'draft'}.docx`
          : `subcontract-${normalizedProject || 'draft'}.docx`;
    const parentContract = contractScaffoldRows.find((row) => row.id === contractScaffoldForm.parent_contract_id) || null;
    const entry = {
      ...contractScaffoldForm,
      attachments: mergePolicyAttachments(contractScaffoldForm.attachments, contractScaffoldForm.policy_ids),
      estimated_value: contractScaffoldEstimate,
      generated_document_name: generatedDocumentName,
      generated_document_status: contractGenerationReadiness.ready ? 'ready_to_generate' : 'draft_only',
      policy_ids: contractScaffoldForm.policy_ids || [],
      policy_acknowledged: Boolean(contractScaffoldForm.policy_acknowledged),
      policy_notes: String(contractScaffoldForm.policy_notes || '').trim() || null,
      contract_party_name:
        contractScaffoldForm.document_type === 'internal_admin_contract'
          ? contractScaffoldForm.contract_party_name.trim()
          : contractScaffoldForm.contract_party_name,
      parent_contract_label: parentContract
        ? `${parentContract.project_name || 'Untitled activity'} (${displayNameFromEmail(parentContract.consultant_email)})`
        : '',
    };
    try {
      const created = await createContract(entry);
      setContractScaffoldRows((prev) => [created, ...prev]);
      setContractScaffoldStatus(
        `${formatTokenLabel(created.document_type)} row added for ${
          created.contract_party_name || displayNameFromEmail(created.consultant_email)
        }.`
      );
    } catch (error) {
      setContractScaffoldStatus(error.message || 'Failed to create contract row.');
    }
  }

  function onAdminQuickAddDate() {
    const dateToAdd = String(adminSessionQuickForm.next_date || '').trim();
    if (!dateToAdd) {
      setStatus('Select a date before adding to the list.');
      return;
    }
    const mergedDates = parseIsoDateList(`${adminSessionQuickForm.session_dates_text}\n${dateToAdd}`);
    setAdminSessionQuickForm((prev) => ({
      ...prev,
      next_date: '',
      session_dates_text: mergedDates.join('\n'),
    }));
  }

  function onAdminQuickRemoveDate(dateValue) {
    setAdminSessionQuickForm((prev) => ({
      ...prev,
      session_dates_text: parseIsoDateList(prev.session_dates_text)
        .filter((value) => value !== dateValue)
        .join('\n'),
    }));
  }

  async function onCreateAdminSessionBatch() {
    const engagementId = String(adminSessionQuickForm.engagement_id || '').trim();
    if (!engagementId) {
      setStatus('Search and select a coachee before adding session dates.');
      return;
    }

    const enteredTokens = String(adminSessionQuickForm.session_dates_text || '')
      .split(/[\n,;]+/)
      .map((token) => token.trim())
      .filter(Boolean);
    const uniqueEnteredTokens = Array.from(new Set(enteredTokens));
    const sessionDates = parseIsoDateList(adminSessionQuickForm.session_dates_text);

    if (!sessionDates.length) {
      setStatus('Add at least one valid session date (dd/mm/yyyy or yyyy-mm-dd).');
      return;
    }
    if (sessionDates.length !== uniqueEnteredTokens.length) {
      setStatus('Some dates are invalid. Use dd/mm/yyyy or yyyy-mm-dd, one date per line.');
      return;
    }
    if (adminSessionQuickForm.lcp_debrief && !String(adminSessionQuickForm.lcp_debrief_date || '').trim()) {
      setStatus('Select an LCP de-brief date when the LCP tick is enabled.');
      return;
    }
    if (adminSessionQuickForm.lcp_debrief && !selectedAdminQuickLcpEnabled) {
      setStatus('Selected coachee does not have LCP de-brief entitlement enabled.');
      return;
    }

    const durationMins = Number(adminSessionQuickForm.duration_mins || 0);
    if (!Number.isFinite(durationMins) || durationMins <= 0) {
      setStatus('Session duration must be 1 minute or greater.');
      return;
    }
    const deliveryMode = String(adminSessionQuickForm.delivery_mode || '').trim() || 'video';

    const basePayload = {
      engagement_id: engagementId,
      session_type: adminSessionQuickForm.session_type,
      lcp_debrief: Boolean(adminSessionQuickForm.lcp_debrief),
      lcp_debrief_date: adminSessionQuickForm.lcp_debrief
        ? String(adminSessionQuickForm.lcp_debrief_date || '').trim() || null
        : null,
      duration_mins: durationMins,
      delivery_mode: deliveryMode,
      invoiced_to_adapsys: Boolean(adminSessionQuickForm.invoiced_to_adapsys),
      notes: String(adminSessionQuickForm.notes || '').trim() || null,
    };

    setIsSavingAdminSessionBatch(true);
    setStatus(`Saving ${sessionDates.length} coaching session date(s)...`);

    let successCount = 0;
    const failedDates = [];
    for (const sessionDate of sessionDates) {
      try {
        await logCoachingSession({
          ...basePayload,
          session_date: sessionDate,
        });
        successCount += 1;
      } catch (error) {
        failedDates.push(`${formatDateAu(sessionDate)} (${error.message || 'save failed'})`);
      }
    }

    try {
      if (successCount > 0) {
        await refresh();
      }
      if (failedDates.length) {
        setStatus(
          `Saved ${successCount}/${sessionDates.length} sessions. Failed: ${failedDates.slice(0, 3).join(' | ')}`
        );
      } else {
        setStatus(`Saved ${successCount} coaching sessions.`);
      }
      setAdminSessionQuickForm((prev) => ({
        ...prev,
        next_date: '',
        session_dates_text: '',
      }));
    } finally {
      setIsSavingAdminSessionBatch(false);
    }
  }

  function onOpenContractPreviewInNewTab() {
    if (!contractPreviewHtml) return;
    const previewBlob = new Blob([contractPreviewHtml], { type: 'text/html' });
    const previewUrl = window.URL.createObjectURL(previewBlob);
    window.open(previewUrl, '_blank', 'noopener,noreferrer');
    window.setTimeout(() => {
      window.URL.revokeObjectURL(previewUrl);
    }, 15000);
  }

  function onClearContractPreview() {
    setContractPreviewHtml('');
    setContractPreviewRowId('');
    setContractScaffoldStatus('Contract preview cleared.');
  }

  function onContractDocumentTypeChange(nextType) {
    const defaultPolicyIdsForType = POLICY_LIBRARY.filter(
      (policy) =>
        policy.sendByDefault &&
        (!Array.isArray(policy.requiredFor) || !policy.requiredFor.length || policy.requiredFor.includes(nextType))
    ).map((policy) => policy.id);
    setContractScaffoldForm((prev) => ({
      ...prev,
      document_type: nextType,
      parent_contract_id: nextType === 'variation_amendment' ? prev.parent_contract_id : '',
      variation_reason: nextType === 'variation_amendment' ? prev.variation_reason : '',
      variation_value_delta: nextType === 'variation_amendment' ? prev.variation_value_delta : '',
      contract_party_name: nextType === 'internal_admin_contract' ? prev.contract_party_name : '',
      policy_ids: defaultPolicyIdsForType,
      policy_acknowledged: false,
    }));
  }

  function onToggleContractPolicy(policyId, checked) {
    const key = String(policyId || '').trim();
    if (!key) return;
    setContractScaffoldForm((prev) => {
      const existing = new Set(Array.isArray(prev.policy_ids) ? prev.policy_ids : []);
      if (checked) {
        existing.add(key);
      } else {
        existing.delete(key);
      }
      return {
        ...prev,
        policy_ids: Array.from(existing),
        attachments: mergePolicyAttachments(prev.attachments, Array.from(existing)),
        policy_acknowledged: false,
      };
    });
  }

  async function onAcknowledgeContractPolicies(rowId) {
    const row = contractScaffoldRows.find((item) => item.id === rowId);
    if (!row) return;
    const nextAttachments = mergePolicyAttachments(row.attachments, row.policy_ids || []);
    onUpdateContractRow(rowId, { policy_acknowledged: true, attachments: nextAttachments });
    try {
      await updateContract(rowId, { policy_acknowledged: true, attachments: nextAttachments });
      setContractScaffoldStatus('Policy checklist tick captured for this contract row.');
    } catch (error) {
      setContractScaffoldStatus(error.message || 'Failed to save policy checklist tick.');
    }
  }

  function onAttachContractFiles(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    const nextAttachments = files
      .filter((file) => file && file.name)
      .map((file) => ({
        id: `${Date.now()}-${file.name}`,
        name: file.name,
        size_bytes: Number(file.size || 0),
        mime_type: file.type || 'application/octet-stream',
        attached_at: new Date().toISOString(),
      }));
    if (!nextAttachments.length) return;
    setContractScaffoldForm((prev) => ({
      ...prev,
      attachments: [...(prev.attachments || []), ...nextAttachments],
    }));
    setContractScaffoldStatus(
      `${nextAttachments.length} file${nextAttachments.length === 1 ? '' : 's'} attached to ${
        contractScaffoldForm.document_type === 'variation_amendment'
          ? 'variation'
          : contractScaffoldForm.document_type === 'internal_admin_contract'
            ? 'internal admin contract'
            : 'subcontract'
      } draft.`
    );
  }

  function onRemoveContractAttachment(attachmentId) {
    setContractScaffoldForm((prev) => ({
      ...prev,
      attachments: (prev.attachments || []).filter((attachment) => attachment.id !== attachmentId),
    }));
    setContractScaffoldStatus('Removed one draft attachment.');
  }

  function onUpdateContractRow(rowId, updater) {
    setContractScaffoldRows((prev) =>
      prev.map((row) => (row.id !== rowId ? row : { ...row, ...(typeof updater === 'function' ? updater(row) : updater) }))
    );
  }

  async function onDeleteContractRow(rowId) {
    const selectedRow = contractScaffoldRows.find((row) => row.id === rowId);
    if (!selectedRow) return;
    const confirmed = window.confirm(
      `Delete contract row for "${selectedRow.project_name || 'activity'}"?`
    );
    if (!confirmed) return;
    try {
      await deleteContract(rowId);
      setContractScaffoldRows((prev) => prev.filter((row) => row.id !== rowId));
      setContractScaffoldStatus('Contract row deleted.');
    } catch (error) {
      setContractScaffoldStatus(error.message || 'Failed to delete contract row.');
    }
  }

  async function onMarkContractLifecycle(rowId, nextStatus) {
    const selectedRow = contractScaffoldRows.find((row) => row.id === rowId);
    if (!selectedRow) return;

    if (nextStatus === 'awaiting_signature') {
      if ((selectedRow.policy_ids || []).length && !selectedRow.policy_acknowledged) {
        setContractScaffoldStatus('Tick policies as sent before issuing this contract for signature.');
        return;
      }
      const fallbackSignerEmail =
        String(localStorage.getItem('adapsys_user_email') || '').trim().toLowerCase() || DEFAULT_ADMIN_EMAIL;
      const signerEmail =
        selectedRow.document_type === 'internal_admin_contract'
          ? fallbackSignerEmail
          : String(selectedRow.consultant_email || fallbackSignerEmail).trim().toLowerCase();
      const signerName =
        selectedRow.contract_party_name ||
        displayNameFromEmail(selectedRow.consultant_email) ||
        deriveDisplayNameFromEmail(fallbackSignerEmail);

      try {
        const nextAttachments = mergePolicyAttachments(selectedRow.attachments, selectedRow.policy_ids || []);
        if ((selectedRow.policy_ids || []).length) {
          onUpdateContractRow(rowId, { attachments: nextAttachments });
          await updateContract(rowId, { attachments: nextAttachments });
        }
        const signatureResult = await sendContractForSignature({
          contract_id: selectedRow.id,
          document_type: selectedRow.document_type,
          document_name: selectedRow.generated_document_name || selectedRow.project_name || 'contract-draft.docx',
          signer_email: signerEmail,
          signer_name: signerName,
          source_payload: {
            ...selectedRow,
            attachments: nextAttachments,
          },
        });

        onUpdateContractRow(rowId, {
          lifecycle_status: signatureResult.status || 'awaiting_signature',
          sent_date: signatureResult.sent_at || new Date().toISOString(),
          signature_provider: signatureResult.provider || 'local',
          signature_envelope_id: signatureResult.envelope_id || '',
          signature_detail: signatureResult.detail || '',
          reminder_count: Number(signatureResult.reminder_count || 0),
          reminder_requested_at: signatureResult.reminder_requested_at || '',
        });
        await updateContract(rowId, {
          lifecycle_status: signatureResult.status || 'awaiting_signature',
          sent_date: signatureResult.sent_at || new Date().toISOString(),
          signature_provider: signatureResult.provider || 'local',
          signature_envelope_id: signatureResult.envelope_id || '',
          signature_detail: signatureResult.detail || '',
          reminder_count: Number(signatureResult.reminder_count || 0),
          reminder_requested_at: signatureResult.reminder_requested_at || null,
        });
        setContractScaffoldStatus(signatureResult.detail || 'Contract sent for signature.');
      } catch (error) {
        setContractScaffoldStatus(error.message || 'Failed to send contract for signature.');
      }
      return;
    }

    const nowIso = new Date().toISOString();
    onUpdateContractRow(rowId, (row) => ({
      lifecycle_status: nextStatus,
      sent_date: nextStatus === 'awaiting_signature' ? nowIso : row.sent_date,
      signed_date: nextStatus === 'signed' ? nowIso : row.signed_date,
      reminder_requested_at: nextStatus === 'signed' ? '' : row.reminder_requested_at,
    }));
    try {
      await updateContract(rowId, {
        lifecycle_status: nextStatus,
        sent_date: nextStatus === 'awaiting_signature' ? nowIso : selectedRow.sent_date,
        signed_date: nextStatus === 'signed' ? nowIso : selectedRow.signed_date,
      });
      setContractScaffoldStatus(`Marked contract as ${formatTokenLabel(nextStatus)}.`);
    } catch (error) {
      setContractScaffoldStatus(error.message || 'Failed to update contract lifecycle.');
    }
  }

  async function onFlagContractReminder(rowId) {
    const selectedRow = contractScaffoldRows.find((row) => row.id === rowId);
    if (!selectedRow) return;

    try {
      const reminderResult = await queueContractSignatureReminder(rowId, {
        note: `Reminder requested for ${selectedRow.project_name || 'activity contract'}`,
      });
      onUpdateContractRow(rowId, {
        reminder_requested_at: reminderResult.reminder_requested_at || new Date().toISOString(),
        reminder_count: Number(reminderResult.reminder_count || 1),
        signature_detail: reminderResult.detail || '',
      });
      await updateContract(rowId, {
        reminder_requested_at: reminderResult.reminder_requested_at || new Date().toISOString(),
        reminder_count: Number(reminderResult.reminder_count || 1),
        signature_detail: reminderResult.detail || '',
      });
      setContractScaffoldStatus(reminderResult.detail || 'Reminder queued for this contract.');
    } catch (error) {
      setContractScaffoldStatus(error.message || 'Failed to queue contract reminder.');
    }
  }

  async function onMarkTripTravelBooked(trip) {
    const key = String(trip.id);
    setMarkingTravelBookedTripId(key);
    setAdminTripSaveNoteById((prev) => ({ ...prev, [key]: 'Marking booked...' }));
    try {
      const result = await markTripTravelBooked(trip.id);
      setAdminTripSaveNoteById((prev) => ({ ...prev, [key]: 'Travel marked booked.' }));
      if (result.should_prompt_add_expense) {
        const proceedToExpenseDraft = window.confirm(
          'Travel is booked and this activity requires an expense report. Open a prefilled expense draft now?'
        );
        if (proceedToExpenseDraft) {
          await onCreateBookedTravelExpenseDraft({
            ...trip,
            travel_request_status: result.travel_request_status || 'booked',
            travel_booked_add_expense_prompted: false,
          });
        }
      }
      setStatus(result.detail || 'Travel marked as booked.');
      await refresh();
    } catch (error) {
      setAdminTripSaveNoteById((prev) => ({ ...prev, [key]: `Travel update failed: ${error.message}` }));
      setStatus(error.message || 'Failed to mark travel booked.');
    } finally {
      setMarkingTravelBookedTripId('');
    }
  }

  async function onCreateBookedTravelExpenseDraft(trip) {
    const tripId = String(trip?.id || '').trim();
    if (!tripId) return;

    try {
      const result = await createBookedTravelExpenseDraft(tripId);
      const draftPayload = result?.draft_payload || {};
      setExpenseForm(() => ({
        ...INITIAL_EXPENSE_FORM,
        ...draftPayload,
      }));
      setActiveScreenTabId('submit-expense');
      setStatus(
        result?.detail ||
          'Opened prefilled expense draft from booked travel queue. Complete amount/supplier and submit.'
      );
    } catch (error) {
      setStatus(error.message || 'Failed to open booked-travel expense draft.');
    }
  }

  async function onDeleteAdminTrip(trip) {
    const key = String(trip.id);
    const label = String(trip.name || trip.id || 'this activity').trim();
    const confirmed = window.confirm(
      `Delete activity "${label}"? This is blocked if linked expenses exist.`
    );
    if (!confirmed) return;

    setDeletingAdminTripId(key);
    setAdminTripSaveNoteById((prev) => ({ ...prev, [key]: 'Deleting...' }));
    try {
      await deleteTrip(trip.id);
      setAdminTripDraftById((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
      setAdminTripSaveNoteById((prev) => ({ ...prev, [key]: 'Deleted.' }));
      setStatus(`Deleted activity: ${label}.`);
      await refresh();
    } catch (error) {
      setAdminTripSaveNoteById((prev) => ({ ...prev, [key]: `Delete failed: ${error.message}` }));
      setStatus(error.message || 'Failed to delete activity.');
    } finally {
      setDeletingAdminTripId('');
    }
  }

  function onAdminBulkActivityFieldChange(rowId, field, value) {
    setAdminBulkActivityRows((prev) =>
      prev.map((row) => (row.id !== rowId ? row : { ...row, [field]: value }))
    );
    setAdminBulkActivityStatus('');
  }

  function onAddAdminBulkActivityRow() {
    setAdminBulkActivityRows((prev) => [...prev, createEmptyAdminActivityBulkRow()]);
    setAdminBulkActivityStatus('');
  }

  function onRemoveAdminBulkActivityRow(rowId) {
    setAdminBulkActivityRows((prev) => {
      const next = prev.filter((row) => row.id !== rowId);
      return next.length ? next : [createEmptyAdminActivityBulkRow()];
    });
    setAdminBulkActivityStatus('');
  }

  async function onSubmitAdminBulkActivities(event) {
    event.preventDefault();
    const preparedRows = adminBulkActivityRows
      .map((row, index) => ({
        ...row,
        rowNumber: index + 1,
        name: String(row.name || '').trim(),
        client_name: String(row.client_name || '').trim(),
        program_name: String(row.program_name || '').trim(),
        consultant_email: String(row.consultant_email || '').trim().toLowerCase(),
        destination_country: String(row.destination_country || '').trim(),
        destination_city: String(row.destination_city || '').trim(),
        project_start_date: String(row.project_start_date || '').trim(),
        project_end_date: String(row.project_end_date || '').trim(),
      }))
      .filter((row) => row.name || row.client_name || row.consultant_email);

    if (!preparedRows.length) {
      setAdminBulkActivityStatus('Add at least one activity row with activity/client/consultant details.');
      return;
    }

    const validationError = preparedRows.find((row) => {
      if (!row.name || !row.client_name || !row.destination_country) return true;
      const assigned = Array.isArray(row.assigned_consultants)
        ? row.assigned_consultants.map((item) => String(item).trim().toLowerCase()).filter(Boolean)
        : String(row.assigned_consultants || '')
          .split(',')
          .map((item) => item.trim().toLowerCase())
          .filter(Boolean);
      return !row.consultant_email && !assigned.length;
    });

    if (validationError) {
      setAdminBulkActivityStatus(
        `Row ${validationError.rowNumber} is missing required fields (activity, client, country, and at least one consultant).`
      );
      return;
    }

    setIsSubmittingAdminBulkActivities(true);
    setAdminBulkActivityStatus(`Creating ${preparedRows.length} activity row(s)...`);

    let successCount = 0;
    const failed = [];

    for (const row of preparedRows) {
      const assignedList = Array.isArray(row.assigned_consultants)
        ? row.assigned_consultants.map((item) => String(item).trim().toLowerCase()).filter(Boolean)
        : String(row.assigned_consultants || '')
          .split(',')
          .map((item) => item.trim().toLowerCase())
          .filter(Boolean);
      const roster = Array.from(new Set([row.consultant_email, ...assignedList].filter(Boolean)));

      try {
        await createTrip({
          name: row.name,
          consultant_email: row.consultant_email || roster[0] || '',
          assigned_consultants: roster,
          client_name: row.client_name,
          program_name: row.program_name || null,
          destination_country: row.destination_country,
          destination_city: row.destination_city || null,
          project_start_date: row.project_start_date || null,
          project_end_date: row.project_end_date || null,
          departure_date: row.project_start_date || null,
          return_date: row.project_end_date || null,
          expense_report_required: Boolean(row.expense_report_required),
        });
        successCount += 1;
      } catch (error) {
        failed.push(`Row ${row.rowNumber}: ${error.message || 'Create failed'}`);
      }
    }

    await refresh();
    if (failed.length) {
      setAdminBulkActivityStatus(
        `Created ${successCount}/${preparedRows.length}. ${failed.slice(0, 2).join(' | ')}`
      );
    } else {
      setAdminBulkActivityStatus(`Created ${successCount} activities successfully.`);
      setAdminBulkActivityRows([createEmptyAdminActivityBulkRow()]);
    }
    setIsSubmittingAdminBulkActivities(false);
  }

  async function onGenerateContractPreview(rowId) {
    const row = contractScaffoldRows.find((item) => item.id === rowId);
    if (!row) {
      setContractScaffoldStatus('Contract row not found for preview.');
      return;
    }
    setIsPreviewingContract(true);
    setContractPreviewRowId(rowId);
    setContractScaffoldStatus('Generating contract preview...');
    try {
      const previewHtml = await fetchContractPreview(rowId);
      setContractPreviewHtml(previewHtml);
      onUpdateContractRow(rowId, { generated_document_status: 'generated_preview' });
      try {
        await updateContract(rowId, { generated_document_status: 'generated_preview' });
      } catch {
        // Preview should still be available even if status persistence fails.
      }
      setContractScaffoldStatus(`Contract preview ready for ${row.project_name || 'selected row'}.`);
    } catch (error) {
      setContractScaffoldStatus(error.message || 'Failed to generate contract preview.');
    } finally {
      setIsPreviewingContract(false);
    }
  }

  async function onDownloadContractPreviewPdf(rowId) {
    const row = contractScaffoldRows.find((item) => item.id === rowId);
    if (!row) {
      setContractScaffoldStatus('Contract row not found for PDF export.');
      return;
    }
    setIsDownloadingContractPdfRowId(rowId);
    setContractScaffoldStatus('Preparing contract PDF...');
    try {
      const blob = await downloadContractPreviewPdf(rowId);
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      const baseName = String(row.generated_document_name || row.project_name || 'contract-preview')
        .replace(/\.html?$/i, '')
        .trim();
      const safeName = (baseName || 'contract-preview').toLowerCase().replace(/[^a-z0-9-_.]+/g, '-');
      anchor.download = `${safeName}.pdf`;
      anchor.click();
      window.URL.revokeObjectURL(url);
      setContractScaffoldStatus('Contract PDF download started.');
    } catch (error) {
      setContractScaffoldStatus(error.message || 'Failed to download contract PDF.');
    } finally {
      setIsDownloadingContractPdfRowId('');
    }
  }

  function formatFileSize(sizeBytes) {
    const raw = Number(sizeBytes || 0);
    if (raw < 1024) return `${raw} B`;
    if (raw < 1024 * 1024) return `${(raw / 1024).toFixed(1)} KB`;
    return `${(raw / (1024 * 1024)).toFixed(2)} MB`;
  }

  function onCreateProfileScaffold() {
    if (!profileScaffoldForm.consultant_email) {
      setProfileScaffoldStatus('Select a consultant before adding a profile scaffold row.');
      return;
    }
    const entry = {
      id: `${Date.now()}`,
      ...profileScaffoldForm,
    };
    setProfileScaffoldRows((prev) => [entry, ...prev]);
    setProfileScaffoldStatus(`Profile scaffold row added for ${displayNameFromEmail(entry.consultant_email)}.`);
  }

  function onOpenExternalTool(url, label) {
    if (!url) {
      setExpenseStatus(
        `${label} link is not configured yet. Add localStorage key ${XERO_EXPENSE_LINK_STORAGE_KEY}, ${XERO_ADMIN_LINK_STORAGE_KEY}, ${CTM_TRAVEL_LINK_STORAGE_KEY}, or ${GOOGLE_CHAT_LINK_STORAGE_KEY}.`
      );
      return;
    }
    window.open(url, '_blank', 'noopener,noreferrer');
  }

  const clientOptions = useMemo(() => {
    const fromPrograms = clientPrograms.map((row) => String(row?.client_name || '').trim());
    const fromTrips = trips.map((row) => String(row?.client_name || '').trim());
    const fromEngagements = coachingEngagements.map((row) => String(row?.client_org || '').trim());
    return Array.from(new Set([...DEFAULT_CLIENT_ORGS, ...fromPrograms, ...fromTrips, ...fromEngagements].filter(Boolean))).sort(
      (a, b) => a.localeCompare(b)
    );
  }, [clientPrograms, trips, coachingEngagements]);

  const isConsultantSession = sessionRole === 'consultant';
  const isAdminSession = sessionRole === 'admin';
  const isClientViewerSession = sessionRole === 'client_viewer';
  const isClientReportsFeatureEnabled =
    String(localStorage.getItem(CLIENT_REPORTS_FEATURE_FLAG_STORAGE_KEY) || '').trim().toLowerCase() === '1';
  const isXeroSyncFeatureEnabled =
    String(localStorage.getItem(XERO_SYNC_FEATURE_FLAG_STORAGE_KEY) || '').trim().toLowerCase() === '1';
  const xeroIntegrationBannerText = useMemo(() => {
    if (!isXeroSyncFeatureEnabled) {
      return `Xero sync controls are hidden. Set localStorage key ${XERO_SYNC_FEATURE_FLAG_STORAGE_KEY}=1 to show controls.`;
    }
    if (!expenseXeroIntegrationStatus?.enabled) {
      return 'Xero sync is disabled on backend. Set ADAPSYS_XERO_SYNC_ENABLED=1 to enable push/retry actions.';
    }
    if (expenseXeroIntegrationStatus?.mode === 'stub') {
      return 'Xero sync is running in STUB mode (demo-safe). Push actions will not send data to live Xero yet.';
    }
    if (!expenseXeroIntegrationStatus?.credentials_configured) {
      return 'Xero sync is set to LIVE mode, but credentials are missing. Configure XERO_CLIENT_ID, XERO_CLIENT_SECRET, XERO_REFRESH_TOKEN, and XERO_TENANT_ID.';
    }
    return 'Xero sync is in LIVE mode with credentials configured.';
  }, [expenseXeroIntegrationStatus, isXeroSyncFeatureEnabled]);
  const isCoachOnlySession = COACH_ONLY_EMAILS.has(normalizeEmailIdentity(sessionEmail));
  const canManagePhase2Modules =
    isAdminSession && PHASE2_MANAGER_EMAILS.has(normalizeEmailIdentity(sessionEmail));
  const isSimplifiedAdminDemoView =
    isAdminSession && (!canManagePhase2Modules || !showPhase2Modules);
  const externalToolLinks = useMemo(
    () => ({
      xeroExpense: sanitizeExternalUrl(localStorage.getItem(XERO_EXPENSE_LINK_STORAGE_KEY)),
      xeroAdmin: sanitizeExternalUrl(localStorage.getItem(XERO_ADMIN_LINK_STORAGE_KEY)),
      ctmTravel: sanitizeExternalUrl(localStorage.getItem(CTM_TRAVEL_LINK_STORAGE_KEY)),
      googleChat: sanitizeExternalUrl(localStorage.getItem(GOOGLE_CHAT_LINK_STORAGE_KEY)),
    }),
    []
  );
  const expenseExternalToolActions = useMemo(() => {
    const actions = [
      {
        id: 'xero-expense',
        label: isConsultantSession ? 'Open Xero (My Expenses)' : 'Open Xero Expenses',
        url: externalToolLinks.xeroExpense,
      },
      {
        id: 'ctm-travel',
        label: 'Open CTM Travel',
        url: externalToolLinks.ctmTravel,
      },
      {
        id: 'google-chat',
        label: 'Open Team Chat',
        url: externalToolLinks.googleChat,
      },
    ];
    if (isAdminSession) {
      actions.push({
        id: 'xero-admin',
        label: 'Open Xero Admin',
        url: externalToolLinks.xeroAdmin,
      });
    }
    return actions;
  }, [externalToolLinks, isAdminSession, isConsultantSession]);

  const orderedConsultants = useMemo(() => {
    const rank = (name) => {
      const idx = CONSULTANT_PRIORITY_ORDER.indexOf(name.toLowerCase());
      return idx === -1 ? 999 : idx;
    };
    return [...consultants].sort((a, b) => {
      const byRank = rank(a.name) - rank(b.name);
      if (byRank !== 0) return byRank;
      return a.name.localeCompare(b.name);
    });
  }, [consultants]);

  const allConsultantEmails = useMemo(
    () => orderedConsultants.map((row) => row.email),
    [orderedConsultants]
  );

  const consultantNameByEmail = useMemo(() => {
    const map = {};
    orderedConsultants.forEach((consultant) => {
      if (!consultant?.email) return;
      map[String(consultant.email).toLowerCase()] = consultant.name || consultant.email;
    });
    return map;
  }, [orderedConsultants]);

  useEffect(() => {
    if (contractScaffoldForm.consultant_email) return;
    if (!orderedConsultants.length) return;
    setContractScaffoldForm((prev) => ({ ...prev, consultant_email: orderedConsultants[0].email }));
  }, [contractScaffoldForm.consultant_email, orderedConsultants]);

  useEffect(() => {
    if (profileScaffoldForm.consultant_email) return;
    if (!orderedConsultants.length) return;
    setProfileScaffoldForm((prev) => ({ ...prev, consultant_email: orderedConsultants[0].email }));
  }, [orderedConsultants, profileScaffoldForm.consultant_email]);

  const orderedCoaches = useMemo(() => {
    const rank = (name) => {
      const idx = CONSULTANT_PRIORITY_ORDER.indexOf(String(name || '').toLowerCase());
      return idx === -1 ? 999 : idx;
    };

    const inferredCoachByEmail = new Map();

    const addCoachCandidate = (row) => {
      const email = String(row?.email || '').trim().toLowerCase();
      if (!email) return;
      const existing = inferredCoachByEmail.get(email);
      const rawName = String(row?.name || '').trim();
      const name = !rawName || rawName.includes('@') ? deriveDisplayNameFromEmail(email) : rawName;
      if (!existing) {
        inferredCoachByEmail.set(email, { name, email });
        return;
      }
      if (!existing.name && name) {
        inferredCoachByEmail.set(email, { ...existing, name });
      }
    };

    coaches.forEach(addCoachCandidate);
    consultants.forEach(addCoachCandidate);
    coachingEngagements.forEach((engagement) => {
      addCoachCandidate({
        email: engagement?.coach_email,
        name: '',
      });
    });
    DEFAULT_COACH_ROSTER.forEach((coach) => {
      addCoachCandidate(coach);
    });

    return Array.from(inferredCoachByEmail.values()).sort((a, b) => {
      const byRank = rank(a.name) - rank(b.name);
      if (byRank !== 0) return byRank;
      return String(a.name || a.email || '').localeCompare(String(b.name || b.email || ''));
    });
  }, [coaches, consultants, coachingEngagements]);

  const coachNameByEmail = useMemo(() => {
    const map = {};
    orderedCoaches.forEach((coach) => {
      if (!coach?.email) return;
      map[String(coach.email).trim().toLowerCase()] = String(coach.name || coach.email).trim();
    });
    return map;
  }, [orderedCoaches]);

  const coachLookupOptions = useMemo(
    () =>
      orderedCoaches.map((coach) => ({
        email: String(coach.email || '').trim(),
        emailLower: String(coach.email || '').trim().toLowerCase(),
        name: String(coach.name || coach.email || '').trim(),
        nameLower: String(coach.name || coach.email || '').trim().toLowerCase(),
      })),
    [orderedCoaches]
  );

  const personNameByEmail = useMemo(
    () => ({ ...consultantNameByEmail, ...coachNameByEmail }),
    [coachNameByEmail, consultantNameByEmail]
  );

  function displayNameFromEmail(email) {
    const normalized = String(email || '').trim().toLowerCase();
    if (!normalized) return '';
    const knownName = personNameByEmail[normalized];
    if (knownName) return knownName;

    const localPart = normalized.split('@')[0] || normalized;
    return localPart
      .split(/[._-]+/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }

  function resolveCoachInput(rawValue) {
    const normalized = String(rawValue || '').trim().toLowerCase();
    if (!normalized) return '';

    // Allow brand-new coaches to be entered by email immediately.
    if (normalized.includes('@')) return normalized;

    const exact = coachLookupOptions.find(
      (coach) =>
        coach.emailLower === normalized ||
        coach.nameLower === normalized ||
        `${coach.nameLower} (${coach.emailLower})` === normalized
    );
    if (exact?.email) return exact.email;

    const startsWithMatches = coachLookupOptions.filter(
      (coach) => coach.nameLower.startsWith(normalized) || coach.emailLower.startsWith(normalized)
    );
    if (startsWithMatches.length === 1) return startsWithMatches[0].email;

    const includesMatches = coachLookupOptions.filter(
      (coach) => coach.nameLower.includes(normalized) || coach.emailLower.includes(normalized)
    );
    if (includesMatches.length === 1) return includesMatches[0].email;

    return '';
  }

  function onCoachingBatchFieldChange(rowIndex, field, value) {
    setCoachingBatchRows((prev) => {
      const next = [...prev];
      const current = next[rowIndex] || createEmptyCoachingBatchRow();
      next[rowIndex] = { ...current, [field]: value };
      if (field === 'coach_input') {
        next[rowIndex].coach_email = resolveCoachInput(value);
      }
      return next;
    });
  }

  function onAddCoachingBatchRow() {
    setCoachingBatchRows((prev) => {
      const lastRow = prev[prev.length - 1] || createEmptyCoachingBatchRow();
      return [
        ...prev,
        {
          ...createEmptyCoachingBatchRow(),
          client_org: String(lastRow.client_org || '').trim(),
          coach_input: String(lastRow.coach_input || '').trim(),
          coach_email: String(lastRow.coach_email || '').trim(),
          total_sessions: String(lastRow.total_sessions || '').trim(),
          lcp_debrief_enabled: Boolean(lastRow.lcp_debrief_enabled),
          lcp_debrief_total_sessions: String(lastRow.lcp_debrief_total_sessions || '0').trim(),
        },
      ];
    });
  }

  function onRemoveCoachingBatchRow(rowIndex) {
    setCoachingBatchRows((prev) => {
      if (prev.length <= 1) return [createEmptyCoachingBatchRow()];
      return prev.filter((_, idx) => idx !== rowIndex);
    });
  }

  function onResetCoachingBatchRows() {
    setCoachingBatchRows([createEmptyCoachingBatchRow()]);
    if (typeof window !== 'undefined') {
      localStorage.removeItem(COACHING_BATCH_DRAFT_STORAGE_KEY);
    }
    setCoachingStatus('Batch draft cleared.');
  }

  async function onSubmitCoachingBatch(event) {
    event.preventDefault();
    setIsSubmittingCoachingBatch(true);
    setCoachingStatus('Uploading coaching batch...');

    try {
      const cleanRows = coachingBatchRows
        .map((row, sourceIndex) => {
          const rawCoachInput = String(row.coach_input || '').trim().toLowerCase();
          const resolvedCoachEmail = row.coach_email || resolveCoachInput(rawCoachInput);
          return {
            name: String(row.name || '').trim(),
            job_title: String(row.job_title || '').trim(),
            client_org: String(row.client_org || '').trim(),
            coach_email: String(resolvedCoachEmail || '').trim(),
            coach_input: rawCoachInput,
            total_sessions: Number(row.total_sessions || 0),
            sessions_used: Number(row.sessions_used || 0),
            lcp_debrief_enabled: Boolean(row.lcp_debrief_enabled),
            lcp_debrief_total_sessions: Number(row.lcp_debrief_total_sessions || 0),
            lcp_debrief_sessions_used: Number(row.lcp_debrief_sessions_used || 0),
            source_index: sourceIndex,
          };
        })
        .filter((row) => row.name || row.client_org || row.coach_email);

      if (!cleanRows.length) {
        setCoachingStatus('Add at least one coaching row before uploading.');
        return;
      }

      const validRows = cleanRows.filter(
        (row) =>
          row.name &&
          row.client_org &&
          row.coach_email &&
          row.total_sessions > 0 &&
          row.sessions_used >= 0 &&
          row.sessions_used <= row.total_sessions &&
          (!row.lcp_debrief_enabled ||
            (row.lcp_debrief_total_sessions >= 0 &&
              row.lcp_debrief_sessions_used >= 0 &&
              row.lcp_debrief_sessions_used <= row.lcp_debrief_total_sessions))
      );

      if (!validRows.length) {
        setCoachingStatus('No complete rows to save yet. Fill coachee, client, coach, and sessions first.');
        return;
      }

      const saveWarnings = [];
      const successfulSourceIndexes = new Set();
      let failedSaveCount = 0;
      let createdRowList = [];

      try {
        const createdRows = await bulkCreateCoachingEngagements({
          items: validRows.map(({ source_index, coach_input, ...payload }) => payload),
        });
        createdRowList = Array.isArray(createdRows) ? createdRows : [];
        validRows.forEach((row) => successfulSourceIndexes.add(row.source_index));
      } catch (bulkError) {
        for (const row of validRows) {
          try {
            const { source_index, coach_input, ...payload } = row;
            const created = await createCoachingEngagement(payload);
            createdRowList.push(created);
            successfulSourceIndexes.add(source_index);
          } catch (rowError) {
            failedSaveCount += 1;
          }
        }

        if (!createdRowList.length) {
          throw bulkError;
        }

        saveWarnings.push('Bulk upload failed; fallback row-by-row save used.');
      }

      if (createdRowList.length) {
        setCoachingEngagements((prev) => {
          const next = [...prev, ...createdRowList];
          const seen = new Set();
          return next.filter((row) => {
            const idKey = String(row?.id || '').trim().toLowerCase();
            if (idKey && seen.has(idKey)) return false;
            if (idKey) seen.add(idKey);
            return true;
          });
        });
      }

      const successfulRows = validRows.filter((row) => successfulSourceIndexes.has(row.source_index));

      const existingCoachByEmail = new Map(
        coaches
          .filter((row) => row?.email)
          .map((row) => [String(row.email).trim().toLowerCase(), String(row.name || '').trim()])
      );
      const newCoachRows = [];
      successfulRows.forEach((row) => {
        const email = String(row.coach_email || '').trim().toLowerCase();
        if (!email || existingCoachByEmail.has(email)) return;
        const derivedName =
          String(row.coach_input || '').includes('@') || !String(row.coach_input || '').trim()
            ? displayNameFromEmail(email)
            : String(row.coach_input || '').trim();
        existingCoachByEmail.set(email, derivedName);
        newCoachRows.push({ name: derivedName, email });
      });

      if (newCoachRows.length) {
        const mergedCoaches = [
          ...coaches,
          ...newCoachRows,
        ].filter((row, idx, arr) => {
          const email = String(row?.email || '').trim().toLowerCase();
          return email && arr.findIndex((candidate) => String(candidate?.email || '').trim().toLowerCase() === email) === idx;
        });

        try {
          await updateLookupCoaches({ items: mergedCoaches });
          setCoaches(mergedCoaches);
        } catch (error) {
          saveWarnings.push('Coach lookup sync failed');
        }
      }

      const knownClientNames = new Set(
        clientPrograms.map((row) => String(row.client_name || '').trim().toLowerCase()).filter(Boolean)
      );
      const newClientProgramRows = [];
      successfulRows.forEach((row) => {
        const clientName = String(row.client_org || '').trim();
        const clientKey = clientName.toLowerCase();
        if (!clientName || knownClientNames.has(clientKey)) return;
        knownClientNames.add(clientKey);
        newClientProgramRows.push({ client_name: clientName, program_name: '' });
      });

      if (newClientProgramRows.length) {
        const mergedClientPrograms = [...clientPrograms, ...newClientProgramRows];
        try {
          await updateLookupClientPrograms({
            items: mergedClientPrograms,
          });
          setClientPrograms(mergedClientPrograms);
        } catch (error) {
          saveWarnings.push('Client lookup sync failed');
        }
      }

      const remainingDraftRows = coachingBatchRows.filter((_, rowIndex) => !successfulSourceIndexes.has(rowIndex));
      setCoachingBatchRows(remainingDraftRows.length ? remainingDraftRows : [createEmptyCoachingBatchRow()]);

      if (!remainingDraftRows.length && typeof window !== 'undefined') {
        localStorage.removeItem(COACHING_BATCH_DRAFT_STORAGE_KEY);
      }

      const skippedCount = cleanRows.length - validRows.length;
      const keptDraftCount = remainingDraftRows.filter((row) => {
        const hasText =
          String(row.name || '').trim() ||
          String(row.client_org || '').trim() ||
          String(row.coach_input || '').trim() ||
          String(row.coach_email || '').trim();
        return Boolean(hasText) || Number(row.total_sessions || 0) > 0 || Number(row.sessions_used || 0) > 0;
      }).length;
      setCoachingStatus(
        [
          keptDraftCount > 0 || failedSaveCount > 0 || skippedCount > 0
            ? `Saved ${createdRowList.length} row(s). Kept ${keptDraftCount} row(s) in draft.`
            : `Batch upload complete: ${createdRowList.length} coaching engagement(s) saved. Added ${newCoachRows.length} new coach lookup(s) and ${newClientProgramRows.length} new client lookup(s).`,
          saveWarnings.length ? `Warning: ${saveWarnings.join('; ')}.` : '',
        ]
          .filter(Boolean)
          .join(' ')
      );

      try {
        await refresh();
      } catch (error) {
        setCoachingStatus((prev) =>
          [prev, 'Saved successfully, but automatic refresh failed. Please refresh once to pull latest totals.']
            .filter(Boolean)
            .join(' ')
        );
      }
    } catch (error) {
      setCoachingStatus(error.message || 'Batch coaching upload failed.');
    } finally {
      setIsSubmittingCoachingBatch(false);
    }
  }

  async function onDeleteAdminEngagement(engagement) {
    const key = String(engagement.id);
    const label = String(engagement.name || engagement.id || 'this coachee').trim();
    const confirmDelete =
      typeof window === 'undefined'
        ? true
        : window.confirm(`Delete ${label}? This also removes linked coaching sessions.`);
    if (!confirmDelete) return;

    setDeletingAdminEngagementId(key);
    try {
      await deleteCoachingEngagement(engagement.id);
      setStatus(`Deleted coachee record: ${label}.`);
      setAdminEngagementDraftById((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
      setSelectedAdminEngagementId((prev) => (prev === key ? '' : prev));
      await refresh();
    } catch (error) {
      setStatus(error.message || 'Failed to delete coachee record.');
    } finally {
      setDeletingAdminEngagementId('');
    }
  }

  const visibleScreenTabs = useMemo(() => {
    const roleFiltered = SCREEN_TABS.filter((tab) => {
      if (!isAdminSession && tab.id === 'admin-console') return false;
      if (isConsultantSession && tab.id === 'create-project') return false;
      return true;
    });
    if (isClientViewerSession) {
      return roleFiltered.filter((tab) => CLIENT_REPORTS_CORE_TAB_IDS.has(tab.id));
    }
    if (isCoachOnlySession) {
      return roleFiltered.filter((tab) => tab.id === 'session-mode' || tab.id === 'help' || tab.id === 'coaching-module');
    }
    if (isConsultantSession) {
      return roleFiltered.filter(
        (tab) => tab.id === 'session-mode' || tab.id === 'help' || tab.id === 'submit-expense' || tab.id === 'coaching-module'
      );
    }
    if (isSimplifiedAdminDemoView) {
      return roleFiltered.filter((tab) => DEMO_CORE_TAB_IDS.has(tab.id));
    }
    return roleFiltered;
  }, [isAdminSession, isClientViewerSession, isCoachOnlySession, isConsultantSession, isSimplifiedAdminDemoView]);

  const activeQuickHelp = useMemo(
    () => QUICK_HELP_BY_TAB_ID[activeScreenTabId] || DEFAULT_QUICK_HELP,
    [activeScreenTabId]
  );

  const isTabbedLayout = layoutMode === 'tabs';

  const sectionVisibilityStyle = (sectionId) =>
    isTabbedLayout && activeScreenTabId !== sectionId ? { display: 'none' } : undefined;

  const filteredAdminEngagements = useMemo(() => {
    const queryName = String(adminEngagementSearch.name || '').trim().toLowerCase();
    const queryClient = String(adminEngagementSearch.client_org || '').trim().toLowerCase();
    const queryCoach = String(adminEngagementSearch.coach_email || '').trim().toLowerCase();

    const filtered = coachingEngagements.filter((engagement) => {
      const name = String(engagement.name || '').toLowerCase();
      const client = String(engagement.client_org || '').toLowerCase();
      const coach = String(engagement.coach_email || '').toLowerCase();
      const coachName = String(coachNameByEmail[coach] || '').toLowerCase();
      if (queryName && !name.includes(queryName)) return false;
      if (queryClient && !client.includes(queryClient)) return false;
      if (queryCoach && !coach.includes(queryCoach) && !coachName.includes(queryCoach)) return false;
      return true;
    });

    const directionMult = adminEngagementSort.direction === 'desc' ? -1 : 1;
    const sortKey = adminEngagementSort.key;
    return [...filtered].sort((a, b) => {
      const aValue = String(a[sortKey] || '').trim().toLowerCase();
      const bValue = String(b[sortKey] || '').trim().toLowerCase();
      return aValue.localeCompare(bValue) * directionMult;
    });
  }, [adminEngagementSearch, adminEngagementSort.direction, adminEngagementSort.key, coachNameByEmail, coachingEngagements]);

  const selectedAdminEngagement = useMemo(
    () => coachingEngagements.find((row) => String(row.id) === String(selectedAdminEngagementId)) || null,
    [coachingEngagements, selectedAdminEngagementId]
  );

  const adminSessionQuickMatches = useMemo(() => {
    const queryCoach = String(adminSessionQuickSearch.coach || '').trim().toLowerCase();
    const queryConsultant = String(adminSessionQuickSearch.consultant || '').trim().toLowerCase();
    const queryClient = String(adminSessionQuickSearch.client || '').trim().toLowerCase();

    return [...coachingEngagements]
      .filter((engagement) => {
        const coachEmail = String(engagement.coach_email || '').trim().toLowerCase();
        const coachName = String(coachNameByEmail[coachEmail] || '').trim().toLowerCase();
        const consultantName = String(engagement.name || '').trim().toLowerCase();
        const clientName = String(engagement.client_org || '').trim().toLowerCase();
        if (queryCoach && !coachEmail.includes(queryCoach) && !coachName.includes(queryCoach)) return false;
        if (queryConsultant && !consultantName.includes(queryConsultant)) return false;
        if (queryClient && !clientName.includes(queryClient)) return false;
        return true;
      })
      .sort((a, b) => {
        const byName = String(a.name || '').localeCompare(String(b.name || ''));
        if (byName !== 0) return byName;
        return String(a.client_org || '').localeCompare(String(b.client_org || ''));
      });
  }, [adminSessionQuickSearch, coachNameByEmail, coachingEngagements]);

  const selectedAdminQuickEngagement = useMemo(
    () =>
      coachingEngagements.find(
        (engagement) => String(engagement.id) === String(adminSessionQuickForm.engagement_id)
      ) || null,
    [adminSessionQuickForm.engagement_id, coachingEngagements]
  );

  const selectedAdminQuickLcpEnabled = Boolean(selectedAdminQuickEngagement?.lcp_debrief_enabled);

  const coachingEngagementById = useMemo(() => {
    const map = {};
    coachingEngagements.forEach((row) => {
      map[String(row.id)] = row;
    });
    return map;
  }, [coachingEngagements]);

  const sessionsByEngagementId = useMemo(() => {
    const map = {};
    coachingSessions.forEach((session) => {
      const key = String(session.engagement_id || '');
      if (!key) return;
      if (!map[key]) map[key] = [];
      map[key].push(session);
    });
    Object.keys(map).forEach((key) => {
      map[key] = map[key].sort((a, b) => String(a.session_date || '').localeCompare(String(b.session_date || '')));
    });
    return map;
  }, [coachingSessions]);

  const adminQuickSessionDates = useMemo(
    () => parseIsoDateList(adminSessionQuickForm.session_dates_text),
    [adminSessionQuickForm.session_dates_text]
  );

  const adminQuickRecentSessions = useMemo(() => {
    if (!selectedAdminQuickEngagement) return [];
    return [...(sessionsByEngagementId[String(selectedAdminQuickEngagement.id)] || [])]
      .sort((a, b) => String(b.session_date || '').localeCompare(String(a.session_date || '')))
      .slice(0, 6);
  }, [selectedAdminQuickEngagement, sessionsByEngagementId]);

  const filteredAdminSessions = useMemo(() => {
    const queryCoach = String(adminSessionQuickSearch.coach || '').trim().toLowerCase();
    const queryConsultant = String(adminSessionQuickSearch.consultant || '').trim().toLowerCase();
    const queryClient = String(adminSessionQuickSearch.client || '').trim().toLowerCase();

    return coachingSessions.filter((session) => {
      const engagement = coachingEngagementById[String(session.engagement_id)] || {};
      const coachEmail = String(engagement.coach_email || '').trim().toLowerCase();
      const coachName = String(coachNameByEmail[coachEmail] || '').trim().toLowerCase();
      const consultantName = String(engagement.name || '').trim().toLowerCase();
      const clientName = String(engagement.client_org || '').trim().toLowerCase();
      if (queryCoach && !coachEmail.includes(queryCoach) && !coachName.includes(queryCoach)) return false;
      if (queryConsultant && !consultantName.includes(queryConsultant)) return false;
      if (queryClient && !clientName.includes(queryClient)) return false;
      return true;
    });
  }, [adminSessionQuickSearch, coachNameByEmail, coachingEngagementById, coachingSessions]);

  const adminSessionEditedRows = useMemo(
    () => filteredAdminSessions.filter((session) => Boolean(adminSessionDraftById[String(session.id)])).length,
    [adminSessionDraftById, filteredAdminSessions]
  );

  useEffect(() => {
    const currentId = String(adminSessionQuickForm.engagement_id || '');
    const stillVisible = adminSessionQuickMatches.some((engagement) => String(engagement.id) === currentId);
    if (stillVisible) return;
    setAdminSessionQuickForm((prev) => ({
      ...prev,
      engagement_id: String(adminSessionQuickMatches[0]?.id || ''),
    }));
  }, [adminSessionQuickForm.engagement_id, adminSessionQuickMatches]);

  const categoryOptions = useMemo(
    () =>
      expenseForm.submitted_by_role === 'consultant'
        ? CONSULTANT_CATEGORY_OPTIONS
        : ADMIN_CATEGORY_OPTIONS,
    [expenseForm.submitted_by_role]
  );

  const programOptions = useMemo(
    () =>
      clientPrograms
        .filter((row) => row.client_name === tripForm.client_name)
        .map((row) => row.program_name),
    [clientPrograms, tripForm.client_name]
  );

  const allProgramOptions = useMemo(
    () => [...new Set(clientPrograms.map((row) => row.program_name))],
    [clientPrograms]
  );

  const adminCountryOptions = useMemo(() => {
    const fromRates = atoRates.map((row) => String(row.country || '').trim()).filter(Boolean);
    const fromTrips = trips.map((row) => String(row.destination_country || '').trim()).filter(Boolean);
    return Array.from(new Set([...fromRates, ...fromTrips])).sort((a, b) => a.localeCompare(b));
  }, [atoRates, trips]);

  const dashboardLogoCandidates = useMemo(() => {
    if (typeof window === 'undefined') return [];

    const browserHost = window.location.hostname || '127.0.0.1';
    const sameOrigin = window.location.origin;
    const overrideBase = (localStorage.getItem('adapsys_api_base') || '').trim();
    const baseCandidates = [
      overrideBase,
      `http://${browserHost}:8000`,
      'http://127.0.0.1:8000',
      'http://localhost:8000',
    ].filter(Boolean);

    const remoteCandidates = baseCandidates.flatMap((base) => [
      `${base}/reports/brand-logo?context=portal`,
      `${base}/reports/brand-logo?context=report`,
      `${base}/reports/brand-logo`,
    ]);
    const staticCandidates = [
      `${sameOrigin}/icons/icon-512.svg`,
      `${sameOrigin}/icons/icon-192.svg`,
    ];

    return Array.from(new Set([...remoteCandidates, ...staticCandidates]));
  }, []);

  const dashboardLogoSrc = dashboardLogoCandidates[dashboardLogoIndex] || '';

  const expenseTripOptions = useMemo(() => {
    if (!isConsultantSession || !sessionEmail) return trips;
    const normalizedSessionEmail = normalizeEmailIdentity(sessionEmail);
    return trips.filter((trip) => {
      const roster = [trip.consultant_email, ...(trip.assigned_consultants || [])]
        .filter(Boolean)
        .map((email) => normalizeEmailIdentity(email));
      return roster.includes(normalizedSessionEmail);
    });
  }, [isConsultantSession, sessionEmail, trips]);

  const expenseContextClientOptions = useMemo(
    () => Array.from(new Set(trips.map((trip) => String(trip.client_name || '').trim()).filter(Boolean))).sort(),
    [trips]
  );

  const submitExpenseConsultantOptions = useMemo(
    () =>
      [...orderedConsultants].sort((a, b) => {
        const byName = String(a.name || '').localeCompare(String(b.name || ''));
        if (byName !== 0) return byName;
        return String(a.email || '').localeCompare(String(b.email || ''));
      }),
    [orderedConsultants]
  );

  const filteredExpenseTripOptions = useMemo(() => {
    return expenseTripOptions
      .filter((trip) => {
        if (expenseContextClientFilter) {
          const tripClient = String(trip.client_name || '').trim();
          if (tripClient !== String(expenseContextClientFilter || '').trim()) return false;
        }
        if (expenseContextConsultantFilter) {
          const roster = [trip.consultant_email, ...(trip.assigned_consultants || [])]
            .filter(Boolean)
            .map((email) => String(email).toLowerCase());
          if (!roster.includes(String(expenseContextConsultantFilter || '').toLowerCase())) return false;
        }
        return true;
      })
      .sort((a, b) => String(a.name || '').localeCompare(String(b.name || '')));
  }, [expenseContextClientFilter, expenseContextConsultantFilter, expenseTripOptions]);

  useEffect(() => {
    if (!isConsultantSession) return;
    const normalized = normalizeEmailIdentity(sessionEmail || '');
    if (!normalized) return;
    setExpenseContextConsultantFilter(normalized);
    setExpenseForm((prev) => {
      if (normalizeEmailIdentity(prev.submitted_by_email) === normalized) return prev;
      return {
        ...prev,
        submitted_by_email: normalized,
      };
    });
  }, [isConsultantSession, sessionEmail]);

  const selectedExpenseTrip = useMemo(
    () => trips.find((trip) => String(trip.id) === String(expenseForm.trip_id)) || null,
    [expenseForm.trip_id, trips]
  );


  useEffect(() => {
    if (!expenseForm.trip_id) return;
    const stillVisible = filteredExpenseTripOptions.some(
      (trip) => String(trip.id) === String(expenseForm.trip_id)
    );
    if (stillVisible) return;
    setExpenseForm((prev) => ({
      ...prev,
      trip_id: '',
      submitted_by_email: '',
    }));
  }, [expenseForm.trip_id, filteredExpenseTripOptions]);

  const expenseReportClientOptions = useMemo(
    () => Array.from(new Set(trips.map((trip) => String(trip.client_name || '').trim()).filter(Boolean))).sort(),
    [trips]
  );

  const expenseReportProjectOptions = useMemo(() => {
    const scopedTrips = !selectedReportClient
      ? trips
      : trips.filter((trip) => String(trip.client_name || '').trim() === String(selectedReportClient || '').trim());
    return [...scopedTrips].sort((a, b) => String(a.name || '').localeCompare(String(b.name || '')));
  }, [selectedReportClient, trips]);

  useEffect(() => {
    const hasSelectedProject = expenseReportProjectOptions.some(
      (trip) => String(trip.id) === String(selectedReportTripId)
    );
    if (hasSelectedProject) return;
    setSelectedReportTripId(String(expenseReportProjectOptions[0]?.id || ''));
  }, [expenseReportProjectOptions, selectedReportTripId]);

  const projectConsultantOptions = useMemo(() => {
    if (!selectedExpenseTrip) return [];
    const roster = Array.from(
      new Set(
        [selectedExpenseTrip.consultant_email, ...(selectedExpenseTrip.assigned_consultants || [])]
          .filter(Boolean)
          .map((email) => String(email).toLowerCase())
      )
    );

    return roster
      .map((email) => {
        const name = consultantNameByEmail[email];
        return {
          email,
          label: name || email,
        };
      })
      .sort((a, b) => a.label.localeCompare(b.label));
  }, [consultantNameByEmail, selectedExpenseTrip]);

  const coachingReportsReady = coachingEngagements.length > 0;
  const expenseReportsReady = expenseReportProjectOptions.length > 0;
  const isPerDiemCategory = expenseForm.category === 'per_diem';
  const isBulkPerDiemMode =
    isPerDiemCategory && expenseForm.per_diem_bulk_mode;

  const expenseValidation = useMemo(() => {
    const amountValue = Number(expenseForm.amount_local);
    const exchangeRateValue = Number(expenseForm.exchange_rate);
    const needsFlightRoutes = expenseForm.category === 'flights' || expenseForm.category === 'flight';
    const missing = {
      trip: !expenseForm.trip_id,
      consultant: !expenseForm.submitted_by_email,
      flightFrom: needsFlightRoutes && !expenseForm.flight_route_from,
      flightTo: needsFlightRoutes && !expenseForm.flight_route_to,
      date: !isBulkPerDiemMode && !expenseForm.expense_date,
      amount: isPerDiemCategory ? false : !(Number.isFinite(amountValue) && amountValue > 0),
      exchangeRate:
        !isPerDiemCategory &&
        expenseForm.currency_local !== 'AUD' &&
        !(Number.isFinite(exchangeRateValue) && exchangeRateValue > 0),
      perDiemStart: isPerDiemCategory && isBulkPerDiemMode && !expenseForm.per_diem_start_date,
      perDiemEnd: isPerDiemCategory && isBulkPerDiemMode && !expenseForm.per_diem_end_date,
      receipt:
        isConsultantSession &&
        !isPerDiemCategory &&
        !expenseForm.no_receipt &&
        !String(expenseForm.receipt_url || '').trim() &&
        !String(expenseForm.receipt_thumb_url || '').trim(),
    };

    const orderedMissingKeys = [
      'trip',
      'consultant',
      'flightFrom',
      'flightTo',
      'date',
      'perDiemStart',
      'perDiemEnd',
      'amount',
      'exchangeRate',
      'receipt',
    ].filter((key) => missing[key]);

    const labelByKey = {
      trip: 'Activity',
      consultant: 'Consultant',
      flightFrom: 'Flight from',
      flightTo: 'Flight to',
      date: 'Date',
      perDiemStart: 'Per diem start date',
      perDiemEnd: 'Per diem end date',
      amount: 'Amount',
      exchangeRate: 'Exchange rate',
      receipt: 'Receipt evidence',
    };

    return {
      missing,
      orderedMissingKeys,
      orderedMissingLabels: orderedMissingKeys.map((key) => labelByKey[key]),
    };
  }, [expenseForm, isBulkPerDiemMode, isConsultantSession, isPerDiemCategory]);

  const expenseNextStep = useMemo(() => {
    const claimKeys = new Set(['flightFrom', 'flightTo', 'date', 'perDiemStart', 'perDiemEnd', 'amount', 'exchangeRate']);
    if (!expenseForm.trip_id || (!isConsultantSession && !expenseForm.submitted_by_email)) {
      return {
        id: 'expense-step-context',
        label: 'Complete Step 1: Context',
      };
    }
    if (expenseValidation.orderedMissingKeys.some((key) => claimKeys.has(key))) {
      return {
        id: 'expense-step-claim',
        label: `Complete Step 2: ${expenseValidation.orderedMissingLabels[0] || 'Claim details'}`,
      };
    }
    if (expenseValidation.orderedMissingKeys.includes('receipt')) {
      return {
        id: 'expense-step-receipt',
        label: 'Complete Step 3: Receipt evidence',
      };
    }
    return {
      id: 'expense-step-submit',
      label: 'Step 4: Review and submit',
    };
  }, [
    expenseForm.submitted_by_email,
    expenseForm.trip_id,
    expenseValidation.orderedMissingKeys,
    expenseValidation.orderedMissingLabels,
    isConsultantSession,
  ]);

  const expenseStepState = useMemo(() => {
    const claimKeys = ['flightFrom', 'flightTo', 'date', 'perDiemStart', 'perDiemEnd', 'amount', 'exchangeRate'];
    const contextComplete = Boolean(expenseForm.trip_id) && (isConsultantSession || Boolean(expenseForm.submitted_by_email));
    const claimComplete = claimKeys.every((key) => !expenseValidation.missing[key]);
    const receiptComplete = !expenseValidation.missing.receipt;
    const submitComplete = contextComplete && claimComplete && receiptComplete;
    return {
      context: contextComplete,
      claim: claimComplete,
      receipt: receiptComplete,
      submit: submitComplete,
    };
  }, [expenseForm.submitted_by_email, expenseForm.trip_id, expenseValidation.missing, isConsultantSession]);

  const expenseCompletedStepCount = useMemo(
    () => Object.values(expenseStepState).filter(Boolean).length,
    [expenseStepState]
  );

  const coachingNextStep = useMemo(() => {
    if (isConsultantSession) {
      if (!coachingSessionForm.engagement_id || !coachingSessionForm.session_date) {
        return {
          id: 'coaching-session-log',
          label: 'Log the next consultant session',
        };
      }
      return {
        id: 'coaching-recent-edit',
        label: 'Review or update recent sessions',
      };
    }

    if (!coachingEngagements.length) {
      return {
        id: 'coaching-batch-entry',
        label: 'Start with Batch Setup',
      };
    }
    if (!coachingSessions.length) {
      return {
        id: 'coaching-admin-sessions',
        label: 'Open Admin Sessions to add first session dates',
      };
    }
    return {
      id: 'coaching-recent-edit',
      label: 'Review/edit recent sessions',
    };
  }, [
    coachingEngagements.length,
    coachingSessionForm.engagement_id,
    coachingSessionForm.session_date,
    coachingSessions.length,
    isConsultantSession,
  ]);

  const flightLocationOptions = useMemo(() => {
    const dynamicLocations = [
      selectedExpenseTrip?.destination_city,
      tripForm.destination_city,
    ]
      .map((value) => toAirportOption(value))
      .filter(Boolean);
    return Array.from(new Set([...FLIGHT_LOCATION_OPTIONS, ...dynamicLocations]));
  }, [selectedExpenseTrip, tripForm.destination_city, tripForm.destination_country]);

  const sortedFlightLocationOptions = useMemo(
    () => [...flightLocationOptions].sort((a, b) => String(a || '').localeCompare(String(b || ''))),
    [flightLocationOptions]
  );

  const sortedExpenseDescriptionOptions = useMemo(
    () => [...EXPENSE_DESCRIPTION_OPTIONS].sort((a, b) => a.localeCompare(b)),
    []
  );

  const sortedExpenseSupplierOptions = useMemo(
    () => [...EXPENSE_SUPPLIER_OPTIONS].sort((a, b) => a.localeCompare(b)),
    []
  );

  const sortedReceiptKindOptions = useMemo(
    () => [...EXPENSE_RECEIPT_KIND_OPTIONS].sort((a, b) => formatTokenLabel(a).localeCompare(formatTokenLabel(b))),
    []
  );

  const sortedStandardDescriptorActivityOptions = useMemo(
    () => [...STANDARD_DESCRIPTOR_ACTIVITY_OPTIONS].sort((a, b) => formatTokenLabel(a).localeCompare(formatTokenLabel(b))),
    []
  );

  const descriptorLocationOptions = useMemo(() => {
    const seed = ['Home', 'Office', 'Airport', ...(flightLocationOptions || [])]
      .map((value) => String(value || '').trim())
      .filter(Boolean);
    return Array.from(new Set(seed)).sort((a, b) => a.localeCompare(b));
  }, [flightLocationOptions]);

  const descriptorFromToOptions = useMemo(() => {
    const category = String(expenseForm.category || '').trim().toLowerCase();
    if (['flight', 'flights'].includes(category)) {
      return sortedFlightLocationOptions;
    }
    if (['uber'].includes(category)) {
      return Array.from(new Set([...EXPENSE_ROUTE_PRESET_OPTIONS, ...descriptorLocationOptions]))
        .sort((a, b) => String(a || '').localeCompare(String(b || '')));
    }
    return descriptorLocationOptions;
  }, [descriptorLocationOptions, expenseForm.category, sortedFlightLocationOptions]);

  const standardDescriptorPreview = useMemo(() => {
    const person = displayNameFromEmail(expenseForm.submitted_by_email) || 'Consultant';
    const projectName = String(selectedExpenseTrip?.name || '').trim() || 'selected activity';
    const activity = String(expenseForm.descriptor_activity || '').trim();
    const fromPointRaw =
      expenseForm.category === 'flights' || expenseForm.category === 'flight'
        ? String(expenseForm.flight_route_from || '').trim()
        : String(expenseForm.descriptor_from || '').trim();
    const toPointRaw =
      expenseForm.category === 'flights' || expenseForm.category === 'flight'
        ? String(expenseForm.flight_route_to || '').trim()
        : String(expenseForm.descriptor_to || '').trim();
    const fromPoint = TRAVEL_POINT_CODE_MAP[fromPointRaw] || fromPointRaw;
    const toPoint = TRAVEL_POINT_CODE_MAP[toPointRaw] || toPointRaw;
    const activitySuffix = activity ? ` ${activity}` : '';

    if (fromPoint && toPoint) {
      if (expenseForm.category === 'flights' || expenseForm.category === 'flight') {
        return `${person} flight ${fromPoint} - ${toPoint} for ${projectName}${activitySuffix}`;
      }
      return `${person} ${formatTokenLabel(expenseForm.category)} from ${fromPointRaw} to ${toPointRaw} for ${projectName}${activitySuffix}`;
    }

    return `${person} ${formatTokenLabel(expenseForm.category)} for ${projectName}${activitySuffix}`;
  }, [
    expenseForm.category,
    expenseForm.descriptor_activity,
    expenseForm.descriptor_from,
    expenseForm.descriptor_to,
    expenseForm.flight_route_from,
    expenseForm.flight_route_to,
    expenseForm.submitted_by_email,
    selectedExpenseTrip?.name,
  ]);

  const reimbursableDraftLocal = useMemo(() => {
    const raw = String(expenseForm.reimbursable_amount_local || '').trim();
    if (!raw) return null;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  }, [expenseForm.reimbursable_amount_local]);

  const nonReimbursableDraftLocal = useMemo(() => {
    const total = Number(expenseForm.amount_local || 0);
    if (!Number.isFinite(total) || total <= 0) return 0;
    const reimbursable = reimbursableDraftLocal === null ? total : reimbursableDraftLocal;
    return Math.max(total - reimbursable, 0);
  }, [expenseForm.amount_local, reimbursableDraftLocal]);

  useEffect(() => {
    if (isConsultantSession) return;
    if (expenseForm.category === 'per_diem') return;
    if (!expenseForm.reimbursement_override_enabled) return;
    if (String(expenseForm.reimbursable_percent || '') === 'custom') return;

    const percentValue = Number(expenseForm.reimbursable_percent || '100');
    const totalValue = Number(expenseForm.amount_local || 0);
    if (!Number.isFinite(percentValue) || !Number.isFinite(totalValue) || totalValue < 0) return;

    const nextReimbursable = totalValue > 0 ? ((totalValue * percentValue) / 100).toFixed(2) : '';
    if (String(expenseForm.reimbursable_amount_local || '') === String(nextReimbursable)) return;
    setExpenseForm((prev) => ({
      ...prev,
      reimbursable_amount_local: nextReimbursable,
    }));
  }, [
    expenseForm.amount_local,
    expenseForm.category,
    expenseForm.reimbursement_override_enabled,
    expenseForm.reimbursable_amount_local,
    expenseForm.reimbursable_percent,
    isConsultantSession,
  ]);

  useEffect(() => {
    setExpenseForm((prev) => {
      if (String(prev.description || '').trim()) return prev;
      return {
        ...prev,
        description: standardDescriptorPreview,
      };
    });
  }, [standardDescriptorPreview]);

  useEffect(() => {
    if (!coachingSessionForm.lcp_debrief) return;
    const handle = setTimeout(() => {
      coachingLcpDateRef.current?.focus?.();
    }, 0);
    return () => clearTimeout(handle);
  }, [coachingSessionForm.lcp_debrief]);

  useEffect(() => {
    if (!adminSessionQuickForm.lcp_debrief) return;
    const handle = setTimeout(() => {
      adminLcpDateRef.current?.focus?.();
    }, 0);
    return () => clearTimeout(handle);
  }, [adminSessionQuickForm.lcp_debrief]);

  const perDiemFinancialYearOptions = useMemo(() => {
    const current = currentFinancialYearLabel();
    const startYear = Number(String(current).slice(0, 4));
    const previous = Number.isInteger(startYear)
      ? formatFinancialYearLabel(startYear - 1)
      : '';
    return [current, previous].filter(Boolean);
  }, []);

  const normalizedSelectedPerDiemFinancialYear = useMemo(
    () => normalizeFinancialYearLabel(selectedPerDiemFinancialYear),
    [selectedPerDiemFinancialYear]
  );

  const atoFinancialYearOptions = useMemo(() => {
    const values = new Set(perDiemFinancialYearOptions);
    atoRates.forEach((rate) => {
      const normalizedYear = normalizeFinancialYearLabel(rate.tax_year);
      if (normalizedYear) values.add(normalizedYear);
    });
    return Array.from(values).sort((a, b) => b.localeCompare(a));
  }, [atoRates, perDiemFinancialYearOptions]);

  const selectedExpenseRate = useMemo(() => {
    if (!selectedExpenseTrip) return null;
    const destinationCountry = selectedExpenseTrip.destination_country;
    const activeCountryRates = atoRates.filter(
      (rate) => rate.country === destinationCountry && rate.active
    );
    if (!activeCountryRates.length) return null;
    return (
      activeCountryRates.find(
        (rate) => normalizeFinancialYearLabel(rate.tax_year) === normalizedSelectedPerDiemFinancialYear
      ) || activeCountryRates[0]
    );
  }, [atoRates, normalizedSelectedPerDiemFinancialYear, selectedExpenseTrip]);

  const coachingEngagementOptions = useMemo(() => {
    if (!isConsultantSession) return coachingEngagements;
    const normalizedSessionEmail = normalizeEmailIdentity(sessionEmail);
    return coachingEngagements.filter(
      (row) => normalizeEmailIdentity(row.coach_email) === normalizedSessionEmail
    );
  }, [coachingEngagements, isConsultantSession, sessionEmail]);

  const activeCoachingClientCount = useMemo(
    () =>
      new Set(
        coachingEngagementOptions
          .map((row) => String(row.client_org || '').trim().toLowerCase())
          .filter(Boolean)
      ).size,
    [coachingEngagementOptions]
  );

  const sortedCoachingEngagementOptions = useMemo(
    () =>
      [...coachingEngagementOptions].sort((a, b) => {
        const aClient = String(a.client_org || '').trim().toLowerCase();
        const bClient = String(b.client_org || '').trim().toLowerCase();
        const byClient = aClient.localeCompare(bClient);
        if (byClient !== 0) return byClient;
        const aName = String(a.name || '').trim().toLowerCase();
        const bName = String(b.name || '').trim().toLowerCase();
        return aName.localeCompare(bName);
      }),
    [coachingEngagementOptions]
  );

  const filteredSessionEngagementOptions = useMemo(() => {
    const queryCoachee = String(coachingSessionEngagementSearch.coachee || '').trim().toLowerCase();
    const queryClient = String(coachingSessionEngagementSearch.client || '').trim().toLowerCase();
    if (!queryCoachee && !queryClient) return sortedCoachingEngagementOptions;
    return sortedCoachingEngagementOptions.filter((engagement) => {
      const coachee = String(engagement.name || '').trim().toLowerCase();
      const client = String(engagement.client_org || '').trim().toLowerCase();
      const coacheePass = !queryCoachee || coachee.includes(queryCoachee);
      const clientPass = !queryClient || client.includes(queryClient);
      return coacheePass && clientPass;
    });
  }, [coachingSessionEngagementSearch, sortedCoachingEngagementOptions]);

  const coachingCoachOptions = useMemo(
    () => Array.from(new Set(coachingEngagements.map((row) => String(row.coach_email || '').trim().toLowerCase()).filter(Boolean))).sort(),
    [coachingEngagements]
  );

  const coachingCoacheeOptions = useMemo(
    () => Array.from(new Set(coachingEngagements.map((row) => String(row.name || '').trim()).filter(Boolean))).sort(),
    [coachingEngagements]
  );

  const coachingClientOptions = useMemo(
    () => Array.from(new Set(coachingEngagements.map((row) => String(row.client_org || '').trim()).filter(Boolean))).sort(),
    [coachingEngagements]
  );

  const coachingOutcomeOptions = useMemo(() => {
    if (!isConsultantSession) return COACHING_SESSION_OUTCOMES;
    return COACHING_SESSION_OUTCOMES.filter((option) => option !== 'no_show_chargeable');
  }, [isConsultantSession]);

  const noShowCountByEngagementId = useMemo(() => {
    const counts = {};
    coachingSessions.forEach((session) => {
      if (session.session_type !== 'no_show_chargeable') return;
      const key = String(session.engagement_id || '');
      if (!key) return;
      counts[key] = (counts[key] || 0) + 1;
    });
    return counts;
  }, [coachingSessions]);

  const coachingEntitlementRows = useMemo(
    () =>
      coachingEngagementOptions.map((engagement) => {
        const entitled = Number(engagement.total_sessions || 0);
        const used = Number(engagement.sessions_used || 0);
        const remaining = Math.max(entitled - used, 0);
        const lcpEnabled = Boolean(engagement.lcp_debrief_enabled);
        const lcpEntitled = Number(engagement.lcp_debrief_total_sessions || 0);
        const lcpUsed = Number(engagement.lcp_debrief_sessions_used || 0);
        const lcpRemaining = lcpEnabled ? Math.max(lcpEntitled - lcpUsed, 0) : 0;
        return {
          ...engagement,
          entitled,
          used,
          remaining,
          lcpEnabled,
          lcpEntitled,
          lcpUsed,
          lcpRemaining,
          oneLeft: remaining === 1,
        };
      }),
    [coachingEngagementOptions]
  );

  const coachingPlannerRows = useMemo(() => {
    const queryName = String(coachingEngagementSearch.name || '').trim().toLowerCase();
    const queryClient = String(coachingEngagementSearch.client || '').trim().toLowerCase();
    if (!queryName && !queryClient) return [];
    const today = new Date().toISOString().slice(0, 10);
    return coachingEngagementOptions
      .filter((engagement) => {
        const name = String(engagement.name || '').toLowerCase();
        const client = String(engagement.client_org || '').toLowerCase();
        if (queryName && !name.includes(queryName)) return false;
        if (queryClient && !client.includes(queryClient)) return false;
        return true;
      })
      .map((engagement) => {
        const allSessions = sessionsByEngagementId[String(engagement.id)] || [];
        const pastSessions = allSessions.filter((session) => String(session.session_date || '') < today).reverse();
        const todayAndFutureSessions = allSessions.filter((session) => String(session.session_date || '') >= today);
        const entitled = Number(engagement.total_sessions || 0);
        const used = Number(engagement.sessions_used || 0);
        const remaining = Math.max(entitled - used, 0);
        const lcpEnabled = Boolean(engagement.lcp_debrief_enabled);
        const lcpEntitled = Number(engagement.lcp_debrief_total_sessions || 0);
        const lcpUsed = Number(engagement.lcp_debrief_sessions_used || 0);
        const lcpRemaining = lcpEnabled ? Math.max(lcpEntitled - lcpUsed, 0) : 0;
        return {
          engagement,
          pastSessions,
          todayAndFutureSessions,
          entitled,
          used,
          remaining,
          lcpEnabled,
          lcpEntitled,
          lcpUsed,
          lcpRemaining,
        };
      })
      .sort((a, b) => {
        const aName = String(a.engagement?.name || '').trim().toLowerCase();
        const bName = String(b.engagement?.name || '').trim().toLowerCase();
        const byName = aName.localeCompare(bName);
        if (byName !== 0) return byName;
        const aClient = String(a.engagement?.client_org || '').trim().toLowerCase();
        const bClient = String(b.engagement?.client_org || '').trim().toLowerCase();
        return aClient.localeCompare(bClient);
      });
  }, [coachingEngagementOptions, coachingEngagementSearch.client, coachingEngagementSearch.name, sessionsByEngagementId]);

  const isPlannerSearchActive = useMemo(
    () => Boolean(String(coachingEngagementSearch.name || '').trim() || String(coachingEngagementSearch.client || '').trim()),
    [coachingEngagementSearch.client, coachingEngagementSearch.name]
  );

  const recentCoachingSessions = useMemo(() => {
    return [...coachingSessions]
      .sort((a, b) => String(b.session_date || '').localeCompare(String(a.session_date || '')))
      .slice(0, 12);
  }, [coachingSessions]);

  const groupedRecentCoachingSessions = useMemo(() => {
    const groups = new Map();
    recentCoachingSessions.forEach((session) => {
      const engagement = coachingEngagementById[String(session.engagement_id)] || {};
      const coachee = String(engagement.name || 'Unknown coachee').trim();
      const client = String(engagement.client_org || 'Unknown client').trim();
      const key = `${client.toLowerCase()}::${coachee.toLowerCase()}`;
      if (!groups.has(key)) {
        groups.set(key, { key, coachee, client, sessions: [] });
      }
      groups.get(key).sessions.push(session);
    });
    return [...groups.values()].sort((a, b) => {
      const byClient = a.client.toLowerCase().localeCompare(b.client.toLowerCase());
      if (byClient !== 0) return byClient;
      return a.coachee.toLowerCase().localeCompare(b.coachee.toLowerCase());
    });
  }, [coachingEngagementById, recentCoachingSessions]);

  useEffect(() => {
    setOpenRecentCoachingGroupByKey((prev) => {
      const fallbackOpen = groupedRecentCoachingSessions.length <= 3;
      const validKeys = new Set(groupedRecentCoachingSessions.map((group) => group.key));
      const next = {};
      let changed = false;

      groupedRecentCoachingSessions.forEach((group) => {
        if (Object.prototype.hasOwnProperty.call(prev, group.key)) {
          next[group.key] = Boolean(prev[group.key]);
        } else {
          next[group.key] = fallbackOpen;
          changed = true;
        }
      });

      Object.keys(prev).forEach((key) => {
        if (!validKeys.has(key)) {
          changed = true;
        }
      });

      if (!changed && Object.keys(prev).length === Object.keys(next).length) {
        return prev;
      }
      return next;
    });
  }, [groupedRecentCoachingSessions]);

  const consultantExpenseRows = useMemo(() => {
    if (!isConsultantSession) return [];
    return [...expenses]
      .filter((row) => String(row.submitted_by_email || '').toLowerCase() === String(sessionEmail || '').toLowerCase())
      .sort((a, b) => String(b.expense_date || '').localeCompare(String(a.expense_date || '')));
  }, [expenses, isConsultantSession, sessionEmail]);

  const consultantExpenseProjectRequirements = useMemo(() => {
    if (!isConsultantSession || !sessionEmail) return [];
    const normalizedSessionEmail = normalizeEmailIdentity(sessionEmail);

    return expenseTripOptions
      .filter((trip) => Boolean(trip.expense_report_required))
      .map((trip) => {
        const projectEndDate = String(trip.project_end_date || '').trim();
        const daysToEnd = daysUntilIso(projectEndDate);
        const hasEnded = daysToEnd !== null && daysToEnd < 0;
        const submittedEntries = expenses.filter(
          (expense) =>
            String(expense.trip_id || '') === String(trip.id) &&
            normalizeEmailIdentity(expense.submitted_by_email) === normalizedSessionEmail
        );
        const hasSubmittedExpense = submittedEntries.length > 0;

        return {
          trip,
          projectEndDate,
          hasEnded,
          submittedCount: submittedEntries.length,
          hasSubmittedExpense,
          isOutstanding: hasEnded && !hasSubmittedExpense,
        };
      })
      .sort((a, b) => {
        const aName = String(a.trip?.name || '').trim().toLowerCase();
        const bName = String(b.trip?.name || '').trim().toLowerCase();
        const byName = aName.localeCompare(bName);
        if (byName !== 0) return byName;
        const aClient = String(a.trip?.client_name || '').trim().toLowerCase();
        const bClient = String(b.trip?.client_name || '').trim().toLowerCase();
        return aClient.localeCompare(bClient);
      });
  }, [expenseTripOptions, expenses, isConsultantSession, sessionEmail]);

  const consultantOutstandingExpenseProjects = useMemo(
    () => consultantExpenseProjectRequirements.filter((item) => item.isOutstanding),
    [consultantExpenseProjectRequirements]
  );

  const adminOutstandingExpenseAlerts = useMemo(() => {
    if (isConsultantSession) return [];

    return trips
      .filter((trip) => Boolean(trip.expense_report_required))
      .map((trip) => {
        const projectEndDate = String(trip.project_end_date || trip.return_date || '').trim();
        const daysToEnd = daysUntilIso(projectEndDate);
        const overdue24h = daysToEnd !== null && daysToEnd <= -1;

        const assigned = Array.from(
          new Set(
            [trip.consultant_email, ...(Array.isArray(trip.assigned_consultants) ? trip.assigned_consultants : [])]
              .map((email) => normalizeEmailIdentity(email))
              .filter(Boolean)
          )
        );

        const outstandingConsultants = assigned.filter((consultantEmail) => {
          const hasSubmitted = expenses.some(
            (expense) =>
              String(expense.trip_id || '') === String(trip.id) &&
              normalizeEmailIdentity(expense.submitted_by_email) === consultantEmail &&
              String(expense.submitted_by_role || '').toLowerCase() === 'consultant'
          );
          return !hasSubmitted;
        });

        return {
          trip,
          projectEndDate,
          daysOverdue: daysToEnd === null ? 0 : Math.abs(daysToEnd),
          overdue24h,
          outstandingConsultants,
        };
      })
      .filter((row) => row.overdue24h && row.outstandingConsultants.length > 0)
      .sort((a, b) => b.daysOverdue - a.daysOverdue);
  }, [expenses, isConsultantSession, trips]);

  const consultantCoachingSessionRows = useMemo(() => {
    if (!isConsultantSession) return [];
    const { start_date, end_date } = consultantCoachingReportFilters;
    return coachingSessions
      .filter((session) => {
        const dateValue = String(session.session_date || '');
        if (!dateValue) return false;
        const engagement = coachingEngagementById[String(session.engagement_id)];
        if (!engagement) return false;
        const coachEmail = String(engagement.coach_email || '').toLowerCase();
        if (coachEmail !== String(sessionEmail || '').toLowerCase()) return false;
        if (start_date && dateValue < start_date) return false;
        if (end_date && dateValue > end_date) return false;
        return true;
      })
      .map((session) => ({
        ...session,
        engagement: coachingEngagementById[String(session.engagement_id)] || null,
      }))
      .sort((a, b) => String(a.session_date || '').localeCompare(String(b.session_date || '')));
  }, [
    coachingEngagementById,
    coachingSessions,
    consultantCoachingReportFilters,
    isConsultantSession,
    sessionEmail,
  ]);

  const bulkPerDiemDates = useMemo(
    () =>
      isBulkPerDiemMode
        ? listIsoDatesInclusive(expenseForm.per_diem_start_date, expenseForm.per_diem_end_date)
        : [],
    [expenseForm.per_diem_end_date, expenseForm.per_diem_start_date, isBulkPerDiemMode]
  );

  const perDiemDisplayDates = useMemo(() => {
    if (isBulkPerDiemMode) return bulkPerDiemDates;
    return expenseForm.expense_date ? [expenseForm.expense_date] : [];
  }, [bulkPerDiemDates, expenseForm.expense_date, isBulkPerDiemMode]);

  useEffect(() => {
    setPerDiemMealsByDate((prev) => {
      const allowed = new Set(perDiemDisplayDates);
      const next = {};
      let changed = false;
      Object.entries(prev).forEach(([isoDate, meals]) => {
        if (!allowed.has(isoDate)) {
          changed = true;
          return;
        }
        next[isoDate] = meals;
      });
      return changed ? next : prev;
    });
  }, [perDiemDisplayDates]);

  const tripPerDiemLastDate = useMemo(() => {
    if (!selectedExpenseTrip) return '';
    return String(selectedExpenseTrip.return_date || selectedExpenseTrip.project_end_date || '').slice(0, 10);
  }, [selectedExpenseTrip]);

  const incidentalEligibleDays = useMemo(() => {
    if (expenseForm.category !== 'per_diem') return 0;
    if (!perDiemDisplayDates.length) return 0;
    return perDiemDisplayDates.filter((isoDate) => !tripPerDiemLastDate || isoDate !== tripPerDiemLastDate).length;
  }, [
    expenseForm.category,
    perDiemDisplayDates,
    tripPerDiemLastDate,
  ]);

  const perDiemMealRates = useMemo(() => ({
    breakfast: Number(toNumber(selectedExpenseRate?.breakfast_aud).toFixed(2)),
    lunch: Number(toNumber(selectedExpenseRate?.lunch_aud).toFixed(2)),
    dinner: Number(toNumber(selectedExpenseRate?.dinner_aud).toFixed(2)),
    incidentalMidpoint: Number(toNumber(selectedExpenseRate?.incidental_midpoint_aud).toFixed(2)),
  }), [selectedExpenseRate]);

  const perDiemDayClaimRows = useMemo(
    () =>
      perDiemDisplayDates.map((isoDate) => {
        const dayMeals = perDiemMealsByDate[isoDate] || {};
        const breakfastClaimed = Boolean(dayMeals.breakfast);
        const lunchClaimed = Boolean(dayMeals.lunch);
        const dinnerClaimed = Boolean(dayMeals.dinner);
        const breakfastAmount = breakfastClaimed ? perDiemMealRates.breakfast : 0;
        const lunchAmount = lunchClaimed ? perDiemMealRates.lunch : 0;
        const dinnerAmount = dinnerClaimed ? perDiemMealRates.dinner : 0;
        const mealTotal = Number((breakfastAmount + lunchAmount + dinnerAmount).toFixed(2));
        const incidentalApplies = !tripPerDiemLastDate || isoDate !== tripPerDiemLastDate;
        const incidentalAmount = incidentalApplies ? perDiemMealRates.incidentalMidpoint : 0;
        return {
          isoDate,
          breakfastClaimed,
          lunchClaimed,
          dinnerClaimed,
          breakfastAmount,
          lunchAmount,
          dinnerAmount,
          mealTotal,
          incidentalApplies,
          incidentalAmount,
          totalAmount: Number((mealTotal + incidentalAmount).toFixed(2)),
        };
      }),
    [perDiemDisplayDates, perDiemMealRates.breakfast, perDiemMealRates.dinner, perDiemMealRates.incidentalMidpoint, perDiemMealRates.lunch, perDiemMealsByDate, tripPerDiemLastDate]
  );

  const perDiemClaimBreakdown = useMemo(() => {
    const daily = Number(
      (
        perDiemMealRates.breakfast +
        perDiemMealRates.lunch +
        perDiemMealRates.dinner
      ).toFixed(2)
    );
    const breakfastTotal = Number(
      perDiemDayClaimRows.reduce((sum, row) => sum + row.breakfastAmount, 0).toFixed(2)
    );
    const lunchTotal = Number(
      perDiemDayClaimRows.reduce((sum, row) => sum + row.lunchAmount, 0).toFixed(2)
    );
    const dinnerTotal = Number(
      perDiemDayClaimRows.reduce((sum, row) => sum + row.dinnerAmount, 0).toFixed(2)
    );
    const mealTotal = Number(
      perDiemDayClaimRows.reduce((sum, row) => sum + row.mealTotal, 0).toFixed(2)
    );
    const incidentalMidpoint = perDiemMealRates.incidentalMidpoint;
    const incidentalTotal = Number(
      perDiemDayClaimRows.reduce((sum, row) => sum + row.incidentalAmount, 0).toFixed(2)
    );
    const singleDayTotal = Number((perDiemDayClaimRows[0]?.totalAmount || 0).toFixed(2));
    const bulkGrandTotal = Number(
      perDiemDayClaimRows.reduce((sum, row) => sum + row.totalAmount, 0).toFixed(2)
    );
    return {
      daily,
      breakfastUnit: perDiemMealRates.breakfast,
      lunchUnit: perDiemMealRates.lunch,
      dinnerUnit: perDiemMealRates.dinner,
      breakfastTotal,
      lunchTotal,
      dinnerTotal,
      mealTotal,
      incidentalMidpoint,
      incidentalEligibleDays,
      incidentalTotal,
      singleDayTotal,
      bulkGrandTotal,
    };
  }, [
    incidentalEligibleDays,
    perDiemDayClaimRows,
    perDiemMealRates.breakfast,
    perDiemMealRates.dinner,
    perDiemMealRates.incidentalMidpoint,
    perDiemMealRates.lunch,
  ]);

  const computedPerDiem = useMemo(() => {
    const selectedRate = atoRates.find(
      (rate) => rate.country === tripForm.destination_country && rate.active
    );
    const rate = selectedRate?.daily_rate_aud || 0;
    const baselineStart = tripForm.departure_date || tripForm.project_start_date;
    const baselineEnd = tripForm.return_date || tripForm.project_end_date;
    const nights = nightsBetween(baselineStart, baselineEnd);
    return { rate, nights, total: rate * nights };
  }, [
    atoRates,
    tripForm.destination_country,
    tripForm.departure_date,
    tripForm.return_date,
    tripForm.project_start_date,
    tripForm.project_end_date,
  ]);

  function handleReceiptFile(file) {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setStatus('Please drop or select an image file for the receipt screenshot.');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = String(reader.result || '');
      if (!dataUrl) return;
      setExpenseForm((prev) => ({
        ...prev,
        receipt_url: dataUrl,
        receipt_thumb_url: dataUrl,
        no_receipt: false,
        no_receipt_reason: '',
      }));
      setStatus(`Receipt screenshot attached: ${file.name}`);
    };
    reader.readAsDataURL(file);
  }

  function focusNextExpenseField() {
    const perDiemDateRef =
      expenseForm.category === 'per_diem' && !isBulkPerDiemMode
        ? expensePerDiemSingleDateRef
        : expenseDateRef;
    const refByField = {
      trip: expenseProjectRef,
      consultant: expenseConsultantRef,
      flightFrom: expenseFlightFromRef,
      flightTo: expenseFlightToRef,
      date: perDiemDateRef,
      perDiemStart: expensePerDiemStartRef,
      perDiemEnd: expensePerDiemEndRef,
      amount: expenseAmountRef,
      exchangeRate: expenseExchangeRateRef,
      receipt: expenseReceiptFileRef,
    };
    const nextKey = expenseValidation.orderedMissingKeys[0];
    if (!nextKey) return;
    refByField[nextKey]?.current?.focus();
  }

  function onTogglePerDiemMeal(isoDate, meal, checked) {
    const key = String(isoDate || '');
    if (!key) return;
    setPerDiemMealsByDate((prev) => ({
      ...prev,
      [key]: {
        ...(prev[key] || {}),
        [meal]: checked,
      },
    }));
  }

  async function onTogglePerDiemInternationalCurrency(checked) {
    const shouldEnable = Boolean(checked);
    setPerDiemUseInternationalCurrency(shouldEnable);
    if (!shouldEnable) {
      setExpenseForm((prev) => ({
        ...prev,
        currency_local: 'AUD',
        gst_applicable: false,
        exchange_rate: '1',
      }));
      return;
    }

    const destinationCountry = String(selectedExpenseTrip?.destination_country || '').trim();
    const currency = currencyForCountry(destinationCountry);
    setIsResolvingPerDiemFx(true);
    try {
      const rateToAud = await fetchTodayAudExchangeRateFor(currency);
      setExpenseForm((prev) => ({
        ...prev,
        currency_local: currency,
        gst_applicable: currency === 'AUD',
        exchange_rate: currency === 'AUD' ? '1' : String(rateToAud),
      }));
      if (currency !== 'AUD') {
        setExpenseStatus(`Per diem set to ${currency} with today's rate to AUD (${rateToAud}).`);
      }
    } catch (error) {
      setExpenseForm((prev) => ({
        ...prev,
        currency_local: currency,
        gst_applicable: currency === 'AUD',
        exchange_rate: currency === 'AUD' ? '1' : '',
      }));
      setExpenseStatus(error instanceof Error ? error.message : 'Unable to load today\'s exchange rate. Enter it manually.');
    } finally {
      setIsResolvingPerDiemFx(false);
    }
  }

  useEffect(() => {
    if (!expenseValidationActive) return;
    if (expenseValidation.orderedMissingKeys.length) return;
    setExpenseValidationActive(false);
  }, [expenseValidation.orderedMissingKeys.length, expenseValidationActive]);

  const tripExpenseSummaries = useMemo(() => {
    const grouped = new Map();

    expenses.forEach((expense) => {
      const key = String(expense.trip_id);
      if (!grouped.has(key)) {
        grouped.set(key, {
          tripId: key,
          totalAud: 0,
          consultantAud: 0,
          adminAud: 0,
          approvedCount: 0,
          pendingCount: 0,
          byCategory: {},
        });
      }

      const summary = grouped.get(key);
      const amountAud = toNumber(expense.amount_aud);
      summary.totalAud += amountAud;
      if (expense.submitted_by_role === 'consultant') {
        summary.consultantAud += amountAud;
      } else {
        summary.adminAud += amountAud;
      }

      if (expense.status === 'approved') {
        summary.approvedCount += 1;
      } else {
        summary.pendingCount += 1;
      }

      summary.byCategory[expense.category] =
        (summary.byCategory[expense.category] || 0) + amountAud;
    });

    return Array.from(grouped.values())
      .map((row) => ({
        ...row,
        trip: trips.find((trip) => String(trip.id) === row.tripId),
      }))
      .sort((a, b) => b.totalAud - a.totalAud);
  }, [expenses, trips]);

  const dashboardMetrics = useMemo(() => {
    const totalAud = tripExpenseSummaries.reduce((sum, row) => sum + row.totalAud, 0);
    const approvedCount = expenses.filter((expense) => expense.status === 'approved').length;
    const pendingCount = expenses.length - approvedCount;
    const cutoff = new Date();
    cutoff.setHours(0, 0, 0, 0);
    cutoff.setMonth(cutoff.getMonth() - 12);

    const tripClientById = {};
    trips.forEach((trip) => {
      tripClientById[String(trip.id)] = String(trip.client_name || '').trim();
    });

    const engagementClientById = {};
    coachingEngagements.forEach((engagement) => {
      engagementClientById[String(engagement.id)] = String(engagement.client_org || '').trim();
    });

    const activeClientNames = new Set();
    expenses.forEach((expense) => {
      const dateValue = String(expense.expense_date || '').trim();
      if (!dateValue) return;
      const activityDate = new Date(`${dateValue}T00:00:00`);
      if (Number.isNaN(activityDate.getTime()) || activityDate < cutoff) return;
      const clientName = tripClientById[String(expense.trip_id)] || '';
      if (clientName) activeClientNames.add(clientName.toLowerCase());
    });

    coachingSessions.forEach((session) => {
      const dateValue = String(session.session_date || '').trim();
      if (!dateValue) return;
      const activityDate = new Date(`${dateValue}T00:00:00`);
      if (Number.isNaN(activityDate.getTime()) || activityDate < cutoff) return;
      const clientName = engagementClientById[String(session.engagement_id)] || '';
      if (clientName) activeClientNames.add(clientName.toLowerCase());
    });

    const activeCoachees = coachingEngagements.filter(
      (engagement) => String(engagement.status || 'active').toLowerCase() !== 'archived'
    ).length;
    const tendersClosingSoon = tenders.filter((tender) => {
      if (String(tender.status || '').toLowerCase() === 'ignore') return false;
      const daysToClose = daysUntilIso(tender.official_close_date);
      return daysToClose !== null && daysToClose >= 0 && daysToClose <= 14;
    }).length;
    return {
      totalAud,
      approvedCount,
      pendingCount,
      activeClients: activeClientNames.size,
      activeCoachees,
      tendersClosingSoon,
    };
  }, [coachingEngagements, coachingSessions, expenses, tenders, tripExpenseSummaries, trips]);

  const portfolioInvoicing = useMemo(() => {
    const outstanding = expenses.filter((expense) => expense.status !== 'invoiced');
    const invoiced = expenses.filter((expense) => expense.status === 'invoiced');
    return {
      outstandingCount: outstanding.length,
      outstandingAud: outstanding.reduce((sum, expense) => sum + toNumber(expense.amount_aud), 0),
      invoicedCount: invoiced.length,
      invoicedAud: invoiced.reduce((sum, expense) => sum + toNumber(expense.amount_aud), 0),
    };
  }, [expenses]);

  const savingsAssumptions = useMemo(
    () => ({
      hourlyRateAud: readLocalStorageNumber('adapsys_savings_hourly_rate_aud', 95),
      reportPrepBeforeMinutes: readLocalStorageNumber('adapsys_savings_report_before_minutes', 45),
      reportPrepAfterMinutes: readLocalStorageNumber('adapsys_savings_report_after_minutes', 12),
      monthlyReportCount: readLocalStorageNumber('adapsys_savings_report_count_monthly', 12),
      workbookFollowupBeforeMinutes: readLocalStorageNumber('adapsys_savings_workbook_followup_before_minutes', 30),
      workbookFollowupAfterMinutes: readLocalStorageNumber('adapsys_savings_workbook_followup_after_minutes', 8),
      monthlyWorkshopCount: readLocalStorageNumber('adapsys_savings_workshop_count_monthly', 6),
      expenseDoubleEntryBeforeMinutes: readLocalStorageNumber('adapsys_savings_expense_double_entry_before_minutes', 6),
      expenseDoubleEntryAfterMinutes: readLocalStorageNumber('adapsys_savings_expense_double_entry_after_minutes', 2),
    }),
    []
  );

  const savingsSnapshot = useMemo(() => {
    const maxZero = (value) => Math.max(0, Number(value) || 0);
    const reportHours =
      (maxZero(savingsAssumptions.reportPrepBeforeMinutes - savingsAssumptions.reportPrepAfterMinutes) *
        maxZero(savingsAssumptions.monthlyReportCount)) /
      60;
    const workbookHours =
      (maxZero(savingsAssumptions.workbookFollowupBeforeMinutes - savingsAssumptions.workbookFollowupAfterMinutes) *
        maxZero(savingsAssumptions.monthlyWorkshopCount)) /
      60;
    const xeroCandidateCount = expenses.filter((row) => ['approved', 'invoiced'].includes(String(row.status || '').toLowerCase())).length;
    const expenseHours =
      (maxZero(savingsAssumptions.expenseDoubleEntryBeforeMinutes - savingsAssumptions.expenseDoubleEntryAfterMinutes) *
        xeroCandidateCount) /
      60;
    const totalHours = reportHours + workbookHours + expenseHours;
    const hourlyRate = maxZero(savingsAssumptions.hourlyRateAud);
    const totalAud = totalHours * hourlyRate;
    return {
      reportHours,
      workbookHours,
      expenseHours,
      totalHours,
      totalAud,
      xeroCandidateCount,
      hourlyRate,
    };
  }, [expenses, savingsAssumptions]);

  const filteredTenders = useMemo(() => {
    const rows = tenderFilter === 'all' ? tenders : tenders.filter((row) => row.status === tenderFilter);
    return rows;
  }, [tenderFilter, tenders]);

  async function refresh() {
    try {
      if (isClientViewerSession) {
        setTrips([]);
        setExpenses([]);
        setExpenseXeroSyncById({});
        setExpenseXeroIntegrationStatus(null);
        setTenders([]);
        setAtoRates([]);
        setCoachingEngagements([]);
        setCoachingSessions([]);
        setConsultants([]);
        setContractScaffoldRows([]);
        setContractMergeTemplates([]);
        setTravelBookingSummary({
          total_required: 0,
          outstanding_to_book: 0,
          booked: 0,
          need_expense_prompt: 0,
        });
        const [coachesData, clientProgramsData] = await Promise.all([listCoaches(), listClientPrograms()]);
        setCoaches(coachesData);
        setClientPrograms(clientProgramsData);

        if (!isClientReportsFeatureEnabled) {
          setClientCoachingSummaryRows([]);
          setClientCoachingSummaryStatus('Client reports feature is currently disabled.');
          return;
        }

        setIsLoadingClientCoachingSummary(true);
        setClientCoachingSummaryStatus('Loading client coaching summary...');
        const rows = await fetchClientCoachingSummary({
          start_date: clientReportFilters.start_date,
          end_date: clientReportFilters.end_date,
        });
        setClientCoachingSummaryRows(Array.isArray(rows) ? rows : []);
        setClientCoachingSummaryStatus('Client coaching summary ready.');
        setIsLoadingClientCoachingSummary(false);
        return;
      }

      if (isCoachOnlySession) {
        const [coachesData, clientProgramsData, coachingEngagementData, coachingSessionData] = await Promise.all([
          listCoaches(),
          listClientPrograms(),
          listCoachingEngagements(),
          listCoachingSessions(),
        ]);
        setTrips([]);
        setExpenses([]);
        setExpenseXeroSyncById({});
        setExpenseXeroIntegrationStatus(null);
        setTenders([]);
        setTenderSummary({ total: 0, urgent: 0, pursue: 0, monitor: 0, ignore: 0, led: 0 });
        setAtoRates([]);
        setReminderLastSentByTripId({});
        setConsultants([]);
        setCoaches(coachesData);
        setClientPrograms(clientProgramsData);
        setContractScaffoldRows([]);
        setContractMergeTemplates([]);
        setTravelBookingSummary({
          total_required: 0,
          outstanding_to_book: 0,
          booked: 0,
          need_expense_prompt: 0,
        });
        setCoachingEngagements(coachingEngagementData);
        setCoachingSessions(coachingSessionData);
        setCoachingSessionForm((prev) => ({
          ...prev,
          engagement_id: prev.engagement_id || coachingEngagementData[0]?.id || '',
        }));
        setCoachingReportFilters((prev) => ({
          report_by: prev.report_by || 'coach',
          client_org: prev.client_org || coachingEngagementData[0]?.client_org || '',
          coach_email: prev.coach_email || coachingEngagementData[0]?.coach_email || '',
          coachee_name: prev.coachee_name || coachingEngagementData[0]?.name || '',
          start_date: prev.start_date || '',
          end_date: prev.end_date || '',
        }));
        return;
      }

      const [
        tripData,
        expenseData,
        tenderData,
        tenderSummaryData,
        ratesData,
        consultantsData,
        coachesData,
        clientProgramsData,
        coachingEngagementData,
        coachingSessionData,
        reminderLastSentData,
        contractRowsData,
        travelBookingSummaryData,
        contractMergeFieldsData,
        expenseXeroSyncRows,
        expenseXeroConfig,
      ] = await Promise.all([
        listTrips(),
        listExpenses(),
        listTenders(),
        getTenderSummary(),
        listAtoRates(),
        listConsultants(),
        listCoaches(),
        listClientPrograms(),
        listCoachingEngagements(),
        listCoachingSessions(),
        isConsultantSession ? Promise.resolve([]) : listReminderLastSent(),
        isConsultantSession ? Promise.resolve([]) : listContracts(),
        isConsultantSession
          ? Promise.resolve({ total_required: 0, outstanding_to_book: 0, booked: 0, need_expense_prompt: 0 })
          : getTravelBookingSummary(),
        isConsultantSession ? Promise.resolve({ templates: [] }) : getContractMergeFields(),
        isConsultantSession ? Promise.resolve([]) : listExpenseXeroSyncStatus().catch(() => []),
        isConsultantSession ? Promise.resolve(null) : getExpenseXeroSyncConfig().catch(() => null),
      ]);
      setTrips(tripData);
      setExpenses(expenseData);
      setTenders(tenderData);
      setTenderSummary(tenderSummaryData);
      setCoachingEngagements(coachingEngagementData);
      setCoachingSessions(coachingSessionData);
      setAtoRates(ratesData);
      const reminderByTripId = {};
      reminderLastSentData.forEach((row) => {
        const key = String(row.trip_id || '');
        if (!key) return;
        reminderByTripId[key] = {
          last_sent_at: row.last_sent_at,
          reminder_type: row.reminder_type,
        };
      });
      setReminderLastSentByTripId(reminderByTripId);
      setConsultants(consultantsData);
      setCoaches(coachesData);
      setClientPrograms(clientProgramsData);
      setContractScaffoldRows(Array.isArray(contractRowsData) ? contractRowsData : []);
      setContractMergeTemplates(Array.isArray(contractMergeFieldsData?.templates) ? contractMergeFieldsData.templates : []);
      setTravelBookingSummary(travelBookingSummaryData || {
        total_required: 0,
        outstanding_to_book: 0,
        booked: 0,
        need_expense_prompt: 0,
      });
      const syncById = {};
      (Array.isArray(expenseXeroSyncRows) ? expenseXeroSyncRows : []).forEach((row) => {
        if (!row?.expense_id) return;
        syncById[String(row.expense_id)] = row;
      });
      setExpenseXeroSyncById(syncById);
      setExpenseXeroIntegrationStatus(expenseXeroConfig);
      setAdminLookupDrafts({
        consultants: JSON.stringify(consultantsData, null, 2),
        coaches: JSON.stringify(coachesData, null, 2),
        clientPrograms: JSON.stringify(clientProgramsData, null, 2),
      });
      if (!tripForm.destination_country && ratesData.length > 0) {
        setTripForm((prev) => ({ ...prev, destination_country: ratesData[0].country }));
      }
      if (consultantsData.length > 0) {
        setTripForm((prev) => {
          const sessionConsultantEmail =
            consultantsData.find(
              (consultant) => String(consultant.email || '').toLowerCase() === String(sessionEmail || '').toLowerCase()
            )?.email || '';
          const defaultRoster =
            isConsultantSession && sessionConsultantEmail
              ? [sessionConsultantEmail]
              : consultantsData.map((consultant) => consultant.email);
          return {
            ...prev,
            consultant_email:
              prev.consultant_email || (isConsultantSession && sessionConsultantEmail ? sessionConsultantEmail : ''),
            assigned_consultants: prev.assigned_consultants.length ? prev.assigned_consultants : defaultRoster,
          };
        });
      }
      if (!tripForm.client_name && clientProgramsData.length > 0) {
        const defaultClient = clientProgramsData[0].client_name;
        setTripForm((prev) => ({
          ...prev,
          client_name: defaultClient,
          program_name: '',
        }));
      }
      setExpenseForm((prev) => {
        const next = { ...prev };
        if (isConsultantSession) {
          next.submitted_by_role = 'consultant';
          next.submitted_by_email = sessionEmail || next.submitted_by_email;
        } else {
          next.submitted_by_email = '';
        }
        return next;
      });
      setEmailIntakeForm((prev) => ({
        ...prev,
        trip_id: prev.trip_id || tripData[0]?.id || '',
      }));
      setCoachingSessionForm((prev) => ({
        ...prev,
        engagement_id: prev.engagement_id || coachingEngagementData[0]?.id || '',
      }));
      setCoachingReportFilters((prev) => {
        return {
          report_by: prev.report_by || 'coach',
          client_org: prev.client_org || coachingEngagementData[0]?.client_org || '',
          coach_email: prev.coach_email || coachingEngagementData[0]?.coach_email || '',
          coachee_name: prev.coachee_name || coachingEngagementData[0]?.name || '',
          start_date: prev.start_date || '',
          end_date: prev.end_date || '',
        };
      });
      setSelectedReportClient((prev) => prev || String(tripData[0]?.client_name || ''));
      setSelectedReportTripId((prev) => prev || tripData[0]?.id || '');
    } catch (error) {
      if (isClientViewerSession) {
        setIsLoadingClientCoachingSummary(false);
      }
      setStatus(error.message);
    }
  }

  async function onMoveExpenseToProject(expenseId) {
    const key = String(expenseId);
    const targetTripId = String(tripDraftByExpenseId[key] || '').trim();
    if (!targetTripId) {
      setStatus('Select a destination project before moving this expense.');
      return;
    }

    setMovingExpenseId(key);
    try {
      await updateExpenseTrip(expenseId, { trip_id: targetTripId });
      setStatus('Expense moved to selected project.');
      setTripDraftByExpenseId((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setMovingExpenseId('');
    }
  }

  async function onTriageTender(event) {
    event.preventDefault();
    setIsSubmittingTender(true);
    try {
      await triageTender({
        ...tenderForm,
        eoi_deadline: tenderForm.eoi_deadline || null,
        official_close_date: tenderForm.official_close_date || null,
      });
      setStatus('Tender triaged and scored.');
      setTenderForm(INITIAL_TENDER_FORM);
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setIsSubmittingTender(false);
    }
  }

  async function onTenderDecision(tenderId, decision) {
    try {
      await setTenderDecision(tenderId, { decision });
      setStatus(`Tender updated: ${decision}.`);
      await refresh();
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function onCreateCoachingEngagement(event) {
    event.preventDefault();
    setIsCreatingCoachingEngagement(true);
    setCoachingStatus(editingCoachingEngagementId ? 'Updating coaching engagement...' : 'Creating coaching engagement...');
    try {
      const totalSessions = Number(coachingEngagementForm.total_sessions || 0);
      const usedSessions = Number(coachingEngagementForm.sessions_used || 0);
      if (!Number.isFinite(totalSessions) || totalSessions <= 0) {
        setCoachingStatus('Entitled sessions must be 1 or greater.');
        setIsCreatingCoachingEngagement(false);
        return;
      }
      if (!Number.isFinite(usedSessions) || usedSessions < 0) {
        setCoachingStatus('Sessions used must be 0 or greater.');
        setIsCreatingCoachingEngagement(false);
        return;
      }
      if (usedSessions > totalSessions) {
        setCoachingStatus('Sessions used cannot be greater than entitled sessions.');
        setIsCreatingCoachingEngagement(false);
        return;
      }

      const lcpTotal = coachingEngagementForm.lcp_debrief_enabled
        ? Number(coachingEngagementForm.lcp_debrief_total_sessions || 0)
        : 0;
      const lcpUsed = coachingEngagementForm.lcp_debrief_enabled
        ? Number(coachingEngagementForm.lcp_debrief_sessions_used || 0)
        : 0;
      if (coachingEngagementForm.lcp_debrief_enabled) {
        if (!Number.isFinite(lcpTotal) || lcpTotal < 0) {
          setCoachingStatus('LCP entitled sessions must be 0 or greater.');
          setIsCreatingCoachingEngagement(false);
          return;
        }
        if (!Number.isFinite(lcpUsed) || lcpUsed < 0) {
          setCoachingStatus('LCP sessions used must be 0 or greater.');
          setIsCreatingCoachingEngagement(false);
          return;
        }
        if (lcpUsed > lcpTotal) {
          setCoachingStatus('LCP sessions used cannot be greater than LCP entitled sessions.');
          setIsCreatingCoachingEngagement(false);
          return;
        }
      }

      const payload = {
        ...coachingEngagementForm,
        total_sessions: totalSessions,
        sessions_used: usedSessions,
        lcp_debrief_enabled: Boolean(coachingEngagementForm.lcp_debrief_enabled),
        lcp_debrief_total_sessions: coachingEngagementForm.lcp_debrief_enabled
          ? lcpTotal
          : 0,
        lcp_debrief_sessions_used: coachingEngagementForm.lcp_debrief_enabled
          ? lcpUsed
          : 0,
        associate_cost_per_session: !isConsultantSession && String(coachingEngagementForm.associate_cost_per_session || '').trim() !== ''
          ? Number(coachingEngagementForm.associate_cost_per_session)
          : null,
      };
      if (editingCoachingEngagementId) {
        await updateCoachingEngagement(editingCoachingEngagementId, payload);
        setCoachingStatus('Coaching engagement updated.');
      } else {
        await createCoachingEngagement(payload);
        setCoachingStatus('Coaching engagement created.');
      }
      setCoachingEngagementForm({
        name: '',
        job_title: '',
        client_org: '',
        coach_email: '',
        total_sessions: '5',
        sessions_used: '0',
        lcp_debrief_enabled: false,
        lcp_debrief_total_sessions: '0',
        lcp_debrief_sessions_used: '0',
        associate_cost_per_session: '',
      });
      setEditingCoachingEngagementId('');
      await refresh();
    } catch (error) {
      setCoachingStatus(error.message);
    } finally {
      setIsCreatingCoachingEngagement(false);
    }
  }

  function onStartEditCoachingEngagement(engagement) {
    setEditingCoachingEngagementId(String(engagement.id));
    setCoachingEngagementForm({
      name: String(engagement.name || ''),
      job_title: String(engagement.job_title || ''),
      client_org: String(engagement.client_org || ''),
      coach_email: String(engagement.coach_email || ''),
      total_sessions: String(engagement.total_sessions ?? '0'),
      sessions_used: String(engagement.sessions_used ?? '0'),
      lcp_debrief_enabled: Boolean(engagement.lcp_debrief_enabled),
      lcp_debrief_total_sessions: String(engagement.lcp_debrief_total_sessions ?? '0'),
      lcp_debrief_sessions_used: String(engagement.lcp_debrief_sessions_used ?? '0'),
      associate_cost_per_session: String(engagement.associate_cost_per_session ?? ''),
    });
    setCoachingStatus('Editing coachee record. Update fields and click Save Coachee Record.');
  }

  function onCancelEditCoachingEngagement() {
    setEditingCoachingEngagementId('');
    setCoachingEngagementForm({
      name: '',
      job_title: '',
      client_org: '',
      coach_email: '',
      total_sessions: '5',
      sessions_used: '0',
      lcp_debrief_enabled: false,
      lcp_debrief_total_sessions: '0',
      lcp_debrief_sessions_used: '0',
      associate_cost_per_session: '',
    });
    setCoachingStatus('Coachee record edit cancelled.');
  }

  async function onLogCoachingSession(event) {
    event.preventDefault();
    if (!String(coachingSessionForm.engagement_id || '').trim()) {
      setCoachingStatus('Select an engagement before saving the session.');
      return;
    }
    if (!String(coachingSessionForm.session_date || '').trim()) {
      setCoachingStatus('Select a session date before saving the session.');
      return;
    }
    const selectedEngagement = coachingEngagementById[String(coachingSessionForm.engagement_id)] || null;
    if (coachingSessionForm.lcp_debrief && !selectedEngagement?.lcp_debrief_enabled) {
      setCoachingStatus('This coachee does not have LCP de-brief entitlement enabled.');
      return;
    }
    if (coachingSessionForm.lcp_debrief && !String(coachingSessionForm.lcp_debrief_date || '').trim()) {
      setCoachingStatus('Select an LCP de-brief date before saving the session.');
      return;
    }
    setIsSubmittingCoachingSession(true);
    setCoachingStatus(editingCoachingSessionId ? 'Updating coaching session...' : 'Logging coaching session...');
    try {
      const durationMins = Number(coachingSessionForm.duration_mins || 0);
      if (!Number.isFinite(durationMins) || durationMins <= 0) {
        setCoachingStatus('Session duration must be 1 minute or greater.');
        setIsSubmittingCoachingSession(false);
        return;
      }
      const deliveryMode = String(coachingSessionForm.delivery_mode || '').trim() || 'video';
      const payload = {
        ...coachingSessionForm,
        duration_mins: durationMins,
        delivery_mode: deliveryMode,
        lcp_debrief_date: coachingSessionForm.lcp_debrief
          ? String(coachingSessionForm.lcp_debrief_date || '').trim() || null
          : null,
      };
      if (editingCoachingSessionId) {
        await updateCoachingSession(editingCoachingSessionId, payload);
        setCoachingStatus('Coaching session updated.');
      } else {
        await logCoachingSession(payload);
        setCoachingStatus('Coaching session logged.');
      }
      setCoachingSessionForm((prev) => ({
        ...prev,
        session_type: 'completed',
        lcp_debrief: false,
        lcp_debrief_date: '',
        duration_mins: prev.duration_mins || '60',
        delivery_mode: prev.delivery_mode || 'video',
        invoiced_to_adapsys: false,
        session_date: '',
        notes: '',
      }));
      setEditingCoachingSessionId('');
      await refresh();
    } catch (error) {
      setCoachingStatus(error.message);
    } finally {
      setIsSubmittingCoachingSession(false);
    }
  }

  function onStartEditCoachingSession(session) {
    setEditingCoachingSessionId(String(session.id));
    setCoachingSessionForm({
      engagement_id: String(session.engagement_id || ''),
      session_date: String(session.session_date || ''),
      session_type: String(session.session_type || 'completed'),
      lcp_debrief: Boolean(session.lcp_debrief),
      lcp_debrief_date: String(session.lcp_debrief_date || ''),
      duration_mins: String(session.duration_mins ?? '60'),
      delivery_mode: String(session.delivery_mode || 'video'),
      invoiced_to_adapsys: Boolean(session.invoiced_to_adapsys),
      notes: String(session.notes || ''),
    });
    setCoachingStatus('Editing coaching session. Update details and click Save Session Changes.');
  }

  function onCancelEditCoachingSession() {
    setEditingCoachingSessionId('');
    setCoachingSessionForm((prev) => ({
      ...prev,
      session_type: 'completed',
      lcp_debrief: false,
      lcp_debrief_date: '',
      duration_mins: prev.duration_mins || '60',
      delivery_mode: prev.delivery_mode || 'video',
      invoiced_to_adapsys: false,
      session_date: '',
      notes: '',
    }));
    setCoachingStatus('Session edit cancelled.');
  }

  async function onDeleteCoachingSession(session) {
    const sessionId = String(session?.id || '');
    if (!sessionId) return;
    const engagement = coachingEngagementById[String(session.engagement_id)] || null;
    const label = `${engagement?.name || 'this session'} on ${formatDateAu(session.session_date)}`;
    const confirmed =
      typeof window === 'undefined'
        ? true
        : window.confirm(`Delete ${label}? This cannot be undone.`);
    if (!confirmed) return;

    setDeletingCoachingSessionId(sessionId);
    try {
      await deleteCoachingSessionApi(session.id);
      if (editingCoachingSessionId === sessionId) {
        onCancelEditCoachingSession();
      }
      setCoachingStatus(`Deleted coaching session: ${label}.`);
      await refresh();
    } catch (error) {
      setCoachingStatus(error.message || 'Failed to delete coaching session.');
    } finally {
      setDeletingCoachingSessionId('');
    }
  }

  async function onAddPlannerFutureSession(engagementId) {
    const key = String(engagementId || '');
    const sessionDate = String(plannerScheduleDraftByEngagementId[key] || '').trim();
    if (!key || !sessionDate) {
      setCoachingStatus('Choose a future session date before adding it.');
      return;
    }

    setSchedulingPlannerEngagementId(key);
    try {
      await logCoachingSession({
        engagement_id: key,
        session_date: sessionDate,
        session_type: 'postponed',
        invoiced_to_adapsys: false,
        notes: 'Planned in engagement planner',
      });
      setPlannerScheduleDraftByEngagementId((prev) => ({
        ...prev,
        [key]: '',
      }));
      setCoachingStatus(`Future session added for ${sessionDate}.`);
      await refresh();
    } catch (error) {
      setCoachingStatus(error.message || 'Failed to add future session.');
    } finally {
      setSchedulingPlannerEngagementId('');
    }
  }

  function onToggleAdminEngagementSort(key) {
    setAdminEngagementSort((prev) => {
      if (prev.key === key) {
        return {
          key,
          direction: prev.direction === 'asc' ? 'desc' : 'asc',
        };
      }
      return {
        key,
        direction: 'asc',
      };
    });
  }

  async function onPreviewCoachingReport() {
    const { report_by, client_org, coach_email, coachee_name, start_date, end_date } = coachingReportFilters;
    const selectedScopeValue =
      report_by === 'client' ? client_org : report_by === 'coach' ? coach_email : coachee_name;
    if (!selectedScopeValue) {
      setCoachingReportStatus(
        report_by === 'client'
          ? 'Select a client to preview coaching report.'
          : report_by === 'coach'
          ? 'Select a coach to preview coaching report.'
          : 'Select a coachee to preview coaching report.'
      );
      return;
    }
    if (start_date && end_date && start_date > end_date) {
      setCoachingReportStatus('Start date must be on or before end date.');
      return;
    }
    setIsPreviewingCoachingReport(true);
    setCoachingReportStatus('Generating coaching report preview...');
    try {
      const html = await fetchCoachingReportPreview({
        report_by,
        client_org: report_by === 'client' ? client_org : '',
        coach_email: report_by === 'coach' ? coach_email : '',
        coachee_name: report_by === 'coachee' ? coachee_name : '',
        start_date,
        end_date,
      });
      setCoachingReportPreviewHtml(html);
      setCoachingReportStatus('Coaching report preview ready.');
    } catch (error) {
      setCoachingReportStatus(error.message);
    } finally {
      setIsPreviewingCoachingReport(false);
    }
  }

  async function onDownloadCoachingReportPdf() {
    const { report_by, client_org, coach_email, coachee_name, start_date, end_date } = coachingReportFilters;
    const selectedScopeValue =
      report_by === 'client' ? client_org : report_by === 'coach' ? coach_email : coachee_name;
    if (!selectedScopeValue) {
      setCoachingReportStatus(
        report_by === 'client'
          ? 'Select a client to download coaching report.'
          : report_by === 'coach'
          ? 'Select a coach to download coaching report.'
          : 'Select a coachee to download coaching report.'
      );
      return;
    }
    if (start_date && end_date && start_date > end_date) {
      setCoachingReportStatus('Start date must be on or before end date.');
      return;
    }
    setIsDownloadingCoachingReportPdf(true);
    try {
      const blob = await downloadCoachingReportPdf({
        report_by,
        client_org: report_by === 'client' ? client_org : '',
        coach_email: report_by === 'coach' ? coach_email : '',
        coachee_name: report_by === 'coachee' ? coachee_name : '',
        start_date,
        end_date,
      });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      const safeClient =
        String(selectedScopeValue).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'report';
      anchor.download = `adapsys-australia-pacific-coaching-report-${report_by}-${safeClient}.pdf`;
      anchor.click();
      window.URL.revokeObjectURL(url);
      setCoachingReportStatus('Coaching PDF download started.');
    } catch (error) {
      setCoachingReportStatus(error.message);
    } finally {
      setIsDownloadingCoachingReportPdf(false);
    }
  }

  async function onSaveAtoRate(rateId) {
    const draft = atoRateDraftById[String(rateId)];
    if (!draft) return;

    const breakfastAud = toNumber(draft.breakfast_aud);
    const lunchAud = toNumber(draft.lunch_aud);
    const dinnerAud = toNumber(draft.dinner_aud);
    const derivedDailyRate = Number((breakfastAud + lunchAud + dinnerAud).toFixed(2));

    setSavingAtoRateId(String(rateId));
    try {
      await updateAtoRate(rateId, {
        daily_rate_aud: derivedDailyRate,
        breakfast_aud: breakfastAud,
        lunch_aud: lunchAud,
        dinner_aud: dinnerAud,
        incidental_midpoint_aud: toNumber(draft.incidental_midpoint_aud),
        tax_year: normalizeFinancialYearLabel(draft.tax_year),
        active: Boolean(draft.active),
      });
      setStatus('ATO rate updated. Meal and incidental amounts are now editable in-app.');
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setSavingAtoRateId('');
    }
  }

  async function onMarkExpenseInvoiced(expenseId) {
    try {
      await markExpenseInvoiced(expenseId);
      setStatus('Expense marked as invoiced.');
      await refresh();
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function onDeleteExpense(expenseId) {
    const confirmed = window.confirm('Delete this expense permanently? This cannot be undone.');
    if (!confirmed) return;

    const key = String(expenseId);
    setDeletingExpenseId(key);
    try {
      await deleteExpense(expenseId);
      setStatus('Expense deleted.');
      setReceiptDraftByExpenseId((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
      setTripDraftByExpenseId((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setDeletingExpenseId('');
    }
  }

  async function onPushExpenseToXero(expenseId) {
    const key = String(expenseId);
    setSyncingExpenseId(key);
    try {
      const result = await pushExpenseToXero(expenseId);
      const syncRow = result?.sync;
      if (syncRow?.expense_id) {
        setExpenseXeroSyncById((prev) => ({
          ...prev,
          [String(syncRow.expense_id)]: syncRow,
        }));
      }
      setStatus(result?.message || 'Expense sync action completed.');
    } catch (error) {
      setStatus(error.message || 'Failed to sync expense to Xero.');
    } finally {
      setSyncingExpenseId('');
    }
  }

  function onAdminEngagementFieldChange(engagementId, field, value) {
    const key = String(engagementId);
    setAdminEngagementDraftById((prev) => ({
      ...prev,
      [key]: {
        ...(prev[key] || {}),
        [field]: value,
      },
    }));
    setAdminEngagementSaveNoteById((prev) => ({ ...prev, [key]: 'Unsaved changes' }));
  }

  function onAdminTripFieldChange(tripId, field, value) {
    const key = String(tripId);
    setAdminTripDraftById((prev) => ({
      ...prev,
      [key]: {
        ...(prev[key] || {}),
        [field]: value,
      },
    }));
    setAdminTripSaveNoteById((prev) => ({ ...prev, [key]: 'Unsaved changes' }));
  }

  async function onSaveAdminTrip(trip) {
    const key = String(trip.id);
    const draft = adminTripDraftById[key] || {};
    const assignedRaw = draft.assigned_consultants ?? trip.assigned_consultants ?? [];
    const assigned = Array.isArray(assignedRaw)
      ? assignedRaw.map((item) => String(item).trim().toLowerCase()).filter(Boolean)
      : String(assignedRaw)
        .split(',')
        .map((item) => item.trim().toLowerCase())
        .filter(Boolean);
    const payload = {
      name: draft.name ?? trip.name,
      consultant_email: String(draft.consultant_email ?? trip.consultant_email ?? '').trim().toLowerCase(),
      assigned_consultants: assigned,
      client_name: draft.client_name ?? trip.client_name,
      program_name: draft.program_name ?? trip.program_name,
      destination_country: draft.destination_country ?? trip.destination_country,
      destination_city: (draft.destination_city ?? trip.destination_city ?? '').trim() || null,
      project_start_date: (draft.project_start_date ?? trip.project_start_date ?? '') || null,
      project_end_date: (draft.project_end_date ?? trip.project_end_date ?? '') || null,
      departure_date: (draft.departure_date ?? trip.departure_date ?? '') || null,
      return_date: (draft.return_date ?? trip.return_date ?? '') || null,
      expense_report_required: Boolean(draft.expense_report_required ?? trip.expense_report_required),
      travel_booking_required: Boolean(draft.travel_booking_required ?? trip.travel_booking_required),
      travel_request_status: String(draft.travel_request_status ?? trip.travel_request_status ?? 'not_required') || 'not_required',
      travel_needs_flight: Boolean(draft.travel_needs_flight ?? trip.travel_needs_flight),
      travel_needs_accommodation: Boolean(draft.travel_needs_accommodation ?? trip.travel_needs_accommodation),
      travel_outbound_preference: String(draft.travel_outbound_preference ?? trip.travel_outbound_preference ?? '').trim() || null,
      travel_outbound_target_date: String(draft.travel_outbound_target_date ?? trip.travel_outbound_target_date ?? '').trim() || null,
      travel_return_preference: String(draft.travel_return_preference ?? trip.travel_return_preference ?? '').trim() || null,
      travel_return_target_date: String(draft.travel_return_target_date ?? trip.travel_return_target_date ?? '').trim() || null,
      travel_admin_notes: String(draft.travel_admin_notes ?? trip.travel_admin_notes ?? '').trim() || null,
      travel_booked_add_expense_prompted: Boolean(
        draft.travel_booked_add_expense_prompted ?? trip.travel_booked_add_expense_prompted
      ),
    };

    setSavingAdminTripId(key);
    setAdminTripSaveNoteById((prev) => ({ ...prev, [key]: 'Saving...' }));
    try {
      await updateTrip(trip.id, payload);
      setStatus(`Updated project: ${payload.name}.`);
      setAdminTripDraftById((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
      setAdminTripSaveNoteById((prev) => ({
        ...prev,
        [key]: `Saved ${new Date().toLocaleTimeString()}`,
      }));
      await refresh();
    } catch (error) {
      setAdminTripSaveNoteById((prev) => ({ ...prev, [key]: `Save failed: ${error.message}` }));
      setStatus(error.message);
    } finally {
      setSavingAdminTripId('');
    }
  }

  async function onSaveAdminLookup(kind) {
    const raw =
      kind === 'consultants'
        ? adminLookupDrafts.consultants
        : kind === 'coaches'
          ? adminLookupDrafts.coaches
          : adminLookupDrafts.clientPrograms;
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (error) {
      setStatus(`Invalid JSON for ${kind}.`);
      return;
    }
    if (!Array.isArray(parsed)) {
      setStatus(`JSON for ${kind} must be an array.`);
      return;
    }

    setSavingAdminLookupKey(kind);
    setAdminLookupSaveNoteByKind((prev) => ({ ...prev, [kind]: 'Saving...' }));
    try {
      if (kind === 'consultants') {
        await updateLookupConsultants({ items: parsed });
      } else if (kind === 'coaches') {
        await updateLookupCoaches({ items: parsed });
      } else {
        await updateLookupClientPrograms({ items: parsed });
      }
      setStatus(`Updated ${kind} lookup file.`);
      setAdminLookupSaveNoteByKind((prev) => ({
        ...prev,
        [kind]: `Saved ${new Date().toLocaleTimeString()}`,
      }));
      await refresh();
    } catch (error) {
      setAdminLookupSaveNoteByKind((prev) => ({ ...prev, [kind]: `Save failed: ${error.message}` }));
      setStatus(error.message);
    } finally {
      setSavingAdminLookupKey('');
    }
  }

  function onFormatAdminLookup(kind) {
    const raw =
      kind === 'consultants'
        ? adminLookupDrafts.consultants
        : kind === 'coaches'
          ? adminLookupDrafts.coaches
          : adminLookupDrafts.clientPrograms;

    const parsed = parseLookupDraftArray(raw);
    if (parsed.error) {
      setStatus(`Cannot format ${kind}: ${parsed.error}`);
      return;
    }

    const pretty = JSON.stringify(parsed.items, null, 2);
    setAdminLookupDrafts((prev) => ({ ...prev, [kind]: pretty }));
    setStatus(`${kind} JSON formatted for readability.`);
  }

  function onLookupRowFieldChange(kind, rowIndex, field, value) {
    const raw =
      kind === 'consultants'
        ? adminLookupDrafts.consultants
        : kind === 'coaches'
          ? adminLookupDrafts.coaches
          : adminLookupDrafts.clientPrograms;
    const parsed = parseLookupDraftArray(raw);
    if (parsed.error) {
      setStatus(`Cannot edit ${kind}: ${parsed.error}`);
      return;
    }

    const next = parsed.items.map((row, idx) =>
      idx === rowIndex ? { ...(row || {}), [field]: value } : row
    );
    setAdminLookupDrafts((prev) => ({
      ...prev,
      [kind]: JSON.stringify(next, null, 2),
    }));
    setAdminLookupSaveNoteByKind((prev) => ({ ...prev, [kind]: 'Unsaved changes' }));
  }

  function onAddLookupRow(kind) {
    const raw =
      kind === 'consultants'
        ? adminLookupDrafts.consultants
        : kind === 'coaches'
          ? adminLookupDrafts.coaches
          : adminLookupDrafts.clientPrograms;
    const parsed = parseLookupDraftArray(raw);
    if (parsed.error) {
      setStatus(`Cannot add row to ${kind}: ${parsed.error}`);
      return;
    }

    const blankRow =
      kind === 'clientPrograms'
        ? { client_name: '', program_name: '' }
        : { name: '', email: '' };

    setAdminLookupDrafts((prev) => ({
      ...prev,
      [kind]: JSON.stringify([...parsed.items, blankRow], null, 2),
    }));
    setAdminLookupSaveNoteByKind((prev) => ({ ...prev, [kind]: 'Unsaved changes' }));
  }

  function onRemoveLookupRow(kind, rowIndex) {
    const raw =
      kind === 'consultants'
        ? adminLookupDrafts.consultants
        : kind === 'coaches'
          ? adminLookupDrafts.coaches
          : adminLookupDrafts.clientPrograms;
    const parsed = parseLookupDraftArray(raw);
    if (parsed.error) {
      setStatus(`Cannot remove row from ${kind}: ${parsed.error}`);
      return;
    }

    const next = parsed.items.filter((_, idx) => idx !== rowIndex);
    setAdminLookupDrafts((prev) => ({
      ...prev,
      [kind]: JSON.stringify(next, null, 2),
    }));
    setAdminLookupSaveNoteByKind((prev) => ({ ...prev, [kind]: 'Unsaved changes' }));
  }

  function onAdminSessionFieldChange(sessionId, field, value) {
    const key = String(sessionId);
    setAdminSessionDraftById((prev) => ({
      ...prev,
      [key]: {
        ...(prev[key] || {}),
        [field]: value,
      },
    }));
  }

  async function onSaveAdminEngagement(engagement) {
    const key = String(engagement.id);
    const draft = adminEngagementDraftById[key] || {};
    const payload = {
      name: draft.name ?? engagement.name,
      job_title: (draft.job_title ?? engagement.job_title) || null,
      client_org: draft.client_org ?? engagement.client_org,
      coach_email: draft.coach_email ?? engagement.coach_email,
      total_sessions: Number(draft.total_sessions ?? engagement.total_sessions ?? 0),
      sessions_used: Number(draft.sessions_used ?? engagement.sessions_used ?? 0),
      lcp_debrief_enabled: Boolean(draft.lcp_debrief_enabled ?? engagement.lcp_debrief_enabled),
      lcp_debrief_total_sessions: Number(
        draft.lcp_debrief_total_sessions ?? engagement.lcp_debrief_total_sessions ?? 0
      ),
      lcp_debrief_sessions_used: Number(
        draft.lcp_debrief_sessions_used ?? engagement.lcp_debrief_sessions_used ?? 0
      ),
      session_rate:
        draft.session_rate === ''
          ? null
          : draft.session_rate !== undefined
            ? Number(draft.session_rate)
            : engagement.session_rate,
      associate_cost_per_session:
        draft.associate_cost_per_session === ''
          ? null
          : draft.associate_cost_per_session !== undefined
            ? Number(draft.associate_cost_per_session)
            : engagement.associate_cost_per_session,
      contract_start: draft.contract_start === '' ? null : (draft.contract_start ?? engagement.contract_start),
      contract_end: draft.contract_end === '' ? null : (draft.contract_end ?? engagement.contract_end),
    };

    setSavingAdminEngagementId(key);
    setAdminEngagementSaveNoteById((prev) => ({ ...prev, [key]: 'Saving...' }));
    try {
      await updateCoachingEngagement(engagement.id, payload);
      setStatus(`Updated coachee record: ${payload.name}.`);
      setAdminEngagementDraftById((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
      setAdminEngagementSaveNoteById((prev) => ({
        ...prev,
        [key]: `Saved ${new Date().toLocaleTimeString()}`,
      }));
      await refresh();
    } catch (error) {
      setAdminEngagementSaveNoteById((prev) => ({ ...prev, [key]: `Save failed: ${error.message}` }));
      setStatus(error.message);
    } finally {
      setSavingAdminEngagementId('');
    }
  }

  async function onSaveAdminSession(session, options = {}) {
    const skipRefresh = Boolean(options.skipRefresh);
    const key = String(session.id);
    const draft = adminSessionDraftById[key] || {};
    const targetEngagementId = draft.engagement_id ?? session.engagement_id;
    const targetEngagement = coachingEngagementById[String(targetEngagementId)] || null;
    if (Boolean(draft.lcp_debrief ?? session.lcp_debrief) && !targetEngagement?.lcp_debrief_enabled) {
      setStatus('Cannot tick LCP de-brief: selected engagement has no LCP entitlement.');
      return false;
    }
    const payload = {
      engagement_id: targetEngagementId,
      session_date: draft.session_date ?? session.session_date,
      session_type: draft.session_type ?? session.session_type,
      lcp_debrief: Boolean(draft.lcp_debrief ?? session.lcp_debrief),
      lcp_debrief_date: Boolean(draft.lcp_debrief ?? session.lcp_debrief)
        ? (draft.lcp_debrief_date ?? session.lcp_debrief_date ?? null)
        : null,
      duration_mins: Number(draft.duration_mins ?? session.duration_mins ?? 60),
      delivery_mode: String(draft.delivery_mode ?? session.delivery_mode ?? 'video'),
      invoiced_to_adapsys: Boolean(draft.invoiced_to_adapsys ?? session.invoiced_to_adapsys),
      notes: draft.notes ?? session.notes ?? '',
    };

    setSavingAdminSessionId(key);
    try {
      await updateCoachingSession(session.id, payload);
      setStatus(`Updated session: ${formatDateAu(payload.session_date)}.`);
      setAdminSessionDraftById((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
      if (!skipRefresh) {
        await refresh();
      }
      return true;
    } catch (error) {
      setStatus(error.message);
      return false;
    } finally {
      setSavingAdminSessionId('');
    }
  }

  async function onSaveAllAdminSessions() {
    const sessionsToSave = filteredAdminSessions.filter((session) => Boolean(adminSessionDraftById[String(session.id)]));
    if (!sessionsToSave.length) {
      setStatus('No edited session rows to save.');
      return;
    }

    setIsSavingAllAdminSessions(true);
    setStatus(`Saving ${sessionsToSave.length} edited session row(s)...`);

    let successCount = 0;
    const failedRows = [];
    for (const session of sessionsToSave) {
      const saved = await onSaveAdminSession(session, { skipRefresh: true });
      if (saved) {
        successCount += 1;
      } else {
        failedRows.push(formatDateAu(session.session_date));
      }
    }

    try {
      if (successCount > 0) {
        await refresh();
      }
      if (failedRows.length) {
        setStatus(
          `Saved ${successCount}/${sessionsToSave.length} edited session row(s). Failed: ${failedRows.slice(0, 3).join(', ')}`
        );
      } else {
        setStatus(`Saved ${successCount} edited session row(s).`);
      }
    } finally {
      setIsSavingAllAdminSessions(false);
    }
  }

  async function onAttachExpenseReceipt(expenseId) {
    const key = String(expenseId);
    const draft = receiptDraftByExpenseId[key] || {};
    const receiptUrl = (draft.receipt_url || '').trim();
    const receiptThumb = (draft.receipt_thumb_url || '').trim();

    if (!receiptUrl) {
      setStatus('Please paste a receipt URL before attaching.');
      return;
    }

    setAttachingReceiptExpenseId(key);
    try {
      await updateExpenseReceipt(expenseId, {
        receipt_url: receiptUrl,
        receipt_thumb_url: receiptThumb || null,
      });
      setStatus('Receipt attached to existing expense.');
      setReceiptDraftByExpenseId((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setAttachingReceiptExpenseId('');
    }
  }

  async function applySessionMode(nextRole, nextEmail, options = {}) {
    const normalizedRole = (nextRole || 'admin').trim().toLowerCase();
    const normalizedEmail = (nextEmail || '').trim().toLowerCase();
    const targetTabId = options.targetTabId || '';
    const statusPrefix = options.statusPrefix || 'Session mode set';

    if (normalizedRole === 'consultant' && !normalizedEmail) {
      setStatus('Consultant mode needs a consultant email.');
      return;
    }

    localStorage.setItem('adapsys_user_role', normalizedRole);
    localStorage.setItem('adapsys_user_email', normalizedEmail || DEFAULT_ADMIN_EMAIL);

    setSessionRole(normalizedRole);
    setSessionEmail(normalizedEmail || DEFAULT_ADMIN_EMAIL);

    setExpenseForm((prev) => ({
      ...prev,
      submitted_by_role: normalizedRole === 'consultant' ? 'consultant' : 'admin',
      submitted_by_email:
        normalizedRole === 'consultant'
          ? normalizedEmail
          : normalizedEmail || prev.submitted_by_email,
      trip_id: '',
    }));
    setExpenseContextClientFilter('');
    setExpenseContextConsultantFilter(normalizedRole === 'consultant' ? normalizedEmail : '');

    if (targetTabId) {
      setActiveScreenTabId(targetTabId);
    }
    setStatus(`${statusPrefix} to ${normalizedRole}: ${normalizedEmail || DEFAULT_ADMIN_EMAIL}`);
    await refresh();
  }

  async function onApplySession() {
    await applySessionMode(sessionRole, sessionEmail);
  }

  async function onSelectSessionProfile(profileId) {
    setSelectedSessionProfileId(profileId);
    if (!profileId) return;
    if (profileId === 'consultant-auto') {
      const preferredEmail = String(orderedConsultants[0]?.email || sessionEmail || '').trim().toLowerCase();
      if (!preferredEmail) {
        setStatus('No consultant email found. Add a consultant in lookups first.');
        return;
      }
      await applySessionMode('consultant', preferredEmail, {
        targetTabId: 'submit-expense',
        statusPrefix: 'Consultant profile ready',
      });
      return;
    }
    const profile = SESSION_PROFILE_OPTIONS.find((option) => option.id === profileId);
    if (!profile) return;
    await applySessionMode(profile.role, profile.email, {
      targetTabId: 'submit-expense',
      statusPrefix: `${profile.label} ready`,
    });
  }

  async function onRunReminderAutomation(options = {}) {
    const dryRun = typeof options.dryRun === 'boolean' ? options.dryRun : automationDryRun;
    try {
      const rows = await runReminderAutomation({ dry_run: dryRun });
      if (!dryRun) {
        const reminderLastSentData = await listReminderLastSent();
        const reminderByTripId = {};
        reminderLastSentData.forEach((row) => {
          const key = String(row.trip_id || '');
          if (!key) return;
          reminderByTripId[key] = {
            last_sent_at: row.last_sent_at,
            reminder_type: row.reminder_type,
          };
        });
        setReminderLastSentByTripId(reminderByTripId);
      }
      const sentCount = rows.filter((row) => row.sent).length;
      const consultantCount = new Set(rows.map((row) => String(row.consultant_email || '').toLowerCase()).filter(Boolean)).size;
      setStatus(
        dryRun
          ? `Reminder preview found ${rows.length} event(s) for ${consultantCount} consultant(s).`
          : `Reminder automation sent ${sentCount}/${rows.length} email event(s) for ${consultantCount} consultant(s).`
      );
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function onRunCeoSignoff() {
    try {
      const rows = await runCeoSignoffAutomation({ dry_run: automationDryRun });
      setStatus(`Admin sign-off automation processed ${rows.length} project(s).`);
    } catch (error) {
      setStatus(error.message);
    }
  }

  useEffect(() => {
    if (!categoryOptions.includes(expenseForm.category)) {
      setExpenseForm((prev) => ({ ...prev, category: categoryOptions[0] || '' }));
    }
  }, [categoryOptions, expenseForm.category]);

  useEffect(() => {
    setAtoRateDraftById((prev) => {
      const next = { ...prev };
      atoRates.forEach((rate) => {
        const key = String(rate.id);
        next[key] = {
          breakfast_aud: rate.breakfast_aud,
          lunch_aud: rate.lunch_aud,
          dinner_aud: rate.dinner_aud,
          incidental_midpoint_aud: rate.incidental_midpoint_aud || 0,
          tax_year: normalizeFinancialYearLabel(rate.tax_year),
          active: rate.active,
        };
      });
      return next;
    });
  }, [atoRates]);

  useEffect(() => {
    if (!expenseForm.trip_id) return;
    const selectedTrip = trips.find((trip) => String(trip.id) === String(expenseForm.trip_id));
    if (!selectedTrip) return;
    const currency = currencyForCountry(selectedTrip.destination_country);
    setExpenseForm((prev) => ({
      ...prev,
      currency_local: currency,
      gst_applicable: currency === 'AUD',
      exchange_rate: currency === 'AUD' ? '1' : prev.exchange_rate === '1' ? '' : prev.exchange_rate,
    }));
  }, [expenseForm.trip_id, trips]);

  useEffect(() => {
    if (expenseForm.submitted_by_role !== 'consultant') return;
    if (!projectConsultantOptions.length) return;

    const availableEmails = projectConsultantOptions.map((option) => option.email);
    const preferredSessionEmail = (sessionEmail || '').toLowerCase();

    setExpenseForm((prev) => {
      if (prev.submitted_by_role !== 'consultant') return prev;
      const currentEmail = String(prev.submitted_by_email || '').toLowerCase();
      const fallbackEmail =
        isConsultantSession && availableEmails.includes(preferredSessionEmail)
          ? preferredSessionEmail
          : '';
      const nextEmail = availableEmails.includes(currentEmail) ? currentEmail : fallbackEmail;
      if (nextEmail === currentEmail) return prev;
      return {
        ...prev,
        submitted_by_email: nextEmail,
      };
    });
  }, [expenseForm.submitted_by_role, isConsultantSession, projectConsultantOptions, sessionEmail]);

  useEffect(() => {
    if (!expenseForm.trip_id || !projectConsultantOptions.length) return;
    setExpenseForm((prev) => {
      const current = String(prev.submitted_by_email || '').toLowerCase();
      const allowed = projectConsultantOptions.map((option) => String(option.email || '').toLowerCase());
      if (allowed.includes(current)) return prev;
      return {
        ...prev,
        submitted_by_email: isConsultantSession ? allowed[0] || prev.submitted_by_email : '',
      };
    });
  }, [expenseForm.trip_id, isConsultantSession, projectConsultantOptions]);

  useEffect(() => {
    if (expenseForm.category !== 'per_diem') return;
    setExpenseForm((prev) => {
      if (prev.per_diem_bulk_mode) return prev;
      return {
        ...prev,
        per_diem_bulk_mode: true,
        per_diem_start_date: prev.per_diem_start_date || prev.expense_date,
        per_diem_end_date: prev.per_diem_end_date || prev.expense_date,
      };
    });
  }, [expenseForm.category]);

  useEffect(() => {
    if (!isConsultantSession) return;
    setExpenseForm((prev) => ({
      ...prev,
      submitted_by_role: 'consultant',
      submitted_by_email: sessionEmail || prev.submitted_by_email,
      trip_id: prev.trip_id || expenseTripOptions[0]?.id || '',
    }));
  }, [expenseTripOptions, isConsultantSession, sessionEmail]);

  useEffect(() => {
    if (!editingProjectId) return;
    const selectedProject = trips.find((trip) => String(trip.id) === String(editingProjectId));
    if (!selectedProject) return;

    setTripForm({
      name: selectedProject.name || '',
      consultant_email: selectedProject.consultant_email || '',
      assigned_consultants: selectedProject.assigned_consultants || [],
      client_name: selectedProject.client_name || '',
      program_name: selectedProject.program_name || '',
      project_start_date: selectedProject.project_start_date || '',
      project_end_date: selectedProject.project_end_date || '',
      destination_country: selectedProject.destination_country || 'Australia',
      destination_city: selectedProject.destination_city || '',
      departure_date: selectedProject.departure_date || '',
      return_date: selectedProject.return_date || '',
      expense_report_required: Boolean(selectedProject.expense_report_required),
    });
    setTripStatus(`Editing project: ${selectedProject.name}`);
  }, [editingProjectId, trips]);

  async function onApproveExpense(expenseId) {
    try {
      await approveExpense(expenseId);
      setStatus('Expense approved.');
      await refresh();
    } catch (error) {
      setStatus(error.message);
    }
  }

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const linkEmail = (params.get('consultant_email') || params.get('email') || '').trim().toLowerCase();
      const roleParam = (params.get('role') || '').trim().toLowerCase();
      const consultantFlag = (params.get('consultant') || '').trim().toLowerCase();
      const lockParam = (params.get('lock_session') || '').trim().toLowerCase();
      const linkRole =
        roleParam === 'admin' || roleParam === 'consultant'
          ? roleParam
          : consultantFlag === '1' || consultantFlag === 'true'
            ? 'consultant'
            : '';

      if (linkEmail && linkRole) {
        localStorage.setItem('adapsys_user_role', linkRole);
        localStorage.setItem('adapsys_user_email', linkEmail);
        setSessionRole(linkRole);
        setSessionEmail(normalizeEmailIdentity(linkEmail));
        setSessionLockedFromLink(lockParam !== '0' && lockParam !== 'false');
        setExpenseForm((prev) => ({
          ...prev,
          submitted_by_role: linkRole === 'consultant' ? 'consultant' : 'admin',
          submitted_by_email: linkEmail,
        }));
        const roleLabel = linkRole === 'admin' ? 'Admin' : 'Consultant';
        setStatus(`${roleLabel} access link active for ${linkEmail}.`);
      }
    }

    refresh();
  }, []);

  useEffect(() => {
    let isCancelled = false;

    async function refreshLookupOptionsOnly() {
      const [consultantsResult, coachesResult, clientProgramsResult] = await Promise.allSettled([
        listConsultants(),
        listCoaches(),
        listClientPrograms(),
      ]);

      if (isCancelled) return;

      const consultantsData = consultantsResult.status === 'fulfilled' && Array.isArray(consultantsResult.value)
        ? consultantsResult.value
        : [];
      const coachesData = coachesResult.status === 'fulfilled' && Array.isArray(coachesResult.value)
        ? coachesResult.value
        : [];
      const clientProgramsData = clientProgramsResult.status === 'fulfilled' && Array.isArray(clientProgramsResult.value)
        ? clientProgramsResult.value
        : [];

      if (consultantsData.length > 0) {
        setConsultants(consultantsData);
      }
      if (coachesData.length > 0) {
        setCoaches(coachesData);
      }
      if (clientProgramsData.length > 0) {
        setClientPrograms(clientProgramsData);
      }

      if (consultantsData.length > 0 || coachesData.length > 0 || clientProgramsData.length > 0) {
        setAdminLookupDrafts((prev) => ({
          consultants:
            consultantsData.length > 0 ? JSON.stringify(consultantsData, null, 2) : prev.consultants,
          coaches: coachesData.length > 0 ? JSON.stringify(coachesData, null, 2) : prev.coaches,
          clientPrograms:
            clientProgramsData.length > 0 ? JSON.stringify(clientProgramsData, null, 2) : prev.clientPrograms,
        }));
      }
    }

    refreshLookupOptionsOnly();

    return () => {
      isCancelled = true;
    };
  }, [sessionRole, sessionEmail]);

  useEffect(() => {
    function onStorageChange(event) {
      if (!event.key || !['adapsys_user_role', 'adapsys_user_email'].includes(event.key)) {
        return;
      }

      const nextRole = (localStorage.getItem('adapsys_user_role') || 'admin').trim().toLowerCase();
      const nextEmail = normalizeEmailIdentity(localStorage.getItem('adapsys_user_email') || DEFAULT_ADMIN_EMAIL);

      setSessionRole(nextRole);
      setSessionEmail(nextEmail);
      setStatus(`Session updated in another tab: ${nextRole} (${nextEmail}).`);
      refresh();
    }

    window.addEventListener('storage', onStorageChange);
    return () => window.removeEventListener('storage', onStorageChange);
  }, []);

  useEffect(() => {
    if (visibleScreenTabs.some((tab) => tab.id === activeScreenTabId)) return;
    setActiveScreenTabId(visibleScreenTabs[0]?.id || 'session-mode');
  }, [activeScreenTabId, visibleScreenTabs]);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const root = document.documentElement;
    const syncHeaderOffset = () => {
      const headerHeight = headerRef.current?.offsetHeight || 220;
      root.style.setProperty('--sticky-header-offset', `${headerHeight + 16}px`);
    };

    syncHeaderOffset();
    window.addEventListener('resize', syncHeaderOffset);
    return () => window.removeEventListener('resize', syncHeaderOffset);
  }, [
    visibleScreenTabs.length,
    dashboardMetrics.activeCoachees,
    dashboardMetrics.tendersClosingSoon,
    isCoachOnlySession,
  ]);

  async function onCreateTrip(event) {
    event.preventDefault();
    setIsCreatingTrip(true);
    setTripStatus(editingProjectId ? 'Updating activity...' : 'Creating activity...');
    try {
      const payload = {
        ...tripForm,
        departure_date: tripForm.departure_date || tripForm.project_start_date || null,
        return_date: tripForm.return_date || tripForm.project_end_date || null,
      };
      const savedProject = editingProjectId
        ? await updateTrip(editingProjectId, payload)
        : await createTrip(payload);

      setIsCreatingTrip(false);
      setStatus(
        editingProjectId
          ? `Activity updated: ${savedProject.name}.`
          : `Activity created: ${savedProject.name}. Ready to submit expenses.`
      );
      setTripStatus(
        editingProjectId ? `Updated activity: ${savedProject.name}.` : `Created activity: ${savedProject.name}.`
      );
      setExpenseForm((prev) => ({
        ...prev,
        trip_id: String(savedProject.id || ''),
        submitted_by_email:
          prev.submitted_by_role === 'consultant'
            ? savedProject.consultant_email || prev.submitted_by_email
            : prev.submitted_by_email,
      }));
      if (!editingProjectId) {
        setTripForm((prev) => ({ ...prev, name: '', destination_city: '', expense_report_required: false }));
      }
      await refresh();
    } catch (error) {
      setIsCreatingTrip(false);
      const message = error?.message === 'Failed to fetch'
        ? 'Failed to fetch. Confirm backend is running at http://127.0.0.1:8000.'
        : error.message;
      setTripStatus(message);
      setStatus(error.message);
    }
  }

  async function onCreateExpense(event) {
    event.preventDefault();
    setExpenseValidationActive(true);
    if (expenseValidation.orderedMissingKeys.length) {
      setExpenseStatus(`Complete required fields: ${expenseValidation.orderedMissingLabels.join(', ')}.`);
      focusNextExpenseField();
      return;
    }

    const normalizedCategory = String(expenseForm.category || '').toLowerCase();
    const descriptionEmpty = !String(expenseForm.description || '').trim();
    const needsDescription = isConsultantSession && normalizedCategory !== 'per_diem';
    if (needsDescription && descriptionEmpty && typeof window !== 'undefined') {
      const proceed = window.confirm(
        'This expense has no description. Finance often has to chase missing descriptions at month end. Submit anyway?'
      );
      if (!proceed) {
        setExpenseStatus('Submission cancelled. Add a short description and resubmit.');
        return;
      }
    }

    setIsSubmittingExpense(true);
    setExpenseStatus('Submitting expense...');
    try {
      const perDiemClaimNotes =
        expenseForm.category === 'per_diem'
          ? [
              'Per diem claim sheet',
              `Meal rates: Breakfast ${formatAud(perDiemClaimBreakdown.breakfastUnit)}, Lunch ${formatAud(perDiemClaimBreakdown.lunchUnit)}, Dinner ${formatAud(perDiemClaimBreakdown.dinnerUnit)}`,
              'Incidental policy: applies to all travel days except the trip end date.',
              tripPerDiemLastDate ? `Trip end date (no incidental): ${formatDateAu(tripPerDiemLastDate)}` : null,
              `Incidental midpoint/day: ${formatAud(perDiemClaimBreakdown.incidentalMidpoint)}`,
              `Incidental eligible days: ${incidentalEligibleDays}`,
              'Per diem timesheet:',
              ...perDiemDayClaimRows.map((row) =>
                `${formatDateAu(row.isoDate)} · Breakfast ${row.breakfastClaimed ? formatAud(row.breakfastAmount) : '—'} · Lunch ${row.lunchClaimed ? formatAud(row.lunchAmount) : '—'} · Dinner ${row.dinnerClaimed ? formatAud(row.dinnerAmount) : '—'} · Incidental ${row.incidentalApplies ? formatAud(row.incidentalAmount) : '—'} · Day total ${formatAud(row.totalAmount)}`
              ),
              `Incidental subtotal: ${formatAud(perDiemClaimBreakdown.incidentalTotal)}`,
              `Claim total: ${formatAud(
                isBulkPerDiemMode ? perDiemClaimBreakdown.bulkGrandTotal : perDiemClaimBreakdown.singleDayTotal
              )}`,
            ]
              .filter(Boolean)
              .join('\n')
          : '';

      const mergedNotes = [expenseForm.notes, perDiemClaimNotes]
        .map((item) => (item || '').trim())
        .filter(Boolean)
        .join('\n\n');

      const flightNotes =
        expenseForm.category === 'flights' || expenseForm.category === 'flight'
          ? [
              expenseForm.flight_route_from
                ? `Flight from: ${expenseForm.flight_route_from}`
                : null,
              expenseForm.flight_route_to
                ? `Flight to: ${expenseForm.flight_route_to}`
                : null,
              expenseForm.flight_is_return_ticket && expenseForm.flight_return_from
                ? `Return from: ${expenseForm.flight_return_from}`
                : null,
              expenseForm.flight_is_return_ticket && expenseForm.flight_return_to
                ? `Return to: ${expenseForm.flight_return_to}`
                : null,
              `Return ticket: ${expenseForm.flight_is_return_ticket ? 'Yes' : 'No'}`,
              expenseForm.flight_is_return_ticket
                ? `Boarding passes expected: ${Number(expenseForm.flight_boarding_pass_count || 1) >= 2 ? '2 (outbound + return)' : '1'}`
                : null,
            ]
              .filter(Boolean)
              .join('\n')
          : '';

      const composedNotes = [mergedNotes, flightNotes]
        .map((item) => (item || '').trim())
        .filter(Boolean)
        .join('\n\n');
      const userDescription = String(expenseForm.description || '').trim();
      const generatedDescription = String(standardDescriptorPreview || '').trim();
      const resolvedDescription = userDescription || generatedDescription || null;

      const submitDates = isBulkPerDiemMode ? bulkPerDiemDates : [expenseForm.expense_date];
      if (!submitDates.length) {
        setExpenseStatus('Set a valid per diem date range (start/end) to submit multiple days.');
        setIsSubmittingExpense(false);
        return;
      }

      const normalizedTripId = String(expenseForm.trip_id || '');
      const normalizedSubmitter = String(expenseForm.submitted_by_email || '').toLowerCase();
      const normalizedCategory = String(expenseForm.category || '').toLowerCase();
      const isFlightCategory = ['flights', 'flight'].includes(normalizedCategory);
      const consultantReceiptKind = String(expenseForm.receipt_kind || '').toLowerCase();
      const effectiveReceiptKind = isConsultantSession
        ? (isFlightCategory
          ? (consultantReceiptKind === 'boarding_pass' ? 'boarding_pass' : 'invoice')
          : 'general')
        : String(expenseForm.receipt_kind || 'general');
      const parsedReimbursable = expenseForm.reimbursement_override_enabled && String(expenseForm.reimbursable_amount_local || '').trim()
        ? Number(expenseForm.reimbursable_amount_local)
        : null;

      const potentialDuplicates = expenses.filter((existing) => {
        const sameTrip = String(existing.trip_id || '') === normalizedTripId;
        const samePerson =
          String(existing.submitted_by_email || '').toLowerCase() === normalizedSubmitter;
        const sameCategory = String(existing.category || '').toLowerCase() === normalizedCategory;
        const sameDate = submitDates.includes(String(existing.expense_date || ''));
        return sameTrip && samePerson && sameCategory && sameDate;
      });

      if (potentialDuplicates.length && typeof window !== 'undefined') {
        const duplicateDates = Array.from(
          new Set(potentialDuplicates.map((row) => String(row.expense_date || '')).filter(Boolean))
        ).sort();
        const duplicateDatesLabel = duplicateDates.map((value) => formatDateAu(value));
        const proceed = window.confirm(
          `Possible duplicate claim detected for ${duplicateDatesLabel.join(', ')} (${normalizedCategory}). Continue anyway?`
        );
        if (!proceed) {
          setExpenseStatus('Submission cancelled to avoid possible duplicate claim.');
          setIsSubmittingExpense(false);
          return;
        }
      }

      if (parsedReimbursable !== null) {
        if (!Number.isFinite(parsedReimbursable) || parsedReimbursable < 0) {
          setExpenseStatus('Reimbursable amount must be 0 or greater.');
          setIsSubmittingExpense(false);
          return;
        }
        const amountLocal = Number(expenseForm.amount_local || 0);
        if (Number.isFinite(amountLocal) && parsedReimbursable > amountLocal) {
          setExpenseStatus('Reimbursable amount cannot be greater than total amount.');
          setIsSubmittingExpense(false);
          return;
        }
      }

      const {
        per_diem_bulk_mode,
        per_diem_start_date,
        per_diem_end_date,
        flight_route_from,
        flight_route_to,
        flight_return_from,
        flight_return_to,
        flight_is_return_ticket,
        flight_boarding_pass_count,
        descriptor_from,
        descriptor_to,
        descriptor_activity,
        reimbursement_override_enabled,
        reimbursable_percent,
        ...expensePayload
      } = expenseForm;

      await Promise.all(
        submitDates.map((expenseDate) => {
          const perDiemRow =
            perDiemDayClaimRows.find((row) => row.isoDate === expenseDate) ||
            null;
          const incidentalApplied = perDiemRow?.incidentalApplies || false;
          const incidentalForEntry = incidentalApplied ? perDiemClaimBreakdown.incidentalMidpoint : 0;
          const perDiemEntryTotal = Number(
            (perDiemRow ? perDiemRow.totalAmount : 0).toFixed(2)
          );
          const entryNotes =
            expenseForm.category === 'per_diem'
              ? [
                  composedNotes,
                  `Breakfast claimed: ${perDiemRow?.breakfastClaimed ? 'Yes' : 'No'}${perDiemRow?.breakfastClaimed ? ` (${formatAud(perDiemRow.breakfastAmount)})` : ''}`,
                  `Lunch claimed: ${perDiemRow?.lunchClaimed ? 'Yes' : 'No'}${perDiemRow?.lunchClaimed ? ` (${formatAud(perDiemRow.lunchAmount)})` : ''}`,
                  `Dinner claimed: ${perDiemRow?.dinnerClaimed ? 'Yes' : 'No'}${perDiemRow?.dinnerClaimed ? ` (${formatAud(perDiemRow.dinnerAmount)})` : ''}`,
                  `Incidental auto-applied: ${incidentalApplied ? 'Yes' : 'No'} (${formatAud(incidentalForEntry)})`,
                  `Per diem entry total: ${formatAud(perDiemEntryTotal)}`,
                ]
                  .filter(Boolean)
                  .join('\n')
              : composedNotes || null;

          return createExpense({
            ...expensePayload,
            receipt_kind: effectiveReceiptKind,
            receipt_group_key: null,
            description: resolvedDescription,
            expense_date: expenseDate,
            amount_local:
              expenseForm.category === 'per_diem' ? perDiemEntryTotal : Number(expenseForm.amount_local),
            reimbursable_amount_local:
              expenseForm.category === 'per_diem'
                ? null
                : parsedReimbursable,
            exchange_rate: Number(expenseForm.exchange_rate),
            receipt_url: expenseForm.no_receipt ? null : expenseForm.receipt_url || null,
            receipt_thumb_url: expenseForm.no_receipt
              ? null
              : expenseForm.receipt_thumb_url || expenseForm.receipt_url || null,
            no_receipt_reason: expenseForm.no_receipt
              ? expenseForm.no_receipt_reason || 'Receipt pending upload'
              : expenseForm.receipt_url
                ? null
                : 'Receipt pending upload',
            notes: entryNotes,
          });
        })
      );
      const submittedBy =
        projectConsultantOptions.find(
          (option) => option.email === String(expenseForm.submitted_by_email || '').toLowerCase()
        )?.label || expenseForm.submitted_by_email;
      setStatus(
        isBulkPerDiemMode
          ? `${submitDates.length} per diem entries submitted for ${submittedBy || 'selected consultant'}.`
          : `Expense submitted for ${submittedBy || 'selected consultant'}.`
      );
      setExpenseStatus(
        isBulkPerDiemMode
          ? `Submitted ${submitDates.length} day(s). Receipt can be uploaded later if needed.`
          : 'Submitted. Receipt can be uploaded later if needed.'
      );
      setExpenseValidationActive(false);
      setExpenseForm((prev) => ({
        ...INITIAL_EXPENSE_FORM,
        submitted_by_role: prev.submitted_by_role,
        submitted_by_email: isConsultantSession ? prev.submitted_by_email : '',
      }));
      setPerDiemMealsByDate({});
      setExpenseContextClientFilter('');
      setExpenseContextConsultantFilter(isConsultantSession ? normalizeEmailIdentity(sessionEmail || '') : '');
      await refresh();
    } catch (error) {
      const message =
        error?.message === 'Failed to fetch'
          ? 'Cannot reach backend (http://127.0.0.1:8000). Start backend and retry.'
          : error.message;
      setExpenseStatus(message);
      setStatus(error.message);
    } finally {
      setIsSubmittingExpense(false);
    }
  }

  async function onIntakeEmailReceipt(event) {
    event.preventDefault();
    try {
      await intakeEmailReceipt({
        ...emailIntakeForm,
        amount_local: Number(emailIntakeForm.amount_local || 0),
        exchange_rate: Number(emailIntakeForm.exchange_rate),
        receipt_thumb_url: emailIntakeForm.receipt_thumb_url || null,
        expense_date: emailIntakeForm.expense_date || null,
      });
      setStatus('Emailed receipt added to Admin draft queue.');
      setEmailIntakeForm((prev) => ({
        ...prev,
        receipt_url: '',
        receipt_thumb_url: '',
        description: '',
        supplier: '',
        receipt_group_key: '',
        amount_local: '',
        notes: '',
      }));
      await refresh();
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function onPreviewExpensePack() {
    const { start_date, end_date } = expenseReportFilters;
    if (!selectedReportTripId) {
      setStatus('Select a project to preview the client expense report. Create a project first if needed.');
      return;
    }
    if (start_date && end_date && start_date > end_date) {
      setReportPreviewStatus('Start date must be on or before end date.');
      return;
    }
    setIsPreviewingExpensePack(true);
    setReportPreviewStatus('Generating preview...');
    try {
      const html = await fetchExpensePackPreview(selectedReportTripId, {
        start_date,
        end_date,
      });
      setReportPreviewHtml(html);
      setReportPreviewStatus('Preview ready below.');
      setStatus('Client expense report preview generated.');
    } catch (error) {
      setReportPreviewStatus(error.message);
      setStatus(error.message);
    } finally {
      setIsPreviewingExpensePack(false);
    }
  }

  async function onDownloadExpensePackPdf() {
    const { start_date, end_date } = expenseReportFilters;
    if (!selectedReportTripId) {
      setStatus('Select a project to generate the PDF report. Create a project first if needed.');
      return;
    }
    if (start_date && end_date && start_date > end_date) {
      setReportPreviewStatus('Start date must be on or before end date.');
      return;
    }
    setIsDownloadingExpensePackPdf(true);
    try {
      const blob = await downloadExpensePackPdf(selectedReportTripId, {
        start_date,
        end_date,
      });
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `adapsys-australia-pacific-expenses-report-${selectedReportTripId}.pdf`;
      anchor.click();
      window.URL.revokeObjectURL(url);
      setStatus('Adapsys Australia Pacific - Expenses Report PDF download started.');
    } catch (error) {
      setStatus(error.message);
    } finally {
      setIsDownloadingExpensePackPdf(false);
    }
  }

  function scrollToSection(sectionId) {
    if (typeof window === 'undefined') return;
    const target = document.getElementById(sectionId);
    if (!target) return;

    const headerOffset = (headerRef.current?.offsetHeight || 220) + 16;
    const nextTop = target.getBoundingClientRect().top + window.scrollY - headerOffset;
    window.scrollTo({ top: Math.max(nextTop, 0), behavior: 'smooth' });
  }

  function onSelectScreenTab(sectionId) {
    setIsQuickHelpOpen(false);
    setActiveScreenTabId(sectionId);
    const isDesktopViewport = typeof window !== 'undefined' && window.innerWidth >= 980;
    if (!isTabbedLayout && isDesktopViewport) {
      setLayoutMode('tabs');
      if (typeof window !== 'undefined') {
        localStorage.setItem('adapsys_layout_mode', 'tabs');
      }
    }
    if (isTabbedLayout || isDesktopViewport) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    scrollToSection(sectionId);
  }

  function onChangeLayoutMode(nextMode) {
    setLayoutMode(nextMode);
    if (typeof window !== 'undefined') {
      localStorage.setItem('adapsys_layout_mode', nextMode);
      if (nextMode === 'tabs') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }
  }

  return (
    <div className="container" lang="en-AU">
      <header className="header" ref={headerRef}>
        <div className="header-arc-secondary" aria-hidden="true" />
        <div className="header-top">
          <div className="header-brand-spacer" aria-hidden="true" />
          <div className="header-brand-block">
            <h1>Adapsys Australia Pacific Portal</h1>
          </div>
          <div className="header-logo-slot">
            {dashboardLogoSrc ? (
              <img
                className="header-logo"
                src={dashboardLogoSrc}
                alt="Adapsys logo"
                onError={() => {
                  setDashboardLogoIndex((prev) =>
                    prev + 1 < dashboardLogoCandidates.length ? prev + 1 : prev
                  );
                }}
              />
            ) : (
              <div className="header-logo-fallback" aria-label="Adapsys logo fallback">
                A
              </div>
            )}
          </div>
        </div>
        <div className="kpi-grid">
          <div className="kpi-chip">
            <span className="kpi-label">Approved</span>
            <strong>{dashboardMetrics.approvedCount}</strong>
          </div>
          <div
            className="kpi-chip kpi-chip-pending"
            data-help="Submitted expenses waiting for finance/admin review."
          >
            <span className="kpi-label">Expense Pending</span>
            <strong>{dashboardMetrics.pendingCount}</strong>
          </div>
          <div className="kpi-chip">
            <span className="kpi-label">Active Clients</span>
            <strong>{dashboardMetrics.activeClients}</strong>
          </div>
          <div className="kpi-chip">
            <span className="kpi-label">Coachees</span>
            <strong>{dashboardMetrics.activeCoachees}</strong>
          </div>
          <div className="kpi-chip">
            <span className="kpi-label">Tenders ≤14d</span>
            <strong>{dashboardMetrics.tendersClosingSoon}</strong>
          </div>
          <div className="kpi-chip">
            <span className="kpi-label">Outstanding Inv.</span>
            <strong>{formatAud(portfolioInvoicing.outstandingAud)}</strong>
          </div>
        </div>
        <div className="mobile-screen-nav header-nav-strip header-nav-attached">
          <div className="screen-nav-grid">
            {visibleScreenTabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                className={`screen-tab ${activeScreenTabId === tab.id ? 'is-active' : ''}`}
                onClick={() => onSelectScreenTab(tab.id)}
              >
                <span>{tab.label}</span>
                {PHASE2_TAB_IDS.has(tab.id) ? <span className="screen-tab-phase">Phase 2</span> : null}
              </button>
            ))}
          </div>
        </div>
        <div className="header-assist-row">
          <div className="quick-help-badge" ref={quickHelpRef}>
            <button
              type="button"
              className="quick-help-trigger"
              aria-expanded={isQuickHelpOpen}
              aria-controls="header-quick-help-popover"
              onClick={() => setIsQuickHelpOpen((prev) => !prev)}
            >
              Help
            </button>
            {isQuickHelpOpen ? (
              <div
                id="header-quick-help-popover"
                className="quick-help-popover"
                role="region"
                aria-label="Quick help for current screen"
              >
                <h3>{activeQuickHelp.title}</h3>
                <ol>
                  {activeQuickHelp.steps.map((step) => (
                    <li key={`quick-help-${activeScreenTabId}-${step}`}>{step}</li>
                  ))}
                </ol>
                <button type="button" className="secondary" onClick={() => onSelectScreenTab('help')}>
                  Open Full Help Tab
                </button>
              </div>
            ) : null}
          </div>
        </div>
        <div className="header-layout-toggle">
          <span className="header-layout-label">View</span>
          <div className="header-layout-buttons">
            <button
              type="button"
              className={`screen-tab ${layoutMode === 'tabs' ? 'is-active' : ''}`}
              onClick={() => onChangeLayoutMode('tabs')}
            >
              Desktop Tabs
            </button>
            <button
              type="button"
              className={`screen-tab ${layoutMode === 'scroll' ? 'is-active' : ''}`}
              onClick={() => onChangeLayoutMode('scroll')}
            >
              Continuous Scroll
            </button>
          </div>
        </div>
        {isAdminSession ? (
          <div className="status demo-mode-banner">
            {isSimplifiedAdminDemoView
              ? 'Demo view active: only core modules are visible for a cleaner presentation.'
              : 'Builder view active: Phase 2 modules are visible for testing.'}
            {canManagePhase2Modules ? (
              <button
                type="button"
                className="secondary"
                style={{ width: 'auto', marginLeft: 8 }}
                onClick={() => setShowPhase2Modules((prev) => !prev)}
              >
                {showPhase2Modules ? 'Hide Phase 2 Modules' : 'Show Phase 2 Modules'}
              </button>
            ) : null}
          </div>
        ) : null}
      </header>

      {status ? (
        <section className="card" style={{ marginTop: 12 }}>
          <div className="status">{status}</div>
        </section>
      ) : null}

      <section id="session-mode" className="card" style={{ marginTop: 12, ...(sectionVisibilityStyle('session-mode') || {}) }}>
        <h2>Session Mode</h2>
        {sessionLockedFromLink ? (
          <div className="status">
            Session is locked from direct access link: {sessionRole} ({sessionEmail}). Remove `lock_session=1`
            from the link to re-enable manual switching.
          </div>
        ) : (
          <>
            <div>
              <label>Sign in as (quick profile)</label>
              <select value={selectedSessionProfileId} onChange={(e) => void onSelectSessionProfile(e.target.value)}>
                <option value="">Custom role/email (manual)</option>
                {SESSION_PROFILE_OPTIONS.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid">
              <div>
                <label>Role</label>
                <select value={sessionRole} onChange={(e) => setSessionRole(e.target.value)}>
                  <option value="admin">Admin</option>
                  <option value="consultant">Consultant</option>
                </select>
              </div>
              <div>
                <label>Email</label>
                <input
                  type="email"
                  list="demo-admin-email-presets"
                  value={sessionEmail}
                  onChange={(e) => setSessionEmail(e.target.value)}
                  placeholder="name@adapsysgroup.com"
                />
                <datalist id="demo-admin-email-presets">
                  {DEMO_ADMIN_EMAIL_PRESETS.map((email) => (
                    <option key={`demo-admin-${email}`} value={email} />
                  ))}
                </datalist>
              </div>
            </div>
            <button type="button" onClick={onApplySession} style={{ marginTop: 8 }}>
              Apply Session
            </button>
            <div className="status" style={{ marginTop: 8 }}>
              Profile dropdown applies one-step sign-in. Consultant mode shows only assigned projects.
            </div>
          </>
        )}
      </section>

      <section id="help" className="card help-shell" style={sectionVisibilityStyle('help')}>
        <h2>Help (Step-by-Step)</h2>
        <div className="status">
          Designed for occasional users. Follow each list in order. Keep this open while you work.
        </div>
        <div className="help-quick-checklist" role="note" aria-label="Quick help checklist">
          <strong>Before you start:</strong> sign in, select the correct role, and keep receipts ready in one folder.
        </div>
        <div className="help-guide-grid">
          <article className="help-guide-card">
            <h3>How to Submit an Expense (Simple)</h3>
            <ol className="help-step-list">
              <li>Open the <strong>Expenses</strong> tab.</li>
              <li>Complete <strong>1. Context</strong> (consultant + activity).</li>
              <li>Complete <strong>2. Claim details</strong> (category, date, amount).</li>
              <li>Complete <strong>3. Receipt evidence</strong> (upload file or mark no receipt with reason).</li>
              <li>Go to <strong>4. Finalise</strong> and click submit.</li>
            </ol>
            <div className="help-example-note">
              Example: Taxi from airport to hotel, AUD 48.00, add receipt photo, then submit.
            </div>
            {helpImageAvailable.expense ? (
              <img
                className="help-image-preview"
                src="/help/help-expense-flow.png"
                alt="Expense flow screenshot with steps 1 to 4"
                onError={() =>
                  setHelpImageAvailable((prev) =>
                    prev.expense ? { ...prev, expense: false } : prev
                  )
                }
              />
            ) : (
              <div className="help-image-placeholder" role="img" aria-label="Placeholder for expense process screenshot">
                <div className="help-image-title">Screenshot placeholder</div>
                <div>Add file: frontend/public/help/help-expense-flow.png</div>
              </div>
            )}
            <div className="help-guide-actions">
              <button type="button" className="secondary" onClick={() => onSelectScreenTab('submit-expense')}>
                Open Expenses
              </button>
            </div>
          </article>

          <article className="help-guide-card">
            <h3>How to Log Coaching (Simple)</h3>
            <ol className="help-step-list">
              <li>Open the <strong>Coaching</strong> tab.</li>
              <li>If consultant: click <strong>Log Session</strong> and fill date/outcome.</li>
              <li>If admin: use <strong>Batch Setup</strong> first for new coachees.</li>
              <li>Use <strong>Recent Coaching Sessions</strong> to check or edit.</li>
            </ol>
            <div className="help-example-note">
              Example: 60-minute completed session today, then confirm it appears in Recent Sessions.
            </div>
            {helpImageAvailable.coaching ? (
              <img
                className="help-image-preview"
                src="/help/help-coaching-flow.png"
                alt="Coaching flow screenshot for setup, logging, and recent sessions"
                onError={() =>
                  setHelpImageAvailable((prev) =>
                    prev.coaching ? { ...prev, coaching: false } : prev
                  )
                }
              />
            ) : (
              <div className="help-image-placeholder" role="img" aria-label="Placeholder for coaching process screenshot">
                <div className="help-image-title">Screenshot placeholder</div>
                <div>Add file: frontend/public/help/help-coaching-flow.png</div>
              </div>
            )}
            <div className="help-guide-actions">
              <button type="button" className="secondary" onClick={() => onSelectScreenTab('coaching-module')}>
                Open Coaching
              </button>
            </div>
          </article>
        </div>
      </section>

      {!isConsultantSession ? (
        <section className="card" style={sectionVisibilityStyle('submit-expense')}>
          <h2>Portfolio Expense Pipeline</h2>
          <div className="status">
            Outstanding: {portfolioInvoicing.outstandingCount} expenses · {formatAud(portfolioInvoicing.outstandingAud)}
          </div>
          <div className="status">
            Invoiced: {portfolioInvoicing.invoicedCount} expenses · {formatAud(portfolioInvoicing.invoicedAud)}
          </div>
        </section>
      ) : null}

      {!isConsultantSession ? (
        <section id="create-project" className="card" style={sectionVisibilityStyle('create-project')}>
          <h2>Activity Setup (Admin)</h2>
          <form onSubmit={onCreateTrip}>
            <div className="grid project-setup-row-four">
              <div>
                <label>Client / Agency</label>
                <input
                  list="client-options"
                  value={tripForm.client_name}
                  onChange={(e) => setTripForm({ ...tripForm, client_name: e.target.value })}
                  placeholder="Choose or type a client"
                  required
                />
              </div>
              <div>
              <label>Program (optional - can stay blank)</label>
              <input
                list="program-options"
                value={tripForm.program_name}
                onChange={(e) => setTripForm({ ...tripForm, program_name: e.target.value })}
                placeholder="Optional"
              />
            </div>
              <div>
              <label>Activity</label>
              <input
                value={tripForm.name}
                onChange={(e) => setTripForm({ ...tripForm, name: e.target.value })}
                required
              />
              </div>
              <div>
              <label>Edit Existing Activity (optional)</label>
              <select
                value={editingProjectId}
                onChange={(e) => {
                  setEditingProjectId(e.target.value);
                  if (!e.target.value) {
                    setTripStatus('Create mode: enter details for a new activity.');
                  }
                }}
              >
                <option value="">Create New Activity</option>
                {trips.map((trip) => (
                  <option key={trip.id} value={trip.id}>
                    Edit: {trip.name} — {formatClientProgramLabel(trip.client_name, trip.program_name)}
                  </option>
                ))}
              </select>
              </div>
            </div>
          <div className="status">Leave "Edit Existing Activity" blank when creating a new activity.</div>

          <div className="grid project-setup-row-four">
            <div>
              <label>Activity Start Date</label>
              <input
                type="date"
                value={tripForm.project_start_date}
                onChange={(e) =>
                  setTripForm({ ...tripForm, project_start_date: e.target.value })
                }
              />
            </div>
            <div>
              <label>Activity End Date</label>
              <input
                type="date"
                value={tripForm.project_end_date}
                onChange={(e) => setTripForm({ ...tripForm, project_end_date: e.target.value })}
              />
            </div>
            <div>
              <label>City (optional)</label>
              <input
                value={tripForm.destination_city}
                onChange={(e) =>
                  setTripForm({ ...tripForm, destination_city: e.target.value })
                }
                placeholder="Optional"
              />
            </div>
            <div>
              <label>Country</label>
              <select
                value={tripForm.destination_country}
                onChange={(e) =>
                  setTripForm({ ...tripForm, destination_country: e.target.value })
                }
              >
                {atoRates.map((rate) => (
                  <option key={rate.id} value={rate.country}>
                    {rate.country}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <label className="inline-checkbox">
            <input
              type="checkbox"
              checked={Boolean(tripForm.expense_report_required)}
              onChange={(e) =>
                setTripForm((prev) => ({
                  ...prev,
                  expense_report_required: e.target.checked,
                }))
              }
            />{' '}
            Expense report required for this activity
          </label>
          <div className="status">
            When enabled, assigned consultants will see this activity in their outstanding expense tracker once the activity end date passes.
          </div>

          <label>Assigned Consultants</label>
          <div className="consultant-roster-list">
            {orderedConsultants.map((consultant) => {
              const isSelected = tripForm.assigned_consultants.includes(consultant.email);
              return (
                <label key={consultant.email} className="consultant-roster-item">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={(e) => {
                      const nextRoster = e.target.checked
                        ? [...tripForm.assigned_consultants, consultant.email]
                        : tripForm.assigned_consultants.filter((email) => email !== consultant.email);
                      setTripForm((prev) => ({
                        ...prev,
                        assigned_consultants: Array.from(new Set(nextRoster)),
                      }));
                    }}
                  />{' '}
                  {consultant.name}
                </label>
              );
            })}
          </div>
          <div className="project-roster-actions" style={{ marginTop: 8, marginBottom: 8 }}>
            <button
              type="button"
              className="secondary"
              onClick={() =>
                setTripForm((prev) => ({
                  ...prev,
                  assigned_consultants: Array.from(new Set(allConsultantEmails)),
                }))
              }
            >
              Select All Consultants
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() =>
                setTripForm((prev) => ({
                  ...prev,
                  assigned_consultants: prev.consultant_email ? [prev.consultant_email] : [],
                }))
              }
            >
              Consultant Only
            </button>
            <div className="roster-lead-picker">
              <label>Consultant</label>
              <select
                value={tripForm.consultant_email}
                onChange={(e) =>
                  setTripForm((prev) => ({
                    ...prev,
                    consultant_email: e.target.value,
                    assigned_consultants: e.target.value
                      ? Array.from(new Set([e.target.value, ...prev.assigned_consultants.filter(Boolean)]))
                      : prev.assigned_consultants,
                  }))
                }
              >
                <option value="">No consultant selected</option>
                {orderedConsultants.map((consultant) => (
                  <option key={consultant.email} value={consultant.email}>
                    {consultant.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="status">
            Select everyone assigned to this activity. Consultants in this assigned list receive reminders.
          </div>

          <datalist id="client-options">
            {clientOptions.map((clientName) => (
              <option key={clientName} value={clientName}>
                {clientName}
              </option>
            ))}
          </datalist>
          <datalist id="program-options">
            {(tripForm.client_name ? programOptions : allProgramOptions).map((programName) => (
              <option key={programName} value={programName}>
                {programName}
              </option>
            ))}
          </datalist>

          <div className="status">
            Per diem preview: AUD {computedPerDiem.rate}/day x {computedPerDiem.nights} nights = AUD{' '}
            {computedPerDiem.total}
          </div>

          <button type="submit" disabled={isCreatingTrip}>
            {isCreatingTrip
              ? editingProjectId
                ? 'Updating Activity...'
                : 'Creating Activity...'
              : editingProjectId
                ? 'Update Activity'
                : 'Create Activity'}
          </button>
          {tripStatus ? <div className="status">{tripStatus}</div> : null}
        </form>
        </section>
      ) : null}

      <section id="submit-expense" className="card expense-shell" style={sectionVisibilityStyle('submit-expense')}>
        <h2>Submit Expense</h2>
        <div className="status expense-shell-guidance">
          {isConsultantSession
            ? 'Consultant quick flow: pick activity, category, date/amount, then add receipt and submit.'
            : 'Admin mode: choose an activity and consultant, then submit or review expenses.'}
        </div>
        <div className="status" style={{ marginBottom: 10 }}>
          <strong>Quick help on this page:</strong> 1) Complete Context, 2) Fill claim + receipt evidence, 3) Finalise and submit.
        </div>
        <div className="expense-external-tools" role="region" aria-label="External tool shortcuts">
          <div className="expense-external-tools-head">
            <strong>External tools</strong>
            <span className="status">Use these shortcuts to reduce duplicate entry and speed up handoffs.</span>
          </div>
          <div className="expense-external-tool-actions">
            {expenseExternalToolActions.map((action) => (
              <button
                key={action.id}
                type="button"
                className="secondary expense-external-tool-button"
                onClick={() => onOpenExternalTool(action.url, action.label)}
                disabled={!action.url}
              >
                {action.label}
              </button>
            ))}
          </div>
          <div className="status expense-external-tools-hint">
            Link keys: {XERO_EXPENSE_LINK_STORAGE_KEY}, {XERO_ADMIN_LINK_STORAGE_KEY}, {CTM_TRAVEL_LINK_STORAGE_KEY},{' '}
            {GOOGLE_CHAT_LINK_STORAGE_KEY}.
          </div>
        </div>
        <div className="workflow-priority-panel expense-priority-panel" role="region" aria-label="Expense priority workflow">
          <div className="workflow-priority-head">
            <strong>{isConsultantSession ? 'Consultant priority path' : 'Admin priority path'}</strong>
            <span className="status">Next best action: {expenseNextStep.label}</span>
            <span className="status workflow-progress-inline">Progress: {expenseCompletedStepCount}/4 steps ready</span>
          </div>
          <div className="workflow-step-list">
            <button
              type="button"
              className={`secondary workflow-step-button ${expenseNextStep.id === 'expense-step-context' ? 'is-active' : ''} ${expenseStepState.context ? 'is-complete' : ''}`}
              onClick={() => document.getElementById('expense-step-context')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
            >
              1. Context
            </button>
            <button
              type="button"
              className={`secondary workflow-step-button ${expenseNextStep.id === 'expense-step-claim' ? 'is-active' : ''} ${expenseStepState.claim ? 'is-complete' : ''}`}
              onClick={() => document.getElementById('expense-step-claim')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
            >
              2. Claim details
            </button>
            <button
              type="button"
              className={`secondary workflow-step-button ${expenseNextStep.id === 'expense-step-receipt' ? 'is-active' : ''} ${expenseStepState.receipt ? 'is-complete' : ''}`}
              onClick={() => document.getElementById('expense-step-receipt')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
            >
              3. Receipt evidence
            </button>
            <button
              type="button"
              className={`secondary workflow-step-button ${expenseNextStep.id === 'expense-step-submit' ? 'is-active' : ''} ${expenseStepState.submit ? 'is-complete' : ''}`}
              onClick={() => document.getElementById('expense-step-submit')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
            >
              4. Finalise
            </button>
          </div>
        </div>
        {!isConsultantSession && expenseForm.no_receipt_reason === 'Booked travel cost to be entered by admin' ? (
          <div className="expense-booked-travel-badge" role="status">
            <strong>Booked Travel Draft</strong>
            <span>
              This draft came from the travel booking queue. Add supplier, amount, and any receipt details before submitting.
            </span>
          </div>
        ) : null}
        <form
          onSubmit={onCreateExpense}
          className={`expense-submit-form ${isConsultantSession ? 'expense-submit-form-consultant' : ''}`}
        >
          <div className={`expense-form-kpis ${isConsultantSession ? 'expense-form-kpis-consultant' : 'expense-form-kpis-admin'}`}>
            <span className="expense-micro-chip">Outstanding expenses: {consultantOutstandingExpenseProjects.length}</span>
            <span className="expense-micro-chip">Available activities: {expenseTripOptions.length}</span>
            {!isConsultantSession ? <span className="expense-micro-chip">Assigned consultants: {projectConsultantOptions.length}</span> : null}
            <span className="expense-micro-chip">
              {expenseForm.no_receipt ? 'Receipt pending upload' : 'Receipt upload recommended'}
            </span>
          </div>

          <div id="expense-step-context" className={`expense-section expense-section-context ${isConsultantSession ? 'consultant-step-panel' : ''}`}>
            <h3 className="expense-section-title">1. Context</h3>
          <div className="expense-compact-row expense-compact-row-top">
            <div className="expense-field-consultant">
              <label>Consultant</label>
              {isConsultantSession ? (
                <input
                  value={displayNameFromEmail(sessionEmail) || sessionEmail || 'Consultant'}
                  readOnly
                />
              ) : (
                <select
                  ref={expenseConsultantRef}
                  value={expenseForm.submitted_by_email}
                  className={expenseValidationActive && expenseValidation.missing.consultant ? 'is-invalid' : ''}
                  onChange={(e) => {
                    const email = e.target.value;
                    setExpenseContextConsultantFilter(email);
                    setExpenseForm((prev) => ({ ...prev, submitted_by_email: email }));
                  }}
                  required
                >
                  <option value="">Select consultant</option>
                  {submitExpenseConsultantOptions.map((consultant) => (
                    <option key={`expense-consultant-${consultant.email}`} value={consultant.email}>
                      {consultant.name}
                    </option>
                  ))}
                </select>
              )}
              {expenseValidationActive && expenseValidation.missing.consultant ? (
                <div className="field-error">Pick the consultant submitting this claim.</div>
              ) : null}
            </div>

            <div className="expense-field-project">
              <label>Client</label>
              <select
                value={expenseContextClientFilter}
                onChange={(e) => setExpenseContextClientFilter(e.target.value)}
              >
                <option value="">All clients</option>
                {expenseContextClientOptions.map((clientName) => (
                  <option key={`expense-client-${clientName}`} value={clientName}>{clientName}</option>
                ))}
              </select>
            </div>

            <div className="expense-field-project">
              <label>Activity</label>
              <select
                ref={expenseProjectRef}
                value={expenseForm.trip_id}
                className={expenseValidationActive && expenseValidation.missing.trip ? 'is-invalid' : ''}
                onChange={(e) => {
                  const tripId = e.target.value;
                  const selectedTrip = trips.find((trip) => String(trip.id) === String(tripId));
                  const roster = Array.from(
                    new Set(
                      [selectedTrip?.consultant_email, ...(selectedTrip?.assigned_consultants || [])]
                        .filter(Boolean)
                        .map((email) => String(email).toLowerCase())
                    )
                  );
                  const fallbackConsultant =
                    isConsultantSession
                      ? (sessionEmail || '').toLowerCase()
                      : roster.includes(String(expenseForm.submitted_by_email || '').toLowerCase())
                        ? String(expenseForm.submitted_by_email || '').toLowerCase()
                        : '';

                  setExpenseForm((prev) => ({
                    ...prev,
                    trip_id: tripId,
                    submitted_by_email: fallbackConsultant,
                  }));
                  setExpenseContextClientFilter(String(selectedTrip?.client_name || '').trim());
                  setExpenseStatus('');
                }}
                required
              >
                <option value="">Select activity</option>
                {filteredExpenseTripOptions.map((trip) => (
                  <option key={trip.id} value={trip.id}>
                    {trip.name} — {formatClientProgramLabel(trip.client_name, trip.program_name)}
                  </option>
                ))}
              </select>
              {expenseValidationActive && expenseValidation.missing.trip ? (
                <div className="field-error">Select an activity to continue.</div>
              ) : null}
            </div>
          </div>
          <div className="status" style={{ marginTop: 8 }}>
            Selected Activity: {selectedExpenseTrip?.name || 'Not selected yet'}
          </div>

          <div className={`expense-top-meta-row ${isConsultantSession ? 'expense-top-meta-row-consultant' : ''}`}>
            {!isConsultantSession ? (
              <div className="expense-role-compact">
                <label>Submitted By</label>
                <select
                  value={expenseForm.submitted_by_role}
                  onChange={(e) => {
                    const role = e.target.value;
                    setExpenseForm((prev) => ({
                      ...prev,
                      submitted_by_role: role,
                    }));
                    setExpenseStatus('');
                  }}
                >
                  <option value="consultant">Consultant</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            ) : null}
            {!isConsultantSession ? (
              <>
                <div className="status expense-flow-hint">
                  Flow: choose consultant, client, activity, then complete claim details.
                </div>
                <button
                  type="button"
                  className="secondary expense-next-required"
                  onClick={() => {
                    setExpenseValidationActive(true);
                    focusNextExpenseField();
                  }}
                >
                  Jump to next required field
                </button>
              </>
            ) : null}
            {expenseValidationActive && expenseValidation.orderedMissingLabels.length ? (
              <div className="status expense-inline-summary">
                Missing: {expenseValidation.orderedMissingLabels.join(', ')}.
              </div>
            ) : null}
          </div>

          {!isConsultantSession && expenseForm.submitted_by_role === 'consultant' &&
            expenseForm.trip_id &&
            !projectConsultantOptions.length ? (
              <div className="status">No consultants are assigned to this activity yet. Update activity roster first.</div>
            ) : null}
          </div>

          <div id="expense-step-claim" className={`expense-section expense-section-claim ${isConsultantSession ? 'consultant-step-panel' : ''}`}>
            <h3 className="expense-section-title">2. Claim details</h3>
            <div className="status expense-claim-guidance">
              Enter route + amount details first, then proceed to receipt evidence.
            </div>

            <div className="expense-claim-head-grid" style={{ marginBottom: 8 }}>
              <div>
                <label>Category</label>
                <select
                  ref={expenseCategoryRef}
                  value={expenseForm.category}
                  onChange={(e) => {
                    const nextCategory = e.target.value;
                    setExpenseForm((prev) => {
                      const next = {
                        ...prev,
                        category: nextCategory,
                      };
                      if (nextCategory === 'per_diem') {
                        next.currency_local = 'AUD';
                        next.exchange_rate = '1';
                        next.gst_applicable = false;
                      }
                      if ((nextCategory === 'flights' || nextCategory === 'flight') && !prev.flight_route_to) {
                        const destinationCity = String(selectedExpenseTrip?.destination_city || '').trim();
                        if (destinationCity) next.flight_route_to = destinationCity;
                      }
                      if (nextCategory === 'flights' || nextCategory === 'flight') {
                        if (!prev.receipt_kind || prev.receipt_kind === 'general') {
                          next.receipt_kind = 'invoice';
                        }
                      } else if (['invoice', 'tax_invoice', 'itinerary', 'boarding_pass'].includes(String(prev.receipt_kind || ''))) {
                        next.receipt_kind = 'general';
                      }
                      return next;
                    });
                  }}
                >
                  {categoryOptions.map((option) => (
                    <option key={option} value={option}>
                      {formatTokenLabel(option)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label>Supplier</label>
                <input
                  list="expense-supplier-options"
                  value={expenseForm.supplier}
                  onChange={(e) => setExpenseForm({ ...expenseForm, supplier: e.target.value })}
                  placeholder={isConsultantSession ? 'e.g. Virgin Australia' : 'Admin supplier entry'}
                />
                <datalist id="expense-supplier-options">
                  {sortedExpenseSupplierOptions.map((option) => (
                    <option key={`supplier-${option}`} value={option} />
                  ))}
                </datalist>
              </div>
            </div>

            {!isConsultantSession && !['flights', 'flight'].includes(String(expenseForm.category || '').toLowerCase()) ? (
              <div className="grid" style={{ marginBottom: 8 }}>
                <div>
                  <label>From (standard)</label>
                  <input
                    list="expense-from-standard-options"
                    value={expenseForm.descriptor_from}
                    onChange={(e) => setExpenseForm({ ...expenseForm, descriptor_from: e.target.value })}
                    placeholder="Select or type from"
                  />
                  <datalist id="expense-from-standard-options">
                    {descriptorFromToOptions.map((option) => (
                      <option key={`from-${option}`} value={option} />
                    ))}
                  </datalist>
                </div>
                <div>
                  <label>To (standard)</label>
                  <input
                    list="expense-to-standard-options"
                    value={expenseForm.descriptor_to}
                    onChange={(e) => setExpenseForm({ ...expenseForm, descriptor_to: e.target.value })}
                    placeholder="Select or type to"
                  />
                  <datalist id="expense-to-standard-options">
                    {descriptorFromToOptions.map((option) => (
                      <option key={`to-${option}`} value={option} />
                    ))}
                  </datalist>
                </div>
                <div>
                  <label>Purpose (optional)</label>
                  <select
                    value={expenseForm.descriptor_activity}
                    onChange={(e) => setExpenseForm({ ...expenseForm, descriptor_activity: e.target.value })}
                  >
                    <option value="">No purpose tag</option>
                    {sortedStandardDescriptorActivityOptions.map((option) => (
                      <option key={`activity-${option}`} value={option}>{formatTokenLabel(option)}</option>
                    ))}
                  </select>
                </div>
              </div>
            ) : null}

            {expenseForm.category === 'flights' ? (
              <div className="expense-claim-subsection">
                <div className="status" style={{ marginBottom: 6 }}>
                  Flights workflow: select outbound airport route first. Tick return leg only when logging a return flight.
                </div>
                <div className="grid expense-flight-grid">
                  <div>
                    <label>Flight From (Outbound)</label>
                    <input
                      ref={expenseFlightFromRef}
                      list="expense-flight-from-options"
                      value={expenseForm.flight_route_from}
                      className={expenseValidationActive && expenseValidation.missing.flightFrom ? 'is-invalid' : ''}
                      onChange={(e) =>
                        setExpenseForm({ ...expenseForm, flight_route_from: e.target.value })
                      }
                      placeholder="Select or type departure"
                      required
                    />
                    <datalist id="expense-flight-from-options">
                      {sortedFlightLocationOptions.map((location) => (
                        <option key={`from-${location}`} value={location} />
                      ))}
                    </datalist>
                    {expenseValidationActive && expenseValidation.missing.flightFrom ? (
                      <div className="field-error">Select a departure airport.</div>
                    ) : null}
                  </div>
                <div>
                  <label>Flight To (Outbound)</label>
                  <input
                    ref={expenseFlightToRef}
                    list="expense-flight-to-options"
                    value={expenseForm.flight_route_to}
                    className={expenseValidationActive && expenseValidation.missing.flightTo ? 'is-invalid' : ''}
                    onChange={(e) =>
                      setExpenseForm({ ...expenseForm, flight_route_to: e.target.value })
                    }
                    placeholder="Select or type destination"
                    required
                  />
                  <datalist id="expense-flight-to-options">
                    {sortedFlightLocationOptions.map((location) => (
                      <option key={`to-${location}`} value={location} />
                    ))}
                  </datalist>
                  {expenseValidationActive && expenseValidation.missing.flightTo ? (
                    <div className="field-error">Select a destination airport.</div>
                  ) : null}
                  <label className="inline-checkbox expense-return-leg-toggle">
                    <input
                      type="checkbox"
                      checked={expenseForm.flight_is_return_ticket}
                      onChange={(e) =>
                        setExpenseForm({
                          ...expenseForm,
                          flight_is_return_ticket: e.target.checked,
                          flight_return_from: e.target.checked ? (expenseForm.flight_route_to || '') : '',
                          flight_return_to: e.target.checked ? (expenseForm.flight_route_from || '') : '',
                          flight_boarding_pass_count: e.target.checked ? expenseForm.flight_boarding_pass_count : '1',
                        })
                      }
                    />{' '}
                    Add return leg for this flight claim
                  </label>
                </div>
              </div>
              {expenseForm.flight_is_return_ticket ? (
                <div className="grid expense-flight-grid expense-flight-return-grid" style={{ marginTop: 6 }}>
                  <div>
                    <label>Flight From (Return)</label>
                    <input
                      list="expense-flight-from-options"
                      value={expenseForm.flight_return_from}
                      onChange={(e) => setExpenseForm({ ...expenseForm, flight_return_from: e.target.value })}
                      placeholder="Select return departure airport"
                      required
                    />
                  </div>
                  <div>
                    <label>Flight To (Return)</label>
                    <input
                      list="expense-flight-to-options"
                      value={expenseForm.flight_return_to}
                      onChange={(e) => setExpenseForm({ ...expenseForm, flight_return_to: e.target.value })}
                      placeholder="Select return destination airport"
                      required
                    />
                  </div>
                  <div>
                    <label>Expected Boarding Passes (later upload)</label>
                    <select
                      value={expenseForm.flight_boarding_pass_count}
                      onChange={(e) =>
                        setExpenseForm({ ...expenseForm, flight_boarding_pass_count: e.target.value })
                      }
                      style={{ maxWidth: 220 }}
                    >
                      <option value="1">1 boarding pass</option>
                      <option value="2">2 boarding passes (outbound + return)</option>
                    </select>
                    <div className="status" style={{ marginTop: 4 }}>
                      For invoice upload now, this only sets the later boarding-pass reminder count.
                    </div>
                  </div>
                </div>
              ) : null}
              </div>
          ) : null}

          <div className={`expense-compact-row expense-compact-row-finance ${isPerDiemCategory ? 'is-per-diem-locked' : ''}`}>
            <div className="expense-field-date">
              <label>{isBulkPerDiemMode ? 'Date (optional in bulk mode)' : 'Date'}</label>
              <input
                ref={expenseDateRef}
                type="date"
                value={expenseForm.expense_date}
                className={expenseValidationActive && expenseValidation.missing.date && !isPerDiemCategory ? 'is-invalid' : ''}
                onChange={(e) =>
                  setExpenseForm({ ...expenseForm, expense_date: e.target.value })
                }
                required={!isBulkPerDiemMode}
                disabled={isPerDiemCategory}
              />
              {expenseValidationActive && expenseValidation.missing.date && !isPerDiemCategory ? (
                <div className="field-error">Enter the expense date.</div>
              ) : null}
            </div>
            <div className="expense-field-amount">
              <label>Amount</label>
              <input
                ref={expenseAmountRef}
                type="number"
                step="0.01"
                value={expenseForm.amount_local}
                className={expenseValidationActive && expenseValidation.missing.amount && !isPerDiemCategory ? 'is-invalid' : ''}
                onChange={(e) => setExpenseForm({ ...expenseForm, amount_local: e.target.value })}
                required
                disabled={isPerDiemCategory}
              />
              {expenseValidationActive && expenseValidation.missing.amount && !isPerDiemCategory ? (
                <div className="field-error">Enter an amount greater than 0.</div>
              ) : null}
            </div>
            <div className="expense-field-gst">
              <label>GST</label>
              <select
                value={expenseForm.gst_applicable ? 'yes' : 'no'}
                onChange={(e) =>
                  setExpenseForm({ ...expenseForm, gst_applicable: e.target.value === 'yes' })
                }
                disabled={isPerDiemCategory}
              >
                <option value="yes">Incl</option>
                <option value="no">No GST</option>
              </select>
            </div>
            <div className="expense-field-paid-by">
              <label>Paid by</label>
              <select
                value={expenseForm.paid_by}
                onChange={(e) => setExpenseForm({ ...expenseForm, paid_by: e.target.value })}
                disabled={isPerDiemCategory}
              >
                <option value="">Auto</option>
                <option value="company_card">Company card</option>
                <option value="personal_reimbursable">Personal (reimburse)</option>
                <option value="personal_non_reimbursable">Personal (no reimburse)</option>
              </select>
              <div className="status" style={{ marginTop: 4 }}>
                Company card = no reimbursement. Personal (reimburse) = reimburse consultant. Personal (no reimburse) = FYI only.
              </div>
            </div>
            <div className="expense-field-currency">
              <label>Currency</label>
              <select
                value={expenseForm.currency_local}
                onChange={(e) => {
                  const currency = e.target.value;
                  setExpenseForm({
                    ...expenseForm,
                    currency_local: currency,
                    gst_applicable: currency === 'AUD',
                    exchange_rate: currency === 'AUD' ? '1' : expenseForm.exchange_rate === '1' ? '' : expenseForm.exchange_rate,
                  });
                }}
                disabled={isPerDiemCategory}
              >
                <option value="AUD">AUD</option>
                <option value="PGK">PGK</option>
                <option value="FJD">FJD</option>
                <option value="USD">USD</option>
                <option value="WST">WST</option>
                <option value="XPF">XPF</option>
                <option value="SBD">SBD</option>
              </select>
            </div>
          </div>
          {expenseForm.category !== 'per_diem' && expenseForm.reimbursement_override_enabled ? (
            <div className="expense-reimbursement-grid" style={{ marginTop: 6, marginBottom: 6 }}>
              {!isConsultantSession ? (
                <div>
                  <label>Charge %</label>
                  <select
                    value={expenseForm.reimbursable_percent}
                    onChange={(e) => {
                      const nextPercent = e.target.value;
                      if (nextPercent === 'custom') {
                        setExpenseForm({ ...expenseForm, reimbursable_percent: 'custom' });
                        return;
                      }
                      const total = Number(expenseForm.amount_local || 0);
                      const calculated = Number.isFinite(total) && total > 0
                        ? ((total * Number(nextPercent)) / 100).toFixed(2)
                        : '';
                      setExpenseForm({
                        ...expenseForm,
                        reimbursable_percent: nextPercent,
                        reimbursable_amount_local: calculated,
                      });
                    }}
                  >
                    {REIMBURSABLE_PERCENT_OPTIONS.map((option) => (
                      <option key={`reimb-${option}`} value={option}>
                        {option === 'custom' ? 'Custom' : `${option}%`}
                      </option>
                    ))}
                  </select>
                </div>
              ) : null}
              <div>
                <label>Set Reimbursable Amount</label>
                <input
                  type="number"
                  step="0.01"
                  value={expenseForm.reimbursable_amount_local}
                  onChange={(e) => setExpenseForm({
                    ...expenseForm,
                    reimbursable_amount_local: e.target.value,
                    reimbursable_percent: 'custom',
                  })}
                  placeholder="e.g. 140.00"
                />
              </div>
              <div className="status expense-reimbursement-summary" style={{ margin: 0 }}>
                Non-reimbursable portion: {nonReimbursableDraftLocal > 0 ? formatAud(nonReimbursableDraftLocal) : 'AUD 0.00'}
              </div>
            </div>
          ) : null}

          {expenseForm.currency_local !== 'AUD' && !isPerDiemCategory ? (
            <>
              <label>Exchange Rate to AUD</label>
              <input
                ref={expenseExchangeRateRef}
                type="number"
                step="0.0001"
                value={expenseForm.exchange_rate}
                className={expenseValidationActive && expenseValidation.missing.exchangeRate ? 'is-invalid' : ''}
                onChange={(e) => setExpenseForm({ ...expenseForm, exchange_rate: e.target.value })}
                placeholder="Enter receipt-day exchange rate"
                required
              />
              {expenseValidationActive && expenseValidation.missing.exchangeRate ? (
                <div className="field-error">Enter a valid exchange rate.</div>
              ) : null}
              <div className="status">Required for overseas currencies. Use the rate from receipt day.</div>
            </>
          ) : isPerDiemCategory ? (
            <div className="status">Exchange rate is managed automatically for per diem claims.</div>
          ) : (
            <div className="status">Exchange rate locked to 1.0000 for AUD expenses.</div>
          )}

          {isPerDiemCategory ? (
            <div className="per-diem-sheet" style={{ marginTop: 8 }}>
              <div className="status">
                Tick the meals you are claiming. Incidental is automatically added to each trip day except the final trip day.
                {selectedExpenseRate
                  ? ` Daily baseline: ${formatAud(perDiemClaimBreakdown.daily)} (${selectedExpenseRate.country}, FY ${normalizeFinancialYearLabel(selectedExpenseRate.tax_year)})`
                  : ''}
              </div>
              <div className="grid" style={{ marginTop: 8 }}>
                <div>
                  <label>ATO Financial Year</label>
                  <select
                    value={selectedPerDiemFinancialYear}
                    onChange={(e) => setSelectedPerDiemFinancialYear(e.target.value)}
                  >
                    {perDiemFinancialYearOptions.map((yearOption) => (
                      <option key={`consultant-per-diem-fy-${yearOption}`} value={yearOption}>
                        {yearOption}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="status">
                {tripPerDiemLastDate
                  ? `Trip end date (${formatDateAu(tripPerDiemLastDate)}) does not include incidental.`
                  : 'Trip end date not set yet; incidental will apply to selected per diem day(s).'}
              </div>
              <div className="status">Bulk mode is enabled by default to submit the full travel range once.</div>
              {!isBulkPerDiemMode ? (
                <div>
                  <label>Per Diem Claim Date</label>
                  <input
                    ref={expensePerDiemSingleDateRef}
                    type="date"
                    value={expenseForm.expense_date}
                    className={expenseValidationActive && expenseValidation.missing.date ? 'is-invalid' : ''}
                    onChange={(e) => setExpenseForm({ ...expenseForm, expense_date: e.target.value })}
                    required
                  />
                </div>
              ) : null}
              {isBulkPerDiemMode ? (
                <div className="grid" style={{ marginTop: 8 }}>
                  <div>
                    <label>Per Diem Start Date</label>
                    <input
                      ref={expensePerDiemStartRef}
                      type="date"
                      value={expenseForm.per_diem_start_date}
                      className={expenseValidationActive && expenseValidation.missing.perDiemStart ? 'is-invalid' : ''}
                      onChange={(e) =>
                        setExpenseForm({ ...expenseForm, per_diem_start_date: e.target.value })
                      }
                      required
                    />
                    {expenseValidationActive && expenseValidation.missing.perDiemStart ? (
                      <div className="field-error">Choose a start date.</div>
                    ) : null}
                  </div>
                  <div>
                    <label>Per Diem End Date</label>
                    <input
                      ref={expensePerDiemEndRef}
                      type="date"
                      value={expenseForm.per_diem_end_date}
                      className={expenseValidationActive && expenseValidation.missing.perDiemEnd ? 'is-invalid' : ''}
                      onChange={(e) =>
                        setExpenseForm({ ...expenseForm, per_diem_end_date: e.target.value })
                      }
                      required
                    />
                    {expenseValidationActive && expenseValidation.missing.perDiemEnd ? (
                      <div className="field-error">Choose an end date.</div>
                    ) : null}
                  </div>
                  <div>
                    <label className="inline-checkbox" style={{ marginTop: 22 }}>
                      <input
                        type="checkbox"
                        checked={perDiemUseInternationalCurrency}
                        onChange={(e) => onTogglePerDiemInternationalCurrency(e.target.checked)}
                        disabled={!selectedExpenseTrip}
                      />{' '}
                      International currency + today's FX
                    </label>
                    <div className="status" style={{ marginTop: 4 }}>
                      {isResolvingPerDiemFx
                        ? 'Loading today\'s exchange rate...'
                        : `Using ${expenseForm.currency_local || 'AUD'} at ${expenseForm.exchange_rate || '—'} to AUD.`}
                    </div>
                  </div>
                  <div className="status" style={{ gridColumn: '1 / -1' }}>
                    {bulkPerDiemDates.length
                      ? `Will create ${bulkPerDiemDates.length} entries. Incidentals apply on ${Math.max(
                          bulkPerDiemDates.length - 1,
                          0
                        )} day(s) only (all except last day).`
                      : 'Choose a valid start/end range.'}
                  </div>
                </div>
              ) : null}

              <div className="per-diem-day-editor">
                {perDiemDayClaimRows.length === 0 ? (
                  <div className="status">Choose date(s) first, then tick breakfast/lunch/dinner per day.</div>
                ) : (
                  perDiemDayClaimRows.map((row) => (
                    <div key={`editor-consultant-${row.isoDate}`} className="per-diem-day-editor-row">
                      <div className="per-diem-day-editor-date">{formatDateAu(row.isoDate)}</div>
                      <label>
                        <input
                          type="checkbox"
                          checked={row.breakfastClaimed}
                          onChange={(e) => onTogglePerDiemMeal(row.isoDate, 'breakfast', e.target.checked)}
                        />{' '}
                        Breakfast
                      </label>
                      <label>
                        <input
                          type="checkbox"
                          checked={row.lunchClaimed}
                          onChange={(e) => onTogglePerDiemMeal(row.isoDate, 'lunch', e.target.checked)}
                        />{' '}
                        Lunch
                      </label>
                      <label>
                        <input
                          type="checkbox"
                          checked={row.dinnerClaimed}
                          onChange={(e) => onTogglePerDiemMeal(row.isoDate, 'dinner', e.target.checked)}
                        />{' '}
                        Dinner
                      </label>
                    </div>
                  ))
                )}
              </div>
            </div>
          ) : null}

          </div>

          <div id="expense-step-receipt" className={`expense-section expense-section-receipt ${isConsultantSession ? 'consultant-step-panel' : ''}`}>
            <h3 className="expense-section-title">3. Receipt evidence</h3>

          <label>Receipt upload (recommended)</label>
          {!expenseForm.no_receipt ? (
            <div
              className={`receipt-dropzone ${receiptDropActive ? 'is-active' : ''}`}
              onDragOver={(e) => {
                e.preventDefault();
                setReceiptDropActive(true);
              }}
              onDragLeave={() => setReceiptDropActive(false)}
              onDrop={(e) => {
                e.preventDefault();
                setReceiptDropActive(false);
                const droppedFile = e.dataTransfer?.files?.[0];
                handleReceiptFile(droppedFile);
              }}
            >
              <div className="status">
                Drag screenshot/photo here or choose file. On phone, choose file opens camera/photos.
              </div>
              <input
                ref={expenseReceiptFileRef}
                type="file"
                accept="image/*"
                capture="environment"
                className={expenseValidationActive && expenseValidation.missing.receipt ? 'is-invalid' : ''}
                onChange={(e) => handleReceiptFile(e.target.files?.[0])}
              />
              {expenseValidationActive && expenseValidation.missing.receipt ? (
                <div className="field-error">Add a receipt image or tick "Draft - add receipt later".</div>
              ) : null}
            </div>
          ) : null}

          <div className="status">
            One receipt image is enough for most expenses. You only need URL/thumbnail fields for admin workflows.
          </div>

          <div className="grid expense-receipt-pair-grid" style={{ marginTop: 8 }}>
            <div>
              {!isConsultantSession ? (
                <>
                  <label>Receipt Type</label>
                  <select
                    value={expenseForm.receipt_kind}
                    onChange={(e) => setExpenseForm({ ...expenseForm, receipt_kind: e.target.value })}
                  >
                    {EXPENSE_RECEIPT_KIND_OPTIONS.map((option) => (
                      <option key={`receipt-kind-${option}`} value={option}>
                        {formatTokenLabel(option)}
                      </option>
                    ))}
                  </select>
                </>
              ) : (
                <div className="status receipt-pairing-hint">
                  {(expenseForm.category === 'flights' || expenseForm.category === 'flight')
                    ? (String(expenseForm.receipt_kind || '').toLowerCase() === 'boarding_pass'
                      ? 'Uploading boarding pass record.'
                      : 'Uploading flight invoice record. Boarding passes can be uploaded as separate expenses.')
                    : 'Receipt type is automatic: General.'}
                </div>
              )}
            </div>
          </div>
          {(expenseForm.category === 'flights' || expenseForm.category === 'flight') ? (
            <div className="status">
              Flight invoices and boarding passes are submitted as separate expenses and grouped together in the report.
            </div>
          ) : null}

          {!isConsultantSession ? (
            <details>
              <summary>Admin advanced receipt fields (optional)</summary>
              <label>Receipt URL (optional)</label>
              <input
                value={expenseForm.receipt_url}
                onChange={(e) => setExpenseForm({ ...expenseForm, receipt_url: e.target.value })}
                placeholder="Optional: paste receipt URL"
                disabled={expenseForm.no_receipt}
              />

              <label>Receipt Thumbnail URL (optional)</label>
              <input
                value={expenseForm.receipt_thumb_url}
                onChange={(e) =>
                  setExpenseForm({ ...expenseForm, receipt_thumb_url: e.target.value })
                }
                placeholder="Optional: smaller image for report thumbnails"
                disabled={expenseForm.no_receipt}
              />
            </details>
          ) : null}

          <label className="inline-checkbox">
            <input
              type="checkbox"
              checked={expenseForm.no_receipt}
              onChange={(e) =>
                setExpenseForm({
                  ...expenseForm,
                  no_receipt: e.target.checked,
                  receipt_url: e.target.checked ? '' : expenseForm.receipt_url,
                })
              }
            />{' '}
            Draft - add receipt later
          </label>

          {expenseForm.no_receipt ? (
            <>
              <div className="status receipt-reminder">Reminder: this expense stays flagged until receipt is uploaded.</div>
              <label>Reason (optional)</label>
              <textarea
                value={expenseForm.no_receipt_reason}
                onChange={(e) =>
                  setExpenseForm({ ...expenseForm, no_receipt_reason: e.target.value })
                }
                placeholder="Optional note about when/how receipt will be provided"
                rows={2}
              />
            </>
          ) : null}
          </div>

          <div id="expense-step-submit" className={`expense-section expense-section-submit ${isConsultantSession ? 'consultant-step-panel' : ''}`}>
            <h3 className="expense-section-title">4. Finalise</h3>

          {expenseForm.category !== 'per_diem' ? (
            <label className="inline-checkbox" style={{ marginBottom: 6, fontSize: 12 }}>
              <input
                type="checkbox"
                checked={Boolean(expenseForm.reimbursement_override_enabled)}
                onChange={(e) => {
                  const enabled = e.target.checked;
                  setExpenseForm((prev) => ({
                    ...prev,
                    reimbursement_override_enabled: enabled,
                    reimbursable_percent: enabled ? (isConsultantSession ? 'custom' : prev.reimbursable_percent) : '100',
                    reimbursable_amount_local: enabled ? prev.reimbursable_amount_local : '',
                  }));
                }}
              />{' '}
              Set a fixed reimbursable amount (add context in Notes below)
            </label>
          ) : null}

          <label>Notes - explain any extra details (optional)</label>
          {isConsultantSession && expenseForm.category !== 'per_diem' && !String(expenseForm.description || '').trim() ? (
            <div className="status" style={{ marginTop: 4 }}>
              Recommended: add a short description so Finance can reconcile quickly at month end.
            </div>
          ) : null}
          <textarea
            value={expenseForm.notes}
            onChange={(e) => setExpenseForm({ ...expenseForm, notes: e.target.value })}
            rows={3}
          />

          <div className="expense-form-actions">
            <button type="submit" disabled={isSubmittingExpense}>
              {isSubmittingExpense ? 'Submitting Expense...' : 'Submit Expense'}
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => {
                setExpenseForm((prev) => ({
                  ...INITIAL_EXPENSE_FORM,
                  submitted_by_role: isConsultantSession ? 'consultant' : prev.submitted_by_role,
                  submitted_by_email: isConsultantSession ? sessionEmail || '' : '',
                }));
                setExpenseContextClientFilter('');
                setExpenseContextConsultantFilter(isConsultantSession ? normalizeEmailIdentity(sessionEmail || '') : '');
                setExpenseStatus('Draft cleared.');
              }}
              disabled={isSubmittingExpense}
            >
              Clear Form
            </button>
          </div>
          {expenseStatus ? <div className="status">{expenseStatus}</div> : null}
          </div>
        </form>
          {isConsultantSession ? (
            <div className="expense-consultant-insights" style={{ marginTop: 12 }}>
              <h3 className="expense-consultant-section-heading">
                Outstanding Expense Reports
              </h3>
            {consultantExpenseProjectRequirements.length === 0 ? (
              <div className="status" style={{ marginBottom: 8 }}>
                No activities currently require expense reporting.
              </div>
            ) : (
              <>
                <div className="status expense-insight-meta">
                  Linked activities requiring expense report: {consultantExpenseProjectRequirements.length} · Outstanding after end date:{' '}
                  {consultantOutstandingExpenseProjects.length}
                </div>
                {consultantOutstandingExpenseProjects.length > 0 ? (
                  <div className="receipt-reminder expense-insight-alert">
                    Outstanding now: {consultantOutstandingExpenseProjects.length} activity/activities have ended and still need your expense submission.
                  </div>
                ) : null}
                {consultantExpenseProjectRequirements.map(({ trip, hasEnded, hasSubmittedExpense, projectEndDate }) => (
                  <div
                    key={`required-${trip.id}`}
                    className={`status consultant-expense-row ${hasEnded ? (hasSubmittedExpense ? 'is-submitted' : 'is-outstanding') : 'is-in-progress'}`}
                  >
                    <strong>{trip.name}</strong> — {formatClientProgramLabel(trip.client_name, trip.program_name)}
                    {' · End: '}
                    {projectEndDate ? formatDateAu(projectEndDate) : 'No end date'}
                    {' · Status: '}
                    {hasEnded
                      ? hasSubmittedExpense
                        ? 'Submitted'
                        : 'Outstanding'
                      : 'In progress'}
                  </div>
                ))}
              </>
            )}

            <h3 className="expense-consultant-section-heading" style={{ marginTop: 12 }}>
              My Expense & Per Diem Check
            </h3>
            <div className="status expense-insight-meta">
              Showing your own submitted expenses only.
            </div>
            <div className="status expense-insight-meta">
              Total entries: {consultantExpenseRows.length} · Per diem entries:{' '}
              {consultantExpenseRows.filter((row) => row.category === 'per_diem').length}
            </div>
            {consultantExpenseRows.length === 0 ? (
              <div className="status">No expenses submitted yet.</div>
            ) : (
              consultantExpenseRows.slice(0, 20).map((row) => (
                <div
                  key={row.id}
                  className={`status consultant-expense-row ${String(row.status || '').toLowerCase() === 'approved' ? 'is-approved' : 'is-pending'}`}
                >
                  <strong>{formatDateAu(row.expense_date)}</strong> · {row.category} · {formatAud(row.amount_aud)} · {row.status}
                  {row.category === 'per_diem' ? ' · Per diem' : ''}
                </div>
              ))
            )}
          </div>
        ) : null}
      </section>

      {!isConsultantSession ? (
        <section className="card" style={sectionVisibilityStyle('submit-expense')}>
          <h2>Email Receipt Intake (Admin only)</h2>
          <div className="status">Optional advanced path. For now you can keep using screenshot/photo upload directly in Submit Expense.</div>
          <details>
            <summary>Open optional email intake form</summary>
            <form onSubmit={onIntakeEmailReceipt} style={{ marginTop: 10 }}>
          <label>Activity</label>
          <select
            value={emailIntakeForm.trip_id}
            onChange={(e) => setEmailIntakeForm({ ...emailIntakeForm, trip_id: e.target.value })}
            required
          >
            <option value="">Select activity</option>
            {trips.map((trip) => (
              <option key={trip.id} value={trip.id}>
                {trip.name} — {formatClientProgramLabel(trip.client_name, trip.program_name)}
              </option>
            ))}
          </select>

          <label>Forwarded From Email</label>
          <input
            type="email"
            value={emailIntakeForm.received_from_email}
            onChange={(e) =>
              setEmailIntakeForm({ ...emailIntakeForm, received_from_email: e.target.value })
            }
            placeholder="receipts@uber.com"
            required
          />

          <label>Category</label>
          <select
            value={emailIntakeForm.category}
            onChange={(e) => setEmailIntakeForm({ ...emailIntakeForm, category: e.target.value })}
          >
            {EMAIL_INTAKE_CATEGORIES.map((option) => (
              <option key={option} value={option}>
                {formatTokenLabel(option)}
              </option>
            ))}
          </select>

          <label>Receipt URL</label>
          <input
            value={emailIntakeForm.receipt_url}
            onChange={(e) => setEmailIntakeForm({ ...emailIntakeForm, receipt_url: e.target.value })}
            placeholder="Paste URL from uploaded email attachment"
            required
          />

          <label>Receipt Thumbnail URL (optional)</label>
          <input
            value={emailIntakeForm.receipt_thumb_url}
            onChange={(e) =>
              setEmailIntakeForm({ ...emailIntakeForm, receipt_thumb_url: e.target.value })
            }
          />

          <label>Description (optional)</label>
          <input
            list="email-intake-description-options"
            value={emailIntakeForm.description}
            onChange={(e) => setEmailIntakeForm({ ...emailIntakeForm, description: e.target.value })}
            placeholder="e.g. Flight invoice"
          />
          <datalist id="email-intake-description-options">
            {sortedExpenseDescriptionOptions.map((option) => (
              <option key={`email-desc-${option}`} value={option} />
            ))}
          </datalist>

          <label>Supplier (optional)</label>
          <input
            list="email-intake-supplier-options"
            value={emailIntakeForm.supplier}
            onChange={(e) => setEmailIntakeForm({ ...emailIntakeForm, supplier: e.target.value })}
            placeholder="e.g. Virgin Australia"
          />
          <datalist id="email-intake-supplier-options">
            {sortedExpenseSupplierOptions.map((option) => (
              <option key={`email-supplier-${option}`} value={option} />
            ))}
          </datalist>

          <label>Receipt Type</label>
          <select
            value={emailIntakeForm.receipt_kind}
            onChange={(e) => setEmailIntakeForm({ ...emailIntakeForm, receipt_kind: e.target.value })}
          >
            {sortedReceiptKindOptions.map((option) => (
              <option key={`email-kind-${option}`} value={option}>
                {formatTokenLabel(option)}
              </option>
            ))}
          </select>

          <label>Expense Date (optional)</label>
          <input
            type="date"
            value={emailIntakeForm.expense_date}
            onChange={(e) => setEmailIntakeForm({ ...emailIntakeForm, expense_date: e.target.value })}
          />

          <label>Amount (local, optional)</label>
          <input
            type="number"
            step="0.01"
            value={emailIntakeForm.amount_local}
            onChange={(e) => setEmailIntakeForm({ ...emailIntakeForm, amount_local: e.target.value })}
          />

          <label>Currency</label>
          <select
            value={emailIntakeForm.currency_local}
            onChange={(e) =>
              setEmailIntakeForm({ ...emailIntakeForm, currency_local: e.target.value })
            }
          >
            <option value="AUD">AUD</option>
            <option value="USD">USD</option>
            <option value="PGK">PGK</option>
          </select>

          <label>Exchange Rate to AUD</label>
          <input
            type="number"
            step="0.0001"
            value={emailIntakeForm.exchange_rate}
            onChange={(e) =>
              setEmailIntakeForm({ ...emailIntakeForm, exchange_rate: e.target.value })
            }
            required
          />

          <label>
            <input
              type="checkbox"
              checked={emailIntakeForm.gst_applicable}
              onChange={(e) =>
                setEmailIntakeForm({ ...emailIntakeForm, gst_applicable: e.target.checked })
              }
            />{' '}
            GST applicable
          </label>

          <label>Admin Notes</label>
          <textarea
            value={emailIntakeForm.notes}
            onChange={(e) => setEmailIntakeForm({ ...emailIntakeForm, notes: e.target.value })}
            rows={2}
          />

          <button type="submit">Add Emailed Receipt Draft</button>
            </form>
          </details>
        </section>
      ) : null}

      <section id="coaching-module" className="card coaching-module-shell" style={sectionVisibilityStyle('coaching-module')}>
        <h2>Coaching Module (Pilot)</h2>

        <div className="coaching-module-kpis">
          <span className="coaching-module-chip">Coachees: {coachingEngagements.length}</span>
          <span className="coaching-module-chip">Sessions: {coachingSessions.length}</span>
          <span className="coaching-module-chip">Active Clients: {activeCoachingClientCount}</span>
        </div>

        <div className="status coaching-shell-guidance">
          {isConsultantSession
            ? 'Consultant mode: focus on logging sessions and tracking your coachee schedule.'
            : 'Admin mode: use Batch Setup for onboarding, then monitor sessions and entitlements below.'}
        </div>
        <div className="status" style={{ marginBottom: 10 }}>
          <strong>Quick help on this page:</strong> 1) Add/update coachees, 2) Log sessions, 3) Use Recent Sessions + Entitlements to edit and check totals.
        </div>

        <div className="workflow-priority-panel coaching-priority-panel" role="region" aria-label="Coaching priority workflow">
          <div className="workflow-priority-head">
            <strong>{isConsultantSession ? 'Consultant coaching flow' : 'Admin coaching flow'}</strong>
            <span className="status">Next best action: {coachingNextStep.label}</span>
          </div>
          {isConsultantSession ? (
            <div className="workflow-step-list">
              <button
                type="button"
                className={`secondary workflow-step-button ${coachingNextStep.id === 'coaching-session-log' ? 'is-active' : ''}`}
                onClick={() => document.getElementById('coaching-session-log')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
              >
                Log Session
              </button>
              <button
                type="button"
                className={`secondary workflow-step-button ${coachingNextStep.id === 'coaching-engagement-planner' ? 'is-active' : ''}`}
                onClick={() => document.getElementById('coaching-engagement-planner')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
              >
                Planner
              </button>
              <button
                type="button"
                className={`secondary workflow-step-button ${coachingNextStep.id === 'coaching-recent-edit' ? 'is-active' : ''}`}
                onClick={() => document.getElementById('coaching-recent-edit')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
              >
                Edit Recent
              </button>
            </div>
          ) : (
            <div className="workflow-step-list">
              <button
                type="button"
                className={`secondary workflow-step-button ${coachingNextStep.id === 'coaching-batch-entry' ? 'is-active' : ''}`}
                onClick={() => document.getElementById('coaching-batch-entry')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
              >
                Batch Setup
              </button>
              <button
                type="button"
                className={`secondary workflow-step-button ${coachingNextStep.id === 'coaching-single-entry' ? 'is-active' : ''}`}
                onClick={() => document.getElementById('coaching-single-entry')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
              >
                Single Entry
              </button>
              <button
                type="button"
                className={`secondary workflow-step-button ${coachingNextStep.id === 'coaching-admin-sessions' ? 'is-active' : ''}`}
                onClick={() => {
                  setActiveScreenTabId('admin-console');
                  setAdminConsoleSection('sessions');
                }}
              >
                Open Admin Sessions
              </button>
            </div>
          )}
        </div>

        {!isConsultantSession ? (
          <div className="status coaching-admin-guidance" style={{ marginBottom: 10 }}>
            <strong>Recommended workflow:</strong> use <strong>Batch Setup</strong> for most onboarding; use
            <strong> Single Coachee Entry</strong> only for one-off fixes.
          </div>
        ) : (
          <div className="status" style={{ marginBottom: 10 }}>
            Batch upload is hidden in Consultant mode. Switch to <strong>Admin</strong> in Session Mode to access it.
          </div>
        )}

        {!isConsultantSession ? (
          <>
            <details id="coaching-single-entry">
              <summary>Single Coachee Entry (Advanced / one-off)</summary>
              <form onSubmit={onCreateCoachingEngagement} className="coaching-engagement-form" style={{ marginTop: 10 }}>
              <label>Coachee Name</label>
              <div className="status coaching-helper-note">
                Use this as the coachee name (e.g. Jane Smith).
              </div>
              <input
                value={coachingEngagementForm.name}
                onChange={(e) =>
                  setCoachingEngagementForm((prev) => ({ ...prev, name: e.target.value }))
                }
                placeholder="Coachee name"
                required
              />
              <label>Job Title (optional)</label>
              <input
                value={coachingEngagementForm.job_title}
                onChange={(e) =>
                  setCoachingEngagementForm((prev) => ({ ...prev, job_title: e.target.value }))
                }
                placeholder="e.g. Program Manager"
              />
              <label>Client Organisation</label>
              <select
                value={
                  clientOptions.includes(String(coachingEngagementForm.client_org || '').trim())
                    ? String(coachingEngagementForm.client_org || '').trim()
                    : '__custom__'
                }
                onChange={(e) =>
                  setCoachingEngagementForm((prev) => ({
                    ...prev,
                    client_org: e.target.value === '__custom__' ? '' : e.target.value,
                  }))
                }
                required
              >
                <option value="">Select client</option>
                {clientOptions.map((clientName) => (
                  <option key={clientName} value={clientName}>
                    {clientName}
                  </option>
                ))}
                <option value="__custom__">Custom client...</option>
              </select>
              {!clientOptions.includes(String(coachingEngagementForm.client_org || '').trim()) ? (
                <input
                  value={coachingEngagementForm.client_org}
                  onChange={(e) =>
                    setCoachingEngagementForm((prev) => ({ ...prev, client_org: e.target.value }))
                  }
                  placeholder="Type new client"
                  required
                />
              ) : null}
              <datalist id="coaching-client-options">
                {clientOptions.map((clientName) => (
                  <option key={clientName} value={clientName}>
                    {clientName}
                  </option>
                ))}
              </datalist>
              <label>Coach</label>
              <select
                value={coachingEngagementForm.coach_email}
                onChange={(e) =>
                  setCoachingEngagementForm((prev) => ({ ...prev, coach_email: e.target.value }))
                }
                required
              >
                <option value="">Select coach</option>
                {orderedCoaches.map((consultant) => (
                  <option key={consultant.email} value={consultant.email}>
                    {consultant.name} ({consultant.email})
                  </option>
                ))}
              </select>
              <div className="grid">
                <div>
                  <label>Entitled Sessions</label>
                  <input
                    type="number"
                    value={coachingEngagementForm.total_sessions}
                    onChange={(e) =>
                      setCoachingEngagementForm((prev) => ({ ...prev, total_sessions: e.target.value }))
                    }
                    required
                  />
                </div>
                <div>
                  <label>Sessions Completed</label>
                  <input
                    type="number"
                    min="0"
                    value={coachingEngagementForm.sessions_used}
                    onChange={(e) =>
                      setCoachingEngagementForm((prev) => ({ ...prev, sessions_used: e.target.value }))
                    }
                  />
                </div>
                <div>
                  <label>Associate Cost Per Session (optional)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={coachingEngagementForm.associate_cost_per_session}
                    onChange={(e) =>
                      setCoachingEngagementForm((prev) => ({
                        ...prev,
                        associate_cost_per_session: e.target.value,
                      }))
                    }
                    placeholder="e.g. 220"
                  />
                </div>
                <div>
                  <label className="inline-checkbox" style={{ marginBottom: 8 }}>
                    <input
                      type="checkbox"
                      checked={Boolean(coachingEngagementForm.lcp_debrief_enabled)}
                      onChange={(e) =>
                        setCoachingEngagementForm((prev) => ({
                          ...prev,
                          lcp_debrief_enabled: e.target.checked,
                          lcp_debrief_total_sessions: e.target.checked ? prev.lcp_debrief_total_sessions : '0',
                          lcp_debrief_sessions_used: e.target.checked ? prev.lcp_debrief_sessions_used : '0',
                        }))
                      }
                    />
                    LCP de-brief available for this client
                  </label>
                </div>
                {coachingEngagementForm.lcp_debrief_enabled ? (
                  <>
                    <div>
                      <label>LCP Entitled Sessions</label>
                      <input
                        type="number"
                        min="0"
                        value={coachingEngagementForm.lcp_debrief_total_sessions}
                        onChange={(e) =>
                          setCoachingEngagementForm((prev) => ({
                            ...prev,
                            lcp_debrief_total_sessions: e.target.value,
                          }))
                        }
                      />
                    </div>
                    <div>
                      <label>LCP Sessions Completed</label>
                      <input
                        type="number"
                        min="0"
                        value={coachingEngagementForm.lcp_debrief_sessions_used}
                        onChange={(e) =>
                          setCoachingEngagementForm((prev) => ({
                            ...prev,
                            lcp_debrief_sessions_used: e.target.value,
                          }))
                        }
                      />
                    </div>
                  </>
                ) : null}
              </div>
              <div className="coaching-form-actions">
                <button type="submit" disabled={isCreatingCoachingEngagement}>
                  {isCreatingCoachingEngagement
                    ? editingCoachingEngagementId
                      ? 'Saving Coachee Record...'
                      : 'Creating Engagement...'
                    : editingCoachingEngagementId
                      ? 'Save Coachee Record'
                      : 'Create Coaching Engagement'}
                </button>
                {editingCoachingEngagementId ? (
                  <button type="button" className="secondary" onClick={onCancelEditCoachingEngagement}>
                    Cancel Coachee Edit
                  </button>
                ) : null}
              </div>
              </form>
            </details>

            <div id="coaching-batch-entry" className="coaching-engagement-form" style={{ marginTop: 12 }}>
              <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
                Primary: Batch Coachee Setup
              </h3>
              <div className="status" style={{ marginBottom: 8 }}>
                Fastest way to onboard many coachees while linking client + coach.
              </div>
              <form onSubmit={onSubmitCoachingBatch}>
                <div className="status coaching-helper-note" style={{ marginBottom: 8 }}>
                  Choose from dropdowns for existing clients/coaches, or pick "Custom" to type a new one.
                </div>
                <div className="status" style={{ marginBottom: 8 }}>
                  Loaded options: {clientOptions.length} clients, {coachLookupOptions.length} coaches.
                </div>

                <datalist id="coaching-batch-client-options">
                  {clientOptions.map((clientName) => (
                    <option key={clientName} value={clientName}>
                      {clientName}
                    </option>
                  ))}
                </datalist>
                <datalist id="coaching-batch-coach-options">
                  {coachLookupOptions.map((coach) => (
                    <option key={coach.email} value={coach.name}>
                      {coach.name} ({coach.email})
                    </option>
                  ))}
                </datalist>

                <div style={{ overflowX: 'auto' }}>
                  <table className="admin-table" style={{ minWidth: 860 }}>
                    <thead>
                      <tr>
                        <th>Coachee</th>
                        <th>Job Title</th>
                        <th>Client</th>
                        <th>Coach</th>
                        <th>Entitled</th>
                        <th>Completed</th>
                        <th>LCP On</th>
                        <th>LCP Entitled</th>
                        <th>LCP Used</th>
                        <th>Row</th>
                      </tr>
                    </thead>
                    <tbody>
                      {coachingBatchRows.map((row, idx) => (
                        <tr key={`coaching-batch-row-${idx}`}>
                          <td>
                            <input
                              value={row.name}
                              onChange={(e) => onCoachingBatchFieldChange(idx, 'name', e.target.value)}
                              placeholder="Jane Smith"
                              required={idx === 0}
                            />
                          </td>
                          <td>
                            <input
                              value={row.job_title}
                              onChange={(e) => onCoachingBatchFieldChange(idx, 'job_title', e.target.value)}
                              placeholder="Program Manager"
                            />
                          </td>
                          <td>
                            <select
                              value={clientOptions.includes(String(row.client_org || '').trim()) ? String(row.client_org || '').trim() : '__custom__'}
                              onChange={(e) =>
                                onCoachingBatchFieldChange(
                                  idx,
                                  'client_org',
                                  e.target.value === '__custom__' ? '' : e.target.value
                                )
                              }
                              required={idx === 0}
                            >
                              <option value="">Select client</option>
                              {clientOptions.map((clientName) => (
                                <option key={clientName} value={clientName}>
                                  {clientName}
                                </option>
                              ))}
                              <option value="__custom__">Custom client...</option>
                            </select>
                            {!clientOptions.includes(String(row.client_org || '').trim()) ? (
                              <input
                                value={row.client_org}
                                onChange={(e) => onCoachingBatchFieldChange(idx, 'client_org', e.target.value)}
                                placeholder="Type new client"
                                required={idx === 0}
                              />
                            ) : null}
                          </td>
                          <td>
                            <select
                              value={
                                coachLookupOptions.some(
                                  (coach) => coach.emailLower === String(row.coach_email || '').trim().toLowerCase()
                                )
                                  ? String(row.coach_email || '').trim().toLowerCase()
                                  : '__custom__'
                              }
                              onChange={(e) => {
                                if (e.target.value === '__custom__') {
                                  onCoachingBatchFieldChange(idx, 'coach_input', '');
                                  return;
                                }
                                onCoachingBatchFieldChange(idx, 'coach_input', e.target.value);
                              }}
                              required={idx === 0}
                            >
                              <option value="">Select coach</option>
                              {coachLookupOptions.map((coach) => (
                                <option key={coach.email} value={coach.emailLower}>
                                  {coach.name} ({coach.email})
                                </option>
                              ))}
                              <option value="__custom__">Custom coach...</option>
                            </select>
                            {!coachLookupOptions.some(
                              (coach) => coach.emailLower === String(row.coach_email || '').trim().toLowerCase()
                            ) ? (
                              <input
                                value={row.coach_input}
                                onChange={(e) => onCoachingBatchFieldChange(idx, 'coach_input', e.target.value)}
                                placeholder="Type new coach name or email"
                                required={idx === 0}
                              />
                            ) : null}
                            <div className="status" style={{ marginTop: 4 }}>
                              {row.coach_email ? `Resolved: ${displayNameFromEmail(row.coach_email)} (${row.coach_email})` : 'Not resolved yet'}
                            </div>
                          </td>
                          <td>
                            <input
                              type="number"
                              min="1"
                              value={row.total_sessions}
                              onChange={(e) => onCoachingBatchFieldChange(idx, 'total_sessions', e.target.value)}
                            />
                          </td>
                          <td>
                            <input
                              type="number"
                              min="0"
                              value={row.sessions_used}
                              onChange={(e) => onCoachingBatchFieldChange(idx, 'sessions_used', e.target.value)}
                            />
                          </td>
                          <td>
                            <label className="inline-checkbox" style={{ margin: 0 }}>
                              <input
                                type="checkbox"
                                checked={Boolean(row.lcp_debrief_enabled)}
                                onChange={(e) =>
                                  onCoachingBatchFieldChange(idx, 'lcp_debrief_enabled', e.target.checked)
                                }
                              />
                              Yes
                            </label>
                          </td>
                          <td>
                            <input
                              type="number"
                              min="0"
                              value={row.lcp_debrief_total_sessions}
                              onChange={(e) =>
                                onCoachingBatchFieldChange(idx, 'lcp_debrief_total_sessions', e.target.value)
                              }
                              disabled={!Boolean(row.lcp_debrief_enabled)}
                            />
                          </td>
                          <td>
                            <input
                              type="number"
                              min="0"
                              value={row.lcp_debrief_sessions_used}
                              onChange={(e) =>
                                onCoachingBatchFieldChange(idx, 'lcp_debrief_sessions_used', e.target.value)
                              }
                              disabled={!Boolean(row.lcp_debrief_enabled)}
                            />
                          </td>
                          <td>
                            <button type="button" className="secondary" onClick={() => onRemoveCoachingBatchRow(idx)}>
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="coaching-form-actions">
                  <button type="button" className="secondary" onClick={onAddCoachingBatchRow}>
                    + Add Row
                  </button>
                  <button type="button" className="secondary" onClick={onResetCoachingBatchRows}>
                    Clear Batch
                  </button>
                  <button type="submit" disabled={isSubmittingCoachingBatch}>
                    {isSubmittingCoachingBatch ? 'Saving Batch...' : 'Save Batch to Portal'}
                  </button>
                </div>
              </form>
            </div>

          </>
        ) : null}

        {isConsultantSession ? (
          <>
            <div className="coaching-session-shell" style={{ marginTop: 12 }}>
              <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
                Invoice Prep (Associates)
              </h3>
              <div className="status" style={{ marginBottom: 8 }}>
                Select unclaimed chargeable sessions, add a claim reference (e.g. KT001), then mark them as claimed so you don't double invoice.
              </div>
              <div className="grid" style={{ marginBottom: 8 }}>
                <div>
                  <label>Start date (optional)</label>
                  <input
                    type="date"
                    value={associateInvoicePrep.start_date}
                    onChange={(e) => setAssociateInvoicePrep((prev) => ({ ...prev, start_date: e.target.value }))}
                  />
                </div>
                <div>
                  <label>End date (optional)</label>
                  <input
                    type="date"
                    value={associateInvoicePrep.end_date}
                    onChange={(e) => setAssociateInvoicePrep((prev) => ({ ...prev, end_date: e.target.value }))}
                  />
                </div>
                <div>
                  <label>Claim reference</label>
                  <input
                    value={associateInvoicePrep.claim_ref}
                    onChange={(e) => setAssociateInvoicePrep((prev) => ({ ...prev, claim_ref: e.target.value }))}
                    placeholder="e.g. KT001"
                  />
                </div>
              </div>
              <div className="status" style={{ marginBottom: 8 }}>
                Unclaimed sessions in range: {associateClaimableSessions.length}. Selected: {associateSelectedClaimSessionIds.length}. Total: ${associateSelectedClaimSummary.total.toFixed(2)}
                {associateSelectedClaimSummary.missingCostCount > 0 ? ` · Missing cost on ${associateSelectedClaimSummary.missingCostCount} selected` : ''}
              </div>
              {associateInvoicePrepStatus ? (
                <div className="status" style={{ marginBottom: 8 }}>
                  {associateInvoicePrepStatus}
                </div>
              ) : null}
              <div className="admin-table-wrap" style={{ marginBottom: 8 }}>
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Select</th>
                      <th>Date</th>
                      <th>Coachee</th>
                      <th>Client</th>
                      <th>Type</th>
                      <th>Cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    {associateClaimableSessions.slice(0, 50).map((session) => {
                      const engagement = coachingEngagementById[String(session.engagement_id)] || null;
                      const key = String(session.id);
                      const checked = Boolean(associateInvoicePrep.selected_ids?.[key]);
                      const cost = Number(session.associate_cost_amount ?? session.associate_cost_per_session ?? 0);
                      return (
                        <tr key={key}>
                          <td>
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={(e) =>
                                setAssociateInvoicePrep((prev) => ({
                                  ...prev,
                                  selected_ids: { ...prev.selected_ids, [key]: e.target.checked },
                                }))
                              }
                            />
                          </td>
                          <td>{formatDateAu(session.session_date)}</td>
                          <td>{engagement?.name || session.engagement_id}</td>
                          <td>{engagement?.client_org || ''}</td>
                          <td>{formatTokenLabel(session.session_type)}</td>
                          <td>{Number.isFinite(cost) ? `$${cost.toFixed(2)}` : ''}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="coaching-form-actions">
                <button
                  type="button"
                  className="secondary"
                  onClick={() => {
                    const shown = associateClaimableSessions.slice(0, 50);
                    const next = {};
                    shown.forEach((row) => {
                      next[String(row.id)] = true;
                    });
                    setAssociateInvoicePrep((prev) => ({ ...prev, selected_ids: next }));
                  }}
                  disabled={!associateClaimableSessions.length}
                >
                  Select All Shown
                </button>
                <button type="button" onClick={onClaimAssociateSessions} disabled={isClaimingAssociateSessions}>
                  {isClaimingAssociateSessions ? 'Saving Claim...' : 'Mark Selected as Claimed'}
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={onCopyAssociateClaimSummary}
                  disabled={!associateSelectedClaimSessionIds.length}
                >
                  Copy Summary
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => setAssociateInvoicePrep((prev) => ({ ...prev, selected_ids: {} }))}
                >
                  Clear Selection
                </button>
              </div>
            </div>
            <div id="coaching-session-log" className="coaching-session-shell" style={{ marginTop: 12 }}>
              <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
                Session Logging
              </h3>
              <div className="status" style={{ marginBottom: 8 }}>
                Log sessions quickly for your assigned coachees.
              </div>

              <form onSubmit={onLogCoachingSession} className="coaching-session-form coaching-session-shell-form">
          <div className="grid" style={{ marginBottom: 8 }}>
            <div>
              <label>Search Client</label>
              <input
                value={coachingSessionEngagementSearch.client}
                onChange={(e) =>
                  setCoachingSessionEngagementSearch((prev) => ({ ...prev, client: e.target.value }))
                }
                placeholder="Type client"
              />
            </div>
            <div>
              <label>Search Coachee</label>
              <input
                value={coachingSessionEngagementSearch.coachee}
                onChange={(e) =>
                  setCoachingSessionEngagementSearch((prev) => ({ ...prev, coachee: e.target.value }))
                }
                placeholder="Type coachee"
              />
            </div>
          </div>
          <label>Engagement</label>
          <select
            value={coachingSessionForm.engagement_id}
            onChange={(e) =>
              setCoachingSessionForm((prev) => ({ ...prev, engagement_id: e.target.value }))
            }
            required
          >
            <option value="">Select engagement</option>
            {filteredSessionEngagementOptions.map((engagement) => (
              <option key={engagement.id} value={engagement.id}>
                {engagement.name} — {engagement.client_org} — {displayNameFromEmail(engagement.coach_email)}
              </option>
            ))}
          </select>

          <div className="grid coaching-session-core-grid">
            <div className="coaching-field-compact coaching-field-date">
              <label>Session Date</label>
              <input
                type="date"
                value={coachingSessionForm.session_date}
                onChange={(e) =>
                  setCoachingSessionForm((prev) => ({ ...prev, session_date: e.target.value }))
                }
                required
              />
            </div>
            <div className="coaching-field-compact coaching-field-outcome">
              <label>Session Outcome</label>
              <select
                value={coachingSessionForm.session_type}
                onChange={(e) =>
                  setCoachingSessionForm((prev) => ({ ...prev, session_type: e.target.value }))
                }
              >
                {coachingOutcomeOptions.map((option) => (
                  <option key={option} value={option}>
                    {formatTokenLabel(option)}
                  </option>
                ))}
              </select>
            </div>
            <div className="coaching-field-compact coaching-field-duration">
              <label>Duration (mins)</label>
              <input
                type="number"
                min="1"
                value={coachingSessionForm.duration_mins}
                onChange={(e) =>
                  setCoachingSessionForm((prev) => ({ ...prev, duration_mins: e.target.value }))
                }
              />
            </div>
            <div className="coaching-field-compact coaching-field-mode">
              <label>Mode</label>
              <select
                value={coachingSessionForm.delivery_mode}
                onChange={(e) =>
                  setCoachingSessionForm((prev) => ({ ...prev, delivery_mode: e.target.value }))
                }
              >
                <option value="video">Video</option>
                <option value="in_person">In person</option>
                <option value="phone">Phone</option>
              </select>
            </div>
            <div className="coaching-field-compact coaching-field-no-show">
              <label>No Show</label>
              <label className="inline-checkbox coaching-inline-checkbox">
                <input
                  type="checkbox"
                  checked={coachingSessionForm.session_type === 'no_show_chargeable'}
                  onChange={(e) =>
                    setCoachingSessionForm((prev) => ({
                      ...prev,
                      session_type: e.target.checked
                        ? 'no_show_chargeable'
                        : prev.session_type === 'no_show_chargeable'
                          ? 'completed'
                          : prev.session_type,
                    }))
                  }
                />{' '}
                Chargeable no-show
              </label>
            </div>
            <div className="coaching-field-compact coaching-field-lcp">
              <label>LCP de-brief</label>
              <label className="inline-checkbox coaching-inline-checkbox">
                <input
                  type="checkbox"
                  checked={Boolean(coachingSessionForm.lcp_debrief)}
                  onChange={(e) =>
                    setCoachingSessionForm((prev) => ({
                      ...prev,
                      lcp_debrief: e.target.checked,
                      lcp_debrief_date: e.target.checked ? prev.lcp_debrief_date : '',
                    }))
                  }
                />{' '}
                LCP de-brief completed
              </label>
              {coachingSessionForm.lcp_debrief ? (
                <>
                  <label style={{ marginTop: 6 }}>LCP de-brief Date</label>
                  <input
                    className="coaching-lcp-date-input"
                    ref={coachingLcpDateRef}
                    type="date"
                    value={coachingSessionForm.lcp_debrief_date}
                    onChange={(e) =>
                      setCoachingSessionForm((prev) => ({
                        ...prev,
                        lcp_debrief_date: e.target.value,
                      }))
                    }
                    required
                  />
                </>
              ) : null}
            </div>
            {!isConsultantSession ? (
              <div>
                <label>Invoiced</label>
                <label className="inline-checkbox coaching-inline-checkbox">
                  <input
                    type="checkbox"
                    checked={Boolean(coachingSessionForm.invoiced_to_adapsys)}
                    onChange={(e) =>
                      setCoachingSessionForm((prev) => ({
                        ...prev,
                        invoiced_to_adapsys: e.target.checked,
                      }))
                    }
                  />{' '}
                  Invoiced to Adapsys
                </label>
              </div>
            ) : null}
          </div>

          <label>Notes (optional)</label>
          <textarea
            rows={2}
            value={coachingSessionForm.notes}
            onChange={(e) =>
              setCoachingSessionForm((prev) => ({ ...prev, notes: e.target.value }))
            }
          />

          <div className="coaching-form-actions">
            <button type="submit" disabled={isSubmittingCoachingSession}>
              {isSubmittingCoachingSession
                ? editingCoachingSessionId
                  ? 'Saving Session Changes...'
                  : 'Logging Session...'
                : editingCoachingSessionId
                  ? 'Save Session Changes'
                  : 'Log Coaching Session'}
            </button>
            {editingCoachingSessionId ? (
              <button type="button" className="secondary" onClick={onCancelEditCoachingSession}>
                Cancel Session Edit
              </button>
            ) : null}
          </div>
        </form>
        {coachingStatus ? <div className="status" style={{ marginTop: 8 }}>{coachingStatus}</div> : null}
            </div>
            <div className="status" style={{ marginTop: 12 }}>
              Use Admin Console → Coaching Sessions for admin edits.
            </div>
          </>
        ) : (
          <div className="status" style={{ marginTop: 12 }}>
            Session logging is available in Consultant mode.
          </div>
        )}

        {isConsultantSession ? (
          <div id="coaching-engagement-planner" className="coaching-planner" style={{ marginTop: 12 }}>
            <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
              Engagement Planner (Search + History + Future)
            </h3>
            <div className="coaching-planner-search">
              <div>
                <label>Search Coachee</label>
                <input
                  value={coachingEngagementSearch.name}
                  onChange={(e) =>
                    setCoachingEngagementSearch((prev) => ({ ...prev, name: e.target.value }))
                  }
                  placeholder="Type coachee name"
                />
              </div>
              <div>
                <label>Search Client</label>
                <input
                  value={coachingEngagementSearch.client}
                  onChange={(e) =>
                    setCoachingEngagementSearch((prev) => ({ ...prev, client: e.target.value }))
                  }
                  placeholder="Type client"
                />
              </div>
            </div>
            <div className="status" style={{ marginBottom: 8 }}>
              {isPlannerSearchActive
                ? `Showing ${coachingPlannerRows.length} engagement(s).`
                : 'Search by coachee or client to show engagement cards.'}
            </div>
            {!isPlannerSearchActive ? (
              <div className="status">No cards shown until a search is entered.</div>
            ) : coachingPlannerRows.length === 0 ? (
              <div className="status">No matching coaching engagements.</div>
            ) : (
              coachingPlannerRows.map(({ engagement, pastSessions, todayAndFutureSessions, entitled, used, remaining, lcpEnabled, lcpEntitled, lcpUsed, lcpRemaining }) => (
                <div key={engagement.id} className="coaching-planner-card">
                  <div className="coaching-planner-head">
                    <strong>{engagement.name}</strong>
                    <span>
                      {engagement.client_org}
                      <label className="coaching-planner-invoice-tick" title="Personal checklist: invoiced Adapsys">
                        <input
                          type="checkbox"
                          checked={Boolean(plannerInvoiceTickByEngagementId[String(engagement.id)])}
                          onChange={(e) =>
                            setPlannerInvoiceTickByEngagementId((prev) => ({
                              ...prev,
                              [String(engagement.id)]: e.target.checked,
                            }))
                          }
                        />{' '}
                        Inv.
                      </label>
                    </span>
                  </div>
                  <div className="coaching-planner-summary">
                    <span className="coaching-planner-pill">Entitled: {entitled}</span>
                    <span className="coaching-planner-pill">Used: {used}</span>
                    <span className="coaching-planner-pill">Remaining: {remaining}</span>
                    <span className="coaching-planner-pill">
                      LCP: {lcpEnabled ? `${lcpUsed}/${lcpEntitled} (${lcpRemaining} left)` : 'Not offered'}
                    </span>
                    <span className="coaching-planner-pill">Upcoming: {todayAndFutureSessions.length}</span>
                    <span className="coaching-planner-pill">History: {pastSessions.length}</span>
                  </div>
                  <div className="coaching-planner-grid" style={{ marginTop: 8 }}>
                    <div>
                      <div className="status"><strong>Future Sessions</strong></div>
                      {todayAndFutureSessions.length === 0 ? (
                        <div className="status">No future sessions scheduled.</div>
                      ) : (
                        todayAndFutureSessions.slice(0, 6).map((session) => (
                          <div key={session.id} className="status coaching-planner-row">
                            {formatDateAu(session.session_date)} · {session.session_type}
                          </div>
                        ))
                      )}
                    </div>
                    <div>
                      <div className="status"><strong>Past Sessions</strong></div>
                      {pastSessions.length === 0 ? (
                        <div className="status">No past sessions yet.</div>
                      ) : (
                        pastSessions.slice(0, 6).map((session) => (
                          <div key={session.id} className="status coaching-planner-row">
                            {formatDateAu(session.session_date)} · {session.session_type}
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                  <div className="coaching-planner-add-row">
                    <label>+ Add future date</label>
                    <input
                      type="date"
                      value={plannerScheduleDraftByEngagementId[String(engagement.id)] || ''}
                      min={new Date().toISOString().slice(0, 10)}
                      onChange={(e) =>
                        setPlannerScheduleDraftByEngagementId((prev) => ({
                          ...prev,
                          [String(engagement.id)]: e.target.value,
                        }))
                      }
                    />
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => onAddPlannerFutureSession(engagement.id)}
                      disabled={schedulingPlannerEngagementId === String(engagement.id)}
                    >
                      {schedulingPlannerEngagementId === String(engagement.id) ? 'Adding...' : 'Add Future Session'}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        ) : null}

        {isConsultantSession ? (
          <div className="coaching-report-panel" style={{ marginTop: 12 }}>
            <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
              My Coachee Sessions Report
            </h3>
            <div className="report-date-row coaching-report-dates">
              <div>
                <label>Start Date (optional)</label>
                <input
                  type="date"
                  value={consultantCoachingReportFilters.start_date}
                  onChange={(e) =>
                    setConsultantCoachingReportFilters((prev) => ({ ...prev, start_date: e.target.value }))
                  }
                />
              </div>
              <div>
                <label>End Date (optional)</label>
                <input
                  type="date"
                  value={consultantCoachingReportFilters.end_date}
                  onChange={(e) =>
                    setConsultantCoachingReportFilters((prev) => ({ ...prev, end_date: e.target.value }))
                  }
                />
              </div>
            </div>
            {consultantCoachingReportFilters.start_date &&
            consultantCoachingReportFilters.end_date &&
            consultantCoachingReportFilters.start_date > consultantCoachingReportFilters.end_date ? (
              <div className="status">Start date must be on or before end date.</div>
            ) : null}
            <div className="status coaching-report-summary">
              Sessions shown: {consultantCoachingSessionRows.length} · Future sessions:{' '}
              {
                consultantCoachingSessionRows.filter(
                  (row) => String(row.session_date || '') >= new Date().toISOString().slice(0, 10)
                ).length
              }
            </div>
            {consultantCoachingSessionRows.length === 0 ? (
              <div className="status">No sessions found for the selected date range.</div>
            ) : (
              consultantCoachingSessionRows.map((row) => {
                const sessionLabel =
                  row.session_type === 'no_show_chargeable' ? 'chargeable no-show' : row.session_type;
                const isFuture = String(row.session_date || '') >= new Date().toISOString().slice(0, 10);
                return (
                  <div key={row.id} className={`status coaching-report-row ${isFuture ? 'is-future' : ''}`}>
                    <strong>{row.engagement?.name || 'Unknown coachee'}</strong> ({row.engagement?.client_org || 'Unknown client'}) ·{' '}
                    {formatDateAu(row.session_date)} · {sessionLabel}
                    {row.invoiced_to_adapsys ? ' · Invoiced to Adapsys' : ' · Not invoiced to Adapsys'}
                    {isFuture ? ' · Future session' : ''}
                    <div className="coaching-row-actions">
                      <button
                        type="button"
                        className="secondary coaching-row-action"
                        onClick={() => onDeleteCoachingSession(row)}
                        disabled={deletingCoachingSessionId === String(row.id)}
                      >
                        {deletingCoachingSessionId === String(row.id) ? 'Removing...' : 'Remove Session'}
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        ) : null}

        <div id="coaching-recent-edit" className="coaching-recent-panel" style={{ marginTop: 12 }}>
          <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
            Recent Coaching Sessions (Edit)
          </h3>
          {recentCoachingSessions.length === 0 ? (
            <div className="status">No coaching sessions logged yet.</div>
          ) : (
            <div className="coaching-recent-groups">
              {groupedRecentCoachingSessions.map((group) => (
                <details
                  key={group.key}
                  className="coaching-recent-group"
                  open={Boolean(openRecentCoachingGroupByKey[group.key])}
                  onToggle={(event) => {
                    const isOpen = Boolean(event.currentTarget.open);
                    setOpenRecentCoachingGroupByKey((prev) => ({
                      ...prev,
                      [group.key]: isOpen,
                    }));
                  }}
                >
                  <summary>
                    <strong>{group.client}</strong> — {group.coachee} ({group.sessions.length} session{group.sessions.length === 1 ? '' : 's'})
                  </summary>
                  <div className="coaching-recent-group-body">
                    {group.sessions.map((session) => {
                      const sessionLabel =
                        session.session_type === 'no_show_chargeable' ? 'chargeable no-show' : session.session_type;
                      const invoiceLabel = session.invoiced_to_adapsys ? 'invoiced' : 'not invoiced';
                      return (
                        <div key={session.id} className="status coaching-recent-row">
                          <strong>{group.coachee}</strong> ({group.client}) ·
                          {` ${formatDateAu(session.session_date)} · ${sessionLabel} · ${invoiceLabel}`}
                          <div className="coaching-row-actions">
                            <button
                              type="button"
                              className="secondary coaching-row-action"
                              onClick={() => onStartEditCoachingSession(session)}
                              disabled={deletingCoachingSessionId === String(session.id)}
                            >
                              Edit Session
                            </button>
                            <button
                              type="button"
                              className="secondary coaching-row-action"
                              onClick={() => onDeleteCoachingSession(session)}
                              disabled={deletingCoachingSessionId === String(session.id)}
                            >
                              {deletingCoachingSessionId === String(session.id) ? 'Removing...' : 'Remove Session'}
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </details>
              ))}
            </div>
          )}
        </div>

        <div className="status" style={{ marginTop: 10 }}>
          Engagements: {coachingEngagementOptions.length} | Sessions: {coachingSessions.length}
        </div>
        {coachingStatus ? <div className="status">{coachingStatus}</div> : null}

        <div className="coaching-entitlements-panel" style={{ marginTop: 10 }}>
          <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
            Entitlements
          </h3>
          {!isConsultantSession ? (
            <div className="status" style={{ marginBottom: 8 }}>
              Use the Admin Console tab for searchable spreadsheet-style coachee editing.
            </div>
          ) : null}
          <details>
            <summary>Open entitlement snapshot ({coachingEntitlementRows.length} coachees)</summary>
            <div style={{ marginTop: 8 }}>
              {coachingEntitlementRows.length === 0 ? (
                <div className="status">No engagements yet.</div>
              ) : (
                coachingEntitlementRows.map((row) => (
                  <div key={row.id} className={`status coaching-entitlement-row ${row.oneLeft ? 'is-alert' : ''}`}>
                    <strong>{row.name}</strong> ({row.client_org}) — Coach:{' '}
                    {coachNameByEmail[String(row.coach_email || '').trim().toLowerCase()] || displayNameFromEmail(row.coach_email)} · Entitled {row.entitled}{' '}
                    · Completed {row.used} · Remaining {row.remaining} · LCP{' '}
                    {row.lcpEnabled ? `${row.lcpUsed}/${row.lcpEntitled} (remaining ${row.lcpRemaining})` : 'not offered'}
                    {row.oneLeft ? ' · ⚠ 1 session left' : ''}
                  </div>
                ))
              )}
            </div>
          </details>
        </div>

      </section>

      {!isConsultantSession ? (
      <section id="tender-intelligence" className="card" style={sectionVisibilityStyle('tender-intelligence')}>
        <h2>Tender Intelligence (Pilot)</h2>
        <div className="grid">
          <div className="status">Total: {tenderSummary.total}</div>
          <div className="status">Urgent: {tenderSummary.urgent}</div>
          <div className="status">Pursue: {tenderSummary.pursue}</div>
          <div className="status">Monitor: {tenderSummary.monitor}</div>
          <div className="status">Ignore: {tenderSummary.ignore}</div>
          <div className="status">Consultant Led: {tenderSummary.led}</div>
        </div>

        {isConsultantSession ? null : (
          <form onSubmit={onTriageTender}>
            <label>New Tender Title</label>
            <input
              value={tenderForm.title}
              onChange={(e) => setTenderForm((prev) => ({ ...prev, title: e.target.value }))}
              placeholder="Paste tender title"
              required
            />
            <div className="grid">
              <div>
                <label>Issuer</label>
                <input
                  value={tenderForm.issuer}
                  onChange={(e) => setTenderForm((prev) => ({ ...prev, issuer: e.target.value }))}
                  placeholder="DFAT / Palladium / etc"
                />
              </div>
              <div>
                <label>Location</label>
                <input
                  value={tenderForm.location}
                  onChange={(e) => setTenderForm((prev) => ({ ...prev, location: e.target.value }))}
                  placeholder="PNG / Pacific / Australia"
                />
              </div>
            </div>
            <label>Summary</label>
            <textarea
              value={tenderForm.summary}
              onChange={(e) => setTenderForm((prev) => ({ ...prev, summary: e.target.value }))}
              rows={3}
              placeholder="Paste opportunity summary or email body"
            />
            <div className="grid">
              <div>
                <label>Contract Value</label>
                <input
                  value={tenderForm.contract_value}
                  onChange={(e) => setTenderForm((prev) => ({ ...prev, contract_value: e.target.value }))}
                  placeholder="$180,000"
                />
              </div>
              <div>
                <label>Tender URL</label>
                <input
                  value={tenderForm.tender_url}
                  onChange={(e) => setTenderForm((prev) => ({ ...prev, tender_url: e.target.value }))}
                  placeholder="https://..."
                />
              </div>
            </div>
            <div className="grid">
              <div>
                <label>EOI Deadline</label>
                <input
                  type="date"
                  value={tenderForm.eoi_deadline}
                  onChange={(e) => setTenderForm((prev) => ({ ...prev, eoi_deadline: e.target.value }))}
                />
              </div>
              <div>
                <label>Official Close</label>
                <input
                  type="date"
                  value={tenderForm.official_close_date}
                  onChange={(e) => setTenderForm((prev) => ({ ...prev, official_close_date: e.target.value }))}
                />
              </div>
            </div>
            <button type="submit" disabled={isSubmittingTender}>
              {isSubmittingTender ? 'Scoring Tender...' : 'Triage and Score Tender'}
            </button>
          </form>
        )}

        <label>Filter Feed</label>
        <select value={tenderFilter} onChange={(e) => setTenderFilter(e.target.value)}>
          <option value="all">All</option>
          <option value="pursue">Pursue</option>
          <option value="monitor">Monitor</option>
          <option value="ignore">Ignore</option>
          <option value="new">New</option>
        </select>

        {filteredTenders.length === 0 ? (
          <div className="status">No tenders in this filter yet.</div>
        ) : (
          filteredTenders.map((tender) => {
            const eoiDays = daysUntilIso(tender.eoi_deadline);
            const closeDays = daysUntilIso(tender.official_close_date);
            const leadName = displayNameFromEmail(tender.lead_consultant_email);
            const interestSummary = Object.entries(tender.consultant_interest || {})
              .map(([email, interest]) => `${displayNameFromEmail(email)} (${interest})`)
              .join(' · ');
            return (
              <div className="card" key={tender.id}>
                <div>
                  <strong>{tender.title}</strong>
                </div>
                <div className="status">
                  {tender.issuer || 'Unknown issuer'} · Score {tender.fit_score}/10 · {String(tender.status || 'new').toUpperCase()}
                </div>
                <div className="status">
                  Recommendation: {tender.recommendation} · Go/No-Go: {tender.go_no_go_score}/5 · Win Probability: {tender.win_probability}%
                </div>
                {tender.hidden_deadline_warning ? (
                  <div className="status">⚠️ {tender.hidden_deadline_warning}</div>
                ) : null}
                <div className="status">
                  EOI:{' '}
                  {tender.eoi_deadline
                    ? `${formatDateAu(tender.eoi_deadline)}${eoiDays === null ? '' : ` (${eoiDays} days)`}`
                    : 'n/a'}{' '}
                  · Close:{' '}
                  {tender.official_close_date
                    ? `${formatDateAu(tender.official_close_date)}${closeDays === null ? '' : ` (${closeDays} days)`}`
                    : 'n/a'}
                </div>
                <div className="status">{tender.strategic_value}</div>
                {leadName ? <div className="status">Consultant: {leadName}</div> : null}
                {interestSummary ? <div className="status">Consultant interest: {interestSummary}</div> : null}
                {tender.tender_url ? (
                  <div className="status">
                    <a href={tender.tender_url} target="_blank" rel="noreferrer">
                      Open tender source
                    </a>
                  </div>
                ) : null}
                <div className="grid" style={{ marginTop: 6 }}>
                  <button type="button" onClick={() => onTenderDecision(tender.id, 'lead')}>
                    I'll Lead
                  </button>
                  <button type="button" className="secondary" onClick={() => onTenderDecision(tender.id, 'watching')}>
                    Watching
                  </button>
                </div>
                <button type="button" className="secondary" onClick={() => onTenderDecision(tender.id, 'pass')}>
                  Pass
                </button>
                {isConsultantSession ? null : (
                  <div className="grid" style={{ marginTop: 4 }}>
                    <button type="button" onClick={() => onTenderDecision(tender.id, 'pursue')}>
                      Set Pursue
                    </button>
                    <button type="button" className="secondary" onClick={() => onTenderDecision(tender.id, 'monitor')}>
                      Set Monitor
                    </button>
                  </div>
                )}
              </div>
            );
          })
        )}
      </section>
      ) : null}

      {!isConsultantSession ? (
      <section className="card" style={sectionVisibilityStyle('expense-review')}>
        <h2>Live Data (Draft)</h2>
        <div className="status">Projects: {trips.length} | Expenses: {expenses.length}</div>
        <div className="status">{status}</div>
      </section>
      ) : null}

      {!isConsultantSession ? (
      <section className="card" style={sectionVisibilityStyle('expense-review')}>
        <h2>Program Expense Snapshot</h2>
        {tripExpenseSummaries.length === 0 ? (
          <div className="status">No grouped expense data yet.</div>
        ) : (
          <div className="expense-review-grid expense-review-grid-admin">
            {tripExpenseSummaries.map((row) => (
              <div className="card expense-snapshot-card" key={row.tripId}>
                <div className="status expense-snapshot-title">
                  {row.trip?.name || 'Unknown Activity'} · {formatClientProgramLabel(row.trip?.client_name, row.trip?.program_name)}
                </div>
                <div className="expense-snapshot-total">
                  <strong>{formatAud(row.totalAud)}</strong> total · Consultant{' '}
                  {formatAud(row.consultantAud)} · Admin {formatAud(row.adminAud)}
                </div>
                <div className="status expense-snapshot-meta">
                  {row.approvedCount} approved · {row.pendingCount} pending
                </div>
                <div className="status expense-snapshot-categories">
                  {Object.entries(row.byCategory)
                    .sort((a, b) => b[1] - a[1])
                    .map(([category, amount]) => `${category}: ${formatAud(amount)}`)
                    .join(' | ')}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
      ) : null}

      {!isConsultantSession ? (
      <section className="card" style={sectionVisibilityStyle('expense-review')}>
        <h2>Outstanding Expense Alerts (24h+)</h2>
        {adminOutstandingExpenseAlerts.length === 0 ? (
          <div className="status">No overdue consultant expense submissions detected.</div>
        ) : (
          <>
            <div className="receipt-reminder admin-alert-summary">
              {adminOutstandingExpenseAlerts.length} activity/activities are overdue by 24h+ with missing consultant expense submissions.
            </div>
            <div className="status admin-alert-guidance">
              Activate email reminders now? Use preview first, then send live reminders with a direct app link.
            </div>
            <div className="grid admin-alert-actions">
              <button type="button" onClick={() => onRunReminderAutomation({ dryRun: true })}>
                Preview Reminder Email Batch
              </button>
              <button type="button" className="secondary" onClick={() => onRunReminderAutomation({ dryRun: false })}>
                Activate Reminder Emails Now
              </button>
            </div>
            <div className="admin-alert-list">
            {adminOutstandingExpenseAlerts.map((alert) => (
              <div key={`overdue-${alert.trip.id}`} className="status consultant-expense-row admin-alert-row is-outstanding">
                <strong>{alert.trip.name}</strong> — {formatClientProgramLabel(alert.trip.client_name, alert.trip.program_name)}
                {' · End: '}
                {alert.projectEndDate ? formatDateAu(alert.projectEndDate) : 'No end date'}
                {' · Missing: '}
                {alert.outstandingConsultants.map((email) => deriveDisplayNameFromEmail(email) || email).join(', ')}
                {' · Last reminder: '}
                {reminderLastSentByTripId[String(alert.trip.id)]
                  ? `${formatDateTimeAu(reminderLastSentByTripId[String(alert.trip.id)].last_sent_at)} (${formatTokenLabel(
                      reminderLastSentByTripId[String(alert.trip.id)].reminder_type
                    )})`
                  : 'Not sent yet'}
              </div>
            ))}
            </div>
          </>
        )}
      </section>
      ) : null}

      {!isConsultantSession ? (
      <section className="card" style={sectionVisibilityStyle('expense-review')}>
        <h2>Automation Controls (Admin)</h2>
        <label>
          <input
            type="checkbox"
            checked={automationDryRun}
            onChange={(e) => setAutomationDryRun(e.target.checked)}
          />{' '}
          Dry run (recommended while validating)
        </label>
        <div className="grid" style={{ marginTop: 12 }}>
          <button type="button" onClick={onRunReminderAutomation}>
            Run 24h Reminder Automation
          </button>
          <button type="button" onClick={onRunCeoSignoff}>
            Run Admin Sign-off Automation
          </button>
        </div>
      </section>
      ) : null}

      {isClientViewerSession ? (
      <section id="reports" className="card" style={sectionVisibilityStyle('reports')}>
        <h2>Client Coaching Report</h2>
        <div className="status" style={{ marginBottom: 10 }}>
          Read-only progress view. Fields shown: coachee, coach, entitled sessions, taken/left, no-shows, session dates, and LCP when available.
        </div>
        <div className="report-date-row">
          <div>
            <label>Start Date (optional)</label>
            <input
              type="date"
              value={clientReportFilters.start_date}
              onChange={(e) => setClientReportFilters((prev) => ({ ...prev, start_date: e.target.value }))}
            />
          </div>
          <div>
            <label>End Date (optional)</label>
            <input
              type="date"
              value={clientReportFilters.end_date}
              onChange={(e) => setClientReportFilters((prev) => ({ ...prev, end_date: e.target.value }))}
            />
          </div>
        </div>
        <div className="report-action-row" style={{ marginTop: 10 }}>
          <button type="button" onClick={refresh} disabled={isLoadingClientCoachingSummary || !isClientReportsFeatureEnabled}>
            {isLoadingClientCoachingSummary ? 'Refreshing...' : 'Refresh Client Report'}
          </button>
          <button type="button" className="secondary" onClick={() => window.print()} disabled={!clientCoachingSummaryRows.length}>
            Print Report
          </button>
        </div>
        {clientCoachingSummaryStatus ? <div className="status report-status-surface">{clientCoachingSummaryStatus}</div> : null}
        {!isClientReportsFeatureEnabled ? (
          <div className="status">Client reports are feature-flagged off. Set localStorage.adapsys_client_reports_enabled = 1 to test.</div>
        ) : clientCoachingSummaryRows.length === 0 ? (
          <div className="status">No coaching records found for the selected filters.</div>
        ) : (
          <div className="reports-panel" style={{ marginTop: 10 }}>
            {clientCoachingSummaryRows.map((row) => (
              <div key={`${row.coachee}-${row.coach_name}`} className="status coaching-entitlement-row" style={{ marginBottom: 8 }}>
                <strong>{row.coachee}</strong> · Coach: {row.coach_name} · Entitled {row.entitled_sessions} · Taken {row.sessions_taken} · Left {row.sessions_left} · No-shows {row.no_show_count}
                {row.lcp_available ? ` · LCP ${row.lcp_taken || 0}/${row.lcp_entitled || 0}` : ''}
                <div className="status" style={{ marginTop: 4 }}>
                  Session dates: {row.session_dates?.length ? row.session_dates.join(', ') : 'No sessions logged'}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
      ) : !isConsultantSession ? (
      <section id="reports" className="card" style={sectionVisibilityStyle('reports')}>
        <h2>Reports Hub</h2>
        <div className="status" style={{ marginBottom: 10 }}>
          <strong>Quick help on this page:</strong> 1) Choose report scope (client, coach, or coachee), 2) Set optional date range,
          3) Click Preview first, then Download PDF when ready.
        </div>
        <div className="reports-hub-grid">
          {!isConsultantSession ? (
            <div className="reports-panel">
              <div className="reports-panel-head">
                <div>
                  <h3>Adapsys Australia Pacific Coaching Report</h3>
                  <div className="status">Export by client, coach, or coachee with optional date window.</div>
                </div>
                <div className="reports-micro-chips">
                  <span className="reports-chip">Clients: {coachingClientOptions.length}</span>
                  <span className="reports-chip">Coaches: {coachingCoachOptions.length}</span>
                  <span className="reports-chip">Coachees: {coachingCoacheeOptions.length}</span>
                </div>
              </div>

              <div className="grid coaching-report-scope-row">
                <div>
                  <label>Report By</label>
                  <select
                    value={coachingReportFilters.report_by}
                    onChange={(e) =>
                      setCoachingReportFilters((prev) => ({ ...prev, report_by: e.target.value }))
                    }
                  >
                    <option value="client">Client</option>
                    <option value="coachee">Coachee</option>
                    <option value="coach">Coach</option>
                  </select>
                </div>
                {coachingReportFilters.report_by === 'client' ? (
                  <div>
                    <label>Client</label>
                    <select
                      value={coachingReportFilters.client_org}
                      onChange={(e) =>
                        setCoachingReportFilters((prev) => ({ ...prev, client_org: e.target.value }))
                      }
                    >
                      <option value="">Select client</option>
                      {coachingClientOptions.map((clientName) => (
                        <option key={clientName} value={clientName}>
                          {clientName}
                        </option>
                      ))}
                    </select>
                  </div>
                ) : coachingReportFilters.report_by === 'coach' ? (
                  <div>
                    <label>Coach</label>
                    <select
                      value={coachingReportFilters.coach_email}
                      onChange={(e) =>
                        setCoachingReportFilters((prev) => ({ ...prev, coach_email: e.target.value }))
                      }
                    >
                      <option value="">Select coach</option>
                      {coachingCoachOptions.map((coachEmail) => (
                        <option key={coachEmail} value={coachEmail}>
                          {coachNameByEmail[coachEmail] || coachEmail}
                        </option>
                      ))}
                    </select>
                  </div>
                ) : coachingReportFilters.report_by === 'coachee' ? (
                  <div>
                    <label>Coachee</label>
                    <select
                      value={coachingReportFilters.coachee_name}
                      onChange={(e) =>
                        setCoachingReportFilters((prev) => ({ ...prev, coachee_name: e.target.value }))
                      }
                    >
                      <option value="">Select coachee</option>
                      {coachingCoacheeOptions.map((coacheeName) => (
                        <option key={coacheeName} value={coacheeName}>
                          {coacheeName}
                        </option>
                      ))}
                    </select>
                  </div>
                ) : null}
              </div>

              <div className="report-date-row">
                <div>
                  <label>Start Date (optional)</label>
                  <input
                    type="date"
                    value={coachingReportFilters.start_date}
                    onChange={(e) =>
                      setCoachingReportFilters((prev) => ({ ...prev, start_date: e.target.value }))
                    }
                  />
                </div>
                <div>
                  <label>End Date (optional)</label>
                  <input
                    type="date"
                    value={coachingReportFilters.end_date}
                    onChange={(e) =>
                      setCoachingReportFilters((prev) => ({ ...prev, end_date: e.target.value }))
                    }
                  />
                </div>
              </div>

              {!coachingReportsReady ? (
                <div className="status report-empty-state">
                  No coaching data yet. Add coaching engagements or sessions first, then generate this report.
                </div>
              ) : null}

              <div className="report-action-row report-action-row-sticky">
                <button
                  type="button"
                  onClick={onPreviewCoachingReport}
                  disabled={isPreviewingCoachingReport || !coachingReportsReady}
                >
                  {isPreviewingCoachingReport ? 'Generating Preview...' : 'Preview Coaching Report'}
                </button>
                <button
                  type="button"
                  onClick={onDownloadCoachingReportPdf}
                  disabled={isDownloadingCoachingReportPdf || !coachingReportsReady}
                >
                  {isDownloadingCoachingReportPdf ? 'Preparing PDF...' : 'Download Coaching PDF'}
                </button>
              </div>

              {coachingReportStatus ? <div className="status report-status-surface">{coachingReportStatus}</div> : null}
              {coachingReportPreviewHtml ? (
                <iframe
                  title="Adapsys Australia Pacific Coaching Report Preview"
                  srcDoc={coachingReportPreviewHtml}
                  className="report-preview-frame"
                />
              ) : null}
            </div>
          ) : (
            <div className="reports-panel">
              <div className="status">Coaching report generation is available in Admin/Finance sessions.</div>
            </div>
          )}

          <div className="reports-panel">
            <div className="reports-panel-head">
              <div>
                <h3>Adapsys Australia Pacific - Expenses Report</h3>
                <div className="status">Build a branded project expense pack for client invoicing.</div>
              </div>
              <div className="reports-micro-chips">
                <span className="reports-chip">Projects: {trips.length}</span>
                <span className="reports-chip">Outstanding: {portfolioInvoicing.outstandingCount}</span>
              </div>
            </div>

            <div className="expense-report-controls">
              <div className="expense-report-picker-row">
                <div className="expense-report-project">
                  <label>Client</label>
                  <select
                    value={selectedReportClient}
                    onChange={(e) => {
                      setSelectedReportClient(e.target.value);
                      setReportPreviewHtml('');
                      setReportPreviewStatus('');
                    }}
                  >
                    <option value="">All clients</option>
                    {expenseReportClientOptions.map((clientName) => (
                      <option key={clientName} value={clientName}>
                        {clientName}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="expense-report-project">
                  <label>Activity</label>
                  <select
                    value={selectedReportTripId}
                    onChange={(e) => {
                      setSelectedReportTripId(e.target.value);
                      setReportPreviewHtml('');
                      setReportPreviewStatus('');
                    }}
                  >
                    <option value="">Select activity</option>
                    {expenseReportProjectOptions.map((trip) => (
                      <option key={trip.id} value={trip.id}>
                        {trip.name} — {formatClientProgramLabel(trip.client_name, trip.program_name)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="expense-report-date-range">
                <div>
                  <label>Start Date (optional)</label>
                  <input
                    type="date"
                    value={expenseReportFilters.start_date}
                    onChange={(e) =>
                      setExpenseReportFilters((prev) => ({ ...prev, start_date: e.target.value }))
                    }
                  />
                </div>
                <div>
                  <label>End Date (optional)</label>
                  <input
                    type="date"
                    value={expenseReportFilters.end_date}
                    onChange={(e) =>
                      setExpenseReportFilters((prev) => ({ ...prev, end_date: e.target.value }))
                    }
                  />
                </div>
              </div>
            </div>

            {!expenseReportsReady ? (
              <div className="status report-empty-state">
                No projects available for reporting. Create a project first, then return here.
              </div>
            ) : null}

            <div className="report-action-row report-action-row-sticky">
              <button type="button" onClick={onPreviewExpensePack} disabled={isPreviewingExpensePack || !expenseReportsReady}>
                {isPreviewingExpensePack ? 'Generating Preview...' : 'Preview Expense Report'}
              </button>
              <button type="button" onClick={onDownloadExpensePackPdf} disabled={isDownloadingExpensePackPdf || !expenseReportsReady}>
                {isDownloadingExpensePackPdf ? 'Preparing PDF...' : 'Download Expense PDF'}
              </button>
            </div>

            {reportPreviewStatus ? <div className="status report-status-surface">{reportPreviewStatus}</div> : null}
            {reportPreviewHtml ? (
              <iframe
                title="Adapsys Australia Pacific - Expenses Report Preview"
                srcDoc={reportPreviewHtml}
                className="report-preview-frame"
              />
            ) : null}
          </div>
        </div>
      </section>
      ) : null}

      {!isConsultantSession ? (
      <section id="expense-review" className="card" style={sectionVisibilityStyle('expense-review')}>
        <h2>Expense Review (Admin)</h2>
        <div className={`xero-integration-banner ${
          !isXeroSyncFeatureEnabled || !expenseXeroIntegrationStatus?.enabled
            ? 'is-warning'
            : expenseXeroIntegrationStatus?.mode === 'stub'
              ? 'is-info'
              : 'is-success'
        }`}>
          {xeroIntegrationBannerText}
        </div>
        {expenses.length === 0 ? (
          <div className="status">No expenses submitted yet.</div>
        ) : (
          expenses.map((expense) => (
            <div className="card" key={expense.id}>
              <div className="status">{formatDateAu(expense.expense_date)} · {expense.category}</div>
              <div>{formatAud(expense.amount_aud)} · {expense.status}</div>
              <div className="status">
                Submitted by: {expense.submitted_by_email} ({expense.submitted_by_role})
              </div>
              <div className="status">
                Project: {trips.find((trip) => String(trip.id) === String(expense.trip_id))?.name || 'Unknown project'}
              </div>
              {isXeroSyncFeatureEnabled ? (
                <div className="expense-xero-sync-panel" role="status" aria-live="polite">
                  <div className="expense-xero-sync-head">
                    <strong>Xero Sync</strong>
                    <span className="status">
                      Status: {formatTokenLabel(expenseXeroSyncById[String(expense.id)]?.sync_status || 'not_synced')}
                    </span>
                  </div>
                  {expenseXeroSyncById[String(expense.id)]?.last_synced_at ? (
                    <div className="status">
                      Last synced: {formatDateTimeAu(expenseXeroSyncById[String(expense.id)]?.last_synced_at)}
                    </div>
                  ) : null}
                  {expenseXeroSyncById[String(expense.id)]?.error ? (
                    <div className="status">Sync note: {expenseXeroSyncById[String(expense.id)]?.error}</div>
                  ) : null}
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => onPushExpenseToXero(expense.id)}
                    disabled={
                      syncingExpenseId === String(expense.id) ||
                      (expense.status !== 'approved' && expense.status !== 'invoiced')
                    }
                  >
                    {syncingExpenseId === String(expense.id)
                      ? 'Syncing to Xero...'
                      : (expenseXeroSyncById[String(expense.id)]?.sync_status || 'not_synced') === 'not_synced'
                        ? 'Push to Xero'
                        : 'Retry Xero Sync'}
                  </button>
                  {expense.status !== 'approved' && expense.status !== 'invoiced' ? (
                    <div className="status">Approve this expense before pushing to Xero.</div>
                  ) : null}
                </div>
              ) : null}
              <label>Move to another project (if initially logged to holding project)</label>
              <div className="grid">
                <select
                  value={tripDraftByExpenseId[String(expense.id)] || String(expense.trip_id || '')}
                  onChange={(e) =>
                    setTripDraftByExpenseId((prev) => ({
                      ...prev,
                      [String(expense.id)]: e.target.value,
                    }))
                  }
                >
                  <option value="">Select activity</option>
                  {trips.map((trip) => (
                    <option key={trip.id} value={trip.id}>
                      {trip.name} — {formatClientProgramLabel(trip.client_name, trip.program_name)}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => onMoveExpenseToProject(expense.id)}
                  disabled={movingExpenseId === String(expense.id)}
                >
                  {movingExpenseId === String(expense.id) ? 'Moving...' : 'Move Expense to Activity'}
                </button>
              </div>
              {expense.receipt_url ? (
                <div className="receipt-preview-wrap">
                  <img
                    className="receipt-thumb"
                    src={expense.receipt_thumb_url || expense.receipt_url}
                    alt="Receipt thumbnail"
                  />
                  <div className="status">
                    <a href={expense.receipt_url} target="_blank" rel="noreferrer">
                      Open full-size receipt
                    </a>
                  </div>
                </div>
              ) : (
                <>
                  <div className="status">No receipt reason: {expense.no_receipt_reason}</div>
                  <label>Attach receipt now (URL)</label>
                  <input
                    value={receiptDraftByExpenseId[String(expense.id)]?.receipt_url || ''}
                    onChange={(e) =>
                      setReceiptDraftByExpenseId((prev) => ({
                        ...prev,
                        [String(expense.id)]: {
                          ...(prev[String(expense.id)] || {}),
                          receipt_url: e.target.value,
                        },
                      }))
                    }
                    placeholder="Paste receipt URL"
                  />
                  <label>Receipt thumbnail URL (optional)</label>
                  <input
                    value={receiptDraftByExpenseId[String(expense.id)]?.receipt_thumb_url || ''}
                    onChange={(e) =>
                      setReceiptDraftByExpenseId((prev) => ({
                        ...prev,
                        [String(expense.id)]: {
                          ...(prev[String(expense.id)] || {}),
                          receipt_thumb_url: e.target.value,
                        },
                      }))
                    }
                    placeholder="Optional thumbnail URL"
                  />
                  <button
                    type="button"
                    onClick={() => onAttachExpenseReceipt(expense.id)}
                    disabled={attachingReceiptExpenseId === String(expense.id)}
                  >
                    {attachingReceiptExpenseId === String(expense.id)
                      ? 'Attaching Receipt...'
                      : 'Attach Receipt to This Expense'}
                  </button>
                </>
              )}
              {expense.status !== 'approved' && expense.status !== 'invoiced' ? (
                <button type="button" onClick={() => onApproveExpense(expense.id)}>
                  Approve
                </button>
              ) : null}
              {expense.status === 'approved' ? (
                <button type="button" onClick={() => onMarkExpenseInvoiced(expense.id)}>
                  Mark Invoiced
                </button>
              ) : null}
              <button
                type="button"
                className="secondary"
                onClick={() => onDeleteExpense(expense.id)}
                disabled={deletingExpenseId === String(expense.id)}
              >
                {deletingExpenseId === String(expense.id) ? 'Deleting...' : 'Delete Expense'}
              </button>
            </div>
          ))
        )}
      </section>
      ) : null}

      {!isConsultantSession ? (
      <section id="ato-rates" className="card" style={sectionVisibilityStyle('ato-rates')}>
        <details>
          <summary>ATO Rates (hidden by default — click to open)</summary>
          <div className="status" style={{ marginTop: 8 }}>
            Enter meal amounts in AUD (not percentages). Incidental is auto-applied to every trip day except the final day.
          </div>
          {atoRates.map((rate) => {
            const key = String(rate.id);
            const draft = atoRateDraftById[key] || {};
            return (
              <div className="card" key={rate.id}>
                <div className="status"><strong>{rate.country}</strong></div>
                <div className="grid">
                  <div>
                    <label>ATO Financial Year</label>
                    <select
                      value={normalizeFinancialYearLabel(draft.tax_year) || perDiemFinancialYearOptions[0] || ''}
                      onChange={(e) =>
                        setAtoRateDraftById((prev) => ({
                          ...prev,
                          [key]: { ...prev[key], tax_year: e.target.value },
                        }))
                      }
                    >
                      {atoFinancialYearOptions.map((yearOption) => (
                        <option key={`ato-tax-year-${key}-${yearOption}`} value={yearOption}>
                          {yearOption}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label>Incidental Midpoint (AUD)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={draft.incidental_midpoint_aud ?? ''}
                      onChange={(e) =>
                        setAtoRateDraftById((prev) => ({
                          ...prev,
                          [key]: { ...prev[key], incidental_midpoint_aud: e.target.value },
                        }))
                      }
                    />
                  </div>
                  <div>
                    <label>Breakfast (AUD)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={draft.breakfast_aud ?? ''}
                      onChange={(e) =>
                        setAtoRateDraftById((prev) => ({
                          ...prev,
                          [key]: { ...prev[key], breakfast_aud: e.target.value },
                        }))
                      }
                    />
                  </div>
                  <div>
                    <label>Lunch (AUD)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={draft.lunch_aud ?? ''}
                      onChange={(e) =>
                        setAtoRateDraftById((prev) => ({
                          ...prev,
                          [key]: { ...prev[key], lunch_aud: e.target.value },
                        }))
                      }
                    />
                  </div>
                  <div>
                    <label>Dinner (AUD)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={draft.dinner_aud ?? ''}
                      onChange={(e) =>
                        setAtoRateDraftById((prev) => ({
                          ...prev,
                          [key]: { ...prev[key], dinner_aud: e.target.value },
                        }))
                      }
                    />
                  </div>
                  <div>
                    <label>Rate Active</label>
                    <select
                      value={draft.active ? 'yes' : 'no'}
                      onChange={(e) =>
                        setAtoRateDraftById((prev) => ({
                          ...prev,
                          [key]: { ...prev[key], active: e.target.value === 'yes' },
                        }))
                      }
                    >
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                    </select>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => onSaveAtoRate(rate.id)}
                  disabled={savingAtoRateId === key}
                >
                  {savingAtoRateId === key ? 'Saving ATO Rate...' : `Save ${rate.country} ATO Rate`}
                </button>
              </div>
            );
          })}
        </details>
      </section>
      ) : null}

      {isAdminSession ? (
        <section id="admin-console" className="card admin-console-shell" style={sectionVisibilityStyle('admin-console')}>
          <h2>Admin Console</h2>
          <div className="status admin-console-intro" style={{ marginBottom: 10 }}>
            Admin workspace. Use one section at a time for cleaner editing.
          </div>
          <div className="status admin-console-intro" style={{ marginBottom: 10 }}>
            <strong>Business Details:</strong> Adapsys Australia Pacific · ABN 56 623 973 446
          </div>
          <div className="status admin-console-quick" style={{ marginBottom: 10 }}>
            <strong>Quick action:</strong> Batch coaching entry lives in <strong>Coaching</strong> tab.
            <button
              type="button"
              className="secondary"
              style={{ marginLeft: 10 }}
              onClick={() => {
                setActiveScreenTabId('coaching-module');
                setCoachingStatus('Batch entry is open in Coaching tab.');
              }}
            >
              Open Batch Coaching Entry
            </button>
          </div>

          <div className="admin-console-snapshot" style={{ marginBottom: 10 }}>
            <span className="admin-console-snapshot-item">Projects (total): <strong>{trips.length}</strong></span>
            <span className="admin-console-snapshot-item">Active Clients: <strong>{dashboardMetrics.activeClients}</strong></span>
            <span className="admin-console-snapshot-item">Coachees: <strong>{coachingEngagements.length}</strong></span>
            <span className="admin-console-snapshot-item">Sessions: <strong>{coachingSessions.length}</strong></span>
          </div>

          <div className="admin-savings-panel" style={{ marginBottom: 10 }}>
            <div className="admin-savings-head">
              <strong>Savings Snapshot (Monthly Estimate)</strong>
              <span className="status">Demo assumptions can be tuned via localStorage savings keys.</span>
            </div>
            <div className="admin-savings-grid">
              <div className="admin-savings-item">
                <div className="status">Client report prep</div>
                <strong>{savingsSnapshot.reportHours.toFixed(1)} hrs</strong>
              </div>
              <div className="admin-savings-item">
                <div className="status">Workflow follow-ups</div>
                <strong>{savingsSnapshot.workbookHours.toFixed(1)} hrs</strong>
              </div>
              <div className="admin-savings-item">
                <div className="status">Xero double-entry reduction</div>
                <strong>{savingsSnapshot.expenseHours.toFixed(1)} hrs</strong>
              </div>
              <div className="admin-savings-item">
                <div className="status">Total monthly time saved</div>
                <strong>{savingsSnapshot.totalHours.toFixed(1)} hrs</strong>
              </div>
              <div className="admin-savings-item">
                <div className="status">Estimated monthly value</div>
                <strong>{formatAud(savingsSnapshot.totalAud)}</strong>
              </div>
            </div>
            <div className="status" style={{ marginTop: 6 }}>
              Xero-ready expenses in this snapshot: {savingsSnapshot.xeroCandidateCount}. Hourly rate assumption: {formatAud(savingsSnapshot.hourlyRate)}.
            </div>
          </div>

          <div className="admin-console-nav" style={{ marginBottom: 12 }}>
            <button
              type="button"
              className={`admin-console-tab ${adminConsoleSection === 'projects' ? 'is-active' : 'secondary'}`}
              onClick={() => setAdminConsoleSection('projects')}
            >
              Projects
            </button>
            <button
              type="button"
              className={`admin-console-tab ${adminConsoleSection === 'lookups' ? 'is-active' : 'secondary'}`}
              onClick={() => setAdminConsoleSection('lookups')}
            >
              Lookup Files
            </button>
            <button
              type="button"
              className={`admin-console-tab ${adminConsoleSection === 'engagements' ? 'is-active' : 'secondary'}`}
              onClick={() => setAdminConsoleSection('engagements')}
            >
              Coaching Engagements
            </button>
            <button
              type="button"
              className={`admin-console-tab ${adminConsoleSection === 'sessions' ? 'is-active' : 'secondary'}`}
              onClick={() => setAdminConsoleSection('sessions')}
            >
              Coaching Sessions
            </button>
            <button
              type="button"
              className={`admin-console-tab ${adminConsoleSection === 'contracts' ? 'is-active' : 'secondary'}`}
              onClick={() => setAdminConsoleSection('contracts')}
            >
              Contracts
            </button>
            <button
              type="button"
              className={`admin-console-tab ${adminConsoleSection === 'consultant-profiles' ? 'is-active' : 'secondary'}`}
              onClick={() => setAdminConsoleSection('consultant-profiles')}
            >
              Consultant Profiles
            </button>
          </div>

          <div className="admin-console-quick-filters" style={{ marginBottom: 12 }}>
            <button
              type="button"
              className={`admin-quick-chip ${adminConsoleSection === 'projects' ? 'is-active' : ''}`}
              onClick={() => setAdminConsoleSection('projects')}
            >
              Projects {adminTripDirtyCount ? `(${adminTripDirtyCount} unsaved)` : ''}
            </button>
            <button
              type="button"
              className={`admin-quick-chip ${adminConsoleSection === 'engagements' || adminConsoleSection === 'sessions' ? 'is-active' : ''}`}
              onClick={() => setAdminConsoleSection('engagements')}
            >
              Coaching {adminEngagementDirtyCount ? `(${adminEngagementDirtyCount} unsaved)` : ''}
            </button>
            <button
              type="button"
              className={`admin-quick-chip ${adminConsoleSection === 'lookups' ? 'is-active' : ''}`}
              onClick={() => setAdminConsoleSection('lookups')}
            >
              Lookups {adminLookupDirtyCount ? `(${adminLookupDirtyCount} unsaved)` : ''}
            </button>
            <button
              type="button"
              className={`admin-quick-chip ${adminConsoleSection === 'contracts' ? 'is-active' : ''}`}
              onClick={() => setAdminConsoleSection('contracts')}
            >
              Contracts
            </button>
            <button
              type="button"
              className={`admin-quick-chip ${adminConsoleSection === 'consultant-profiles' ? 'is-active' : ''}`}
              onClick={() => setAdminConsoleSection('consultant-profiles')}
            >
              Consultant Profiles
            </button>
          </div>

          {adminConsoleSection === 'projects' ? (
          <>
          <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
            Bulk Add Activities
          </h3>
          <div className="status" style={{ marginBottom: 8 }}>
            Best place for initial setup when you already know client/program, consultants, and dates.
          </div>
          <form onSubmit={onSubmitAdminBulkActivities} style={{ marginBottom: 12 }}>
            <div className="admin-table-wrap">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Client</th>
                    <th>Program (optional)</th>
                    <th>Activity</th>
                    <th>Consultants</th>
                    <th>Start</th>
                    <th>End</th>
                    <th>Expense Report?</th>
                    <th>Row</th>
                  </tr>
                </thead>
                <tbody>
                  {adminBulkActivityRows.map((row, index) => (
                    <tr key={row.id}>
                      <td>
                        <select value={row.client_name} onChange={(e) => onAdminBulkActivityFieldChange(row.id, 'client_name', e.target.value)} style={{ minWidth: 190 }}>
                          <option value="">Select client</option>
                          {clientOptions.map((clientName) => (
                            <option key={`bulk-client-${row.id}-${clientName}`} value={clientName}>{clientName}</option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <input
                          list={`bulk-program-options-${row.id}`}
                          value={row.program_name}
                          onChange={(e) => onAdminBulkActivityFieldChange(row.id, 'program_name', e.target.value)}
                          placeholder="Optional"
                          style={{ minWidth: 170 }}
                        />
                        <datalist id={`bulk-program-options-${row.id}`}>
                          {allProgramOptions.map((programName) => (
                            <option key={`bulk-program-${row.id}-${programName}`} value={programName} />
                          ))}
                        </datalist>
                      </td>
                      <td>
                        <input value={row.name} onChange={(e) => onAdminBulkActivityFieldChange(row.id, 'name', e.target.value)} placeholder="Activity name" style={{ minWidth: 220 }} />
                      </td>
                      <td>
                        <select
                          multiple
                          value={Array.from(new Set([row.consultant_email, ...(row.assigned_consultants || [])].filter(Boolean)))}
                          onChange={(e) => {
                            const selectedEmails = Array.from(e.target.selectedOptions || []).map((option) => option.value);
                            const [lead = '', ...assigned] = selectedEmails;
                            onAdminBulkActivityFieldChange(row.id, 'consultant_email', lead);
                            onAdminBulkActivityFieldChange(row.id, 'assigned_consultants', assigned);
                          }}
                          style={{ minWidth: 250, minHeight: 98 }}
                        >
                          {orderedConsultants.map((consultant) => (
                            <option key={`bulk-consultant-${row.id}-${consultant.email}`} value={consultant.email}>{consultant.name}</option>
                          ))}
                        </select>
                        <div className="status" style={{ marginTop: 4 }}>Lead is first selected. Names shown; emails stored.</div>
                      </td>
                      <td><input type="date" value={row.project_start_date} onChange={(e) => onAdminBulkActivityFieldChange(row.id, 'project_start_date', e.target.value)} style={{ minWidth: 135 }} /></td>
                      <td><input type="date" value={row.project_end_date} onChange={(e) => onAdminBulkActivityFieldChange(row.id, 'project_end_date', e.target.value)} style={{ minWidth: 135 }} /></td>
                      <td>
                        <label className="inline-checkbox" style={{ margin: 0 }}>
                          <input type="checkbox" checked={Boolean(row.expense_report_required)} onChange={(e) => onAdminBulkActivityFieldChange(row.id, 'expense_report_required', e.target.checked)} />{' '}
                          Yes
                        </label>
                      </td>
                      <td>
                        <button type="button" className="secondary" onClick={() => onRemoveAdminBulkActivityRow(row.id)} disabled={adminBulkActivityRows.length === 1}>
                          Remove
                        </button>
                        <div className="status" style={{ marginTop: 6 }}>#{index + 1}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
              <button type="button" className="secondary" onClick={onAddAdminBulkActivityRow}>Add Row</button>
              <button type="submit" disabled={isSubmittingAdminBulkActivities}>
                {isSubmittingAdminBulkActivities ? 'Creating Activities...' : 'Create Activities in Bulk'}
              </button>
            </div>
            {adminBulkActivityStatus ? <div className="status" style={{ marginTop: 8 }}>{adminBulkActivityStatus}</div> : null}
          </form>

          <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
            Activities (Quick Edit)
          </h3>
          <div className="admin-console-snapshot" style={{ marginBottom: 8 }}>
            <div><strong>{travelBookingSummary.total_required || 0}</strong><span>Travel Requests</span></div>
            <div><strong>{travelBookingSummary.outstanding_to_book || 0}</strong><span>Travel To Book</span></div>
            <div><strong>{travelBookingSummary.booked || 0}</strong><span>Booked Travel</span></div>
            <div><strong>{travelBookingSummary.need_expense_prompt || 0}</strong><span>Prompt Add Expense</span></div>
          </div>
          <div className="status" style={{ marginBottom: 8 }}>
            Key fields are shown first. Open "Advanced" in a row for less-changed fields.
          </div>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Activity</th>
                  <th>Consultant</th>
                  <th>Client</th>
                  <th>Program (optional)</th>
                  <th>Country</th>
                  <th>Start</th>
                  <th>End</th>
                  <th>Advanced</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {trips.map((trip) => {
                  const key = String(trip.id);
                  const draft = adminTripDraftById[key] || {};
                  const isTripDirty = Boolean(adminTripDraftById[key]);
                  const selectedConsultant = String(draft.consultant_email ?? trip.consultant_email ?? '').trim().toLowerCase();
                  const leadConsultantOptions = [selectedConsultant, ...allConsultantEmails]
                    .filter(Boolean)
                    .filter((value, idx, arr) => arr.indexOf(value) === idx)
                    .sort((a, b) => {
                      const byName = displayNameFromEmail(a).localeCompare(displayNameFromEmail(b));
                      if (byName !== 0) return byName;
                      return a.localeCompare(b);
                    });
                  const selectedClient = String(draft.client_name ?? trip.client_name ?? '').trim();
                  const clientSelectOptions = [selectedClient, ...clientOptions]
                    .filter(Boolean)
                    .filter((value, idx, arr) => arr.indexOf(value) === idx)
                    .sort((a, b) => a.localeCompare(b));
                  const selectedProgram = String(draft.program_name ?? trip.program_name ?? '').trim();
                  const programSelectOptions = [selectedProgram, ...allProgramOptions]
                    .filter(Boolean)
                    .filter((value, idx, arr) => arr.indexOf(value) === idx)
                    .sort((a, b) => a.localeCompare(b));
                  const selectedCountry = String(draft.destination_country ?? trip.destination_country ?? '').trim();
                  const countrySelectOptions = [selectedCountry, ...adminCountryOptions]
                    .filter(Boolean)
                    .filter((value, idx, arr) => arr.indexOf(value) === idx)
                    .sort((a, b) => a.localeCompare(b));
                  return (
                    <tr key={trip.id} className={isTripDirty ? 'admin-row-dirty' : ''}>
                      <td>
                        <input
                          value={draft.name ?? trip.name ?? ''}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'name', e.target.value)}
                        />
                      </td>
                      <td>
                        <select
                          className="admin-project-lead-select"
                          value={selectedConsultant}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'consultant_email', e.target.value)}
                        >
                          <option value="">Select consultant</option>
                          {leadConsultantOptions.map((email) => (
                            <option key={`${trip.id}-lead-${email}`} value={email}>
                              {displayNameFromEmail(email)}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <select
                          value={selectedClient}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'client_name', e.target.value)}
                        >
                          <option value="">Select client</option>
                          {clientSelectOptions.map((clientName) => (
                            <option key={`${trip.id}-client-${clientName}`} value={clientName}>
                              {clientName}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <select
                          value={selectedProgram}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'program_name', e.target.value)}
                        >
                          <option value="">No program (leave blank)</option>
                          {programSelectOptions.map((programName) => (
                            <option key={`${trip.id}-program-${programName}`} value={programName}>
                              {programName}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <select
                          className="admin-project-country-select"
                          value={selectedCountry}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'destination_country', e.target.value)}
                        >
                          <option value="">Select country</option>
                          {countrySelectOptions.map((countryName) => (
                            <option key={`${trip.id}-country-${countryName}`} value={countryName}>
                              {COUNTRY_ACRONYM_LABELS[countryName] || countryName}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <input
                          className="admin-project-date-input"
                          type="date"
                          value={draft.project_start_date ?? trip.project_start_date ?? ''}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'project_start_date', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          className="admin-project-date-input"
                          type="date"
                          value={draft.project_end_date ?? trip.project_end_date ?? ''}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'project_end_date', e.target.value)}
                        />
                      </td>
                      <td>
                        <details>
                          <summary>Open</summary>
                          <div style={{ display: 'grid', gap: 6, marginTop: 6, minWidth: 260 }}>
                            <label>Assigned Consultants</label>
                            <select
                              multiple
                              value={
                                Array.isArray(draft.assigned_consultants)
                                  ? draft.assigned_consultants
                                  : (trip.assigned_consultants || [])
                              }
                              onChange={(e) =>
                                onAdminTripFieldChange(
                                  trip.id,
                                  'assigned_consultants',
                                  Array.from(e.target.selectedOptions || []).map((option) => String(option.value || '').toLowerCase())
                                )
                              }
                              style={{ minHeight: 86 }}
                            >
                              {allConsultantEmails.map((email) => (
                                <option key={`${trip.id}-assigned-${email}`} value={email}>
                                  {displayNameFromEmail(email)}
                                </option>
                              ))}
                            </select>
                            <div className="status">Names are shown; consultant emails are stored in background.</div>
                            <label>City</label>
                            <input
                              value={draft.destination_city ?? trip.destination_city ?? ''}
                              onChange={(e) => onAdminTripFieldChange(trip.id, 'destination_city', e.target.value)}
                            />
                            <label>Departure Date</label>
                            <input
                              type="date"
                              value={draft.departure_date ?? trip.departure_date ?? ''}
                              onChange={(e) => onAdminTripFieldChange(trip.id, 'departure_date', e.target.value)}
                            />
                            <label>Return Date</label>
                            <input
                              type="date"
                              value={draft.return_date ?? trip.return_date ?? ''}
                              onChange={(e) => onAdminTripFieldChange(trip.id, 'return_date', e.target.value)}
                            />
                            <label className="inline-checkbox" style={{ margin: 0 }}>
                              <input
                                type="checkbox"
                                checked={Boolean(draft.travel_booking_required ?? trip.travel_booking_required)}
                                onChange={(e) => onAdminTripFieldChange(trip.id, 'travel_booking_required', e.target.checked)}
                              />{' '}
                              Travel booking required
                            </label>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                              <label className="inline-checkbox" style={{ margin: 0 }}>
                                <input
                                  type="checkbox"
                                  checked={Boolean(draft.travel_needs_flight ?? trip.travel_needs_flight)}
                                  onChange={(e) => onAdminTripFieldChange(trip.id, 'travel_needs_flight', e.target.checked)}
                                />{' '}
                                Flight required
                              </label>
                              <label className="inline-checkbox" style={{ margin: 0 }}>
                                <input
                                  type="checkbox"
                                  checked={Boolean(draft.travel_needs_accommodation ?? trip.travel_needs_accommodation)}
                                  onChange={(e) => onAdminTripFieldChange(trip.id, 'travel_needs_accommodation', e.target.checked)}
                                />{' '}
                                Accommodation required
                              </label>
                            </div>
                            <label>Outbound Preference</label>
                            <select
                              value={String(draft.travel_outbound_preference ?? trip.travel_outbound_preference ?? '')}
                              onChange={(e) => onAdminTripFieldChange(trip.id, 'travel_outbound_preference', e.target.value)}
                            >
                              <option value="">Not set</option>
                              <option value="arrive_by">Arrive by</option>
                              <option value="leave_after">Leave after</option>
                            </select>
                            <label>Outbound Target Date</label>
                            <input
                              type="date"
                              value={draft.travel_outbound_target_date ?? trip.travel_outbound_target_date ?? ''}
                              onChange={(e) => onAdminTripFieldChange(trip.id, 'travel_outbound_target_date', e.target.value)}
                            />
                            <label>Return Preference</label>
                            <select
                              value={String(draft.travel_return_preference ?? trip.travel_return_preference ?? '')}
                              onChange={(e) => onAdminTripFieldChange(trip.id, 'travel_return_preference', e.target.value)}
                            >
                              <option value="">Not set</option>
                              <option value="leave_after">Leave after</option>
                              <option value="arrive_before">Arrive before</option>
                            </select>
                            <label>Return Target Date</label>
                            <input
                              type="date"
                              value={draft.travel_return_target_date ?? trip.travel_return_target_date ?? ''}
                              onChange={(e) => onAdminTripFieldChange(trip.id, 'travel_return_target_date', e.target.value)}
                            />
                            <label>Travel Request Status</label>
                            <select
                              value={String(draft.travel_request_status ?? trip.travel_request_status ?? 'not_required')}
                              onChange={(e) => onAdminTripFieldChange(trip.id, 'travel_request_status', e.target.value)}
                            >
                              <option value="not_required">Not required</option>
                              <option value="requested">Requested</option>
                              <option value="booked">Booked</option>
                              <option value="cancelled">Cancelled</option>
                            </select>
                            <label>Travel Notes</label>
                            <textarea
                              rows={2}
                              value={draft.travel_admin_notes ?? trip.travel_admin_notes ?? ''}
                              onChange={(e) => onAdminTripFieldChange(trip.id, 'travel_admin_notes', e.target.value)}
                              placeholder="Preferred windows, special notes for admin booking"
                            />
                            <button
                              type="button"
                              className="secondary"
                              onClick={() => onMarkTripTravelBooked(trip)}
                              disabled={markingTravelBookedTripId === key}
                            >
                              {markingTravelBookedTripId === key ? 'Marking...' : 'Mark Travel Booked'}
                            </button>
                            {Boolean(trip.expense_report_required) &&
                            String(trip.travel_request_status || '').toLowerCase() === 'booked' &&
                            !Boolean(trip.travel_booked_add_expense_prompted) ? (
                              <button
                                type="button"
                                onClick={() => onCreateBookedTravelExpenseDraft(trip)}
                              >
                                Create Expense Draft
                              </button>
                            ) : null}
                          </div>
                        </details>
                      </td>
                      <td>
                        <div className="admin-row-actions">
                          <button
                            type="button"
                            onClick={() => onSaveAdminTrip(trip)}
                            disabled={savingAdminTripId === key || deletingAdminTripId === key}
                          >
                            {savingAdminTripId === key ? 'Saving...' : 'Save'}
                          </button>
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => onDeleteAdminTrip(trip)}
                            disabled={savingAdminTripId === key || deletingAdminTripId === key}
                          >
                            {deletingAdminTripId === key ? 'Removing...' : 'Remove'}
                          </button>
                        </div>
                        {adminTripSaveNoteById[key] ? (
                          <div className="status admin-save-note">{adminTripSaveNoteById[key]}</div>
                        ) : null}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          </>
          ) : null}

          {adminConsoleSection === 'lookups' ? (
          <>
          <h3 style={{ margin: '16px 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
            Lookup Files (Admin Editable)
          </h3>
          <div className="status" style={{ marginBottom: 8 }}>
            Edit rows directly below. Use Advanced only if you need raw JSON edits.
          </div>
          <div className="grid" style={{ marginBottom: 8 }}>
            <div>
              <label>Consultants</label>
              <div className="status" style={{ marginBottom: 6 }}>
                {consultantLookupPreview.error
                  ? `Table unavailable: ${consultantLookupPreview.error}`
                  : `${consultantLookupPreview.items.length} consultant(s)`}
              </div>
              {!consultantLookupPreview.error ? (
                <div className={`admin-table-wrap ${adminLookupDirtyByKind.consultants ? 'admin-scope-dirty' : ''}`} style={{ maxHeight: 180, marginBottom: 6 }}>
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                      </tr>
                    </thead>
                    <tbody>
                      {consultantLookupPreview.items.map((row, idx) => (
                        <tr key={`consultant-preview-${idx}`}>
                          <td>
                            <input
                              value={String(row?.name || '')}
                              onChange={(e) => onLookupRowFieldChange('consultants', idx, 'name', e.target.value)}
                              placeholder="Consultant name"
                            />
                          </td>
                          <td>
                            <button
                              type="button"
                              className="secondary"
                              onClick={() => onRemoveLookupRow('consultants', idx)}
                            >
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
              <button type="button" className="secondary" onClick={() => onAddLookupRow('consultants')}>
                + Add Consultant
              </button>
              <button
                type="button"
                onClick={() => onSaveAdminLookup('consultants')}
                disabled={savingAdminLookupKey === 'consultants'}
              >
                {savingAdminLookupKey === 'consultants' ? 'Saving...' : 'Save Consultants'}
              </button>
              {adminLookupSaveNoteByKind.consultants ? (
                <div className="status admin-save-note">{adminLookupSaveNoteByKind.consultants}</div>
              ) : null}
              <details style={{ marginTop: 6 }}>
                <summary>Advanced JSON</summary>
                <textarea
                  rows={10}
                  value={adminLookupDrafts.consultants}
                  onChange={(e) => {
                    setAdminLookupDrafts((prev) => ({ ...prev, consultants: e.target.value }));
                    setAdminLookupSaveNoteByKind((prev) => ({ ...prev, consultants: 'Unsaved changes' }));
                  }}
                />
                <button type="button" className="secondary" onClick={() => onFormatAdminLookup('consultants')}>
                  Format JSON
                </button>
              </details>
            </div>
            <div>
              <label>Coaches</label>
              <div className="status" style={{ marginBottom: 6 }}>
                {coachLookupPreview.error
                  ? `Table unavailable: ${coachLookupPreview.error}`
                  : `${coachLookupPreview.items.length} coach(es)`}
              </div>
              {!coachLookupPreview.error ? (
                <div className={`admin-table-wrap ${adminLookupDirtyByKind.coaches ? 'admin-scope-dirty' : ''}`} style={{ maxHeight: 180, marginBottom: 6 }}>
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                      </tr>
                    </thead>
                    <tbody>
                      {coachLookupPreview.items.map((row, idx) => (
                        <tr key={`coach-preview-${idx}`}>
                          <td>
                            <input
                              value={String(row?.name || '')}
                              onChange={(e) => onLookupRowFieldChange('coaches', idx, 'name', e.target.value)}
                              placeholder="Coach name"
                            />
                          </td>
                          <td>
                            <input
                              value={String(row?.email || '')}
                              onChange={(e) => onLookupRowFieldChange('coaches', idx, 'email', e.target.value)}
                              placeholder="coach@email.com"
                            />
                          </td>
                          <td>
                            <button
                              type="button"
                              className="secondary"
                              onClick={() => onRemoveLookupRow('coaches', idx)}
                            >
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
              <button type="button" className="secondary" onClick={() => onAddLookupRow('coaches')}>
                + Add Coach
              </button>
              <button
                type="button"
                onClick={() => onSaveAdminLookup('coaches')}
                disabled={savingAdminLookupKey === 'coaches'}
              >
                {savingAdminLookupKey === 'coaches' ? 'Saving...' : 'Save Coaches'}
              </button>
              {adminLookupSaveNoteByKind.coaches ? (
                <div className="status admin-save-note">{adminLookupSaveNoteByKind.coaches}</div>
              ) : null}
              <details style={{ marginTop: 6 }}>
                <summary>Advanced JSON</summary>
                <textarea
                  rows={10}
                  value={adminLookupDrafts.coaches}
                  onChange={(e) => {
                    setAdminLookupDrafts((prev) => ({ ...prev, coaches: e.target.value }));
                    setAdminLookupSaveNoteByKind((prev) => ({ ...prev, coaches: 'Unsaved changes' }));
                  }}
                />
                <button type="button" className="secondary" onClick={() => onFormatAdminLookup('coaches')}>
                  Format JSON
                </button>
              </details>
            </div>
          </div>
          <div>
            <label>Client Programs</label>
            <div className="status" style={{ marginBottom: 6 }}>
              {clientProgramLookupPreview.error
                ? `Table unavailable: ${clientProgramLookupPreview.error}`
                : `${clientProgramLookupPreview.items.length} client program row(s)`}
            </div>
            {!clientProgramLookupPreview.error ? (
              <div className={`admin-table-wrap ${adminLookupDirtyByKind.clientPrograms ? 'admin-scope-dirty' : ''}`} style={{ maxHeight: 220, marginBottom: 6 }}>
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Client</th>
                      <th>Program</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clientProgramLookupPreview.items.map((row, idx) => (
                      <tr key={`client-program-preview-${idx}`}>
                        <td>
                          <input
                            value={String(row?.client_name || '')}
                            onChange={(e) => onLookupRowFieldChange('clientPrograms', idx, 'client_name', e.target.value)}
                            placeholder="Client name"
                          />
                        </td>
                        <td>
                          <input
                            value={String(row?.program_name || '')}
                            onChange={(e) => onLookupRowFieldChange('clientPrograms', idx, 'program_name', e.target.value)}
                            placeholder="Program name"
                          />
                        </td>
                        <td>
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => onRemoveLookupRow('clientPrograms', idx)}
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
            <button type="button" className="secondary" onClick={() => onAddLookupRow('clientPrograms')}>
              + Add Client Program
            </button>
            <button
              type="button"
              onClick={() => onSaveAdminLookup('clientPrograms')}
              disabled={savingAdminLookupKey === 'clientPrograms'}
            >
              {savingAdminLookupKey === 'clientPrograms' ? 'Saving...' : 'Save Client Programs'}
            </button>
            {adminLookupSaveNoteByKind.clientPrograms ? (
              <div className="status admin-save-note">{adminLookupSaveNoteByKind.clientPrograms}</div>
            ) : null}
            <details style={{ marginTop: 6 }}>
              <summary>Advanced JSON</summary>
              <textarea
                rows={12}
                value={adminLookupDrafts.clientPrograms}
                onChange={(e) => {
                  setAdminLookupDrafts((prev) => ({ ...prev, clientPrograms: e.target.value }));
                  setAdminLookupSaveNoteByKind((prev) => ({ ...prev, clientPrograms: 'Unsaved changes' }));
                }}
              />
              <button type="button" className="secondary" onClick={() => onFormatAdminLookup('clientPrograms')}>
                Format JSON
              </button>
            </details>
          </div>
          </>
          ) : null}

          {adminConsoleSection === 'contracts' ? (
          <>
          <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
            Contracts Module — Phase 1.5 Automation Scaffold
          </h3>
          <div className="status" style={{ marginBottom: 8 }}>
            Branches for subcontract vs variation amendment with lightweight intake dropbox and lifecycle readiness checks.
          </div>
          <div className="grid" style={{ marginBottom: 8 }}>
            <div>
              <label>Consultant</label>
              <select
                value={contractScaffoldForm.consultant_email}
                onChange={(e) => setContractScaffoldForm((prev) => ({ ...prev, consultant_email: e.target.value }))}
              >
                {orderedConsultants.map((consultant) => (
                  <option key={consultant.email} value={consultant.email}>
                    {consultant.name}
                  </option>
                ))}
              </select>
            </div>
            {contractScaffoldForm.document_type === 'internal_admin_contract' ? (
              <div>
                <label>Contract Party (Internal)</label>
                <input
                  value={contractScaffoldForm.contract_party_name}
                  onChange={(e) =>
                    setContractScaffoldForm((prev) => ({ ...prev, contract_party_name: e.target.value }))
                  }
                  placeholder="Samantha"
                />
              </div>
            ) : null}
            <div>
              <label>Document Type</label>
              <select
                value={contractScaffoldForm.document_type}
                onChange={(e) => onContractDocumentTypeChange(e.target.value)}
              >
                {CONTRACT_DOCUMENT_TYPE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {formatTokenLabel(option)}
                  </option>
                ))}
              </select>
            </div>
            {contractScaffoldForm.document_type === 'variation_amendment' ? (
              <div>
                <label>Parent Contract</label>
                <select
                  value={contractScaffoldForm.parent_contract_id}
                  onChange={(e) =>
                    setContractScaffoldForm((prev) => ({ ...prev, parent_contract_id: e.target.value }))
                  }
                >
                  <option value="">Select signed/sent contract</option>
                  {contractParentOptions.map((row) => (
                    <option key={row.id} value={row.id}>
                      {row.label}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}
            <div>
              <label>Activity</label>
              <input
                value={contractScaffoldForm.project_name}
                onChange={(e) => setContractScaffoldForm((prev) => ({ ...prev, project_name: e.target.value }))}
                placeholder="PNG Leadership Program"
              />
            </div>
            <div>
              <label>Contract Start</label>
              <input
                type="date"
                value={contractScaffoldForm.start_date}
                onChange={(e) => setContractScaffoldForm((prev) => ({ ...prev, start_date: e.target.value }))}
              />
            </div>
            <div>
              <label>Contract End</label>
              <input
                type="date"
                value={contractScaffoldForm.end_date}
                onChange={(e) => setContractScaffoldForm((prev) => ({ ...prev, end_date: e.target.value }))}
              />
            </div>
            <div>
              <label>Daily Rate (AUD)</label>
              <input
                type="number"
                step="0.01"
                value={contractScaffoldForm.daily_rate}
                onChange={(e) => setContractScaffoldForm((prev) => ({ ...prev, daily_rate: e.target.value }))}
              />
            </div>
            <div>
              <label>Estimated Days</label>
              <input
                type="number"
                step="1"
                value={contractScaffoldForm.estimated_days}
                onChange={(e) => setContractScaffoldForm((prev) => ({ ...prev, estimated_days: e.target.value }))}
              />
            </div>
            <div>
              <label>Lifecycle Status</label>
              <select
                value={contractScaffoldForm.lifecycle_status}
                onChange={(e) => setContractScaffoldForm((prev) => ({ ...prev, lifecycle_status: e.target.value }))}
              >
                {CONTRACT_LIFECYCLE_STATUS_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {formatTokenLabel(option)}
                  </option>
                ))}
              </select>
            </div>
            {contractScaffoldForm.document_type === 'variation_amendment' ? (
              <>
                <div>
                  <label>Variation Value Delta (AUD)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={contractScaffoldForm.variation_value_delta}
                    onChange={(e) =>
                      setContractScaffoldForm((prev) => ({ ...prev, variation_value_delta: e.target.value }))
                    }
                    placeholder="1500"
                  />
                </div>
                <div>
                  <label>Variation Reason</label>
                  <input
                    value={contractScaffoldForm.variation_reason}
                    onChange={(e) =>
                      setContractScaffoldForm((prev) => ({ ...prev, variation_reason: e.target.value }))
                    }
                    placeholder="Scope increase for additional workshop"
                  />
                </div>
              </>
            ) : null}
          </div>
          <div className="status" style={{ marginBottom: 8 }}>
            Estimated value preview: {formatAud(contractScaffoldEstimate)}
          </div>
          <div className={`contract-dropzone ${contractDropActive ? 'is-active' : ''}`}
            onDragOver={(e) => {
              e.preventDefault();
              setContractDropActive(true);
            }}
            onDragLeave={() => setContractDropActive(false)}
            onDrop={(e) => {
              e.preventDefault();
              setContractDropActive(false);
              onAttachContractFiles(e.dataTransfer?.files);
            }}
          >
            <div className="status">Drop contract source files here (SOW, prior contract, variation notes), or choose files.</div>
            <input type="file" multiple onChange={(e) => onAttachContractFiles(e.target.files)} />
            {(contractScaffoldForm.attachments || []).length ? (
              <div className="contract-file-list">
                {contractScaffoldForm.attachments.map((attachment) => (
                  <div key={attachment.id} className="contract-file-item">
                    <div>
                      <strong>{attachment.name}</strong>
                      <div className="status">{formatFileSize(attachment.size_bytes)} · {formatDateAu(String(attachment.attached_at || '').slice(0, 10))}</div>
                    </div>
                    <button type="button" className="secondary" onClick={() => onRemoveContractAttachment(attachment.id)}>
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
          <div className={`status ${contractGenerationReadiness.ready ? 'qa-pass' : 'qa-fail'}`} style={{ marginBottom: 8 }}>
            Template readiness: {contractGenerationReadiness.message}
          </div>
          <div className="contracts-workflow-grid" style={{ marginBottom: 8 }}>
            <div className="contract-merge-panel">
              <h4>Template Merge Fields</h4>
              <div className="status" style={{ marginBottom: 6 }}>
                {formatTokenLabel(contractScaffoldForm.document_type)} uses these merge points.
              </div>
              {mergeFieldsForSelectedContractType.length ? (
                <div className="contract-merge-chip-grid">
                  {mergeFieldsForSelectedContractType.map((field) => (
                    <span key={field} className="contract-merge-chip">
                      {'{{'}{field}{'}}'}
                    </span>
                  ))}
                </div>
              ) : (
                <div className="status">No merge-fields metadata loaded yet.</div>
              )}
            </div>

            <div className="contract-policy-panel">
              <h4>Policy Send Workflow</h4>
              <div className="status" style={{ marginBottom: 6 }}>
                Select which policies will be bundled when issuing this contract.
              </div>
              <div className="contract-policy-checklist">
                {contractPoliciesForSelectedType.map((policy) => {
                  const checked = (contractScaffoldForm.policy_ids || []).includes(policy.id);
                  return (
                    <label key={policy.id} className="contract-policy-option">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(e) => onToggleContractPolicy(policy.id, e.target.checked)}
                      />
                      <span>
                        <strong>{policy.title}</strong>
                        <small>{policy.version} · Effective {formatDateAu(policy.effectiveDate)}</small>
                      </span>
                    </label>
                  );
                })}
              </div>
              <label className="contract-policy-ack">
                <input
                  type="checkbox"
                  checked={Boolean(contractScaffoldForm.policy_acknowledged)}
                  onChange={(e) =>
                    setContractScaffoldForm((prev) => ({ ...prev, policy_acknowledged: e.target.checked }))
                  }
                />
                I confirm selected policies will be attached before sending for signature.
              </label>
              <label>Policy Notes</label>
              <textarea
                rows={2}
                value={contractScaffoldForm.policy_notes}
                onChange={(e) => setContractScaffoldForm((prev) => ({ ...prev, policy_notes: e.target.value }))}
                placeholder="Optional: include any policy package notes for this contract."
              />
            </div>
          </div>

          {activePolicyDetail ? (
            <div className="policy-reference-card" style={{ marginBottom: 8 }}>
              <div className="policy-reference-header">
                <div>
                  <div className="policy-eyebrow">Adapsys Policy Reference</div>
                  <h4>{activePolicyDetail.title}</h4>
                  <p>{activePolicyDetail.summary}</p>
                </div>
                <select
                  value={activePolicyDetail.id}
                  onChange={(e) => setSelectedPolicyId(e.target.value)}
                >
                  {contractPoliciesForSelectedType.map((policy) => (
                    <option key={policy.id} value={policy.id}>
                      {policy.title}
                    </option>
                  ))}
                </select>
              </div>
              <div className="policy-highlight-grid">
                {(activePolicyDetail.highlights || []).map((highlight) => (
                  <div key={highlight} className="policy-highlight-item">
                    {highlight}
                  </div>
                ))}
              </div>
              {(activePolicyDetail.sections || []).length ? (
                <div className="policy-section-grid">
                  {activePolicyDetail.sections.map((section) => (
                    <article key={section.heading} className="policy-section-card">
                      <h5>{section.heading}</h5>
                      <p>{section.body}</p>
                    </article>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
          <div className="admin-console-snapshot" style={{ marginBottom: 8 }}>
            <div><strong>{contractOpsSummary.total}</strong><span>Total Drafts</span></div>
            <div><strong>{contractOpsSummary.awaitingSignature}</strong><span>Awaiting Signature</span></div>
            <div><strong>{contractOpsSummary.overdueSignature}</strong><span>Overdue Signature (&gt;7d)</span></div>
            <div><strong>{contractOpsSummary.variation}</strong><span>Variation Amendments</span></div>
            <div><strong>{contractOpsSummary.internalAdmin}</strong><span>Internal Admin Contracts</span></div>
            <div><strong>{contractOpsSummary.withAttachments}</strong><span>Rows With Files</span></div>
          </div>
          <button type="button" onClick={onCreateContractScaffold}>Add Contract Scaffold Row</button>
          {contractScaffoldStatus ? <div className="status admin-save-note">{contractScaffoldStatus}</div> : null}
          {contractPreviewHtml ? (
            <div className="contract-preview-surface">
              <div className="contract-preview-header">
                <div className="status report-status-surface" style={{ margin: 0 }}>
                  Contract preview {contractPreviewRowId ? `for ${contractScaffoldRows.find((row) => row.id === contractPreviewRowId)?.project_name || 'selected row'}` : ''}
                </div>
                <div className="contract-preview-actions">
                  <button type="button" className="secondary" onClick={onOpenContractPreviewInNewTab}>Open in New Tab</button>
                  <button type="button" className="secondary" onClick={onClearContractPreview}>Close Preview</button>
                </div>
              </div>
              <iframe
                title="Adapsys Contract Preview"
                srcDoc={contractPreviewHtml}
                className="report-preview-frame"
              />
            </div>
          ) : null}
          {contractScaffoldRows.length ? (
            <div className="admin-table-wrap" style={{ marginTop: 8 }}>
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Party</th>
                    <th>Consultant</th>
                    <th>Activity</th>
                    <th>Parent</th>
                    <th>Start</th>
                    <th>End</th>
                    <th>Daily Rate</th>
                    <th>Days</th>
                    <th>Estimated Value</th>
                    <th>Status</th>
                    <th>Policies</th>
                    <th>Sent</th>
                    <th>Signed</th>
                    <th>Files</th>
                    <th>Doc Draft</th>
                    <th>Row Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {contractScaffoldRows.map((row) => (
                    <tr key={row.id}>
                      <td>{formatTokenLabel(row.document_type)}</td>
                      <td>{row.contract_party_name || '—'}</td>
                      <td>{displayNameFromEmail(row.consultant_email)}</td>
                      <td>{row.project_name}</td>
                      <td>{row.parent_contract_label || '—'}</td>
                      <td>{formatDateAu(row.start_date)}</td>
                      <td>{formatDateAu(row.end_date)}</td>
                      <td>{formatAud(row.daily_rate)}</td>
                      <td>{row.estimated_days}</td>
                      <td>{formatAud(row.estimated_value)}</td>
                      <td>{formatTokenLabel(row.lifecycle_status)}</td>
                      <td>
                        {(row.policy_ids || []).length ? `${row.policy_ids.length} selected` : 'None'}
                        <div className={`status ${(row.policy_ids || []).length && !row.policy_acknowledged ? 'qa-fail' : 'qa-pass'}`}>
                          {(row.policy_ids || []).length
                            ? row.policy_acknowledged
                              ? 'Policies ticked'
                              : 'Policy tick pending'
                            : 'No policies required'}
                        </div>
                        {(row.attachments || []).some(
                          (attachment) => String(attachment?.source || '').trim().toLowerCase() === 'policy_library'
                        ) ? (
                          <div className="status" style={{ marginTop: 4 }}>
                            Bundled:{' '}
                            {(row.attachments || [])
                              .filter(
                                (attachment) =>
                                  String(attachment?.source || '').trim().toLowerCase() === 'policy_library'
                              )
                              .map((attachment) => String(attachment?.name || '').trim())
                              .filter(Boolean)
                              .join(', ')}
                          </div>
                        ) : null}
                      </td>
                      <td>{formatDateAu(String(row.sent_date || '').slice(0, 10)) || '—'}</td>
                      <td>{formatDateAu(String(row.signed_date || '').slice(0, 10)) || '—'}</td>
                      <td>{(row.attachments || []).length}</td>
                      <td>{row.generated_document_name}</td>
                      <td>
                        <div className="coaching-form-actions contract-row-actions" style={{ margin: 0 }}>
                          <button
                            type="button"
                            className={`secondary ${contractPreviewRowId === row.id && contractPreviewHtml ? 'is-active' : ''}`}
                            onClick={() => onGenerateContractPreview(row.id)}
                            disabled={isPreviewingContract && contractPreviewRowId === row.id}
                          >
                            {isPreviewingContract && contractPreviewRowId === row.id
                              ? 'Generating...'
                              : contractPreviewRowId === row.id && contractPreviewHtml
                                ? 'Previewing'
                                : 'Preview'}
                          </button>
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => onDownloadContractPreviewPdf(row.id)}
                            disabled={isDownloadingContractPdfRowId === row.id}
                          >
                            {isDownloadingContractPdfRowId === row.id ? 'Preparing PDF...' : 'Download PDF'}
                          </button>
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => onAcknowledgeContractPolicies(row.id)}
                            disabled={!(row.policy_ids || []).length || row.policy_acknowledged}
                          >
                            {row.policy_acknowledged ? 'Policies Ticked' : 'Tick Policies Sent'}
                          </button>
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => onMarkContractLifecycle(row.id, 'awaiting_signature')}
                            disabled={(row.policy_ids || []).length > 0 && !row.policy_acknowledged}
                          >
                            Send
                          </button>
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => onFlagContractReminder(row.id)}
                            disabled={row.lifecycle_status !== 'awaiting_signature'}
                          >
                            Remind
                          </button>
                          <button
                            type="button"
                            onClick={() => onMarkContractLifecycle(row.id, 'signed')}
                          >
                            Mark Signed
                          </button>
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => onDeleteContractRow(row.id)}
                          >
                            Delete
                          </button>
                        </div>
                        {row.reminder_requested_at ? (
                          <div className="status" style={{ marginTop: 4 }}>
                            Reminder {Number(row.reminder_count || 0)} at {formatDateAu(String(row.reminder_requested_at || '').slice(0, 10))}
                          </div>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
          </>
          ) : null}

          {adminConsoleSection === 'consultant-profiles' ? (
          <>
          <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
            Consultant Profiles Module — Phase 1 Scaffold
          </h3>
          <div className="status" style={{ marginBottom: 8 }}>
            Starter structure for Module 6: profile title, expertise tags, Pacific countries and a professional summary.
          </div>
          <div className="grid" style={{ marginBottom: 8 }}>
            <div>
              <label>Consultant</label>
              <select
                value={profileScaffoldForm.consultant_email}
                onChange={(e) => setProfileScaffoldForm((prev) => ({ ...prev, consultant_email: e.target.value }))}
              >
                {orderedConsultants.map((consultant) => (
                  <option key={consultant.email} value={consultant.email}>
                    {consultant.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label>Title</label>
              <input
                value={profileScaffoldForm.title}
                onChange={(e) => setProfileScaffoldForm((prev) => ({ ...prev, title: e.target.value }))}
                placeholder="Principal Consultant"
              />
            </div>
            <div>
              <label>Expertise Tags (comma separated)</label>
              <input
                value={profileScaffoldForm.expertise_tags}
                onChange={(e) => setProfileScaffoldForm((prev) => ({ ...prev, expertise_tags: e.target.value }))}
                placeholder="adaptive leadership, executive coaching"
              />
            </div>
            <div>
              <label>Pacific Countries (comma separated)</label>
              <input
                value={profileScaffoldForm.pacific_countries}
                onChange={(e) => setProfileScaffoldForm((prev) => ({ ...prev, pacific_countries: e.target.value }))}
                placeholder="PNG, Fiji, Samoa"
              />
            </div>
          </div>
          <label>Professional Summary</label>
          <textarea
            rows={3}
            value={profileScaffoldForm.summary}
            onChange={(e) => setProfileScaffoldForm((prev) => ({ ...prev, summary: e.target.value }))}
          />
          <button type="button" onClick={onCreateProfileScaffold}>Add Profile Scaffold Row</button>
          {profileScaffoldStatus ? <div className="status admin-save-note">{profileScaffoldStatus}</div> : null}
          {profileScaffoldRows.length ? (
            <div style={{ marginTop: 8 }}>
              {profileScaffoldRows.map((row) => (
                <div key={row.id} className="card" style={{ marginBottom: 8 }}>
                  <div><strong>{displayNameFromEmail(row.consultant_email)}</strong> — {row.title || 'Title pending'}</div>
                  <div className="status">Expertise: {row.expertise_tags || 'None listed yet'}</div>
                  <div className="status">Countries: {row.pacific_countries || 'None listed yet'}</div>
                  <div className="status">Summary: {row.summary || 'No summary entered yet.'}</div>
                </div>
              ))}
            </div>
          ) : null}
          </>
          ) : null}

          {adminConsoleSection === 'engagements' ? (
          <>
          <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
            Coaching Engagements (All Fields)
          </h3>
          <div className="grid" style={{ marginBottom: 8 }}>
            <div>
              <label>Search Coachee Name</label>
              <input
                value={adminEngagementSearch.name}
                onChange={(e) =>
                  setAdminEngagementSearch((prev) => ({ ...prev, name: e.target.value }))
                }
                placeholder="Type name..."
              />
            </div>
            <div>
              <label>Search Client</label>
              <input
                value={adminEngagementSearch.client_org}
                onChange={(e) =>
                  setAdminEngagementSearch((prev) => ({ ...prev, client_org: e.target.value }))
                }
                placeholder="Type client..."
              />
            </div>
            <div>
              <label>Search Coach</label>
              <input
                value={adminEngagementSearch.coach_email}
                onChange={(e) =>
                  setAdminEngagementSearch((prev) => ({ ...prev, coach_email: e.target.value }))
                }
                placeholder="Type coach..."
              />
            </div>
          </div>
          <div className="status" style={{ marginBottom: 8 }}>
            Showing {filteredAdminEngagements.length} of {coachingEngagements.length} coachees.
          </div>
          <div className="coaching-form-actions" style={{ marginBottom: 8 }}>
            <button
              type="button"
              onClick={() => {
                if (!selectedAdminEngagement) return;
                onSaveAdminEngagement(selectedAdminEngagement);
              }}
              disabled={!selectedAdminEngagement}
            >
              Save Selected
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => {
                if (!selectedAdminEngagement) return;
                onDeleteAdminEngagement(selectedAdminEngagement);
              }}
              disabled={!selectedAdminEngagement}
            >
              Delete Selected
            </button>
            <div className="status" style={{ margin: 0 }}>
              {selectedAdminEngagement
                ? `Selected: ${selectedAdminEngagement.name || selectedAdminEngagement.id}`
                : 'Select a coachee row to edit/save/delete.'}
            </div>
          </div>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Select</th>
                  <th className="col-coachee">
                    <button type="button" className="admin-sort-btn" onClick={() => onToggleAdminEngagementSort('name')}>
                      Coachee {adminEngagementSort.key === 'name' ? (adminEngagementSort.direction === 'asc' ? '^' : 'v') : ''}
                    </button>
                  </th>
                  <th className="col-job">Job Title</th>
                  <th className="col-client">
                    <button type="button" className="admin-sort-btn" onClick={() => onToggleAdminEngagementSort('client_org')}>
                      Client {adminEngagementSort.key === 'client_org' ? (adminEngagementSort.direction === 'asc' ? '^' : 'v') : ''}
                    </button>
                  </th>
                  <th className="col-coach">
                    <button type="button" className="admin-sort-btn" onClick={() => onToggleAdminEngagementSort('coach_email')}>
                      Coach {adminEngagementSort.key === 'coach_email' ? (adminEngagementSort.direction === 'asc' ? '^' : 'v') : ''}
                    </button>
                  </th>
                  <th className="col-entitled">Entitled</th>
                  <th className="col-completed">Completed</th>
                  <th>LCP On</th>
                  <th>LCP Entitled</th>
                  <th>LCP Used</th>
                  <th className="col-no-show">No Show</th>
                  <th className="col-rate">Rate</th>
                  <th className="col-cost">Cost/Session</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredAdminEngagements.map((engagement) => {
                  const key = String(engagement.id);
                  const draft = adminEngagementDraftById[key] || {};
                  const isSelected = selectedAdminEngagementId === key;
                  const isDirty = Boolean(adminEngagementDraftById[key]);
                  return (
                    <tr
                      key={engagement.id}
                      className={isDirty ? 'admin-row-dirty' : ''}
                      style={isSelected ? { background: 'rgba(0, 153, 186, 0.08)' } : undefined}
                    >
                      <td>
                        <button
                          type="button"
                          className={isSelected ? '' : 'secondary'}
                          onClick={() => setSelectedAdminEngagementId((prev) => (prev === key ? '' : key))}
                          disabled={savingAdminEngagementId === key || deletingAdminEngagementId === key}
                        >
                          {isSelected ? 'Selected' : 'Select'}
                        </button>
                      </td>
                      <td className="col-coachee">
                        <input
                          value={draft.name ?? engagement.name ?? ''}
                          onChange={(e) => onAdminEngagementFieldChange(engagement.id, 'name', e.target.value)}
                        />
                      </td>
                      <td className="col-job">
                        <input
                          value={draft.job_title ?? engagement.job_title ?? ''}
                          onChange={(e) => onAdminEngagementFieldChange(engagement.id, 'job_title', e.target.value)}
                        />
                      </td>
                      <td className="col-client">
                        <select
                          value={draft.client_org ?? engagement.client_org ?? ''}
                          onChange={(e) => onAdminEngagementFieldChange(engagement.id, 'client_org', e.target.value)}
                        >
                          {[draft.client_org ?? engagement.client_org, ...clientOptions]
                            .filter(Boolean)
                            .filter((value, idx, arr) => arr.indexOf(value) === idx)
                            .map((clientName) => (
                              <option key={clientName} value={clientName}>
                                {clientName}
                              </option>
                            ))}
                        </select>
                      </td>
                      <td className="col-coach">
                        <select
                          value={draft.coach_email ?? engagement.coach_email ?? ''}
                          onChange={(e) => onAdminEngagementFieldChange(engagement.id, 'coach_email', e.target.value)}
                        >
                          {orderedCoaches.map((coach) => (
                            <option key={coach.email} value={coach.email}>
                              {coach.name}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="col-entitled">
                        <input
                          type="number"
                          value={draft.total_sessions ?? engagement.total_sessions ?? 0}
                          onChange={(e) => onAdminEngagementFieldChange(engagement.id, 'total_sessions', e.target.value)}
                        />
                      </td>
                      <td className="col-completed">
                        <input
                          type="number"
                          value={draft.sessions_used ?? engagement.sessions_used ?? 0}
                          onChange={(e) => onAdminEngagementFieldChange(engagement.id, 'sessions_used', e.target.value)}
                        />
                      </td>
                      <td>
                        <label className="inline-checkbox" style={{ margin: 0 }}>
                          <input
                            type="checkbox"
                            checked={Boolean(draft.lcp_debrief_enabled ?? engagement.lcp_debrief_enabled)}
                            onChange={(e) =>
                              onAdminEngagementFieldChange(engagement.id, 'lcp_debrief_enabled', e.target.checked)
                            }
                          />
                          Yes
                        </label>
                      </td>
                      <td>
                        <input
                          type="number"
                          value={draft.lcp_debrief_total_sessions ?? engagement.lcp_debrief_total_sessions ?? 0}
                          onChange={(e) =>
                            onAdminEngagementFieldChange(engagement.id, 'lcp_debrief_total_sessions', e.target.value)
                          }
                          disabled={!Boolean(draft.lcp_debrief_enabled ?? engagement.lcp_debrief_enabled)}
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          value={draft.lcp_debrief_sessions_used ?? engagement.lcp_debrief_sessions_used ?? 0}
                          onChange={(e) =>
                            onAdminEngagementFieldChange(engagement.id, 'lcp_debrief_sessions_used', e.target.value)
                          }
                          disabled={!Boolean(draft.lcp_debrief_enabled ?? engagement.lcp_debrief_enabled)}
                        />
                      </td>
                      <td className="col-no-show">
                        <input
                          type="number"
                          value={noShowCountByEngagementId[String(engagement.id)] || 0}
                          readOnly
                        />
                      </td>
                      <td className="col-rate">
                        <input
                          type="number"
                          step="0.01"
                          value={draft.session_rate ?? engagement.session_rate ?? ''}
                          onChange={(e) => onAdminEngagementFieldChange(engagement.id, 'session_rate', e.target.value)}
                        />
                      </td>
                      <td className="col-cost">
                        <input
                          type="number"
                          step="0.01"
                          value={draft.associate_cost_per_session ?? engagement.associate_cost_per_session ?? ''}
                          onChange={(e) =>
                            onAdminEngagementFieldChange(engagement.id, 'associate_cost_per_session', e.target.value)
                          }
                        />
                      </td>
                      <td>
                        <div className="admin-row-actions">
                          <button
                            type="button"
                            onClick={() => onSaveAdminEngagement(engagement)}
                            disabled={savingAdminEngagementId === key || deletingAdminEngagementId === key}
                          >
                            {savingAdminEngagementId === key ? 'Saving...' : 'Save'}
                          </button>
                          <button
                            type="button"
                            className="secondary"
                            onClick={() => onDeleteAdminEngagement(engagement)}
                            disabled={savingAdminEngagementId === key || deletingAdminEngagementId === key}
                          >
                            {deletingAdminEngagementId === key ? 'Deleting...' : 'Delete'}
                          </button>
                        </div>
                        {adminEngagementSaveNoteById[key] ? (
                          <div className="status admin-save-note">{adminEngagementSaveNoteById[key]}</div>
                        ) : null}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          </>
          ) : null}

          {adminConsoleSection === 'sessions' ? (
          <>
          <h3 style={{ margin: '16px 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
            Coaching Sessions (All Fields)
          </h3>
          <div className="coaching-planner" style={{ marginBottom: 10 }}>
            <h4 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 14 }}>
              Quick Add Multiple Session Dates
            </h4>
            <div className="coaching-planner-search is-admin">
              <div>
                <label>Search Coach</label>
                <input
                  value={adminSessionQuickSearch.coach}
                  onChange={(e) =>
                    setAdminSessionQuickSearch((prev) => ({ ...prev, coach: e.target.value }))
                  }
                  placeholder="Coach name or email"
                />
              </div>
              <div>
                <label>Search Consultant/Coachee</label>
                <input
                  value={adminSessionQuickSearch.consultant}
                  onChange={(e) =>
                    setAdminSessionQuickSearch((prev) => ({ ...prev, consultant: e.target.value }))
                  }
                  placeholder="Coachee name"
                />
              </div>
              <div>
                <label>Search Client</label>
                <input
                  value={adminSessionQuickSearch.client}
                  onChange={(e) =>
                    setAdminSessionQuickSearch((prev) => ({ ...prev, client: e.target.value }))
                  }
                  placeholder="Client"
                />
              </div>
            </div>
            <div className="status" style={{ marginBottom: 8 }}>
              Matching people: {adminSessionQuickMatches.length}
            </div>
            <label>Selected Person</label>
            <select
              value={adminSessionQuickForm.engagement_id}
              onChange={(e) =>
                setAdminSessionQuickForm((prev) => ({ ...prev, engagement_id: e.target.value }))
              }
            >
              <option value="">Select coachee</option>
              {adminSessionQuickMatches.map((engagement) => (
                <option key={engagement.id} value={engagement.id}>
                  {engagement.name} — {engagement.client_org} — {displayNameFromEmail(engagement.coach_email)}
                </option>
              ))}
            </select>

            {selectedAdminQuickEngagement ? (
              <div className="status" style={{ marginTop: 8 }}>
                Recent dates for {selectedAdminQuickEngagement.name}:{' '}
                {adminQuickRecentSessions.length
                  ? adminQuickRecentSessions.map((session) => formatDateAu(session.session_date)).join(', ')
                  : 'No sessions logged yet'}
                {selectedAdminQuickLcpEnabled ? ' · LCP de-brief available' : ' · LCP de-brief not offered'}
              </div>
            ) : null}

            <div className="coaching-planner-add-row" style={{ marginTop: 8 }}>
              <label>Add Date</label>
              <input
                type="date"
                value={adminSessionQuickForm.next_date}
                onChange={(e) =>
                  setAdminSessionQuickForm((prev) => ({ ...prev, next_date: e.target.value }))
                }
              />
              <button type="button" className="secondary" onClick={onAdminQuickAddDate}>
                Add Date
              </button>
            </div>

            <label style={{ marginTop: 8 }}>Session Dates (one per line)</label>
            <textarea
              rows={3}
              value={adminSessionQuickForm.session_dates_text}
              onChange={(e) =>
                setAdminSessionQuickForm((prev) => ({ ...prev, session_dates_text: e.target.value }))
              }
              placeholder={'30/03/2026\n06/04/2026\n13/04/2026'}
            />

            {adminQuickSessionDates.length ? (
              <div className="admin-session-date-chip-list">
                {adminQuickSessionDates.map((dateValue) => (
                  <button
                    key={dateValue}
                    type="button"
                    className="secondary admin-session-date-chip"
                    onClick={() => onAdminQuickRemoveDate(dateValue)}
                    title="Remove date"
                  >
                    {formatDateAu(dateValue)} ×
                  </button>
                ))}
              </div>
            ) : null}

            <div className="coaching-session-core-grid" style={{ marginTop: 8 }}>
              <div className="coaching-field-compact coaching-field-duration">
                <label>Duration (mins)</label>
                <input
                  type="number"
                  min="1"
                  value={adminSessionQuickForm.duration_mins}
                  onChange={(e) =>
                    setAdminSessionQuickForm((prev) => ({ ...prev, duration_mins: e.target.value }))
                  }
                />
              </div>
              <div className="coaching-field-compact coaching-field-mode">
                <label>Mode</label>
                <select
                  value={adminSessionQuickForm.delivery_mode}
                  onChange={(e) =>
                    setAdminSessionQuickForm((prev) => ({ ...prev, delivery_mode: e.target.value }))
                  }
                >
                  <option value="video">Video</option>
                  <option value="in_person">In person</option>
                  <option value="phone">Phone</option>
                </select>
              </div>
              <div className="coaching-field-compact coaching-field-no-show">
                <label>No Show</label>
                <label className="inline-checkbox coaching-inline-checkbox">
                  <input
                    type="checkbox"
                    checked={adminSessionQuickForm.session_type === 'no_show_chargeable'}
                    onChange={(e) =>
                      setAdminSessionQuickForm((prev) => ({
                        ...prev,
                        session_type: e.target.checked ? 'no_show_chargeable' : 'completed',
                      }))
                    }
                  />{' '}
                  Chargeable no-show
                </label>
              </div>
              <div className="coaching-field-compact coaching-field-lcp">
                <label>LCP de-brief</label>
                <label className="inline-checkbox coaching-inline-checkbox">
                  <input
                    type="checkbox"
                    checked={Boolean(adminSessionQuickForm.lcp_debrief)}
                    disabled={!selectedAdminQuickLcpEnabled}
                    onChange={(e) =>
                      setAdminSessionQuickForm((prev) => ({
                        ...prev,
                        lcp_debrief: e.target.checked,
                        lcp_debrief_date: e.target.checked ? prev.lcp_debrief_date : '',
                      }))
                    }
                  />{' '}
                  LCP de-brief completed
                </label>
                {!selectedAdminQuickLcpEnabled ? (
                  <div className="status" style={{ marginTop: 4 }}>LCP de-brief is not enabled for this coachee.</div>
                ) : null}
                {adminSessionQuickForm.lcp_debrief ? (
                  <>
                    <label style={{ marginTop: 6 }}>LCP de-brief Date</label>
                    <input
                      className="coaching-lcp-date-input"
                      ref={adminLcpDateRef}
                      type="date"
                      value={adminSessionQuickForm.lcp_debrief_date}
                      onChange={(e) =>
                        setAdminSessionQuickForm((prev) => ({
                          ...prev,
                          lcp_debrief_date: e.target.value,
                        }))
                      }
                      required
                    />
                  </>
                ) : null}
              </div>
              <div className="coaching-field-compact coaching-field-date">
                <label>Invoiced</label>
                <label className="inline-checkbox coaching-inline-checkbox">
                  <input
                    type="checkbox"
                    checked={Boolean(adminSessionQuickForm.invoiced_to_adapsys)}
                    onChange={(e) =>
                      setAdminSessionQuickForm((prev) => ({
                        ...prev,
                        invoiced_to_adapsys: e.target.checked,
                      }))
                    }
                  />{' '}
                  Invoiced to Adapsys
                </label>
              </div>
            </div>

            <label>Notes (optional)</label>
            <textarea
              rows={2}
              value={adminSessionQuickForm.notes}
              onChange={(e) =>
                setAdminSessionQuickForm((prev) => ({ ...prev, notes: e.target.value }))
              }
              placeholder="Optional note applied to all dates above"
            />

            <div className="coaching-form-actions">
              <button
                type="button"
                onClick={onCreateAdminSessionBatch}
                disabled={isSavingAdminSessionBatch}
              >
                {isSavingAdminSessionBatch ? 'Saving Dates...' : 'Save All Dates'}
              </button>
              <div className="status">
                Default outcome is <strong>completed</strong> unless no-show is ticked.
              </div>
            </div>
          </div>
          <div className="status" style={{ marginBottom: 8 }}>
            Showing {filteredAdminSessions.length} session row(s) after search filters.
          </div>
          <div className="coaching-form-actions" style={{ marginBottom: 8 }}>
            <button
              type="button"
              className="secondary"
              onClick={onSaveAllAdminSessions}
              disabled={isSavingAllAdminSessions || adminSessionEditedRows === 0}
            >
              {isSavingAllAdminSessions ? 'Saving Edited Rows...' : `Save Edited Rows (${adminSessionEditedRows})`}
            </button>
            <div className="status">
              Use <strong>Save All Dates</strong> above to add new sessions in bulk; use this button to batch-save table edits.
            </div>
          </div>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Engagement</th>
                  <th>Outcome</th>
                  <th>LCP</th>
                  <th>LCP Date</th>
                  <th>Invoiced</th>
                  <th>Notes</th>
                  <th>Save</th>
                </tr>
              </thead>
              <tbody>
                {filteredAdminSessions.map((session) => {
                  const key = String(session.id);
                  const draft = adminSessionDraftById[key] || {};
                  const rowEngagement = coachingEngagementById[String(draft.engagement_id ?? session.engagement_id)] || null;
                  const rowLcpEnabled = Boolean(rowEngagement?.lcp_debrief_enabled);
                  return (
                    <tr key={session.id}>
                      <td>
                        <input
                          type="date"
                          value={draft.session_date ?? session.session_date ?? ''}
                          onChange={(e) => onAdminSessionFieldChange(session.id, 'session_date', e.target.value)}
                        />
                      </td>
                      <td>
                        <select
                          value={draft.engagement_id ?? session.engagement_id ?? ''}
                          onChange={(e) => onAdminSessionFieldChange(session.id, 'engagement_id', e.target.value)}
                        >
                          {coachingEngagements.map((engagement) => (
                            <option key={engagement.id} value={engagement.id}>
                              {engagement.name} — {engagement.client_org} — {displayNameFromEmail(engagement.coach_email)}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <select
                          value={draft.session_type ?? session.session_type ?? 'completed'}
                          onChange={(e) => onAdminSessionFieldChange(session.id, 'session_type', e.target.value)}
                        >
                          {COACHING_SESSION_OUTCOMES.map((option) => (
                            <option key={option} value={option}>
                              {formatTokenLabel(option)}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <label className="inline-checkbox" style={{ margin: 0 }}>
                          <input
                            type="checkbox"
                            checked={Boolean(draft.lcp_debrief ?? session.lcp_debrief)}
                            disabled={!rowLcpEnabled}
                            onChange={(e) => {
                              onAdminSessionFieldChange(session.id, 'lcp_debrief', e.target.checked);
                              if (!e.target.checked) {
                                onAdminSessionFieldChange(session.id, 'lcp_debrief_date', '');
                              }
                            }}
                          />
                          Done
                        </label>
                      </td>
                      <td>
                        <input
                          type="date"
                          value={draft.lcp_debrief_date ?? session.lcp_debrief_date ?? ''}
                          onChange={(e) => onAdminSessionFieldChange(session.id, 'lcp_debrief_date', e.target.value)}
                          disabled={!Boolean(draft.lcp_debrief ?? session.lcp_debrief) || !rowLcpEnabled}
                        />
                      </td>
                      <td>
                        <label className="inline-checkbox" style={{ margin: 0 }}>
                          <input
                            type="checkbox"
                            checked={Boolean(draft.invoiced_to_adapsys ?? session.invoiced_to_adapsys)}
                            onChange={(e) =>
                              onAdminSessionFieldChange(session.id, 'invoiced_to_adapsys', e.target.checked)
                            }
                          />
                          Yes
                        </label>
                      </td>
                      <td>
                        <input
                          value={draft.notes ?? session.notes ?? ''}
                          onChange={(e) => onAdminSessionFieldChange(session.id, 'notes', e.target.value)}
                        />
                      </td>
                      <td>
                        <button
                          type="button"
                          onClick={() => onSaveAdminSession(session)}
                          disabled={savingAdminSessionId === key}
                        >
                          {savingAdminSessionId === key ? 'Saving...' : 'Save'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          </>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
