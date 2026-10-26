# StudioForge Strategist

*Your built-in business strategist. Goal: **$2,000 per week within 6 months** (26 weeks).*

## What it does in plain words

Every day it hands you a **short, ordered to-do list** sized to the time you have — never a wall of options. Each task is a small sprint that ships something real (a book pack, marketing pins, an upload). You tick a task, it records a win and keeps your streak. When a selling season passes (e.g. Halloween), the list automatically moves to the next one — you never have to re-plan.

## Commands

```bash
python -m strategist.plan today          # today's list (add --min 45 for a short day)
python -m strategist.plan done <task-id> # tick a task — the id is shown in the list
python -m strategist.plan week           # this week's shape + the ramp math
python -m strategist.plan scan "topic"   # market scan (auto if an API key exists, else a 15-min checklist)
python -m strategist.plan stats          # wins, streak, ramp numbers
```

## How it thinks (the strategy)

- **The math:** a live mini-bundle is assumed to earn ~$25/week (tune `AVG_WEEKLY_PER_PRODUCT` in `brain.py` once real TPT numbers land). $2,000/wk ≈ 80 live products in 26 weeks ≈ ~3 uploads/week. `stats` shows the ramp honestly.
- **Seasons:** `brain.py` holds a selling-seasons calendar (Back to School → Halloween → Thanksgiving → Christmas → New Year → Valentine's → Spring → Easter → End of Year → Summer). Tasks inside a season window push that season's products; outside it, evergreen products (wh-questions, core vocab, AAC, sorting) which pay every week.
- **Weekly rhythm:** Mon/Thu = Tailwind pins sprint, Tue/Fri = market scan, Wed = SEO refresh, Sat = book companions, Sun = stats. Review-gate and ready-to-upload work always jump to the top of the list.
- **ADHD-friendly by design:** one list, ordered, each item ≤45 min, a "Start here →" pointer, and a win recorded every tick (`done` prints a cheer + streak).

## Where it lives in studioforge-next

- `strategist/state.py` — the ONE record (`config/strategist_state.json`), per the brief's "one writer per concept" rule.
- `strategist/brain.py` — pure strategy logic; no file I/O.
- `strategist/research.py` — market scans (Serper/Tavily keys if present; manual checklist otherwise).
- `strategist/plan.py` — the CLI/render layer. The studioforge-next **Today** screen should call `brain.build_day_plan()` + `state.load()` directly — this file is just the terminal view.

## Wiring still to do (next steps)

- Feed `state["pipeline"]["pending_reviews"]` / `["ready_to_upload"]` from the real review/upload state so "upload day" detection is automatic.
- Feed `state["uploads"]` from the upload tracker so the ramp reflects reality.
- Optional: drop `SERPER_API_KEY` or `TAVILY_API_KEY` in `.env` to make `scan` pull live results.
- Surface `today` as the opening screen of studioforge-next (the "Today" view).
