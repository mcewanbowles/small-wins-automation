import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PIN_W = 1000
PIN_H = 1500

PURPLE = (112, 50, 255)
NAVY = (12, 35, 64)
TEAL = (0, 160, 170)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 214, 92)


@dataclass
class PinSpec:
    level: int
    src_path: Path
    out_path: Path
    headline: str
    subhead: str
    badges: list[str]
    accent: tuple[int, int, int] | None = None


def _try_load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if os.name == "nt":
        windir = os.environ.get("WINDIR", "C:\\Windows")
        candidates.extend(
            [
                Path(windir) / "Fonts" / ("arialbd.ttf" if bold else "arial.ttf"),
                Path(windir) / "Fonts" / ("calibrib.ttf" if bold else "calibri.ttf"),
            ]
        )
    candidates.extend(
        [
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf"),
        ]
    )

    for p in candidates:
        try:
            if p.exists():
                return ImageFont.truetype(str(p), size=size)
        except Exception:
            continue

    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def _fit_into(img: Image.Image, box_w: int, box_h: int) -> Image.Image:
    img = img.convert("RGBA")
    scale = min(box_w / img.width, box_h / img.height)
    new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
    return img.resize(new_size, Image.Resampling.LANCZOS)


def _mean_color(img: Image.Image) -> tuple[int, int, int]:
    img = img.convert("RGB")
    # Downsample to reduce cost.
    small = img.resize((64, 64), Image.Resampling.BILINEAR)
    pixels = list(small.getdata())
    r = sum(p[0] for p in pixels) / len(pixels)
    g = sum(p[1] for p in pixels) / len(pixels)
    b = sum(p[2] for p in pixels) / len(pixels)
    return (int(r), int(g), int(b))


def sample_level_accent(src_img: Image.Image) -> tuple[int, int, int]:
    """Sample a representative 'level color' from the source thumbnail.

    The Canva thumbnails have a strong background/header color at the top.
    We sample a small top-corner region to avoid most text.
    """

    img = src_img.convert("RGB")
    w, h = img.size
    # Sample a top-left patch that is usually mostly background.
    x0 = int(w * 0.02)
    y0 = int(h * 0.02)
    x1 = int(w * 0.18)
    y1 = int(h * 0.14)
    patch = img.crop((x0, y0, x1, y1))
    return _mean_color(patch)


def _white_to_transparent(frame_rgba: Image.Image, threshold: int = 245) -> Image.Image:
    """Treat near-white pixels as transparent so the middle 'window' shows the product image."""

    frame = frame_rgba.convert("RGBA")
    px = frame.load()
    w, h = frame.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if r >= threshold and g >= threshold and b >= threshold:
                px[x, y] = (r, g, b, 0)
    return frame


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_centered(draw: ImageDraw.ImageDraw, text: str, y: int, font: ImageFont.ImageFont, fill: tuple[int, int, int], w: int):
    tw, th = _text_size(draw, text, font)
    x = int((w - tw) / 2)
    draw.text((x, y), text, font=font, fill=fill)
    return th


def render_pin(spec: PinSpec) -> None:
    canvas = Image.new("RGB", (PIN_W, PIN_H), WHITE)
    draw = ImageDraw.Draw(canvas)

    header_h = 170
    accent = spec.accent or PURPLE
    draw.rectangle([0, 0, PIN_W, header_h], fill=accent)

    font_head = _try_load_font(78, bold=True)
    font_sub = _try_load_font(38, bold=True)
    font_badge = _try_load_font(32, bold=True)
    font_small = _try_load_font(26, bold=False)

    head_y = 18
    head_h = _draw_centered(draw, spec.headline, head_y, font_head, WHITE, PIN_W)
    _draw_centered(draw, spec.subhead, head_y + head_h + 10, font_sub, WHITE, PIN_W)

    img = Image.open(spec.src_path)
    img_fit = _fit_into(img, box_w=PIN_W - 120, box_h=PIN_H - header_h - 280)

    img_x = int((PIN_W - img_fit.width) / 2)
    img_y = header_h + 60
    canvas.paste(img_fit, (img_x, img_y), mask=img_fit)

    badge_y = PIN_H - 240
    badge_h = 74
    gap = 20
    x = 70

    for badge in spec.badges:
        tw, th = _text_size(draw, badge, font_badge)
        bw = min(PIN_W - 2 * 70, tw + 60)
        box = [x, badge_y, x + bw, badge_y + badge_h]

        draw.rounded_rectangle(box, radius=18, fill=accent, outline=NAVY, width=4)
        tx = x + int((bw - tw) / 2)
        ty = badge_y + int((badge_h - th) / 2) - 2
        draw.text((tx, ty), badge, font=font_badge, fill=WHITE)

        x = x + bw + gap
        if x > PIN_W - 250:
            badge_y += badge_h + 16
            x = 70

    cta_text = "Grab the FREE sampler on TpT"
    cta_tw, cta_th = _text_size(draw, cta_text, font_small)
    cta_w = min(PIN_W - 120, cta_tw + 80)
    cta_h = 62
    cta_x = int((PIN_W - cta_w) / 2)
    cta_y = PIN_H - 92

    draw.rounded_rectangle([cta_x, cta_y, cta_x + cta_w, cta_y + cta_h], radius=18, fill=YELLOW, outline=BLACK, width=3)
    draw.text((cta_x + int((cta_w - cta_tw) / 2), cta_y + int((cta_h - cta_th) / 2) - 1), cta_text, font=font_small, fill=BLACK)

    spec.out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(spec.out_path, format="PNG", optimize=True)


