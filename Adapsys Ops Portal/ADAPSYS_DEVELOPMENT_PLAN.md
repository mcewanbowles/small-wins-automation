# Adapsys Australia Pacific
## Portal Development Plan — Complete Technical Reference
### Windsurf Master Build Document
### Version 2.0 — Updated March 2026

---

> **HOW TO USE THIS FILE**
> Drop this into every Windsurf session:
> `@ADAPSYS_DEVELOPMENT_PLAN.md`
>
> This is the single source of truth for the entire portal build.
> It supersedes all previous spec documents.
> All new features, amendments and additions are captured here.
>
> Supporting files (still valid for detail):
> `@ADAPSYS_BRAND_STYLE_GUIDE.md`
> `@ADAPSYS_EXPENSE_APP_WINDSURF_BRIEF.md`
> `@ADAPSYS_BD_GROWTH_STRATEGY_AND_TENDER_MODULE.md`
> `@ADAPSYS_MODULE_11_WORKSHOP_REFERENCE_BOOK.md`
> `@ADAPSYS_MODULE_12_WAYS_OF_WORKING.md`

---

## Platform Overview

**Product Name:** Adapsys Ops Portal
**Domain:** To be confirmed (domain purchase in progress)
**Purpose:** Unified operations, coaching, BD, contracts,
             and participant learning platform for
             Adapsys Australia Pacific
**Users:** Admin team, consultants/coaches, participants
**Access model:** Login for admin | Magic links for consultants
                  | Time-limited links for participants

---

## Technology Stack

```
Frontend:     React + Tailwind CSS
Backend:      Python FastAPI
Database:     Supabase (PostgreSQL + Storage)
Auth:         Supabase Auth + JWT + Magic links
Email:        Resend
PDF:          WeasyPrint (server-side)
Contracts:    DocuSign (Phase 1 AU-compliant) + built-in e-signature later if required
File backup:  Google Drive API (auto-sync)
AI:           Claude API (claude-sonnet-4-20250514)
Automation:   n8n (external, connects to portal via webhooks)
Hosting:      Railway
Font:         Poppins (Google Fonts)
```

---

## Brand Standards

Apply to every screen without exception.

```css
:root {
  --color-teal: #00b8b8;
  --color-dark-teal: #006379;
  --color-dark-grey: #595959;
  --color-hot-pink: #ef2b97;
  --color-deep-pink: #c20c5b;
  --color-burgundy: #740839;
  --color-mid-grey: #999999;
  --color-light-grey: #b7b7b7;
  --color-near-white: #f3f3f3;
}

font-family: 'Poppins', sans-serif;
/* Weights: 300 (light), 400 (regular), 500 (medium), 700 (bold) */
```

---

## Module Status Overview

```
MODULE 1:  Expense Hub              ✅ IN PROGRESS
MODULE 2:  Coaching Hub             ✅ IN PROGRESS
MODULE 3:  Tender Intelligence      ✅ IN PROGRESS
MODULE 4:  Dashboard                ✅ IN PROGRESS
MODULE 5:  Contract Management      🔲 NOT STARTED — spec below
MODULE 6:  Consultant Profiles      🔲 NOT STARTED — spec below
MODULE 7:  BD / Relationship CRM    🔲 NOT STARTED
MODULE 8:  Participant Portal       🔲 NOT STARTED — Phase 2
MODULE 9:  Adaptive Leadership Tool 🔲 NOT STARTED — Phase 3
MODULE 10: Google Drive Sync        🔲 NOT STARTED — integrate throughout
MODULE 11: Workshop + Ref Books     🔲 NOT STARTED — Phase 3
MODULE 12: Ways of Working (SOP)    🔲 NOT STARTED — Phase 3
```

---

## User Roles & Access — Full Picture

```
ROLE 1: Admin (Fi)
  Full access to all modules
  Manage all consultants, contracts, engagements
  Approve expenses, generate PDFs
  Manage participant programs
  Login: email + password

ROLE 2: Finance (Collette)
  Coaching invoice dashboard
  Expense report approval
  Contract status visibility
  Outstanding items tracking
  Login: email + password

ROLE 3: Consultant / Coach
  Own profile page (editable)
  Their coaching engagements
  Session logging
  Expense submission
  Contract viewing and signing
  Access: permanent magic link
  Link control: admin can revoke/delete any consultant link at any time

ROLE 4: Participant
  Program resources (readings, videos)
  Program chat (limited to cohort)
  Adaptive leadership tool (when built)
  Access: time-limited magic link
  Expires: configurable per program (e.g. 6 months)

ROLE 5: Coachee
  Session confirmation (optional)
  Access: single-use notification link
  No access to financial or contract data
```

