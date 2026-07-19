from tools.color_utils import Color
import time,os,json
def main():
    print(f'{Color.RED}未检测到配置文件，已启动引导程序。\nNo configuration file detected, bootloader started.{Color.RESET}')
    print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')
    time.sleep(1)
    print(f'{Color.WHITE}欢迎使用突触助理。\nWelcome to {Color.CYAN}S{Color.WHITE}ynapse {Color.CYAN}A{Color.WHITE}gent')
    print(f'在我们开始前，请回答以下问题。\nBefore we get started, please answer the following questions.')
    print(f'配置结束后，突触助理将在本目录下创建{Color.RED}配置文件{Color.RESET}。如果你需要更改配置，可以随时访问{Color.RED}config.py{Color.RESET}。\nAfter the setup is complete, Synapse Agent will create the {Color.RED}configuration file{Color.RESET} in this directory. If you need to change the settings, you can access {Color.RED}config.py{Color.RESET} anytime.')

    print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')
    print(f'{Color.MAGENTA}●{Color.RESET}你所使用的语言是？(zh_cn:简体中文)\nWhat language do you prefer?(en_us:English)')
    while True:
        lang = input(f'{Color.GREEN}>{Color.RESET}').strip()
        if lang == 'zh_cn':
            print(f'{Color.CYAN}●{Color.RESET}设置语言为简体中文。')
            break
        elif lang == 'en_us':
            print(f'{Color.CYAN}●{Color.RESET}language set English')
            break
        else:
            print(f'{Color.RED}×{Color.RESET}目前不支持该语言，请选择{Color.RED}zh_cn{Color.RESET}或{Color.RED}en_us{Color.RESET}。\n{Color.RED}×{Color.RESET}This language is not supported at the moment, please choose {Color.RED}zh_cn{Color.RESET} or {Color.RED}en_us{Color.RESET}.')
    
    print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')
    if lang == 'zh_cn':
        print(f'{Color.MAGENTA}●{Color.RESET}你希望助理使用的{Color.CYAN}工作目录{Color.RESET}是什么？请输入{Color.CYAN}绝对路径{Color.RESET}，使用"/"分隔。')
        base_path = input(f'{Color.GREEN}>{Color.RESET}').strip()
        print(f'{Color.CYAN}●{Color.RESET}助理将使用目录: {Color.CYAN}{base_path}{Color.RESET}。')
    elif lang == 'en_us':
        print(f'{Color.MAGENTA}●{Color.RESET}What {Color.CYAN}working directory{Color.RESET} do you want the assistant to use? Please enter the {Color.CYAN}absolute path{Color.RESET}, using "/" to separate.')
        base_path = input(f'{Color.GREEN}>{Color.RESET}').strip()
        print(f'{Color.CYAN}●{Color.RESET}Agent will use directory: {Color.CYAN}{base_path}{Color.RESET}。')
    
    print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')
    if lang == 'zh_cn':
        print(f'{Color.MAGENTA}●{Color.RESET}当助理工作时，可能会请求一些{Color.CYAN}操作指令{Color.RESET}。你是希望在指令执行前先经过{Color.CYAN}你的同意{Color.RESET}？(y/n)')
        t = input(f'{Color.GREEN}>{Color.RESET}').strip()
        if t == 'y':
            cmd_check = True
            print(f'{Color.CYAN}●{Color.RESET}助理将向你申请指令，在得到批准后执行。')
        else:
            cmd_check = False
            print(f'{Color.CYAN}●{Color.RESET}助理将直接执行指令。')
    elif lang == 'en_us':
        print(f'{Color.MAGENTA}●{Color.RESET}When working as an assistant, you might be asked for some {Color.CYAN}operation instructions{Color.RESET}. Do you want to get {Color.CYAN}your approval{Color.RESET} before the instructions are executed? (y/n)')
        t = input(f'{Color.GREEN}>{Color.RESET}').strip()
        if t == 'y':
            cmd_check = True
            print(f'{Color.CYAN}●{Color.RESET}The assistant will ask you for instructions and carry them out once approved.')
        else:
            cmd_check = False
            print(f'{Color.CYAN}●{Color.RESET}The assistant will follow the instructions directly.')

    print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')
    if lang == 'zh_cn':
        print(f'{Color.MAGENTA}●{Color.RESET}当助理工作时，可能会错误的发送{Color.CYAN}重复指令{Color.RESET}造成循环。你是否在循环发生时立刻拦截回复？(y/n)')
        t = input(f'{Color.GREEN}>{Color.RESET}').strip()
        if t == 'y':
            tbreak = True
            print(f'{Color.CYAN}●{Color.RESET}Agent将立刻拦截重复指令。')
        else:
            tbreak = False
            print(f'{Color.CYAN}●{Color.RESET}Agent将提醒模型，但不会终止回复循环。')
    elif lang == 'en_us':
        print(f'{Color.MAGENTA}●{Color.RESET}When working as an assistant, you might accidentally send {Color.CYAN}duplicate commands{Color.RESET}, causing a loop. Do you want to intercept the reply immediately if a loop occurs? (y/n)')
        t = input(f'{Color.GREEN}>{Color.RESET}').strip()
        if t == 'y':
            tbreak = True
            print(f'{Color.CYAN}●{Color.RESET}The agent will immediately intercept duplicate commands.')
        else:
            tbreak = False
            print(f'{Color.CYAN}●{Color.RESET}The agent will remind the model, but it won’t stop the reply loop.')

    print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')
    if lang == 'zh_cn':
        print(f'{Color.MAGENTA}●{Color.RESET}是否启用{Color.CYAN}调试模式{Color.RESET}？如启用将在本地留下会话记录，存储在./logs/目录中。可能会造成{Color.RED}大量空间占用{Color.RESET}，需定期删除。(y/n)')
        t = input(f'{Color.GREEN}>{Color.RESET}').strip()
        if t == 'y':
            enable_log = True
            print(f'{Color.CYAN}●{Color.RESET}调试模式启用。')
        else:
            enable_log = False
            print(f'{Color.CYAN}●{Color.RESET}调试模式禁用。')
    elif lang == 'en_us':
        print(f'{Color.MAGENTA}●{Color.RESET}Enable {Color.CYAN}debug mode{Color.RESET}? If enabled, it will leave session logs locally, stored in the ./logs/ directory. This may {Color.RED}take up a lot of space{Color.RESET}, so you need to delete them regularly. (y/n)')
        t = input(f'{Color.GREEN}>{Color.RESET}').strip()
        if t == 'y':
            enable_log = True
            print(f'{Color.CYAN}●{Color.RESET}Debug mode enabled.')
        else:
            enable_log = False
            print(f'{Color.CYAN}●{Color.RESET}Debug mode disabled.')

    print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')
    if lang == 'zh_cn':
        print(f'接下来需要配置你的后端模型。你需要在任意大模型平台申请你的API KEY。')
        print(f'{Color.MAGENTA}●{Color.RESET}请输入你的{Color.CYAN}API KEY{Color.RESET}。')
        API_KEY = input(f'{Color.GREEN}>{Color.RESET}').strip()
        print(f'{Color.MAGENTA}●{Color.RESET}请输入你的{Color.CYAN}BASE URL{Color.RESET}。')
        BASE_URL = input(f'{Color.GREEN}>{Color.RESET}').strip()
        print(f'{Color.MAGENTA}●{Color.RESET}请输入你的{Color.CYAN}模型名{Color.RESET}。')
        MODEL = input(f'{Color.GREEN}>{Color.RESET}').strip()
    elif lang == 'en_us':
        print(f'Next, you need to set up your backend model. You’ll need to apply for your API KEY on any large model platform.')
        print(f'{Color.MAGENTA}●{Color.RESET}Please enter your {Color.CYAN}API KEY{Color.RESET}.')
        API_KEY = input(f'{Color.GREEN}>{Color.RESET}').strip()
        print(f'{Color.MAGENTA}●{Color.RESET}Please enter your {Color.CYAN}BASE URL{Color.RESET}.')
        BASE_URL = input(f'{Color.GREEN}>{Color.RESET}').strip()
        print(f'{Color.MAGENTA}●{Color.RESET}Please enter your {Color.CYAN}MODEL NAME{Color.RESET}.')
        MODEL = input(f'{Color.GREEN}>{Color.RESET}').strip()
    
    print(f'{Color.WHITE}{"─" * (os.get_terminal_size().columns-1)}{Color.RESET}')
    config = {}
    config['API_KEY'] = API_KEY
    config['BASE_URL'] = BASE_URL
    config['MODEL'] = MODEL
    config['base_path'] = base_path
    config['lang'] = lang
    config['break'] = tbreak
    config['cmd_check'] = cmd_check
    config['enable_log'] = enable_log

    if lang == 'zh_cn':
        print(f'请检查配置信息是否正确。如有问题请结束程序并重新配置。如没有问题请按回车键继续。')
        print(f'{Color.CYAN}●{Color.RESET}API KEY: {Color.RED}{config['API_KEY']}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}BASE URL: {Color.RED}{config['BASE_URL']}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}模型名: {Color.RED}{config['MODEL']}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}工作目录: {Color.RED}{config['base_path']}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}语言: {Color.RED}{config['lang']}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}重复指令是否中断: {Color.RED}{'是' if config['break'] else '否'}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}指令是否需要检查: {Color.RED}{'是' if config['break'] else '否'}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}是否使用调试模式: {Color.RED}{'是' if config['break'] else '否'}{Color.RESET}')
    elif lang == 'en_us':
        print(f'Please check if the configuration information is correct. If there is a problem, please terminate the program and reconfigure.If there are no issues, please press Enter to continue.')
        print(f'{Color.CYAN}●{Color.RESET}API KEY: {Color.RED}{config['API_KEY']}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}BASE URL: {Color.RED}{config['BASE_URL']}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}MODEL NAME: {Color.RED}{config['MODEL']}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}working directory: {Color.RED}{config['base_path']}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}language: {Color.RED}{config['lang']}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}intercept duplicate commands: {Color.RED}{'YES' if config['break'] else 'NO'}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}check operation instructions: {Color.RED}{'YES' if config['break'] else 'NO'}{Color.RESET}')
        print(f'{Color.CYAN}●{Color.RESET}enable debug mode: {Color.RED}{'YES' if config['break'] else 'NO'}{Color.RESET}')
    input()
    with open(f'./config.json','w',encoding='utf-8') as f:
        json.dump(config,f,indent=4,ensure_ascii=False)

    if lang == 'zh_cn':
        print(f'已生成配置文件。\n欢迎使用突触助理。')
    elif lang == 'en_us':
        print(f'Configuration file created。\nwelcome to {Color.CYAN}S{Color.WHITE}ynapse {Color.CYAN}A{Color.WHITE}gent.')
    time.sleep(1)

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

if not os.path.exists('./config.json'):
    print_banner()
    main()