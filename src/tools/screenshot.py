import ctypes
import io
import base64
import platform

IS_WIN = platform.system() == 'Windows'

if IS_WIN:
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass
    SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
    SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]


def _grab_windows():
    from PIL import Image
    x = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    y = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    w = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    h = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    hwin = user32.GetDesktopWindow()
    hdc_src = user32.GetWindowDC(hwin)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_src)
    hbm     = gdi32.CreateCompatibleBitmap(hdc_src, w, h)
    gdi32.SelectObject(hdc_mem, hbm)
    SRCCOPY = 0x00CC0020
    gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_src, x, y, SRCCOPY)
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbm, 0, h, buf, ctypes.byref(bmi), 0)
    img = Image.frombytes("RGB", (w, h), bytes(buf), "raw", "BGRX", 0, 1)
    gdi32.DeleteObject(hbm)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(hwin, hdc_src)
    return img


def _grab_x11():
    """非 Windows（X11）抓取整个虚拟屏幕。优先 mss，回退 PIL.ImageGrab。"""
    try:
        import mss
        from PIL import Image
        with mss.mss() as sct:
            monitor = sct.monitors[0]  # 0 = 所有显示器组成的虚拟屏
            raw = sct.grab(monitor)
            return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
    except Exception:
        from PIL import ImageGrab
        return ImageGrab.grab()


def grab_virtual_screen():
    if IS_WIN:
        return _grab_windows()
    return _grab_x11()


def capture_all_base64(fmt: str = "PNG", data_uri: bool = False, prefix = '') -> str:
    img = grab_virtual_screen()
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"<{prefix}>{b64}</{prefix}>"


def get_screen_cord(cord = [0,0,0,0],index = 0,path='./database/screen.png'):
    import cv2
    import numpy as np
    if IS_WIN:
        from PIL import ImageGrab
        if cord == [0,0,0,0]:
            screen = ImageGrab.grab()
            offset_x, offset_y = 0, 0
        else:
            screen = ImageGrab.grab(bbox=(cord[0],cord[1],cord[2],cord[3]))
            offset_x, offset_y = cord[0], cord[1]
    else:
        full = grab_virtual_screen()
        if cord == [0,0,0,0]:
            screen = full
            offset_x, offset_y = 0, 0
        else:
            screen = full.crop((cord[0],cord[1],cord[2],cord[3]))
            offset_x, offset_y = cord[0], cord[1]
    img = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 15, 15
    )

    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
    merged = cv2.dilate(thresh, kernel_h, iterations=3)
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
    merged = cv2.morphologyEx(merged, cv2.MORPH_CLOSE, kernel_v)

    contours, _ = cv2.findContours(merged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w * h < 500:
            continue
        boxes.append((x, y, w, h))

    boxes.sort(key=lambda b: (b[1], b[0]))

    for (x, y, w, h) in boxes:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

    centers = ''
    idx = 0

    for idx, (x, y, w, h) in enumerate(boxes, start=1):
        label = str(idx+index)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.9
        thickness = 2
        (tw, th), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        tx = x + w - tw
        ty = y + h + th + 5

        if tx + tw > img.shape[1]:
            tx = img.shape[1] - tw
        if ty > img.shape[0]:
            ty = img.shape[0]

        cv2.putText(img, label, (tx, ty), font, font_scale, (0, 255, 0), thickness)

        cx = x + w // 2 + offset_x
        cy = y + h // 2 + offset_y
        centers += f'{idx+index}=>({cx},{cy})\n'

    cv2.imwrite(path, img)

    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    return {"cord":centers.strip(),
            "image":b64,
            "last_index":idx}