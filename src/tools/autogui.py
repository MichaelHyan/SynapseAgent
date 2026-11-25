import time


def click(x,y,button='left',click=1):
    import pyautogui
    x = int(x)
    y = int(y)
    click = int(click)
    pyautogui.click(x,y,button=button,clicks=click)


def typewrite(string):
    import pyautogui
    pyautogui.typewrite(string)