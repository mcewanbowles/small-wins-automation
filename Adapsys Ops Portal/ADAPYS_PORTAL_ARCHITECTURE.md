# Adapys Australia Pacific
## Ops Portal — Master Architecture Specification
### Single Source of Truth for All Windsurf Build Sessions

---

> **Drop this file into every Windsurf session:**
> `@ADAPYS_PORTAL_ARCHITECTURE.md`
>
> Reference supporting files as needed:
> `@ADAPYS_BRAND_STYLE_GUIDE.md`
> `@ADAPYS_OPS_PORTAL_BRIEF.md`
> `@ADAPYS_EXPENSE_APP_WINDSURF_BRIEF.md`
> `@ADAPYS_COMPLETE_DIGITAL_STRATEGY_BRIEF.md`

---

## What We Are Building

A single private web portal — **Adapys Ops Portal** — that replaces:
- Zoho Creator (coaching tracking — too restrictive, too expensive per seat)
- Manual expense spreadsheets and PDF assembly
- "Invoice when we get a chance" (revenue leakage)
- Cameron's Pacific network living only in his head
- Tender emails buried in noise

One URL. Five modules. Zero per-user licence costs for consultants.
Everything syncs to Zoho for the official record.

---

## The Five Modules

```
┌─────────────────────────────────────────────────────────┐
│              ADAPYS OPS PORTAL                          │
│         adapsysauspac.com                               │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ COACHING │ │ EXPENSE  │ │  TENDER  │ │    BD    │  │
│  │   HUB    │ │   HUB    │ │ TRIAGE   │ │   CRM    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              DASHBOARD (Fi + Collette)          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              ZOHO SYNC LAYER                    │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

| Module | Priority | Status | Brief File |
|--------|----------|--------|------------|
| Expense Hub | 1 — Build first | Not started | ADAPYS_EXPENSE_APP_WINDSURF_BRIEF.md |
| Coaching Hub | 2 | Not started | ADAPYS_OPS_PORTAL_BRIEF.md |
| Dashboard | 3 | Not started | This file |
| Tender Triage | 4 | Not started | ADAPYS_COMPLETE_DIGITAL_STRATEGY_BRIEF.md |
| BD CRM | 5 | Not started | ADAPYS_COMPLETE_DIGITAL_STRATEGY_BRIEF.md |

---

## Users & Access Model

### Internal Users (login with email + password)

| User | Role | Access |
|------|------|--------|
| Fi McEwan | Admin | Full access to all modules |
| Collette | Finance | Coaching invoicing + expense approvals only |

### External Users (magic link — no login, no licence)

| User | Access Via | Can Do |
|------|-----------|--------|
| Cameron | Permanent magic link | Log sessions + submit expenses |
| Any consultant/associate | Permanent magic link | Log sessions + submit expenses |
| Coachee | Single-use notification link | Confirm session (optional) |

### Magic Link Architecture
```
Each consultant has ONE permanent token
URL: adapsysauspac.com/portal/[uuid-token]

On opening their link, consultant sees:
├── Their active coaching engagements
├── Their active expense reports / trips
└── Links to log sessions or submit expenses

Coachee links:
- Generated per notification
- Single purpose (confirm session or view program status)
- Expire 7 days after sending
- No access to financial data
```

---

## User Journeys

### Journey 1: Fi Sets Up A New Coaching Engagement
```
Fi logs in → Coaching Hub → New Engagement
→ Enters client, coachee, sessions, rate, coach
→ System generates magic link for coach
→ Welcome email sent to coach automatically
→ Engagement appears on Fi's dashboard
→ Collette sees it in invoice queue
```

### Journey 2: Cameron Logs A Session (from PNG on his phone)
```
Cameron opens his magic link (saved in phone)
→ Sees all active engagements
→ Taps DFAT — Sarah Thompson
→ Taps Log Session
→ Selects: Session took place / No show / Cancelled
→ Enters date, duration, mode
→ Taps Submit
→ Fi gets dashboard update
→ Collette gets invoice alert (if per-session billing)
→ If penultimate session → alerts fire automatically
```

### Journey 3: Fi Creates A Trip + Cameron Submits Expenses
```
Fi logs in → Expense Hub → New Trip
→ Enters destination, dates, consultant, flights
→ System calculates per diem (ATO rate for PNG)
→ Magic link sent to Cameron