def render_pin_with_frame(
    *,
    src_image_path: Path,
    frame_path: Path,
    out_path: Path,
    placement: tuple[int, int, int, int],
) -> None:
    """Render a Pinterest pin by placing src image into a rectangle, then overlaying a Canva frame."""

    canvas = Image.new("RGB", (PIN_W, PIN_H), WHITE)

    src = Image.open(src_image_path).convert("RGBA")
    frame = Image.open(frame_path).convert("RGBA")

    # Normalize frame size to the Pinterest canvas.
    if frame.size != (PIN_W, PIN_H):
        frame = frame.resize((PIN_W, PIN_H), Image.Resampling.LANCZOS)

    # Most Canva exports here have a white 'window' rather than true transparency.
    # Make near-white pixels transparent so the product image shows through.
    frame = _white_to_transparent(frame)

    x, y, w, h = placement
    fitted = _fit_into(src, box_w=w, box_h=h)
    px = x + int((w - fitted.width) / 2)
    py = y + int((h - fitted.height) / 2)

    canvas.paste(fitted, (px, py), mask=fitted)
    canvas.paste(frame, (0, 0), mask=frame)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, format="PNG", optimize=True)


def discover_canva_level_thumbs(canva_dir: Path) -> dict[int, Path]:
    level_map: dict[int, Path] = {}
    if not canva_dir.exists():
        return level_map

    rx = re.compile(r"level\s*(\d)", re.IGNORECASE)

    for p in sorted(canva_dir.glob("*.png")):
        m = rx.search(p.stem)
        if not m:
            continue
        level = int(m.group(1))
        if 1 <= level <= 5:
            level_map[level] = p

    return level_map


def discover_frame_pngs(frames_dir: Path) -> list[Path]:
    if not frames_dir.exists():
        return []
    return sorted([p for p in frames_dir.glob("*.png") if p.is_file()])


def _safe_slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "frame"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--canva-dir",
        default=str(
            Path("production")
            / "final_products"
            / "brown_bear"
            / "matching"
            / "Canva Thumbnails"
        ),
    )
    parser.add_argument(
        "--frames-dir",
        default=str(
            Path("production")
            / "final_products"
            / "brown_bear"
            / "matching"
            / "pinterest frames"
        ),
    )
    parser.add_argument(
        "--out-dir",
        default=str(
            Path("production")
            / "marketing"
            / "brown_bear"
            / "matching"
            / "pins"
            / "auto"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "canva-overlay"],
        default="auto",
        help="auto = generate simple pins with text/badges; canva-overlay = use Canva frame PNG overlays",
    )
    parser.add_argument("--levels", default="1-5")
    parser.add_argument(
        "--placement",
        default="80,260,840,900",
        help="Placement rectangle for the product image when using canva-overlay: x,y,width,height",
    )

    args = parser.parse_args()

    canva_dir = Path(args.canva_dir)
    frames_dir = Path(args.frames_dir)
    out_dir = Path(args.out_dir)

    levels = []
    if "-" in args.levels:
        a, b = args.levels.split("-", 1)
        levels = list(range(int(a), int(b) + 1))
    else:
        levels = [int(x.strip()) for x in args.levels.split(",") if x.strip()]

    thumbs = discover_canva_level_thumbs(canva_dir)
    missing = [lvl for lvl in levels if lvl not in thumbs]
    if missing:
        raise SystemExit(
            "Missing Canva thumbnails for levels: "
            + ", ".join(str(x) for x in missing)
            + f". Expected filenames containing 'level#' in {canva_dir}"
        )

    if args.mode == "auto":
        for lvl in levels:
            src = thumbs[lvl]
            out_path = out_dir / f"brown_bear_matching_level{lvl}_pin_1000x1500.png"

            accent = sample_level_accent(Image.open(src))

            spec = PinSpec(
                level=lvl,
                src_path=src,
                out_path=out_path,
                headline="BROWN BEAR",
                subhead=f"MATCHING • LEVEL {lvl}",
                badges=["AAC", "SPED", "LOW PREP"],
                accent=accent,
            )
            render_pin(spec)

        print(f"OK Created pins in: {out_dir}")
        return 0

    # Canva overlay mode
    try:
        parts = [int(x.strip()) for x in str(args.placement).split(",")]
        if len(parts) != 4:
            raise ValueError
        placement = (parts[0], parts[1], parts[2], parts[3])
    except Exception:
        raise SystemExit("Invalid --placement. Expected: x,y,width,height")

    frames = discover_frame_pngs(frames_dir)
    if not frames:
        raise SystemExit(f"No frame PNGs found in: {frames_dir}")

    for frame_path in frames:
        frame_slug = _safe_slug(frame_path.stem)
        frame_out_dir = out_dir / frame_slug
        for lvl in levels:
            src = thumbs[lvl]
            out_path = frame_out_dir / f"brown_bear_matching_level{lvl}_pin_1000x1500.png"
            render_pin_with_frame(
                src_image_path=src,
                frame_path=frame_path,
                out_path=out_path,
                placement=placement,
            )

    print(f"OK Created Canva-overlay pins in: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
