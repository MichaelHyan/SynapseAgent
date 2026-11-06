from src.main import subagent
from src.tools import autogui, fileedit, lang, mcp_call, memory, runcmd, screenshot, skills, timer
from src.tools import webgrab
import json,threading,time,copy
import urllib.parse

_REGISTRY = {}
SKIP_CALL = []

def tool(function:str):
    ori_function = copy.deepcopy(function)
    function = function.replace('<tool_call>','').replace('</tool_call>','')
    if function[0] == '\n':
        function = function[1:]
    if function[-1] == '\n':
        function = function[:-1]
    try:
        function,args = function.strip().split(maxsplit=1)
    except:
        args = None
    if function in SKIP_CALL:
        return {'sys':'<tool_call>{''}PAUSE{''}</tool_call>',
            'cli':f'<tool_call>{ori_function}</tool_call>'}
    func = _REGISTRY.get(function)
    if func:
        result = func(args)
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
    runcmd.cmd_output=''
    threading.Thread(target=runcmd.cmd, args=(args,)).start()
    time.sleep(5)
    return {'sys':runcmd.cmd_output,
            'cli':f'{lang.lang['bot.agentlog.cmd']}{args}'}

@method()
def cmdresult(args=None):
    return {'sys':runcmd.cmd_output,
            'cli':f'{lang.lang['bot.agentlog.cmdresult']}'}

@method()
def powershell(args:str):
    runcmd.cmd_output=''
    threading.Thread(target=runcmd.pws, args=(args,)).start()
    time.sleep(5)
    return {'sys':runcmd.cmd_output,
            'cli':f'{lang.lang['bot.agentlog.powershell']}{args}'}

@method()
def powershellresult(args=None):
    return {'sys':runcmd.cmd_output,
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
        sys = f'<agent_imageurl>{path}</agent_imageurl>'
    else:
        sys = fileedit.encode(path,'agent_image')
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.imread']}{path}'}

@method()
def audio_read(path:str):
    if 'http' in path:
        sys = f'<agent_audiourl>{path}</agent_audiourl>'
    else:
        sys = fileedit.encode(path,'agent_audio')
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.auread']}{path}'}

@method()
def video_read(path:str):
    if 'http' in path:
        sys = f'<agent_videourl>{path}</agent_videourl>'
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
        "sys": f'{cord['cord']}<agent_image>{cord['image']}</agent_image>',
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
        "sys": f'{cord['cord']}<agent_image>{cord['image']}</agent_image>',
        'cli': f'{lang.lang['bot.agentlog.click']}{args_temp}'
    }

@method()
def typewrite(args:str):
    autogui.typewrite(args)
    time.sleep(1)
    cord = screenshot.get_screen_cord()
    return {
        "sys": f'{cord['cord']}<agent_image>{cord['image']}</agent_image>',
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
def taskstart(args=None):
    subagent.startsubagent()
    return {'sys':f'<tool_call>{''}PAUSE{''}</tool_call>',
            'cli':f'{lang.lang['cnmd.subagent.start']}'}