from pathlib import Path
import re, sys

ROOT = Path(r"D:\Seagate\small-wins-automation")
EXCLUDE_DIRS = {".git", "_ARCHIVE", "__pycache__", ".venv", ".venv311_x64"}
EXCLUDE_PATTERNS = ("icons_colored_20260820",)
PATTERNS = ("*.py", "*.ps1", "*.bat", "*.cmd", "*.json", "*.md", "*.cfg", "*.txt")

hits = {}
for pat in PATTERNS:
    for p in ROOT.rglob(pat):
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if any(s in str(p) for s in EXCLUDE_PATTERNS):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        lines = [i for i, line in enumerate(text.splitlines(), 1) if "icons_colored" in line.lower()]
        if lines:
            hits[str(p)] = lines

out = []
out.append("# Files referencing 'icons_colored'\n")
for path in sorted(hits):
    out.append(f"\n{path}")
    for ln in hits[path]:
        out.append(f"  line {ln}")

report = "\n".join(out)
print(report)
outfile = ROOT / "__tmp_icons_colored_refs.txt"
outfile.write_text(report, encoding="utf-8")

Path(__file__).unlink(missing_ok=True)
