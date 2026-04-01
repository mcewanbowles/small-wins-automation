# ListingLift — Multi-Platform Keyword & Listing Optimizer
## Windsurf Build Spec

---

## What this product is

A web app that shows digital product sellers what buyers are actually searching for on their platform, then writes their optimised listing for them. Think Publisher Rocket — but for TPT, Etsy, Amazon KDP, and other digital product platforms.

**Core problem it solves:** Sellers currently guess at keywords. They type a word and hope it has demand. This tool reverses that — start with real demand data, build the listing around it.

---

## Two core features

### Feature 1: Keyword Gap Finder

User flow:
1. User selects platform (TPT, Etsy, Amazon KDP, Creative Market, Gumroad)
2. User types a seed topic (e.g. "social stories autism" or "watercolour clipart")
3. App queries autocomplete sources in real time:
   - Google Autocomplete API (free, no key needed)
   - Pinterest search autocomplete (scrape endpoint)
   - Platform-specific autocomplete (scrape the platform's own search bar)
4. Returns a ranked list of long-tail phrases ordered by estimated demand signal
5. Flags GAP keywords — phrases with search signal but low supply on that platform
6. User can click any keyword to copy it or send it to the Listing Generator

**The Gold Formula:**
High search demand + Low platform supply = Gold keyword.
A buyer is actively searching for it. Hardly anyone has made it yet. Create it and you own that search term.

**Demand signal — is anyone searching this?**
Score 1 point for each source the phrase appears in:
- Google Autocomplete → real people are typing it
- Pinterest Autocomplete → teachers are actively saving/searching it
- TPT search bar suggestions → buyers on platform want it right now
- Score 3/3 = 🔥 High demand | Score 2/3 = Medium | Score 1/3 = Low

**Supply — how crowded is it?**
Search the exact phrase on TPT and count results returned:
- 0–50 results = 🟢 GOLD — wide open, make this now
- 51–200 results = 🟡 SILVER — winnable with a quality product
- 200+ results = 🔴 SATURATED — hard to rank, avoid unless your product is exceptional

**Gap score = Demand score minus Supply penalty**
Display combined verdict as:
- 🟢 MAKE THIS — high demand + low supply
- 🟡 WORTH A SHOT — medium demand or medium supply
- 🔴 CROWDED — avoid

**The output format sellers need — ranked table:**
| Keyword phrase | Demand | TPT supply | Verdict |
|---|---|---|---|
| social stories autism secondary | 🔥 High | 12 results | 🟢 MAKE THIS |
| AAC core word activities | 🔥 High | 8 results | 🟢 MAKE THIS |
| visual schedule autism adults | Medium | 23 results | 🟡 Worth a shot |
| social stories teenagers | 🔥 High | 340 results | 🔴 Crowded |

Sort by verdict: all MAKE THIS first, then WORTH A SHOT, then CROWDED.
Allow user to filter to show GOLD only (most common use case).

---

### Feature 2: Listing Generator

User flow:
1. User pastes their product description (free text)
2. User selects platform
3. User selects niche/category and target buyer type
4. Clicks Generate
5. Claude API generates:
   - Optimised title (respecting platform character limits — see rules below)
   - Full tag/keyword list (respecting platform tag counts)
   - Opening paragraph for the product description
   - 5 suggested long-tail keyword angles to target
6. One-click copy for each output section

**Platform listing rules:**

| Platform | Title limit | Tags | Notes |
|---|---|---|---|
| TPT | 80 chars | 20 tags | Comma separated |
| Etsy | 140 chars | 13 tags, max 20 chars each | Phrase-based |
| Amazon KDP | 200 chars | 7 keyword fields, 50 chars each | Backend keywords |
| Creative Market | 100 chars | 15 tags | |
| Gumroad | No limit | No tag system | SEO title + description only |

---

## Tech stack

### Frontend
- React (Vite)
- Tailwind CSS
- Platform selector as prominent first step (tab or dropdown)

### Backend
- Node.js or Python (FastAPI)
- Endpoints:
  - `POST /api/keywords` — takes seed + platform, returns keyword list with gap scores
  - `POST /api/generate-listing` — takes description + platform + niche, calls Claude API, returns title/tags/description
- Rate limiting on autocomplete scraping (respect platform ToS — add delays, rotate user agents)

### External services
- Claude API (claude-sonnet-4-20250514) for listing generation
- Google Autocomplete: `https://suggestqueries.google.com/complete/search?client=firefox&q={query}`
- Pinterest autocomplete: `https://www.pinterest.com/typeahead/?q={query}`
- TPT search: `https://www.teacherspayteachers.com/search?search={query}`
- Etsy search: `https://www.etsy.com/api/v3/ajax/bespoke/public/neu/specs/search_suggestions?query={query}`

### Auth + payments
- Clerk or Supabase Auth for user accounts
- Stripe for subscriptions
- Pricing tiers:
  - Free: 5 keyword searches/day, 3 listing generations/day, TPT only
  - Pro $19/month: unlimited searches, all platforms, keyword history saved
  - Lifetime $67 one-time: Pro features, no subscription

---

## Database (simple)

Users table: id, email, plan, searches_today, created_at
SavedKeywords table: id, user_id, platform, seed_term, keyword_phrase, gap_score, created_at
SavedListings table: id, user_id, platform, product_description, generated_title, generated_tags, created_at

---

## UI structure

### Page layout
```
Header: Logo | Platform selector (tabs) | Account
---
Left panel (40%): Keyword Gap Finder
  - Seed input
  - Search button
  - Results list with gap indicators
Right panel (60%): Listing Generator
  - Product description textarea
  - Niche + buyer selectors
  - Generate button
  - Output sections (title / tags / description) with copy buttons
```

### Platform selector
Prominent tab bar at the top:
`[ TPT ] [ Etsy ] [ Amazon KDP ] [ Creative Market ] [ Gumroad ]`
Selecting platform updates:
- Autocomplete sources used
- Character limits shown in generator
- Tag count shown in generator
- Gap detection search target

---

## MVP scope (build this first)

1. TPT platform only
2. Google Autocomplete as the only keyword source (no scraping yet)
3. Claude API listing generator (title + tags + description opener)
4. No auth, no database — stateless single session
5. Deploy to Vercel

Add in order after MVP:
- Pinterest autocomplete source
- Platform-specific autocomplete scraping
- Gap score (supply detection)
- User accounts + saved history
- Additional platforms (Etsy, KDP)
- Stripe payments

---

## Environment variables needed
```
ANTHROPIC_API_KEY=
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
DATABASE_URL=
```

---

## Claude API prompt structure (for listing generator)

```
System: You are an expert SEO copywriter specialising in {platform} listings for {niche} resources targeting {buyer_type}. You understand {platform}'s search algorithm and what buyers search for. Always output valid JSON only.

User: Generate an optimised {platform} listing for this product:

{product_description}

Return JSON with these fields:
- title: string (max {title_limit} characters, include top keywords near the start)
- tags: array of {tag_count} strings (each max {tag_char_limit} characters if applicable)
- description_opener: string (2-3 sentences, hook + main benefit + call to action)
- keyword_angles: array of 5 long-tail keyword phrases this product should target
- gap_opportunities: array of 3 underserved angles competitors are missing
```

---

## Notes for builder

- Scraping autocomplete endpoints is legal and standard practice (these are public suggestion APIs)
- Add 300-500ms delays between requests to be respectful
- Cache autocomplete results for 24 hours to avoid hammering endpoints
- The gap detection (counting search results) is the highest-value feature — prioritise it
- Mobile responsive is nice-to-have, not MVP requirement
- This tool is built by a TPT/SPED seller — the default niche options should include: Special Education, AAC/Communication, Social Stories, Literacy, Math, ELA, Science, TPT Seller Tools
