import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import src.tools.timer as timer
from src.tools.color_utils import Color

'''
Invoke-RestMethod -Uri "http://127.0.0.1:56700/cnmd" `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body '{"method":"ask","params":{"content":"hello"}}'
'''
#--------------------------------------------------------------------------------------------------
HOST = "127.0.0.1"
PORT = 56700
PATH = "/cnmd"
#--------------------------------------------------------------------------------------------------

# 暂停指令：#p / #pause —— 不进入消息队列，直接释放 mslock
_PAUSE_CMDS = ("#p", "#pause")

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

#--------------------------------------------------------------------------------------------------
import src.main.CNMD as CNMD
import argparse,threading,os,queue,time

parser = argparse.ArgumentParser()
parser.add_argument('name', nargs='?', default='agent_base')
args = parser.parse_args()

cnm = CNMD.CNMD(args.name)

#--------------------------------------------------------------------------------------------------
# 消息队列与串行调度
#   cnm.status == 1 : 上一轮还没跑完，新消息只入队，不处理
#   cnm.status == 0 : 空闲，队列里的消息按顺序依次处理
#   全程只有 _queue_worker 一个消费者，保证同一时刻只跑一条任务
#   _pending 为标准 FIFO 队列，按消息到达先后依次处理
#--------------------------------------------------------------------------------------------------
_pending = queue.Queue()
_STOP = object()

# worker 已取走消息、但 cnm.status 尚未变 1 的窗口期用此标志兜底，
# 避免 _busy() 在该瞬间把 qsize 误判为 0 而返回 status=0
_worker_busy = threading.Event()

# status 从 0 变 1 的宽限窗口（秒），用于兼容“异步置位”的实现
_STATUS_GRACE = 0.2
_POLL = 0.05

def _busy():
    """是否还有未完成的工作：
       - 正在跑 (cnm.status != 0)
       - 队列里还有没被取走的消息 (_pending.qsize() > 0)
       - worker 已取走消息但整轮尚未结束 (_worker_busy)
       只要任一成立，对外 status 就应为 1。
    """
    return cnm.status != 0 or _pending.qsize() > 0 or _worker_busy.is_set()

def _wait_status_0(timeout=None):
    """阻塞等待 cnm.status 回到 0（本轮跑完）。"""
    start = time.time()
    while cnm.status != 0:
        if timeout is not None and (time.time() - start) > timeout:
            return False
        time.sleep(_POLL)
    return True

def print_banner():
    print()
    print(f'{Color.CYAN}{Color.BRIGHT}')
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"╭──────────────────────────────────────────╮")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"│     //  \\                               |")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"│     \\  //       SynapseAgent Server     |")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"│       ||         ────────────────────    |")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"│    //    \\         Think Backward       |")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"│ //  \\  //  \\       And Re:Start!       |")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"│ \\  //  \\  //                           |")
    print(f"{' ' * int((os.get_terminal_size().columns/2-23))}" + r"╰──────────────────────────────────────────╯")
    print(f"{Color.RESET}")
    print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')

def response(post:str):
    cnm.CNMD(post)

def _queue_worker():
    """单消费者：串行处理队列中的消息，同一时刻只跑一条，且等 status 归 0 再继续。"""
    while True:
        content = _pending.get()
        # 取走的瞬间立刻置忙，堵住 qsize 已减 1 但 status 还没变 1 的窗口
        _worker_busy.set()
        if content is _STOP:
            _worker_busy.clear()
            _pending.task_done()
            break
        try:
            # 1) 等上一轮彻底跑完
            _wait_status_0()

            # 2) 投递这一条
            response(content)

            # 3) 兼容异步实现：给 status 变 1 留一个极短宽限期
            grace_start = time.time()
            while cnm.status == 0 and (time.time() - grace_start) < _STATUS_GRACE:
                time.sleep(_POLL)

            # 4) 等这一轮真正结束，再取下一条
            _wait_status_0()

        except Exception as exc:
            print(f"[S]:{timer.timer_json()['timestring']}-{Color.RED}worker error{Color.RESET}:{exc}")
        finally:
            _worker_busy.clear()
            _pending.task_done()

@method()
def ping():
    print(f'[S]:{timer.timer_json()['timestring']}-{Color.RED}ping{Color.RESET}')
    return {
        "status": 0,
        "response": ""
    }

@method()
def ask(content:str):
    print(f'{Color.CYAN}[S]{Color.RESET}:{Color.CYAN}{timer.timer_json()['timestring']}{Color.RESET}-{Color.GREEN}ask{Color.RESET}:{content if len(content) < 50 else content[:50] + '...'}')

    # #p / #pause：无视是否在跑，直接释放 mslock，且不入队
    if isinstance(content, str) and content.strip().lower() in _PAUSE_CMDS:
        cnm.mslock = False
        print(f"[S]:{timer.timer_json()['timestring']}-{Color.MAGENTA}pause{Color.RESET}")
        return {
            "status": cnm.status,
            "response": "paused"
        }

    # status == 1 时自然排在队尾，不并发处理；status == 0 时 worker 会立即取走
    _pending.put(content)
    queued = _pending.qsize()
    if cnm.status != 0:
        print(f"[S]:{timer.timer_json()['timestring']}-{Color.YELLOW}queued{Color.RESET}:{queued}")
    return {
        "status": 1,
        "response": ""
    }

@method()
def answer(type='rp'):
    if type == 'rp':
        if cnm.msg_stack != []:
            # FIFO：从头部取最早堆积的一条回复
            resp = cnm.msg_stack.pop(0)
            # 还有回复/还在跑/队列没取空 → 1；全空 → 0
            status = 1 if (cnm.msg_stack != [] or _busy()) else 0
            print(f'{Color.CYAN}[S]{Color.RESET}:{Color.CYAN}{timer.timer_json()['timestring']}{Color.RESET}-{Color.BLUE}reply{Color.RESET}:{resp if len(resp) < 50 else resp[:50] + '...'}')
            return {
                "status": status,
                "response": resp
            }
        else:
            # 没有回复可取：只要还在跑 / 队列还有消息 / worker 未结束，就继续返回 1
            return {
                "status": 1 if _busy() else 0,
                "response":""
            }
    elif type == 'rl':
        print(f'[S]:{timer.timer_json()['timestring']}-{Color.MAGENTA}reply read only{Color.RESET}')
        return {
            "status": 1 if _busy() else 0,
            "response": '\n'.join(str(x) for x in cnm.msg_stack)
        }
    else:
        return {
            "status": 0,
            "response": "Unknown type"
        }
#--------------------------------------------------------------------------------------------------

def main():
    worker = threading.Thread(target=_queue_worker, name="cnmd-queue-worker", daemon=True)
    worker.start()

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print_banner()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        _pending.put(_STOP)

if __name__ == "__main__":
    main()