import ctypes, time
import ctypes.wintypes
from pathlib import Path
from PIL import ImageGrab

# Make Windows APIs available
user32 = ctypes.windll.user32
SetProcessDPIAware = user32.SetProcessDPIAware
SetProcessDPIAware()

GetWindowText = user32.GetWindowTextW
IsWindowVisible = user32.IsWindowVisible
GetWindowRect = user32.GetWindowRect
SetForegroundWindow = user32.SetForegroundWindow
ShowWindow = user32.ShowWindow
SetWindowPos = user32.SetWindowPos
BringWindowToTop = user32.BringWindowToTop

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_long)
handles = []

@WNDENUMPROC
def enum_callback(hwnd, _):
    if IsWindowVisible(hwnd):
        buf = ctypes.create_unicode_buffer(512)
        GetWindowText(hwnd, buf, 512)
        title = buf.value
        if 'Tool Launcher' in title:
            handles.append(hwnd)
    return True

user32.EnumWindows(enum_callback, 0)

if not handles:
    print('ERROR: Tool Launcher window not found')
    raise SystemExit(1)

hwnd = handles[0]
print(f'Found window {hwnd}')

# Restore and bring to front
ShowWindow(hwnd, 9)  # SW_RESTORE
BringWindowToTop(hwnd)
SetForegroundWindow(hwnd)
SetWindowPos(hwnd, -1, 0, 0, 0, 0, 3)  # HWND_TOPMOST, NOMOVE+_NOSIZE

time.sleep(1.0)

rect = ctypes.wintypes.RECT()
GetWindowRect(hwnd, rect)
bbox = (rect.left, rect.top, rect.right, rect.bottom)
print(f'Bounds: {bbox}')

img = ImageGrab.grab(bbox=bbox)
out = Path(r'D:\Seagate\small-wins-automation\__tmp_tool_launcher_screenshot.png')
img.save(out)
print(f'Saved: {out}')

SetWindowPos(hwnd, -2, 0, 0, 0, 0, 3)  # HWND_NOTOPMOST
