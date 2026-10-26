"""CLI + render layer for the Strategist.

Usage:
    python -m strategist.plan today            # today's task list
    python -m strategist.plan today --min 60   # smaller sitting
    python -m strategist.plan done <task_id>   # tick a task → dopamine
    python -m strategist.plan week             # the week's shape + ramp math
    python -m strategist.plan scan "topic"     # run a market scan
    python -m strategist.plan stats            # wins, streak, ramp numbers

Output is plain text — Streamlit (studioforge-next "Today" screen) can
import build_day_plan/current_season directly instead of parsing this.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from . import brain, research, state as st

DOPAMINE = [
    "Done. That's money-adjacent.",
    "Checked off — the machine moved.",
    "One less thing between you and $2k/wk.",
    "Banked. Momentum is the whole game.",
    "Progress, not perfection. Next.",
]


def _render_today(state: dict, minutes: int) -> str:
    today = date.today()
    season = brain.current_season(today)
    ramp = brain.weekly_target_now(state, today)
    plan = st.load().get("today")

    # Reuse the plan already issued today so re-opening shows ticks, not a reshuffle.
    if plan and plan.get("date") == today.isoformat():
        fields = {f for f in brain.Task.__dataclass_fields__}
        tasks = [brain.Task(**{k: v for k, v in t.items() if k in fields})
                 for t in plan["tasks"]]
    else:
        tasks = brain.build_day_plan(state, today, available_min=minutes)
        state["today"] = {"date": today.isoformat(),
                          "tasks": [vars(t) for t in tasks]}
        st.save(state)

    lines = [
        f"Today — {today.strftime('%A %d %b')}  |  Week {ramp['week']} of 26",
        f"Season: {season.name} ({season.upload_deadline_hint})",
        f"Ramp: ~{ramp['live_products']} live products → "
        f"need ~{ramp['uploads_per_week']}/week to hit $2k/wk. "
        f"{ramp['weeks_left']} weeks left.",
        "",
    ]
    if all(t.done for t in tasks):
        lines.append("All done. Genuinely — go enjoy the rest of the day.")
    else:
        for i, t in enumerate(tasks, 1):
            box = "[x]" if t.done else "[ ]"
            lines.append(f"{i}. {box} {t.label}  (~{t.est_min} min)")
            if t.why and not t.done:
                lines.append(f"      ↳ {t.why}")
        nxt = next((t for t in tasks if not t.done), None)
        if nxt:
            lines += ["", f"Start here → python -m strategist.plan done {nxt.id}  (when finished)"]
    return "\n".join(lines)


def _render_week(state: dict) -> str:
    today = date.today()
    season = brain.current_season(today)
    nxt = brain.next_season(today)
    ramp = brain.weekly_target_now(state, today)
    wins = [w for w in state["wins"] if w["date"] >= _week_start(today)]
    return "\n".join([
        f"Week {ramp['week']}/26 — {len(wins)} task(s) done this week, "
        f"streak {state['streak']['current']} day(s)",
        "",
        f"In season now : {season.name} — {', '.join(season.hooks[:3])}",
        f"Prep next     : {nxt.name} — products must be {nxt.upload_deadline_hint}",
        f"Upload pace   : ~{ramp['uploads_per_week']} products/week needed",
        "",
        "Suggested week shape:",
        "  Mon: pins sprint + main build   Tue: market scan",
        "  Wed: SEO pass                   Thu: pins sprint + main build",
        "  Fri: market scan + upload QA    Sat: companions   Sun: stats",
    ])


def _week_start(d: date) -> str:
    return date.fromordinal(d.toordinal() - d.weekday()).isoformat()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="strategist")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("today"); t.add_argument("--min", type=int, default=90)
    d = sub.add_parser("done"); d.add_argument("task_id")
    sub.add_parser("week")
    s = sub.add_parser("scan"); s.add_argument("topic")
    sub.add_parser("stats")
    args = p.parse_args(argv)

    state = st.load()

    if args.cmd == "today":
        print(_render_today(state, args.min))
    elif args.cmd == "done":
        state, task = st.mark_done(state, args.task_id)
        if task:
            total = len(state["wins"])
            streak = state["streak"]["current"]
            cheer = DOPAMINE[total % len(DOPAMINE)]
            print(f"✓ {task['label']}\n{cheer}  ({total} wins total, {streak}-day streak)")
        else:
            print(f"No open task '{args.task_id}' — run `today` to see the list.")
    elif args.cmd == "week":
        print(_render_week(state))
    elif args.cmd == "scan":
        f = research.scan(args.topic, state)
        st.save(state)
        if f["mode"] == "api":
            print(f"Top results for '{args.topic}':")
            for r in f["results"]:
                print(f"  • {r['title']}\n    {r['link']}\n    {r['snippet']}")
        else:
            print(f"No search API key set — 15-min manual scan for '{args.topic}':")
            for i, step in enumerate(f["checklist"], 1):
                print(f"  {i}. {step}")
    elif args.cmd == "stats":
        ramp = brain.weekly_target_now(state)
        print(f"Wins: {len(state['wins'])}  |  Streak: {state['streak']['current']} "
              f"(best {state['streak']['best']})")
        print(f"Est. ${ramp['current_weekly_est']:.0f}/wk from "
              f"{ramp['live_products']} products → target $2,000/wk, "
              f"need {ramp['products_needed']} more at "
              f"~{ramp['uploads_per_week']}/week.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
