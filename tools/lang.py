import json,re
def clean(text):
    return re.sub(
        r'---.*?---',
        lambda m: '\n' * m.group(0).count('\n'),
        text,
        flags=re.DOTALL,
    ).strip()
with open('./config/config.json',encoding='utf-8') as f:
    config = json.load(f)
with open(f'./lang/{config['lang']}/key.json',encoding='utf-8') as f:
    lang = json.load(f)
with open(f'./lang/{config['lang']}/text.json',encoding='utf-8') as f:
    _text_config = json.load(f)
text = {}
for key,value in _text_config.items():
    with open(f'./lang/{config['lang']}/text/{value}.md',encoding='utf-8') as f:
        temp = f.read()
    text[key] = clean(temp)