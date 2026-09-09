import os
import sys
import json
import re
import time
import threading
import tools.lang as lang
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

import tools.subagent as subagent
from tools.color_utils import Color

print(f'{Color.CYAN}{Color.BRIGHT}')
print(r"╭──────────────────────────────────────────╮")
print(r"│     //  \\                               |")
print(r"│     \\  //           SynapseAgent        |")
print(r"│       ||         ────────────────────    |")
print(r"│    //    \\         SubAgent Runner      |")
print(r"│ //  \\  //  \\                           |")
print(r"│ \\  //  \\  //                           |")
print(r"╰──────────────────────────────────────────╯")
print(f"{Color.RESET}")
print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')

msg_stack = subagent.msg_stack

json_lock = threading.Lock()
color_map = {}

TASK_COLORS = [
    Color.RED,
    Color.GREEN,
    Color.YELLOW,
    Color.BLUE,
    Color.MAGENTA,
    Color.CYAN,
    Color.WHITE,
]

def load_tasks(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def assign_colors(tasks):
    for idx, item in enumerate(tasks):
        number = item.get('number', idx)
        color_map[number] = TASK_COLORS[idx % len(TASK_COLORS)]


def update_report(file_path, number, report):
    with json_lock:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            if item.get('number') == number:
                item['report'] = report
                break

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


def run_task(file_path, item):
    number = item.get('number', 0)
    task = item.get('task', '')
    if not isinstance(task, str):
        task = str(task)

    agent = subagent.SubAgent(task, number=number)
    report = agent.submission()
    update_report(file_path, number, report)


def process_thread():
    while True:
        if msg_stack:
            first_element = msg_stack.pop(0)

            while '\n\n' in first_element:
                first_element = first_element.replace('\n\n', '\n')

            match = re.match(r'^SubAgent(\d+):(.*)$', first_element, re.DOTALL)
            if match:
                number = int(match.group(1))
                content = match.group(2)
                color = color_map.get(number, Color.WHITE)

                print(f"{color}●{Color.RESET} {color}SubAgent{number}{Color.RESET}")
                print(f"{color}{content}{Color.RESET}")
            else:
                print(f"{Color.MAGENTA}●{Color.RESET} {Color.CYAN}Assistant{Color.RESET}")
                print(f"{Color.BLUE}{first_element}{Color.RESET}")

            if not msg_stack:
                try:
                    width = os.get_terminal_size().columns
                except Exception:
                    width = 80
                print(f'{Color.WHITE}{"─" * (width - 1)}{Color.RESET}')

        time.sleep(0.1)


def main():
    print(lang.lang['subagent.task.gettasklist'])
    file_path = input().strip().strip('"').strip("'")
    file_path = os.path.abspath(file_path)

    tasks = load_tasks(file_path)
    assign_colors(tasks)

    output_thread = threading.Thread(target=process_thread, daemon=True)
    output_thread.start()

    task_threads = []
    for item in tasks:
        t = threading.Thread(target=run_task, args=(file_path, item), daemon=True)
        t.start()
        task_threads.append(t)

    for t in task_threads:
        t.join()

    while msg_stack:
        time.sleep(0.1)
    time.sleep(0.2)

    print()
    print(lang.lang['subagent.task.taskdone'])

if __name__ == "__main__":
    main()