Cameron opens link from his phone in Port Moresby
→ Sees trip details and per diem entitlement
→ Taps Add Expense
→ Takes photo of taxi receipt
→ Enters amount in PGK → converts to AUD automatically
→ Ticks dinner provided on Tuesday
→ Per diem adjusts automatically
→ Taps Submit

Fi gets notification → opens review screen
→ Sees all pre-booked + consultant expenses
→ Approves
→ Taps Generate PDF
→ Branded PDF with receipt images downloaded
→ Uploaded to Zoho Books manually (Phase 1)
   or pushed automatically (Phase 2)
```

### Journey 4: Collette Invoices A Client
```
Collette logs in → sees Invoice Dashboard
→ DFAT engagement shows 3 sessions completed, uninvoiced
→ Taps Generate Invoice Summary
→ Sees: 3 sessions × $450 = $1,350
→ Plus: travel expenses from linked trip = $842
→ Total invoice: $2,192
→ Taps Mark as Invoiced → enters date sent
→ When payment received → Mark as Paid
→ Revenue dashboard updates
```

### Journey 5: Tender Arrives, Fi Triages It
```
Fi receives Australian Tenders email
→ Opens Tender Triage module
→ Pastes full email text
→ Taps Triage
→ Claude scores each tender against Adapys profile
→ Sees: 1 PURSUE, 1 MONITOR, 2 IGNORE
→ PURSUE tender added to pipeline
→ 3 duplicates suppressed (seen before)
→ Fi shares relevant tender with Cameron
```

---

## Complete Database Schema

```sql
-- ═══════════════════════════════
-- USERS & ACCESS
-- ═══════════════════════════════

users
  id              uuid PRIMARY KEY
  name            text
  email           text UNIQUE
  role            text  -- 'admin' | 'finance' | 'consultant'
  magic_link_token uuid UNIQUE  -- for consultant access
  active          boolean
  created_at      timestamptz

-- ═══════════════════════════════
-- COACHING MODULE
-- ═══════════════════════════════

engagements
  id                  uuid PRIMARY KEY
  name                text
  client_org          text
  billing_contact     text
  billing_email       text
  billing_to          text  -- 'client_org' | 'managing_contractor' | 'coachee'
  po_number           text
  managing_contractor text  -- e.g. Palladium, Coffey
  coach_id            uuid REFERENCES users(id)
  total_sessions      integer
  session_rate        decimal(10,2)
  no_show_rate        decimal(10,2)
  contract_value      decimal(10,2)  -- auto-calculated
  contract_start      date
  contract_end        date
  invoice_frequency   text  -- 'per_session' | 'per_block' | 'end_of_contract'
  block_size          integer  -- if per_block, how many sessions per invoice
  status              text  -- 'active' | 'complete' | 'cancelled' | 'on_hold'
  notes               text
  coachee_alerts      boolean  -- send penultimate alert to coachee?
  created_by          uuid REFERENCES users(id)
  created_at          timestamptz
  updated_at          timestamptz

coachees
  id              uuid PRIMARY KEY
  engagement_id   uuid REFERENCES engagements(id)
  name            text
  email           text
  role            text
  organisation    text
  notes           text
  created_at      timestamptz

sessions
  id              uuid PRIMARY KEY
  engagement_id   uuid REFERENCES engagements(id)
  coachee_id      uuid REFERENCES coachees(id)
  date            date
  type            text  -- 'completed' | 'no_show_chargeable' |
                        --  'cancelled_no_charge' | 'postponed'
  session_number  integer  -- e.g. 4 (of 6)
  duration_mins   integer
  delivery_mode   text  -- 'video' | 'in_person' | 'phone'
  notes           text  -- internal only
  chargeable      boolean  -- default true except cancelled_no_charge
  invoiced        boolean  -- has this session been invoiced?
  invoice_id      uuid REFERENCES invoices(id)
  logged_by       uuid REFERENCES users(id)
  logged_at       timestamptz
  created_at      timestamptz

