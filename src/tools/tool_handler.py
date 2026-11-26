from src.tools import autogui, fileedit, lang, mcp_call, memory, runcmd, screenshot, skills, timer
from src.tools import webgrab
from src.tools import tag_parser
import json,time,copy,threading
import urllib.parse

_REGISTRY = {}
SKIP_CALL = []

REPLACE_STRING_START = f'<{'tool_call'}>'
REPLACE_STRING_END = f'</{'tool_call'}>'

_subagent_lock = threading.Lock()
_subagent_reports = []
_subagent_jobs = []
_subagent_seq = 0
_SUBAGENT_KEEP = 100


def pop_subagent_reports():
    with _subagent_lock:
        out = list(_subagent_reports)
        _subagent_reports.clear()
    return out


def has_running_subagent():
    with _subagent_lock:
        for j in _subagent_jobs:
            if j['status'] == 'running':
                return True
        return False


def _trim_jobs():
    if len(_subagent_jobs) <= _SUBAGENT_KEEP:
        return
    over = len(_subagent_jobs) - _SUBAGENT_KEEP
    kept = []
    for j in _subagent_jobs:
        if over > 0 and j['status'] != 'running':
            over -= 1
            continue
        kept.append(j)
    _subagent_jobs[:] = kept


def tool(function:str):
    ori_function = copy.deepcopy(function)
    function = tag_parser.strip_tags(function)
    if function[0] == '\n':
        function = function[1:]
    if function[-1] == '\n':
        function = function[:-1]
    try:
        function,args = function.strip().split(maxsplit=1)
    except:
        args = None
    if function in SKIP_CALL:
        return {'sys':f'{REPLACE_STRING_START}PAUSE{REPLACE_STRING_END}',
            'cli':f'{REPLACE_STRING_START}{ori_function}{REPLACE_STRING_END}'}
    func = _REGISTRY.get(function)
    if func:
        try:
            result = func(args)
        except Exception as e:
            result = error(e)
    else:
        result = notfound(function)
    return result

def method(name=None):
    def deco(func):
        _REGISTRY[name or func.__name__] = func
        return func
    return deco

@method()
def notfound(e):
    return {'sys':lang.lang['bot.tool.commandnotfound'],
            'cli':f'{lang.lang['cnmd.bot.toolfail']}{e}'}

@method()
def error(e):
    return {'sys':lang.lang['bot.tool.error'],
            'cli':f'{lang.lang['cnmd.bot.toolfail']}{e}'}

@method()
def dir(path:str):
    sys = fileedit.dir(path)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.dir']}{path}'}

@method()
def listdir(path:str):
    sys = cmd = fileedit.list_dir(path)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.listdir']}{path}'}

@method()
def read(args:str):
    sys = fileedit.read(args)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.read']}{args}'}

@method()
def write(args:str):
    path,content = args.split(maxsplit=1)
    sys = fileedit.write(path,content)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.write']}{path}'}

@method()
def delete(path:str):
    sys = fileedit.delete(path)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.delete']}{path}'}

@method()
def search_string(args:str):
    path,content = args.split(maxsplit=1)
    content = content.split()
    sys = fileedit.search_string(root=path,patterns=content)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.search']}{content}'}

@method()
def cmd(args:str):
    runcmd.clear_output()
    runcmd.cmd(args)
    return {'sys':runcmd.get_output(),
            'cli':f'{lang.lang['bot.agentlog.cmd']}{args}'}

@method()
def cmdresult(args=None):
    return {'sys':runcmd.get_output(),
            'cli':f'{lang.lang['bot.agentlog.cmdresult']}'}

@method()
def powershell(args:str):
    runcmd.clear_output()
    runcmd.pws(args)
    return {'sys':runcmd.get_output(),
            'cli':f'{lang.lang['bot.agentlog.powershell']}{args}'}

@method()
def powershellresult(args=None):
    return {'sys':runcmd.get_output(),
            'cli':f'{lang.lang['bot.agentlog.cmdresult']}'}

@method()
def timeread(args=None):
    sys = timer.timer()
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.time']}'}

