"""Analyze rendered PDF pages for QA verification."""
import sys
from pathlib import Path
from PIL import Image
import numpy as np

def analyze_text_regions(img, regions, name):
    """Check for text content in specified regions."""
    arr = np.array(img.convert('RGB'))
    h, w = arr.shape[:2]
    print(f"\n=== {name} ({w}x{h}) ===")
    for label, (x1, y1, x2, y2) in regions.items():
        # Convert percentage coords to pixels
        px1, py1 = int(x1 * w), int(y1 * h)
        px2, py2 = int(x2 * w), int(y2 * h)
        region = arr[py1:py2, px1:px2]
        if region.size == 0:
            print(f"  {label}: empty region")
            continue
        non_white = np.sum(np.any(region < 230, axis=2))
        total = region.shape[0] * region.shape[1]
        pct = 100.0 * non_white / total
        print(f"  {label}: {non_white}/{total} non-white pixels ({pct:.1f}%)")

def find_text_overlap(img, y1_pct, y2_pct, name):
    """Check for content overlap in a horizontal band."""
    arr = np.array(img.convert('RGB'))
    h, w = arr.shape[:2]
    y1, y2 = int(y1_pct * h), int(y2_pct * h)
    band = arr[y1:y2, :]
    non_white_rows = []
    for y in range(band.shape[0]):
        row = band[y]
        non_white = np.sum(np.any(row < 230, axis=1))
        if non_white > 3:
            non_white_rows.append(y)
    if non_white_rows:
        print(f"  {name}: content from y={y1_pct:.3f} to y={y2_pct:.3f}: rows {non_white_rows[0]} to {non_white_rows[-1]}")
        # Find gaps
        gaps = []
        for i in range(1, len(non_white_rows)):
            if non_white_rows[i] - non_white_rows[i-1] > 3:
                gaps.append((non_white_rows[i-1], non_white_rows[i]))
        if gaps:
            print(f"    Gaps: {gaps[:3]}")
    else:
        print(f"  {name}: no content in band")

# 1. IEP Monitoring Form
print("=" * 60)
print("ITEM 1: IEP Monitoring Form")
print("=" * 60)
iep = Image.open('_qa_renders/iep_p1.png')
analyze_text_regions(iep, {
    'subtitle_area': (0.30, 0.04, 0.70, 0.08),
    'grid_header': (0.05, 0.20, 0.95, 0.25),
    'footer': (0.05, 0.92, 0.95, 0.98),
}, 'IEP Monitoring Form')

# 2. Yes/No Questions - check icon mapping
print("\n" + "=" * 60)
print("ITEM 2: Yes/No Questions icon mapping")
print("=" * 60)
for p in range(1, 6):
    img = Image.open(f'_qa_renders/yesno_p{p}.png')
    arr = np.array(img.convert('RGB'))
    h, w = arr.shape[:2]
    # Each page has 4 cards in 2x2 grid
    # Check for colored (icon) content in each card area
    print(f"\n  Page {p}:")
    for card_idx, (cx, cy) in enumerate([(0.18, 0.15), (0.55, 0.15), (0.18, 0.55), (0.55, 0.55)]):
        x1, y1 = int(cx * w), int(cy * h)
        x2, y2 = int((cx + 0.27) * w), int((cy + 0.27) * h)
        region = arr[y1:y2, x1:x2]
        if region.size == 0:
            continue
        # Count colored pixels (icons have color)
        r, g, b = region[:, :, 0], region[:, :, 1], region[:, :, 2]
        colored = np.sum((np.abs(r.astype(int) - g.astype(int)) > 15) | (np.abs(g.astype(int) - b.astype(int)) > 15))
        total = region.shape[0] * region.shape[1]
        pct = 100.0 * colored / total
        print(f"    Card {card_idx+1}: {colored}/{total} colored pixels ({pct:.1f}%)")

# 3. AAC Board footer
print("\n" + "=" * 60)
print("ITEM 4: AAC Board footer collision")
print("=" * 60)
for name, fname in [('COLOR', 'aac_color_p1.png'), ('HI-VIS BLACK', 'aac_hvblack_p1.png'), ('HI-VIS YELLOW', 'aac_hvyellow_p1.png')]:
    img = Image.open(f'_qa_renders/{fname}')
    analyze_text_regions(img, {
        'footer_top_line': (0.05, 0.88, 0.95, 0.93),
        'footer_bottom_line': (0.05, 0.93, 0.95, 0.98),
    }, f'AAC Board {name}')

# 4. Adapted Book footer
print("\n" + "=" * 60)
print("ITEM 6: Adapted Book footer clipping")
print("=" * 60)
for p in [2, 3, 8]:
    img = Image.open(f'_qa_renders/adapted_book_p{p}.png')
    arr = np.array(img.convert('RGB'))
    h, w = arr.shape[:2]
    print(f"\n  Page {p} ({w}x{h}):")
    # Check left and right edges of footer area
    footer_y = int(0.92 * h)
    footer_h = int(0.06 * h)
    # Left edge (first 5% should have PCS text)
    left_edge = arr[footer_y:footer_y+footer_h, :int(0.05*w)]
    # Right edge (last 5% should have Studio text)
    right_edge = arr[footer_y:footer_y+footer_h, int(0.95*w):]
    left_nonwhite = np.sum(np.any(left_edge < 230, axis=2))
    right_nonwhite = np.sum(np.any(right_edge < 230, axis=2))
    print(f"    Footer left edge: {left_nonwhite} non-white pixels")
    print(f"    Footer right edge: {right_nonwhite} non-white pixels")
    # Check if footer text is clipped (very few pixels at edges means clipping)
    if left_nonwhite < 5:
        print(f"    WARNING: Left footer may be clipped!")
    if right_nonwhite < 5:
        print(f"    WARNING: Right footer may be clipped!")
