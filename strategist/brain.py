"""The strategy brain: goal math, seasonal calendar, sprint templates.

Everything here is pure functions + data. No file I/O — state.py owns that.

Revenue model (deliberately simple, tweak as real data arrives):
- Target $2,000/week in 26 weeks. Roughly linear ramp on product count:
  each uploaded mini-bundle is assumed to earn ~AVG_WEEKLY_PER_PRODUCT.
- Weeks elapsed vs weeks needed tells us the required upload pace.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

# --- revenue model knobs (adjust as real TPT numbers come in) ---
AVG_WEEKLY_PER_PRODUCT = 25.0   # one live mini-bundle ≈ $25/wk on average
GOAL_WEEKS = 26


@dataclass
class Season:
    name: str
    start: tuple[int, int]        # (month, day) inclusive
    end: tuple[int, int]          # (month, day) inclusive
    hooks: list[str]              # content/marketing angles
    upload_deadline_hint: str     # when products for it must be LIVE


# Selling seasons — upload ~4-6 weeks BEFORE the event (TPT buyers shop early).
SEASONS: list[Season] = [
    Season("New Year / MLK",      (12, 26), (1, 20),
           ["new year routines", "goal setting", "MLK", "winter vocab"],
           "live by mid-December"),
    Season("Valentine's / 100th Day", (1, 21), (2, 14),
           ["valentine's day", "friendship", "100th day of school", "kindness"],
           "live by mid-January"),
    Season("St Patrick's / Spring", (2, 15), (3, 17),
           ["st patrick's day", "spring vocab", "weather", "life cycles"],
           "live by mid-February"),
    Season("Easter / Earth Day",  (3, 18), (4, 22),
           ["easter", "earth day", "spring animals", "recycling"],
           "live by early March"),
    Season("End of Year / Summer", (4, 23), (6, 20),
           ["end of year review", "summer vocab", "field day", "graduation"],
           "live by mid-April"),
    Season("Back to School",      (6, 21), (9, 15),
           ["back to school", "classroom routines", "all about me", "school supplies"],
           "live by early August — biggest TPT season"),
    Season("Fall / Halloween",    (9, 16), (10, 31),
           ["fall leaves", "halloween", "fire safety week", "pumpkins"],
           "live by early September"),
    Season("Thanksgiving",        (11, 1), (11, 28),
           ["thanksgiving", "gratitude", "turkey", "family"],
           "live by mid-October"),
    Season("Christmas / Winter",  (11, 29), (12, 25),
           ["christmas", "winter holidays", "gingerbread", "hanukkah", "kwanaa"],
           "live by mid-November"),
]

EVERGREEN_HOOKS = [
    "wh-questions", "core vocabulary", "aac boards", "sorting mats",
    "following directions", "sequencing", "categories", "sight words",
    "social skills", "emotions", "life skills", "phonics",
]


@dataclass
class Task:
    id: str
    label: str
    kind: str         # "sprint" | "research" | "upload" | "review" | "maintenance"
    est_min: int
    why: str = ""
    done: bool = False


# --- sprint templates: small batches that ship ---

SPRINT_TEMPLATES = [
    ("build-books", "Build {n} evergreen book pack(s) ({hook})", "sprint", 45,
     "Evergreen packs sell year-round — the base of the $2k/wk ramp"),
    ("book-companions", "Draft {n} book companion outline(s) — search trending titles", "sprint", 30,
     "Book companions ride existing book demand; cheapest acquisition"),
    ("tailwind-ads", "Create {n} Tailwind/Pinterest marketing pin(s)", "sprint", 20,
     "Pinterest is the #1 external traffic source for TPT sellers"),
    ("seo-pass", "SEO refresh on {n} existing listing(s): title + tags + first 3 lines", "sprint", 25,
     "Better SEO on live products beats new products 3:1 early on"),
    ("qa-upload", "Final QA + upload {n} ready product(s) to TPT", "upload", 30,
     "Nothing earns until it's live — upload day is the whole point"),
    ("market-scan", "Run market scan: {topic}", "research", 20,
     "Price/competition intel keeps the backlog aimed at demand"),
    ("review-gate", "Clear review queue: approve/edit {n} pending item(s)", "review", 15,
     "Review is the bottleneck — unreviewed = unbuilt = unearned"),
    ("stats-check", "Log this week's TPT stats into the tracker", "maintenance", 10,
     "The ramp only self-corrects if real numbers feed the model"),
]


def current_season(today: date | None = None) -> Season:
    today = today or date.today()
    md = (today.month, today.day)
    for s in SEASONS:
        if s.start <= s.end:      # same-year span
            if s.start <= md <= s.end:
                return s
        else:                     # wraps over New Year
            if md >= s.start or md <= s.end:
                return s
    return SEASONS[0]


def next_season(today: date | None = None) -> Season:
    cur = current_season(today)
    i = SEASONS.index(cur)
    return SEASONS[(i + 1) % len(SEASONS)]


def weekly_target_now(state: dict, today: date | None = None) -> dict:
    """Where the ramp should be vs where it is. Returns the math for the UI."""
    today = today or date.today()
    goal = state["goal"]
    started = date.fromisoformat(goal["started_on"])
    elapsed = max(0, (today - started).days // 7)
    remaining = max(1, GOAL_WEEKS - elapsed)
    live_products = len(state.get("uploads", []))
    current_weekly = live_products * AVG_WEEKLY_PER_PRODUCT
    weekly_needed = goal["weekly_revenue_target"] - current_weekly
    products_needed = max(0, round(weekly_needed / AVG_WEEKLY_PER_PRODUCT + 0.49))
    per_week = round(products_needed / remaining, 1)
    return {
        "week": elapsed + 1,
        "weeks_left": remaining,
        "live_products": live_products,
        "current_weekly_est": current_weekly,
        "products_needed": products_needed,
        "uploads_per_week": per_week,
    }


def build_day_plan(state: dict, today: date | None = None,
                   available_min: int = 90) -> list[Task]:
    """Ordered, right-sized task list for one sitting.

    Order: review gate → upload → one build sprint → one marketing/research
    sprint → stats. Cut off at available_min so the list always feels doable.
    """
    today = today or date.today()
    season = current_season(today)
    nxt = next_season(today)
    ramp = weekly_target_now(state, today)
    tasks: list[Task] = []

    def t(tid, label, kind, mins, why=""):
        tasks.append(Task(tid, label, kind, mins, why))

    # 1. Always lead with unblocking work (review gate first — it's the cap).
    pending = _pending_reviews(state)
    if pending:
        t("review-gate", f"Approve/edit {pending} item(s) in the review queue",
          "review", 15, "Unblocks the build pipeline — review is the bottleneck")

    # 2. If products are ready, today is upload day.
    ready = _ready_uploads(state)
    if ready:
        t("qa-upload", f"QA + upload {ready} ready product(s) to TPT",
          "upload", 30, "Nothing earns until it's live")

    # 2b. One-off marketplace test (until done): TeacherStore.io bulk upload.
    tests = state.get("marketplace_tests") or {}
    if not tests.get("teacherstore_done"):
        t("teacherstore-test",
          "TeacherStore.io test: sign up + free bulk upload of 5-10 evergreen packs",
          "sprint", 40,
          "Free upload while you're not exclusive — cheap diversification data for the Jan 1 tier decision")

    # 3. The main build sprint — seasonal first while inside the window,
    #    evergreen otherwise.
    seasonal_open = season.end >= (today.month, today.day)
    if seasonal_open and season.name not in ("Christmas / Winter",):
        t("build-seasonal",
          f"Build 1 {season.name} pack — hook: {season.hooks[0]} "
          f"(must be {season.upload_deadline_hint})",
          "sprint", 45, f"In-season window: {season.name}")
    else:
        t("build-evergreen",
          f"Build 1 evergreen pack — hook: {EVERGREEN_HOOKS[today.toordinal() % len(EVERGREEN_HOOKS)]}",
          "sprint", 45, "Evergreen compounds — pays every week of the year")

    # 4. Marketing/research alternates by weekday so both happen weekly.
    weekday = today.weekday()
    if weekday in (0, 3):      # Mon, Thu
        t("tailwind-ads", "Create 3 Tailwind/Pinterest pins for live listings",
          "sprint", 20, "Pinterest drives external TPT traffic")
    elif weekday in (1, 4):    # Tue, Fri
        t("market-scan",
          f"Market scan: top 5 '{nxt.hooks[0]}' products on TPT — price, preview style, gap",
          "research", 20, f"Next season prep: {nxt.name} ({nxt.upload_deadline_hint})")
    elif weekday == 2:         # Wed
        t("seo-pass", "SEO refresh on 3 live listings (title + tags + first 3 lines)",
          "sprint", 25, "Cheapest growth lever: listings that rank")
    else:                      # Sat
        t("book-companions", "Draft 2 book-companion outlines from trending read-alouds",
          "sprint", 30, "Companions ride existing book demand")
    if weekday == 6:           # Sun
        t("stats-check", "Log this week's TPT sales/traffic into the tracker",
          "maintenance", 10, "Feeds the ramp model real numbers")

    # 5. Right-size to the sitting.
    out, used = [], 0
    for task in tasks:
        if used + task.est_min <= available_min or not out:
            out.append(task)
            used += task.est_min
    return out


def _pending_reviews(state: dict) -> int:
    # Wired to review_state.json counts once studioforge-next lands the
    # book record; until then the user can set it in state manually.
    return int((state.get("pipeline") or {}).get("pending_reviews", 0))


def _ready_uploads(state: dict) -> int:
    return int((state.get("pipeline") or {}).get("ready_to_upload", 0))
