import os
def list():
    items = os.listdir('./skills/')
    files = [item for item in items if os.path.isfile(os.path.join('./skills', item))]
    skilllist = ''
    for i in files:
        skilllist += f'{i[:-3]}\n'
    return skilllist

def load(skill):
    with open(f'./skills/{skill}.md','r',encoding='utf-8') as f:
        return f.read()