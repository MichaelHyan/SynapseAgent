import os as _os, sys as _sys
if __name__ == "__main__":
    _ROOT = _os.path.dirname(_os.path.abspath(__file__))
    if _ROOT not in _sys.path:
        _sys.path.insert(0, _ROOT)
    _os.chdir(_ROOT)

import src.tools.guide as guide
import src.main.CNMD as CNMD
import threading, time, copy, os, sys, argparse, queue, json, socket, subprocess
import ctypes
import unicodedata
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from src.tools import lang
from src.tools.color_utils import Color

# ================================================================ 基础参数
parser = argparse.ArgumentParser()
parser.add_argument('name', nargs='?', default='agent_base')
args = parser.parse_args()

cnm = CNMD.CNMD(args.name)

# 网络参数（单端口）
HOST = "127.0.0.1"
PORT = 56700
PATH = "/cnmd"

# 插件目录
ADDON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'addon')

# 网络端暂停指令：#p / #pause —— 不入队，直接释放 mslock
_PAUSE_CMDS = ("#p", "#pause")

BAR = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'

# Ctrl+P 急停信号的哨兵值（正常输入不可能产生该串）
PAUSE_SIGNAL = '\x00__SYNAPSE_PAUSE__'

# ================================================================ 跨平台终端辅助
#   Windows：msvcrt 逐字符读取 + kernel32 控制台光标定位
#   Linux  ：termios 关闭规范模式/回显/ICRNL + ANSI 转义序列控制光标
IS_WIN = (os.name == 'nt')


def _char_width(c):
    return 2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1


def _display_width(s):
    return sum(_char_width(c) for c in s)


if IS_WIN:
    import msvcrt

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

    # 回调到上一行末尾（跨行退格）
    def _back_to_prev_line_end(prev_line):
        _, y = _get_cursor()
        _set_cursor(_display_width(prev_line), y - 1)

    def _getch():
        return msvcrt.getwch()

    def _flush_escape():
        msvcrt.getwch()

    # Windows 语义：普通回车 \r 换行，Ctrl+Enter（\n）提交
    _KEY_SUBMIT = '\n'
    _KEY_NEWLINE = '\r'