@method()
def web(args:str):
    def _normalize_url(url:str) -> str:
        if not isinstance(url, str):
            return url
        url = url.strip().strip('\r\n\t')
        for _ch in ('\u200b', '\u200c', '\u200d', '\ufeff'):
            url = url.replace(_ch, '')
        url = url.replace('\u3000', ' ')
        parts = urllib.parse.urlsplit(url)
        if not parts.scheme or not parts.netloc:
            return url
        query = parts.query.replace('+', ' ')
        return urllib.parse.urlunsplit(
            (parts.scheme, parts.netloc, parts.path, query, parts.fragment))
    args = args.strip()
    if args.startswith(('http://', 'https://')):
        url = _normalize_url(args)
        sys = webgrab.get_html(url)
        return {'sys':sys,
                'cli':f'{lang.lang['bot.agentlog.webgrab']}{url}'}
    parts = args.split(maxsplit=1)
    if len(parts) == 1:
        url = _normalize_url(parts[0])
        sys = webgrab.get_html(url)
        return {'sys':sys,
                'cli':f'{lang.lang['bot.agentlog.webgrab']}{url}'}
    exc, content = parts
    if exc == 'grab':
        url = _normalize_url(content.strip())
        sys = webgrab.get_html(url)
        return {'sys':sys,
                'cli':f'{lang.lang['bot.agentlog.webgrab']}{url}'}
    elif exc == 'ping':
        content = content.strip()
        sys = webgrab.ping(content)
        return {'sys':sys,
                'cli':f'{lang.lang['bot.agentlog.ping']}{content}'}
    elif exc == 'setheader':
        json.loads(content)
        return {'sys':f'{lang.lang['bot.tool.setheader']}{content}',
                'cli':f'{lang.lang['bot.agentlog.setheader']}{content}'}

@method()
def mem(args:str):
    mem = memory.mem_load(args)
    if mem != None:
        sys = f'{lang.lang['bot.tool.memory']}\n'
        sys += mem
    else:
        sys = lang.lang['bot.tool.memorynone']
    return {'sys':sys,
            'cli':lang.lang['cnmd.mem.search']}

@method()
def image_read(path:str):
    if 'http' in path:
        sys = f'<{'agent_imageurl'}>{path}</{'agent_imageurl'}>'
    else:
        sys = fileedit.encode(path,'agent_image')
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.imread']}{path}'}

@method()
def audio_read(path:str):
    if 'http' in path:
        sys = f'<{'agent_audiourl'}>{path}</{'agent_audiourl'}>'
    else:
        sys = fileedit.encode(path,'agent_audio')
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.auread']}{path}'}

@method()
def video_read(path:str):
    if 'http' in path:
        sys = f'<{'agent_videourl'}>{path}</{'agent_videourl'}>'
    else:
        sys = fileedit.encode(path,'agent_video')
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.viread']}{path}'}

@method()
def screen(args=None):
    sys = screenshot.capture_all_base64(prefix='agent_image')
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.screenshot']}'}

@method()
def screen_cord(args=None):
    if args == None:
        cord = screenshot.get_screen_cord()
    else:
        cord = screenshot.get_screen_cord(eval(args))
    return {
        "sys": f'{cord['cord']}<{'agent_image'}>{cord['image']}</{'agent_image'}>',
        'cli': f'{lang.lang['bot.agentlog.screenshot']}'
    }

@method()
def click(args:str):
    args = args.split()
    args_temp = []
    for i in range(0,4):
        try:
            args_temp.append(args[i])
        except:
            if i == 2:
                args_temp.append('left')
            if i == 3:
                args_temp.append('1')
    autogui.click(args_temp[0],args_temp[1],args_temp[2],args_temp[3])
    time.sleep(1)
    cord = screenshot.get_screen_cord()
    return {
        "sys": f'{cord['cord']}<{'agent_image'}>{cord['image']}</{'agent_image'}>',
        'cli': f'{lang.lang['bot.agentlog.click']}{args_temp}'
    }

@method()
def typewrite(args:str):
    autogui.typewrite(args)
    time.sleep(1)
    cord = screenshot.get_screen_cord()
    return {
        "sys": f'{cord['cord']}<{'agent_image'}>{cord['image']}</{'agent_image'}>',
        'cli': f'{lang.lang['bot.agentlog.typewrite']}{args}'
    }

@method()
def skill(args=None):
    if args == None:
        return {'sys':skills.list(),
                'cli':lang.lang['bot.agentlog.skilllist']}
    else:
        return {'sys':skills.load(args),
                'cli':lang.lang['bot.agentlog.skillread']}

