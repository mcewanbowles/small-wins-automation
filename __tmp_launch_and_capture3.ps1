# Capture-only script: no process-killing, no launching.
# Run this AFTER the Tool Launcher window is visible.
py -3 -c "from PIL import ImageGrab; img = ImageGrab.grab(all_screens=True); img.save(r'D:\Seagate\small-wins-automation\__tmp_tl_screenshot3.png')"
