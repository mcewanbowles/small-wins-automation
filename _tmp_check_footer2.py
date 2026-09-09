"""Check Adapted Book footer content presence after fix."""
import numpy as np
from PIL import Image
from pathlib import Path

qa_dir = Path('_qa_renders')

for p in [2, 3, 8]:
    img = Image.open(qa_dir / f'adapted_book_p{p}.png')
    arr = np.array(img.convert('RGB'))
    h, w = arr.shape[:2]
    print(f"\nPage {p} ({w}x{h}):")
    # Check the full footer area (bottom 10% of each pane)
    footer_y = int(0.88 * h)
    footer_h = int(0.10 * h)
    for pane_name, px_start, px_end in [('Left pane', 0, w//2), ('Right pane', w//2, w)]:
        footer_region = arr[footer_y:footer_y+footer_h, px_start:px_end]
        non_white = np.sum(np.any(footer_region < 230, axis=2))
        total = footer_region.shape[0] * footer_region.shape[1]
        pct = 100.0 * non_white / total
        print(f"  {pane_name}: {non_white}/{total} non-white ({pct:.1f}%)")
        # Check if text is centered (content should be in the middle portion)
        if non_white > 0:
            # Find the leftmost and rightmost non-white columns
            col_nonwhite = np.sum(np.any(footer_region < 230, axis=2), axis=0)
            nonzero_cols = np.where(col_nonwhite > 0)[0]
            if len(nonzero_cols) > 0:
                left_bound = nonzero_cols[0]
                right_bound = nonzero_cols[-1]
                pane_w = px_end - px_start
                print(f"    Content spans x={left_bound} to x={right_bound} (pane width={pane_w})")
                print(f"    Left margin: {left_bound}px, Right margin: {pane_w - right_bound}px")
