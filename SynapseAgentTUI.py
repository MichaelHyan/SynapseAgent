import asyncio
import argparse
import re
import threading
from datetime import datetime

import CNMD

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

BAR = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
ANSI_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

parser = argparse.ArgumentParser()
parser.add_argument('name', nargs='?', default='agent_base')
args = parser.parse_args()
MODEL_NAME = args.name

cnm = CNMD.CNMD()
cnm.set_prompt(args.name)

app = None
input_buffer = None
status_control = None
output_control = None
output_window = None
output_lines = []
scroll_offset = 0
auto_scroll = True

is_busy = False
is_reasoning = False
spinner_index = 0

BANNER = r'''
╭───────────────────────────────────────────╮
│                                           │
│  ███  █   █ █   █  ███  ████   ███  █████ │
│ █     █   █ ██  █ █   █ █   █ █     █     │
│  ███   █ █  █ █ █ █████ ████   ███  ████  │
│     █   █   █  ██ █   █ █         █ █     │
│     █   █   █   █ █   █ █         █ █     │
│ ████    █   █   █ █   █ █     ████  █████ │
│                                           │
│       SynapseAgent · Think Backward       │
│               And Re:Start!               │
│                                           │
╰───────────────────────────────────────────╯
'''


def strip_ansi(text):
    return ANSI_RE.sub('', str(text))


def get_visible_height():
    global output_window
    if output_window is None or output_window.render_info is None:
        return 25
    return max(1, output_window.render_info.window_height)


def append_output_message(style, text):
    global output_lines, scroll_offset, auto_scroll
    if text is None:
        return
    clean = strip_ansi(text)
    lines = clean.split('\n')
    for line in lines:
        output_lines.append((style, line))
    auto_scroll = True
    scroll_offset = len(output_lines)
    refresh_output()


def append_output_user(text):
    ts = datetime.now().strftime('%H:%M')
    append_output_message('class:user', f'[{ts}] 你: {text}')


def append_output_agent(text):
    ts = datetime.now().strftime('%H:%M')
    append_output_message('class:agent', f'[{ts}] {text}')


def append_output_system(text):
    ts = datetime.now().strftime('%H:%M')
    append_output_message('class:system', f'[{ts}] ⚡ {text}')


def refresh_output():
    global output_control, output_lines, scroll_offset, auto_scroll, output_window
    if output_control is None:
        return

    visible_height = get_visible_height()
    max_offset = max(0, len(output_lines) - visible_height)

    if auto_scroll:
        scroll_offset = max_offset
    else:
        scroll_offset = max(0, min(scroll_offset, max_offset))

    visible_lines = output_lines[scroll_offset:scroll_offset + visible_height]

    fragments = []
    for i, (style, text) in enumerate(visible_lines):
        fragments.append((style, text))
        if i < len(visible_lines) - 1:
            fragments.append(('', '\n'))
    output_control.text = fragments


def scroll_up(event):
    global scroll_offset, auto_scroll
    if scroll_offset > 0:
        auto_scroll = False
        scroll_offset -= 1
        refresh_output()
        event.app.invalidate()


def scroll_down(event):
    global scroll_offset, auto_scroll
    max_offset = max(0, len(output_lines) - get_visible_height())
    if scroll_offset < max_offset:
        scroll_offset += 1
        if scroll_offset >= max_offset:
            auto_scroll = True
        refresh_output()
        event.app.invalidate()


def agent_worker(text):
    global is_busy, is_reasoning
    try:
        cnm.CNMD(text)
    except Exception as e:
        cnm.msg_stack.append(f'处理出错: {e}')
    finally:
        is_busy = False
        is_reasoning = False


def handle_submit(text, active_app):
    global is_busy, is_reasoning
    if text is None:
        return
    text = text.strip()
    if not text:
        return

    if text == '#exit':
        active_app.exit()
        return

    if text == '#pause':
        cnm.mslock = False
        append_output_system('已发送暂停指令')
        return

    if is_busy:
        append_output_system('当前正在处理上一条消息，请稍候...')
        return

    global auto_scroll
    auto_scroll = True
    append_output_user(text)
    is_busy = True
    is_reasoning = True
    threading.Thread(target=agent_worker, args=(text,), daemon=True).start()


async def update_loop():
    global is_reasoning, spinner_index, output_window
    last_height = None
    while True:
        try:
            current_height = get_visible_height()
            if current_height != last_height:
                last_height = current_height
                refresh_output()

            if cnm.msg_stack:
                is_reasoning = False
                while cnm.msg_stack:
                    msg = cnm.msg_stack.pop(0)
                    append_output_agent(msg)

            if is_reasoning:
                spinner_index = (spinner_index + 1) % len(BAR)
                status_control.text = HTML(
                    f'<ansigreen>{BAR[spinner_index]} 思考中...</ansigreen>'
                    f' <ansigray>· 模型 {MODEL_NAME}</ansigray>'
                )
            else:
                status_control.text = HTML(
                    f'<ansigreen>●</ansigreen>'
                    f' <ansigray>就绪 · 模型 {MODEL_NAME}</ansigray>'
                )

            if app is not None:
                app.invalidate()
        except Exception:
            pass
        await asyncio.sleep(0.1)


kb = KeyBindings()


@kb.add('enter')
def _(event):
    text = input_buffer.text
    input_buffer.reset()
    handle_submit(text, event.app)


@kb.add('c-j')
def _(event):
    input_buffer.insert_text('\n')
    event.app.invalidate()


@kb.add('c-c')
def _(event):
    event.app.exit()


@kb.add('up')
def _(event):
    scroll_up(event)


@kb.add('down')
def _(event):
    scroll_down(event)


async def main():
    global app, output_control, output_window, input_buffer, status_control, output_lines, scroll_offset, auto_scroll

    output_lines = []
    for line in BANNER.strip('\n').split('\n'):
        output_lines.append(('class:banner', line))
    output_lines.append(('class:system', '[系统] Enter 发送 | Ctrl+J 换行 | #help 查看命令 | #exit 退出'))
    scroll_offset = len(output_lines)
    auto_scroll = True

    output_control = FormattedTextControl(text=[], focusable=False)
    input_buffer = Buffer(multiline=True)
    status_control = FormattedTextControl(text=HTML('<ansigray>就绪</ansigray>'))

    output_window = Window(
        content=output_control,
        wrap_lines=True,
        style='class:output',
    )
    input_prompt_window = Window(
        width=6,
        content=FormattedTextControl([('class:prompt', '❯ 你: ')]),
        style='class:prompt',
    )
    input_window = Window(
        content=BufferControl(buffer=input_buffer, focusable=True),
        wrap_lines=True,
        style='class:input',
    )
    input_container = VSplit([input_prompt_window, input_window], height=3)
    separator = Window(height=1, char='━', style='class:separator')
    status_window = Window(content=status_control, height=1, style='class:status')

    root = HSplit([
        output_window,
        separator,
        status_window,
        input_container,
    ])

    layout = Layout(container=root, focused_element=input_window)

    style = Style.from_dict({
        'output': 'fg:#d4d4d4',
        'input': 'fg:#ffffff',
        'prompt': 'bold fg:#00ff87',
        'status': 'fg:#aaaaaa bg:#2d2d2d',
        'banner': 'fg:#00d4ff',
        'user': 'bold fg:#ffb86c',
        'agent': 'fg:#e4e4e4',
        'system': 'fg:#8a8a8a',
        'separator': 'fg:#444444',
    })

    app = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=True,
        style=style,
        mouse_support=False,
    )

    refresh_output()

    task = asyncio.create_task(update_loop())
    await app.run_async()
    task.cancel()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass