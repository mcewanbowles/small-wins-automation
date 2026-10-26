# StudioForge Strategy & Build Roadmap
*Prepared in my role as your strategist · 2026-10-26 · goal: $2,000/week within 26 weeks*

---

## 0. The one-paragraph answer

Build **`studioforge-next` in phases with a "Today" screen first** — a single page that shows progress at a glance (what's done, what's next, money ramp) so you never have to ask a chat where things stand. Do **not** start by rebuilding generators or porting features — that's how last time went piecemeal. Everything below is ordered so each phase leaves you with something usable, and the business keeps shipping products while the rebuild happens in parallel.

---

## 1. What to explore BEFORE the build (so it's not piecemeal)

Last time the pain came from building features without deciding these five things first. Decide them now — they're cheap decisions, expensive to change later:

| # | Decision | My recommendation |
|---|---|---|
| 1 | **Where does studioforge-next live?** | Same tree, `studioforge_next/` folder + one launcher. Not a new repo, not a new laptop setup. The brief's migration tree IS home. |
| 2 | **What is the unit of everything?** | The **Book record** (brief §4.1). Agree the schema before any UI — every later feature is just a view of it. |
| 3 | **What kills the tracker confusion?** | You shouldn't *read* a tracker — the Today screen should *tell* you. Design the status machine (brief §4.3) so one field per book = its stage. |
| 4 | **What stays in the old app vs moves?** | Old app keeps running for production work until next reaches parity on one book (brief §9 golden-file check). No big-bang cutover — ever. |
| 5 | **What do we deliberately NOT build?** | No new product generators during the rebuild. No multi-marketplace uploads. No new features that aren't a view of the book record. The scope fence is what prevents piecemeal. |

---

## 2. The "live data" you asked for — the Today screen spec

This is the feature that answers "what progress is" without asking anyone. One screen, four numbers at the top:

```
┌──────────────────────────────────────────────────────────┐
│  WEEK 6 of 26          $310/wk est. → $2,000 target       │
│  14 live products      need ~2.8 uploads/week             │
│  Streak: 5 days 🔥     3 things blocked on YOU            │
└──────────────────────────────────────────────────────────┘
  TODAY'S LIST                    PIPELINE AT A GLANCE
  1. [ ] Upload Gingerbread pack  scaffolded ......... 12
  2. [ ] 3 Pinterest pins         awaiting review ... 2 ← blocked
  3. [x] SEO pass (3 listings)    built/QA .......... 4
                                  ready to upload ... 3 ← money waiting
  Season: Christmas — live by mid-Nov
```

- Every number comes from the book records — no separate tracker to decode.
- "Blocked on YOU" = the review queue. It's the only number that can stall the whole business, so it gets its own callout.
- Wins/streak already built (the Strategist module) — this screen is its natural home.

---

## 3. Build phases & timescale

Pace assumption: ~1 focused phase per 1–2 weeks, working alongside your normal product-building days (the Strategist keeps sprints going — the rebuild should never eat more than half your week, or the $2k goal dies).

| Phase | What | Time | You get |
|---|---|---|---|
| **0 — Now** | Safety net: git baseline + backup button (DONE today); .gitignore; desktop launcher confirmed | done | Work can't be lost |
| **1 — Foundations** | Book record schema + migrate-on-read loader (reads your existing files, writes one record) | 1 week | Invisible change; kills the "7 files per book" bug class |
| **2 — Today screen** | The glanceable dashboard above inside the current app (not next) | 1 week | You stop asking "what's progress" — **this week if you want it first** |
| **3 — One app** | Review dashboard absorbed into the app; one port; ICON_LABELER secured | 1–2 weeks | One app, one mental model |
| **4 — Status machine** | Per-product typed state; "what can I upload today" is a query not a hunt | 1–2 weeks | Upload days become obvious |
| **5 — Pipeline runner** | `sf build` one function: build→finalize→package→thumbs→SEO→QA | 2 weeks | One command instead of 4 shells deep |
| **6 — Quarantine & slim** | 700 one-off scripts → `_archive/`; one generator tree | 1 week | Nothing resurrects old bugs |
| **7 — Parity & cutover** | Golden-file check on 2–3 known books, then old tree → read-only | 1–2 weeks | studioforge-next is THE app |
| **8 — Phase-2 business** | Own storefront page + Pinterest engine (AI-search hedge, per market research); TGM bulk-upload test | after | Diversified income |

**Total to cutover: ~8–10 weeks** — which lands the new system about 4 months before the $2k deadline, with 16+ weeks to run the upload ramp on it. Realistic, not heroic.

## 4. How the money clock maps to the build

- Weeks 1–8: build continues BUT every week includes upload sprints — target ~2 products/week live by week 8 (ramps to ~$50/wk).
- Weeks 9–16: on the new system, uploads should hit 3–4/week → ~$400–800/wk.
- Weeks 17–26: SEO refresh + bundles + seasonal pushes + storefront → the $2k push.
- If upload pace slips below 2/week for 2 consecutive weeks, the Strategist flags it and we rebalance build-vs-ship (the ramp math in `brain.py` does this automatically).

## 5. What I need from you (the decisions)

1. **Phase 2 first?** The Today screen alone might be worth doing before the deep rebuild — it's the visibility you asked for. Say yes and I start there.
2. **GitHub backup repo** — still needs you to create `small-wins-studio` (private) on github.com so pushes have somewhere to go.
3. **TPT tier check** — tell me if you're Basic or Exclusive; it decides whether the TGM test is even allowed.