invoices
  id              uuid PRIMARY KEY
  engagement_id   uuid REFERENCES engagements(id)
  session_ids     uuid[]  -- array of session ids on this invoice
  trip_ids        uuid[]  -- array of trip ids on this invoice (combined)
  amount          decimal(10,2)
  status          text  -- 'pending' | 'sent' | 'paid' | 'overdue' | 'disputed'
  sent_date       date
  due_date        date
  paid_date       date
  reference       text  -- invoice number
  notes           text
  created_by      uuid REFERENCES users(id)
  created_at      timestamptz

alerts_log
  id              uuid PRIMARY KEY
  type            text  -- 'penultimate' | 'fifty_percent' | 'no_show' |
                        --  'overdue_invoice' | 'contract_end'
  engagement_id   uuid REFERENCES engagements(id)
  sent_to         text  -- email addresses
  sent_at         timestamptz
  dismissed       boolean

-- ═══════════════════════════════
-- EXPENSE MODULE
-- ═══════════════════════════════

trips
  id                    uuid PRIMARY KEY
  name                  text
  consultant_id         uuid REFERENCES users(id)
  linked_engagement_id  uuid REFERENCES engagements(id)  -- optional link
  client_org            text
  destination_country   text
  destination_city      text
  departure_date        date
  return_date           date
  nights                integer  -- auto-calculated
  per_diem_rate_daily   decimal(10,2)  -- from ATO rate table
  per_diem_total        decimal(10,2)  -- auto-calculated
  per_diem_adjusted     decimal(10,2)  -- after meal deductions
  status                text  -- 'draft' | 'active' | 'submitted' |
                               --  'approved' | 'pdf_generated'
  magic_link_token      uuid UNIQUE
  notes_to_consultant   text
  pdf_url               text  -- generated PDF location
  created_by            uuid REFERENCES users(id)
  created_at            timestamptz
  submitted_at          timestamptz
  approved_at           timestamptz
  approved_by           uuid REFERENCES users(id)

expenses
  id                uuid PRIMARY KEY
  trip_id           uuid REFERENCES trips(id)
  added_by          text  -- 'fi' | 'consultant'
  date              date
  category          text  -- 'flights' | 'accommodation' | 'taxi_transfer' |
                           --  'meals' | 'parking' | 'internet_phone' |
                           --  'visa_entry' | 'equipment' | 'other'
  description       text
  amount_local      decimal(10,2)
  currency_local    text  -- 'AUD' | 'PGK' | 'FJD' | 'SBD' etc
  exchange_rate     decimal(10,6)  -- locked at time of entry
  amount_aud        decimal(10,2)  -- converted
  receipt_url       text  -- full size in Supabase Storage
  receipt_thumb_url text  -- compressed thumbnail
  approved          boolean
  notes             text
  created_at        timestamptz

meal_declarations
  id          uuid PRIMARY KEY
  trip_id     uuid REFERENCES trips(id)
  date        date
  breakfast   boolean  -- was breakfast provided by client?
  lunch       boolean
  dinner      boolean
  deduction   decimal(10,2)  -- auto-calculated from ATO proportions
  created_at  timestamptz

ato_rates
  id              uuid PRIMARY KEY
  country         text  -- 'Australia' | 'Papua New Guinea' | etc
  city_tier       text  -- for domestic: 'tier1' | 'tier2' | 'other'
  daily_rate_aud  decimal(10,2)
  breakfast_pct   decimal(5,2)  -- % of daily rate
  lunch_pct       decimal(5,2)
  dinner_pct      decimal(5,2)
  tax_year        text  -- '2025-26'
  ato_reference   text  -- e.g. 'TD 2025/18'
  active          boolean
  updated_at      timestamptz

-- ═══════════════════════════════
-- TENDER MODULE
-- ═══════════════════════════════

