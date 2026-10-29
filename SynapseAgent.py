import src.tools.guide as guide
import src.main.CNMD as CNMD
import threading, time, copy, os, sys, argparse
import msvcrt
import ctypes
import unicodedata
from src.tools import lang
from src.tools.color_utils import Color

input_list = ''
parser = argparse.ArgumentParser()
parser.add_argument('name', nargs='?', default='agent_base')
args = parser.parse_args()

cnm = CNMD.CNMD(args.name)

BAR = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'

# Ctrl+P 急停信号的哨兵值（正常输入不可能产生该串）
PAUSE_SIGNAL = '\x00__SYNAPSE_PAUSE__'

# ---------- Windows 控制台光标辅助（用于跨行退格定位，不依赖 ANSI） ----------
_kernel32 = ctypes.windll.kernel32

class _COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

class _SMALL_RECT(ctypes.Structure):
    _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short),
                ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]

class _CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [("dwSize", _COORD),
                ("dwCursorPosition", _COORD),
                ("wAttributes", ctypes.c_ushort),
                ("srWindow", _SMALL_RECT),
                ("dwMaximumWindowSize", _COORD)]

_kernel32.GetStdHandle.argtypes = [ctypes.c_uint32]
_kernel32.GetStdHandle.restype = ctypes.c_void_p
_hout = _kernel32.GetStdHandle(0xFFFFFFF5)  # STD_OUTPUT_HANDLE = -11

_kernel32.GetConsoleScreenBufferInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(_CONSOLE_SCREEN_BUFFER_INFO)]
_kernel32.GetConsoleScreenBufferInfo.restype = ctypes.c_int
_kernel32.SetConsoleCursorPosition.argtypes = [ctypes.c_void_p, _COORD]
_kernel32.SetConsoleCursorPosition.restype = ctypes.c_int

def _get_cursor():
    info = _CONSOLE_SCREEN_BUFFER_INFO()
    _kernel32.GetConsoleScreenBufferInfo(_hout, ctypes.byref(info))
    return info.dwCursorPosition.X, info.dwCursorPosition.Y

def _set_cursor(x, y):
    _kernel32.SetConsoleCursorPosition(_hout, _COORD(x, y))

def _char_width(c):
    return 2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1

def _display_width(s):
    return sum(_char_width(c) for c in s)

def read_input_block():
    """逐字符读取：普通回车换行，Ctrl+Enter 提交，Ctrl+P 急停。返回提交的文本(含换行)或 PAUSE_SIGNAL。"""
    text = ''
    while True:
        ch = msvcrt.getwch()
        if ch in ('\x00', '\xe0'):      # 功能键/方向键前缀：吞掉后续扫描码
            msvcrt.getwch()
            continue
        if ch == '\x03':                # Ctrl+C
            raise KeyboardInterrupt
        if ch == '\x10':                # Ctrl+P：急停，立即返回哨兵信号（丢弃半截输入）
            sys.stdout.write('\r\n')
            sys.stdout.flush()
            return PAUSE_SIGNAL
        if ch == '\n':                  # Ctrl+Enter：提交
            sys.stdout.write('\r\n')
            sys.stdout.flush()
            return text
        if ch == '\r':                  # 普通回车：换行
            text += '\n'
            sys.stdout.write('\r\n')
            sys.stdout.flush()
            continue
        if ch == '\b':                  # 退格
            if text == '':
                continue
            if text.endswith('\n'):     # 跨行退格：光标上移回上一行末尾
                _, y = _get_cursor()
                prev_line = text[:-1].split('\n')[-1]
                _set_cursor(_display_width(prev_line), y - 1)
                text = text[:-1]
            else:                       # 行内退格（宽字符占 2 列）
                w = _char_width(text[-1])
                sys.stdout.write('\b' * w + ' ' * w + '\b' * w)
                sys.stdout.flush()
                text = text[:-1]
            continue
        # 普通字符（含中文等宽字符）
        text += ch
        sys.stdout.write(ch)
        sys.stdout.flush()

def print_banner():
    print()
    print(f'{Color.CYAN}{Color.BRIGHT}')
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"╭──────────────────────────────────────────╮")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"│     //  \\                               |")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"│     \\  //           SynapseAgent        |")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"│       ||         ────────────────────    |")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"│    //    \\         Think Backward       |")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"│ //  \\  //  \\       And Re:Start!       |")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"│ \\  //  \\  //                           |")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"╰──────────────────────────────────────────╯")
    print(f"{Color.RESET}")
    print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')

def input_thread():
    global input_list, cnm
    while True:
        try:
            text = read_input_block()
        except KeyboardInterrupt:
            continue
        except Exception:
            continue
        if text == PAUSE_SIGNAL:        # Ctrl+P 急停
            print(f'{Color.RED}{lang.lang["cnmd.base.pause"]}{Color.RESET}')
            cnm.mslock = False
            continue
        stripped = text.strip()
        normalized = ''.join(text.split())   # 剔除所有空格和换行，用于 #exit / #pause 匹配
        if normalized == '#exit':
            print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')
            os._exit(0)
        elif normalized in ('#pause', '#p'):
            print(f'{Color.RED}{lang.lang["cnmd.base.pause"]}{Color.RESET}')
            cnm.mslock = False
        elif stripped == '':
            continue
        else:
            input_list = text
            threading.Thread(target=agent_thread).start()
            print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')

def agent_thread():
    global input_list
    temp = copy.deepcopy(input_list)
    input_list = ''
    cnm.CNMD(temp)

def process_thread():
    while True:
        if cnm.msg_stack:
            sys.stdout.write(f'\r{" " * 20}\r')
            sys.stdout.flush()
            first_element = cnm.msg_stack.pop(0)
            if cnm.msg_stack:
                pass
            else:
                print(f"{Color.MAGENTA}●{Color.RESET} {Color.CYAN}Assistant{Color.RESET}")
            while '\n\n\n' in first_element:
                first_element = first_element.replace('\n\n\n','\n\n')
            print(f"{Color.BLUE}{first_element}{Color.RESET}")
            if not cnm.msg_stack:
                print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')
        time.sleep(0.1)

def reasoning_thread():
    i = 0
    prev_running = False

    while True:
        running = (getattr(cnm, 'status', 0) == 1)
        if running:
            sys.stdout.write(f'\r{Color.GREEN}{BAR[i % len(BAR)]}{Color.RESET} {lang.lang["cnmd.bot.reasoning"]}')
            sys.stdout.flush()
            i += 1
            prev_running = True
        elif prev_running:
            sys.stdout.write(f'\r{" " * 30}\r')
            sys.stdout.flush()
            prev_running = False

        time.sleep(0.15)

if __name__ == "__main__":
    print_banner()
    t_input = threading.Thread(target=input_thread)
    t_input.daemon = True
    t_process = threading.Thread(target=process_thread)
    t_process.daemon = True
    t_reasoning = threading.Thread(target=reasoning_thread)
    t_reasoning.daemon = True
    t_input.start()
    t_process.start()
    t_reasoning.start()
    try:
        while True:
            time.sleep(1)
    except:
        pass