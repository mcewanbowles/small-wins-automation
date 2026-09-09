import ctypes, ctypes.wintypes

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_long)

@WNDENUMPROC
def cb(hwnd, _):
    if user32.IsWindowVisible(hwnd):
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        title = buf.value
        r = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, r)
        print(f'{hwnd}\t{title!r}\t({r.left},{r.top},{r.right},{r.bottom})')
    return True

user32.EnumWindows(cb, 0)