tenders
  id              uuid PRIMARY KEY
  title           text
  issuer          text
  location        text
  closing_date    date
  days_remaining  integer  -- calculated
  status          text  -- current | future | closed
  description     text
  source          text  -- 'australian_tenders' | 'austender' | 'dfat' | 'manual'
  fit_score       integer  -- 1-10 from Claude
  recommendation  text  -- 'PURSUE' | 'MONITOR' | 'IGNORE'
  fit_reasons     text[]
  opportunity_angle text
  red_flags       text[]
  pipeline_stage  text  -- 'identified' | 'assessing' | 'writing' |
                         --  'submitted' | 'won' | 'lost' | 'withdrawn'
  assigned_to     uuid REFERENCES users(id)
  duplicate_hash  text UNIQUE  -- for deduplication
  strategic_value text         -- BD strategist note
  go_no_go_score  integer      -- 0-5 criteria met
  draft_url       text         -- proposal draft location
  win_probability integer      -- percentage estimate
  first_seen      timestamptz
  last_seen       timestamptz
  suppressed      boolean  -- duplicate suppression
  notes           text
  created_at      timestamptz

consultant_bd_profile
  id                    uuid PRIMARY KEY
  consultant_id         uuid REFERENCES users(id)
  expertise_tags        text[]
  pacific_countries     text[]
  notify_threshold      integer  -- minimum fit score to notify
  bd_active             boolean
  opportunities_flagged integer
  opportunities_led     integer
  opportunities_won     integer
  created_at            timestamptz
  updated_at            timestamptz

content_bank
  id           uuid PRIMARY KEY
  category     text  -- company | methodology | personnel | case_study | standard_clause
  subcategory  text
  title        text
  content      text
  word_count   integer
  last_updated timestamptz
  updated_by   uuid REFERENCES users(id)
  active       boolean

-- ═══════════════════════════════
-- BD / RELATIONSHIP MODULE
-- ═══════════════════════════════

contacts
  id                  uuid PRIMARY KEY
  name                text
  organisation        text
  role                text
  relationship_type   text  -- 'managing_contractor' | 'government' |
                             --  'pacific_partner' | 'dfat' | 'associate' | 'other'
  countries           text[]  -- countries they work in
  programs_together   text
  relationship_owner  uuid REFERENCES users(id)
  warmth              text  -- 'hot' | 'warm' | 'cool' | 'cold' | 'dormant'
  last_contact_date   date
  next_touchpoint     date
  what_they_know      text  -- what they know Adapys can do
  capability_gaps     text  -- what they DON'T know Adapys can do
  personal_notes      text
  active              boolean
  created_at          timestamptz
  updated_at          timestamptz

touchpoint_log
  id            uuid PRIMARY KEY
  contact_id    uuid REFERENCES contacts(id)
  date          date
  type          text  -- 'email' | 'call' | 'meeting' | 'event'
  notes         text
  logged_by     uuid REFERENCES users(id)
  created_at    timestamptz
```

---

## API Architecture

### Internal API Routes (FastAPI)

```
AUTH
POST   /auth/login
POST   /auth/refresh
GET    /auth/magic-link/[token]     ← validates consultant access

COACHING
GET    /engagements                  ← Fi: all engagements
POST   /engagements                  ← Fi: create new
GET    /engagements/[id]
PUT    /engagements/[id]
GET    /engagements/[id]/sessions
POST   /sessions                     ← coach: log session
PUT    /sessions/[id]
GET    /portal/[token]/engagements   ← consultant magic link view

EXPENSES
GET    /trips                        ← Fi: all trips
POST   /trips                        ← Fi: create trip
GET    /trips/[id]
PUT    /trips/[id]
POST   /trips/[id]/approve           ← Fi: approve and trigger PDF
GET    /portal/[token]/trips         ← consultant magic link view
POST   /expenses                     ← consultant: add expense
POST   /expenses/[id]/receipt        ← consultant: upload receipt
DELETE /expenses/[id]
POST   /meal-declarations            ← consultant: declare provided meals
GET    /trips/[id]/pdf               ← download generated PDF

INVOICING
GET    /invoices                     ← Collette: invoice dashboard
POST   /invoices                     ← create invoice
PUT    /invoices/[id]/sent
PUT    /invoices/[id]/paid

TENDERS
GET    /tenders                      ← Fi: tender list
POST   /tenders/triage               ← Claude scoring endpoint
GET    /tenders/[id]
PUT    /tenders/[id]/pipeline
DELETE /tenders/[id]

