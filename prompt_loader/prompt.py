import json
import platform

_base_config = None
_loader_config = None


def _load_configs():
    global _base_config, _loader_config
    if _base_config is None:
        with open('./config/config.json', encoding='utf-8') as f:
            _base_config = json.load(f)
    if _loader_config is None:
        with open('./prompt_loader/config.json', encoding='utf-8') as f:
            _loader_config = json.load(f)


def load(prp:str):
    if prp[:15] == 'PROMPTOVERWRITE':
            return prp[15:].strip()
    _load_configs()
    config = _loader_config
    config_base = _base_config
    prompt = ''
    try:
        p = config[prp]
    except:
        p = None
    if p == None:
        prp = 'agent_base'
    if config[prp]['persona'] != 'none':
        with open(f'./prompt_loader/persona/{config[prp]['persona']}.md',encoding='utf-8') as f:
            prompt += f.read()
            prompt += '\n'
    if config[prp]['skills'] != 'none':
        with open(f'./prompt_loader/skills/{config[prp]['skills']}.md',encoding='utf-8') as f:
            prompt += f.read().replace('''{config['base_path']}''',config_base['base_path']).replace('''{platform.system()}''',platform.system())
            prompt += '\n'
    if config[prp]['extra'] != 'none':
        with open(f'./prompt_loader/extra/{config[prp]['extra']}.md',encoding='utf-8') as f:
            prompt += f.read()
    return prompt