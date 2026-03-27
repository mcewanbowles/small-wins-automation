import { useEffect, useMemo, useState } from 'react';
import {
  approveExpense,
  createExpense,
  createTrip,
  downloadExpensePackPdf,
  fetchExpensePackPreview,
  intakeEmailReceipt,
  listAtoRates,
  listClientPrograms,
  listConsultants,
  listExpenses,
  listTrips,
  runCeoSignoffAutomation,
  runReminderAutomation,
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

const CONSULTANT_CATEGORY_OPTIONS = ['taxi', 'dinner', 'per_diem', 'misc'];
const ADMIN_CATEGORY_OPTIONS = ['flights', 'uber', 'hotel', ...CONSULTANT_CATEGORY_OPTIONS];
const EMAIL_INTAKE_CATEGORIES = ['flights', 'uber', 'hotel'];

export default function App() {
  const [tripForm, setTripForm] = useState({
    name: '',
    consultant_email: '',
    assigned_consultants: [],
    client_name: '',
    program_name: '',
    project_start_date: '',
    project_end_date: '',
    destination_country: 'Papua New Guinea',
    destination_city: '',
    departure_date: '',
    return_date: '',
  });
  const [expenseForm, setExpenseForm] = useState({
    trip_id: '',
    submitted_by_role: 'consultant',
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
  });
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
  const [trips, setTrips] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [atoRates, setAtoRates] = useState([]);
  const [consultants, setConsultants] = useState([]);
  const [clientPrograms, setClientPrograms] = useState([]);
  const [status, setStatus] = useState('');
  const [automationDryRun, setAutomationDryRun] = useState(true);
  const [selectedReportTripId, setSelectedReportTripId] = useState('');
  const [reportPreviewHtml, setReportPreviewHtml] = useState('');

  const clientOptions = useMemo(
    () => [...new Set(clientPrograms.map((row) => row.client_name))],
    [clientPrograms]
  );

  const fiEmail = useMemo(() => {
    const fi = consultants.find((row) => row.email.toLowerCase().startsWith('fi@'));
    return fi?.email || '';
  }, [consultants]);

  const consultantEmailOptions = useMemo(
    () => consultants.map((row) => row.email),
    [consultants]
  );

  const allConsultantEmails = useMemo(
    () => consultants.map((row) => row.email),
    [consultants]
  );

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

  const computedPerDiem = useMemo(() => {
    const selectedRate = atoRates.find(
      (rate) => rate.country === tripForm.destination_country && rate.active
    );
    const rate = selectedRate?.daily_rate_aud || 0;
    const nights = nightsBetween(tripForm.departure_date, tripForm.return_date);
    return { rate, nights, total: rate * nights };
  }, [
    atoRates,
    tripForm.destination_country,
    tripForm.departure_date,
    tripForm.return_date,
  ]);

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
    return {
      totalAud,
      approvedCount,
      pendingCount,
      activeTrips: trips.length,
    };
  }, [expenses, tripExpenseSummaries, trips.length]);

  async function refresh() {
    try {
      const [tripData, expenseData, ratesData, consultantsData, clientProgramsData] = await Promise.all([
        listTrips(),
        listExpenses(),
        listAtoRates(),
        listConsultants(),
        listClientPrograms(),
      ]);
      setTrips(tripData);
      setExpenses(expenseData);
      setAtoRates(ratesData);
      setConsultants(consultantsData);
      setClientPrograms(clientProgramsData);
      if (!tripForm.destination_country && ratesData.length > 0) {
        setTripForm((prev) => ({ ...prev, destination_country: ratesData[0].country }));
      }
      if (!tripForm.consultant_email && consultantsData.length > 0) {
        setTripForm((prev) => ({
          ...prev,
          consultant_email: consultantsData[0].email,
          assigned_consultants: prev.assigned_consultants.length
            ? prev.assigned_consultants
            : consultantsData.map((consultant) => consultant.email),
        }));
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
        if (!next.submitted_by_email) {
          next.submitted_by_email = consultantsData[0]?.email || '';
        }
        return next;
      });
      setEmailIntakeForm((prev) => ({
        ...prev,
        trip_id: prev.trip_id || tripData[0]?.id || '',
      }));
      setSelectedReportTripId((prev) => prev || tripData[0]?.id || '');
    } catch (error) {
      setStatus(error.message);
    }
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
      setStatus(`CEO sign-off automation processed ${rows.length} trip(s).`);
    } catch (error) {
      setStatus(error.message);
    }
  }

  useEffect(() => {
    if (!categoryOptions.includes(expenseForm.category)) {
      setExpenseForm((prev) => ({ ...prev, category: categoryOptions[0] || '' }));
    }
  }, [categoryOptions, expenseForm.category]);

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
    refresh();
  }, []);

  async function onCreateTrip(event) {
    event.preventDefault();
    try {
      await createTrip(tripForm);
      setStatus('Trip created.');
      setTripForm((prev) => ({ ...prev, name: '', destination_city: '' }));
      await refresh();
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function onCreateExpense(event) {
    event.preventDefault();
    try {
      await createExpense({
        ...expenseForm,
        amount_local: Number(expenseForm.amount_local),
        exchange_rate: Number(expenseForm.exchange_rate),
        receipt_url: expenseForm.no_receipt ? null : expenseForm.receipt_url,
        receipt_thumb_url: expenseForm.no_receipt
          ? null
          : expenseForm.receipt_thumb_url || expenseForm.receipt_url,
        no_receipt_reason: expenseForm.no_receipt
          ? expenseForm.no_receipt_reason
          : null,
      });
      setStatus('Expense submitted.');
      setExpenseForm((prev) => ({
        ...prev,
        amount_local: '',
        receipt_url: '',
        receipt_thumb_url: '',
        no_receipt: false,
        no_receipt_reason: '',
        notes: '',
      }));
      await refresh();
    } catch (error) {
      setStatus(error.message);
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
      setStatus('Emailed receipt added to Fi draft queue.');
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
    if (!selectedReportTripId) {
      setStatus('Select a trip to preview the expense pack.');
      return;
    }
    try {
      const html = await fetchExpensePackPreview(selectedReportTripId);
      setReportPreviewHtml(html);
      setStatus('Expense pack preview generated.');
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function onDownloadExpensePackPdf() {
    if (!selectedReportTripId) {
      setStatus('Select a trip to generate the PDF pack.');
      return;
    }
    try {
      const blob = await downloadExpensePackPdf(selectedReportTripId);
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `adapsys-expense-pack-${selectedReportTripId}.pdf`;
      anchor.click();
      window.URL.revokeObjectURL(url);
      setStatus('Expense PDF download started.');
    } catch (error) {
      setStatus(error.message);
    }
  }

  return (
    <div className="container">
      <header className="header">
        <h1>Adapsys Expense Hub</h1>
        <div className="status">Premium mobile-first operating dashboard</div>
        <div className="kpi-grid">
          <div className="kpi-chip">
            <span className="kpi-label">Portfolio Total</span>
            <strong>{formatAud(dashboardMetrics.totalAud)}</strong>
          </div>
          <div className="kpi-chip">
            <span className="kpi-label">Approved</span>
            <strong>{dashboardMetrics.approvedCount}</strong>
          </div>
          <div className="kpi-chip">
            <span className="kpi-label">Pending</span>
            <strong>{dashboardMetrics.pendingCount}</strong>
          </div>
          <div className="kpi-chip">
            <span className="kpi-label">Active Trips</span>
            <strong>{dashboardMetrics.activeTrips}</strong>
          </div>
        </div>
      </header>

      <section className="card">
        <h2>Create Trip (Fi)</h2>
        <form onSubmit={onCreateTrip}>
          <label>Trip Name</label>
          <input
            value={tripForm.name}
            onChange={(e) => setTripForm({ ...tripForm, name: e.target.value })}
            required
          />

          <label>Consultant</label>
          <select
            value={tripForm.consultant_email}
            onChange={(e) =>
              setTripForm((prev) => ({
                ...prev,
                consultant_email: e.target.value,
                assigned_consultants: Array.from(
                  new Set([e.target.value, ...prev.assigned_consultants.filter(Boolean)])
                ),
              }))
            }
            required
          >
            <option value="">Select consultant</option>
            {consultants.map((consultant) => (
              <option key={consultant.email} value={consultant.email}>
                {consultant.name} ({consultant.email})
              </option>
            ))}
          </select>

          <label>Assigned Consultant Roster</label>
          <div className="grid" style={{ marginBottom: 8 }}>
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
              Keep Primary Only
            </button>
          </div>
          <div className="consultant-roster-list">
            {consultants.map((consultant) => {
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
                  {consultant.name} ({consultant.email})
                </label>
              );
            })}
          </div>
          <div className="status">
            Select everyone going to this project. Consultants in this roster receive reminders.
          </div>

          <label>Client</label>
          <select
            value={tripForm.client_name}
            onChange={(e) =>
              setTripForm({
                ...tripForm,
                client_name: e.target.value,
                program_name: '',
              })
            }
            required
          >
            <option value="">Select client</option>
            {clientOptions.map((clientName) => (
              <option key={clientName} value={clientName}>
                {clientName}
              </option>
            ))}
          </select>

          <label>Program</label>
          <select
            value={tripForm.program_name}
            onChange={(e) => setTripForm({ ...tripForm, program_name: e.target.value })}
            required
            disabled={!tripForm.client_name}
          >
            <option value="">Select program</option>
            {programOptions.map((programName) => (
              <option key={programName} value={programName}>
                {programName}
              </option>
            ))}
          </select>

          <div className="grid">
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
          </div>

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

          <label>City</label>
          <input
            value={tripForm.destination_city}
            onChange={(e) =>
              setTripForm({ ...tripForm, destination_city: e.target.value })
            }
            required
          />

          <div className="grid">
            <div>
              <label>Travel Start Date (project baseline)</label>
              <input
                type="date"
                value={tripForm.departure_date}
                onChange={(e) =>
                  setTripForm({ ...tripForm, departure_date: e.target.value })
                }
                required
              />
            </div>
            <div>
              <label>Travel End Date (project baseline)</label>
              <input
                type="date"
                value={tripForm.return_date}
                onChange={(e) =>
                  setTripForm({ ...tripForm, return_date: e.target.value })
                }
                required
              />
            </div>
          </div>

          <div className="status">
            Per diem preview: AUD {computedPerDiem.rate}/day x {computedPerDiem.nights} nights = AUD{' '}
            {computedPerDiem.total}
          </div>
          <div className="status">
            Tip: Use a broad shared travel window here. Individual consultant expenses can still be entered daily.
          </div>

          <button type="submit">Create Trip</button>
        </form>
      </section>

      <section className="card">
        <h2>Submit Expense (Consultant)</h2>
        <form onSubmit={onCreateExpense}>
          <label>Submitted By Role</label>
          <select
            value={expenseForm.submitted_by_role}
            onChange={(e) => {
              const role = e.target.value;
              setExpenseForm((prev) => ({
                ...prev,
                submitted_by_role: role,
                submitted_by_email:
                  role === 'consultant'
                    ? consultantEmailOptions[0] || ''
                    : fiEmail || consultantEmailOptions[0] || '',
              }));
            }}
          >
            <option value="consultant">Consultant</option>
            <option value="admin">Admin (Fi)</option>
            <option value="finance">Finance</option>
          </select>

          <label>Submitted By Email</label>
          <select
            value={expenseForm.submitted_by_email}
            onChange={(e) =>
              setExpenseForm({ ...expenseForm, submitted_by_email: e.target.value })
            }
            required
          >
            <option value="">Select submitter</option>
            {(expenseForm.submitted_by_role === 'consultant'
              ? consultantEmailOptions
              : [fiEmail || consultantEmailOptions[0] || '']
            )
              .filter(Boolean)
              .map((email) => (
                <option key={email} value={email}>
                  {email}
                </option>
              ))}
          </select>

          <label>Trip</label>
          <select
            value={expenseForm.trip_id}
            onChange={(e) => setExpenseForm({ ...expenseForm, trip_id: e.target.value })}
            required
          >
            <option value="">Select trip</option>
            {trips.map((trip) => (
              <option key={trip.id} value={trip.id}>
                {trip.name} — {trip.client_name}/{trip.program_name}
              </option>
            ))}
          </select>

          <label>Date</label>
          <input
            type="date"
            value={expenseForm.expense_date}
            onChange={(e) =>
              setExpenseForm({ ...expenseForm, expense_date: e.target.value })
            }
            required
          />

          <label>Category</label>
          <select
            value={expenseForm.category}
            onChange={(e) => setExpenseForm({ ...expenseForm, category: e.target.value })}
          >
            {categoryOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>

          <label>Amount (local)</label>
          <input
            type="number"
            step="0.01"
            value={expenseForm.amount_local}
            onChange={(e) => setExpenseForm({ ...expenseForm, amount_local: e.target.value })}
            required
          />

          <label>Currency</label>
          <select
            value={expenseForm.currency_local}
            onChange={(e) =>
              setExpenseForm({ ...expenseForm, currency_local: e.target.value })
            }
          >
            <option value="AUD">AUD</option>
            <option value="PGK">PGK</option>
            <option value="FJD">FJD</option>
            <option value="USD">USD</option>
          </select>

          <label>Exchange Rate to AUD</label>
          <input
            type="number"
            step="0.0001"
            value={expenseForm.exchange_rate}
            onChange={(e) => setExpenseForm({ ...expenseForm, exchange_rate: e.target.value })}
            required
          />

          <label>
            <input
              type="checkbox"
              checked={expenseForm.gst_applicable}
              onChange={(e) =>
                setExpenseForm({ ...expenseForm, gst_applicable: e.target.checked })
              }
            />{' '}
            GST applicable
          </label>

          <label>Receipt URL (temporary)</label>
          <input
            value={expenseForm.receipt_url}
            onChange={(e) => setExpenseForm({ ...expenseForm, receipt_url: e.target.value })}
            placeholder="Paste uploaded receipt URL"
            required={!expenseForm.no_receipt}
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

          <label>
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
            No receipt available
          </label>

          {expenseForm.no_receipt ? (
            <>
              <label>Reason for no receipt</label>
              <textarea
                value={expenseForm.no_receipt_reason}
                onChange={(e) =>
                  setExpenseForm({ ...expenseForm, no_receipt_reason: e.target.value })
                }
                placeholder="e.g. handwritten market/taxi note in remote location"
                rows={2}
                required
              />
            </>
          ) : null}

          <label>Notes</label>
          <textarea
            value={expenseForm.notes}
            onChange={(e) => setExpenseForm({ ...expenseForm, notes: e.target.value })}
            rows={3}
          />

          <button type="submit">Submit Expense</button>
        </form>
      </section>

      <section className="card">
        <h2>Email Receipt Intake (Fi only)</h2>
        <div className="status">Use for forwarded flights, Uber, and hotel receipts.</div>
        <form onSubmit={onIntakeEmailReceipt}>
          <label>Trip</label>
          <select
            value={emailIntakeForm.trip_id}
            onChange={(e) => setEmailIntakeForm({ ...emailIntakeForm, trip_id: e.target.value })}
            required
          >
            <option value="">Select trip</option>
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

          <label>Fi Notes</label>
          <textarea
            value={emailIntakeForm.notes}
            onChange={(e) => setEmailIntakeForm({ ...emailIntakeForm, notes: e.target.value })}
            rows={2}
          />

          <button type="submit">Add Emailed Receipt Draft</button>
        </form>
      </section>

      <section className="card">
        <h2>Live Data (Draft)</h2>
        <div className="status">Trips: {trips.length} | Expenses: {expenses.length}</div>
        <div className="status">{status}</div>
      </section>

      <section className="card">
        <h2>Program Expense Snapshot</h2>
        {tripExpenseSummaries.length === 0 ? (
          <div className="status">No grouped expense data yet.</div>
        ) : (
          tripExpenseSummaries.map((row) => (
            <div className="card" key={row.tripId}>
              <div className="status">
                {row.trip?.name || 'Unknown Trip'} · {row.trip?.client_name || 'Unknown Client'}/
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

      <section className="card">
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

      <section className="card">
        <h2>Branded Expense Pack</h2>
        <label>Trip</label>
        <select
          value={selectedReportTripId}
          onChange={(e) => setSelectedReportTripId(e.target.value)}
        >
          <option value="">Select trip</option>
          {trips.map((trip) => (
            <option key={trip.id} value={trip.id}>
              {trip.name} — {trip.client_name}/{trip.program_name}
            </option>
          ))}
        </select>
        <div className="grid" style={{ marginTop: 12 }}>
          <button type="button" onClick={onPreviewExpensePack}>
            Preview Branded Pack
          </button>
          <button type="button" onClick={onDownloadExpensePackPdf}>
            Download PDF Pack
          </button>
        </div>
        {reportPreviewHtml ? (
          <details style={{ marginTop: 12 }}>
            <summary>Open HTML Preview</summary>
            <iframe
              title="Expense Pack Preview"
              srcDoc={reportPreviewHtml}
              style={{ width: '100%', minHeight: 520, border: '1px solid #d6e3e3', marginTop: 8 }}
            />
          </details>
        ) : null}
      </section>

      <section className="card">
        <h2>Expense Review (Fi/CEO)</h2>
        {expenses.length === 0 ? (
          <div className="status">No expenses submitted yet.</div>
        ) : (
          expenses.map((expense) => (
            <div className="card" key={expense.id}>
              <div className="status">{expense.expense_date} · {expense.category}</div>
              <div>{formatAud(expense.amount_aud)} · {expense.status}</div>
              <div className="status">
                Submitted by: {expense.submitted_by_email} ({expense.submitted_by_role})
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
                <div className="status">No receipt reason: {expense.no_receipt_reason}</div>
              )}
              {expense.status !== 'approved' ? (
                <button type="button" onClick={() => onApproveExpense(expense.id)}>
                  Approve
                </button>
              ) : null}
            </div>
          ))
        )}
      </section>

      <section className="card">
        <h2>ATO Rates (Option 1: in-app fixed table)</h2>
        {atoRates.map((rate) => (
          <div className="status" key={rate.id}>
            {rate.country}: AUD {rate.daily_rate_aud}/day ({rate.tax_year})
          </div>
        ))}
      </section>
    </div>
  );
}
