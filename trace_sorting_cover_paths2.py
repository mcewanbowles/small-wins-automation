from pathlib import Path

# Read-only replica of Sorting cover asset resolution
ROOT = Path(__file__).resolve().parent
THEME_SLUG = 'llama_llama_red_pajama'

theme_dir = ROOT / 'assets' / 'themes' / THEME_SLUG
print('theme_dir:', theme_dir)

# Hero resolution (matches priority in SORTING_CARDS new flow)
hero_candidates = [
    theme_dir / 'characters' / 'llama_llama.png',
    theme_dir / 'activity_images' / 'llama_llama.png',
    theme_dir / 'hero_header.png',
    theme_dir / 'heroes' / 'hero_header.png',
    theme_dir / 'characters' / 'hero_header.png',
    theme_dir / 'hero.png',
    theme_dir / 'heroes' / 'hero.png',
    theme_dir / 'characters' / 'hero.png',
    theme_dir / 'header_icon.png',
]
hero_path_str = None
for hp in hero_candidates:
    print('HERO_CAND:', hp, 'EXISTS' if hp.exists() else 'missing')
    if hp.exists() and hero_path_str is None:
        hero_path_str = str(hp)
print('RESOLVED hero_path_str =', hero_path_str)

# Book cover resolution (matches SORTING_CARDS new flow)
cover_names = ["book_cover", "cover", "front_cover", "bookfront", "book", "cover_reference"]
cover_subdirs = [theme_dir, theme_dir / 'covers', theme_dir / 'images', theme_dir / 'marketing', theme_dir / 'book']
exts = ['png', 'jpg', 'jpeg', 'webp']
book_cover_path_str = None
for sd in cover_subdirs:
    for nm in cover_names:
        for ex in exs:
            fp = sd / f"{nm}.{ex}"
            if fp.exists():
                print('COVER_CAND:', fp, 'EXISTS')
                book_cover_path_str = str(fp)
                break
        if book_cover_path_str:
            break
    if book_cover_path_str:
        break

if not book_cover_path_str:
    for fp in theme_dir.rglob('*cover*.*'):
        if fp.suffix.lower().lstrip('.') in exs:
            print('COVER_SCAN_HIT:', fp)
            book_cover_path_str = str(fp)
            break

print('RESOLVED book_cover_path_str =', book_cover_path_str)
