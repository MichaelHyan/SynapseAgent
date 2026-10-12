import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

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
import CNMD
import argparse,threading,os
from tools.color_utils import Color

parser = argparse.ArgumentParser()
parser.add_argument('name', nargs='?', default='agent_base')
args = parser.parse_args()

cnm = CNMD.CNMD(args.name)

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

def response(post:str):
    cnm.CNMD(post)

@method()
def ping():
    return {
        "status": 0,
        "response": ""
    }

@method()
def ask(content:str):
    threading.Thread(target=response, args=(content,)).start()
    return {
        "status": 1,
        "response":""
    }

@method()
def answer(type='rp'):
    if type == 'rp':
        if cnm.msg_stack != []:
            resp = cnm.msg_stack.pop()
            status = 1
            if cnm.msg_stack == [] and cnm.status == 0:
                status = 0
            return {
                "status": status,
                "response": resp
            }
        else:
            return {
                "status": cnm.status,
                "response":""
            }
    elif type == 'rl':
        return {
            "status": cnm.status,
            "response": '\n'.join(str(x) for x in cnm.msg_stack)
        }
    else:
        return {
            "status": 0,
            "response": "Unknown type"
        }
#--------------------------------------------------------------------------------------------------

def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print_banner()
    try:
        server.serve_forever()
    except:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()