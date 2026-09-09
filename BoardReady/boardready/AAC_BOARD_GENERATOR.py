#!/usr/bin/env python3
import argparse
import json
import csv
import re
import io
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, LETTER, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

try:
    from PIL import Image  # noqa: F401  # optional; images drawn directly by reportlab
except Exception:
    Image = None

DEFAULT_VOCAB = Path(__file__).resolve().parent / "vocab" / "book_vocab.json"
DEFAULT_THEMES_ROOT = Path(r"D:\Seagate\small-wins-automation\assets\themes")
DEFAULT_CORE = Path(r"D:\Seagate\small-wins-automation\assets\symbols\core")
DEFAULT_SYMBOLS_PNG = Path(r"D:\Seagate\small-wins-automation\assets\symbols\png")
DEFAULT_GLOBAL_AAC_CORE = Path(r"D:\Seagate\small-wins-automation\assets\global\aac_core")
DEFAULT_GLOBAL_COLOURS = Path(r"D:\Seagate\small-wins-automation\assets\global\colours")
DEFAULT_CORE_PROFILE = Path(__file__).resolve().parent / "config" / "core_profile.json"

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
HEADLINE_BOLD = "Helvetica-Bold"

def _register_brand_fonts():
    """Register SWS brand fonts (Poppins -> Comic Sans -> Helvetica)."""
    global FONT_REGULAR, FONT_BOLD, HEADLINE_BOLD
    try:
        import sys, os
        # Add repo root to path so we can import the shared font utility
        _repo_root = Path(__file__).resolve().parents[2]
        if str(_repo_root) not in sys.path:
            sys.path.insert(0, str(_repo_root))
        from utils.sws_fonts import BRAND_FONT_REGULAR, BRAND_FONT_BOLD
        FONT_REGULAR = BRAND_FONT_REGULAR
        FONT_BOLD = BRAND_FONT_BOLD
        HEADLINE_BOLD = BRAND_FONT_BOLD
    except Exception:
        pass

_register_brand_fonts()

