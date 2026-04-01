# ListingLift — The Keyword & Listing Tool Built for Sellers Who Don't Have 500 Reviews Yet
## Windsurf Build Spec v2

---

## The problem this solves

Every TPT keyword tool on the market assumes you already have traction. They optimise for established sellers with hundreds of reviews and years of sales history.

New and growing sellers face a brutal catch-22:
- You can't rank without reviews and sales
- You can't get reviews and sales without ranking
- Every keyword tool shows you high-demand keywords dominated by sellers with 200–500+ reviews
- You compete, get buried, give up

**ListingLift solves this with one core filter no competitor has: "Winnable Right Now."**

Show sellers only the keywords where the top-ranking products have a similar review count to their own store. Zero-review store? Show gaps where page 1 products also have zero to five reviews. Twenty reviews? Show keywords where that's competitive.

---

## Target user

Primary: New and growing TPT sellers (0–50 reviews) who are struggling to break into search rankings.
Secondary: Established sellers optimising and expanding their store.
Also works for: Etsy digital product sellers, Amazon KDP authors, Creative Market sellers.

**Positioning line:** "The keyword tool built for sellers who don't have 500 reviews yet."

---

## The six core features

---

### Feature 1: Keyword Gap Finder (core)

User flow:
1. Select platform (TPT, Etsy, Amazon KDP, Creative Market, Gumroad)
2. Enter a seed topic (e.g. "social stories autism")
3. App queries in real time:
   - Google Autocomplete
   - Pinterest Autocomplete
   - Platform-specific search autocomplete
4. Returns ranked list of long-tail phrases with demand + supply scores
5. User can click any keyword to copy or send to Listing Generator

**Demand scoring — how searched is this?**
Score 1 point for each source the phrase appears in:
- Google Autocomplete = 1 point
- Pinterest Autocomplete = 1 point
- Platform search bar suggestion = 1 point
- Score 3/3 = High demand | 2/3 = Medium | 1/3 = Low

**Supply scoring — how crowded is it?**
Search the exact phrase on the platform, count results:
- 0–50 results = Wide open
- 51–200 results = Winnable
- 200+ results = Saturated

**Gap verdict (combined):**
- High demand + Wide open = GOLD — make this now
- High demand + Winnable = SILVER — worth targeting
- Any + Saturated = CROWDED — avoid unless exceptional product

**Output table format:**
| Keyword phrase | Demand | Supply | Top review count | Verdict |
|---|---|---|---|---|
| social stories autism secondary | High | 12 products | avg 3 reviews | GOLD |
| AAC core word activities | High | 8 products | avg 0 reviews | GOLD |
| visual schedule autism adults | Medium | 23 products | avg 7 reviews | SILVER |
| social stories teenagers | High | 340 products | avg 180 reviews | CROWDED |

Sort: GOLD first, then SILVER, then CROWDED.
Filter toggle: "Show GOLD only" — most common use case, make it the default view.

---

### Feature 2: Winnable Right Now Filter (hero differentiator — no competitor has this)

This is the feature that makes ListingLift unique.

On every keyword result, show:
- Average review count of the top 5 products ranking for that keyword
- Lowest review count on page 1

User sets their "My store level":
- New store (0–5 reviews)
- Growing (6–25 reviews)
- Established (26–100 reviews)
- Authority (100+ reviews)

"Winnable Right Now" filter then hides any keyword where the average page 1 review count is significantly higher than the user's store level.

Result: A new seller with zero reviews only sees keywords they can actually compete for today.

**This is the Publisher Rocket moment for TPT.** The thing that makes sellers say "where has this been my whole life."

---

### Feature 3: Niche Finder — "What should I make?"

Discovery mode — for when the seller doesn't have a product yet and wants to find their next opportunity.

User selects:
- Platform
- Broad category (SPED, ELA, Math, Science, Social Studies, Art, TPT Seller Tools, etc.)
- Optional: Grade band (Early Childhood, Primary, Upper Primary, Secondary, Adult)

App returns:
- Top 10 trending gap opportunities in that category right now
- Each shows: keyword phrase, demand score, supply count, avg competitor reviews
- "This week's best gaps in Secondary SPED" — updated regularly via scheduled scraping

This is the niche finder. Not "optimise what you have" but "here's what to make next."

---

### Feature 4: Seasonal Launch Planner

TPT sales are heavily seasonal. Sellers who plan ahead dominate; sellers who react too late miss the window.

Show a 12-month calendar view with:
- When each seasonal topic starts trending (search demand rises)
- Optimal product upload date (6–8 weeks before peak to allow ranking time)
- Peak sales window
- Examples per category

