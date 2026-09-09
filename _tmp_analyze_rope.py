import sys, os
sys.path.insert(0, '.')
os.chdir('.')
from PIL import Image
import numpy as np

for name in ['yn', 'aac']:
    img = Image.open(f'_qa_{name}_rope.png').convert('RGB')
    arr = np.array(img)
    h, w = arr.shape[:2]
    print(f"\n=== {name} rope crop ({w}x{h}) ===")
    # Check for non-white pixels row by row (text/diagram content)
    # White is (255,255,255), near-white is >240
    non_white_rows = []
    for y in range(h):
        row = arr[y]
        non_white = np.sum(np.any(row < 240, axis=1))
        if non_white > 5:
            non_white_rows.append((y, non_white))
    if non_white_rows:
        print(f"  Content rows: {non_white_rows[0][0]} to {non_white_rows[-1][0]}")
        # Find gaps (empty rows between content)
        gaps = []
        for i in range(1, len(non_white_rows)):
            if non_white_rows[i][0] - non_white_rows[i-1][0] > 5:
                gaps.append((non_white_rows[i-1][0], non_white_rows[i][0]))
        if gaps:
            print(f"  Gaps (empty regions): {gaps[:5]}")
        # Check for colored (non-gray) pixels - the rope diagram has teal/blue colors
        colored_pixels = 0
        for y, cnt in non_white_rows:
            row = arr[y]
            # Colored = significant difference between R, G, B channels
            r, g, b = row[:, 0], row[:, 1], row[:, 2]
            colored = np.sum((np.abs(r.astype(int) - g.astype(int)) > 20) | (np.abs(g.astype(int) - b.astype(int)) > 20))
            colored_pixels += colored
        print(f"  Colored (non-gray) pixels: {colored_pixels}")
        if colored_pixels > 100:
            print(f"  -> Rope diagram likely PRESENT (colored content detected)")
        else:
            print(f"  -> Rope diagram likely MISSING (only text/gray content)")
    else:
        print(f"  No content found")