CONTACTS
GET    /contacts
POST   /contacts
PUT    /contacts/[id]
POST   /contacts/[id]/touchpoint
POST   /contacts/[id]/draft-message  ← Claude drafting endpoint

DASHBOARD
GET    /dashboard/summary            ← Fi morning dashboard
GET    /dashboard/revenue            ← revenue snapshot

ATO RATES
GET    /ato-rates
PUT    /ato-rates/[id]               ← Fi: annual update

ZOHO SYNC
POST   /sync/zoho/session/[id]
POST   /sync/zoho/expense/[trip_id]
POST   /sync/zoho/invoice/[id]
```

### External API Calls

```
Claude API
  POST https://api.anthropic.com/v1/messages
  Used for:
  - Tender scoring (/tenders/triage)
  - Contact message drafting (/contacts/[id]/draft-message)
  Model: claude-sonnet-4-20250514
  Max tokens: 1000

Supabase
  Database: PostgreSQL via Supabase client
  Storage: Receipt images and generated PDFs
  Auth: JWT tokens

Resend (email)
  Send: Magic links, session alerts, invoice alerts,
        penultimate notifications, expense confirmations

Zoho Books API (Phase 2)
  POST /books/v3/expenses
  POST /books/v3/invoices
  Auth: OAuth2

Exchange Rates (Phase 1: manual entry)
  Phase 2: Open Exchange Rates API or similar
  Rates locked at time of entry for audit trail
```

---

## File & Folder Structure

```
adapys-portal/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── dashboard/
│   │   │   ├── coaching/
│   │   │   │   ├── EngagementList.jsx
│   │   │   │   ├── EngagementDetail.jsx
│   │   │   │   ├── NewEngagement.jsx
│   │   │   │   └── SessionLog.jsx
│   │   │   ├── expenses/
│   │   │   │   ├── TripList.jsx
│   │   │   │   ├── TripDetail.jsx
│   │   │   │   ├── NewTrip.jsx
│   │   │   │   └── TripReview.jsx
│   │   │   ├── portal/
│   │   │   │   ├── ConsultantPortal.jsx    ← magic link landing
│   │   │   │   ├── SessionLogger.jsx       ← mobile session logging
│   │   │   │   └── ExpenseSubmitter.jsx    ← mobile expense submission
│   │   │   ├── invoicing/
│   │   │   │   └── InvoiceDashboard.jsx
│   │   │   ├── tenders/
│   │   │   │   ├── TenderTriage.jsx
│   │   │   │   └── TenderPipeline.jsx
│   │   │   └── contacts/
│   │   │       ├── ContactList.jsx
│   │   │       └── ContactDetail.jsx
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   │   ├── Button.jsx
│   │   │   │   ├── Card.jsx
│   │   │   │   ├── Badge.jsx
│   │   │   │   ├── ProgressBar.jsx
│   │   │   │   └── Alert.jsx
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   ├── Header.jsx
│   │   │   │   └── MobileNav.jsx
│   │   │   └── shared/
│   │   │       ├── ReceiptUploader.jsx
│   │   │       ├── PerDiemCalculator.jsx
│   │   │       └── SessionTypeSelector.jsx
│   │   ├── styles/
│   │   │   └── globals.css              ← Adapys CSS variables + Poppins
│   │   ├── lib/
│   │   │   ├── api.js                   ← API client
│   │   │   ├── supabase.js
│   │   │   └── utils.js
│   │   └── App.jsx
│   └── package.json
│
├── backend/
│   ├── main.py                          ← FastAPI app
│   ├── routers/
│   │   ├── auth.py
│   │   ├── engagements.py
│   │   ├── sessions.py
│   │   ├── trips.py
│   │   ├── expenses.py
│   │   ├── invoices.py
│   │   ├── tenders.py
│   │   ├── contacts.py
│   │   ├── dashboard.py
│   │   └── sync.py
│   ├── services/
│   │   ├── claude_service.py            ← All Claude API calls
│   │   ├── pdf_service.py               ← PDF generation
│   │   ├── email_service.py             ← Resend integration
│   │   ├── per_diem_service.py          ← ATO calculations
│   │   ├── alert_service.py             ← Penultimate/invoice alerts
│   │   └── zoho_service.py              ← Zoho sync
│   ├── models/
│   │   └── schemas.py                   ← Pydantic models
│   ├── db/
│   │   └── supabase_client.py
│   └── requirements.txt
│
├── docs/
│   ├── ADAPYS_PORTAL_ARCHITECTURE.md    ← this file
│   ├── ADAPYS_BRAND_STYLE_GUIDE.md
│   ├── ADAPYS_OPS_PORTAL_BRIEF.md
│   ├── ADAPYS_EXPENSE_APP_WINDSURF_BRIEF.md
│   └── ADAPYS_COMPLETE_DIGITAL_STRATEGY_BRIEF.md
│
└── README.md
```

---

## Technology Stack — Final Decisions

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React + Tailwind CSS | Fast to build, mobile-friendly, Windsurf excels at it |
| Backend | Python FastAPI | Clean, fast, great for Claude API integration |
| Database | Supabase (PostgreSQL) | Cloud, accessible from Pacific, real-time, storage included |
| File Storage | Supabase Storage | Receipt images and PDFs, same platform |
| Auth | Supabase Auth + JWT | Simple, secure, supports magic links |
| AI | Claude API (Anthropic) | Tender scoring + message drafting |
| PDF | WeasyPrint (Python) | Server-side branded PDF generation |
| Email | Resend | Simple, reliable, great API |
| Hosting | Railway | Simple deployment, auto-deploy from GitHub |
| Domain | adapsysauspac.com | Primary production domain |
| Font | Poppins (Google Fonts) | Adapys brand typeface |

---

## Environment Variables Required

```bash
# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=