---

# MODULE 1: EXPENSE HUB
## Status: ✅ IN PROGRESS

Full specification in `@ADAPSYS_EXPENSE_APP_WINDSURF_BRIEF.md`

### Summary of Core Features
- Fi creates trip with destination, dates, consultant
- ATO per diem auto-calculated by country/destination
- Consultant submits receipts via magic link on mobile
- Receipt photo capture (camera or upload)
- Currency conversion locked at date of entry
- Meal declaration checkboxes reduce per diem per ATO rules
- Fi reviews and approves
- Branded PDF generated with embedded receipts
- Linked to coaching engagements for combined invoicing

### Outstanding Items to Complete
- [ ] WeasyPrint PDF generation with Adapsys branding
- [ ] Google Drive auto-backup of approved PDFs
- [ ] Zoho Books export (Phase 1: formatted CSV)
- [ ] Multi-destination trip support
- [ ] ATO rate table admin screen for Fi to update annually

---

# MODULE 2: COACHING HUB
## Status: ✅ IN PROGRESS

Full specification in `@ADAPSYS_OPS_PORTAL_BRIEF.md`

### Summary of Core Features
- Fi creates engagements (client, coachee, sessions, rate)
- Magic link sent to coach automatically on creation
- Coach logs sessions: completed / no-show / cancelled
- Penultimate session alerts to coach + coachee + Fi + Collette
- 50% consumption alert to Fi
- No-show immediately flagged to Fi
- Collette invoice dashboard with sessions ready to invoice
- Combined coaching + expense invoice view
- Mark invoices as sent / paid / overdue

### Outstanding Items to Complete
- [ ] Collette invoice PDF generation
- [ ] Invoice overdue detection and escalation
- [ ] Google Drive backup of session records
- [ ] Zoho CRM sync (Phase 1: export CSV)
- [ ] Group coaching support (multiple coachees per engagement)

---

# MODULE 3: TENDER INTELLIGENCE
## Status: ✅ IN PROGRESS

Full specification in `@ADAPSYS_BD_GROWTH_STRATEGY_AND_TENDER_MODULE.md`

