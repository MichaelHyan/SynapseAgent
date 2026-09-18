import cv2
import numpy as np
import base64
import time
from PIL import ImageGrab
def get_screen_cord(x1,y1,x2,y2):
    if x1 == x2 == y1 == y2 == 0:
        screen = ImageGrab.grab()
    else:
        screen = ImageGrab.grab(bbox=(x1,y1,x2,y2))
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