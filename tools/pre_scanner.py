import tools.multymodalhandler as multymodel
import tools.screenshot as screenshot
import tools.bot as bot
import tools.lang as lang
import pyautogui,json
WIDTH,HIGHT= pyautogui.size()

def get_complex_cord():
    x_range = WIDTH//960
    y_range = HIGHT//540
    cords = []
    index = 0
    for y in range(y_range):
        for x in range(x_range):
            cords.append(screenshot.get_screen_cord(cord=(
                x*960,
                y*540,
                x*960+960 if x*960+960 <= WIDTH else WIDTH,
                y*540+540 if y*540+540 <= HIGHT else HIGHT),
                index = index,
                path=f'./database/screen_{x}_{y}.png'))
            index += cords[-1]['last_index']
    image = screenshot.capture_all_base64(prefix='image')
    cord = ''
    for i in cords:
        image += f'<image>{i['image']}</image>'
        cord += f'{i['cord']}\n'
    return f'{image}{cord}'

def get_avaliable_operation():
    messages = [
            {
                "role":"system",
                "content": lang.text['prompt.prescan']
            }
        ]
    messages.append(multymodel.user(get_complex_cord()))
    response = bot.reply(messages)
    with open(f'test.json','w',encoding='utf-8') as f:
        json.dump(messages,f,indent=4,ensure_ascii=False)
    print(response['content'])