def load_core_profile(path: Path = DEFAULT_CORE_PROFILE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    layout = data.get("layout", [])
    if data.get("rows") != 6 or data.get("columns") != 6 or len(layout) != 6:
        raise ValueError("BoardReady core profile must define a 6x6 layout")
    core_words = [word for row in layout if row.get("role") == "core" for word in row.get("words", [])]
    if len(core_words) != 24 or len({str(word).lower() for word in core_words}) != 24:
        raise ValueError("BoardReady core profile must define 24 unique core words")
    if [row.get("role") for row in layout] != ["core", "core", "fringe", "fringe", "core", "core"]:
        raise ValueError("BoardReady core/fringe row roles do not match the canonical layout")
    zoned = data.get("zoned_layout", {})
    zoned_rows = zoned.get("left_core_columns", [])
    completion = zoned.get("completion_cells", [])
    if len(zoned_rows) != 6 or any(len(row) != 3 for row in zoned_rows) or len(completion) != 3:
        raise ValueError("BoardReady zoned layout must define six core columns and three completion cells")
    if not {str(word).lower() for row in zoned_rows for word in row}.union(str(word).lower() for word in completion).issubset({str(word).lower() for word in core_words}):
        raise ValueError("BoardReady zoned layout may use only canonical core words")
    return data


CORE_PROFILE = load_core_profile()
CORE_ROWS = [CORE_PROFILE["layout"][0]["words"], CORE_PROFILE["layout"][1]["words"]]
ROW5_ROW = CORE_PROFILE["layout"][4]["words"]
BOTTOM_ROW = CORE_PROFILE["layout"][5]["words"]
CANONICAL_CORE_WORDS = {str(word).strip().lower().replace(" ", "_") for row in CORE_PROFILE["layout"] if row.get("role") == "core" for word in row.get("words", [])}
COLOUR_ROW = ["red", "blue", "green", "yellow", "orange", "purple"]

WINDSURF_CORE_ROWS = CORE_PROFILE["zoned_layout"]["left_core_columns"]
WINDSURF_ZONE_D = CORE_PROFILE["zoned_layout"]["completion_cells"]

HIGH_VIS = False
SHOW_HEADER_BANNER = True
HV_STYLE = "black"
HV_LABELS = True
NO_COVER = False
HV_HALO = True


# Cache for per-book icon lock maps to avoid re-reading JSON repeatedly
ICON_LOCK_CACHE: dict[str, dict[str, str]] = {}

def _load_icon_lock_map(book_key: str, themes_root: Path) -> dict[str, str] | None:
    """Load assets/themes/<book_key>/icon_lock.json if present.

    Returns a mapping of normalised label -> absolute path string.
    Normalisation is lowercased and spaces to underscores.
    """
    try:
        p = themes_root / book_key / "icon_lock.json"
        if not p.exists():
            return None
        data = load_json(p)
        mapping: dict[str, str] = {}
        if isinstance(data, dict):
            for k, v in data.items():
                kk = str(k).strip().lower().replace(" ", "_")
                # Support either {word: path} or {word: {path: ..., variant: ...}}
                if isinstance(v, dict):
                    path = v.get("path")
                else:
                    path = v
                if isinstance(path, str) and path.strip():
                    mapping[kk] = path.strip()
        return mapping or None
    except Exception:
        return None


def load_json(p: Path):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def draw_footer(c: canvas.Canvas, top_line: Optional[str] = None, page_text: Optional[str] = None, bw: bool = False):
    width, _ = c._pagesize
    # Text colour adapts in HV: white on black, black on yellow; normal grey otherwise
    if HIGH_VIS:
        if HV_STYLE == "black":
            fg_color = colors.white
        else:
            fg_color = colors.black
    else:
        fg_color = colors.HexColor("#666666")
    footer_fs = 10 if HIGH_VIS else 7
    top_fs = 12 if HIGH_VIS else 8
    c.setFillColor(fg_color)
    c.setFont(FONT_REGULAR, footer_fs)

    # Load logo (skip in High-Vis so icons are the only colour)
    logo_reader = None
    if not HIGH_VIS and not bw:
        try:
            for lp in [
                Path(__file__).resolve().parents[2] / "assets" / "branding" / "logos" / "logo_transparent.png",
                Path(__file__).resolve().parents[2] / "assets" / "branding" / "logos" / "small_wins_logo_with_text.png",
            ]:
                if lp.exists():
                    logo_reader = ImageReader(str(lp))
                    break
        except Exception:
            logo_reader = None

    # Two-line footer to prevent overlap between PCS license line and brand line
    pcs_line = "PCS\u00AE symbols | PCS Maker Personal License"
    brand_line = "(c) Small Wins Studio 2026"

    # Logo size and gap
    gap = 2  # pts
    logo_w = 0
    logo_h = 0
    if logo_reader is not None:
        try:
            iw, ih = logo_reader.getSize()
            logo_h = 10  # slightly smaller to match footer_fs
            logo_w = max(1, int(iw * (logo_h / ih)))
        except Exception:
            logo_w = 0
            logo_h = 0

    # Y positions: brand line at bottom, PCS line above it with clear gap
    brand_y = 12
    pcs_y = brand_y + footer_fs + 6

    if not HIGH_VIS:
        try:
            c.setFillColor(colors.white)
            c.rect(0, brand_y - 8, width, 60, fill=1, stroke=0)  # taller mask for two-line clearance
        except Exception:
            pass

    # Optional top footer line (product + code [+ page x/y]) centered, to match Small Wins frame
    if isinstance(top_line, str) and top_line.strip():
        tl = top_line.strip()
        if isinstance(page_text, str) and page_text.strip():
            tl = f"{tl} | {page_text.strip()}"
        c.setFillColor(fg_color)
        c.setFont(FONT_BOLD, top_fs)
        tw = c.stringWidth(tl, FONT_BOLD, top_fs)
        c.drawString((width - tw) / 2, pcs_y + 22, tl)  # well above the PCS line
    if not HIGH_VIS:
        c.setFillColor(fg_color)

    # Draw PCS license line (centered)
    c.setFont(FONT_REGULAR, footer_fs)
    pcs_w = c.stringWidth(pcs_line, FONT_REGULAR, footer_fs)
    c.drawString((width - pcs_w) / 2, pcs_y, pcs_line)

    # Draw brand line (centered with optional logo)
    brand_w = c.stringWidth(brand_line, FONT_REGULAR, footer_fs)
    group_w = brand_w + (gap + logo_w if logo_w else 0)
    gx = (width - group_w) / 2
    c.drawString(gx, brand_y, brand_line)
    if logo_reader and logo_w:
        try:
            c.drawImage(logo_reader, gx + brand_w + gap, brand_y - 1, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass


def draw_header(c: canvas.Canvas, title: str, hero_path: Optional[Path] = None):
    width, height = c._pagesize
    margin = 36
    # Brand teal header banner across the top for consistency with Matching
    banner_h = 36
    y = height - margin - banner_h + 6
    c.setFillColor(colors.HexColor("#31A8A0"))
    c.rect(0, y, width, banner_h, fill=1, stroke=0)
    # Optional hero icon left inside banner; fall back to Small Wins logo
    icon_path = hero_path
    if icon_path is None or not icon_path.exists():
        for lp in [
            Path(__file__).resolve().parents[2] / "assets" / "branding" / "logos" / "small_wins_logo_with_text.png",
            Path(__file__).resolve().parents[2] / "assets" / "branding" / "logos" / "logo_transparent.png",
        ]:
            if lp.exists():
                icon_path = lp
                break
    if icon_path is not None and icon_path.exists():
        try:
            ir = ImageReader(str(icon_path))
            iw, ih = ir.getSize()
            tgt_h = banner_h * 0.78
            scale = tgt_h / max(1, ih)
            dw = iw * scale
            dh = ih * scale
            px = margin * 0.5
            py = y + (banner_h - dh) / 2
            c.drawImage(ir, px, py, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    # Title in white centered on banner
    c.setFillColor(colors.white)
    c.setFont(HEADLINE_BOLD, 14)
    tw = c.stringWidth(title, HEADLINE_BOLD, 14)
    c.drawString((width - tw) / 2, y + (banner_h - 14) / 2 + 2, title)


def choose_pagesize(ps: str):
    if ps.lower() == "letter":
        return landscape(LETTER)
    return landscape(A4)


def choose_cover_pagesize(ps: str):
    """Return portrait page size (A4 or LETTER) for the cover page."""
    if ps.lower() == "letter":
        return LETTER
    return A4


def _alt_names(word: str) -> List[str]:
    alts: List[str] = []
    alts.append(word)
    if "_" in word:
        alts.append(word.replace("_", " "))
    if word == "colour":
        alts.append("color")
    if word == "what_next":
        alts.append("what next")
    if word == "dont_know":
        alts.append("dont know")
        alts.append("i dont know")
        alts.append("I dont know")
        alts.append("i don't know")
        alts.append("I don't know")
    if word == "dont_like":
        alts.append("dont like")
    if word == "all_done":
        alts.append("finished")
    if word == "I" or word == "i":
        alts.extend(["me", "my", "mine"])
    if word == "you":
        alts.append("yours")
    # Single-letter variants
    if len(word) == 1 and word.isalpha():
        alts.append(f"letter_{word}")
        alts.append(f"alphabet_{word}")
        if word == "a":
            alts.append("aa")  # PCS letter A sometimes stored as 'aa.png'
    # Common UK/US and compound variants
    if word == "favourite":
        alts.append("favorite")
    if word in ("goodnight", "good_night", "good night"):
        alts.extend(["good night", "good_night", "goodnight"])  # try both
    if word in ("wake_up", "wakeup", "wake up"):
        alts.extend(["wake up", "wake_up", "wake"])
    # Simple plural/singular alternates for frequent nouns
    if word.endswith("ies"):
        alts.append(word[:-3] + "y")
    if word.endswith("s") and not word.endswith("ss"):
        alts.append(word[:-1])
    # Curated common synonyms for PCS naming variants
    SYN = {
        "hippopotamus": ["hippo"],
        "boa_constrictor": ["boa", "snake", "boa constrictor"],
        "roar": ["roaring", "lion", "tiger"],
        "growl": ["growling", "bear"],
        "goodnight": ["good_night", "good night"],
        "keys": ["key", "house_keys"],
        "balloon": ["balloons"],
        "sun": ["sunny", "sunshine"],
        "moon": ["crescent_moon", "full_moon"],
        "rain": ["raining", "rain_cloud", "raindrops", "raindrop"],
        "cloud": ["clouds", "cloudy"],
        "wind": ["windy", "wind_blow"],
        "puddle": ["puddles", "water_puddle"],
        "pond": ["lake", "water_pond"],
        "nest": ["bird_nest"],
        "duckling": ["baby_duck", "duck_baby", "duck"],
        "kid": ["goat_kid", "baby_goat"],
        "calf": ["baby_cow", "cow_calf"],
        "piglet": ["baby_pig", "pig_baby"],
        "hen": ["chicken", "chicken_hen"],
        "rooster": ["chicken", "cockerel", "rooster_chicken"],
        "web": ["spider_web"],
        "ladybug": ["lady_bird", "ladybird", "lady_beetle"],
        "aphid": ["aphids"],
        "beetle": ["beetles", "bug"],
        "snail": ["snails"],
        "blossom": ["blossoms", "flower_blossom", "flower"],
        "buds": ["bud", "flower_bud"],
        "bloom": ["blossom", "flower"],
        "breeze": ["wind", "windy"],
        "trail": ["path", "track"],
        "path": ["trail", "track", "walkway"],
        "hatch": ["hatching", "egg_hatch"],
        "shell": ["egg_shell", "sea_shell", "shells"],
        "chrysalis": ["cocoon", "pupa"],
        "nectar": ["flower_nectar"],
        "milkweed": ["milk_weed"],
        "pollen": ["flower_pollen"],
        "sprout": ["sprouts", "seedling", "shoot"],
        "seed": ["seeds"],
        "pod": ["seed_pod", "pea_pod"],
        "bulb": ["flower_bulb"],
        "rainbow": ["rain_bow"],
        "soil": ["dirt", "ground", "earth"],
        "compost": ["compost_bin", "compost_heap"],
        "water_plants": ["watering_can", "water_flowers", "watering"],
        "trumpet": ["horn"],
        "snow": ["snowflake", "snowy"],
        "melt": ["melting", "thaw"],
        "hear": ["listen", "ear"],
        "found": ["find", "found_it"],
        "have_you_seen": ["see", "look"],
        "following": ["follow"],
        "goodness": ["good", "wow"],
        "bucket": ["pail"],
        "parrot": ["parrot_bird"],
        "stomp": ["stamp", "stomp_feet"],
        "sleeping_sheep": ["sheep_sleeping", "sleep", "sheep"],
        "loud_sheep": ["sheep_loud", "loud", "shout"],
        "scared_sheep": ["sheep_scared", "scared"],
        "thin_sheep": ["sheep_thin", "thin", "skinny"],
        "bath_sheep": ["sheep_bath", "bath"],
        "mole": ["mole_animal"],
        "hare": ["rabbit", "bunny"],
        "berries": ["berry"],
        "net": ["fishing_net"],
        "escape": ["run_away", "escape_run"],
        "dragonfly": ["dragon_fly"],
        "below": ["under", "below_under"],
        "calf_animal": ["calf"],
        "toad": ["frog_toad", "frog"],
        "roof": ["house_roof", "roof_top"],
        "storm": ["thunderstorm", "stormy"],
        "traffic": ["traffic_jam", "cars"],
        "twig": ["stick", "branch"],
        "beaver": ["beaver_animal"],
        "dragonfly": ["dragon_fly"],
        "heron": ["heron_bird"],
        "robin": ["bird_robin"],
        "song": ["music", "sing"],
        "shells": ["shell"],
        "engine": ["locomotive", "train_engine"],
        "boxcar": ["freight_car", "box_car", "train_car"],
        "caboose": ["train_caboose", "caboose_train"],
        "tank": ["tank_car", "tanker"],
        "track": ["rail", "railway", "train_track"],
        "station": ["train_station", "railway_station"],
        "dot": ["dots", "circle_dot"],
        "ten": ["10", "number_ten"],
        "shape": ["shapes", "geometry", "shape_icon"],
        "letter_a": ["a", "alphabet_a"],
        "letter_b": ["b", "alphabet_b"],
        "letter_c": ["c", "alphabet_c"],
        "cricket": ["cricket_insect"],
        "firefly": ["fire_fly", "lightning_bug"],
        "moth": ["moth_insect"],
        "praying_mantis": ["mantis", "praying-mantis"],
        "katydid": ["katy_did"],
        "sound": ["sound_icon", "sound_wave", "audio"],
        "chirp": ["chirping", "tweet"],
        "grandma": ["grandmother", "nana"],
        "hedgehog": ["hedgehog_animal"],
        "sneeze": ["sneezing"],
        "cave": ["cave_mouth", "cave_entrance"],
        "badger": ["badger_animal"],
        "crow": ["crow_bird"],
        "forest": ["woods", "trees_forest"],
        "snowstorm": ["blizzard"],
        "hard_hat": ["hardhat", "safety_helmet", "helmet"],
        "siren": ["alarm_siren"],
        "rescue": ["help", "save"],
        "painter": ["paint_brush", "artist", "painting"],
        "uniform": ["clothes_uniform", "uniform_clothes"],
        "hill": ["slope", "hill_mountain"],
        "road": ["street", "road_sign"],
        "stop_sign": ["stop sign", "stop", "sign_stop"],
        "shout": ["yelling", "yell"],
        "job": ["work", "occupation"],
        "driver": ["bus_driver", "driver_bus"],
        "seat": ["chair", "bus_seat"],
        "wheel": ["steering_wheel"],
        "ask": ["question", "ask_question"],
        "mail": ["post", "letter", "envelope"],
        "police": ["police_officer", "officer"],
        "angry": ["mad"],
        "scared": ["afraid"],
        "calm": ["relaxed"],
        "mixed": ["mixed_up", "mixed_emotions"],
        "jungle": ["rainforest", "forest"],
        "grumpy": ["mad", "angry"],
        "pigeon": ["pigeon_bird", "bird_pigeon"],
        "llama": ["alpaca", "llama_animal"],
        "coconut_tree": ["palm_tree", "coconut_palm", "palm"],
        "coconut": ["coconut_fruit"],
        "time_out": ["timeout", "time-out"],
        "come_back": ["return", "come back"],
        "loved": ["love", "heart"],
        "hyena": ["hyena_animal"],
        "armadillo": ["armadillo_animal"],
        "pickle": ["pickles", "gherkin", "cucumber"],
        "harvest": ["harvesting", "farm", "crops"],
    }
    if word in SYN:
        alts.extend(SYN[word])
    return alts


def _first_existing(root: Path, names: List[str]) -> Optional[Path]:
    for name in names:
        p = root / f"{name}.png"
        if p.exists():
            return p
    return None


def _theme_art_paths(book_key: str, themes_root: Path) -> tuple[Optional[Path], Optional[Path]]:
    """Return (hero_path, book_cover_path) if found under assets/themes/<book_key>."""
    tdir = themes_root / book_key
    hero_path: Optional[Path] = None
    cover_path: Optional[Path] = None
    try:
        hero_candidates = [
            tdir / "hero_header.png",
            tdir / "heroes" / "hero_header.png",
            tdir / "characters" / "hero_header.png",
            tdir / "characters" / "main.png",
            tdir / "characters" / "llama_llama.png",
            tdir / "activity_images" / "llama_llama.png",
            tdir / "hero.png",
            tdir / "heroes" / "hero.png",
            tdir / "characters" / "hero.png",
            tdir / "header_icon.png",
        ]
        for hp in hero_candidates:
            if hp.exists():
                hero_path = hp
                break
        cover_names = ["book_cover", "cover", "front_cover", "bookfront", "book", "cover_reference"]
        cover_subdirs = [tdir, tdir / "covers", tdir / "images", tdir / "marketing", tdir / "book"]
        for sd in cover_subdirs:
            for nm in cover_names:
                for ex in ("png", "jpg", "jpeg", "webp"):
                    cp = sd / f"{nm}.{ex}"
                    if cp.exists():
                        cover_path = cp
                        raise StopIteration  # break all loops
    except StopIteration:
        pass
    except Exception:
        hero_path, cover_path = hero_path, cover_path
    return hero_path, cover_path


def _make_cover_image(book_key: str, book_title: str, themes_root: Path, page_count: Optional[int], book_code: str) -> Optional["Image.Image"]:
    """Use utils.sws_design to build an AAC-specific teacher-style cover image."""
    if NO_COVER:
        return None
    try:
        import importlib
        design = importlib.import_module("utils.sws_design")
    except Exception:
        return None
    try:
        hero_path, cover_path = _theme_art_paths(book_key, themes_root)
        cov = getattr(design, "generate_teacher_cover_page", None)
        if not callable(cov):
            return None
        img = cov(
            theme_name=book_title,
            pack_code=book_code,
            product_name="AAC Communication Board",
            page_count=1,  # 1 board page after cover → total_pages=2
            level_count=None,
            hero_image=None,
            hero_image_path=str(hero_path) if hero_path else None,
            book_cover_path=None,  # Don't use published book cover; use PCS hero icon instead
            draw_footer=True,
            whats_included=[
                "Core + book fringe vocabulary",
                "36-cell communication grid",
                "Boardmaker PCS symbols throughout",
            ],
            also_included=["Communication strips"],
            top_tips=[
                "Model core words during shared reading.",
                "Use consistent cell locations to build motor memory.",
            ],
            rope_strand="Communication",
            rope_skills="Expressive Language · Core Vocab · Turn-Taking",
            render_chips=False,
            small_win_text="Small Wins",
        )
        return img
    except Exception:
        return None


def _find_by_stem(root: Path, names: List[str]) -> Optional[Path]:
    def norm(s: str) -> str:
        s = s.lower().replace(" ", "_").replace("-", "_")
        s = re.sub(r"[^a-z0-9_]", "", s)
        return s
    targets = set(norm(n) for n in names)
    if not root.exists():
        return None
    for p in root.rglob("*.png"):
        try:
            if p.stem and norm(p.stem) in targets:
                return p
        except Exception:
            continue
    return None


def _find_by_tokens(root: Path, names: List[str]) -> Optional[Path]:
    def tokenize(s: str) -> List[str]:
        s = s.lower().replace("-", "_").replace(" ", "_")
        s = re.sub(r"[^a-z0-9_]", "", s)
        toks = [t for t in s.split("_") if t]
        return toks

    def singularize(t: str) -> str:
        if t.endswith("ies") and len(t) > 3:
            return t[:-3] + "y"
        if t.endswith("es") and len(t) > 2 and not t.endswith(("ses", "xes", "ches", "shes")):
            return t[:-2]
        if t.endswith("s") and not t.endswith("ss"):
            return t[:-1]
        return t

    def token_set(s: str) -> set:
        toks = tokenize(s)
        # include simple singular variants for matching
        out = set(toks)
        out.update(singularize(t) for t in toks)
        return out

    if not root.exists():
        return None

    target_token_sets = [token_set(n) for n in names]
    for p in root.rglob("*.png"):
        try:
            cand = token_set(p.stem)
            for tgt in target_token_sets:
                if tgt and cand.issuperset(tgt):
                    return p
        except Exception:
            continue
    return None


def _degrade_candidates(word: str) -> List[str]:
    # Produce simpler fallbacks, e.g., brown_horse -> horse, sleeping_sheep -> sheep
    w = word.lower()
    # letter_a -> a
    m = re.match(r"^letter[_\s-]?([a-z])$", w)
    if m:
        return [m.group(1)]

    tokens = re.split(r"[_\s-]+", w)
    COLORS = {"red","blue","green","yellow","orange","purple","pink","brown","black","white","grey","gray"}
    ADJS = {"sleeping","loud","scared","thin","bath","little","big","small","kid","baby"}
    # Diminutives map
    DIMAP = {"duckling": "duck", "piglet": "pig", "calf": "cow", "kid": "goat"}

    candidates: List[str] = []
    # 1) strip leading colors/adjectives
    filtered = [DIMAP.get(t, t) for t in tokens if t and t not in COLORS and t not in ADJS]
    if filtered and filtered != tokens:
        candidates.append("_".join(filtered))
    # 2) last token only (e.g., sleeping_sheep -> sheep)
    if tokens:
        last = DIMAP.get(tokens[-1], tokens[-1])
        candidates.append(last)
    # 3) animal-color swap fallback: horse_brown -> horse
    if len(tokens) == 2 and (tokens[0] in COLORS or tokens[1] in COLORS):
        base = DIMAP.get(tokens[0], tokens[0]) if tokens[1] in COLORS else DIMAP.get(tokens[1], tokens[1])
        candidates.append(base)
    # Deduplicate while preserving order
    seen: set = set()
    out: List[str] = []
    for c in candidates:
        if c and c not in seen:
            out.append(c)
            seen.add(c)
    return out


def symbol_path_for(word: str, book_key: str, themes_root: Path, core_root: Path, symbols_png_root: Path, global_aac_core: Path, global_colours: Path) -> Optional[Path]:
    names = _alt_names(word)

    # -1. Prefer per-book icon_lock.json direct mapping if present
    try:
        norm = str(word).strip().lower().replace(" ", "_")
        lock_map = ICON_LOCK_CACHE.get(book_key)
        if lock_map is None:
            lock_map = _load_icon_lock_map(book_key, themes_root) or {}
            ICON_LOCK_CACHE[book_key] = lock_map
        p_lock = lock_map.get(norm)
        if p_lock:
            pl = Path(p_lock)
            if pl.exists():
                return pl
    except Exception:
        pass

    norm_word = str(word).strip().lower().replace(" ", "_")
    if norm_word in CANONICAL_CORE_WORDS:
        cand = _first_existing(global_aac_core, names)
        if cand:
            return cand
        for name in names:
            core_candidate = core_root / f"{name}.png"
            if core_candidate.exists():
                return core_candidate

    # (moved) Prefer book-specific locked activity images later, after curated/global sets

    # 1. prefer user's global sets
    colours_set = set(COLOUR_ROW + ["colour", "color"])
    if word in colours_set:
        cand = _first_existing(global_colours, names)
        if cand:
            return cand
    # Prefer book-level symbol_map.json (inserted icons) to override defaults
    smap = themes_root / book_key / "symbol_map.json"
    if smap.exists():
        try:
            mapping = load_json(smap)
            if word in mapping and mapping[word]:
                p = Path(mapping[word])
                if p.exists():
                    return p
        except Exception:
            pass

    # 1b. theme-level characters should override library defaults for book-specific heroes/characters
    chars_dir = themes_root / book_key / "characters"
    if chars_dir.exists():
        cand = _first_existing(chars_dir, names)
        if cand:
            return cand

    # 0b. Finally, prefer book-specific locked activity images as a fallback
    try:
        locked_dir = themes_root / book_key / "activity_images_locked"
        if locked_dir.exists():
            cand = _first_existing(locked_dir, names)
            if cand:
                return cand
    except Exception:
        pass

    # 2. heroes and curated global/library fallbacks (prefer modern curated 'alpha' and category art first)

    # global heroes folder (assets/symbols/png/heroes)
    heroes_dir = symbols_png_root / "heroes"
    if heroes_dir.exists():
        cand = _first_existing(heroes_dir, names)
        if cand:
            return cand
        # Try token-based match for variants like red_pete_the_cat
        cand = _find_by_tokens(heroes_dir, names)
        if cand:
            return cand

    # prefer PNG alpha folder for exact names (modern curated set)
    alpha_dir = symbols_png_root / "alpha"
    cand = _first_existing(alpha_dir, names)
    if cand:
        return cand

    # search by stem within categories subtree (e.g., categories/food/fruits)
    categories_dir = symbols_png_root / "categories"
    cand = _find_by_stem(categories_dir, names)
    if cand:
        return cand

    # token-based fuzzy search within categories (order-agnostic tokens)
    cand = _find_by_tokens(categories_dir, names)
    if cand:
        return cand

    # broad fallback: search anywhere under symbols png
    cand = _find_by_stem(symbols_png_root, names)
    if cand:
        return cand
    # token-based fuzzy search across all symbols
    cand = _find_by_tokens(symbols_png_root, names)
    if cand:
        return cand

    # 3. legacy/global aac core and simple core folder fallbacks at the end
    cand = _first_existing(global_aac_core, names)
    if cand:
        return cand
    core_candidate = core_root / f"{word}.png"
    if core_candidate.exists():
        return core_candidate
    # 7. degrade compound/adjective forms and retry searches
    for deg in _degrade_candidates(word):
        dn = _alt_names(deg)
        cand = _first_existing(global_aac_core, dn)
        if cand:
            return cand
        # core fallback
        core_candidate = core_root / f"{deg}.png"
        if core_candidate.exists():
            return core_candidate
        # prefer alpha exact
        alpha_dir = symbols_png_root / "alpha"
        cand = _first_existing(alpha_dir, dn)
        if cand:
            return cand
        # categories + broad search
        categories_dir = symbols_png_root / "categories"
        for finder in (_find_by_stem, _find_by_tokens):
            cand = finder(categories_dir, dn)
            if cand:
                return cand
            cand = finder(symbols_png_root, dn)
            if cand:
                return cand
    return None


def _prepare_board_icon(path: Path, bw: bool = False, high_vis: bool = False) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    edge = max(2, int(image.width * 0.02))
    image = image.crop((edge, edge, image.width - edge, image.height - edge))
    pixels = []
    source = image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()
    # High-vis boards need crisp icons; only remove near-pure backgrounds, not light icon details.
    avg_threshold = 250 if high_vis else 150
    range_threshold = 5 if high_vis else 12
    for red, green, blue, alpha in source:
        neutral = max(red, green, blue) - min(red, green, blue) < range_threshold and (red + green + blue) / 3 > avg_threshold
        pixels.append((red, green, blue, 0 if neutral else alpha))
    image.putdata(pixels)
    bounds = image.getchannel("A").getbbox()
    if bounds:
        image = image.crop(bounds)
    if bw:
        alpha = image.getchannel("A")
        image = image.convert("L").convert("RGBA")
        image.putalpha(alpha)
    elif high_vis:
        # Convert to high-contrast silhouette for consistent hi-vis treatment
        alpha = image.getchannel("A")
        # Desaturate to grayscale, then threshold to solid silhouette
        gray = image.convert("L")
        threshold = 128
        bw_alpha = gray.point(lambda p: 255 if p < threshold else 0)
        # Combine original alpha with thresholded silhouette
        combined_alpha = Image.composite(bw_alpha, Image.new("L", image.size, 0), alpha)
        # Create solid silhouette in the appropriate hi-vis color
        if HV_STYLE == "black":
            # Black background -> white icons
            silhouette = Image.new("RGBA", image.size, (255, 255, 255, 255))
        else:
            # Yellow background -> black icons
            silhouette = Image.new("RGBA", image.size, (0, 0, 0, 255))
        silhouette.putalpha(combined_alpha)
        image = silhouette
    return image


def draw_board(c: canvas.Canvas, rows: int, cols: int, items: List[str], book_key: str, book_title: str, themes_root: Path, core_root: Path, symbols_png_root: Path, global_aac_core: Path, global_colours: Path, bw: bool, pack_code: Optional[str] = None, page_text: Optional[str] = None):
    width, height = c._pagesize
    margin = 36
    # Determine HV mode up-front and paint page background accordingly
    hv = (not bw) and HIGH_VIS
    if hv:
        if HV_STYLE == "black":
            c.setFillColor(colors.black)
        else:
            c.setFillColor(colors.HexColor("#FFD100"))
        c.rect(0, 0, width, height, fill=1, stroke=0)
    # Reserve space for the header banner to prevent overlap
    header_clear = 48  # banner (~36) + safe gap
    header_clear = 48 if SHOW_HEADER_BANNER else 14
    # Also reserve clearance for the footer block (white strip + two lines)
    footer_clear = 64  # ~0.9 inch safe zone to avoid collisions
    grid_w = width - 2 * margin
    grid_h = height - 2 * margin - header_clear - footer_clear
    cell_w = grid_w / cols
    cell_h = grid_h / rows

    # Grid origin: cells start at margin + footer_clear, so the background and
    # frame must be anchored at the same y to stay in sync with the cells.
    grid_y = margin + footer_clear

    # Background inside frame (color only)
    if hv:
        # Reinforce background inside frame to ensure consistent tone
        c.setFillColor(colors.black if HV_STYLE == "black" else colors.HexColor("#FFD100"))
        c.rect(margin, grid_y, grid_w, grid_h, fill=1, stroke=0)
    elif not bw:
        c.setFillColor(colors.HexColor("#EBF5FF"))
        c.rect(margin, grid_y, grid_w, grid_h, fill=1, stroke=0)

    # Branding/frame
    if hv:
        c.setStrokeColor(colors.white)
        c.setLineWidth(3)
    elif bw:
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
    else:
        c.setStrokeColor(colors.HexColor("#31A8A0"))
        c.setLineWidth(2)
    c.roundRect(margin - 8, grid_y - 8, grid_w + 16, grid_h + 16, 10, stroke=1, fill=0)
    # Header
    if SHOW_HEADER_BANNER and (not hv):
        try:
            hero_path, _ = _theme_art_paths(book_key, themes_root)
        except Exception:
            hero_path = None
        draw_header(c, book_title, hero_path)
    elif not hv:
        c.setFillColor(colors.black if bw else colors.HexColor("#31A8A0"))
        c.setFont(HEADLINE_BOLD, 14)
        tw = c.stringWidth(book_title, HEADLINE_BOLD, 14)
        c.drawString((width - tw) / 2, height - margin - 2, book_title)

    for r in range(rows):
        for k in range(cols):
            idx = r * cols + k
            label = items[idx] if idx < len(items) else ""
            x = margin + k * cell_w
            y = margin + footer_clear + (rows - 1 - r) * cell_h

            # Cell background with row tints and special yes/no
            row_num = r + 1
            label_fg = colors.black
            hv = (not bw) and HIGH_VIS
            if hv and (label == "yes"):
                # Keep semantic colour plates with stronger contrast
                c.setFillColor(colors.HexColor("#4CAF50")); label_fg = colors.white
                c.setStrokeColor(colors.white if HV_STYLE == "black" else colors.HexColor("#333333")); c.setLineWidth(2)
                c.roundRect(x + 4, y + 4, cell_w - 8, cell_h - 8, 6, stroke=1, fill=1)
            elif hv and (label == "no"):
                c.setFillColor(colors.HexColor("#F44336")); label_fg = colors.white
                c.setStrokeColor(colors.white if HV_STYLE == "black" else colors.HexColor("#333333")); c.setLineWidth(2)
                c.roundRect(x + 4, y + 4, cell_w - 8, cell_h - 8, 6, stroke=1, fill=1)
            elif not bw and label == "yes":
                c.setFillColor(colors.HexColor("#4CAF50")); label_fg = colors.white
                c.setStrokeColor(colors.HexColor("#CCCCCC")); c.setLineWidth(1.5)
                c.roundRect(x + 4, y + 4, cell_w - 8, cell_h - 8, 6, stroke=1, fill=1)
            elif not bw and label == "no":
                c.setFillColor(colors.HexColor("#F44336")); label_fg = colors.white
                c.setStrokeColor(colors.HexColor("#CCCCCC")); c.setLineWidth(1.5)
                c.roundRect(x + 4, y + 4, cell_w - 8, cell_h - 8, 6, stroke=1, fill=1)
            else:
                # Default cells are white plates in all modes; high-vis uses high-contrast plates
                if hv:
                    if HV_STYLE == "black":
                        plate_fill = colors.HexColor("#FFD100")  # safety yellow
                        plate_stroke = colors.white
                        label_fg = colors.black
                    else:
                        plate_fill = colors.black
                        plate_stroke = colors.white
                        label_fg = colors.white
                    c.setFillColor(plate_fill)
                    c.setStrokeColor(plate_stroke)
                    c.setLineWidth(3)
                else:
                    c.setFillColor(colors.white)
                    c.setStrokeColor(colors.black if bw else colors.HexColor("#CCCCCC"))
                    c.setLineWidth(1.5)
                    label_fg = colors.black
                c.roundRect(x + 4, y + 4, cell_w - 8, cell_h - 8, 6, stroke=1, fill=1)

            # Adjust balance for High-Vis icons-only vs normal
            if hv:
                # Leave room for a larger text label beneath the icon
                img_h = (cell_h - 10) * 0.78
                inner_pad = 4
                label_h = (cell_h - 10) * 0.20
            else:
                img_h = (cell_h - 10) * 0.88
                inner_pad = 4
                label_h = (cell_h - 10) * 0.12
            img_w = (cell_w - 2 * inner_pad)
            img_x = x + inner_pad
            img_y = y + cell_h - 6 - img_h

            label_y = y + 5

            # Draw image if available
            if label:
                p = symbol_path_for(label, book_key, themes_root, core_root, symbols_png_root, global_aac_core, global_colours)
            else:
                p = None
            if p and p.exists():
                try:
                    im = _prepare_board_icon(p, bw=bw, high_vis=hv)
                    iw, ih = im.size
                    PAD = 2.0
                    scale = min((img_w - 2*PAD) / iw, (img_h - 2*PAD) / ih)
                    dw = iw * scale
                    dh = ih * scale
                    dx = img_x + (img_w - dw) / 2
                    dy = img_y + (img_h - dh) / 2
                    if hv and HV_HALO:
                        try:
                            sw, sh = max(1, int(dw)), max(1, int(dh))
                            rim = im.resize((sw, sh), Image.LANCZOS)
                            # Build a contrasting outline by dilating alpha
                            alpha = rim.split()[-1]
                            # Thicker outline for genuine high-visibility
                            dilated = alpha.filter(ImageFilter.MaxFilter(7))
                            if HV_STYLE == "black":
                                outline_color = (0, 0, 0, 255)  # black outline on yellow cells
                            else:
                                outline_color = (255, 255, 255, 255)  # white outline on black cells
                            halo = Image.new("RGBA", rim.size, outline_color)
                            halo.putalpha(dilated)
                            comp = Image.new("RGBA", rim.size, (0, 0, 0, 0))
                            comp.paste(halo, (0, 0), halo)
                            comp.paste(rim, (0, 0), rim)
                            buf = io.BytesIO(); comp.save(buf, format="PNG"); buf.seek(0)
                            c.drawImage(ImageReader(buf), dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
                        except Exception:
                            buf = io.BytesIO(); im.save(buf, format="PNG"); buf.seek(0)
                            c.drawImage(ImageReader(buf), dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
                    else:
                        buf = io.BytesIO(); im.save(buf, format="PNG"); buf.seek(0)
                        c.drawImage(ImageReader(buf), dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
                except Exception:
                    # Fallback: no image
                    pass

            # Draw label (HV obeys HV_LABELS)
            if (not hv) or (hv and HV_LABELS):
                # Choose label colour for HV for readability on high-contrast plate
                if hv and label not in ("yes", "no"):
                    label_fg = colors.white if HV_STYLE == "yellow" else colors.black
                c.setFillColor(label_fg)
                text = label.replace("_", " ") if label else ""
                if label == "dont_like":
                    text = "don't like"
                elif label == "dont_know":
                    text = "I don't know"
                elif label == "uh_oh":
                    text = "uh oh"
                elif label == "what_next":
                    text = "what next"
                elif label in ("I", "i"):
                    text = "I / me"
                # High-vis gets the largest label that fits the cell width
                max_fs = 18 if hv else 12
                FS = 12
                for fs in range(max_fs, 9, -1):
                    c.setFont(FONT_BOLD, fs)
                    if c.stringWidth(text, FONT_BOLD, fs) <= cell_w - 10:
                        FS = fs
                        break
                c.setFont(FONT_BOLD, FS)
                tw = c.stringWidth(text, FONT_BOLD, FS)
                c.drawString(x + (cell_w - tw) / 2, label_y + max(0, (label_h - FS) / 2) + 2, text)
    # Footer: always draw (including HV), with standardized top line
    tl = None
    if isinstance(pack_code, str) and pack_code.strip():
        tl = f"AAC Communication Board | {pack_code.strip()}"
    draw_footer(c, top_line=tl, page_text=page_text, bw=bw)


def _assemble_items_for_book_locked(book_key: str, themes_root: Path, rows: int, cols: int) -> Optional[List[str]]:
    """If assets/themes/<book_key>/icon_lock.json exists, build the 36-cell
    list in the exact locked order (JSON preserves insertion order).

    The file is expected to contain at least rows*cols keys in order mapping
    labels -> paths. We normalise labels to use underscores.
    """
    try:
        p = themes_root / book_key / "icon_lock.json"
        if not p.exists():
            return None
        data = load_json(p)
        if not isinstance(data, dict):
            return None
        seq: List[str] = []
        for k in data.keys():
            lbl = str(k).strip().lower().replace(" ", "_")
            seq.append(lbl)
            if len(seq) >= rows * cols:
                break
        if len(seq) < rows * cols:
            # Not enough entries to fully lock — ignore
            return None
        return seq[: rows * cols]
    except Exception:
        return None


def assemble_items_for_book(book: dict, *, prefer_locked: bool = False, book_key: str | None = None, themes_root: Path | None = None, rows: int = 6, cols: int = 6) -> List[str]:
    # Prefer locked sequence if requested and available
    if prefer_locked and book_key and themes_root is not None:
        seq = _assemble_items_for_book_locked(book_key, themes_root, rows, cols)
        if seq:
            return seq
    items: List[str] = []
    # Rows 1-2 core (new layout)
    for row in CORE_ROWS:
        items.extend(row)
    # Rows 3-4: book-specific fringe words
    # Priority 1: use fringe_12 from new vocab format (hero already in slot 0)
    book_words: List[str] = []
    if book.get("fringe_12"):
        book_words = [w.replace(" ", "_") for w in book.get("fringe_12", []) if w]
    else:
        # Legacy: activity_images + aac_extras + hero from characters
        book_words.extend([w.replace(" ", "_") for w in book.get("activity_images", [])])
        book_words.extend([w.replace(" ", "_") for w in book.get("aac_extras", [])])
        # Hero: check hero dict first (new format), then characters list (old format)
        try:
            hero_dict = book.get("hero", {})
            hero = ""
            if hero_dict and isinstance(hero_dict, dict):
                hero = hero_dict.get("name", "").strip().replace(" ", "_")
            if not hero:
                chars = book.get("characters", []) or []
                if isinstance(chars, list) and len(chars) > 0:
                    hero = str(chars[0]).strip().replace(" ", "_")
            if hero and hero not in book_words:
                book_words.insert(0, hero)
        except Exception:
            pass

    # Build a seen set to avoid duplicates with fixed rows
    fixed_words: List[str] = []
    for row in CORE_ROWS:
        fixed_words.extend(row)
    fixed_words.extend(BOTTOM_ROW)
    seen = set(fixed_words)

    # Deduplicate book words against seen and within themselves
    unique_book: List[str] = []
    for w in book_words:
        if not w:
            continue
        if w in seen:
            continue
        if w in unique_book:
            continue
        unique_book.append(w)
        if len(unique_book) >= 12:
            break

    # Pad to 12
    if len(unique_book) < 12:
        unique_book += [""] * (12 - len(unique_book))

    # Rows 3-4 from unique_book
    items.extend(unique_book[:6])   # Row 3
    items.extend(unique_book[6:12]) # Row 4

    # Update seen with the ones we just added
    for w in unique_book:
        if w:
            seen.add(w)

    # Row 5: suggested utility words minus anything already used
    row5_candidates = [w for w in ROW5_ROW if w not in seen]
    row5 = (row5_candidates + [""] * 6)[:6]
    items.extend(row5)

    # Row 6: fixed bottom row order
    items.extend(BOTTOM_ROW)
    return items


def assemble_items_for_book_windsurf(book: dict) -> List[str]:
    # Build candidate book words (fringe pool): activity_images first, then aac_extras
    book_words: List[str] = []
    book_words.extend([w.replace(" ", "_") for w in book.get("activity_images", [])])
    book_words.extend([w.replace(" ", "_") for w in book.get("aac_extras", [])])
    # Optionally front-load hero character as a fringe candidate
    try:
        chars = book.get("characters", []) or []
        if isinstance(chars, list) and len(chars) > 0:
            hero = str(chars[0]).strip().replace(" ", "_")
            if hero:
                book_words.insert(0, hero)
    except Exception:
        pass

    # Seen set to avoid duplicates with fixed cells
    fixed_words: List[str] = []
    for row in WINDSURF_CORE_ROWS:
        fixed_words.extend(row)
    fixed_words.extend(WINDSURF_ZONE_D)
    seen = set(fixed_words)

    # Deduplicate/select up to 12 fringe words
    unique_fringe: List[str] = []
    for w in book_words:
        if not w:
            continue
        if w in seen or w in unique_fringe:
            continue
        unique_fringe.append(w)
        if len(unique_fringe) >= 12:
            break
    if len(unique_fringe) < 12:
        unique_fringe += [""] * (12 - len(unique_fringe))

    # AI slots (3): support either list[str] or list[{word:...}]; fallback to first 3 aac_extras
    def _ai_slots_from_book(b: dict) -> List[str]:
        slots = b.get("ai_slots") or b.get("ai_emotion_slots") or []
        out: List[str] = []
        if isinstance(slots, list) and slots:
            if isinstance(slots[0], dict):
                for d in slots:
                    try:
                        w = str(d.get("word", "")).strip().replace(" ", "_")
                        if w:
                            out.append(w)
                    except Exception:
                        continue
            else:
                for s in slots:
                    try:
                        w = str(s).strip().replace(" ", "_")
                        if w:
                            out.append(w)
                    except Exception:
                        continue
        if not out:
            out = [w.replace(" ", "_") for w in (book.get("aac_extras", [])[:3] or [])]
        out = (out + ["", "", ""])[:3]
        return out

    ai_row = _ai_slots_from_book(book)

    # Build 6×6 grid in row-major order
    items: List[str] = []
    # Prepare fringe slices for rows 1–4
    fr_rows = [unique_fringe[i*3:(i+1)*3] for i in range(4)]
    for r in range(6):
        # Start row template with 6 empties
        row_items = ["", "", "", "", "", ""]
        # Zone A core for this row
        row_items[0:3] = WINDSURF_CORE_ROWS[r]
        # Right zone per row
        if r <= 3:
            row_items[3:6] = fr_rows[r]
        elif r == 4:
            row_items[3:6] = ai_row
        else:  # r == 5
            row_items[3:6] = WINDSURF_ZONE_D
        items.extend(row_items)
    return items


def draw_comm_strips(c: canvas.Canvas, book_key: str, book_title: str, themes_root: Path, core_root: Path, symbols_png_root: Path, global_aac_core: Path, global_colours: Path, bw: bool):
    width, height = c._pagesize
    margin = 36
    header_clear = 48 if SHOW_HEADER_BANNER else 14
    inner_w = width - 2 * margin
    inner_h = height - 2 * margin - header_clear
    strips = [
        ["I", "want", "more", "help", "finished", "go"],
        ["yes", "no", "like", "dont_like", "finished", "dont_know"],
        ["what", "where", "why", "choose", "colour", "read"],
        ["look", "see", "same", "different", "think", "what_next"],
        ["uh_oh", "you", "want", "help", "finished", "dont_know"],
        ["what_next", "go", "more", "help", "dont_know", "finished"],
    ]
    strip_h = inner_h / 6.0
    cell_w = inner_w / 6.0
    # Optional outer frame
    c.setStrokeColor(colors.HexColor("#31A8A0"))
    c.setLineWidth(2)
    c.roundRect(margin - 8, margin - 8, inner_w + 16, inner_h + 16, 10, stroke=1, fill=0)
    # Header
    if SHOW_HEADER_BANNER:
        draw_header(c, book_title)
    else:
        c.setFillColor(colors.HexColor("#31A8A0"))
        c.setFont(HEADLINE_BOLD, 14)
        tw = c.stringWidth(book_title, HEADLINE_BOLD, 14)
        c.drawString((width - tw) / 2, height - margin - 2, book_title)
    for si, strip in enumerate(strips):
        y = margin + (6 - 1 - si) * strip_h
        for ci, label in enumerate(strip):
            x = margin + ci * cell_w
            # Background with optional High-Vis mode
            hv = (not bw) and HIGH_VIS
            label_fg = colors.black
            if not bw and label == "yes":
                c.setFillColor(colors.HexColor("#4CAF50")); label_fg = colors.white
                c.setStrokeColor(colors.HexColor("#CCCCCC")); c.setLineWidth(1.5)
                c.roundRect(x + 4, y + 4, cell_w - 8, strip_h - 8, 6, stroke=1, fill=1)
            elif not bw and label == "no":
                c.setFillColor(colors.HexColor("#F44336")); label_fg = colors.white
                c.setStrokeColor(colors.HexColor("#CCCCCC")); c.setLineWidth(1.5)
                c.roundRect(x + 4, y + 4, cell_w - 8, strip_h - 8, 6, stroke=1, fill=1)
            elif hv:
                c.setFillColor(colors.HexColor("#FFEB3B"))
                c.setStrokeColor(colors.HexColor("#FFEB3B"))
                c.roundRect(x + 2, y + 2, cell_w - 4, strip_h - 4, 8, stroke=0, fill=1)
                c.setFillColor(colors.white)
                c.setStrokeColor(colors.HexColor("#CCCCCC")); c.setLineWidth(1.5)
                c.roundRect(x + 6, y + 6, cell_w - 12, strip_h - 12, 6, stroke=1, fill=1)
            else:
                c.setFillColor(colors.white if bw else colors.HexColor("#EBF5FF"))
                c.setStrokeColor(colors.HexColor("#CCCCCC")); c.setLineWidth(1.5)
                c.roundRect(x + 4, y + 4, cell_w - 8, strip_h - 8, 6, stroke=1, fill=1)
            # Image area prioritizing icon size
            img_h = (strip_h - 12) * 0.75
            inner_pad = 12 if ((not bw) and HIGH_VIS and label not in ("yes", "no")) else 6
            img_w = (cell_w - 2 * inner_pad)
            img_x = x + inner_pad
            img_y = y + strip_h - 6 - img_h
            p = symbol_path_for(label, book_key, themes_root, core_root, symbols_png_root, global_aac_core, global_colours)
            if p and p.exists():
                try:
                    ir = ImageReader(str(p))
                    iw, ih = ir.getSize()
                    # Add padding factor to reduce perceived clipping
                    PAD = 3.0
                    scale = min((img_w - 2*PAD) / iw, (img_h - 2*PAD) / ih)
                    dw = iw * scale
                    dh = ih * scale
                    dx = img_x + (img_w - dw) / 2
                    dy = img_y + (img_h - dh) / 2
                    c.drawImage(str(p), dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
                except Exception:
                    pass
            # Label area
            c.setFillColor(label_fg)
            c.setFont(FONT_BOLD, 11)
            text = label.replace("_", " ")
            tw = c.stringWidth(text, FONT_BOLD, 11)
            c.drawString(x + (cell_w - tw) / 2, y + (8 if ((not bw) and HIGH_VIS and label not in ("yes", "no")) else 6) + ((strip_h - 12) * 0.25 - 11) / 2, text)
    draw_footer(c, bw=bw)


def audit_missing_for_book(book_key: str, book: dict, themes_root: Path, core_root: Path, symbols_png_root: Path, global_aac_core: Path, global_colours: Path) -> List[str]:
    items = assemble_items_for_book(book, prefer_locked=True, book_key=book_key, themes_root=themes_root)
    missing: List[str] = []
    for lbl in items:
        if not lbl:
            continue
        p = symbol_path_for(lbl, book_key, themes_root, core_root, symbols_png_root, global_aac_core, global_colours)
        if not p or not p.exists():
            if lbl not in missing:
                missing.append(lbl)
    return missing


def export_missing_csv(csv_path: Path, selected_books: List[str], vocab: dict, themes_root: Path, core_root: Path, symbols_png_root: Path, global_aac_core: Path, global_colours: Path) -> None:
    rows = []
    for key in selected_books:
        if key not in vocab:
            continue
        book = vocab[key]
        missing = audit_missing_for_book(key, book, themes_root, core_root, symbols_png_root, global_aac_core, global_colours)
        # Hero character suggestion (first from book['characters'] if present)
        hero_label = ""
        try:
            chars = book.get("characters", []) or []
            if isinstance(chars, list) and len(chars) > 0:
                hero_label = str(chars[0]).strip().replace(" ", "_")
        except Exception:
            hero_label = ""
        hero_folder = f"themes/{key}/characters"
        for lbl in missing:
            alts = ", ".join(_alt_names(lbl))
            degs = ", ".join(_degrade_candidates(lbl))
            # Human-readable display label
            disp = lbl.replace("_", " ")
            if lbl == "dont_like":
                disp = "don't like"
            elif lbl == "dont_know":
                disp = "I don't know"
            elif lbl == "uh_oh":
                disp = "uh oh"
            elif lbl == "what_next":
                disp = "what next"
            rows.append({
                "book_key": key,
                "book_code": book.get("code", ""),
                "book_title": book.get("title", ""),
                "label_required": lbl,
                "label_display": disp,
                "acceptable_file_names": alts,
                "degrade_candidates": degs,
                "recommended_filename": lbl,
                "preferred_folder": "assets/symbols/png/alpha",
                "hero_label": hero_label,
                "hero_display_name": (book.get("characters", [""])[0] if (book.get("characters") and isinstance(book.get("characters"), list) and len(book.get("characters"))>0) else ""),
                "hero_recommended_filename": (hero_label if hero_label else ""),
                "hero_preferred_folder": hero_folder,
                "hero_icon_path": "",
            })
    ensure = csv_path.parent
    ensure.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "book_key","book_code","book_title",
            "label_required","label_display","acceptable_file_names","degrade_candidates","recommended_filename","preferred_folder",
            "hero_label","hero_display_name","hero_recommended_filename","hero_preferred_folder","hero_icon_path"
        ])
        w.writeheader()
        for r in rows:
            w.writerow(r)


def apply_mapping_csv(csv_path: Path, themes_root: Path) -> None:
    if not csv_path.exists():
        return
    by_book: dict = {}
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            bk = (row.get("book_key") or "").strip()
            lbl = (row.get("label") or row.get("label_required") or "").strip()
            pth = (row.get("icon_path") or row.get("path") or "").strip()
            if not bk or not lbl or not pth:
                # Check hero mapping if present on the row
                hero_lbl = (row.get("hero_label") or "").strip()
                hero_pth = (row.get("hero_icon_path") or "").strip()
                if bk and hero_lbl and hero_pth:
                    by_book.setdefault(bk, []).append((hero_lbl, hero_pth))
                continue
            by_book.setdefault(bk, []).append((lbl, pth))
            # Also capture hero on the same row if provided
            hero_lbl = (row.get("hero_label") or "").strip()
            hero_pth = (row.get("hero_icon_path") or "").strip()
            if bk and hero_lbl and hero_pth:
                by_book.setdefault(bk, []).append((hero_lbl, hero_pth))
    for bk, pairs in by_book.items():
        book_dir = themes_root / bk
        book_dir.mkdir(parents=True, exist_ok=True)
        smap = book_dir / "symbol_map.json"
        data = {}
        if smap.exists():
            try:
                data = load_json(smap)
            except Exception:
                data = {}
        for lbl, pth in pairs:
            data[lbl] = pth
        with open(smap, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    ap = argparse.ArgumentParser(description="Generate AAC literacy chat boards.")
    ap.add_argument("--vocab", default=str(DEFAULT_VOCAB))
    ap.add_argument("--themes-root", default=str(DEFAULT_THEMES_ROOT))
    ap.add_argument("--core", default=str(DEFAULT_CORE))
    ap.add_argument("--symbols-png", default=str(DEFAULT_SYMBOLS_PNG))
    ap.add_argument("--global-aac-core", default=str(DEFAULT_GLOBAL_AAC_CORE))
    ap.add_argument("--global-colours", default=str(DEFAULT_GLOBAL_COLOURS))
    ap.add_argument("--high-vis", action="store_true", help="High-visibility mode for print accessibility")
    ap.add_argument("--high-vis-style", default="black", choices=["black", "yellow"], help="HV background style")
    ap.add_argument("--high-vis-labels", default="on", choices=["on", "off"], help="Show labels in HV mode")
    ap.add_argument("--high-vis-halo", default="on", choices=["on", "off"], help="White halo around icons in HV mode")
    ap.add_argument("--no-cover", action="store_true", help="Skip teacher cover page — board only with Page 1/1")
    ap.add_argument("--audit", action="store_true", help="Audit icon coverage per book and skip PDF generation")
    ap.add_argument("--export-missing-csv", help="Write CSV of missing icons for selected books and exit")
    ap.add_argument("--apply-mapping-csv", help="CSV with columns: book_key,label,icon_path to update per-book symbol_map.json")
    ap.add_argument("--book", help="Book key to generate")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--rows", type=int, default=6)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--page-size", default="LETTER", choices=["A4", "LETTER"])
    ap.add_argument("--windsurf", action="store_true", help="Generate using Windsurf Zone A/B/C/D spec layout")
    ap.add_argument("--compare-windsurf", action="store_true", help="Generate both current BoardReady and Windsurf spec variants for comparison")
    ap.add_argument("--no-accent-strip", action="store_true", help="Hide teal header banner on board/strips pages to increase grid height")
    ap.add_argument("--pack-code", help="Override pack code for outputs and footer")
    args = ap.parse_args()

    vocab = load_json(Path(args.vocab))
    themes_root = Path(args.themes_root)
    core_root = Path(args.core)
    symbols_png_root = Path(args.symbols_png)
    global_aac_core = Path(args.global_aac_core)
    global_colours = Path(args.global_colours)

    # Repo-relative fallbacks if needed
    if not themes_root.exists():
        alt = Path(__file__).resolve().parents[2] / "assets" / "themes"
        if alt.exists():
            themes_root = alt
    if not core_root.exists():
        altc = Path(__file__).resolve().parents[2] / "assets" / "symbols" / "core"
        if altc.exists():
            core_root = altc
    if not symbols_png_root.exists():
        alts = Path(__file__).resolve().parents[2] / "assets" / "symbols" / "png"
        if alts.exists():
            symbols_png_root = alts

    # Fallbacks for global icon roots
    if not global_aac_core.exists():
        altg = Path(__file__).resolve().parents[2] / "assets" / "global" / "aac_core"
        if altg.exists():
            global_aac_core = altg
    if not global_colours.exists():
        altc2 = Path(__file__).resolve().parents[2] / "assets" / "global" / "colours"
        if altc2.exists():
            global_colours = altc2

    if not args.all and not args.book:
        ap.error("Specify --book <key> or --all")

    books = [args.book] if args.book else list(vocab.keys())
    page_size = choose_pagesize(args.page_size)
    cover_size = choose_cover_pagesize(args.page_size)

    # toggle high-visibility mode
    global HIGH_VIS
    HIGH_VIS = bool(getattr(args, "high_vis", False))
    # toggle header banner visibility
    global SHOW_HEADER_BANNER
    SHOW_HEADER_BANNER = not bool(getattr(args, "no_accent_strip", False))
    # high-visibility configuration
    global HV_STYLE, HV_LABELS, HV_HALO
    HV_STYLE = str(getattr(args, "high_vis_style", "black")).lower()
    HV_LABELS = str(getattr(args, "high_vis_labels", "on")).lower() == "on"
    HV_HALO = str(getattr(args, "high_vis_halo", "on")).lower() == "on"
    # skip cover page (board-only output with Page 1/1)
    global NO_COVER
    NO_COVER = bool(getattr(args, "no_cover", False))

    if getattr(args, "apply_mapping_csv", None):
        apply_mapping_csv(Path(args.apply_mapping_csv), themes_root)

    if getattr(args, "export_missing_csv", None):
        export_missing_csv(Path(args.export_missing_csv), books, vocab, themes_root, core_root, symbols_png_root, global_aac_core, global_colours)
        print(f"Wrote missing CSV to {args.export_missing_csv}")
        return

    for key in books:
        if key not in vocab:
            print(f"[WARN] Unknown book key: {key}")
            continue
        book = vocab[key]
        book_code = (getattr(args, "pack_code", None) or book.get("code") or (key[:3].upper() + "1"))
        # Write outputs to Studioforge/OUTPUT/<pack_code> for consistency with other activities
        repo_root = Path(__file__).resolve().parents[2]
        out_dir = repo_root / "Studioforge" / "OUTPUT" / book_code
        out_dir.mkdir(parents=True, exist_ok=True)

        if getattr(args, "audit", False):
            missing = audit_missing_for_book(key, book, themes_root, core_root, symbols_png_root, global_aac_core, global_colours)
            if missing:
                print(f"[MISSING] {book_code} {book['title']}: {', '.join(missing)}")
            else:
                print(f"[OK] {book_code} {book['title']}: all icons resolved")
            continue

        def _ensure_len(lst: List[str]) -> List[str]:
            needed = args.rows * args.cols
            if len(lst) < needed:
                return lst + [""] * (needed - len(lst))
            return lst[:needed]

        if getattr(args, "compare_windsurf", False):
            items_br = _ensure_len(assemble_items_for_book(book, prefer_locked=True, book_key=key, themes_root=themes_root, rows=args.rows, cols=args.cols))
            items_ws = _ensure_len(assemble_items_for_book_windsurf(book))

            # COLOR variants
            color_suffix = ("_HIGHVIS_" + HV_STYLE.upper()) if HIGH_VIS else ""
            out_pdf_br = out_dir / f"{book_code}_AAC_Board_BR_COLOR{color_suffix}.pdf"
            c = canvas.Canvas(str(out_pdf_br), pagesize=page_size)
            cov = _make_cover_image(key, book["title"], themes_root, page_count=None, book_code=book_code)
            had_cover = cov is not None
            if had_cover:
                # True portrait cover page
                c.setPageSize(cover_size)
                pw, ph = cover_size
                iw, ih = getattr(cov, 'size', (pw, ph))
                scale = min(pw / max(1, iw), ph / max(1, ih))
                dw, dh = iw * scale, ih * scale
                dx, dy = (pw - dw) / 2.0, (ph - dh) / 2.0
                buf = io.BytesIO(); cov.save(buf, format="PNG"); buf.seek(0)
                c.drawImage(ImageReader(buf), dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
                c.showPage()
                # Switch back to landscape for board pages
                c.setPageSize(page_size)
            page_text = "Page 2/2" if had_cover else "Page 1/1"
            draw_board(c, args.rows, args.cols, items_br, key, book["title"], themes_root, core_root, symbols_png_root, global_aac_core, global_colours, bw=False, pack_code=book_code, page_text=page_text)
            c.save()
            print(f"Wrote {out_pdf_br}")

            out_pdf_ws = out_dir / f"{book_code}_AAC_Board_WS_COLOR{color_suffix}.pdf"
            c3 = canvas.Canvas(str(out_pdf_ws), pagesize=page_size)
            cov = _make_cover_image(key, book["title"], themes_root, page_count=None, book_code=book_code)
            had_cover = cov is not None
            if had_cover:
                c3.setPageSize(cover_size)
                pw, ph = cover_size
                iw, ih = getattr(cov, 'size', (pw, ph))
                scale = min(pw / max(1, iw), ph / max(1, ih))
                dw, dh = iw * scale, ih * scale
                dx, dy = (pw - dw) / 2.0, (ph - dh) / 2.0
                buf = io.BytesIO(); cov.save(buf, format="PNG"); buf.seek(0)
                c3.drawImage(ImageReader(buf), dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
                c3.showPage()
                c3.setPageSize(page_size)
            page_text = "Page 2/2" if had_cover else "Page 1/1"
            draw_board(c3, args.rows, args.cols, items_ws, key, book["title"], themes_root, core_root, symbols_png_root, global_aac_core, global_colours, bw=False, pack_code=book_code, page_text=page_text)
            c3.save()
            print(f"Wrote {out_pdf_ws}")

            # B&W variants
            out_pdf_br_bw = out_dir / f"{book_code}_AAC_Board_BR_BW.pdf"
            c4 = canvas.Canvas(str(out_pdf_br_bw), pagesize=page_size)
            cov = _make_cover_image(key, book["title"], themes_root, page_count=None, book_code=book_code)
            had_cover = cov is not None
            if had_cover:
                # grayscale for B&W
                cov_bw = cov.convert('L') if hasattr(cov, 'convert') else None
                c4.setPageSize(cover_size)
                pw, ph = cover_size
                iw, ih = getattr(cov_bw or cov, 'size', (pw, ph))
                scale = min(pw / max(1, iw), ph / max(1, ih))
                dw, dh = iw * scale, ih * scale
                dx, dy = (pw - dw) / 2.0, (ph - dh) / 2.0
                buf = io.BytesIO(); (cov_bw or cov).save(buf, format="PNG"); buf.seek(0)
                c4.drawImage(ImageReader(buf), dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
                c4.showPage()
                c4.setPageSize(page_size)
            page_text = "Page 2/2" if had_cover else "Page 1/1"
            draw_board(c4, args.rows, args.cols, items_br, key, book["title"], themes_root, core_root, symbols_png_root, global_aac_core, global_colours, bw=True, pack_code=book_code, page_text=page_text)
            c4.save()
            print(f"Wrote {out_pdf_br_bw}")

            out_pdf_ws_bw = out_dir / f"{book_code}_AAC_Board_WS_BW.pdf"
            c5 = canvas.Canvas(str(out_pdf_ws_bw), pagesize=page_size)
            cov = _make_cover_image(key, book["title"], themes_root, page_count=None, book_code=book_code)
            had_cover = cov is not None
            if had_cover:
                cov_bw = cov.convert('L') if hasattr(cov, 'convert') else None
                c5.setPageSize(cover_size)
                pw, ph = cover_size
                iw, ih = getattr(cov_bw or cov, 'size', (pw, ph))
                scale = min(pw / max(1, iw), ph / max(1, ih))
                dw, dh = iw * scale, ih * scale
                dx, dy = (pw - dw) / 2.0, (ph - dh) / 2.0
                buf = io.BytesIO(); (cov_bw or cov).save(buf, format="PNG"); buf.seek(0)
                c5.drawImage(ImageReader(buf), dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
                c5.showPage()
                c5.setPageSize(page_size)
            page_text = "Page 2/2" if had_cover else "Page 1/1"
            draw_board(c5, args.rows, args.cols, items_ws, key, book["title"], themes_root, core_root, symbols_png_root, global_aac_core, global_colours, bw=True, pack_code=book_code, page_text=page_text)
            c5.save()
            print(f"Wrote {out_pdf_ws_bw}")
            continue

        if getattr(args, "windsurf", False):
            items = _ensure_len(assemble_items_for_book_windsurf(book))
            color_suffix = ("_HIGHVIS_" + HV_STYLE.upper()) if HIGH_VIS else ""
            out_pdf = out_dir / f"{book_code}_AAC_Board_WS_COLOR{color_suffix}.pdf"
            c = canvas.Canvas(str(out_pdf), pagesize=page_size)
            cov = _make_cover_image(key, book["title"], themes_root, page_count=None, book_code=book_code)
            had_cover = cov is not None
            if had_cover:
                buf = io.BytesIO(); cov.save(buf, format="PNG"); buf.seek(0)
                c.drawImage(ImageReader(buf), 0, 0, width=page_size[0], height=page_size[1])
                c.showPage()
            page_text = "Page 2/2" if had_cover else "Page 1/1"
            draw_board(c, args.rows, args.cols, items, key, book["title"], themes_root, core_root, symbols_png_root, global_aac_core, global_colours, bw=False, pack_code=book_code, page_text=page_text)
            c.save()
            print(f"Wrote {out_pdf}")

            out_pdf_bw = out_dir / f"{book_code}_AAC_Board_WS_BW.pdf"
            c2 = canvas.Canvas(str(out_pdf_bw), pagesize=page_size)
            cov = _make_cover_image(key, book["title"], themes_root, page_count=None, book_code=book_code)
            had_cover = cov is not None
            if had_cover:
                cov_bw = cov.convert('L') if hasattr(cov, 'convert') else None
                buf = io.BytesIO(); (cov_bw or cov).save(buf, format="PNG"); buf.seek(0)
                c2.drawImage(ImageReader(buf), 0, 0, width=page_size[0], height=page_size[1])
                c2.showPage()
            page_text = "Page 2/2" if had_cover else "Page 1/1"
            draw_board(c2, args.rows, args.cols, items, key, book["title"], themes_root, core_root, symbols_png_root, global_aac_core, global_colours, bw=True, pack_code=book_code, page_text=page_text)
            c2.save()
            print(f"Wrote {out_pdf_bw}")
            continue

        # Default: current BoardReady layout (prefer locked sequence if available)
        items = _ensure_len(assemble_items_for_book(book, prefer_locked=True, book_key=key, themes_root=themes_root, rows=args.rows, cols=args.cols))
        color_suffix = ("_HIGHVIS_" + HV_STYLE.upper()) if HIGH_VIS else ""
        out_pdf = out_dir / f"{book_code}_AAC_Board_COLOR{color_suffix}.pdf"
        c = canvas.Canvas(str(out_pdf), pagesize=page_size)
        cov = _make_cover_image(key, book["title"], themes_root, page_count=None, book_code=book_code)
        had_cover = cov is not None
        if had_cover:
            c.setPageSize(cover_size)
            pw, ph = cover_size
            iw, ih = getattr(cov, 'size', (pw, ph))
            scale = min(pw / max(1, iw), ph / max(1, ih))
            dw, dh = iw * scale, ih * scale
            dx, dy = (pw - dw) / 2.0, (ph - dh) / 2.0
            buf = io.BytesIO(); cov.save(buf, format="PNG"); buf.seek(0)
            c.drawImage(ImageReader(buf), dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
            c.showPage()
            c.setPageSize(page_size)
        page_text = "Page 2/2" if had_cover else "Page 1/1"
        draw_board(c, args.rows, args.cols, items, key, book["title"], themes_root, core_root, symbols_png_root, global_aac_core, global_colours, bw=False, pack_code=book_code, page_text=page_text)
        c.save()
        print(f"Wrote {out_pdf}")

        out_pdf_bw = out_dir / f"{book_code}_AAC_Board_BW.pdf"
        c2 = canvas.Canvas(str(out_pdf_bw), pagesize=page_size)
        cov = _make_cover_image(key, book["title"], themes_root, page_count=None, book_code=book_code)
        had_cover = cov is not None
        if had_cover:
            cov_bw = cov.convert('L') if hasattr(cov, 'convert') else None
            c2.setPageSize(cover_size)
            pw, ph = cover_size
            iw, ih = getattr(cov_bw or cov, 'size', (pw, ph))
            scale = min(pw / max(1, iw), ph / max(1, ih))
            dw, dh = iw * scale, ih * scale
            dx, dy = (pw - dw) / 2.0, (ph - dh) / 2.0
            buf = io.BytesIO(); (cov_bw or cov).save(buf, format="PNG"); buf.seek(0)
            c2.drawImage(ImageReader(buf), dx, dy, width=dw, height=dh, preserveAspectRatio=True, mask='auto')
            c2.showPage()
            c2.setPageSize(page_size)
        page_text = "Page 2/2" if had_cover else "Page 1/1"
        draw_board(c2, args.rows, args.cols, items, key, book["title"], themes_root, core_root, symbols_png_root, global_aac_core, global_colours, bw=True, pack_code=book_code, page_text=page_text)
        c2.save()
        print(f"Wrote {out_pdf_bw}")


if __name__ == "__main__":
    main()