else:
    import termios
    import select
    import atexit

    _stdin_fd = sys.stdin.fileno()
    _term_state = {'saved': None}

    def _enter_cbreak():
        """关闭规范模式/回显，并关闭 ICRNL 以便区分 Enter(\\r) 与 Ctrl+J(\\n)。
        保留 OPOST|ONLCR，保证 print 换行正常；保留 ISIG，Ctrl+C 仍可中断。"""
        if _term_state['saved'] is not None:
            return
        saved = termios.tcgetattr(_stdin_fd)
        _term_state['saved'] = saved
        new = termios.tcgetattr(_stdin_fd)
        new[0] &= ~termios.ICRNL          # iflag
        new[3] &= ~(termios.ICANON | termios.ECHO)  # lflag
        new[6][termios.VMIN] = 1
        new[6][termios.VTIME] = 0
        termios.tcsetattr(_stdin_fd, termios.TCSADRAIN, new)

    def _leave_cbreak():
        saved = _term_state['saved']
        if saved is None:
            return
        try:
            termios.tcsetattr(_stdin_fd, termios.TCSADRAIN, saved)
        except Exception:
            pass
        _term_state['saved'] = None

    atexit.register(_leave_cbreak)

    def _read_bytes(n):
        data = b''
        while len(data) < n:
            r, _, _ = select.select([_stdin_fd], [], [], 0.2)
            if not r:
                continue
            chunk = os.read(_stdin_fd, n - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def _getch():
        """读取一个字符（自动拼接 UTF-8 多字节）"""
        _enter_cbreak()
        b = _read_bytes(1)
        if not b:
            return ''
        lead = b[0]
        if lead < 0x80:
            return b.decode('latin-1')
        if lead >> 5 == 0b110:
            need = 1
        elif lead >> 4 == 0b1110:
            need = 2
        elif lead >> 3 == 0b11110:
            need = 3
        else:
            need = 0
        if need:
            b += _read_bytes(need)
        return b.decode('utf-8', 'replace')

    def _flush_escape():
        """吞掉方向键/功能键的转义序列（ESC [ ... 或 ESC O x）"""
        r, _, _ = select.select([_stdin_fd], [], [], 0.01)
        if not r:
            return
        c1 = os.read(_stdin_fd, 1)
        if c1 in (b'[', b'O'):
            while True:
                r, _, _ = select.select([_stdin_fd], [], [], 0.01)
                if not r:
                    break
                c = os.read(_stdin_fd, 1)
                if c.isalpha() or c == b'~':
                    break

    def _back_to_prev_line_end(prev_line):
        """ANSI：上移一行 + 回到行首 + 右移到上一行末尾"""
        w = _display_width(prev_line)
        sys.stdout.write('\033[1A\r')
        if w > 0:
            sys.stdout.write(f'\033[{w}C')

    # Linux 语义：Enter（\r）提交，Ctrl+J（\n）换行
    _KEY_SUBMIT = '\r'
    _KEY_NEWLINE = '\n'


def read_input_block():
    """逐字符读取：可换行编辑，专用键提交，Ctrl+P 急停。
    Windows：\\r 换行 / Ctrl+Enter(\\n) 提交
    Linux  ：Ctrl+J(\\n) 换行 / Enter(\\r) 提交
    返回提交的文本（含换行）或 PAUSE_SIGNAL。
    """
    text = ''
    while True:
        ch = _getch()
        if ch == '':
            continue
        if ch == '\x1b':                # ESC：功能键/方向键序列，整体吞掉
            _flush_escape()
            continue
        if ch == '\x03':                # Ctrl+C
            raise KeyboardInterrupt
        if ch == '\x10':                # Ctrl+P：急停，立即返回哨兵信号（丢弃半截输入）
            sys.stdout.write('\r\n')
            sys.stdout.flush()
            return PAUSE_SIGNAL
        if ch == _KEY_SUBMIT:           # 提交
            sys.stdout.write('\r\n')
            sys.stdout.flush()
            return text
        if ch == _KEY_NEWLINE:          # 换行
            text += '\n'
            sys.stdout.write('\r\n')
            sys.stdout.flush()
            continue
        if ch in ('\b', '\x7f'):        # 退格（Linux 终端的退格是 0x7f）
            if text == '':
                continue
            if text.endswith('\n'):     # 跨行退格：光标上移回上一行末尾
                prev_line = text[:-1].split('\n')[-1]
                _back_to_prev_line_end(prev_line)
                sys.stdout.flush()
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
    print(f'{Color.RESET}')
    print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')

def _sep():
    try:
        width = os.get_terminal_size().columns - 1
    except OSError:
        width = 60
    return f'{Color.WHITE}{"─" * width}{Color.RESET}'

# ================================================================ 统一任务队列与串行调度
#   两条入口（CLI 输入 / 网络 ask）统一投递到 _pending，元素为 (content, source)
#   全程只有 _queue_worker 一个消费者，保证同一时刻只跑一条任务、共享 cnm 不并发
# ================================================================
_pending = queue.Queue()

# worker 已取走消息、但 cnm.status 尚未变化期间用此标志兜底
_worker_busy = threading.Event()

_POLL = 0.05

# 网络独立缓冲区：模型输出镜像给网络端（与 CLI 各自独立）
_net_buffer = deque(maxlen=2000)
_net_lock = threading.Lock()

def _busy():
    """是否还有未完成的工作（用于向网络端汇报 status）。"""
    return (cnm.status != 0
            or _pending.qsize() > 0
            or _worker_busy.is_set()
            or len(_net_buffer) > 0
            or cnm.msg_stack != [])

def _wait_status_0(timeout=None):
    """阻塞等待 cnm.status 回到 0（本轮跑完）。"""
    start = time.time()
    while cnm.status != 0:
        if timeout is not None and (time.time() - start) > timeout:
            return False
        time.sleep(_POLL)
    return True

def _print_net_input(content):
    """把来自网络端的输入像正常输入一样显示在 CLI。"""
    sys.stdout.write('\r' + ' ' * 30 + '\r')
    sys.stdout.flush()
    print(f'{Color.YELLOW}[NET Input]{Color.RESET} {content}')
    print(_sep())
    sys.stdout.flush()

def _queue_worker():
    """单消费者：串行处理队列中的消息，同一时刻只跑一条，且等 status 归 0 再继续。"""
    while True:
        content, source = _pending.get()
        _worker_busy.set()
        try:
            # 1) 等上一轮彻底跑完
            _wait_status_0()
            # 2) 网络来源任务：先在 CLI 显示输入记录
            if source == 'net':
                _print_net_input(content)
            # 3) 投递这一条（同步阻塞直到本轮结束）
            cnm.CNMD(content)
            # 4) 等这一轮真正结束
            _wait_status_0()
        except Exception as exc:
            print(f'{Color.RED}worker error{Color.RESET}:{exc}')
        finally:
            _worker_busy.clear()
            _pending.task_done()

# ================================================================ HTTP 服务（单端口）
_REGISTRY = {}

def method(name=None):
    def deco(func):
        _REGISTRY[name or func.__name__] = func
        return func
    return deco

def dispatch(data):
    if not isinstance(data, dict):
        raise ValueError("Request body has to be a JSON object")

    name = data.get("method")
    func = _REGISTRY.get(name)
    if func is None:
        raise LookupError("Unregistered method: %s" % name)

    params = data.get("params")
    if params is None:
        params = {k: v for k, v in data.items() if k != "method"}

    if isinstance(params, dict):
        return func(**params)
    if isinstance(params, list):
        return func(*params)
    raise ValueError("params must be an object or an array")

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _reply(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlparse(self.path).path.rstrip("/") not in ("", PATH):
            self._reply({"ok": False, "error": {"type": "NotFound",
                                                "message": "unknown path: %s" % self.path}}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            self._reply({"ok": True, "result": dispatch(json.loads(raw))})
        except Exception as exc:
            self._reply({"ok": False, "error": {"type": type(exc).__name__,
                                                "message": str(exc)}}, 400)

    def log_message(self, fmt, *args):
        pass

@method()
def ping():
    return {
        "status": 0,
        "response": ""
    }

@method()
def ask(content: str):
    # #p / #pause：无视是否在跑，直接释放 mslock，且不入队
    if isinstance(content, str) and content.strip().lower() in _PAUSE_CMDS:
        cnm.mslock = False
        return {
            "status": cnm.status,
            "response": "paused"
        }
    # 投递到统一队列，由唯一 worker 串行执行
    _pending.put((content, 'net'))
    return {
        "status": 1,
        "response": ""
    }

@method()
def answer(type='rp'):
    if type == 'rp':
        with _net_lock:
            resp = _net_buffer.popleft() if _net_buffer else None
        if resp is not None:
            with _net_lock:
                status = 1 if (len(_net_buffer) > 0 or _busy()) else 0
            return {
                "status": status,
                "response": resp
            }
        else:
            return {
                "status": 1 if _busy() else 0,
                "response": ""
            }
    elif type == 'rl':
        with _net_lock:
            joined = '\n'.join(str(x) for x in _net_buffer)
        return {
            "status": 1 if _busy() else 0,
            "response": joined
        }
    else:
        return {
            "status": 0,
            "response": "Unknown type"
        }

class _ExclusiveHTTPServer(ThreadingHTTPServer):
    """关闭 SO_REUSEADDR，确保端口被占用时 bind 会真正失败。"""
    allow_reuse_address = False
    daemon_threads = True

def _port_in_use():
    """connect 探测：能连上说明已有服务在监听该端口。"""
    try:
        with socket.create_connection((HOST, PORT), timeout=0.15):
            return True
    except OSError:
        return False

def _start_server():
    """尝试在单端口启动 HTTP 服务；端口被占用则静默跳过，纯 CLI 运行。"""
    if _port_in_use():
        return None
    try:
        server = _ExclusiveHTTPServer((HOST, PORT), Handler)
    except OSError:
        return None
    t = threading.Thread(target=server.serve_forever, name="http-server", daemon=True)
    t.start()
    print(f'{Color.GREEN}[NET]{Color.RESET} 已开启网络服务: http://{HOST}:{PORT}{PATH}')
    print(_sep())
    return server

# ================================================================ 插件启动
def _start_addons():
    """读取 addon/config.json 的 enabled 列表，逐个以独立进程启动插件。
    Windows 下新开控制台窗口；类 Unix 下以独立进程组启动（不抢占当前终端）。"""
    cfg_path = os.path.join(ADDON_DIR, 'config.json')
    try:
        with open(cfg_path, encoding='utf-8') as f:
            cfg = json.load(f)
        enabled = cfg.get('enabled', [])
    except Exception as exc:
        print(f'{Color.YELLOW}[ADDON]{Color.RESET} 读取 addon/config.json 失败: {exc}')
        return
    if not enabled:
        return
    for name in enabled:
        main_py = os.path.join(ADDON_DIR, name, 'main.py')
        if not os.path.exists(main_py):
            print(f'{Color.YELLOW}[ADDON]{Color.RESET} 跳过插件 {name}: 未找到 main.py')
            continue
        try:
            kwargs = {'cwd': os.path.dirname(main_py)}
            if IS_WIN:
                kwargs['creationflags'] = 0x00000010  # CREATE_NEW_CONSOLE：单开窗口
            else:
                kwargs['start_new_session'] = True    # 独立会话，不干扰当前终端
            subprocess.Popen([sys.executable, main_py], **kwargs)
            print(f'{Color.GREEN}[ADDON]{Color.RESET} 已启动插件: {name}')
        except Exception as exc:
            print(f'{Color.RED}[ADDON]{Color.RESET} 启动插件 {name} 失败: {exc}')
    print(_sep())

# ================================================================ CLI 线程
def input_thread():
    """读取本地输入，投递到统一队列；处理 #exit / #pause。"""
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
            print(_sep())
            os._exit(0)
        elif normalized in ('#pause', '#p'):
            print(f'{Color.RED}{lang.lang["cnmd.base.pause"]}{Color.RESET}')
            cnm.mslock = False
        elif stripped == '':
            continue
        else:
            print(_sep())
            _pending.put((text, 'cli'))

def process_thread():
    """唯一消费者：把 cnm.msg_stack 分发给 CLI（打印）与网络缓冲（镜像）。"""
    while True:
        if cnm.msg_stack:
            sys.stdout.write('\r' + ' ' * 20 + '\r')
            sys.stdout.flush()
            first_element = cnm.msg_stack.pop(0)
            # 网络端同步接收模型输出（独立缓冲）
            with _net_lock:
                _net_buffer.append(first_element)
            if cnm.msg_stack:
                pass
            else:
                print(f"{Color.MAGENTA}●{Color.RESET} {Color.CYAN}Assistant{Color.RESET}")
            while '\n\n\n' in first_element:
                first_element = first_element.replace('\n\n\n', '\n\n')
            print(f"{Color.BLUE}{first_element}{Color.RESET}")
            if not cnm.msg_stack:
                print(_sep())
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

    # 统一 worker
    t_worker = threading.Thread(target=_queue_worker, name="queue-worker", daemon=True)
    t_worker.start()
    # 网络服务（占用则静默跳过）
    _start_server()
    # 插件（网络就绪后启动）
    _start_addons()
    # CLI 线程
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