# Claude API
ANTHROPIC_API_KEY=

# Email
RESEND_API_KEY=

# App
SECRET_KEY=                    # JWT signing
APP_URL=https://adapsysauspac.com
ADMIN_EMAIL=fi@adapsysgroup.com
FINANCE_EMAIL=collette@adapsysgroup.com

# Zoho (Phase 2)
ZOHO_CLIENT_ID=
ZOHO_CLIENT_SECRET=
ZOHO_REFRESH_TOKEN=
ZOHO_ORG_ID=
```

---

## Build Roadmap — Session by Session

### SESSION 1: Foundation + Expense Hub Core
**Time estimate: 3-4 hours**
```
- Project scaffold (React + FastAPI + Supabase)
- Adapys brand CSS variables and Poppins font
- Authentication (Fi + Collette login)
- Magic link validation endpoint
- Trip creation form (Fi)
- ATO rate table with key Pacific destinations
- Per diem calculation engine
- Basic consultant portal view (mobile)
```
**Deliverable:** Fi can create a trip. Per diem calculates correctly.

---

### SESSION 2: Expense Submission (Mobile)
**Time estimate: 2-3 hours**
```
- Consultant mobile expense submission screen
- Receipt photo capture + upload to Supabase Storage
- Currency conversion (local → AUD, rate locked)
- Meal declaration checkboxes with per diem adjustment
- Running total display
- Submit flow + email notification to Fi
```
**Deliverable:** Cameron can submit expenses from his phone.

---

### SESSION 3: Expense Review + PDF
**Time estimate: 2-3 hours**
```
- Fi review and approval screen
- Pre-booked vs consultant expenses view
- Approve flow
- WeasyPrint PDF generation (branded, receipts embedded)
- Download PDF
- ATO rate citation on PDF
- Declaration section
```
**Deliverable:** Fi approves → branded PDF generated automatically.

---

### SESSION 4: Coaching Hub Core
**Time estimate: 3-4 hours**
```
- Engagement creation form (Fi)
- Coachee management
- Magic link generation + welcome email to coach
- Coach portal — engagement list (mobile)
- Session logging screen (mobile)
- Session types: completed / no-show / cancelled / postponed
- Session counter and progress bar
- No-show immediate alert to Fi
```
**Deliverable:** Cameron can log sessions from his phone.

---

### SESSION 5: Alert System
**Time estimate: 2-3 hours**
```
- Penultimate session detection (triggers on logging)
- Alert emails: coach + coachee + Fi + Collette
- 50% consumption alert to Fi
- Contract end approaching alert
- Overdue invoice detection
- Alert log (so same alert isn't sent twice)
```
**Deliverable:** Nobody ever misses a penultimate session again.

---

### SESSION 6: Collette Invoice Dashboard
**Time estimate: 2-3 hours**
```
- Invoice dashboard for Collette
- Sessions ready to invoice (grouped by engagement)
- Combined coaching + expense invoice view
- Mark as invoiced / paid
- Overdue tracking
- Invoice summary PDF
- Revenue totals
```
**Deliverable:** Collette can invoice in 10 minutes instead of never.

---

### SESSION 7: Fi Dashboard
**Time estimate: 2 hours**
```
- Morning dashboard for Fi
- Revenue snapshot (uninvoiced / outstanding / paid)
- Needs attention alerts
- Active engagements summary
- Expense reports pending
- Tender pipeline summary
- Network health (if BD module built)
```
**Deliverable:** Fi opens one screen every morning and knows exactly
what needs attention.

---

### SESSION 8: Tender Triage
**Time estimate: 2-3 hours**
```
- Tender triage input (paste email text)
- Claude API scoring against Adapys profile
- Deduplication engine
- PURSUE / MONITOR / IGNORE display
- Tender pipeline kanban
- Suppression log
```
**Deliverable:** No relevant tender ever missed in noise again.

---

### SESSION 9: BD / Relationship CRM
**Time estimate: 3-4 hours**
```
- Contact database with all fields
- Warmth tracking and visual indicators
- Days since last contact counter
- AI touchpoint message drafting (Claude API)
- Managing contractor intelligence view
- Network health score
```
**Deliverable:** Cameron's Pacific network stops being a single
point of failure.

---

### SESSION 10: Zoho Sync + Polish
**Time estimate: 2-3 hours**
```
- Zoho sync export (Phase 1: formatted CSV/data for manual import)
- Mobile testing and refinements
- Email template polish
- Edge cases (multi-destination trips, extended contracts)
- Rate table admin screen for Fi
- README and deployment docs
```
**Deliverable:** Production-ready. Everything syncs to Zoho.

---

## What To Say To Windsurf Each Session

### Session 1 Start:
```
@ADAPYS_PORTAL_ARCHITECTURE.md
@ADAPYS_BRAND_STYLE_GUIDE.md
@ADAPYS_EXPENSE_APP_WINDSURF_BRIEF.md

Build Session 1 of the Adapys Ops Portal.
Scaffold the full project structure as specified in the
architecture doc. Build the foundation: React + FastAPI +
Supabase, Adapys brand styles, authentication, magic link
system, trip creation form, and per diem calculation engine.
Use Poppins font and Adapys brand colours throughout.
```

### Subsequent Sessions:
```
@ADAPYS_PORTAL_ARCHITECTURE.md
@ADAPYS_BRAND_STYLE_GUIDE.md

Sessions 1-3 are complete. Now build Session 4:
Coaching Hub core. Reference the coaching module
specification in the architecture doc.
```

---

## Revenue Impact Summary

| Problem Solved | Conservative Annual Value |
|---------------|--------------------------|
| No-show sessions now charged consistently | $10,800 |
| Invoicing on time instead of "when we get a chance" | $15,000+ |
| Missed contract renewals caught | $10,800 |
| Tender opportunities no longer missed | $80,000+ (one extra win) |
| Fi time recovered (40-60 hrs/year on expenses alone) | $6,000+ |
| **Total conservative impact** | **$120,000+/year** |

Build cost: ~20 hours of Windsurf sessions.

---

## Immediate Pre-Build Checklist

Before starting Session 1, have these ready:

- [ ] Supabase account created (free tier fine to start)
- [ ] Anthropic API key (for Claude scoring + message drafting)
- [ ] Resend account created (free tier: 3,000 emails/month)
- [ ] Railway account for hosting
- [ ] Adapys logo file (PNG with transparent background)
- [ ] ATO per diem rates verified against current Tax Determination
- [ ] Cameron's top 5 Pacific contact details (seeds the CRM)
- [ ] 3 past proposals uploaded (seeds the tender content bank)

---

*Adapys Australia Pacific*
*Ops Portal — Master Architecture v1.0*
*March 2026*
*Confidential — Internal Use Only*