@method()
def mcp(args:str=None):
    args=None if args == None else args.strip().split(maxsplit=2)
    if args == None or args[0] == 'list':
        result = mcp_call.get_mcp_list()
        return {'sys':result,
                'cli':lang.lang['cnmd.mcp.getlist']}
    if len(args) == 1:
        result = mcp_call.list_tools(args[0])
        return {'sys':result,
                'cli':lang.lang['cnmd.mcp.gettoollist']}
    else:
        if len(args) == 3:
            dic = json.loads(args[2])
            result = mcp_call.call_tool(args[0],args[1],dic)
            return {'sys':result,
                    'cli':f'{lang.lang['cnmd.mcp.usetool']}{args[0]}→{args[1]}: {args[2]}'}
        else:
            result = mcp_call.call_tool(args[0],args[1],None)
            return {'sys':result,
                    'cli':f'{lang.lang['cnmd.mcp.usetool']}{args[0]}→{args[1]}'}

@method()
def subagent(args:str=None):
    """启动子智能体（普通工具，立即返回"已开始运行"提示，任务在后台线程执行）。
    args 为单条任务文本，或 JSON 数组（多任务并行）。
    子代理结束后把 report 写入 _subagent_reports，由主 CNMD 循环在发送给模型前
    固定查询注入；状态记录写入 _subagent_jobs，可用 subagent_status 查询。
    """
    global _subagent_seq
    from src.main.CNMD import CNMD as _CNMD   # 延迟导入，避免循环导入
    if args is None or args.strip() == '':
        return {'sys':lang.lang['bot.tool.subagent.empty'],
                'cli':lang.lang['cnmd.subagent.empty']}
    text = args.strip()
    tasks = []
    if text.startswith('['):
        try:
            data = json.loads(text)
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    tasks.append((item.get('number', idx), str(item.get('task', ''))))
                else:
                    tasks.append((idx, str(item)))
        except Exception:
            tasks = [(0, text)]
    else:
        tasks = [(0, text)]
    if not tasks:
        return {'sys':lang.lang['bot.tool.subagent.empty'],
                'cli':lang.lang['cnmd.subagent.empty']}

    launch = []
    with _subagent_lock:
        for num, tsk in tasks:
            _subagent_seq += 1
            tid = _subagent_seq
            _subagent_jobs.append({
                'id': tid,
                'number': num,
                'task': tsk,
                'status': 'running',
                'start': time.time(),
                'end': None,
                'report': None
            })
            launch.append((tid, num, tsk))
        _trim_jobs()

    def _worker(tid, num, tsk):
        rep = ''
        status = 'done'
        try:
            agent = _CNMD('sub_agent_base', subagent=True, number=num)
            agent.CNMD(tsk)
            rep = getattr(agent, 'report', '') or ''
        except Exception as e:
            status = 'error'
            rep = f'{lang.lang['bot.tool.error']}{e}'
        with _subagent_lock:
            for j in _subagent_jobs:
                if j['id'] == tid:
                    j['status'] = status
                    j['end'] = time.time()
                    j['report'] = rep
                    break
            _subagent_reports.append({'number': num, 'report': rep})

    for tid, num, tsk in launch:
        threading.Thread(target=_worker, args=(tid, num, tsk),
                         name=f'subagent-{tid}', daemon=True).start()

    return {'sys':lang.lang['bot.tool.subagent.started'],
            'cli':lang.lang['cnmd.subagent.running']}

@method()
def subagent_status(args:str=None):
    """查询子代理任务状态。
    无参数：列出全部任务；带参数：按任务序号(number)或任务ID(id)过滤。
    """
    with _subagent_lock:
        jobs = copy.deepcopy(_subagent_jobs)
    if args is not None and args.strip() != '':
        key = args.strip()
        jobs = [j for j in jobs if str(j['number']) == key or str(j['id']) == key]
    if not jobs:
        return {'sys':lang.lang['bot.tool.subagent.statusnone'],
                'cli':lang.lang['bot.tool.subagent.statuslog']}
    now = time.time()
    lines = []
    for j in jobs:
        status = j['status']
        start = time.strftime('%H:%M:%S', time.localtime(j['start']))
        if j['end'] is not None:
            cost = f'{j['end'] - j['start']:.1f}s'
        else:
            cost = f'{now - j['start']:.1f}s(running)'
        task = j['task'].replace('\n', ' ')
        if len(task) > 60:
            task = f'{task[:60]}...'
        lines.append(f'[id{j['id']}/#{j['number']}] {status} | {start} | {cost} | {task}')
        if status != 'running' and j['report']:
            rep = j['report'].strip()
            if len(rep) > 500:
                rep = f'{rep[:500]}...'
            lines.append(f'    report: {rep}')
    sys = f'{lang.lang['bot.tool.subagent.status']}\n' + '\n'.join(lines)
    return {'sys':sys,
            'cli':lang.lang['bot.tool.subagent.statuslog']}