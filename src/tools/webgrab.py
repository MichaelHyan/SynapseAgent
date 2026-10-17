import urllib.request
import urllib.parse
import urllib.error
import subprocess
import platform
import json
import socket
import ipaddress
import re

try:
    from .lang import lang as _lang
except Exception:
    try:
        from lang import lang as _lang
    except Exception:
        _lang = {}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

_CONFIG_PATH = './config/webtool_guard.json'

_DEFAULT_CONFIG = {
    "enabled": True,
    "scheme_whitelist": ["http", "https"],
    "port_whitelist": [80, 443],
    "block_private_ip": True,
    "ip_blacklist": [
        "0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8",
        "169.254.0.0/16", "172.16.0.0/12", "192.0.0.0/24", "192.168.0.0/16",
        "198.18.0.0/15", "224.0.0.0/4", "240.0.0.0/4",
        "::1/128", "fc00::/7", "fe80::/10", "ff00::/8"
    ],
    "allow_redirects": True,
    "max_redirects": 5,
    "max_response_bytes": 5242880,
    "timeout_seconds": 20,
    "ping": {
        "enabled": True,
        "host_pattern": r"^[A-Za-z0-9][A-Za-z0-9.\-]{0,252}$",
        "count": 4,
        "timeout_seconds": 10
    }
}


class _BlockedError(Exception):
    """策略拦截专用异常，仅承载语言键文本。"""


def _load_config():
    cfg = dict(_DEFAULT_CONFIG)
    try:
        with open(_CONFIG_PATH, encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            cfg.update(data)
            if isinstance(data.get('ping'), dict):
                merged = dict(_DEFAULT_CONFIG['ping'])
                merged.update(data['ping'])
                cfg['ping'] = merged
    except Exception:
        # 配置文件缺失或损坏时退回默认策略（默认开启保护）
        pass
    return cfg


def _ip_blocked(ip_str, networks):
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    for net in networks:
        try:
            if ip in ipaddress.ip_network(net, strict=False):
                return True
        except ValueError:
            continue
    return False


def _check_url(url, cfg):
    """校验目标 URL。返回 (ok, reason)；ok=False 时 reason 为语言键文本。"""
    if not cfg.get('enabled', True):
        return True, None

    try:
        parts = urllib.parse.urlsplit(url)
    except Exception:
        return False, _lang['bot.tool.weburlerror']

    scheme = (parts.scheme or '').lower()
    schemes = [str(s).lower() for s in cfg.get('scheme_whitelist', [])]
    if scheme not in schemes:
        return False, _lang['bot.tool.webscheme']

    host = parts.hostname
    if not host:
        return False, _lang['bot.tool.webnohost']

    try:
        port = parts.port
    except ValueError:
        return False, _lang['bot.tool.webportinvalid']

    if port is None:
        port = 443 if scheme == 'https' else 80

    if port not in cfg.get('port_whitelist', []):
        return False, _lang['bot.tool.webport']

    if cfg.get('block_private_ip', True):
        try:
            infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        except socket.gaierror:
            # 域名无法解析：放行，交给 urlopen 处理
            return True, None
        networks = cfg.get('ip_blacklist', [])
        for info in infos:
            addr = info[4][0]
            if _ip_blocked(addr, networks):
                return False, _lang['bot.tool.webipblocked']

    return True, None


class _CheckedRedirectHandler(urllib.request.HTTPRedirectHandler):
    """跟随重定向，但每一跳都重新执行完整校验。"""

    def __init__(self, cfg):
        super().__init__()
        self._cfg = cfg
        self.max_redirections = int(cfg.get('max_redirects', 5))

    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        ok, _ = _check_url(newurl, self._cfg)
        if not ok:
            raise _BlockedError(_lang['bot.tool.webredirect'])
        return super().redirect_request(req, fp, code, msg, hdrs, newurl)


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """allow_redirects=false 时使用：不跟随，直接返回 3xx 响应。"""

    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        return None


def get_html(url):
    global headers
    cfg = _load_config()

    if not isinstance(url, str):
        return _lang['bot.tool.webparamerror']

    ok, reason = _check_url(url, cfg)
    if not ok:
        return reason

    try:
        # 保留 % 与 #，避免对已编码 URL 二次编码（修复 V-06）
        safe_url = urllib.parse.quote(url, safe='/:?=&%#')

        encoded_headers = {}
        for key, value in headers.items():
            if isinstance(value, str):
                encoded_headers[key] = value.encode('utf-8').decode('latin-1')
            else:
                encoded_headers[key] = value

        req = urllib.request.Request(safe_url, headers=encoded_headers)
        timeout = cfg.get('timeout_seconds', 20)

        if cfg.get('allow_redirects', True):
            opener = urllib.request.build_opener(_CheckedRedirectHandler(cfg))
        else:
            opener = urllib.request.build_opener(_NoRedirectHandler)

        response = opener.open(req, timeout=timeout)

        max_bytes = cfg.get('max_response_bytes', 5242880)
        html_bytes = response.read(max_bytes + 1)
        if len(html_bytes) > max_bytes:
            return _lang['bot.tool.webtoolarge']

        try:
            return html_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return html_bytes.decode('gbk')

    except _BlockedError as e:
        return str(e)
    except Exception:
        return _lang['bot.tool.weberror']


def ping(host):
    cfg = _load_config()
    ping_cfg = cfg.get('ping', {}) or {}

    if not ping_cfg.get('enabled', True):
        return _lang['bot.tool.pingdisabled']

    host_str = str(host)
    pattern = ping_cfg.get('host_pattern', r'^[A-Za-z0-9][A-Za-z0-9.\-]{0,252}$')
    try:
        passed = re.fullmatch(pattern, host_str) is not None
    except re.error:
        passed = False
    if not passed:
        return _lang['bot.tool.pingblocked']

    param = '-n' if platform.system().lower() == 'windows' else '-c'
    count_param = str(ping_cfg.get('count', 4))
    timeout = ping_cfg.get('timeout_seconds', 10)
    command = ['ping', param, count_param, host_str]
    try:
        response = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        return response.stdout
    except Exception:
        return _lang['bot.tool.pingerror']