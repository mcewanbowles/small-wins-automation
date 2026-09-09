# Archived: Tool Launcher (WINDSURF_TOOL_LAUNCHER.py)

**Retired:** 2026-09-09 (Phase 1 of the Tool Launcher + StudioForge merge)
**Replaced by:** StudioForge (`studioforge_app.py`, launched via `run_studioforge.bat`)

## Why retired

The Tool Launcher had better wayfinding UX (grouped sidebar, flow stepper, status pills) but pointed at the wrong, legacy generators (`Accurate generators/GENERATE_ALL.py`, legacy `AAC_BOARD_GENERATOR.py` with hardcoded `H:\` paths and old brand colors). StudioForge points at the canonical `Studioforge/_TRUTH/` generators and has the correct gated 9-stage workflow.

Decision: merge the best of both into StudioForge and retire the Tool Launcher. See `../../MERGE_PLAN.md` at the repo root for the full comparison and phased plan.

## What lives here

- `WINDSURF_TOOL_LAUNCHER.py` — the retired Tkinter app (source of UX patterns to port in Phase 2)
- `WINDSURF_TOOL_LAUNCHER.py.bak_deadcode_*` — pre-cleanup backup
- `Launch_Tool_Launcher.bat` / `Launch_Tool_Launcher_DEBUG.bat` — old launchers
- `create_tool_launcher_shortcuts*.ps1` / `remove_tool_launcher_*.ps1` — shortcut scripts
- `_patch_tool_launcher_*.ps1` — historical patch scripts
- `_tool_launcher_log.bak` — backup of last-used log

## What was NOT moved (kept in place)

- `_tool_launcher_log.json` stays at `Studioforge/_tool_launcher_log.json` — its last-used timestamps will seed the new StudioForge sidebar in Phase 2.

## Do not re-wire these files

These are archived for reference only. The desktop shortcut `Small Wins Tool Launcher.lnk` and the repo shortcut `Small Wins Studio.lnk` now both point at `run_studioforge.bat`.
