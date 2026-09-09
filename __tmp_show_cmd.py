import ctypes, ctypes.wintypes

user32 = ctypes.windll.user32
buf = ctypes.create_unicode_buffer(512)
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_long)

@WNDENUMPROC
def cb(hwnd, _):
    user32.GetWindowTextW(hwnd, buf, 512)
    t = buf.value
    if 'cmd.exe' in t and 'WINDSURF_TOOL_LAUNCHER' in t:
        print('found', t, 'restoring')
        user32.ShowWindow(hwnd, 3)   # SW_MAXIMIZE
        user32.SetForegroundWindow(hwnd)
        r = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, r)
        print('rect', (r.left, r.top, r.right, r.bottom))
    return True

user32.EnumWindows(cb, 0)
