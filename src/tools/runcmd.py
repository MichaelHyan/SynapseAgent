import subprocess
import threading
import time,os
import shutil
import platform
import locale

cmd_output = ''

IS_WIN = platform.system() == 'Windows'


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
        for output in iter(process.stdout.readline, ''):
            if output:
                cmd_output += f'{output.strip()}\n'
        process.stdout.close()
        return_code = process.wait()
        cmd_output += f"command end, return code: {return_code}\n"
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
        result = subprocess.run(
            [powershell_path, "-Command", cmd],
            check=False,
            capture_output=True
        )
        cmd_output += f'{_smart_decode(result.stdout)}\n'
        if result.stderr:
            cmd_output += f'{_smart_decode(result.stderr)}\n'
    except Exception as e:
        cmd_output += f'{e}\n'