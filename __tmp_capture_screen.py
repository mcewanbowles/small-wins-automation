import time, PIL.ImageGrab as ImageGrab
from pathlib import Path

# ensure windows aren't minimized before capturing? not possible for all
out = Path(r'D:\Seagate\small-wins-automation\__tmp_screenshot_full.png')
img = ImageGrab.grab()
img.save(out)
print(out)
