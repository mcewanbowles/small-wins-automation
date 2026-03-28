import { useEffect, useMemo, useRef, useState } from 'react';
import {
  approveExpense,
  createCoachingEngagement,
  createExpense,
  createTrip,
  deleteExpense,
  downloadCoachingReportPdf,
  downloadExpensePackPdf,
  fetchCoachingReportPreview,
  fetchExpensePackPreview,
  intakeEmailReceipt,
  getTenderSummary,
  listAtoRates,
  listCoaches,
  listClientPrograms,
  listCoachingEngagements,
  listCoachingSessions,
  listConsultants,
  listExpenses,
  listTenders,
  logCoachingSession,
  markExpenseInvoiced,
  listTrips,
  runCeoSignoffAutomation,
  runReminderAutomation,
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
  updateTrip,
} from './api';

function nightsBetween(departureDate, returnDate) {
  const start = new Date(departureDate);
  const end = new Date(returnDate);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return 0;
  const msPerDay = 1000 * 60 * 60 * 24;
  const raw = Math.floor((end - start) / msPerDay);
  return Math.max(raw, 0);
}

function toNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatAud(value) {
  return `AUD ${toNumber(value).toFixed(2)}`;
}

function formatDateAu(value) {
  const raw = String(value || '').trim();
  const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return raw;
  return `${match[3]}/${match[2]}/${match[1]}`;
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

const CONSULTANT_CATEGORY_OPTIONS = ['taxi', 'dinner', 'per_diem', 'misc'];
const ADMIN_CATEGORY_OPTIONS = ['flights', 'uber', 'hotel', ...CONSULTANT_CATEGORY_OPTIONS];
const EMAIL_INTAKE_CATEGORIES = ['flights', 'uber', 'hotel'];
const COACHING_SESSION_OUTCOMES = ['completed', 'no_show_chargeable', 'cancelled', 'postponed'];
const CONSULTANT_PRIORITY_ORDER = ['cameron bowles', 'collette brown'];
const COACH_ONLY_EMAILS = new Set(['tony.liston@adapsysgroup.com']);
const FLIGHT_LOCATION_OPTIONS = [
  'Brisbane',
  'Sydney',
  'Melbourne',
  'Canberra',
  'Perth',
  'Adelaide',
  'Honiara',
  'Port Moresby',
  'Nadi',
  'Apia',
  'Noumea',
];
const COUNTRY_CURRENCY_MAP = {
  Australia: 'AUD',
  'Papua New Guinea': 'PGK',
  Fiji: 'FJD',
  Samoa: 'WST',
  'New Caledonia': 'XPF',
  'Solomon Islands': 'SBD',
};

const SCREEN_TABS = [
  { id: 'session-mode', label: 'Session' },
  { id: 'create-project', label: 'Projects' },
  { id: 'submit-expense', label: 'Expenses' },
  { id: 'coaching-module', label: 'Coaching' },
  { id: 'tender-intelligence', label: 'Tenders' },
  { id: 'reports', label: 'Reports' },
  { id: 'expense-review', label: 'Review' },
  { id: 'admin-console', label: 'Admin Console' },
  { id: 'ato-rates', label: 'ATO' },
];

function currencyForCountry(country) {
  return COUNTRY_CURRENCY_MAP[country] || 'AUD';
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

const INITIAL_EXPENSE_FORM = {
  trip_id: '',
  submitted_by_role: 'admin',
  submitted_by_email: '',
  expense_date: '',
  category: 'taxi',
  amount_local: '',
  currency_local: 'AUD',
  exchange_rate: '1',
  gst_applicable: true,
  receipt_url: '',
  receipt_thumb_url: '',
  no_receipt: false,
  no_receipt_reason: '',
  notes: '',
  per_diem_breakfast: false,
  per_diem_lunch: false,
  per_diem_dinner: false,
  per_diem_incidental: true,
  per_diem_is_last_travel_day: false,
  per_diem_bulk_mode: false,
  per_diem_start_date: '',
  per_diem_end_date: '',
  flight_route_from: '',
  flight_route_to: '',
  flight_is_return_ticket: false,
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

export default function App() {
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
  });
  const [expenseForm, setExpenseForm] = useState(INITIAL_EXPENSE_FORM);
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
    notes: '',
  });
  const [coachingEngagementForm, setCoachingEngagementForm] = useState({
    name: '',
    job_title: '',
    client_org: '',
    coach_email: '',
    total_sessions: '5',
    sessions_used: '0',
  });
  const [coachingSessionForm, setCoachingSessionForm] = useState({
    engagement_id: '',
    session_date: '',
    session_type: 'completed',
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
  const [consultantCoachingReportFilters, setConsultantCoachingReportFilters] = useState({
    start_date: '',
    end_date: '',
  });
  const [isCreatingTrip, setIsCreatingTrip] = useState(false);
  const [isSubmittingExpense, setIsSubmittingExpense] = useState(false);
  const [isCreatingCoachingEngagement, setIsCreatingCoachingEngagement] = useState(false);
  const [editingCoachingEngagementId, setEditingCoachingEngagementId] = useState('');
  const [isSubmittingCoachingSession, setIsSubmittingCoachingSession] = useState(false);
  const [editingCoachingSessionId, setEditingCoachingSessionId] = useState('');
  const [savingConsultantInvoiceSessionId, setSavingConsultantInvoiceSessionId] = useState('');
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
    (localStorage.getItem('adapsys_user_email') || 'fi@adapsysgroup.com').trim().toLowerCase()
  );
  const [automationDryRun, setAutomationDryRun] = useState(true);
  const [selectedReportTripId, setSelectedReportTripId] = useState('');
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
  const [receiptDropActive, setReceiptDropActive] = useState(false);
  const [sessionLockedFromLink, setSessionLockedFromLink] = useState(false);
  const [receiptDraftByExpenseId, setReceiptDraftByExpenseId] = useState({});
  const [attachingReceiptExpenseId, setAttachingReceiptExpenseId] = useState('');
  const [tripDraftByExpenseId, setTripDraftByExpenseId] = useState({});
  const [movingExpenseId, setMovingExpenseId] = useState('');
  const [deletingExpenseId, setDeletingExpenseId] = useState('');
  const [adminEngagementDraftById, setAdminEngagementDraftById] = useState({});
  const [adminSessionDraftById, setAdminSessionDraftById] = useState({});
  const [adminEngagementSearch, setAdminEngagementSearch] = useState({
    name: '',
    client_org: '',
    coach_email: '',
  });
  const [adminEngagementSort, setAdminEngagementSort] = useState({
    key: 'name',
    direction: 'asc',
  });
  const [savingAdminEngagementId, setSavingAdminEngagementId] = useState('');
  const [savingAdminSessionId, setSavingAdminSessionId] = useState('');
  const [adminTripDraftById, setAdminTripDraftById] = useState({});
  const [savingAdminTripId, setSavingAdminTripId] = useState('');
  const [adminLookupDrafts, setAdminLookupDrafts] = useState({
    consultants: '[]',
    coaches: '[]',
    clientPrograms: '[]',
  });
  const [savingAdminLookupKey, setSavingAdminLookupKey] = useState('');
  const [atoRateDraftById, setAtoRateDraftById] = useState({});
  const [savingAtoRateId, setSavingAtoRateId] = useState('');
  const [layoutMode, setLayoutMode] = useState(() => {
    if (typeof window === 'undefined') return 'tabs';
    const saved = localStorage.getItem('adapsys_layout_mode');
    if (saved === 'tabs' || saved === 'scroll') return saved;
    return window.innerWidth >= 980 ? 'tabs' : 'scroll';
  });
  const headerRef = useRef(null);

  const clientOptions = useMemo(
    () => [...new Set(clientPrograms.map((row) => row.client_name))],
    [clientPrograms]
  );

  const isConsultantSession = sessionRole === 'consultant';
  const isAdminSession = sessionRole === 'admin';
  const isCoachOnlySession = COACH_ONLY_EMAILS.has(String(sessionEmail || '').toLowerCase());

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

  const orderedCoaches = useMemo(() => {
    const rank = (name) => {
      const idx = CONSULTANT_PRIORITY_ORDER.indexOf(String(name || '').toLowerCase());
      return idx === -1 ? 999 : idx;
    };
    return [...coaches].sort((a, b) => {
      const byRank = rank(a.name) - rank(b.name);
      if (byRank !== 0) return byRank;
      return a.name.localeCompare(b.name);
    });
  }, [coaches]);

  const coachNameByEmail = useMemo(() => {
    const map = {};
    orderedCoaches.forEach((coach) => {
      if (!coach?.email) return;
      map[String(coach.email).trim().toLowerCase()] = String(coach.name || coach.email).trim();
    });
    return map;
  }, [orderedCoaches]);

  const visibleScreenTabs = useMemo(() => {
    const roleFiltered = SCREEN_TABS.filter((tab) => {
      if (!isAdminSession && tab.id === 'admin-console') return false;
      if (isConsultantSession && tab.id === 'create-project') return false;
      return true;
    });
    if (isCoachOnlySession) {
      return roleFiltered.filter((tab) => tab.id === 'session-mode' || tab.id === 'coaching-module');
    }
    if (isConsultantSession) {
      return roleFiltered.filter(
        (tab) => tab.id === 'session-mode' || tab.id === 'submit-expense' || tab.id === 'coaching-module'
      );
    }
    return roleFiltered;
  }, [isAdminSession, isCoachOnlySession, isConsultantSession]);

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
  }, [adminEngagementSearch, adminEngagementSort, coachNameByEmail, coachingEngagements]);

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

  const dashboardLogoCandidates = useMemo(() => {
    if (typeof window === 'undefined') return [];

    const browserHost = window.location.hostname || '127.0.0.1';
    const overrideBase = (localStorage.getItem('adapsys_api_base') || '').trim();
    const baseCandidates = [
      overrideBase,
      `http://${browserHost}:8000`,
      'http://127.0.0.1:8000',
      'http://localhost:8000',
    ].filter(Boolean);

    return Array.from(new Set(baseCandidates.map((base) => `${base}/reports/brand-logo`)));
  }, []);

  const dashboardLogoSrc = dashboardLogoCandidates[dashboardLogoIndex] || '';

  const expenseTripOptions = useMemo(() => {
    if (!isConsultantSession || !sessionEmail) return trips;
    return trips.filter((trip) => {
      const roster = [trip.consultant_email, ...(trip.assigned_consultants || [])]
        .filter(Boolean)
        .map((email) => String(email).toLowerCase());
      return roster.includes(sessionEmail);
    });
  }, [isConsultantSession, sessionEmail, trips]);

  const selectedExpenseTrip = useMemo(
    () => trips.find((trip) => String(trip.id) === String(expenseForm.trip_id)) || null,
    [expenseForm.trip_id, trips]
  );

  const projectConsultantOptions = useMemo(() => {
    if (!selectedExpenseTrip) return [];
    const roster = Array.from(
      new Set(
        [selectedExpenseTrip.consultant_email, ...(selectedExpenseTrip.assigned_consultants || [])]
          .filter(Boolean)
          .map((email) => String(email).toLowerCase())
      )
    );

    return roster.map((email) => {
      const name = consultantNameByEmail[email];
      return {
        email,
        label: name || email,
      };
    });
  }, [consultantNameByEmail, selectedExpenseTrip]);

  const flightLocationOptions = useMemo(() => {
    const dynamicLocations = [
      selectedExpenseTrip?.destination_city,
      selectedExpenseTrip?.destination_country,
      tripForm.destination_city,
      tripForm.destination_country,
    ]
      .map((value) => String(value || '').trim())
      .filter(Boolean);
    return Array.from(new Set([...FLIGHT_LOCATION_OPTIONS, ...dynamicLocations]));
  }, [selectedExpenseTrip, tripForm.destination_city, tripForm.destination_country]);

  const selectedExpenseRate = useMemo(() => {
    if (!selectedExpenseTrip) return null;
    return (
      atoRates.find(
        (rate) =>
          rate.country === selectedExpenseTrip.destination_country && rate.active
      ) || null
    );
  }, [atoRates, selectedExpenseTrip]);

  const coachingEngagementOptions = useMemo(() => {
    if (!isConsultantSession) return coachingEngagements;
    return coachingEngagements.filter(
      (row) => String(row.coach_email || '').toLowerCase() === String(sessionEmail || '').toLowerCase()
    );
  }, [coachingEngagements, isConsultantSession, sessionEmail]);

  const coachingCoachOptions = useMemo(
    () => Array.from(new Set(coachingEngagements.map((row) => String(row.coach_email || '').trim().toLowerCase()).filter(Boolean))).sort(),
    [coachingEngagements]
  );

  const coachingCoacheeOptions = useMemo(
    () => Array.from(new Set(coachingEngagements.map((row) => String(row.name || '').trim()).filter(Boolean))).sort(),
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
        return {
          ...engagement,
          entitled,
          used,
          remaining,
          oneLeft: remaining === 1,
        };
      }),
    [coachingEngagementOptions]
  );

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

  const coachingPlannerRows = useMemo(() => {
    const queryName = String(coachingEngagementSearch.name || '').trim().toLowerCase();
    const queryClient = String(coachingEngagementSearch.client || '').trim().toLowerCase();
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
        return {
          engagement,
          pastSessions,
          todayAndFutureSessions,
        };
      });
  }, [coachingEngagementOptions, coachingEngagementSearch.client, coachingEngagementSearch.name, sessionsByEngagementId]);

  const recentCoachingSessions = useMemo(() => {
    return [...coachingSessions]
      .sort((a, b) => String(b.session_date || '').localeCompare(String(a.session_date || '')))
      .slice(0, 12);
  }, [coachingSessions]);

  const consultantExpenseRows = useMemo(() => {
    if (!isConsultantSession) return [];
    return [...expenses]
      .filter((row) => String(row.submitted_by_email || '').toLowerCase() === String(sessionEmail || '').toLowerCase())
      .sort((a, b) => String(b.expense_date || '').localeCompare(String(a.expense_date || '')));
  }, [expenses, isConsultantSession, sessionEmail]);

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

  const isBulkPerDiemMode =
    expenseForm.category === 'per_diem' && expenseForm.per_diem_bulk_mode;

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

  const incidentalEligibleDays = useMemo(() => {
    if (expenseForm.category !== 'per_diem') return 0;
    if (!expenseForm.per_diem_incidental) return 0;
    if (isBulkPerDiemMode) return Math.max(bulkPerDiemDates.length - 1, 0);
    return expenseForm.per_diem_is_last_travel_day ? 0 : 1;
  }, [
    bulkPerDiemDates.length,
    expenseForm.category,
    expenseForm.per_diem_incidental,
    expenseForm.per_diem_is_last_travel_day,
    isBulkPerDiemMode,
  ]);

  const perDiemClaimBreakdown = useMemo(() => {
    const daily = toNumber(selectedExpenseRate?.daily_rate_aud);
    const breakfast = expenseForm.per_diem_breakfast
      ? Number((daily * toNumber(selectedExpenseRate?.breakfast_pct)).toFixed(2))
      : 0;
    const lunch = expenseForm.per_diem_lunch
      ? Number((daily * toNumber(selectedExpenseRate?.lunch_pct)).toFixed(2))
      : 0;
    const dinner = expenseForm.per_diem_dinner
      ? Number((daily * toNumber(selectedExpenseRate?.dinner_pct)).toFixed(2))
      : 0;
    const incidentalMidpoint = Number(toNumber(selectedExpenseRate?.incidental_midpoint_aud).toFixed(2));
    const mealTotal = Number((breakfast + lunch + dinner).toFixed(2));
    const incidentalTotal = Number(
      (incidentalMidpoint * incidentalEligibleDays).toFixed(2)
    );
    const singleDayTotal = Number(
      (mealTotal + (expenseForm.per_diem_is_last_travel_day ? 0 : incidentalMidpoint)).toFixed(2)
    );
    const bulkGrandTotal = Number(
      (mealTotal * bulkPerDiemDates.length + incidentalTotal).toFixed(2)
    );
    return {
      daily,
      breakfast,
      lunch,
      dinner,
      mealTotal,
      incidentalMidpoint,
      incidentalEligibleDays,
      incidentalTotal,
      singleDayTotal,
      bulkGrandTotal,
    };
  }, [
    bulkPerDiemDates.length,
    expenseForm.per_diem_breakfast,
    expenseForm.per_diem_dinner,
    expenseForm.per_diem_is_last_travel_day,
    expenseForm.per_diem_lunch,
    incidentalEligibleDays,
    selectedExpenseRate,
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
      activeProjects: activeClientNames.size,
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

  const filteredTenders = useMemo(() => {
    const rows = tenderFilter === 'all' ? tenders : tenders.filter((row) => row.status === tenderFilter);
    return rows;
  }, [tenderFilter, tenders]);

  async function refresh() {
    try {
      if (isCoachOnlySession) {
        const [coachesData, clientProgramsData, coachingEngagementData, coachingSessionData] = await Promise.all([
          listCoaches(),
          listClientPrograms(),
          listCoachingEngagements(),
          listCoachingSessions(),
        ]);
        setTrips([]);
        setExpenses([]);
        setTenders([]);
        setTenderSummary({ total: 0, urgent: 0, pursue: 0, monitor: 0, ignore: 0, led: 0 });
        setAtoRates([]);
        setConsultants([]);
        setCoaches(coachesData);
        setClientPrograms(clientProgramsData);
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
      ]);
      setTrips(tripData);
      setExpenses(expenseData);
      setTenders(tenderData);
      setTenderSummary(tenderSummaryData);
      setCoachingEngagements(coachingEngagementData);
      setCoachingSessions(coachingSessionData);
      setAtoRates(ratesData);
      setConsultants(consultantsData);
      setCoaches(coachesData);
      setClientPrograms(clientProgramsData);
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
        const defaultProgram = clientProgramsData[0].program_name;
        setTripForm((prev) => ({
          ...prev,
          client_name: defaultClient,
          program_name: defaultProgram,
        }));
      }
      setExpenseForm((prev) => {
        const next = { ...prev };
        if (isConsultantSession) {
          next.submitted_by_role = 'consultant';
          next.submitted_by_email = sessionEmail || next.submitted_by_email;
        } else if (!next.submitted_by_email) {
          next.submitted_by_email = consultantsData[0]?.email || '';
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
      setSelectedReportTripId((prev) => prev || tripData[0]?.id || '');
    } catch (error) {
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
      const payload = {
        ...coachingEngagementForm,
        total_sessions: Number(coachingEngagementForm.total_sessions || 0),
        sessions_used: Number(coachingEngagementForm.sessions_used || 0),
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
    });
    setCoachingStatus('Coachee record edit cancelled.');
  }

  async function onLogCoachingSession(event) {
    event.preventDefault();
    setIsSubmittingCoachingSession(true);
    setCoachingStatus(editingCoachingSessionId ? 'Updating coaching session...' : 'Logging coaching session...');
    try {
      const payload = {
        ...coachingSessionForm,
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
      invoiced_to_adapsys: false,
      session_date: '',
      notes: '',
    }));
    setCoachingStatus('Session edit cancelled.');
  }

  async function onToggleConsultantSessionInvoiced(session) {
    const sessionId = String(session.id || '');
    if (!sessionId) return;
    setSavingConsultantInvoiceSessionId(sessionId);
    try {
      await updateCoachingSession(session.id, {
        engagement_id: session.engagement_id,
        session_date: session.session_date,
        session_type: session.session_type,
        duration_mins: Number(session.duration_mins || 60),
        delivery_mode: session.delivery_mode || 'video',
        invoiced_to_adapsys: !Boolean(session.invoiced_to_adapsys),
        notes: session.notes || '',
      });
      setCoachingStatus(
        !Boolean(session.invoiced_to_adapsys)
          ? 'Session marked as invoiced to Adapsys.'
          : 'Session marked as not invoiced.'
      );
      await refresh();
    } catch (error) {
      setCoachingStatus(error.message);
    } finally {
      setSavingConsultantInvoiceSessionId('');
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
    const { report_by, coach_email, coachee_name, start_date, end_date } = coachingReportFilters;
    const selectedScopeValue = report_by === 'coach' ? coach_email : coachee_name;
    if (!selectedScopeValue) {
      setCoachingReportStatus(
        report_by === 'coach'
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
        client_org: '',
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
    const { report_by, coach_email, coachee_name, start_date, end_date } = coachingReportFilters;
    const selectedScopeValue = report_by === 'coach' ? coach_email : coachee_name;
    if (!selectedScopeValue) {
      setCoachingReportStatus(
        report_by === 'coach'
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
        client_org: '',
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
      anchor.download = `adapsys-coaching-report-${report_by}-${safeClient}.pdf`;
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

    setSavingAtoRateId(String(rateId));
    try {
      await updateAtoRate(rateId, {
        daily_rate_aud: toNumber(draft.daily_rate_aud),
        breakfast_pct: toNumber(draft.breakfast_pct),
        lunch_pct: toNumber(draft.lunch_pct),
        dinner_pct: toNumber(draft.dinner_pct),
        incidental_midpoint_aud: toNumber(draft.incidental_midpoint_aud),
        tax_year: draft.tax_year,
        active: Boolean(draft.active),
      });
      setStatus('ATO rate updated. Yearly midpoint values are now editable in-app.');
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

  function onAdminEngagementFieldChange(engagementId, field, value) {
    const key = String(engagementId);
    setAdminEngagementDraftById((prev) => ({
      ...prev,
      [key]: {
        ...(prev[key] || {}),
        [field]: value,
      },
    }));
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
  }

  async function onSaveAdminTrip(trip) {
    const key = String(trip.id);
    const draft = adminTripDraftById[key] || {};
    const assignedRaw =
      draft.assigned_consultants ?? (Array.isArray(trip.assigned_consultants) ? trip.assigned_consultants.join(', ') : '');
    const assigned = String(assignedRaw)
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
    };

    setSavingAdminTripId(key);
    try {
      await updateTrip(trip.id, payload);
      setStatus(`Updated project: ${payload.name}.`);
      setAdminTripDraftById((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
      await refresh();
    } catch (error) {
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
    try {
      if (kind === 'consultants') {
        await updateLookupConsultants({ items: parsed });
      } else if (kind === 'coaches') {
        await updateLookupCoaches({ items: parsed });
      } else {
        await updateLookupClientPrograms({ items: parsed });
      }
      setStatus(`Updated ${kind} lookup file.`);
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setSavingAdminLookupKey('');
    }
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
      session_rate:
        draft.session_rate === ''
          ? null
          : draft.session_rate !== undefined
            ? Number(draft.session_rate)
            : engagement.session_rate,
      contract_start: draft.contract_start === '' ? null : (draft.contract_start ?? engagement.contract_start),
      contract_end: draft.contract_end === '' ? null : (draft.contract_end ?? engagement.contract_end),
    };

    setSavingAdminEngagementId(key);
    try {
      await updateCoachingEngagement(engagement.id, payload);
      setStatus(`Updated coachee record: ${payload.name}.`);
      setAdminEngagementDraftById((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setSavingAdminEngagementId('');
    }
  }

  async function onSaveAdminSession(session) {
    const key = String(session.id);
    const draft = adminSessionDraftById[key] || {};
    const payload = {
      engagement_id: draft.engagement_id ?? session.engagement_id,
      session_date: draft.session_date ?? session.session_date,
      session_type: draft.session_type ?? session.session_type,
      duration_mins: Number(draft.duration_mins ?? session.duration_mins ?? 60),
      delivery_mode: draft.delivery_mode ?? session.delivery_mode ?? 'video',
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
      await refresh();
    } catch (error) {
      setStatus(error.message);
    } finally {
      setSavingAdminSessionId('');
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

  async function onApplySession() {
    const normalizedRole = (sessionRole || 'admin').trim().toLowerCase();
    const normalizedEmail = (sessionEmail || '').trim().toLowerCase();

    if (normalizedRole === 'consultant' && !normalizedEmail) {
      setStatus('Consultant mode needs a consultant email.');
      return;
    }

    localStorage.setItem('adapsys_user_role', normalizedRole);
    localStorage.setItem('adapsys_user_email', normalizedEmail || 'fi@adapsysgroup.com');

    setSessionRole(normalizedRole);
    setSessionEmail(normalizedEmail || 'fi@adapsysgroup.com');

    setExpenseForm((prev) => ({
      ...prev,
      submitted_by_role: normalizedRole === 'consultant' ? 'consultant' : 'admin',
      submitted_by_email:
        normalizedRole === 'consultant'
          ? normalizedEmail
          : normalizedEmail || prev.submitted_by_email,
      trip_id: '',
    }));

    setStatus(`Session mode set to ${normalizedRole}: ${normalizedEmail || 'fi@adapsysgroup.com'}`);
    await refresh();
  }

  async function onRunReminderAutomation() {
    try {
      const rows = await runReminderAutomation({ dry_run: automationDryRun });
      setStatus(`Reminder automation processed ${rows.length} reminder event(s).`);
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function onRunCeoSignoff() {
    try {
      const rows = await runCeoSignoffAutomation({ dry_run: automationDryRun });
      setStatus(`CEO sign-off automation processed ${rows.length} project(s).`);
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
          daily_rate_aud: rate.daily_rate_aud,
          breakfast_pct: rate.breakfast_pct,
          lunch_pct: rate.lunch_pct,
          dinner_pct: rate.dinner_pct,
          incidental_midpoint_aud: rate.incidental_midpoint_aud || 0,
          tax_year: rate.tax_year,
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
          : availableEmails[0] || '';
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
        submitted_by_email: allowed[0] || prev.submitted_by_email,
      };
    });
  }, [expenseForm.trip_id, projectConsultantOptions]);

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
        setSessionEmail(linkEmail);
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
    function onStorageChange(event) {
      if (!event.key || !['adapsys_user_role', 'adapsys_user_email'].includes(event.key)) {
        return;
      }

      const nextRole = (localStorage.getItem('adapsys_user_role') || 'admin').trim().toLowerCase();
      const nextEmail = (localStorage.getItem('adapsys_user_email') || 'fi@adapsysgroup.com').trim().toLowerCase();

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
    setTripStatus(editingProjectId ? 'Updating project...' : 'Creating project...');
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
          ? `Project updated: ${savedProject.name}.`
          : `Project created: ${savedProject.name}. Ready to submit expenses.`
      );
      setTripStatus(
        editingProjectId ? `Updated project: ${savedProject.name}.` : `Created project: ${savedProject.name}.`
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
        setTripForm((prev) => ({ ...prev, name: '', destination_city: '' }));
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
    setIsSubmittingExpense(true);
    setExpenseStatus('Submitting expense...');
    try {
      const perDiemClaimNotes =
        expenseForm.category === 'per_diem'
          ? [
              'Per diem claim sheet',
              `Breakfast claimed: ${expenseForm.per_diem_breakfast ? 'Yes' : 'No'}${expenseForm.per_diem_breakfast ? ` (${formatAud(perDiemClaimBreakdown.breakfast)})` : ''}`,
              `Lunch claimed: ${expenseForm.per_diem_lunch ? 'Yes' : 'No'}${expenseForm.per_diem_lunch ? ` (${formatAud(perDiemClaimBreakdown.lunch)})` : ''}`,
              `Dinner claimed: ${expenseForm.per_diem_dinner ? 'Yes' : 'No'}${expenseForm.per_diem_dinner ? ` (${formatAud(perDiemClaimBreakdown.dinner)})` : ''}`,
              `Incidental enabled: ${expenseForm.per_diem_incidental ? 'Yes' : 'No'}`,
              `Incidental midpoint/day: ${formatAud(perDiemClaimBreakdown.incidentalMidpoint)}`,
              `Incidental eligible days: ${incidentalEligibleDays}`,
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
        expenseForm.category === 'flights'
          ? [
              expenseForm.flight_route_from
                ? `Flight from: ${expenseForm.flight_route_from}`
                : null,
              expenseForm.flight_route_to
                ? `Flight to: ${expenseForm.flight_route_to}`
                : null,
              `Return ticket: ${expenseForm.flight_is_return_ticket ? 'Yes' : 'No'}`,
            ]
              .filter(Boolean)
              .join('\n')
          : '';

      const composedNotes = [mergedNotes, flightNotes]
        .map((item) => (item || '').trim())
        .filter(Boolean)
        .join('\n\n');

      const submitDates = isBulkPerDiemMode ? bulkPerDiemDates : [expenseForm.expense_date];
      if (!submitDates.length) {
        setExpenseStatus('Set a valid per diem date range (start/end) to submit multiple days.');
        setIsSubmittingExpense(false);
        return;
      }

      const normalizedTripId = String(expenseForm.trip_id || '');
      const normalizedSubmitter = String(expenseForm.submitted_by_email || '').toLowerCase();
      const normalizedCategory = String(expenseForm.category || '').toLowerCase();

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

      const {
        per_diem_bulk_mode,
        per_diem_start_date,
        per_diem_end_date,
        per_diem_incidental,
        flight_route_from,
        flight_route_to,
        flight_is_return_ticket,
        ...expensePayload
      } = expenseForm;

      await Promise.all(
        submitDates.map((expenseDate, index) => {
          const incidentalApplied =
            expenseForm.category !== 'per_diem'
              ? false
              : !expenseForm.per_diem_incidental
                ? false
              : isBulkPerDiemMode
                ? index < submitDates.length - 1
                : !expenseForm.per_diem_is_last_travel_day;
          const incidentalForEntry = incidentalApplied ? perDiemClaimBreakdown.incidentalMidpoint : 0;
          const perDiemEntryTotal = Number(
            (perDiemClaimBreakdown.mealTotal + incidentalForEntry).toFixed(2)
          );
          const entryNotes =
            expenseForm.category === 'per_diem'
              ? [
                  composedNotes,
                  `Incidental midpoint applied: ${incidentalApplied ? 'Yes' : 'No'} (${formatAud(incidentalForEntry)})`,
                  `Per diem entry total: ${formatAud(perDiemEntryTotal)}`,
                ]
                  .filter(Boolean)
                  .join('\n')
              : composedNotes || null;

          return createExpense({
            ...expensePayload,
            expense_date: expenseDate,
            amount_local:
              expenseForm.category === 'per_diem' ? perDiemEntryTotal : Number(expenseForm.amount_local),
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
      setExpenseForm((prev) => ({
        ...INITIAL_EXPENSE_FORM,
        trip_id: prev.trip_id,
        submitted_by_role: prev.submitted_by_role,
        submitted_by_email: prev.submitted_by_email,
        category: prev.category,
        currency_local: prev.currency_local,
        exchange_rate: prev.currency_local === 'AUD' ? '1' : '',
        gst_applicable: prev.currency_local === 'AUD',
        per_diem_bulk_mode: prev.category === 'per_diem',
        per_diem_start_date: prev.per_diem_start_date,
        per_diem_end_date: prev.per_diem_end_date,
      }));
      await refresh();
    } catch (error) {
      const message =
        error?.message === 'Failed to fetch'
          ? 'Failed to fetch. Confirm backend is running at http://127.0.0.1:8000.'
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
      anchor.download = `adapsys-expense-pack-${selectedReportTripId}.pdf`;
      anchor.click();
      window.URL.revokeObjectURL(url);
      setStatus('Client expense report PDF download started.');
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
    setActiveScreenTabId(sectionId);
    if (isTabbedLayout) {
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
    <div className="container">
      <header className="header" ref={headerRef}>
        <div className="header-top">
          <div className="header-brand-spacer" aria-hidden="true" />
          <div className="header-brand-block">
            <h1>Adapsys Australia Pacific Portal</h1>
            <div className="status">Premium mobile-first operating dashboard</div>
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
            ) : null}
          </div>
        </div>
        <div className="kpi-grid">
          <div className="kpi-chip">
            <span className="kpi-label">Approved</span>
            <strong>{dashboardMetrics.approvedCount}</strong>
          </div>
          <div className="kpi-chip">
            <span className="kpi-label">Pending</span>
            <strong>{dashboardMetrics.pendingCount}</strong>
          </div>
          <div className="kpi-chip">
            <span className="kpi-label">Active Projects</span>
            <strong>{dashboardMetrics.activeProjects}</strong>
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
          <div className="kpi-chip">
            <span className="kpi-label">Invoiced</span>
            <strong>{formatAud(portfolioInvoicing.invoicedAud)}</strong>
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
                {tab.label}
              </button>
            ))}
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
                  value={sessionEmail}
                  onChange={(e) => setSessionEmail(e.target.value)}
                  placeholder="name@adapsysgroup.com"
                />
              </div>
            </div>
            <button type="button" onClick={onApplySession} style={{ marginTop: 8 }}>
              Apply Session
            </button>
            <div className="status" style={{ marginTop: 8 }}>
              Use this instead of Swagger headers. Consultant mode shows only assigned projects.
            </div>
          </>
        )}
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
          <h2>Project Setup (Admin)</h2>
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
              <label>Program / Workstream</label>
              <input
                list="program-options"
                value={tripForm.program_name}
                onChange={(e) => setTripForm({ ...tripForm, program_name: e.target.value })}
                placeholder="Choose or type a program"
                required
              />
            </div>
              <div>
              <label>Project Name</label>
              <input
                value={tripForm.name}
                onChange={(e) => setTripForm({ ...tripForm, name: e.target.value })}
                required
              />
              </div>
              <div>
              <label>Edit Existing Project (optional)</label>
              <select
                value={editingProjectId}
                onChange={(e) => {
                  setEditingProjectId(e.target.value);
                  if (!e.target.value) {
                    setTripStatus('Create mode: enter details for a new project.');
                  }
                }}
              >
                <option value="">Create New Project</option>
                {trips.map((trip) => (
                  <option key={trip.id} value={trip.id}>
                    Edit: {trip.name} — {trip.client_name}/{trip.program_name}
                  </option>
                ))}
              </select>
              </div>
            </div>
          <div className="status">Leave "Edit Existing Project" blank when creating a new project.</div>

          <div className="grid project-setup-row-four">
            <div>
              <label>Project Start Date</label>
              <input
                type="date"
                value={tripForm.project_start_date}
                onChange={(e) =>
                  setTripForm({ ...tripForm, project_start_date: e.target.value })
                }
              />
            </div>
            <div>
              <label>Project End Date</label>
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

          <label>Assigned Consultant Roster</label>
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
              Lead Consultant Only
            </button>
            <div className="roster-lead-picker">
              <label>Lead Consultant</label>
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
                <option value="">No lead consultant selected</option>
                {orderedConsultants.map((consultant) => (
                  <option key={consultant.email} value={consultant.email}>
                    {consultant.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="status">
            Select everyone going to this project. Consultants in this roster receive reminders.
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
                ? 'Updating Project...'
                : 'Creating Project...'
              : editingProjectId
                ? 'Update Project'
                : 'Create Project'}
          </button>
          {tripStatus ? <div className="status">{tripStatus}</div> : null}
        </form>
        </section>
      ) : null}

      <section id="submit-expense" className="card" style={sectionVisibilityStyle('submit-expense')}>
        <h2>Submit Expense</h2>
        <form onSubmit={onCreateExpense}>
          <div className="expense-compact-row expense-compact-row-top">
            <div className="expense-field-project">
              <label>Project</label>
              <select
                value={expenseForm.trip_id}
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
                    isConsultantSession && roster.includes((sessionEmail || '').toLowerCase())
                      ? (sessionEmail || '').toLowerCase()
                      : roster[0] || '';

                  setExpenseForm((prev) => ({
                    ...prev,
                    trip_id: tripId,
                    submitted_by_email: fallbackConsultant,
                  }));
                  setExpenseStatus('');
                }}
                required
              >
                <option value="">Select project</option>
                {expenseTripOptions.map((trip) => (
                  <option key={trip.id} value={trip.id}>
                    {trip.name} — {trip.client_name}/{trip.program_name}
                  </option>
                ))}
              </select>
            </div>

            <div className="expense-field-consultant">
              <label>Consultant</label>
              <select
                value={expenseForm.submitted_by_email}
                onChange={(e) =>
                  setExpenseForm({ ...expenseForm, submitted_by_email: e.target.value })
                }
                required
                disabled={!expenseForm.trip_id || !projectConsultantOptions.length}
              >
                <option value="">
                  {expenseForm.trip_id ? 'Select consultant' : 'Select project first'}
                </option>
                {projectConsultantOptions.map((option) => (
                  <option key={option.email} value={option.email}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="expense-field-category">
              <label>Category</label>
              <select
                value={expenseForm.category}
                onChange={(e) =>
                  setExpenseForm((prev) => ({
                    ...prev,
                    category: e.target.value,
                  }))
                }
              >
                {categoryOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="expense-top-meta-row">
            <label className="inline-checkbox per-diem-toggle">
              <input
                type="checkbox"
                checked={expenseForm.category === 'per_diem'}
                onChange={(e) =>
                  setExpenseForm((prev) => ({
                    ...prev,
                    category: e.target.checked ? 'per_diem' : prev.category === 'per_diem' ? 'taxi' : prev.category,
                    per_diem_bulk_mode: e.target.checked ? true : prev.per_diem_bulk_mode,
                  }))
                }
              />{' '}
              Per diem claim
            </label>
            <div className="status expense-flow-hint">
              Flow: select project, then consultant, then category, then date and amount.
            </div>
          </div>

          {!isConsultantSession ? (
            <>
              <label>Submitted By Role</label>
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
            </>
          ) : null}

          {!isConsultantSession && expenseForm.submitted_by_role === 'consultant' &&
          expenseForm.trip_id &&
          !projectConsultantOptions.length ? (
            <div className="status">No consultants are assigned to this project yet. Update project roster first.</div>
          ) : null}

          {expenseForm.category === 'flights' ? (
            <>
              <div className="grid">
                <div>
                  <label>Flight From</label>
                  <select
                    value={expenseForm.flight_route_from}
                    onChange={(e) =>
                      setExpenseForm({ ...expenseForm, flight_route_from: e.target.value })
                    }
                    required
                  >
                    <option value="">Select departure city</option>
                    {flightLocationOptions.map((location) => (
                      <option key={`from-${location}`} value={location}>
                        {location}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label>Flight To</label>
                  <select
                    value={expenseForm.flight_route_to}
                    onChange={(e) =>
                      setExpenseForm({ ...expenseForm, flight_route_to: e.target.value })
                    }
                    required
                  >
                    <option value="">Select destination city</option>
                    {flightLocationOptions.map((location) => (
                      <option key={`to-${location}`} value={location}>
                        {location}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <label>
                <input
                  type="checkbox"
                  checked={expenseForm.flight_is_return_ticket}
                  onChange={(e) =>
                    setExpenseForm({ ...expenseForm, flight_is_return_ticket: e.target.checked })
                  }
                />{' '}
                Return ticket
              </label>
            </>
          ) : null}

          <div className="expense-compact-row expense-compact-row-finance">
            <div className="expense-field-date">
              <label>{isBulkPerDiemMode ? 'Date (optional in bulk mode)' : 'Date'}</label>
              <input
                type="date"
                value={expenseForm.expense_date}
                onChange={(e) =>
                  setExpenseForm({ ...expenseForm, expense_date: e.target.value })
                }
                required={!isBulkPerDiemMode}
              />
            </div>
            <div className="expense-field-amount">
              <label>Amount</label>
              <input
                type="number"
                step="0.01"
                value={expenseForm.amount_local}
                onChange={(e) => setExpenseForm({ ...expenseForm, amount_local: e.target.value })}
                required
              />
            </div>
            <div className="expense-field-gst">
              <label>GST</label>
              <select
                value={expenseForm.gst_applicable ? 'yes' : 'no'}
                onChange={(e) =>
                  setExpenseForm({ ...expenseForm, gst_applicable: e.target.value === 'yes' })
                }
              >
                <option value="yes">Incl</option>
                <option value="no">No GST</option>
              </select>
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

          {expenseForm.currency_local !== 'AUD' ? (
            <>
              <label>Exchange Rate to AUD</label>
              <input
                type="number"
                step="0.0001"
                value={expenseForm.exchange_rate}
                onChange={(e) => setExpenseForm({ ...expenseForm, exchange_rate: e.target.value })}
                placeholder="Enter receipt-day exchange rate"
                required
              />
              <div className="status">Required for overseas currencies. Use the rate from receipt day.</div>
            </>
          ) : (
            <div className="status">Exchange rate locked to 1.0000 for AUD expenses.</div>
          )}

          {expenseForm.category === 'per_diem' ? (
            <div className="per-diem-sheet">
              <div className="status">
                Tick the meals you are claiming. Incidentals apply only when enabled below (all travel days except the last day).
                {selectedExpenseRate
                  ? ` Daily baseline: ${formatAud(selectedExpenseRate.daily_rate_aud)} (${selectedExpenseRate.country})`
                  : ''}
              </div>
              <label className="inline-checkbox per-diem-incidental-toggle">
                <input
                  type="checkbox"
                  checked={expenseForm.per_diem_incidental}
                  onChange={(e) =>
                    setExpenseForm((prev) => ({
                      ...prev,
                      per_diem_incidental: e.target.checked,
                    }))
                  }
                />{' '}
                Include incidental allowance
              </label>
              <div className="status">Bulk mode is enabled by default to submit the full travel range once.</div>
              {!isBulkPerDiemMode ? (
                <>
                  <div className="status">Day-by-day mode is active. Submit one per diem day at a time.</div>
                  <label>
                    <input
                      type="checkbox"
                      checked={expenseForm.per_diem_is_last_travel_day}
                      onChange={(e) =>
                        setExpenseForm((prev) => ({
                          ...prev,
                          per_diem_is_last_travel_day: e.target.checked,
                        }))
                      }
                    />{' '}
                    This is the final travel day (no incidental)
                  </label>
                </>
              ) : null}
              {isBulkPerDiemMode ? (
                <div className="grid" style={{ marginTop: 8 }}>
                  <div>
                    <label>Per Diem Start Date</label>
                    <input
                      type="date"
                      value={expenseForm.per_diem_start_date}
                      onChange={(e) =>
                        setExpenseForm({ ...expenseForm, per_diem_start_date: e.target.value })
                      }
                      required
                    />
                  </div>
                  <div>
                    <label>Per Diem End Date</label>
                    <input
                      type="date"
                      value={expenseForm.per_diem_end_date}
                      onChange={(e) =>
                        setExpenseForm({ ...expenseForm, per_diem_end_date: e.target.value })
                      }
                      required
                    />
                  </div>
                  <div className="status" style={{ gridColumn: '1 / -1' }}>
                    {bulkPerDiemDates.length
                      ? `Will create ${bulkPerDiemDates.length} entries. Incidentals apply on ${Math.max(
                          bulkPerDiemDates.length - 1,
                          0
                        )} day(s) only (all except last day). Bulk total ${formatAud(
                          perDiemClaimBreakdown.bulkGrandTotal
                        )}.`
                      : 'Choose a valid start/end range.'}
                  </div>
                </div>
              ) : null}

              <div className="per-diem-timesheet">
                <div className="per-diem-timesheet-head">Per Diem Days Preview</div>
                {perDiemDisplayDates.length === 0 ? (
                  <div className="status">Choose dates to display the per diem day list.</div>
                ) : (
                  perDiemDisplayDates.map((isoDate, index) => {
                    const isLastTravelDay = index === perDiemDisplayDates.length - 1;
                    const incidentalApplies =
                      expenseForm.per_diem_incidental &&
                      (isBulkPerDiemMode ? !isLastTravelDay : !expenseForm.per_diem_is_last_travel_day);
                    return (
                      <div key={`${isoDate}-${index}`} className="per-diem-timesheet-row">
                        <div className="per-diem-timesheet-date">{formatDateAu(isoDate)}</div>
                        <span
                          className={`per-diem-timesheet-check ${
                            expenseForm.per_diem_breakfast ? 'is-active' : 'is-inactive'
                          }`}
                        >
                          {expenseForm.per_diem_breakfast ? '✓' : '—'} Breakfast
                        </span>
                        <span
                          className={`per-diem-timesheet-check ${
                            expenseForm.per_diem_lunch ? 'is-active' : 'is-inactive'
                          }`}
                        >
                          {expenseForm.per_diem_lunch ? '✓' : '—'} Lunch
                        </span>
                        <span
                          className={`per-diem-timesheet-check ${
                            expenseForm.per_diem_dinner ? 'is-active' : 'is-inactive'
                          }`}
                        >
                          {expenseForm.per_diem_dinner ? '✓' : '—'} Dinner
                        </span>
                        <span
                          className={`per-diem-timesheet-check ${incidentalApplies ? 'is-active' : 'is-inactive'}`}
                        >
                          {incidentalApplies ? '✓' : '—'} Incidental
                        </span>
                      </div>
                    );
                  })
                )}
              </div>

              <div className="per-diem-grid">
                <label>
                  <input
                    type="checkbox"
                    checked={expenseForm.per_diem_breakfast}
                    onChange={(e) =>
                      setExpenseForm({
                        ...expenseForm,
                        per_diem_breakfast: e.target.checked,
                      })
                    }
                  />{' '}
                  Breakfast ({formatAud(perDiemClaimBreakdown.breakfast)})
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={expenseForm.per_diem_lunch}
                    onChange={(e) =>
                      setExpenseForm({
                        ...expenseForm,
                        per_diem_lunch: e.target.checked,
                      })
                    }
                  />{' '}
                  Lunch ({formatAud(perDiemClaimBreakdown.lunch)})
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={expenseForm.per_diem_dinner}
                    onChange={(e) =>
                      setExpenseForm({
                        ...expenseForm,
                        per_diem_dinner: e.target.checked,
                      })
                    }
                  />{' '}
                  Dinner ({formatAud(perDiemClaimBreakdown.dinner)})
                </label>
              </div>
              <div className="status">
                Incidental midpoint: {formatAud(perDiemClaimBreakdown.incidentalMidpoint)} per eligible day.
              </div>
              <div className="status">
                Suggested per diem total:{' '}
                {formatAud(
                  isBulkPerDiemMode
                    ? perDiemClaimBreakdown.bulkGrandTotal
                    : perDiemClaimBreakdown.singleDayTotal
                )}
              </div>
              <button
                type="button"
                className="secondary"
                onClick={() =>
                  setExpenseForm((prev) => ({
                    ...prev,
                    amount_local: isBulkPerDiemMode
                      ? String(perDiemClaimBreakdown.bulkGrandTotal)
                      : String(perDiemClaimBreakdown.singleDayTotal),
                    currency_local: 'AUD',
                    exchange_rate: '1',
                  }))
                }
              >
                Use Suggested Per Diem Amount
              </button>
            </div>
          ) : null}

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
                type="file"
                accept="image/*"
                capture="environment"
                onChange={(e) => handleReceiptFile(e.target.files?.[0])}
              />
            </div>
          ) : null}

          <div className="status">
            One receipt image is enough for most expenses. You only need URL/thumbnail fields for admin workflows.
          </div>

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

          <label>Notes</label>
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
                  trip_id: isConsultantSession ? prev.trip_id : '',
                }));
                setExpenseStatus('Draft cleared.');
              }}
              disabled={isSubmittingExpense}
            >
              Clear Form
            </button>
          </div>
          {expenseStatus ? <div className="status">{expenseStatus}</div> : null}
        </form>
        {isConsultantSession ? (
          <div style={{ marginTop: 12 }}>
            <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
              My Expense & Per Diem Check
            </h3>
            <div className="status" style={{ marginBottom: 8 }}>
              Showing your own submitted expenses only.
            </div>
            <div className="status" style={{ marginBottom: 8 }}>
              Total entries: {consultantExpenseRows.length} · Per diem entries:{' '}
              {consultantExpenseRows.filter((row) => row.category === 'per_diem').length}
            </div>
            {consultantExpenseRows.length === 0 ? (
              <div className="status">No expenses submitted yet.</div>
            ) : (
              consultantExpenseRows.slice(0, 20).map((row) => (
                <div
                  key={row.id}
                  className="status"
                  style={{
                    border: '1px solid #d6e3e3',
                    borderRadius: 10,
                    padding: '8px 10px',
                    marginBottom: 6,
                    background: '#f9fdfd',
                  }}
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
          <label>Project</label>
          <select
            value={emailIntakeForm.trip_id}
            onChange={(e) => setEmailIntakeForm({ ...emailIntakeForm, trip_id: e.target.value })}
            required
          >
            <option value="">Select project</option>
            {trips.map((trip) => (
              <option key={trip.id} value={trip.id}>
                {trip.name} — {trip.client_name}/{trip.program_name}
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
                {option}
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

        {!isConsultantSession ? (
          <>
            <details>
              <summary>Create coaching engagement (Admin/Finance)</summary>
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
              <input
                value={coachingEngagementForm.client_org}
                onChange={(e) =>
                  setCoachingEngagementForm((prev) => ({ ...prev, client_org: e.target.value }))
                }
                list="coaching-client-options"
                placeholder="Select or type client"
                required
              />
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

          </>
        ) : null}

        <form onSubmit={onLogCoachingSession} className="coaching-session-form" style={{ marginTop: 12 }}>
          <label>Engagement</label>
          <select
            value={coachingSessionForm.engagement_id}
            onChange={(e) =>
              setCoachingSessionForm((prev) => ({ ...prev, engagement_id: e.target.value }))
            }
            required
          >
            <option value="">Select engagement</option>
            {coachingEngagementOptions.map((engagement) => (
              <option key={engagement.id} value={engagement.id}>
                {engagement.name} — {engagement.client_org}
              </option>
            ))}
          </select>

          <div className="grid">
            <div>
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
            <div>
              <label>Session Outcome</label>
              <select
                value={coachingSessionForm.session_type}
                onChange={(e) =>
                  setCoachingSessionForm((prev) => ({ ...prev, session_type: e.target.value }))
                }
              >
                {coachingOutcomeOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
            <div>
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

        {isConsultantSession ? (
          <div className="coaching-planner" style={{ marginTop: 12 }}>
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
              Showing {coachingPlannerRows.length} engagement(s).
            </div>
            {coachingPlannerRows.length === 0 ? (
              <div className="status">No matching coaching engagements.</div>
            ) : (
              coachingPlannerRows.map(({ engagement, pastSessions, todayAndFutureSessions }) => (
                <div key={engagement.id} className="coaching-planner-card">
                  <div className="coaching-planner-head">
                    <strong>{engagement.name}</strong>
                    <span>{engagement.client_org}</span>
                  </div>
                  <div className="coaching-planner-grid">
                    <div>
                      <div className="status"><strong>Upcoming / Planned</strong></div>
                      {todayAndFutureSessions.length === 0 ? (
                        <div className="status">No future sessions scheduled.</div>
                      ) : (
                        todayAndFutureSessions.map((session) => (
                          <div key={session.id} className="status coaching-planner-row">
                            {formatDateAu(session.session_date)} · {session.session_type}
                            {session.invoiced_to_adapsys ? ' · Invoiced' : ' · Not invoiced'}
                          </div>
                        ))
                      )}
                    </div>
                    <div>
                      <div className="status"><strong>History</strong></div>
                      {pastSessions.length === 0 ? (
                        <div className="status">No past sessions yet.</div>
                      ) : (
                        pastSessions.slice(0, 8).map((session) => (
                          <div key={session.id} className="status coaching-planner-row">
                            {formatDateAu(session.session_date)} · {session.session_type}
                            {session.invoiced_to_adapsys ? ' · Invoiced' : ' · Not invoiced'}
                          </div>
                        ))
                      )}
                    </div>
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
                    <button
                      type="button"
                      className="secondary coaching-row-action"
                      onClick={() => onToggleConsultantSessionInvoiced(row)}
                      disabled={savingConsultantInvoiceSessionId === String(row.id)}
                    >
                      {savingConsultantInvoiceSessionId === String(row.id)
                        ? 'Saving...'
                        : row.invoiced_to_adapsys
                          ? 'Mark Not Invoiced'
                          : 'Mark Invoiced'}
                    </button>
                  </div>
                );
              })
            )}
          </div>
        ) : null}

        <div className="coaching-recent-panel" style={{ marginTop: 12 }}>
          <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
            Recent Coaching Sessions (Edit)
          </h3>
          {recentCoachingSessions.length === 0 ? (
            <div className="status">No coaching sessions logged yet.</div>
          ) : (
            recentCoachingSessions.map((session) => {
              const engagement = coachingEngagementById[String(session.engagement_id)];
              const sessionLabel =
                session.session_type === 'no_show_chargeable' ? 'chargeable no-show' : session.session_type;
              const invoiceLabel = session.invoiced_to_adapsys ? 'invoiced' : 'not invoiced';
              return (
                <div key={session.id} className="status coaching-recent-row">
                  <strong>{engagement?.name || 'Unknown coachee'}</strong> ({engagement?.client_org || 'Unknown client'}) ·
                  {` ${formatDateAu(session.session_date)} · ${sessionLabel} · ${invoiceLabel}`}
                  <button
                    type="button"
                    className="secondary coaching-row-action"
                    onClick={() => onStartEditCoachingSession(session)}
                  >
                    Edit Session
                  </button>
                </div>
              );
            })
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
                    <strong>{row.name}</strong> ({row.client_org}) — Coach: {row.coach_email} · Entitled {row.entitled}{' '}
                    · Completed {row.used} · Remaining {row.remaining}
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
          tripExpenseSummaries.map((row) => (
            <div className="card" key={row.tripId}>
              <div className="status">
                {row.trip?.name || 'Unknown Project'} · {row.trip?.client_name || 'Unknown Client'}/
                {row.trip?.program_name || 'Unknown Program'}
              </div>
              <div>
                <strong>{formatAud(row.totalAud)}</strong> total · Consultant{' '}
                {formatAud(row.consultantAud)} · Fi/Admin {formatAud(row.adminAud)}
              </div>
              <div className="status">
                {row.approvedCount} approved · {row.pendingCount} pending
              </div>
              <div className="status">
                {Object.entries(row.byCategory)
                  .sort((a, b) => b[1] - a[1])
                  .map(([category, amount]) => `${category}: ${formatAud(amount)}`)
                  .join(' | ')}
              </div>
            </div>
          ))
        )}
      </section>
      ) : null}

      {!isConsultantSession ? (
      <section className="card" style={sectionVisibilityStyle('expense-review')}>
        <h2>Automation Controls (Fi/Admin)</h2>
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
            Run CEO Sign-off Automation
          </button>
        </div>
      </section>
      ) : null}

      {!isConsultantSession ? (
      <section id="reports" className="card" style={sectionVisibilityStyle('reports')}>
        <h2>Reports Hub</h2>
        {!isConsultantSession ? (
          <>
            <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
              Branded Coaching Report
            </h3>
            <div className="grid">
              <div>
                <label>Report By</label>
                <select
                  value={coachingReportFilters.report_by}
                  onChange={(e) =>
                    setCoachingReportFilters((prev) => ({ ...prev, report_by: e.target.value }))
                  }
                >
                  <option value="coach">Coach</option>
                  <option value="coachee">Coachee</option>
                </select>
              </div>
              {coachingReportFilters.report_by === 'coach' ? (
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
            <div className="report-date-row" style={{ marginTop: 8 }}>
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
            <div className="report-action-row" style={{ marginTop: 12 }}>
              <button
                type="button"
                onClick={onPreviewCoachingReport}
                disabled={isPreviewingCoachingReport}
              >
                {isPreviewingCoachingReport ? 'Generating Preview...' : 'Preview Coaching Report'}
              </button>
              <button
                type="button"
                onClick={onDownloadCoachingReportPdf}
                disabled={isDownloadingCoachingReportPdf}
              >
                {isDownloadingCoachingReportPdf ? 'Preparing PDF...' : 'Download Coaching PDF'}
              </button>
            </div>
            {coachingReportStatus ? <div className="status" style={{ marginTop: 8 }}>{coachingReportStatus}</div> : null}
            {coachingReportPreviewHtml ? (
              <iframe
                title="Coaching Report Preview"
                srcDoc={coachingReportPreviewHtml}
                style={{ width: '100%', minHeight: 520, border: '1px solid #d6e3e3', marginTop: 12 }}
              />
            ) : null}
          </>
        ) : (
          <div className="status">Coaching report generation is available in Admin/Finance sessions.</div>
        )}

        <h3 style={{ margin: '16px 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
          Client Expense Report
        </h3>
        <div className="expense-report-controls" style={{ marginTop: 8 }}>
          <div className="expense-report-project">
            <label>Project</label>
            <select
              value={selectedReportTripId}
              onChange={(e) => {
                setSelectedReportTripId(e.target.value);
                setReportPreviewHtml('');
                setReportPreviewStatus('');
              }}
            >
              <option value="">Select project</option>
              {trips.map((trip) => (
                <option key={trip.id} value={trip.id}>
                  {trip.name} — {trip.client_name}/{trip.program_name}
                </option>
              ))}
            </select>
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
        <div className="report-action-row" style={{ marginTop: 12 }}>
          <button type="button" onClick={onPreviewExpensePack} disabled={isPreviewingExpensePack}>
            {isPreviewingExpensePack ? 'Generating Preview...' : 'Preview Client Report'}
          </button>
          <button type="button" onClick={onDownloadExpensePackPdf} disabled={isDownloadingExpensePackPdf}>
            {isDownloadingExpensePackPdf ? 'Preparing PDF...' : 'Download Client Report PDF'}
          </button>
        </div>
        {reportPreviewStatus ? <div className="status" style={{ marginTop: 8 }}>{reportPreviewStatus}</div> : null}
        {reportPreviewHtml ? (
          <iframe
            title="Expense Pack Preview"
            srcDoc={reportPreviewHtml}
            style={{ width: '100%', minHeight: 520, border: '1px solid #d6e3e3', marginTop: 12 }}
          />
        ) : null}
      </section>
      ) : null}

      {!isConsultantSession ? (
      <section id="expense-review" className="card" style={sectionVisibilityStyle('expense-review')}>
        <h2>Expense Review (Fi/CEO)</h2>
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
                  <option value="">Select project</option>
                  {trips.map((trip) => (
                    <option key={trip.id} value={trip.id}>
                      {trip.name} — {trip.client_name}/{trip.program_name}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => onMoveExpenseToProject(expense.id)}
                  disabled={movingExpenseId === String(expense.id)}
                >
                  {movingExpenseId === String(expense.id) ? 'Moving...' : 'Move Expense'}
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
            Use midpoint incidental values for now. You can update each country next week when final ATO amounts are confirmed.
          </div>
          {atoRates.map((rate) => {
            const key = String(rate.id);
            const draft = atoRateDraftById[key] || {};
            return (
              <div className="card" key={rate.id}>
                <div className="status"><strong>{rate.country}</strong></div>
                <div className="grid">
                  <div>
                    <label>Daily Rate (AUD)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={draft.daily_rate_aud ?? ''}
                      onChange={(e) =>
                        setAtoRateDraftById((prev) => ({
                          ...prev,
                          [key]: { ...prev[key], daily_rate_aud: e.target.value },
                        }))
                      }
                    />
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
                    <label>Breakfast %</label>
                    <input
                      type="number"
                      step="0.01"
                      value={draft.breakfast_pct ?? ''}
                      onChange={(e) =>
                        setAtoRateDraftById((prev) => ({
                          ...prev,
                          [key]: { ...prev[key], breakfast_pct: e.target.value },
                        }))
                      }
                    />
                  </div>
                  <div>
                    <label>Lunch %</label>
                    <input
                      type="number"
                      step="0.01"
                      value={draft.lunch_pct ?? ''}
                      onChange={(e) =>
                        setAtoRateDraftById((prev) => ({
                          ...prev,
                          [key]: { ...prev[key], lunch_pct: e.target.value },
                        }))
                      }
                    />
                  </div>
                  <div>
                    <label>Dinner %</label>
                    <input
                      type="number"
                      step="0.01"
                      value={draft.dinner_pct ?? ''}
                      onChange={(e) =>
                        setAtoRateDraftById((prev) => ({
                          ...prev,
                          [key]: { ...prev[key], dinner_pct: e.target.value },
                        }))
                      }
                    />
                  </div>
                  <div>
                    <label>Tax Year</label>
                    <input
                      value={draft.tax_year ?? ''}
                      onChange={(e) =>
                        setAtoRateDraftById((prev) => ({
                          ...prev,
                          [key]: { ...prev[key], tax_year: e.target.value },
                        }))
                      }
                    />
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
        <section id="admin-console" className="card" style={sectionVisibilityStyle('admin-console')}>
          <h2>Admin Console</h2>
          <div className="status" style={{ marginBottom: 10 }}>
            Full admin editor for projects, lookup files, and coaching data.
          </div>

          <h3 style={{ margin: '0 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
            Projects (All Editable Fields)
          </h3>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Lead Consultant</th>
                  <th>Assigned Consultants (comma list)</th>
                  <th>Client</th>
                  <th>Program</th>
                  <th>Country</th>
                  <th>City</th>
                  <th>Start</th>
                  <th>End</th>
                  <th>Depart</th>
                  <th>Return</th>
                  <th>Save</th>
                </tr>
              </thead>
              <tbody>
                {trips.map((trip) => {
                  const key = String(trip.id);
                  const draft = adminTripDraftById[key] || {};
                  return (
                    <tr key={trip.id}>
                      <td>
                        <input
                          value={draft.name ?? trip.name ?? ''}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'name', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          value={draft.consultant_email ?? trip.consultant_email ?? ''}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'consultant_email', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          value={draft.assigned_consultants ?? (trip.assigned_consultants || []).join(', ')}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'assigned_consultants', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          value={draft.client_name ?? trip.client_name ?? ''}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'client_name', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          value={draft.program_name ?? trip.program_name ?? ''}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'program_name', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          value={draft.destination_country ?? trip.destination_country ?? ''}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'destination_country', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          value={draft.destination_city ?? trip.destination_city ?? ''}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'destination_city', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          type="date"
                          value={draft.project_start_date ?? trip.project_start_date ?? ''}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'project_start_date', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          type="date"
                          value={draft.project_end_date ?? trip.project_end_date ?? ''}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'project_end_date', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          type="date"
                          value={draft.departure_date ?? trip.departure_date ?? ''}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'departure_date', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          type="date"
                          value={draft.return_date ?? trip.return_date ?? ''}
                          onChange={(e) => onAdminTripFieldChange(trip.id, 'return_date', e.target.value)}
                        />
                      </td>
                      <td>
                        <button
                          type="button"
                          onClick={() => onSaveAdminTrip(trip)}
                          disabled={savingAdminTripId === key}
                        >
                          {savingAdminTripId === key ? 'Saving...' : 'Save'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <h3 style={{ margin: '16px 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
            Lookup Files (Admin Editable)
          </h3>
          <div className="grid" style={{ marginBottom: 8 }}>
            <div>
              <label>Consultants JSON</label>
              <textarea
                rows={10}
                value={adminLookupDrafts.consultants}
                onChange={(e) =>
                  setAdminLookupDrafts((prev) => ({ ...prev, consultants: e.target.value }))
                }
              />
              <button
                type="button"
                onClick={() => onSaveAdminLookup('consultants')}
                disabled={savingAdminLookupKey === 'consultants'}
              >
                {savingAdminLookupKey === 'consultants' ? 'Saving...' : 'Save Consultants'}
              </button>
            </div>
            <div>
              <label>Coaches JSON</label>
              <textarea
                rows={10}
                value={adminLookupDrafts.coaches}
                onChange={(e) =>
                  setAdminLookupDrafts((prev) => ({ ...prev, coaches: e.target.value }))
                }
              />
              <button
                type="button"
                onClick={() => onSaveAdminLookup('coaches')}
                disabled={savingAdminLookupKey === 'coaches'}
              >
                {savingAdminLookupKey === 'coaches' ? 'Saving...' : 'Save Coaches'}
              </button>
            </div>
          </div>
          <div>
            <label>Client Programs JSON</label>
            <textarea
              rows={12}
              value={adminLookupDrafts.clientPrograms}
              onChange={(e) =>
                setAdminLookupDrafts((prev) => ({ ...prev, clientPrograms: e.target.value }))
              }
            />
            <button
              type="button"
              onClick={() => onSaveAdminLookup('clientPrograms')}
              disabled={savingAdminLookupKey === 'clientPrograms'}
            >
              {savingAdminLookupKey === 'clientPrograms' ? 'Saving...' : 'Save Client Programs'}
            </button>
          </div>

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
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
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
                  <th className="col-no-show">No Show</th>
                  <th className="col-rate">Rate</th>
                  <th>Save</th>
                </tr>
              </thead>
              <tbody>
                {filteredAdminEngagements.map((engagement) => {
                  const key = String(engagement.id);
                  const draft = adminEngagementDraftById[key] || {};
                  return (
                    <tr key={engagement.id}>
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
                      <td>
                        <button
                          type="button"
                          onClick={() => onSaveAdminEngagement(engagement)}
                          disabled={savingAdminEngagementId === key}
                        >
                          {savingAdminEngagementId === key ? 'Saving...' : 'Save'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <h3 style={{ margin: '16px 0 8px', color: 'var(--color-dark-teal)', fontSize: 15 }}>
            Coaching Sessions (All Fields)
          </h3>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Engagement</th>
                  <th>Outcome</th>
                  <th>Duration</th>
                  <th>Mode</th>
                  <th>Notes</th>
                  <th>Save</th>
                </tr>
              </thead>
              <tbody>
                {coachingSessions.map((session) => {
                  const key = String(session.id);
                  const draft = adminSessionDraftById[key] || {};
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
                              {engagement.name} — {engagement.client_org}
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
                              {option}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <input
                          type="number"
                          value={draft.duration_mins ?? session.duration_mins ?? 60}
                          onChange={(e) => onAdminSessionFieldChange(session.id, 'duration_mins', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          value={draft.delivery_mode ?? session.delivery_mode ?? 'video'}
                          onChange={(e) => onAdminSessionFieldChange(session.id, 'delivery_mode', e.target.value)}
                        />
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
        </section>
      ) : null}
    </div>
  );
}
