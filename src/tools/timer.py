import time

def timer():
    return f'[A] timestamp: {round(time.time())}\ntimestring: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}\n'

def timer_json():
    return {"timestamp": {round(time.time())},
            "timestring": {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}
            }
