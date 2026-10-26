"""StudioForge Strategist — daily/weekly business planning brain.

Goal: get Fiona to $2,000/week within 6 months by turning the big goal
into small, ordered, completable tasks with visible wins.

Design rules (from STUDIOFORGE_REDESIGN_BRIEF.md):
- One record: all strategist state lives in ONE json file via state.py.
- No one-off mutation scripts: every action is a function or a CLI command.
- Files are persistence, not structure.
"""

__all__ = ["plan", "brain", "state", "research"]
