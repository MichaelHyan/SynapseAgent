from tools import fileedit,runcmd,webgrab,timer,memory,skills,lang,mcp_call,subagent,screenshot
import json,threading,time
def tool(function:str):
    function = function.replace('<tool_call>','').replace('</tool_call>','')
    if function[0] == '\n':
        function = function[1:]
    if function[-1] == '\n':
        function = function[:-1]
    try:
        function,args = function.strip().split(maxsplit=1)
    except:
        args = None
    func = globals().get(function)
    if func:
        result = func(args)
    else:
        result = notfound(function)
    return result

def notfound(e):
    return {'sys':lang.lang['bot.tool.commandnotfound'],
            'cli':f'{lang.lang['cnmd.bot.toolfail']}{e}'}

def dir(path:str):
    sys = fileedit.dir(path)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.dir']}{path}'}

def listdir(path:str):
    sys = cmd = fileedit.list_dir(path)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.listdir']}{path}'}

def read(args:str):
    sys = fileedit.read(args)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.read']}{args}'}

def write(args:str):
    path,content = args.split(maxsplit=1)
    sys = fileedit.write(path,content)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.write']}{path}'}

def delete(path:str):
    sys = fileedit.delete(path)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.delete']}{path}'}

def search_string(args:str):
    path,content = args.split(maxsplit=1)
    content = content.split()
    sys = fileedit.search_string(root=path,patterns=content)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.search']}{content}'}

def cmd(args:str):
    runcmd.cmd_output=''
    threading.Thread(target=runcmd.cmd, args=(args,)).start()
    time.sleep(5)
    return {'sys':runcmd.cmd_output,
            'cli':f'{lang.lang['bot.agentlog.cmd']}{args}'}

def cmdresult(args=None):
    return {'sys':runcmd.cmd_output,
            'cli':f'{lang.lang['bot.agentlog.cmdresult']}'}

def powershell(args:str):
    runcmd.cmd_output=''
    threading.Thread(target=runcmd.pws, args=(args,)).start()
    time.sleep(5)
    return {'sys':runcmd.cmd_output,
            'cli':f'{lang.lang['bot.agentlog.powershell']}{args}'}

def powershellresult(args=None):
    return {'sys':runcmd.cmd_output,
            'cli':f'{lang.lang['bot.agentlog.cmdresult']}'}

def timeread(args=None):
    sys = timer.timer()
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.time']}'}

def web(args:str):
    if len(args.split(maxsplit=1)) == 1:
        sys = webgrab.get_html(args)
        return {'sys':sys,
                'cli':f'{lang.lang['bot.agentlog.webgrab']}{args}'}
    else:
        exc,content = args.split(maxsplit=1)
        if exc == 'grab':
            sys = webgrab.get_html(content)
            return {'sys':sys,
                    'cli':f'{lang.lang['bot.agentlog.webgrab']}{content}'}
        elif exc == 'ping':
            sys = webgrab.ping(content)
            return {'sys':sys,
                    'cli':f'{lang.lang['bot.agentlog.ping']}{content}'}
        elif exc == 'setheader':
            json.loads(content)
            return {'sys':f'{lang.lang['bot.tool.setheader']}{content}',
                    'cli':f'{lang.lang['bot.agentlog.setheader']}{content}'}

def mem(args:str):
    mem = memory.mem_load(args)
    if mem != None:
        sys = f'{lang.lang['bot.tool.memory']}\n'
        sys += mem
    else:
        sys = lang.lang['bot.tool.memorynone']
    return {'sys':sys,
            'cli':lang.lang['cnmd.mem.search']}

def image_read(path:str):
    if 'http' in path:
        sys = f'<imageurl>{path}</imageurl>'
    else:
        sys = fileedit.encode(path,'image')
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.imread']}{path}'}

def audio_read(path:str):
    if 'http' in path:
        sys = f'<audiourl>{path}</audiourl>'
    else:
        sys = fileedit.encode(path,'audio')
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.auread']}{path}'}

def video_read(path:str):
    if 'http' in path:
        sys = f'<videourl>{path}</videourl>'
    else:
        sys = fileedit.encode(path,'video')
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.viread']}{path}'}

def screen(args=None):
    sys = screenshot.capture_all_base64(prefix='image')
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.screenshot']}'}

def skill(args=None):
    if args == None:
        return {'sys':skills.list(),
                'cli':lang.lang['bot.agentlog.skilllist']}
    else:
        return {'sys':skills.load(args),
                'cli':lang.lang['bot.agentlog.skillread']}
    
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

def taskstart(args=None):
    subagent.startsubagent()
    return {'sys':'<tool_call>PAUSE</tool_call>',
            'cli':f'{lang.lang['cnmd.subagent.start']}'}