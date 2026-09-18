import pyautogui,time

def click(x,y,button='left',click=1):
    pyautogui.click(x,y,button=button,clicks=click)

def typewrite(string):
    pyautogui.typewrite(string)

def scroll(amont,vertical=False):
    if vertical == False:
        pyautogui.scroll(amont)
    else:
        pyautogui.hscroll(amont)

time.sleep(1)
typewrite('ssjssf')