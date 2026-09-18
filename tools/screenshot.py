import ctypes
from ctypes import wintypes
import io
import base64
import cv2
import numpy as np
from PIL import Image
from PIL import ImageGrab
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    user32.SetProcessDPIAware()
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

def grab_virtual_screen() -> Image.Image:
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

def capture_all_base64(fmt: str = "PNG", data_uri: bool = False, prefix = '') -> str:
    img = grab_virtual_screen()
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"<{prefix}>{b64}</{prefix}>"

def get_screen_cord(cord = [0,0,0,0]):
    if cord == [0,0,0,0]:
        screen = ImageGrab.grab()
    else:
        screen = ImageGrab.grab(bbox=(cord[0],cord[1],cord[2],cord[3]))
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

    centers = 'Coordinates:\n'

    for idx, (x, y, w, h) in enumerate(boxes, start=1):
        label = str(idx)
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

        cx = x + w // 2
        cy = y + h // 2
        centers += f'{idx}=>({cx},{cy})\n'

    cv2.imwrite('./database/screen.png', img)

    with open('./database/screen.png', 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    return {"cord":centers,
            "image":b64}