import sys, os, json, threading, time, uuid, logging, webbrowser
from datetime import datetime

logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Paths: web/ is inside SynapseAgent/, so project_dir is parent
web_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(web_dir)  # SynapseAgent/
sys.path.insert(0, project_dir)

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_folder='static', template_folder='static')
app.config['SECRET_KEY'] = uuid.uuid4().hex
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

CONFIG_PATH = os.path.join(project_dir, 'config.json')
MODELS_PATH = os.path.join(web_dir, 'models.json')

cnm = None
msg_queue = []
queue_lock = threading.Lock()
is_processing = False

# ── Config (shared with backend) ──

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

def load_models():
    if os.path.exists(MODELS_PATH):
        with open(MODELS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_models(models):
    with open(MODELS_PATH, 'w', encoding='utf-8') as f:
        json.dump(models, f, indent=4, ensure_ascii=False)

# ── Engine ──

def init_engine():
    global cnm
    if not os.path.exists(CONFIG_PATH):
        default = {
            "API_KEY": "", "BASE_URL": "https://api.xiaomimimo.com/v1",
            "MODEL": "mimo-v2.5", "base_path": project_dir,
            "lang": "zh_cn", "break": True, "cmd_check": False, "enable_log": False
        }
        save_config(default)
        print("  [i] config.json created")
    os.chdir(project_dir)
    cfg = load_config()
    if not cfg.get('API_KEY'):
        print("  [!] API_KEY empty - set in settings")
    try:
        import CNMD as CNMD_module
        cnm = CNMD_module.CNMD()
        cnm.set_prompt('agent_base')
        print("  [OK] engine ready")
    except Exception as e:
        print(f"  [!] engine init failed: {e}")
        cnm = None

# ── HTTP Routes ──

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.json
    cfg = load_config()
    cfg.update(data)
    save_config(cfg)
    return jsonify({'success': True, 'config': cfg})

@app.route('/api/models', methods=['GET'])
def get_models():
    return jsonify({'models': load_models()})

@app.route('/api/models', methods=['POST'])
def add_model():
    data = request.json
    models = load_models()
    models.append({
        'name': data.get('name', ''),
        'api_key': data.get('api_key', ''),
        'base_url': data.get('base_url', ''),
        'model': data.get('model', ''),
    })
    save_models(models)
    return jsonify({'success': True, 'models': models})

@app.route('/api/models/delete', methods=['POST'])
def delete_model():
    data = request.json
    idx = data.get('index', -1)
    models = load_models()
    if 0 <= idx < len(models):
        models.pop(idx)
        save_models(models)
    return jsonify({'success': True, 'models': models})

@app.route('/api/models/apply', methods=['POST'])
def apply_model():
    data = request.json
    cfg = load_config()
    cfg['API_KEY'] = data.get('api_key', cfg.get('API_KEY', ''))
    cfg['BASE_URL'] = data.get('base_url', cfg.get('BASE_URL', ''))
    cfg['MODEL'] = data.get('model', cfg.get('MODEL', ''))
    save_config(cfg)
    return jsonify({'success': True, 'config': cfg})

@app.route('/api/files')
def list_files():
    path = request.args.get('path', '')
    if not path:
        cfg = load_config()
        path = cfg.get('base_path', project_dir)
    try:
        items = []
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            is_dir = os.path.isdir(full)
            size = 0 if is_dir else os.path.getsize(full)
            items.append({'name': name, 'path': full, 'is_dir': is_dir, 'size': size})
        return jsonify({'path': path, 'items': items})
    except Exception as e:
        return jsonify({'error': str(e), 'path': path, 'items': []}), 400

@app.route('/api/file')
def read_file():
    path = request.args.get('path', '')
    try:
        size = os.path.getsize(path)
        if size > 2 * 1024 * 1024:
            return jsonify({'error': 'File too large (>2MB)'}), 400
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'path': path, 'content': content, 'size': size})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/file/save', methods=['POST'])
def save_file():
    data = request.json
    path = data.get('path', '')
    content = data.get('content', '')
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/skills')
def list_skills():
    skills_dir = os.path.join(project_dir, 'skills')
    skills = []
    if os.path.isdir(skills_dir):
        for f in sorted(os.listdir(skills_dir)):
            if f.endswith('.md'):
                skills.append(f[:-3])
    return jsonify({'skills': skills})

