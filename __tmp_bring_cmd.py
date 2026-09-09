import ctypes, ctypes.wintypes

user32 = ctypes.windll.user32
buf = ctypes.create_unicode_buffer(512)
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_long)

@WNDENUMPROC
def cb(hwnd, _):
    user32.GetWindowTextW(hwnd, buf, 512)
    t = buf.value
    if 'WINDSURF_TOOL_LAUNCHER' in t or 'Tool Launcher' in t:
        print('bringing', t)
        user32.ShowWindow(hwnd, 9)   # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
    return True

user32.EnumWindows(cb, 0)
