import json
import tools.bot as bot
import tools.wordvec as wordvec
import tools.lang as lang

def mem_save(dict):
    with open('./database/mem.json','r', encoding='utf-8') as f:
        data = json.load(f)
    for k,y in dict.items():
        data[k] = y
    with open('./database/mem.json','w',encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def similarity(str1, str2):
    set1 = set(str1)
    set2 = set(str2)
    intersection = set1 & set2
    union = set1 | set2
    if not union:
        return 1.0 if not intersection else 0.0
    return len(intersection) / len(union)

def mem_load(target:str):
    result = ''
    target = target.strip().split()
    with open('./database/mem.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    match_result = wordvec.target(target)
    for i in match_result:
        result += f'{i}:{data[i]}\n'
    return result

def compress(x):
    content=lang.lang['prompt.compress_memory']
    x.append({
        "role":"user",
        "content": content
    })
    reply = bot.reply(x)
    content = reply['content']
    return content

def analyse():
    with open('./database/mem.json','r',encoding='utf-8') as f:
        data = json.load(f)
    f = ''
    for k,y in data.items():
        f += f'{k}=>{y}\n'
    content=f'''{lang.text['prompt.analyse']}\n{f}
'''
    c=[{
        "role":"user",
        "content": content
    }]
    reply = bot.reply(c)['content']
    c = {}
    for i in reply.split('\n'):
        if i:
            k = i.split('=>')
            c[k[0]] = k[1]
    with open('./database/mem.json','w',encoding='utf-8') as f:
        json.dump(c, f, indent=4, ensure_ascii=False)

def save(x):
    content=lang.text['prompt.memory']
    x.append({
        "role":"user",
        "content": content
    })
    reply = bot.reply(x)
    content = reply['content']
    content = content.strip().split('\n')
    c = {}
    for i in content:
        if i:
            k,v = i.split('=>')
            c[k] = v
    mem_save(c)