@app.route('/api/skill/<name>')
def read_skill(name):
    path = os.path.join(project_dir, 'skills', name + '.md')
    if not os.path.exists(path):
        return jsonify({'error': 'not found'}), 404
    with open(path, 'r', encoding='utf-8') as f:
        return jsonify({'name': name, 'content': f.read()})

@app.route('/api/file/raw')
def raw_file():
    path = request.args.get('path', '')
    if not path or not os.path.exists(path):
        return '', 404
    import mimetypes
    mime = mimetypes.guess_type(path)[0] or 'application/octet-stream'
    return send_from_directory(os.path.dirname(path), os.path.basename(path), mimetype=mime)

@app.route('/api/node/list')
def node_list():
    if cnm:
        nodes = [{'name': n, 'indices': i} for n, i in cnm.nodelist.items()]
        return jsonify({'nodes': nodes})
    return jsonify({'nodes': []})

@app.route('/api/node/delete', methods=['POST'])
def node_delete():
    data = request.json
    names = data.get('names', [])
    if not cnm:
        return jsonify({'success': False, 'error': 'engine not ready'})
    deleted = []
    for name in names:
        if name in cnm.nodelist and name != 'init':
            del cnm.nodelist[name]
            deleted.append(name)
    return jsonify({'success': True, 'deleted': deleted})

