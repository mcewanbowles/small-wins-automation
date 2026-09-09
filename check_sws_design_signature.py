from __future__ import annotations

import inspect
from PIL import Image

import utils.sws_design as m

print("module:", m.__file__)
print("has shrink_font_to_fit_with_pt:", hasattr(m, "shrink_font_to_fit_with_pt"))
print("has generate_teacher_cover_page:", hasattr(m, "generate_teacher_cover_page"))
print("has generate_internal_cover_page:", hasattr(m, "generate_internal_cover_page"))
print("has safe_footer_inset_px:", hasattr(m, "safe_footer_inset_px"))

try:
    params = list(inspect.signature(m.apply_small_wins_frame).parameters.keys())
except Exception as e:
    params = [f"<error reading signature: {type(e).__name__}: {e}>"]
print("apply_small_wins_frame params:", params)

# Try a no-op call to verify signature compatibility (read-only; draws into a RAM image)
im = Image.new("RGB", (2550, 3300), "white")

# Baseline call
try:
    m.apply_small_wins_frame(
        im,
        product_title="Test",
        subtitle="Sub",
        pack_code="PK",
        page_num=1,
        total_pages=1,
        level=None,
        draw_footer=False,
    )
    print("baseline call: OK")
except Exception as e:
    print("baseline call: FAIL:", type(e).__name__, e)

# Optional arg compatibility
try:
    m.apply_small_wins_frame(
        im,
        product_title="Test",
        subtitle="Sub",
        pack_code="PK",
        page_num=1,
        total_pages=1,
        level=None,
        draw_footer=False,
        show_data_strip=False,
    )
    print("call with show_data_strip: OK")
except TypeError as e:
    print("call with show_data_strip TypeError:", e)
except Exception as e:
    print("call with show_data_strip other error:", type(e).__name__, e)
