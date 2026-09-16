from tools import fileedit,memory
from prompt_loader import prompt
import tools.tool_handler as tool
import tools.bot as bot
import tools.lang as lang
import tools.tag_parser as tag_parser
import tools.multymodalhandler as multymodel
import copy,json,time,threading,os,sys,subprocess
if not os.path.exists('./logs'):
    os.makedirs('./logs')
if not os.path.exists('./bak'):
    os.makedirs('./bak')

msg_stack = []

class SubAgent():
    def __init__(self,task,number=0):
        self.task = task
        self.number = number
        with open('./config/config.json',encoding='utf-8') as f:
            self.config = json.load(f)
        self.TIME_STAMP = round(time.time())
        self.stage_break = self.config['break']
        self.prompt = prompt.load('sub_agent_base')
        self.nodelist = {}
        self.nodelist['init'] = [0]
        self.messages = [
            {
                "role":"system",
                "content":self.prompt
            }
        ]
        self.toolcall = [['none']]
        self.msg = self.nodelist['init']
        self.tic = 1
        self.cmd_check = []
        self.mslock = True
        self.enable_log = self.config['enable_log']

    def _reset(self):
        bot.reload()
        with open('./config/config.json',encoding='utf-8') as f:
            self.config = json.load(f)
        self.TIME_STAMP = round(time.time())
        self.prompt = prompt.load('sub_agent_base')
        self.nodelist['init'] = [0]
        self.messages = [
            {
                "role":"system",
                "content":self.prompt
            }
        ]
        self.msg = self.nodelist['init']
        self.tic = 1

    def set_prompt(self,p):
        self.prompt = prompt.load(p)
        self.TIME_STAMP = round(time.time())
        self.nodelist = {}
        self.nodelist['init'] = [0]
        self.messages = [
            {
                "role":"system",
                "content":self.prompt
            }
        ]
        self.msg = self.nodelist['init']
        self.tic = 1

    def log(self):
        if self.enable_log:
            with open(f'./logs/subagent{self.number}_{self.TIME_STAMP}.json','w',encoding='utf-8') as f:
                json.dump(self.messages,f,indent=4,ensure_ascii=False)
            with open(f'./logs/subagent{self.number}_{self.TIME_STAMP}_node.json','w',encoding='utf-8') as f:
                json.dump(self.nodelist,f,indent=4,ensure_ascii=False)
            with open(f'./logs/subagent{self.number}_{self.TIME_STAMP}_tool.json','w',encoding='utf-8') as f:
                json.dump(self.toolcall,f,indent=4,ensure_ascii=False)

    def submission(self):
        msg_stack.append(f'SubAgent{self.number}: START')
        cmd = copy.deepcopy(self.task)
        while True:
            self.messages.append(multymodel.user(cmd))
            self.msg.append(self.tic)
            self.tic += 1
            post = []
            for i in self.msg:
                post.append(self.messages[i])
            response = bot.reply(post)
            #c = input()
            #response = {"content":c,
            #            "reasoning_content":None}
            if response:
                content = response.get('content')
                reasoning_content = response.get('reasoning_content')
            else:
                content = lang.lang['cnmd.bot.responsefail']
                reasoning_content = lang.lang['cnmd.bot.responsefail']
            calls,text = tag_parser.parse(content)
            for i in calls:
                i = i.strip()
                if i[:7] == 'report ':
                    msg_stack.append(f'SubAgent{self.number}: FINISH')
                    return i[7:]
            if calls == [] and '<tool_call>' not in content:
                if text == '':
                    msg_stack.append(f'SubAgent{self.number}:{lang.lang['cnmd.bot.responsefailcontinue']}')
                else:
                    msg_stack.append(f'SubAgent{self.number}:{text}')
                self.messages.append(
                    {
                        "role": "system",
                        "content": content
                    }
                )
                self.msg.append(self.tic)
                self.tic += 1
                self.toolcall.append(['none'])
                self.log()
            elif calls == [] and '<tool_call>' in content:
                if text == '':
                    msg_stack.append(f'SubAgent{self.number}:{lang.lang['cnmd.bot.responsefailcontinue']}')
                else:
                    msg_stack.append(f'SubAgent{self.number}:{text}')
                self.messages.append(
                    {
                        "role": "system",
                        "content": content
                    }
                )
                self.msg.append(self.tic)
                self.tic += 1
                self.toolcall.append(['none'])
                self.log()
                cmd = lang.lang['cnmd.bot.callfail']
            else:
                self.messages.append(
                    {
                        "role": "system",
                        "content": content
                    }
                )
                self.msg.append(self.tic)
                self.tic += 1
                self.toolcall.append(calls)
                self.log()
                try:
                    if self.cmd_check != [] and self.cmd_check == calls:
                        msg_stack.append(f'SubAgent{self.number}:{lang.lang['cnmd.bot.refuse']}')
                        cmd = lang.lang['bot.tool.refuse']
                    else:
                        cmd = '[A]tool call feedback:\n'
                        for i in calls:
                            toolcall = tool.tool(i)
                            cmd += f'{toolcall['sys']}\n---\n'
                            msg_stack.append(f'SubAgent{self.number}:{toolcall['cli']}')

                except Exception as e:
                    msg_stack.append(f'SubAgent{self.number}:{lang.lang['cnmd.base.error']}{str(e)}')
                    cmd = f'{lang.lang['bot.base.error']}{str(e)}'
        return

def startsubagent():
    if sys.platform.startswith("win"):
        cmd = 'start "" cmd /k "python SynapseAgent_SubAgent.py"'
        subprocess.Popen(cmd, shell=True)
    elif sys.platform == "darwin":
        subprocess.Popen(["osascript", "-e",
                          'tell application "Terminal" to do script "python SynapseAgent_SubAgent.py"'])
    else:
        args = ["gnome-terminal", "--", "bash", "-c",
                "python SynapseAgent_SubAgent.py; exec bash"]
        subprocess.Popen(args)

def stack_print(stack):
    while True:
        if stack:
            item = stack.pop(0)
            print(item)
        time.sleep(0.5)

if __name__ == '__main__':
    CNM = SubAgent('test')
    t = threading.Thread(target=stack_print,args=(msg_stack,),daemon=True)
    t.start()
    while True:
        print('======================================')
        CNM.submission()