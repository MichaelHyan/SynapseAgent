import json
import re

def clean(text):
    return re.sub(
        r'---.*?---',
        lambda m: '\n' * m.group(0).count('\n'),
        text,
        flags=re.DOTALL,
    ).strip()

_cache = {}

def _lang_code():
    with open('./config/config.json', encoding='utf-8') as f:
        return json.load(f)['lang']

def _load_lang():
    code = _lang_code()
    with open(f'./lang/{code}/key.json', encoding='utf-8') as f:
        return json.load(f)

def _load_text():
    code = _lang_code()
    with open(f'./lang/{code}/text.json', encoding='utf-8') as f:
        _text_config = json.load(f)
    text = {}
    for key, value in _text_config.items():
        with open(f'./lang/{code}/text/{value}.md', encoding='utf-8') as f:
            temp = f.read()
        text[key] = clean(temp)
    return text

def __getattr__(name):
    if name == 'lang':
        if 'lang' not in _cache:
            _cache['lang'] = _load_lang()
        return _cache['lang']
    if name == 'text':
        if 'text' not in _cache:
            _cache['text'] = _load_text()
        return _cache['text']
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")