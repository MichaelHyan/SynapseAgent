import tools.guide as guide
import CNMD
import threading, time, copy, os, sys, argparse
from tools import lang
from tools.color_utils import Color

input_list = ''
parser = argparse.ArgumentParser()
parser.add_argument('name', nargs='?', default='agent_base')
args = parser.parse_args()

cnm = CNMD.CNMD()
cnm.set_prompt(args.name)

is_reasoning = False
BAR = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'

def print_banner():
    print()
    print(f'{Color.CYAN}{Color.BRIGHT}')
    print(r"╭──────────────────────────────────────────╮")
    print(r"│     //  \\                               |")
    print(r"│     \\  //           SynapseAgent        |")
    print(r"│       ||         ────────────────────    |")
    print(r"│    //    \\         Think Backward       |")
    print(r"│ //  \\  //  \\       And Re:Start!       |")
    print(r"│ \\  //  \\  //                           |")
    print(r"╰──────────────────────────────────────────╯")
    print(f"{Color.RESET}")
    print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')

def input_thread():
    global input_list, cnm, is_reasoning
    while True:
        try:
            user_input = input()
            
            if user_input == '' and input_list != '':
                threading.Thread(target=agent_thread).start()
                print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')
                is_reasoning = True
            elif user_input == '#pause':
                print(f'{Color.RED}{lang.lang['cnmd.base.pause']}{Color.RESET}')
                cnm.mslock = False
            elif user_input == '#exit':
                print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')
                os._exit(0)
            elif user_input == '' and input_list == '':
                pass
            else:
                input_list += user_input
        except Exception as e:
            pass

def agent_thread():
    global input_list
    temp = copy.deepcopy(input_list)
    input_list = ''    
    cnm.CNMD(temp)

def process_thread():
    global is_reasoning
    while True:
        if cnm.msg_stack:
            is_reasoning = False
            sys.stdout.write(f'\r{" " * 20}\r')
            sys.stdout.flush()
            first_element = cnm.msg_stack.pop(0)
            if cnm.msg_stack:
                pass
            else:
                print(f"{Color.MAGENTA}●{Color.RESET} {Color.CYAN}Assistant{Color.RESET}")
            while '\n\n' in first_element:
                first_element = first_element.replace('\n\n','\n')
            print(f"{Color.BLUE}{first_element}{Color.RESET}")
            if not cnm.msg_stack:
                print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')
        time.sleep(0.1)

def reasoning_thread():
    global is_reasoning
    i = 0
    prev_is_reasoning = False
    
    while True:
        if is_reasoning:
            sys.stdout.write(f'\r{Color.GREEN}{BAR[i % len(BAR)]}{Color.RESET} 思考中...')
            sys.stdout.flush()
            i += 1
            prev_is_reasoning = True
        elif prev_is_reasoning:
            sys.stdout.write(f'\r{" " * 30}\r')
            sys.stdout.flush()
            prev_is_reasoning = False
        
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