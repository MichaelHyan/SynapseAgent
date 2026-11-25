import subprocess
import os
import shutil
import platform
import locale

cmd_output = ''

IS_WIN = platform.system() == 'Windows'

CMD_TIMEOUT = 60


def _shell_encoding():
    """Windows 沿用 gbk；Linux 用系统 locale 编码（通常 UTF-8）"""
    if IS_WIN:
        return 'gbk'
    enc = locale.getpreferredencoding(False)
    if not enc or enc.lower() in ('ascii', 'ansi_x3.4-1968'):
        enc = 'utf-8'
    return enc


def _smart_decode(raw, encodings=None):
    if raw is None:
        return ''
    if isinstance(raw, str):
        return raw
    if encodings is None:
        encodings = ('gbk', 'utf-8') if IS_WIN else ('utf-8', 'gbk')
    for enc in encodings:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode(encodings[0], errors='replace')


def _append(out):
    global cmd_output
    if not out:
        return
    cmd_output += out
    if not out.endswith('\n'):
        cmd_output += '\n'


def _kill_tree(process):
    if process.poll() is not None:
        return
    try:
        if IS_WIN:
            subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(process.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            process.kill()
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def cmd(cmd):
    global cmd_output
    try:
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   text=True,
                                   encoding=_shell_encoding(),
                                   errors='replace',
                                   shell=True)
        try:
            out, _ = process.communicate(timeout=CMD_TIMEOUT)
            _append(out)
            cmd_output += f"command end, return code: {process.returncode}\n"
        except subprocess.TimeoutExpired:
            _kill_tree(process)
            try:
                out, _ = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                out = ''
            _append(out)
            cmd_output += f"command timeout ({CMD_TIMEOUT}s), process killed\n"
    except Exception as e:
        cmd_output += f'{e}\n'


def pws(cmd):
    global cmd_output
    try:
        if IS_WIN:
            powershell_path = os.path.join(
                os.environ.get("SYSTEMROOT", r"C:\Windows"),
                "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
        else:
            powershell_path = shutil.which('pwsh') or shutil.which('powershell')
            if not powershell_path:
                cmd_output += 'powershell not available: pwsh not found on this platform\n'
                return
        process = subprocess.Popen(
            [powershell_path, "-Command", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            out, err = process.communicate(timeout=CMD_TIMEOUT)
            _append(_smart_decode(out))
            if err:
                _append(_smart_decode(err))
        except subprocess.TimeoutExpired:
            _kill_tree(process)
            try:
                out, err = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                out, err = b'', b''
            _append(_smart_decode(out))
            if err:
                _append(_smart_decode(err))
            cmd_output += f"command timeout ({CMD_TIMEOUT}s), process killed\n"
    except Exception as e:
        cmd_output += f'{e}\n'