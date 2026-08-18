from pathlib import Path
import sys
import time
import zipfile

repo_root = Path(__file__).resolve().parents[2]


def gather(base: Path, pack_code: str, slug: str, include_all: bool = False):
    files = []
    if base.exists():
        for p in base.rglob("*.pdf"):
            n = p.name.lower()
            if include_all:
                files.append(p)
            else:
                if n.startswith(pack_code.lower() + "-") or slug.replace("_", " ") in n or slug in str(p).lower():
                    files.append(p)
    return sorted(set(files))


def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else "llama_llama_red_pajama"
    pack = sys.argv[2] if len(sys.argv) > 2 else "LLRP"

    global_out = repo_root / "OUTPUT"
    theme_out = repo_root / "assets" / "themes" / slug / "OUTPUT"
    boards_dir = repo_root / "assets" / "themes" / slug / "aac_boards"

    group_a = gather(global_out, pack, slug, include_all=False)
    group_b = gather(theme_out, pack, slug, include_all=False)
    group_c = gather(boards_dir, pack, slug, include_all=True)

    ts = time.strftime("%Y%m%d-%H%M%S")
    pkg_dir = repo_root / "_packages"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    zip_path = pkg_dir / f"{pack}_package_{ts}.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in group_a:
            z.write(p, arcname=str(Path("Global_OUTPUT") / p.name))
        for p in group_b:
            z.write(p, arcname=str(Path("Theme_OUTPUT") / p.name))
        for p in group_c:
            z.write(p, arcname=str(Path("AAC_Boards") / p.name))

    print("PACKAGE_WRITTEN", str(zip_path))
    print("COUNTS", len(group_a), len(group_b), len(group_c))


if __name__ == "__main__":
    main()