@app.route('/api/prompts')
def list_prompts():
    config_path = os.path.join(project_dir, 'prompt_loader', 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        return jsonify({'prompts': list(prompts.keys())})
    except:
        return jsonify({'prompts': ['agent_base']})

@app.route('/api/status')
def get_status():
    return jsonify({
        'processing': is_processing,
        'engine_ready': cnm is not None,
        'node_count': len(cnm.nodelist) if cnm else 0,
        'msg_count': len(cnm.messages) if cnm else 0,
        'queue_len': len(msg_queue),
        'allow_reasoning': cnm.allow_reasoning if cnm else False,
    })

# ── SocketIO Events ──

@socketio.on('connect')
def handle_connect():
    client_id = str(uuid.uuid4())[:8]
    emit('connected', {'client_id': client_id})
    cfg = load_config()
    if not cfg.get('API_KEY'):
        emit('system_notice', {'type': 'warning', 'msg': 'API_KEY not set'})
    if not cnm:
        emit('system_notice', {'type': 'error', 'msg': 'Engine not ready - check config'})

@socketio.on('send_message')
def handle_send_message(data):
    message = data.get('message', '').strip()
    if not message:
        return
    msg_id = str(uuid.uuid4())[:8]
    with queue_lock:
        msg_queue.append(message)
    emit('new_message', {
        'id': msg_id, 'user_id': 'user',
        'content': message, 'timestamp': datetime.now().isoformat(), 'type': 'user',
    })

@socketio.on('pause')
def handle_pause():
    if cnm:
        cnm.mslock = False
        socketio.emit('new_message', {
            'id': str(uuid.uuid4())[:8], 'user_id': 'system',
            'content': '[U] Agent paused', 'timestamp': datetime.now().isoformat(), 'type': 'system',
        })

@socketio.on('node_action')
def handle_node_action(data):
    action = data.get('action', '')
    name = data.get('name', '')
    if action == 'load' and name:
        with queue_lock:
            msg_queue.append(f'#node load {name}')
    elif action == 'save' and name:
        with queue_lock:
            msg_queue.append(f'#node save {name}')
    elif action == 'delete' and name:
        names = data.get('names', [name])
        for n in names:
            with queue_lock:
                msg_queue.append(f'#node delete {n}')

@socketio.on('reset_engine')
def handle_reset_engine():
    if cnm:
        cnm.nodelist.clear()
        cnm.nodelist['init'] = [0]
        cnm.messages = [{"role": "system", "content": cnm.prompt}]
        cnm.msg = cnm.nodelist['init']
        cnm.toolcall = [['none']]
        cnm.tic = 1
        cnm.cmd_check = []
        nodes = [{'name': 'init', 'indices': [0]}]
        socketio.emit('nodes_updated', {'nodes': nodes})
        print("  [reset_engine] nodelist cleared")

@socketio.on('file_action')
def handle_file_action(data):
    action = data.get('action', '')
    if action == 'reset_base':
        new_path = data.get('new_path', '')
        if new_path:
            cfg = load_config()
            cfg['base_path'] = new_path
            save_config(cfg)
            with queue_lock:
                msg_queue.append('#bot reset')
            emit('file_action_result', {'action': 'reset_base', 'success': True, 'new_path': new_path})
            return
    emit('file_action_result', {'action': action, 'success': True})

@socketio.on('update_setting')
def handle_update_setting(data):
    """Update a config key AND apply it to the running engine immediately."""
    key = data.get('key')
    val = data.get('value')
    if key is None:
        return
    cfg = load_config()
    cfg[key] = val
    save_config(cfg)
    if cnm:
        cnm.config[key] = val
        if key == 'break':
            cnm.stage_break = val
        elif key == 'cmd_check':
            cnm.allow_cmd = val
        elif key == 'enable_log':
            cnm.enable_log = val
    emit('setting_updated', {'key': key, 'value': val})

# ── Background Threads ──

def _node_watcher():
    last_keys = set(cnm.nodelist.keys()) if cnm else set()
    while True:
        if cnm:
            cur_keys = set(cnm.nodelist.keys())
            if cur_keys != last_keys:
                last_keys = cur_keys
                nodes = [{'name': n, 'indices': i} for n, i in cnm.nodelist.items()]
                socketio.emit('nodes_updated', {'nodes': nodes})
        time.sleep(0.5)

def msg_sender():
    global is_processing
    while True:
        if cnm and cnm.msg_stack:
            with queue_lock:
                msg = cnm.msg_stack.pop(0)
            if msg.startswith('reasoning:'):
                reasoning_text = msg[10:].strip()
                socketio.emit('thinking', {
                    'content': reasoning_text[:200],
                    'timestamp': datetime.now().isoformat(),
                })
                socketio.emit('new_message', {
                    'id': str(uuid.uuid4())[:8], 'user_id': 'assistant',
                    'content': reasoning_text, 'timestamp': datetime.now().isoformat(), 'type': 'thinking',
                })
                continue
            msg_type = 'assistant'
            if msg.startswith('[U]'):
                msg_type = 'system'
                msg = msg[3:].strip()
            elif msg.startswith('[D]'):
                msg_type = 'debug'
                msg = msg[3:].strip()
            elif msg.startswith('[A]'):
                msg = msg[3:].strip()
            socketio.emit('new_message', {
                'id': str(uuid.uuid4())[:8], 'user_id': 'assistant',
                'content': msg, 'timestamp': datetime.now().isoformat(), 'type': msg_type,
            })
            if not cnm.msg_stack:
                is_processing = False
                socketio.emit('processing', {'active': False})
        time.sleep(0.3)

def msg_processor():
    global is_processing
    while True:
        cmd = None
        with queue_lock:
            if msg_queue:
                cmd = msg_queue.pop(0)
        if cmd:
            if cnm:
                is_processing = True
                socketio.emit('processing', {'active': True})
                socketio.emit('thinking', {'content': 'thinking...', 'timestamp': datetime.now().isoformat()})
                try:
                    cnm.CNMD(cmd)
                except Exception as e:
                    socketio.emit('new_message', {
                        'id': str(uuid.uuid4())[:8], 'user_id': 'system',
                        'content': f'[Error] {e}', 'timestamp': datetime.now().isoformat(), 'type': 'system',
                    })
                is_processing = False
                socketio.emit('processing', {'active': False})
            else:
                socketio.emit('new_message', {
                    'id': str(uuid.uuid4())[:8], 'user_id': 'system',
                    'content': '[Error] Engine not ready', 'timestamp': datetime.now().isoformat(), 'type': 'system',
                })
        time.sleep(0.3)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    print()
    print(f"  {'='*40}")
    print(f"  SynapseAgent Web UI")
    print(f"  http://localhost:{port}")
    print(f"  {'='*40}")
    print()
    init_engine()
    threading.Thread(target=msg_sender, daemon=True).start()
    threading.Thread(target=msg_processor, daemon=True).start()
    threading.Thread(target=_node_watcher, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    webbrowser.open(f"http://localhost:{port}/")
