from src.tools import fileedit
from src.tools import memory
from prompt_loader import prompt
import src.tools.tool_handler as tool
import src.tools.bot as bot
import src.tools.lang as lang
import src.tools.tag_parser as tag_parser
import src.tools.multymodalhandler as multymodel
import copy,json,time,threading,os
import src.tools.guide as guide
if not os.path.exists('./logs'):
    os.makedirs('./logs')
if not os.path.exists('./bak'):
    os.makedirs('./bak')
USR_COMMAND = [
    '#help',
    '#node save',
    '#node load',
    '#node list',
    '#node backward',
    '#node backwardms',
    '#backup',
    '#help',
    '#bot reasoning',
    '#bot reset',
    '#bot reload',
    '#bot prompt',
    '#mem save',
    '#mem analyse',
    '#mem compress',
    '#execute',
    '#memory',
    '#dream',
    '#subagent'
    ]

REPLACE_STRING_START = f'<{'tool_call'}>'
REPLACE_STRING_END = f'</{'tool_call'}>'

class CNMD():
    def _load_config(self):
        with open('./config/config.json',encoding='utf-8') as f:
            self.config = json.load(f)
        with open('./config/config_intercept.json',encoding='utf-8') as f:
            self.intercept = json.load(f)

    def __init__(self,prompt_init = 'agent_base', subagent=False, number=0):
        self._load_config()
        self.TIME_STAMP = round(time.time())
        self.stage_break = self.config['break']
        self.prompt_init = prompt_init
        self.prompt = prompt.load(self.prompt_init)
        self.msg_stack = []
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
        self.allow_reasoning = False
        self.allow_cmd = self.config['cmd_check']
        self.cmd_check = []
        self.mslock = True
        self.enable_log = self.config['enable_log']
        self.status = 0
        self.help_text = lang.text['cnmd.helptext']
        self.subagent_mode = subagent
        self.number = number
        self.report = ''
        if self.subagent_mode:
            self.allow_cmd = False
            self.stage_break = False
            self.mslock = True

    def _similarity(self,str1, str2):
        set1 = set(str1)
        set2 = set(str2)
        intersection = set1 & set2
        union = set1 | set2
        if not union:
            return 1.0 if not intersection else 0.0
        return len(intersection) / len(union)

    def _correction(self,str):
        s = {}
        for i in USR_COMMAND:
            s[i] = self._similarity(str,i)
        self.msg_stack.append(f'{lang.lang['cnmd.base.notfound']}{max(s,key=s.get)}')

    def _compress_number(self,nums):
        result = []
        start = nums[0]
        for i in range(1, len(nums)):
            if nums[i] != nums[i-1] + 1:
                end = nums[i-1]
                if start == end:
                    result.append(str(start))
                else:
                    result.append(f"{start}-{end}")
                start = nums[i]
        if start == nums[-1]:
            result.append(str(start))
        else:
            result.append(f"{start}-{nums[-1]}")
        return ",".join(result)

    def _user_command(self,cmd:str):
        cmd = cmd.strip()
        ori_cmd = copy.deepcopy(cmd)
        cmd = cmd.split(maxsplit=1)
        if cmd[0] == '#node':
            cmd[1] = cmd[1].split(maxsplit=1)
            if cmd[1][0] == 'save':
                self.nodelist[cmd[1][1]] = copy.deepcopy(self.msg)
                self.msg_stack.append(f'{lang.lang['cnmd.node.savecomplete']}{cmd[1][1]}')
                return
            if cmd[1][0] == 'delete':
                tlist = {k: v for k, v in self.nodelist.items() if k != cmd[1][1]}
                if self.nodelist == tlist:
                    self.msg_stack.append(f'{lang.lang['cnmd.node.delunsuccess']}')
                    return
                else:
                    self.nodelist = copy.deepcopy(tlist)
                    self.msg_stack.append(f'{lang.lang['cnmd.node.delcomplete']}{cmd[1][1]}')
                    return
            elif cmd[1][0] == 'load':
                temp = self.nodelist.get(cmd[1][1])
                if temp:
                    self.msg = copy.deepcopy(self.nodelist.get(cmd[1][1]))
                    self.msg_stack.append(f'{lang.lang['cnmd.node.loadcomplete']}{cmd[1][1]}')
                    return
                else:
                    self.msg_stack.append(f'{lang.lang['cnmd.node.nodenotfound']}')
                    return
            elif cmd[1][0] == 'savef':
                temp = cmd[1][1]
                if temp:
                    try:
                        with open(f'./logs/{temp}.json','w',encoding='utf-8') as f:
                            json.dump(self.messages,f,indent=4,ensure_ascii=False)
                        with open(f'./logs/{temp}_node.json','w',encoding='utf-8') as f:
                            json.dump(self.nodelist,f,indent=4,ensure_ascii=False)
                        with open(f'./logs/{temp}_tool.json','w',encoding='utf-8') as f:
                            json.dump(self.toolcall,f,indent=4,ensure_ascii=False)
                        self.msg_stack.append(lang.lang['cnmd.log.savecomplete'])
                        return
                    except Exception as e:
                        self.msg_stack.append(lang.lang['cnmd.log.filenotfound'])
                        return
                else:
                    self.msg_stack.append(lang.lang['cnmd.log.filenotfound'])
                    return
            elif cmd[1][0] == 'loadf':
                temp = cmd[1][1]
                if temp:
                    try:
                        with open(f'./logs/{temp}.json','r',encoding='utf-8') as f:
                            self.messages = json.load(f)
                        with open(f'./logs/{temp}_node.json','r',encoding='utf-8') as f:
                            self.nodelist = json.load(f)
                        with open(f'./logs/{temp}_tool.json','r',encoding='utf-8') as f:
                            self.toolcall = json.load(f)
                        self.msg_stack.append(lang.lang['cnmd.log.loadcomplete'])
                        self.msg_stack.append(self._gen_context())
                        return
                    except Exception as e:
                        self.msg_stack.append(lang.lang['cnmd.log.filenotfound'])
                        return
                else:
                    self.msg_stack.append(lang.lang['cnmd.log.filenotfound'])
                    return
            elif cmd[1][0] == 'list':
                temp = f'{lang.lang['cnmd.node.nodelist']}\n'
                for key,value in self.nodelist.items():
                    temp += f'{key} [{self._compress_number(value)}]\n'
                self.msg_stack.append(temp.strip())
                return
            elif cmd[1][0] == 'backward':
                if len(self.msg) == 1:
                    self.msg_stack.append(lang.lang['cnmd.node.backwardunable'])
                self.nodelist['temp'] = copy.deepcopy(self.msg)
                try:
                    self.msg = self.msg[:-2*int(cmd[1][1])]
                    self.msg_stack.append(f'{lang.lang['cnmd.node.backwardcount']}{cmd[1][1]}')
                    return
                except:
                    self.msg = self.msg[:-2]
                    self.msg_stack.append(lang.lang['cnmd.node.backward'])
                    return
            elif cmd[1][0] == 'backwardms':
                self.msg = copy.deepcopy(self.mstemp)
                self.msg_stack.append(lang.lang['cnmd.node.backward'])
                return
            else:
                self._correction(ori_cmd)
                return
        elif cmd[0] == '#help':
            self.msg_stack.append(self.help_text)
            return
        elif cmd[0] == '#bot':
            cmd[1] = cmd[1].split(maxsplit=1)
            if cmd[1][0] == 'reasoning':
                if cmd[1][1] == 'on' or cmd[1][1] == 'true' or cmd[1][1] == 'True' or cmd[1][1] == '1':
                    self.allow_reasoning = True
                    self.msg_stack.append(lang.lang['cnmd.bot.reasoningon'])
                    return
                elif cmd[1][1] == 'off' or cmd[1][1] == 'false' or cmd[1][1] == 'False' or cmd[1][1] == '0':
                    self.allow_reasoning = False
                    self.msg_stack.append(lang.lang['cnmd.bot.reasoningoff'])
                    return
                else:
                    self._correction(ori_cmd)
                    return
            elif cmd[1][0] == 'prompt':
                self.set_prompt(cmd[1][1])
                return
            elif cmd[1][0] == 'reset':
                self._reset()
                return
            elif cmd[1][0] == 'reload':
                bot.reload()
                self.msg_stack.append(lang.lang['cnmd.bot.reload'])
                return
            else:
                self._correction(ori_cmd)
                return
        elif cmd[0] == '#backup':
            fileedit.backup(self.config['base_path'])
            self.msg_stack.append(lang.lang['cnmd.base.backup'])
        elif cmd[0] == '#mem':
            if cmd[1] == 'save':
                post = []
                for i in self.msg:
                    post.append(self.messages[i])
                memory.save(post)
                self.msg_stack.append(lang.lang['cnmd.mem.save'])
            elif cmd[1] == 'compress':
                post = []
                for i in self.msg:
                    post.append(self.messages[i])
                content = memory.compress(post)
                self._reset(compress=content)
                self.msg_stack.append(lang.lang['cnmd.mem.compress'])
            elif cmd[1] == 'analyse':
                memory.analyse()
                self.msg_stack.append(lang.lang['cnmd.mem.analyse'])
            else:
                self._correction(ori_cmd)
        elif cmd[0] == '#memory':
            post = []
            for i in self.msg:
                post.append(self.messages[i])
            memory.save(post)
            self.msg_stack.append(lang.lang['cnmd.mem.save'])
        elif cmd[0] == '#dream':
            memory.analyse()
            self.msg_stack.append(lang.lang['cnmd.mem.analyse'])
        elif cmd[0] == '#skipable':
            tool.SKIP_CALL = cmd[1].split()
            self.msg_stack.append(f'{lang.lang['cnmd.base.skipable']}{cmd[1]}')
        elif cmd[0] == '#subagent':
            args = cmd[1].strip() if len(cmd) > 1 else None
            result = tool.subagent_status(args)
            self.msg_stack.append(result['sys'])
            return
        else:
            self._correction(ori_cmd)

    def _reset(self,compress=None):
        bot.reload()
        self._load_config()
        self.stage_break = self.config['break']
        self.allow_cmd = self.config['cmd_check']
        self.enable_log = self.config['enable_log']
        self.cmd_check = []
        self.TIME_STAMP = round(time.time())
        self.prompt = prompt.load(self.prompt_init)
        self.nodelist['init'] = [0]
        if compress != None:
            self.prompt = f'{self.prompt}{lang.lang['bot.compress.log']}{compress}'
        self.messages = [
            {
                "role":"system",
                "content":self.prompt
            }
        ]
        self.msg = self.nodelist['init']
        self.tic = 1
        self.msg_stack.append(lang.lang['cnmd.bot.reset'])

    def set_prompt(self,p:str):
        self.prompt_init = p
        self.prompt = prompt.load(self.prompt_init)
        self.cmd_check = []
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
        self.msg_stack.append(lang.lang['cnmd.bot.setprompt'])

    def _content_to_text(self, content, multimodal_filter=False):
        if content is None:
            return ''
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text = ''
            for i in content:
                if isinstance(i, dict):
                    if i.get('type') == 'text':
                        text += i.get('text', '')
                    elif not multimodal_filter:
                        text += f"[{i.get('type')}]"
                else:
                    text += str(i)
            return text
        return str(content)

    def _gen_context(self, limit=10):
        turns = []
        user_text = None
        agent_text = []
        for i in self.messages[1:]:
            if not isinstance(i, dict):
                continue
            role = i.get('role')
            if role == 'user':
                text = self._content_to_text(i.get('content'), multimodal_filter=True)
                if text.lstrip().startswith('[A]tool call feedback'):
                    continue
                if text.lstrip().startswith('[A]subagent report'):
                    continue
                if user_text is not None:
                    turns.append((user_text, '\n'.join(agent_text).strip()))
                user_text = text
                agent_text = []
            elif role == 'system':
                text = self._content_to_text(i.get('content'))
                plain = tag_parser.parse(text)[1].strip()
                if plain != '':
                    agent_text.append(plain)
        if user_text is not None:
            turns.append((user_text, '\n'.join(agent_text).strip()))
        prefix = ''
        if len(turns) > limit:
            turns = turns[-limit:]
            prefix = '...\n'
        out = prefix
        for user, agent in turns:
            out += f'> User:\n{user}\n\n> Agent:\n{agent}\n\n'
        return out.strip()

    def _intercept_check(self,text):
        for i in self.intercept:
            if i in text:
                return True
        return False

    def log(self):
        if self.enable_log:
            if self.subagent_mode:
                tag = f'subagent{self.number}_{self.TIME_STAMP}_{threading.get_ident()}'
            else:
                tag = f'{self.TIME_STAMP}'
            with open(f'./logs/{tag}.json','w',encoding='utf-8') as f:
                json.dump(self.messages,f,indent=4,ensure_ascii=False)
            with open(f'./logs/{tag}_node.json','w',encoding='utf-8') as f:
                json.dump(self.nodelist,f,indent=4,ensure_ascii=False)
            with open(f'./logs/{tag}_tool.json','w',encoding='utf-8') as f:
                json.dump(self.toolcall,f,indent=4,ensure_ascii=False)

    def _exec_calls(self, calls):
        """统一执行一组工具调用，只产出普通工具反馈。
        子代理报告不在此处理，改由 _inject_subagent_reports 在发送给模型前注入。
        """
        feedback = ''
        for i in calls:
            toolcall = tool.tool(i)
            feedback += f'{toolcall['sys']}\n---\n'
            self.msg_stack.append(toolcall['cli'])
        if feedback.strip() == '':
            return ''
        return f'[A]tool call feedback:\n{feedback}'

    def _inject_subagent_reports(self, cmd):
        """在把消息发送给模型之前，固定查询子代理共享状态并注入报告，取走即清。
        无报告时原样返回 cmd（即拼接空字符串）；有报告则追加到 cmd 之后。
        不中断循环，仅影响本轮发给模型的上下文。
        """
        reports = tool.pop_subagent_reports()
        lines = []
        for r in reports:
            rep = (r.get('report') or '').strip()
            if rep != '':
                lines.append(f'[{r['number']}] {rep}')
        if not lines:
            return cmd
        report_text = '[A]subagent report:\n' + '\n'.join(lines) + '\n'
        if cmd is None or cmd.strip() == '':
            return report_text
        return f'{cmd}\n{report_text}'

    def CNMD(self,cmd):
        self.status = 1
        if cmd[0] == '#':
            if '#execute' not in cmd and '#e' not in cmd:
                self._user_command(cmd)
                self.status = 0
                return
            else:
                if len(cmd.split()) == 1:
                    cmd = self._exec_calls(self.cmd_check)
                else:
                    c = cmd.split()[1:]
                    calls = [self.cmd_check[int(i)] for i in c]
                    cmd = self._exec_calls(calls)

        self.mstemp = copy.deepcopy(self.msg)
        while True and self.mslock:
            if '<toolcall>PAUSE</toolcall>'.replace('toolcall','tool_call') in cmd:
                self.status = 0
                return
            if not self.subagent_mode:
                cmd = self._inject_subagent_reports(cmd)
            self.messages.append(multymodel.user(cmd))
            self.msg.append(self.tic)
            self.tic += 1
            post = []
            for i in self.msg:
                post.append(self.messages[i])
            response = bot.reply(post)
            #c = input()
            #response = {"content":c,"reasoning_content":"bruh!"}
            if response:
                content = response.get('content')
                reasoning_content = response.get('reasoning_content')
                if reasoning_content and self.allow_reasoning:
                    reasoning_content = tag_parser.strip_tags(reasoning_content)
                    self.msg_stack.append(f'reasoning: {reasoning_content}')
            else:
                content = lang.lang['cnmd.bot.responsefail']
                reasoning_content = lang.lang['cnmd.bot.responsefail']
            calls,text = tag_parser.parse(content)
            if self.subagent_mode:
                report_found = None
                for i in calls:
                    s = i.strip()
                    if s[:7] == 'report ':
                        report_found = s[7:]
                        break
                if report_found is not None:
                    self.messages.append(
                        {
                            "role": "system",
                            "content": content
                        }
                    )
                    self.msg.append(self.tic)
                    self.tic += 1
                    self.toolcall.append(['report'])
                    self.report = report_found
                    self.log()
                    break
            if calls == [] and self._intercept_check(content):
                self.msg_stack.append(f'{lang.lang['cnmd.bot.toolunknown']}')
                text = tag_parser.strip_tags(text)
                self.msg_stack.append(text)
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
            elif calls == [] and '<toolcall>'.replace('toolcall','tool_call') not in content:
                if text == '':
                    self.msg_stack.append(lang.lang['cnmd.bot.responsefailcontinue'])
                else:
                    text = tag_parser.strip_tags(text)
                    self.msg_stack.append(text)
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
                if not self.subagent_mode and tool.has_running_subagent():
                    self.msg_stack.append(lang.lang['cnmd.subagent.pending'])
                break
            elif calls == [] and '<toolcall>'.replace('toolcall','tool_call') in content:
                if text == '':
                    self.msg_stack.append(lang.lang['cnmd.bot.responsefailcontinue'])
                else:
                    text = tag_parser.strip_tags(text)
                    self.msg_stack.append(text)
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
                if text != '':
                    text = tag_parser.strip_tags(text)
                    self.msg_stack.append(text)
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
                        if self.stage_break:
                            self.msg_stack.append(lang.lang['cnmd.bot.refuse'])
                            self.cmd_check = []
                            break
                        else:
                            self.msg_stack.append(lang.lang['cnmd.bot.refuse'])
                            cmd = lang.lang['bot.tool.refuse']
                            self.cmd_check = []
                    else:
                        self.cmd_check = copy.deepcopy(calls)
                        if not self.allow_cmd:
                            cmd = self._exec_calls(calls)
                        else:
                            cmd = lang.lang['cnmd.base.cmd']
                            k = 0
                            for i in calls:
                                cmd += f'[{k}] {i[:30] if len(i) > 30 else i}'
                                k += 1
                            self.msg_stack.append(cmd)
                            break
                except Exception as e:
                    self.msg_stack.append(f'{lang.lang['cnmd.base.error']}{str(e)}')
                    cmd = f'{lang.lang['bot.base.error']}{str(e)}'
        if self.mslock == False:
            self.mslock = True
            self.msg_stack.append(lang.lang['cnmd.base.pause'])
        self.cmd_check = []
        self.status = 0
        return