### Summary of Core Features
- Fi pastes tender email → Claude scores each tender
- Scores against Adapsys profile (1-10, PURSUE/MONITOR/IGNORE)
- Hidden deadline extraction (EOI, registration, briefing dates)
- Deduplication by reference number hash
- Consultant tender feed on magic link (personalised by expertise)
- One-tap interest buttons (I'll Lead / Watching / Pass)
- Immediate Fi notification on consultant interest
- Tender pipeline kanban
- BD contribution tracker per consultant

### Outstanding Items to Complete
- [ ] Consultant BD profile fields (expertise tags, countries)
- [ ] Personalised feed filtering by consultant profile
- [ ] n8n webhook endpoint for automated tender ingestion
- [ ] Proposal assembly engine (content bank + Claude draft)
- [ ] Source health monitoring display
- [ ] Win rate tracking over time

---

# MODULE 4: DASHBOARD
## Status: ✅ IN PROGRESS

### Summary of Core Features
- Fi morning dashboard
- Revenue snapshot (uninvoiced / outstanding / paid)
- Needs attention alerts
- Active engagements summary
- Expense reports pending
- Tender pipeline summary

### Outstanding Items to Complete (detailed below)
- [ ] Outstanding contracts tracker (NEW — see Module 5)
- [ ] Outstanding expense reports tracker (NEW)
- [ ] Consultant compliance status (NEW)
- [ ] Editable alert parameters (NEW)

### NEW: Admin Alert System (add to dashboard)

Fi needs to see at a glance everything that is
overdue or outstanding across the whole business.
All thresholds must be editable by Fi.

```
OUTSTANDING ITEMS — Admin View

⚠️ CONTRACTS AWAITING SIGNATURE (2)
  Cameron McDonald — PNG Leadership Program
  Sent: 20 Mar | Waiting 8 days [Send Reminder]

  Sarah Chen — APS Coaching Program
  Sent: 15 Mar | Waiting 13 days ⚠️ [Send Reminder]

⚠️ EXPENSE REPORTS OVERDUE (1)
  Cameron — Fiji Trip (ended 15 Mar)
  Due: 22 Mar | 13 days overdue [Send Reminder]

⚠️ INVOICES OVERDUE (2)
  DFAT — $2,700 — 45 days [Chase]
  Palladium — $1,350 — 31 days [Chase]

⚠️ SESSIONS NOT LOGGED (1)
  Sarah Chen — 2 sessions unlogged (>7 days)
  [Send Reminder]
```

### Editable Alert Parameters (Fi Admin Settings)

```
ALERT THRESHOLDS (Fi can edit)
Contract signature overdue after:    [7]  days
Expense report due after trip end:   [7]  days
Expense report overdue after:        [14] days
Invoice chase after:                 [30] days
Session logging overdue after:       [7]  days
Penultimate session alert at:        [1]  session before last
50% consumption alert:               [on/off toggle]
```

---

# MODULE 5: CONTRACT MANAGEMENT
## Status: 🔲 NOT STARTED

### The Problem
Every time Adapsys wins work, Fi must:
- Write a new subcontract for the consultant
- Update dates, project name, rates, special conditions
- Email it manually
- Chase signatures manually
- File the signed copy manually

This takes hours and gets lost in email.

### What to Build

#### 5A — Contract Template System

Adapsys has one master subcontractor agreement template.
The variables change each time:

```
EDITABLE FIELDS PER CONTRACT:
  Consultant name
  Consultant ABN
  Project name
  Client organisation
  Contract start date
  Contract end date
  Daily rate (AUD)
  Estimated days
  Total estimated value (auto-calculated)
  Deliverables description (free text)
  Special conditions (free text, optional)
  Travel entitlements (yes/no + per diem reference)
  Reporting requirements (free text)
  Payment terms (dropdown: 14 days / 30 days / on milestone)
  Confidentiality clause (standard / enhanced toggle)
  IP ownership clause (standard / project-specific toggle)
```

#### 5B — Contract Generation Flow (Fi)

```
Fi navigates to: Contracts → New Contract

Step 1: Select consultant (dropdown from consultant list)
        Auto-populates: name, ABN, email, bank details

Step 2: Select or create engagement
        Auto-populates: project name, client, dates
        (or enter manually if not linked to coaching engagement)

Step 3: Fill variable fields
        Rate, days, deliverables, special conditions

Step 4: Preview contract
        Full formatted contract displayed before sending
        Fi can edit any field inline

Step 5: Send for signature
        [Send Contract to Consultant]
        → Branded email sent to consultant
        → Contract status: AWAITING SIGNATURE
        → Dashboard alert created
        → Reminder scheduled (based on Fi's threshold setting)
```

#### 5C — Contract Signing (Consultant)

Consultant receives email:

```
Subject: Contract for signature — PNG Leadership Program

Hi Cameron,

Please review and sign your contract for the
PNG Leadership Program with Adapsys Australia Pacific.

Contract details:
  Project: PNG Leadership Program
  Period: 15 April – 30 June 2026
  Rate: $1,200/day
  Estimated days: 15
  Estimated value: $18,000

[Review & Sign Contract →]
```

Consultant opens link → sees full contract → scrolls to bottom:

```
┌─────────────────────────────────────────────┐
│ CONSULTANT DECLARATION                       │
│                                             │
│ I have read and agree to the terms of this  │
│ contract.                                   │
│                                             │
│ Full name: [Cameron McDonald          ]     │
│ Date:      [25 March 2026] (auto)           │
│                                             │
│ Signature: [Draw or type signature    ]     │
│            [Draw] [Type] [Upload image]     │
│                                             │
│ [✅ Sign and Submit Contract]               │
└─────────────────────────────────────────────┘
```

On signature:
- Timestamp recorded with IP address
- Signed PDF generated with signature embedded
- Copy emailed to consultant automatically
- Copy saved to Google Drive automatically
  → `/Adapsys/Contracts/[Year]/[Consultant]/[Project].pdf`
- Fi notified: "Cameron has signed PNG Leadership contract"
- Dashboard alert cleared

#### 5D — Contract Database

```sql
contracts
  id                  uuid PRIMARY KEY
  engagement_id       uuid REFERENCES engagements(id)  -- optional
  consultant_id       uuid REFERENCES users(id)
  project_name        text
  client_org          text
  start_date          date
  end_date            date
  daily_rate          decimal(10,2)
  estimated_days      integer
  estimated_value     decimal(10,2)  -- auto-calculated
  deliverables        text
  special_conditions  text
  travel_entitlements boolean
  payment_terms       text
  confidentiality     text  -- 'standard' | 'enhanced'
  ip_ownership        text  -- 'standard' | 'project_specific'
  status              text  -- 'draft' | 'sent' | 'signed' |
                            --  'expired' | 'cancelled'
  sent_date           date
  signed_date         date
  signature_data      text  -- base64 signature image
  signed_pdf_url      text  -- Supabase Storage URL
  drive_backup_url    text  -- Google Drive URL
  reminder_sent       boolean
  created_by          uuid REFERENCES users(id)
  created_at          timestamptz
  updated_at          timestamptz
```

#### 5E — Contract History View

For each consultant, Fi can see:
```
CAMERON McDONALD — CONTRACT HISTORY

Current:
  PNG Leadership Program | Apr–Jun 2026 | $18,000
  Status: ✅ SIGNED 25 Mar 2026 [View PDF]

Previous:
  Fiji Capacity Building | Jan–Mar 2026 | $14,400
  Status: ✅ SIGNED 05 Jan 2026 [View PDF]

  Solomon Islands Program | Oct–Dec 2025 | $9,600
  Status: ✅ SIGNED 01 Oct 2025 [View PDF]
```

---

# MODULE 6: CONSULTANT PROFILES
## Status: 🔲 NOT STARTED

### The Problem
Consultant CVs and experience records:
- Live in email attachments
- Are out of date the moment they're sent
- Have to be manually assembled for each tender
- Don't reflect the full breadth of capability

### What to Build

#### 6A — Consultant Profile Page (Self-Managed)

Each consultant has a profile page they own and update.
Accessible from their magic link portal.

```
MY PROFILE — Cameron McDonald

[Profile Photo]  ← upload / change
[Upload Photo]

PERSONAL DETAILS (editable)
Full name:       Cameron McDonald
Title:           Principal Consultant
Email:           cameron@adapsysgroup.com
Phone:           +61 xxx xxx xxx
Location:        Gold Coast, QLD / Pacific region
ABN:             [                    ]
Languages:       English, [+ add]

PROFESSIONAL SUMMARY (editable, 300 words max)
[Free text — appears on tender CVs]

EXPERTISE AREAS (tag selector)
☑ Adaptive Leadership      ☑ Executive Coaching
☑ Pacific Development      ☑ Capacity Building
☑ Public Sector Reform     ☑ Organisational Development
☑ Facilitation             ☐ M&E
☐ Gender & Social Inclusion [+ add custom tag]

PACIFIC EXPERIENCE (countries worked in)
☑ Fiji    ☑ Samoa    ☑ PNG    ☑ Solomon Islands
☑ Vanuatu ☑ Noumea   ☐ Tonga  ☑ Timor-Leste
[+ add country]
```

#### 6B — CV Sections (Multiple CV Types)

Consultants maintain multiple tailored CV versions:

```
MY CVs

[+ Add New CV]

┌─────────────────────────────────────────┐
│ 📄 Coaching CV                          │
│ Last updated: 15 Mar 2026               │
│ Used in: 3 tenders                      │
│ [Edit] [Preview] [Download PDF]         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 📄 Pacific Development CV               │
│ Last updated: 02 Feb 2026               │
│ Used in: 5 tenders                      │
│ [Edit] [Preview] [Download PDF]         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 📄 APS Capability CV                    │
│ Last updated: 10 Jan 2026               │
│ Used in: 2 tenders                      │
│ [Edit] [Preview] [Download PDF]         │
└─────────────────────────────────────────┘
```

Each CV contains sections:

```
CV SECTIONS (drag to reorder)
├── Professional Summary
├── Core Competencies
├── Employment History
│   └── [Add position] — organisation, role, dates, description
├── Key Projects / Assignments
│   └── [Add project] — name, client, country, dates, outcomes
├── Education & Qualifications
│   └── [Add qualification]
├── Professional Memberships
└── Referees (2-3, with permission toggle)
```

#### 6C — Tender CV Integration

When Fi is assembling a tender response, she can:

```
INSERT PERSONNEL CVs

Select consultant: [Cameron McDonald      ▼]
Select CV type:    [Pacific Development CV ▼]
Max words:         [400                    ]

[Generate Tailored CV →]

Claude trims and tailors the CV to:
- The specified word count
- The specific tender context
- Highlighting most relevant experience
- Consistent Adapsys formatting

[Insert into proposal] [Download standalone PDF]
```

#### 6D — Profile Database

```sql
consultant_profiles
  id                  uuid PRIMARY KEY
  user_id             uuid REFERENCES users(id)
  photo_url           text
  title               text
  phone               text
  location            text
  abn                 text
  languages           text[]
  summary             text
  expertise_tags      text[]
  pacific_countries   text[]
  bank_name           text  -- for expense reimbursement
  bank_bsb            text
  bank_account        text
  emergency_contact   text
  updated_at          timestamptz

consultant_cvs
  id              uuid PRIMARY KEY
  consultant_id   uuid REFERENCES users(id)
  cv_type         text  -- 'coaching' | 'pacific' | 'aps' | 'medical' | custom
  cv_name         text  -- display name
  content         jsonb -- structured sections
  pdf_url         text  -- generated PDF cache
  times_used      integer
  last_updated    timestamptz
  updated_by      uuid  -- consultant updates their own

cv_sections
  id              uuid PRIMARY KEY
  cv_id           uuid REFERENCES consultant_cvs(id)
  section_type    text  -- 'summary' | 'employment' | 'project' |
                        --  'education' | 'membership' | 'referee'
  display_order   integer
  content         jsonb  -- flexible per section type
  created_at      timestamptz
```

#### 6E — Google Drive Backup

All CVs and profile data automatically backed up:
```
/Adapsys/Consultants/
  Cameron McDonald/
    ├── Profile/
    │   └── cameron-profile-2026.pdf
    ├── CVs/
    │   ├── cameron-cv-coaching-2026.pdf
    │   ├── cameron-cv-pacific-2026.pdf
    │   └── cameron-cv-aps-2026.pdf
    └── Contracts/
        └── [see Module 5]
```

---

# MODULE 7: BD / RELATIONSHIP CRM
## Status: 🔲 NOT STARTED

Brief in `@ADAPSYS_BD_GROWTH_STRATEGY_AND_TENDER_MODULE.md`

### Summary
- Contact database (Cameron's Pacific network)
- Warmth tracking (Hot/Warm/Cool/Cold/Dormant)
- Days since last contact counter
- AI touchpoint message drafting (Claude)
- Managing contractor intelligence view
- Network health score on dashboard

### Build after Module 5 and 6 are complete.

---

# MODULE 8: PARTICIPANT PORTAL
## Status: 🔲 NOT STARTED — PHASE 2

### The Problem
Coaching and leadership programs have participants who need:
- Access to program resources during their program
- A private space for their cohort
- Materials that expire when the program ends
- No access to any financial or consultant data

### What to Build

#### 8A — Program Setup (Fi creates)

```
NEW PROGRAM

Program name:     [APS Leadership Cohort — Q2 2026  ]
Program type:     [Leadership Program ▼]
Start date:       [01 April 2026]
End date:         [30 June 2026]
Access expires:   [30 days after end date] (editable)
Lead consultant:  [Cameron McDonald ▼]
Participants:     [+ Add participant] ← name + email

CONTENT
[+ Add resource]
  Type: [Reading ▼] [Video Link ▼] [Document ▼]
  Title: [                              ]
  URL or upload: [                      ]
  Visible from: [Program start ▼]
  Visible to: [All participants ▼] [Individual ▼]

CHAT
Enable cohort chat: [✅ Yes / ○ No]
Chat moderated by:  [Cameron McDonald ▼]
```

#### 8B — Participant Experience (Magic Link)

Participant receives email:

```
Subject: Welcome to your Adapsys Leadership Program

Hi Sarah,

Welcome to the APS Leadership Cohort Q2 2026.

Your program runs from 1 April to 30 June 2026.
Use the link below to access your program portal —
readings, resources, and your cohort space.

[Access Your Program Portal →]

This link is personal to you. It expires 30 July 2026.
```

Participant portal (mobile-friendly):

```
┌─────────────────────────────────────────┐
│ [ADAPSYS LOGO]                          │
│ APS Leadership Cohort — Q2 2026         │
│ Hi Sarah 👋                             │
│                                         │
│ PROGRAM RESOURCES                       │
│                                         │
│ 📄 Week 1 — Adaptive Leadership Intro  │
│    Reading | Added 1 Apr               │
│    [Open]                               │
│                                         │
│ 🎥 Ron Heifetz — Leadership Without    │
│    Easy Answers                         │
│    Video | 45 mins | Added 1 Apr       │
│    [Watch]                              │
│                                         │
│ 📄 Week 2 — The Balcony and the        │
│    Dance Floor                          │
│    Reading | Available from 8 Apr      │
│    [Locked until 8 Apr]                │
│                                         │
│ COHORT DISCUSSION                       │
│                                         │
│ [View Group Chat →]                    │
│ 4 new messages since your last visit   │
│                                         │
│ YOUR PROGRAM                           │
│ Sessions: 2 of 6 completed             │
│ Next: 15 April with Cameron            │
└─────────────────────────────────────────┘
```

#### 8C — Cohort Chat

Deferred / out of scope for now.

Decision:
- Participant chat is cancelled for current and near-term phases.
- Reconsider only when a clear moderation model and governance policy are defined.

#### 8D — Program Database

```sql
programs
  id              uuid PRIMARY KEY
  name            text
  type            text  -- 'leadership' | 'coaching' | 'workshop'
  lead_consultant uuid REFERENCES users(id)
  start_date      date
  end_date        date
  access_expires  date  -- configurable days after end
  status          text  -- 'draft' | 'active' | 'completed'
  created_by      uuid REFERENCES users(id)
  created_at      timestamptz

program_participants
  id              uuid PRIMARY KEY
  program_id      uuid REFERENCES programs(id)
  name            text
  email           text
  organisation    text
  magic_link_token uuid UNIQUE
  last_accessed   timestamptz
  enrolled_at     timestamptz

program_resources
  id              uuid PRIMARY KEY
  program_id      uuid REFERENCES programs(id)
  type            text  -- 'reading' | 'video' | 'document' | 'link'
  title           text
  description     text
  url             text
  file_url        text  -- if uploaded
  available_from  date  -- drip release
  visible_to      text  -- 'all' | specific participant id
  display_order   integer
  created_at      timestamptz

-- program_messages table deferred with chat scope
```

---

# MODULE 9: ADAPTIVE LEADERSHIP TOOL
## Status: 🔲 NOT STARTED — PHASE 3

### Placeholder — Spec to come from Adapsys

This module will house Adapsys's proprietary adaptive
leadership diagnostic or assessment tool.

Requirements to be defined — likely includes:
- Self-assessment questionnaire
- Scored output / profile
- PDF report generation
- Integration with participant portal
- Accessible to both coachees and program participants
- Results stored against consultant engagement record

### Data structure to scaffold now:

```sql
al_assessments
  id              uuid PRIMARY KEY
  participant_id  text  -- program participant or coachee
  engagement_id   uuid  -- optional coaching link
  completed_at    timestamptz
  responses       jsonb  -- all question responses
  score_data      jsonb  -- calculated scores by dimension
  report_url      text  -- generated PDF
```

---

# MODULE 10: GOOGLE DRIVE SYNC
## Status: 🔲 INTEGRATE THROUGHOUT — PHASE 1 MANUAL, PHASE 2 AUTO

### Why Google Drive

Adapsys already uses Google Drive as its operational
file system. The portal should treat Drive as the
official record — not replace it.

### Sync Architecture

```
PORTAL ACTION              → DRIVE BACKUP
──────────────────────────────────────────
Expense report approved    → /Expenses/[Year]/[Consultant]/
Contract signed            → /Contracts/[Year]/[Consultant]/
CV updated                 → /Consultants/[Name]/CVs/
Session record created     → /Coaching/[Client]/Sessions/
Tender won                 → /Tenders/Won/[Year]/
Proposal submitted         → /Tenders/Submitted/[Year]/
```

### Phase 1 (Manual Export — Build Now)
- Every PDF has a "Save to Drive" button
- Fi clicks → file pushed to correct Drive folder via API
- Folder structure created automatically if not exists
- Confirmation shown: "Saved to Drive ✓"

### Phase 2 (Auto-Sync — After Core Build)
- All approvals trigger automatic Drive backup
- No manual step required
- Drive folder listed on every record in portal
- Changes in portal update Drive automatically

### Google Drive API Setup
```python
# Required scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]

# Folder structure constants
DRIVE_ROOT = 'Adapsys Portal'
DRIVE_FOLDERS = {
    'expenses':   'Expenses',
    'contracts':  'Contracts',
    'consultants': 'Consultants',
    'coaching':   'Coaching Records',
    'tenders':    'Tenders',
    'programs':   'Programs'
}
```

---

# MODULE 11: WORKSHOP MANAGEMENT + REFERENCE BOOK BUILDER
## Status: 🔲 NOT STARTED — PHASE 3

Full specification in `@ADAPSYS_MODULE_11_WORKSHOP_REFERENCE_BOOK.md`

### Summary of Core Features
- Workshop creation opens a trackable project with auto-generated project code
- Optional reference-book workflow with design deadline, print location, and quantity
- Facilitator selector pulls from consultant profiles (photo + bio auto-population)
- Consultant-facing reference book builder with reorderable page structure
- Eight page types (cover, facilitator bios, text, image+text, full image, activity, client logo, custom upload)
- Dashboard KPI for outstanding reference books with deadline escalation
- Fi submission flow with structured design-brief PDF generation
- Google Drive asset backup for submitted content + attachments

### Implementation Scope (first pass)
- [ ] Workshop schema + CRUD (workshops, workshop_facilitators)
- [ ] Reference book schema + CRUD (reference_books, book_pages)
- [ ] Workshop creation screen (admin/lead consultant)
- [ ] Reference book builder shell UI + page ordering
- [ ] Submit-to-Fi workflow + status transitions
- [ ] Design brief PDF endpoint (WeasyPrint)
- [ ] Print location intelligence + preferred printer settings

---

# MODULE 12: WAYS OF WORKING (KNOWLEDGE BASE + SOP)
## Status: 🔲 NOT STARTED — PHASE 3

Full specification in `@ADAPSYS_MODULE_12_WAYS_OF_WORKING.md`

### Summary of Core Features
- Consultant-facing SOP knowledge base in magic-link portal
- Fi admin content builder for SOP categories/pages (draft + publish)
- Structured content sections: intro, steps, checklist, warning, portal links, contacts
- Mark-as-read tracking per consultant and per policy page
- New starter onboarding checklist with completion tracker
- Policy update notifications and review-due reminders
- Search across SOP pages and recently updated feed

### Implementation Scope (first pass)
- [ ] SOP schema + CRUD (sop_categories, sop_pages)
- [ ] Read tracking + onboarding progress schema and endpoints
- [ ] Fi admin: category manager + SOP page builder
- [ ] Consultant portal tab: Ways of Working list + page render
- [ ] Mark-as-read action + Fi tracker view
- [ ] Onboarding checklist gate (first-login flow)
- [ ] Policy update email and review reminder widget

---

# ADMIN PORTAL — COMPLETE FEATURE LIST

## What Fi Sees on Login Every Morning

```
ADAPSYS OPS PORTAL
Good morning Fi 👋 — Friday 27 March 2026

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ ACTION REQUIRED (5 items)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 2 contracts awaiting signature (13 days, 8 days)
🔴 1 expense report overdue — Cameron, Fiji trip
🟡 2 invoices overdue — DFAT 45d, Palladium 31d
🟡 1 session unlogged — Sarah Chen, 7 days
🔵 3 tenders worth reviewing — 1 urgent (EOI 3 days)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 REVENUE THIS MONTH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Uninvoiced:     $9,900   [Invoice Now]
Outstanding:    $8,100
Paid:          $12,600
Forecast:       $6,750

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌏 ACTIVE THIS WEEK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Engagements:    12 active
Contracts:       4 active | 2 awaiting signature
Trips:           1 active (Cameron — PNG)
Programs:        2 participant programs running
Tenders:         3 in pipeline | $520k value
```

## Admin Navigation Structure

```
SIDEBAR NAVIGATION
├── 🏠 Dashboard (morning overview)
├── 🎯 Coaching Hub
│   ├── All Engagements
│   ├── New Engagement
│   ├── Session Log
│   └── Invoice Queue (Collette)
├── 🧾 Expense Hub
│   ├── All Trips
│   ├── New Trip
│   └── Pending Approval
├── 📋 Contracts
│   ├── All Contracts
│   ├── New Contract
│   ├── Awaiting Signature ← badge count
│   └── Contract Templates
├── 👥 Consultants
│   ├── All Consultants
│   ├── Profiles & CVs
│   └── Invite Consultant
├── 🔍 Tenders
│   ├── Triage New Tenders
│   ├── Pipeline
│   ├── Content Bank
│   └── BD Analytics
├── 🌏 BD / Relationships
│   ├── Contact Network
│   ├── Managing Contractors
│   └── Pacific Intelligence
├── 🎓 Programs (Phase 2)
│   ├── Active Programs
│   ├── New Program
│   └── Participants
└── ⚙️ Settings
    ├── Alert Thresholds
    ├── ATO Rate Table
    ├── Contract Templates
    ├── Email Templates
    └── Google Drive Sync
```

---

# BUILD SESSION PLAN — UPDATED

## PHASE 1: Core Operations (Current)

### Session 1-4: Expense Hub ✅ In progress
### Session 5-7: Coaching Hub ✅ In progress
### Session 8-9: Tender Intelligence ✅ In progress
### Session 10: Dashboard ✅ In progress

### Session 11: Contract Management (NEW — build next)
```
@ADAPSYS_DEVELOPMENT_PLAN.md

Build Module 5 — Contract Management.
Start with:
1. Contract database schema (section 5D)
2. New contract form for Fi with all editable fields
3. Contract preview screen
4. Send for signature flow
5. Consultant signing screen (magic link)
6. Signature capture (draw/type/upload)
7. Signed PDF generation
8. Fi notification on signature
9. Dashboard outstanding contracts widget
10. Google Drive save button for signed PDFs
```

### Session 12: Consultant Profiles (NEW)
```
@ADAPSYS_DEVELOPMENT_PLAN.md

Build Module 6 — Consultant Profiles.
Start with:
1. Profile database schema (section 6D)
2. Profile page on consultant magic link portal
3. Photo upload
4. Expertise tags and Pacific countries
5. CV builder (multiple CV types)
6. CV section editor (employment, projects, education)
7. CV PDF generation (Adapsys branded)
8. Fi view of all consultant profiles
9. Google Drive backup of CVs
```

### Session 13: Admin Polish + Alert System
```
@ADAPSYS_DEVELOPMENT_PLAN.md

Complete the admin dashboard alert system.
Build:
1. Outstanding contracts tracker with days counter
2. Overdue expense reports tracker
3. Overdue invoice tracker
4. Session logging overdue tracker
5. Editable alert thresholds in Settings
6. Send reminder buttons (trigger email via Resend)
7. Google Drive sync — manual export buttons throughout
```

## PHASE 2: Participant Portal

### Session 14-16: Participant Portal
```
@ADAPSYS_DEVELOPMENT_PLAN.md

Build Module 8 — Participant Portal.
Full spec in section 8A-8D of this document.
Start with program creation, then participant
magic link experience, then resources.
Exclude chat (deferred/cancelled).
```

### PHASE 1 EXIT GATE (Required before Phase 2)

All checks below must be green before Session 14 starts.

```
GO / NO-GO CHECKLIST

[ ] Module 5 contracts live with AU-compliant signing path (DocuSign)
[ ] Contract statuses + reminders visible on dashboard
[ ] Module 6 consultant profiles usable end-to-end
[ ] CV generation/download works for at least one CV type
[ ] Admin alert system operational (contracts/expenses/invoices/sessions)
[ ] Google Drive manual export buttons working in core flows
[ ] Backup/restore spot-check completed (local + Google webhook/Drive path)
[ ] UAT pass by Fi and Collette
```

## PHASE 3: Advanced Features

### Session 17: BD / Relationship CRM (Module 7)
### Session 18: Adaptive Leadership Tool (Module 9)
### Session 19: Workshop Management + Ref Book Core (Module 11)
### Session 20: Ways of Working + SOP Tracker (Module 12)
### Session 21: Google Drive Auto-Sync (Module 10)
### Session 22: n8n Integration + Zoho Sync

---

# WINDSURF SESSION PROMPT TEMPLATES

## Starting a new session:
```
@ADAPSYS_DEVELOPMENT_PLAN.md
@ADAPSYS_BRAND_STYLE_GUIDE.md

[Describe what to build from the plan]

Context:
- Adapsys Australia Pacific — boutique leadership consultancy
- Poppins font throughout, brand colours from style guide
- React + FastAPI + Supabase stack
- Magic links for consultants (no login required)
- Mobile-first for all consultant-facing screens
```

## Continuing an existing module:
```
@ADAPSYS_DEVELOPMENT_PLAN.md

Continue building [Module Name].
Current status: [describe what's working]
Next to build: [specific feature from plan]
Known issues: [anything to fix]
```

## Starting a new module:
```
@ADAPSYS_DEVELOPMENT_PLAN.md
@ADAPSYS_BRAND_STYLE_GUIDE.md

Begin Module [X] — [Module Name].
Full spec is in section [X] of the development plan.
Build in this order: [list from session plan above]
Connect to existing: [what it integrates with]
```

---

# ENVIRONMENT VARIABLES

```bash
# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=

# Claude API
ANTHROPIC_API_KEY=

# Email
RESEND_API_KEY=

# Google Drive
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=
GOOGLE_DRIVE_ROOT_FOLDER_ID=

# App
SECRET_KEY=
APP_URL=https://[domain-to-be-confirmed]
ADMIN_EMAIL=fi@adapsysgroup.com
FINANCE_EMAIL=collette@adapsysgroup.com

# n8n webhooks
N8N_TENDER_WEBHOOK=
N8N_RELATIONSHIP_WEBHOOK=
```

---

# WHAT THIS PLATFORM REPLACES

| Old Way | New Way |
|---------|---------|
| Zoho Creator (coaching) | Coaching Hub ✅ |
| Manual expense spreadsheets | Expense Hub ✅ |
| Tender emails unread | Tender Intelligence ✅ |
| Word doc contracts emailed | Contract Management 🔲 |
| CV in email attachments | Consultant Profiles 🔲 |
| Cameron's head | BD CRM 🔲 |
| Teachable / Canvas (LMS) | Participant Portal 🔲 |
| DocuSign subscription | Built-in e-signature 🔲 |
| Manual Drive filing | Auto Google Drive sync 🔲 |
| "Invoice when we get a chance" | Automated alerts ✅ |

---

*Adapsys Australia Pacific*
*Portal Development Plan v2.0*
*March 2026 — Internal Use Only*
*Update this document as modules are completed*