Example data:
| Topic | Demand starts rising | Upload by | Peak sales |
|---|---|---|---|
| Back to school | Late June | July 1 | Aug 1–15 |
| Halloween | Late September | Sep 15 | Oct 1–25 |
| Christmas | Early November | Nov 1 | Dec 1–15 |
| Valentine's Day | Early January | Jan 5 | Feb 1–12 |
| End of year | Late April | Apr 15 | May 15–Jun 15 |

User can filter by their niche. Clicking any season shows the best low-competition keyword gaps for that season right now.

**Why this matters:** Most sellers upload Halloween resources in October. The sellers who rank are the ones who uploaded in September.

---

### Feature 5: Competitor Reverse Lookup

Paste a competitor's TPT product URL (or Etsy listing URL).

App extracts and analyses:
- Every keyword phrase their title is targeting
- Tags they are using
- First 180 characters of their description (the TPT snippet)
- Price point
- Review count and rating
- How many products they have in this niche

Returns:
- The keyword strategy this listing is built around
- Gaps they are missing (keywords in the same niche they haven't targeted)
- Suggested alternative angle to differentiate your product

This is Helium 10 Cerebro, but for TPT. No competitor offers this properly.

---

### Feature 6: Listing Health Audit

Paste an existing product URL (or paste title + description + tags manually).

App scores the listing across:
- Title: keyword placement, character usage, specificity (0–25 points)
- Description: keyword in first 180 chars, scannability, length (0–25 points)
- Tags: relevance, variety, long-tail vs short-tail balance (0–25 points)
- Price: compared to top 5 competitors for the same keyword (0–25 points)

Returns:
- Total score out of 100
- Specific fixes ranked by impact ("Your title keyword is at position 7 — move it to position 1")
- One-click: "Rewrite this listing" → sends to Listing Generator with existing content pre-loaded

---

### Feature 7: Listing Generator (AI-powered)

User flow:
1. Paste product description (or it arrives pre-loaded from Audit or Gap Finder)
2. Select platform
3. Select niche + grade band + buyer type
4. Click Generate

Claude API outputs:
- Optimised title (hard validated to platform character limits, keyword first)
- Full tag list (exact platform tag count, each within character limits)
- Description opener (first 180 characters — the TPT snippet — keyword-rich, benefit-led)
- Full description draft (scannable, bullet-pointed, educator tone)
- 5 long-tail keyword angles to target across related products
- 3 gap opportunities this product could also capture

One-click copy for every section.

**Platform listing rules enforced:**
| Platform | Title limit | Tags | Tag limit | Notes |
|---|---|---|---|---|
| TPT | 80 chars | 20 tags | No limit | Keyword in first word |
| Etsy | 140 chars | 13 tags | 20 chars each | Phrase-based |
| Amazon KDP | 200 chars | 7 keyword fields | 50 chars each | Backend keywords |
| Creative Market | 100 chars | 15 tags | — | |
| Gumroad | No limit | None | — | SEO title + meta description |

Live character counter on title field. Hard stop + warning if over limit.
Live tag counter. Warning if under platform max (leaving tags unused = wasted SEO).

---

## The Gold Formula (core logic, used across all features)

**Gold = High demand + Low supply + Winnable review threshold**

A keyword is gold when:
1. Real buyers are searching for it (demand signal from 2–3 autocomplete sources)
2. Few products exist for it on the platform (supply count under 50)
3. The products that do rank have a similar or lower review count to the user's store (winnable)

All three must be true. High demand + saturated market = not gold. Low competition + nobody searching = not gold.

---

## Tech stack

### Frontend
- React (Vite)
- Tailwind CSS
- Single page app, tab navigation between features
- Mobile responsive (secondary priority, nice to have for MVP)

### Backend
- FastAPI (Python)
- Endpoints:
  - POST /api/keywords — seed + platform → keyword list with scores
  - POST /api/niche-gaps — category + platform → top gap opportunities
  - POST /api/competitor-lookup — product URL → keyword analysis
  - POST /api/audit — listing content → health score + fixes
  - POST /api/generate-listing — description + platform + niche → full listing
- Async scraping with 300–500ms delays between requests
- Redis cache: autocomplete results cached 24 hours, supply counts cached 6 hours

### Scraping sources
- Google Autocomplete: `https://suggestqueries.google.com/complete/search?client=firefox&q={query}`
- Pinterest: `https://www.pinterest.com/typeahead/?q={query}`
- TPT autocomplete: scrape TPT search bar suggestions
- TPT supply count: search TPT and parse result count
- Etsy autocomplete: `https://www.etsy.com/api/v3/ajax/bespoke/public/neu/specs/search_suggestions?query={query}`

### AI
- Claude API: claude-sonnet-4-20250514
- Used only for Listing Generator and Competitor Gap analysis
- Users supply their own Anthropic API key via .env (no shared key — zero ongoing AI cost to operator)
- Include clear setup instructions: "Get your free API key at console.anthropic.com"

### Auth + payments (post-MVP)
- Clerk or Supabase Auth
- Stripe subscriptions

**Pricing tiers:**
- Free: 5 keyword searches/day, 3 listing generations/day, TPT only, no Winnable filter
- Pro $19/month: unlimited, all platforms, Winnable filter, Niche Finder, Seasonal Planner, Competitor Lookup, Audit
- Lifetime $67 one-time: all Pro features forever

### Database (post-MVP)
- Users: id, email, plan, store_level (review count band), created_at
- SavedKeywords: id, user_id, platform, keyword, demand_score, supply_count, avg_competitor_reviews, verdict, created_at
- SavedListings: id, user_id, platform, title, tags, description, created_at
- AuditHistory: id, user_id, product_url, score, fixes_json, created_at

---

## UI structure

### Platform selector
Prominent tab bar at top of every feature:
`[ TPT ] [ Etsy ] [ Amazon KDP ] [ Creative Market ] [ Gumroad ]`
Drives all character limits, tag counts, and scraping sources.

### Main navigation
`[ Keyword Finder ] [ Niche Finder ] [ Seasonal Planner ] [ Competitor Lookup ] [ Listing Audit ] [ Listing Generator ]`

### My Store Level (persistent setting)
Visible in header or sidebar. User sets their current review count band once. Drives the Winnable filter across all features. Reminder to update it as store grows.

### Keyword results table
Sortable columns: Keyword | Demand | Supply | Avg Reviews on P1 | Verdict
Default sort: GOLD first
Filter toggle: "Winnable for my store" ON by default
Export to CSV button

---

## Brand

- Use EasyPrep / PackReady visual identity
- Same teal colour palette
- Same logo family
- Position as a companion product: "From the makers of PackReady"
- Name: ListingLift (working title — confirm before launch)

---

## MVP scope (build this first — everything else is v2)

MVP = TPT only, no auth, no database, stateless single session:

1. Keyword Gap Finder — Google Autocomplete only as demand source, TPT supply count
2. Winnable Right Now filter — user enters their review count manually each session
3. Listing Generator — Claude API, user supplies own API key via .env
4. Basic Listing Audit — title + tags + description paste, score out of 100

Deploy to Vercel. Package as local web app for Gumroad launch (buyer runs locally with their own API key).

**Add in order after MVP:**
1. Pinterest + TPT autocomplete as additional demand sources
2. Niche Finder
3. Competitor Reverse Lookup
4. Seasonal Planner
5. User accounts + saved history (Supabase)
6. Stripe payments
7. Additional platforms (Etsy, KDP)

---

## Environment variables
```
ANTHROPIC_API_KEY=        # User supplies their own — see setup guide
REDIS_URL=                # Optional for MVP, add when caching needed
DATABASE_URL=             # Post-MVP only
STRIPE_SECRET_KEY=        # Post-MVP only
STRIPE_PUBLISHABLE_KEY=   # Post-MVP only
```

---

## Claude API prompt (Listing Generator)

```
System:
You are an expert TPT (Teachers Pay Teachers) SEO copywriter specialising in {niche}
resources for {buyer_type}. You know exactly how TPT's search algorithm works and
what language teachers use when searching. You write listings that rank AND convert.
Respond only in valid JSON. No preamble, no markdown, no backticks.

User:
Generate a fully optimised TPT listing for this product:

{product_description}

Platform rules:
- Title: maximum {title_limit} characters, primary keyword must appear in first 3 words
- Tags: exactly {tag_count} tags, comma separated
- Description snippet: first 180 characters must contain primary keyword and main benefit

Return JSON:
{
  "title": "string",
  "tags": ["tag1", "tag2", ...],
  "description_snippet": "string (first 180 chars — the TPT preview)",
  "full_description": "string (full listing copy, scannable, bullet points)",
  "keyword_angles": ["phrase1", "phrase2", "phrase3", "phrase4", "phrase5"],
  "gap_opportunities": ["opportunity1", "opportunity2", "opportunity3"]
}
```

---

## Default niche options (all features)

Special Education, AAC / Communication, Social Stories, Adapted Literacy,
Autism Support, Intellectual Disability, Behaviour Support, Morning Work,
ELA, Math, Science, Social Studies, Art, Music, Physical Education,
Seasonal / Holiday, Back to School, TPT Seller Tools, General / All Subjects

---

## Why this wins

Every competitor targets established sellers optimising existing stores.
ListingLift targets new and growing sellers who need to break in first.

The Winnable Right Now filter is not available anywhere else.
The Niche Finder (discovery before creation) is not available anywhere else.
The Seasonal Launch Planner with upload timing is not available anywhere else.

Combined with a clean UI, multi-platform support, and AI listing generation —
this is the tool the TPT community has been asking for and nobody has built properly yet.
