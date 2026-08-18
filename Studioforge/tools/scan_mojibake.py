from pathlib import Path
import re
import sys
import fitz

repo_root = Path(__file__).resolve().parents[2]
patterns = [
    r"ï»¿",
    r"Â",
    r"Ã.",
    r"â€™",
    r"â€œ",
    r"â€\x9d",
    r"â€˜",
    r"â€“",
    r"â€”",
    r"�",
]
regex = re.compile("|".join(patterns))

def scan_pdf(path: Path):
    hits = []
    try:
        with fitz.open(path) as doc:
            for i, page in enumerate(doc, start=1):
                text = page.get_text("text") or ""
                if regex.search(text):
                    for m in regex.finditer(text):
                        frag = text[max(0, m.start()-20):m.end()+20].replace("\n", " ")
                        hits.append((i, m.group(0), frag))
    except Exception as e:
        return [(0, "ERROR", str(e))]
    return hits

def main():
    outputs = []
    global_out = repo_root / "OUTPUT"
    theme_out = repo_root / "assets" / "themes" / "llama_llama_red_pajama" / "OUTPUT"
    board_out = repo_root / "assets" / "themes" / "llama_llama_red_pajama" / "aac_boards"
    for base in (global_out, theme_out, board_out):
        if base.exists():
            for p in base.rglob("*.pdf"):
                if p.name.startswith("LLRP-") or "llama_llama_red_pajama" in str(p).lower() or "aac_board" in p.name.lower():
                    outputs.append(p)
    bad = {}
    for pdf in sorted(set(outputs)):
        res = scan_pdf(pdf)
        if res:
            bad[str(pdf)] = res
    if bad:
        print("MOJIBAKE_FOUND")
        for f, rows in bad.items():
            print(f":: {f}")
            for page, token, frag in rows[:10]:
                print(f"  p{page}: [{token}] ... {frag} ...")
        sys.exit(2)
    else:
        print("MOJIBAKE_CLEAN")

if __name__ == "__main__":
    main()
