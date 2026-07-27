(function(){
'use strict';

const socket = io();
let currentPath = '';
let soundEnabled = true;
let isTyping = false;
let isProcessing = false;
let seenMsgIds = new Set();
let konamiBuffer = [];
let currentEditPath = '';
const KONAMI = [38,38,40,40,37,39,37,39,66,65,66,65];
const $ = s => document.querySelector(s);

const AudioCtx = window.AudioContext || window.webkitAudioContext;
let audioCtx = null;

function beep(f,d,v){ if(!soundEnabled)return; try{ if(!audioCtx)audioCtx=new AudioCtx(); const o=audioCtx.createOscillator(),g=audioCtx.createGain(); o.connect(g);g.connect(audioCtx.destination); o.frequency.value=f;o.type='sine'; g.gain.setValueAtTime(v||.1,audioCtx.currentTime);g.gain.exponentialRampToValueAtTime(.001,audioCtx.currentTime+d); o.start();o.stop(audioCtx.currentTime+d); }catch(e){} }
function sndSend(){ beep(880,.08,.08) }
function sndRecv(){ beep(660,.1,.06);setTimeout(()=>beep(880,.08,.06),80) }
function sndClick(){ beep(1200,.04,.05) }
function sndError(){ beep(300,.2,.1) }
function sndEaster(){ beep(523,.1,.08);setTimeout(()=>beep(659,.1,.08),100);setTimeout(()=>beep(784,.1,.08),200);setTimeout(()=>beep(1047,.15,.08),300) }
window.sndEaster=sndEaster;

function toast(msg,type){
    const c=$('#toast-container'),el=document.createElement('div');
    el.className='toast '+(type||'info');
    el.innerHTML='<i class="fas fa-'+(type==='success'?'check-circle':type==='error'?'exclamation-circle':'info-circle')+'"></i> '+esc(msg);
    c.appendChild(el);
    setTimeout(()=>{ el.style.animation='toastOut .3s ease forwards';setTimeout(()=>el.remove(),300) },2500);
}
window.toast=toast;
function esc(s){ const d=document.createElement('div');d.textContent=s;return d.innerHTML }
function formatTime(ts){ if(!ts)return '';return new Date(ts).toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'}) }
function formatSize(b){ if(!b)return '';if(b<1024)return b+' B';if(b<1048576)return(b/1024).toFixed(1)+' KB';return(b/1048576).toFixed(1)+' MB' }
function ripple(e,el){ const r=el.getBoundingClientRect(),d=Math.max(r.width,r.height),x=e.clientX-r.left-d/2,y=e.clientY-r.top-d/2,s=document.createElement('span'); s.className='ripple';s.style.cssText='width:'+d+'px;height:'+d+'px;left:'+x+'px;top:'+y+'px';el.appendChild(s);setTimeout(()=>s.remove(),500) }

function showTyping(){ if(isTyping)return;isTyping=true; const box=$('#chat-messages'),wel=box.querySelector('.chat-welcome');if(wel){moveLogoToFloat()} const el=document.createElement('div');el.className='typing-indicator';el.id='typing-ind';el.innerHTML='<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';box.appendChild(el);box.scrollTop=box.scrollHeight }
function hideTyping(){ isTyping=false;const el=document.getElementById('typing-ind');if(el)el.remove() }
function showThinking(content){
    hideTyping();
    const box=$('#chat-messages');
    let el=document.getElementById('thinking-ind');
    if(!el){ el=document.createElement('div');el.className='thinking-indicator';el.id='thinking-ind';box.appendChild(el) }
    el.innerHTML='<div class="thinking-dots"><div class="thinking-dot"></div><div class="thinking-dot"></div><div class="thinking-dot"></div></div><span class="thinking-text">'+esc(content||'思考中...')+'</span>';
    box.scrollTop=box.scrollHeight;
}
function hideThinking(){ const el=document.getElementById('thinking-ind');if(el)el.remove() }

function fillInput(text){ const inp=$('#chat-input');inp.value=text;inp.style.height='auto';inp.style.height=Math.min(inp.scrollHeight,120)+'px';inp.focus() }
function doReset(){ setActiveNode('init');setNodeParent({});setNodePositions({});_pendingParent={};_pendingActive=null;socket.emit('reset_engine') }


function confetti(){
    const colors=['#f44747','#dcdcaa','#6a9955','#569cd6','#c586c0','#4ec9b0','#ce9178'];
    for(let i=0;i<30;i++){ const el=document.createElement('div');el.style.cssText='position:fixed;top:-10px;left:'+Math.random()*100+'%;width:8px;height:8px;background:'+colors[Math.floor(Math.random()*colors.length)]+';border-radius:'+(Math.random()>.5?'50%':'2px')+';z-index:9999;pointer-events:none;animation:confettiFall '+(1+Math.random()*2)+'s ease-in forwards';document.body.appendChild(el);setTimeout(()=>el.remove(),3000) }
    if(!document.getElementById('confetti-style')){ const s=document.createElement('style');s.id='confetti-style';s.textContent='@keyframes confettiFall{to{top:100vh;transform:rotate('+(360+Math.random()*720)+'deg) translateX('+(Math.random()*200-100)+'px);opacity:0}}';document.head.appendChild(s) }
}
window.confetti=confetti;

function init(){
    bindChat();bindControls();bindFiles();bindNodes();bindQuick();bindModals();bindTheme();bindKeyboard();bindResize();bindResetLayout();bindNodeContextMenu();bindCopyPath();
    loadConfig();loadFiles();loadNodes();loadPrompts();loadSkills();restoreLayout();syncStatus();
    setInterval(()=>{loadNodes();syncStatus()},5000);
}

socket.on('connect',()=>{
    $('#status-dot').style.background='var(--green)';
    $('#status-text').textContent='已连接';
});
socket.on('disconnect',()=>{
    $('#status-dot').style.background='var(--red)';
    $('#status-text').textContent='已断开';
    sndError();
});
socket.on('new_message',d=>{
    if(d.id&&seenMsgIds.has(d.id))return;
    if(d.id)seenMsgIds.add(d.id);
    hideTyping();hideThinking();
    appendMsg(d);
    if(d.type==='assistant')sndRecv();
});
socket.on('thinking',d=>{ showThinking(d.content) });
socket.on('processing',d=>{ isProcessing=d.active;const bar=$('#processing-bar');if(bar)bar.classList.toggle('active',d.active) });
socket.on('system_notice',d=>{ if(d.type==='warning')toast(d.msg,'error');else toast(d.msg,'info') });
socket.on('file_action_result',d=>{ if(d.action==='reset_base'&&d.success){loadConfig();loadFiles();toast('base_path 已更新: '+d.new_path,'success')} });
socket.on('nodes_updated',d=>{ if(_isDraggingNode)return;renderNodes(d.nodes||[]);syncActiveHighlight() });

function bindChat(){
    const inp=document.getElementById('chat-input');
    if(!inp)return;
    inp.onkeydown=function(e){
        if(e.keyCode===13&&!e.shiftKey){e.preventDefault();send();return false}
    };
    document.getElementById('btn-send').onclick=send;
    inp.oninput=function(){ inp.style.height='auto';inp.style.height=Math.min(inp.scrollHeight,120)+'px' };
}
function send(){ const inp=$('#chat-input'),t=inp.value.trim();if(!t)return;if(t==='#bot reset'){doReset();inp.value='';inp.style.height='auto';return}socket.emit('send_message',{message:t});inp.value='';inp.style.height='auto';sndSend();if(!t.startsWith('#'))showTyping();const btn=$('#btn-send');btn.classList.add('sending');setTimeout(()=>btn.classList.remove('sending'),300) }

function moveLogoToFloat(){
    if(document.getElementById('floating-logo'))return;
    const wel=$('#chat-messages .chat-welcome');
    if(!wel)return;
    const icon=wel.querySelector('.welcome-icon');
    if(!icon)return;
    const container=document.createElement('div');
    container.id='floating-logo';
    container.appendChild(icon);
    document.body.appendChild(container);
}
function moveLogoToWelcome(){
    const fl=document.getElementById('floating-logo');
    if(!fl)return;
    const icon=fl.querySelector('.welcome-icon');
    if(icon)fl.removeChild(icon);
    fl.remove();
}


function appendMsg(d){
    hideTyping();hideThinking();
    const wel=$('#chat-messages .chat-welcome');
    if(wel){moveLogoToFloat();wel.remove()}
    const type=d.type||'assistant';
    const isUser=d.user_id==='user';
    const msg=document.createElement('div');
    msg.className='chat-msg '+type;
    const av=document.createElement('div');
    av.className='msg-avatar';
    if(isUser)av.innerHTML='<i class="fas fa-user"></i>';
    else if(type==='assistant')av.innerHTML='<img src="/static/logo.jpg" alt="Bot">';
    else if(type==='thinking')av.innerHTML='<i class="fas fa-brain"></i>';
    else if(type==='debug')av.innerHTML='<i class="fas fa-bug"></i>';
    else av.innerHTML='<i class="fas fa-info-circle"></i>';
    const bub=document.createElement('div');
    bub.className='msg-bubble';
    bub.innerHTML=renderContent(d.content);
    const tm=document.createElement('div');
    tm.className='msg-time';
    tm.textContent=formatTime(d.timestamp);
    const wrap=document.createElement('div');
    wrap.className='msg-bubble-wrap';
    wrap.appendChild(bub);wrap.appendChild(tm);
    msg.appendChild(av);msg.appendChild(wrap);
    const box=$('#chat-messages');box.appendChild(msg);box.scrollTop=box.scrollHeight;
}
function renderContent(t){ if(!t)return '';let h=esc(t);h=h.replace(/```(\w*)\n?([\s\S]*?)```/g,'<pre><code>$2</code></pre>');h=h.replace(/`([^`]+)`/g,'<code>$1</code>');h=h.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');h=h.replace(/\n/g,'<br>');return h }

function bindControls(){
    $('#btn-reset-path').addEventListener('click',e=>{ ripple(e,e.currentTarget);const p=$('#config-base-path').value.trim();if(!p){toast('请先输入 base_path','error');sndError();return}socket.emit('file_action',{action:'reset_base',new_path:p});sndClick() });
    $('#toggle-reasoning').addEventListener('change',e=>{ socket.emit('send_message',{message:'#bot reasoning '+(e.target.checked?'on':'off')});sndClick() });
    $('#toggle-break').addEventListener('change',e=>{ socket.emit('update_setting',{key:'break',value:e.target.checked});sndClick() });
    $('#toggle-cmdcheck').addEventListener('change',e=>{ socket.emit('update_setting',{key:'cmd_check',value:e.target.checked});sndClick() });
    $('#toggle-log').addEventListener('change',e=>{ socket.emit('update_setting',{key:'enable_log',value:e.target.checked});sndClick() });
    $('#btn-set-prompt').addEventListener('click',e=>{ ripple(e,e.currentTarget);const p=$('#prompt-select').value;if(p)fillInput('#bot prompt '+p);sndClick() });
    $('#btn-sound').addEventListener('click',()=>{ soundEnabled=!soundEnabled;const btn=$('#btn-sound');btn.querySelector('i').className=soundEnabled?'fas fa-volume-up':'fas fa-volume-mute';btn.classList.toggle('muted',!soundEnabled);toast(soundEnabled?'提示音已开启':'提示音已关闭','info') });
}

function syncStatus(){
    fetch('/api/status').then(r=>r.json()).then(s=>{
        const toggle=$('#toggle-reasoning');
        if(toggle)toggle.checked=!!s.allow_reasoning;
    }).catch(()=>{});
}

function loadConfig(){
    fetch('/api/config').then(r=>r.json()).then(c=>{
        $('#config-base-path').value=c.base_path||'';
        $('#info-model').textContent=c.MODEL||'-';
        $('#info-url').textContent=c.BASE_URL||'-';
        $('#setting-apikey').value=c.API_KEY||'';
        $('#setting-url').value=c.BASE_URL||'';
        $('#setting-model').value=c.MODEL||'';
        $('#setting-lang').value=c.lang||'zh_cn';
        $('#toggle-break').checked=!!c.break;
        $('#toggle-cmdcheck').checked=!!c.cmd_check;
        $('#toggle-log').checked=!!c.enable_log;
        if(!c.API_KEY&&!document.getElementById('api-warn')){
            const el=document.createElement('div');el.id='api-warn';
            el.textContent='API_KEY not set - click to open settings';
            el.onclick=()=>{$('#btn-settings').click();sndClick()};
            document.querySelector('.top-bar').after(el);
        } else if(c.API_KEY){ const w=document.getElementById('api-warn');if(w)w.remove() }
        renderModelSwitcher(c);
    }).catch(()=>{});
}

function renderModelSwitcher(cfg){
    const container=$('#model-switcher');
    if(!container)return;
    fetch('/api/models').then(r=>r.json()).then(d=>{
        container.innerHTML='';
        const models=d.models||[];
        models.forEach((m,i)=>{
            const chip=document.createElement('div');
            chip.className='model-chip'+(cfg.MODEL===m.model?' active':'');
            chip.textContent=m.name||m.model;
            chip.title=m.model+' @ '+m.base_url;
            chip.addEventListener('click',()=>{
                fetch('/api/models/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(m)}).then(()=>{
                    loadConfig();fillInput('#bot reload');toast('已切换到 '+(m.name||m.model),'success');sndClick()
                });
            });
            container.appendChild(chip);
        });
        const addBtn=document.createElement('div');
        addBtn.className='model-chip';addBtn.textContent='+';addBtn.title='保存当前配置为模型';
        addBtn.addEventListener('click',()=>{
            const name=prompt('模型别名:');
            if(!name)return;
            fetch('/api/models',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name,api_key:cfg.API_KEY||'',base_url:cfg.BASE_URL||'',model:cfg.MODEL||''})}).then(()=>{
                renderModelSwitcher(cfg);toast('模型已保存','success');sndClick()
            });
        });
        container.appendChild(addBtn);
    });
}

function loadPrompts(){
    fetch('/api/prompts').then(r=>r.json()).then(d=>{
        const sel=$('#prompt-select');
        sel.innerHTML='';
        (d.prompts||['agent_base']).forEach(p=>{
            const opt=document.createElement('option');
            opt.value=p;opt.textContent=p;
            sel.appendChild(opt);
        });
    }).catch(()=>{});
}

function loadSkills(){
    fetch('/api/skills').then(r=>r.json()).then(d=>{
        const list=$('#skills-list');
        if(!list)return;
        list.innerHTML='';
        (d.skills||[]).forEach(s=>{
            const chip=document.createElement('div');
            chip.className='skill-chip';
            chip.textContent=s;
            chip.addEventListener('click',()=>{
                fetch('/api/skill/'+encodeURIComponent(s)).then(r=>r.json()).then(d=>{
                    if(d.content){
                        fillInput('请根据以下技能指导完成任务：\n\n'+d.content);
                        toast('已加载技能: '+s,'info');
                    }
                });
            });
            list.appendChild(chip);
        });
    }).catch(()=>{});
}

function bindCopyPath(){
    const btn=$('#btn-copy-path');
    if(!btn)return;
    btn.addEventListener('click',()=>{
        if(!currentPath)return;
        navigator.clipboard.writeText(currentPath).then(()=>toast('路径已复制','info')).catch(()=>toast('复制失败','error'));
        sndClick();
    });
}

function bindFiles(){
    $('#btn-file-home').addEventListener('click',e=>{ ripple(e,e.currentTarget);loadFiles('');sndClick() });
    $('#btn-file-up').addEventListener('click',e=>{ ripple(e,e.currentTarget);if(currentPath){const parent=currentPath.replace(/[\\/][^\\/]+[\\/]?$/,'');loadFiles(parent||'');sndClick()} });
    $('#btn-file-refresh').addEventListener('click',e=>{ ripple(e,e.currentTarget);loadFiles(currentPath);sndClick() });
}
function loadFiles(path){
    const fl=$('#file-list');fl.innerHTML='<div class="file-loading"><i class="fas fa-spinner fa-spin"></i><span>加载中...</span></div>';
    const url=path!==undefined?'/api/files?path='+encodeURIComponent(path):'/api/files';
    fetch(url).then(r=>r.json()).then(d=>{ if(d.error){fl.innerHTML='<div class="file-loading"><i class="fas fa-exclamation-triangle"></i><span>'+esc(d.error)+'</span></div>';return}currentPath=d.path||'';renderBreadcrumb(currentPath);renderFileList(d.items||[]) }).catch(()=>{ fl.innerHTML='<div class="file-loading"><i class="fas fa-exclamation-triangle"></i><span>加载失败</span></div>' });
}
function renderBreadcrumb(path){
    const bc=$('#file-breadcrumb');if(!path){bc.innerHTML='<span class="breadcrumb-seg">/</span>';return}
    const parts=path.split(/[\\/]/).filter(Boolean);let html='<span class="breadcrumb-seg" data-path="">root</span>',accum='';
    for(let i=0;i<parts.length;i++){ accum+=(i===0&&path.startsWith('/')?'/':'')+parts[i]+(i<parts.length-1?'/':'');html+='<span class="breadcrumb-sep"><i class="fas fa-chevron-right"></i></span><span class="breadcrumb-seg" data-path="'+esc(accum)+'">'+esc(parts[i])+'</span>' }
    bc.innerHTML=html;bc.querySelectorAll('.breadcrumb-seg').forEach(s=>s.addEventListener('click',()=>loadFiles(s.dataset.path)));
}
function renderFileList(items){
    const fl=$('#file-list');if(!items.length){fl.innerHTML='<div class="file-loading"><i class="fas fa-folder-open"></i><span>空目录</span></div>';return}
    items.sort((a,b)=>a.is_dir!==b.is_dir?(a.is_dir?-1:1):a.name.localeCompare(b.name));fl.innerHTML='';
    items.forEach((it,i)=>{
        const el=document.createElement('div');el.className='file-item';el.style.animationDelay=(i*20)+'ms';
        const isEditable=it.name.match(/\.(txt|py|html|js|css|json|md|yml|yaml|toml|xml|bat|sh|cfg|ini|log)$/i);
        const isImage=it.name.match(/\.(png|jpg|jpeg|gif|svg|bmp|webp)$/i);
        el.innerHTML='<i class="'+fileIcon(it)+'"></i><span class="file-name">'+esc(it.name)+'</span><span class="file-size">'+(it.is_dir?'':formatSize(it.size))+'</span><span class="file-actions"><button class="file-action-btn" title="Copy path"><i class="fas fa-copy"></i></button>'+(isEditable&&!it.is_dir?'<button class="file-action-btn file-edit-btn" title="Edit"><i class="fas fa-edit"></i></button>':'')+(isImage&&!it.is_dir?'<button class="file-action-btn file-img-btn" title="Preview"><i class="fas fa-eye"></i></button>':'')+'</span>';
        el.querySelector('.file-name').addEventListener('click',()=>{sndClick();it.is_dir?loadFiles(it.path):openFileViewer(it.path,it.name)});
        el.querySelector('i:first-child').addEventListener('click',()=>{sndClick();it.is_dir?loadFiles(it.path):openFileViewer(it.path,it.name)});
        const copyBtn=el.querySelector('.file-action-btn');
        if(copyBtn)copyBtn.addEventListener('click',e=>{e.stopPropagation();navigator.clipboard.writeText(it.path).then(()=>toast('路径已复制','info')).catch(()=>toast('复制失败','error'));sndClick()});
        const editBtn=el.querySelector('.file-edit-btn');
        if(editBtn)editBtn.addEventListener('click',e=>{e.stopPropagation();openFileEditor(it.path,it.name);sndClick()});
        const imgBtn=el.querySelector('.file-img-btn');
        if(imgBtn)imgBtn.addEventListener('click',e=>{e.stopPropagation();openImageViewer(it.path,it.name);sndClick()});
        fl.appendChild(el);
    });
}
function fileIcon(it){
    if(it.is_dir)return 'fas fa-folder';const ext=it.name.split('.').pop().toLowerCase();
    const m={py:'fab fa-python',js:'fab fa-js-square',ts:'fab fa-js-square',html:'fab fa-html5',css:'fab fa-css3-alt',json:'fas fa-file-code',md:'fas fa-file-alt',txt:'fas fa-file-alt',bat:'fas fa-terminal',sh:'fas fa-terminal',png:'fas fa-file-image',jpg:'fas fa-file-image',jpeg:'fas fa-file-image',gif:'fas fa-file-image',svg:'fas fa-file-image',pdf:'fas fa-file-pdf',zip:'fas fa-file-archive',rar:'fas fa-file-archive',log:'fas fa-file-alt',yml:'fas fa-file-code',yaml:'fas fa-file-code',toml:'fas fa-file-code',xml:'fas fa-file-code'};
    return m[ext]||'fas fa-file';
}
function openFileViewer(path,name){ const modal=$('#file-viewer-modal');$('#file-viewer-title').textContent=name;$('#file-viewer-content').textContent='加载中...';modal.classList.add('show');fetch('/api/file?path='+encodeURIComponent(path)).then(r=>r.json()).then(d=>{$('#file-viewer-content').textContent=d.error?'错误: '+d.error:d.content}).catch(()=>{$('#file-viewer-content').textContent='加载失败'}) }

function openImageViewer(path,name){
    const modal=$('#file-viewer-modal');
    $('#file-viewer-title').textContent=name;
    $('#file-viewer-content').innerHTML='<img src="/api/file/raw?path='+encodeURIComponent(path)+'" style="max-width:100%;max-height:60vh;object-fit:contain;border-radius:6px" onerror="this.outerHTML=\'<span style=color:var(--red)>Failed to load image</span>\'">';
    modal.classList.add('show');
}

function openFileEditor(path,name){
    currentEditPath=path;
    $('#file-editor-title').textContent='编辑: '+name;
    $('#file-editor-content').value='加载中...';
    $('#file-editor-modal').classList.add('show');
    fetch('/api/file?path='+encodeURIComponent(path)).then(r=>r.json()).then(d=>{
        $('#file-editor-content').value=d.error?'错误: '+d.error:d.content;
    }).catch(()=>{$('#file-editor-content').value='加载失败'});
}

function bindNodes(){
    $('#btn-node-refresh').addEventListener('click',e=>{ ripple(e,e.currentTarget);loadNodes();sndClick() });
    $('#btn-node-save').addEventListener('click',e=>{ ripple(e,e.currentTarget);$('#node-save-modal').classList.add('show');$('#node-save-name').value='';setTimeout(()=>$('#node-save-name').focus(),100);sndClick() });
    $('#btn-node-reset').addEventListener('click',e=>{ ripple(e,e.currentTarget);if(confirm('清空所有节点？')){doReset();toast('节点已清空','info');sndClick()} });
    $('#btn-confirm-node-save').addEventListener('click',e=>{ ripple(e,e.currentTarget);const n=$('#node-save-name').value.trim();if(n){_pendingParent[n]=getActiveNode();_pendingActive=n;socket.emit('node_action',{action:'save',name:n});$('#node-save-modal').classList.remove('show');toast('节点已保存: '+n,'success')} });
    $('#btn-cancel-node-save').addEventListener('click',()=>$('#node-save-modal').classList.remove('show'));
    $('#node-save-name').addEventListener('keydown',e=>{ if(e.key==='Enter')$('#btn-confirm-node-save').click() });
    bindNodeZoom();
}

let nodeZoom={scale:1,panX:0,panY:0,dragging:false,startX:0,startY:0};
function bindNodeZoom(){
    const svg=$('#node-svg'),g=$('#node-svg-group');
    function applyView(){ g.setAttribute('transform','translate('+nodeZoom.panX+','+nodeZoom.panY+') scale('+nodeZoom.scale+')') }
    svg.addEventListener('wheel',e=>{ e.preventDefault();const d=e.deltaY>0?.9:1.1;nodeZoom.scale=Math.max(.2,Math.min(3,nodeZoom.scale*d));applyView() },{passive:false});
    svg.addEventListener('mousedown',e=>{ if(e.target.closest('.svg-node'))return;nodeZoom.dragging=true;nodeZoom.startX=e.clientX-nodeZoom.panX;nodeZoom.startY=e.clientY-nodeZoom.panY;svg.style.cursor='grabbing' });
    document.addEventListener('mousemove',e=>{ if(!nodeZoom.dragging)return;nodeZoom.panX=e.clientX-nodeZoom.startX;nodeZoom.panY=e.clientY-nodeZoom.startY;applyView() });
    document.addEventListener('mouseup',()=>{ nodeZoom.dragging=false;$('#node-svg').style.cursor='grab' });
    $('#btn-node-zoomin').addEventListener('click',()=>{ nodeZoom.scale=Math.min(3,nodeZoom.scale*1.2);applyView() });
    $('#btn-node-zoomout').addEventListener('click',()=>{ nodeZoom.scale=Math.max(.2,nodeZoom.scale*.8);applyView() });
    $('#btn-node-fit').addEventListener('click',()=>{
        const svg=$('#node-svg'),g=$('#node-svg-group');
        const nodes=g.querySelectorAll('.svg-node');
        if(!nodes.length){nodeZoom.scale=1;nodeZoom.panX=0;nodeZoom.panY=0;g.setAttribute('transform','translate(0,0) scale(1)');return}
        let minX=Infinity,minY=Infinity,maxX=-Infinity,maxY=-Infinity;
        nodes.forEach(n=>{
            const t=n.getAttribute('transform');
            const m=t.match(/translate\(([^,]+),([^)]+)\)/);
            if(!m)return;
            const x=parseFloat(m[1]),y=parseFloat(m[2]);
            minX=Math.min(minX,x);minY=Math.min(minY,y);
            maxX=Math.max(maxX,x+90);maxY=Math.max(maxY,y+30);
        });
        const W=svg.clientWidth||240,H=svg.clientHeight||300;
        const treeW=maxX-minX,treeH=maxY-minY;
        const scaleX=W/(treeW+40),scaleY=H/(treeH+40);
        const scale=Math.min(scaleX,scaleY,2);
        const panX=(W-treeW*scale)/2-minX*scale;
        const panY=(H-treeH*scale)/2-minY*scale;
        nodeZoom.scale=scale;nodeZoom.panX=panX;nodeZoom.panY=panY;
        g.setAttribute('transform','translate('+panX+','+panY+') scale('+scale+')');
    });
}

function loadNodes(){ fetch('/api/node/list').then(r=>r.json()).then(d=>renderNodes(d.nodes||[])).catch(()=>{}) }

function getNodeParent(){ try{return JSON.parse(localStorage.getItem('node-parent')||'{}') }catch(e){return {}} }
function setNodeParent(p){ localStorage.setItem('node-parent',JSON.stringify(p)) }
function getActiveNode(){ return localStorage.getItem('active-node')||'init' }
function setActiveNode(n){ localStorage.setItem('active-node',n) }
function getNodePositions(){ try{return JSON.parse(localStorage.getItem('node-positions')||'{}') }catch(e){return {}} }
function setNodePositions(p){ localStorage.setItem('node-positions',JSON.stringify(p)) }
function syncActiveHighlight(){ const active=getActiveNode();document.querySelectorAll('.svg-node').forEach(el=>{ el.classList.toggle('active',el.getAttribute('data-name')===active) }) }

let _pendingActive=null;
let _pendingParent={};
let _isDraggingNode=false;

function getChildren(nodeName){
    const p=getNodeParent();
    const children=[];
    function find(n){ Object.keys(p).forEach(k=>{ if(p[k]===n){children.push(k);find(k)} }) }
    find(nodeName);
    return children;
}

function deleteNodeCascade(name){
    const all=[name,...getChildren(name)];
    const p=getNodeParent();const pos=getNodePositions();
    all.forEach(n=>{ delete p[n];delete pos[n] });
    setNodeParent(p);setNodePositions(pos);
    if(all.includes(getActiveNode()))setActiveNode('init');
    socket.emit('node_action',{action:'delete',name:name,names:all});
    setTimeout(loadNodes,500);
}

function renderNodes(nodes){
    if(nodes.length<=1&&nodes.every(n=>n.name==='init')){
        setNodeParent({});setNodePositions({});_pendingParent={};_pendingActive=null;setActiveNode('init');
    }
    const svg=$('#node-svg'),g=$('#node-svg-group'),hint=$('#node-empty-hint');
    g.textContent='';
    if(!nodes.length){ hint.style.display='';svg.style.display='none';return }
    hint.style.display='none';svg.style.display='block';

    const names=new Set(nodes.map(n=>n.name));
    const parent=getNodeParent();
    let changed=false;

    nodes.forEach(n=>{
        if(n.name==='init'||n.name==='temp')return;
        if(!parent[n.name]){
            if(_pendingParent[n.name]){ parent[n.name]=_pendingParent[n.name] }
            else if(names.has(getActiveNode())){ parent[n.name]=getActiveNode() }
            else{ parent[n.name]='init' }
            changed=true;
        }
    });
    if(_pendingActive&&names.has(_pendingActive)){ setActiveNode(_pendingActive);_pendingActive=null }
    Object.keys(parent).forEach(k=>{
        if(!names.has(k)){ delete parent[k];delete _pendingParent[k];changed=true }
        else if(parent[k]&&!names.has(parent[k])&&parent[k]!=='init'){ parent[k]=getActiveNode();changed=true }
    });
    Object.keys(_pendingParent).forEach(k=>{ if(names.has(k)&&parent[k])delete _pendingParent[k] });
    if(changed)setNodeParent(parent);

    const tree={};
    nodes.forEach(n=>{ if(n.name==='temp')return;tree[n.name]={name:n.name,children:[],depth:0,x:0,y:0} });
    const root=tree['init'];
    if(!root)return;

    Object.values(tree).forEach(n=>{
        if(n===root)return;
        const pName=parent[n.name];
        if(pName&&tree[pName]&&pName!==n.name){ tree[pName].children.push(n) }
        else{ root.children.push(n) }
    });

    function setDepth(n,d){ n.depth=d;n.children.forEach(c=>setDepth(c,d+1)) }
    setDepth(root,0);

    const W=svg.clientWidth||240,H=svg.clientHeight||300;
    const nodeW=90,nodeH=30,padX=20,padY=50;
    const depthNodes={};
    Object.values(tree).forEach(n=>{ if(!depthNodes[n.depth])depthNodes[n.depth]=[];depthNodes[n.depth].push(n) });

    const savedPos=getNodePositions();
    function layoutRow(row,rowY){
        const totalW=row.length*(nodeW+padX)-padX;
        let startX=Math.max(10,(W-totalW)/2);
        row.forEach((n,i)=>{
            if(savedPos[n.name]){ n.x=savedPos[n.name].x;n.y=savedPos[n.name].y }
            else{ n.x=startX+i*(nodeW+padX)+nodeW/2;n.y=rowY }
        });
    }
    function layoutTree(node, left, right, depth) {
        const y = 25 + depth * (nodeH + padY);
        const mid = (left + right) / 2;
        node.x = mid;
        node.y = y;
        if (node.children.length === 0) return;
        const childWidth = nodeW + padX;
        const totalNeeded = node.children.length * childWidth;
        const start = Math.max(left, mid - totalNeeded / 2);
        node.children.forEach((c, i) => {
            const cLeft = start + i * childWidth;
            const cRight = cLeft + childWidth;
            layoutTree(c, cLeft, cRight, depth + 1);
        });
    }
    const svgW = svg.clientWidth || 240;
    layoutTree(root, 0, svgW, 0);
    Object.keys(savedPos).forEach(name => {
        if (tree[name]) {
            tree[name].x = savedPos[name].x;
            tree[name].y = savedPos[name].y;
        }
    });

    const colorMap=['#569cd6','#6a9955','#c586c0','#ce9178','#4ec9b0','#dcdcaa','#f44747','#9cdcfe'];

    function drawLinks(n){
        n.children.forEach(c=>{
            const path=document.createElementNS('http://www.w3.org/2000/svg','path');
            const x1=n.x,y1=n.y+nodeH/2,x2=c.x,y2=c.y-nodeH/2;
            const midY=(y1+y2)/2;
            path.setAttribute('d','M'+x1+','+y1+' C'+x1+','+midY+' '+x2+','+midY+' '+x2+','+y2);
            path.setAttribute('class','svg-link');
            path.setAttribute('stroke',colorMap[c.depth%colorMap.length]);
            g.appendChild(path);
            drawLinks(c);
        });
    }
    drawLinks(root);

    const active=getActiveNode();
    function drawNode(n){
        const color=colorMap[n.depth%colorMap.length];
        const ng=document.createElementNS('http://www.w3.org/2000/svg','g');
        ng.setAttribute('class','svg-node'+(n.name===active?' active':''));
        ng.setAttribute('data-name',n.name);
        ng.setAttribute('transform','translate('+(n.x-nodeW/2)+','+(n.y-nodeH/2)+')');

        const rect=document.createElementNS('http://www.w3.org/2000/svg','rect');
        rect.setAttribute('width',nodeW);rect.setAttribute('height',nodeH);
        rect.setAttribute('fill',color+'18');rect.setAttribute('stroke',color);
        ng.appendChild(rect);

        const txt=document.createElementNS('http://www.w3.org/2000/svg','text');
        txt.setAttribute('x',nodeW/2);txt.setAttribute('y',nodeH/2+4);txt.setAttribute('text-anchor','middle');
        txt.textContent=n.name.length>12?n.name.slice(0,12)+'..':n.name;
        ng.appendChild(txt);

        ng.addEventListener('dblclick',e=>{ e.stopPropagation();socket.emit('send_message',{message:'#node load '+n.name});setActiveNode(n.name);sndClick();document.querySelectorAll('.svg-node.active').forEach(x=>x.classList.remove('active'));ng.classList.add('active') });
        ng.addEventListener('click',e=>{ e.stopPropagation() });

        makeDraggable(ng,n);
        g.appendChild(ng);
        n.children.forEach(drawNode);
    }
    drawNode(root);
}

function makeDraggable(ng,nodeData){
    let dragging=false,startX,startY,nodeStartX,nodeStartY;
    ng.addEventListener('mousedown',e=>{
        if(e.button!==0)return;
        e.stopPropagation();
        dragging=true;_isDraggingNode=true;
        document.body.style.userSelect='none';
        document.body.style.webkitUserSelect='none';
        const svg=$('#node-svg');
        const rect=svg.getBoundingClientRect();
        const scale=nodeZoom.scale;
        startX=(e.clientX-rect.left-nodeZoom.panX)/scale;
        startY=(e.clientY-rect.top-nodeZoom.panY)/scale;
        nodeStartX=nodeData.x;
        nodeStartY=nodeData.y;
        ng.classList.add('dragging');
    });
    document.addEventListener('mousemove',e=>{
        if(!dragging)return;
        const svg=$('#node-svg');
        const rect=svg.getBoundingClientRect();
        const scale=nodeZoom.scale;
        const curX=(e.clientX-rect.left-nodeZoom.panX)/scale;
        const curY=(e.clientY-rect.top-nodeZoom.panY)/scale;
        nodeData.x=nodeStartX+(curX-startX);
        nodeData.y=nodeStartY+(curY-startY);
        const nodeW=90,nodeH=30;
        ng.setAttribute('transform','translate('+(nodeData.x-nodeW/2)+','+(nodeData.y-nodeH/2)+')');
        rerenderLinks();
    });
    document.addEventListener('mouseup',()=>{
        if(!dragging)return;
        dragging=false;_isDraggingNode=false;
        document.body.style.userSelect='';
        document.body.style.webkitUserSelect='';
        ng.classList.remove('dragging');
        const pos=getNodePositions();
        pos[nodeData.name]={x:nodeData.x,y:nodeData.y};
        setNodePositions(pos);
        rerenderLinks();
    });
}

function rerenderLinks(){
    const g=$('#node-svg-group');
    g.querySelectorAll('.svg-link').forEach(l=>l.remove());
    const nodeW=90,nodeH=30;
    const colorMap=['#569cd6','#6a9955','#c586c0','#ce9178','#4ec9b0','#dcdcaa','#f44747','#9cdcfe'];
    const parent=getNodeParent();
    const positions={};
    g.querySelectorAll('.svg-node').forEach(ng=>{
        const name=ng.getAttribute('data-name');
        const t=ng.getAttribute('transform');
        const m=t.match(/translate\(([^,]+),([^)]+)\)/);
        if(m)positions[name]={x:parseFloat(m[1])+nodeW/2,y:parseFloat(m[2])+nodeH/2};
    });
    Object.keys(parent).forEach(childName=>{
        const pName=parent[childName];
        if(pName&&positions[pName]&&positions[childName]){
            const p=positions[pName],c=positions[childName];
            const y1=p.y+nodeH/2,y2=c.y-nodeH/2;
            const path=document.createElementNS('http://www.w3.org/2000/svg','path');
            path.setAttribute('d','M'+p.x+','+y1+' C'+p.x+','+((y1+y2)/2)+' '+c.x+','+((y1+y2)/2)+' '+c.x+','+y2);
            path.setAttribute('class','svg-link');
            path.setAttribute('stroke',colorMap[0]);
            path.style.opacity='.35';
            g.insertBefore(path,g.firstChild);
        }
    });
}

function bindNodeContextMenu(){
    const menu=$('#node-context-menu');
    let targetNode=null;
    document.addEventListener('contextmenu',e=>{
        const nodeEl=e.target.closest('.svg-node');
        if(!nodeEl){menu.classList.remove('show');return}
        e.preventDefault();
        targetNode=nodeEl.getAttribute('data-name');
        if(!targetNode)return;
        menu.style.left=e.clientX+'px';menu.style.top=e.clientY+'px';
        menu.classList.add('show');
    });
    document.addEventListener('click',()=>menu.classList.remove('show'));
    document.addEventListener('keydown',e=>{if(e.key==='Escape')menu.classList.remove('show')});
    menu.querySelectorAll('.ctx-item').forEach(item=>{
        item.addEventListener('click',()=>{
            if(!targetNode)return;
            const action=item.dataset.action;
            if(action==='load'){socket.emit('send_message',{message:'#node load '+targetNode});setActiveNode(targetNode)}
            else if(action==='input'){fillInput('#node load '+targetNode)}
            else if(action==='delete'){
                deleteNodeCascade(targetNode);
                toast('已删除 '+targetNode+' 及子节点','info');sndClick()
            }
            menu.classList.remove('show');sndClick();
        });
    });
}

function bindQuick(){
    document.querySelectorAll('.quick-btn[data-cmd]').forEach(b=>b.addEventListener('click',e=>{ ripple(e,b);const c=b.dataset.cmd;if(c)fillInput(c) }));
    $('#btn-quick-save-node').addEventListener('click',e=>{ ripple(e,e.currentTarget);$('#node-save-modal').classList.add('show');$('#node-save-name').value='';setTimeout(()=>$('#node-save-name').focus(),100);sndClick() });
    $('#btn-pause').addEventListener('click',e=>{ ripple(e,e.currentTarget);socket.emit('pause');sndClick();toast('已发送急停','info') });
    $('#btn-chat-clear').addEventListener('click',e=>{ ripple(e,e.currentTarget);seenMsgIds.clear();doReset();moveLogoToWelcome();$('#chat-messages').innerHTML='<div class="chat-welcome" id="chat-welcome"><div class="welcome-icon" id="welcome-logo"><img src="/static/logo.jpg" alt="SynapseAgent" style="width:100%;height:100%;object-fit:cover;border-radius:16px"></div><h2>SynapseAgent</h2><p>Think Backward, And Re:Start!</p><p class="welcome-hint">赞美万机之神欧姆弥赛亚</p></div>';sndClick() });
}

function bindModals(){
    $('#btn-settings').addEventListener('click',()=>{ loadConfig();$('#settings-modal').classList.add('show');sndClick() });
    $('#btn-save-settings').addEventListener('click',e=>{ ripple(e,e.currentTarget);fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({API_KEY:$('#setting-apikey').value.trim(),BASE_URL:$('#setting-url').value.trim(),MODEL:$('#setting-model').value.trim(),lang:$('#setting-lang').value})}).then(r=>r.json()).then(()=>{loadConfig();$('#settings-modal').classList.remove('show');toast('配置已保存','success');fillInput('#bot reload')}) });
    $('#btn-cancel-settings').addEventListener('click',()=>$('#settings-modal').classList.remove('show'));
    $('#btn-save-file').addEventListener('click',e=>{ ripple(e,e.currentTarget);fetch('/api/file/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:currentEditPath,content:$('#file-editor-content').value})}).then(r=>r.json()).then(d=>{if(d.success){toast('文件已保存','success');$('#file-editor-modal').classList.remove('show');loadFiles(currentPath)}else toast('保存失败','error')}) });
    $('#btn-cancel-file').addEventListener('click',()=>$('#file-editor-modal').classList.remove('show'));
    document.querySelectorAll('.modal-close-btn').forEach(b=>b.addEventListener('click',()=>b.closest('.modal-overlay').classList.remove('show')));
    document.addEventListener('keydown',e=>{ if(e.key==='Escape')document.querySelectorAll('.modal-overlay.show').forEach(m=>m.classList.remove('show')) });
}

function bindTheme(){
    const saved=localStorage.getItem('synapse-accent');if(saved)setAccent(saved);
    $('#btn-theme').addEventListener('click',()=>{ $('#theme-modal').classList.add('show');sndClick() });
    document.querySelectorAll('.theme-swatch').forEach(s=>{ if(s.dataset.color===(saved||'#569cd6'))s.classList.add('active');s.addEventListener('click',()=>{document.querySelectorAll('.theme-swatch').forEach(x=>x.classList.remove('active'));s.classList.add('active');setAccent(s.dataset.color);localStorage.setItem('synapse-accent',s.dataset.color);sndClick()}) });
    $('#btn-apply-custom-color').addEventListener('click',e=>{ ripple(e,e.currentTarget);const c=$('#theme-custom-color').value;document.querySelectorAll('.theme-swatch').forEach(x=>x.classList.remove('active'));setAccent(c);localStorage.setItem('synapse-accent',c);toast('主题色已更新','success');sndClick() });
}
function setAccent(hex){ document.documentElement.style.setProperty('--accent',hex);const r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);document.documentElement.style.setProperty('--accent-dim',hex);document.documentElement.style.setProperty('--accent-glow','rgba('+r+','+g+','+b+',.15)');document.querySelectorAll('.top-title i,.panel-header>i,.control-label i,.modal-header h3 i').forEach(el=>el.style.color=hex) }

function bindKeyboard(){
    document.addEventListener('keydown',e=>{
        konamiBuffer.push(e.keyCode);if(konamiBuffer.length>12)konamiBuffer.shift();
        if(konamiBuffer.join(',')===KONAMI.join(',')){ konamiBuffer=[];toast('↑↑↓↓←→←→BABA — 万机之神降临！','success');sndEaster();confetti();document.body.style.transition='filter 1s';document.body.style.filter='hue-rotate(180deg)';setTimeout(()=>{document.body.style.filter=''},3000) }
        if(e.ctrlKey||e.metaKey){
            if(e.key==='l'){e.preventDefault();$('#btn-chat-clear').click()}
            if(e.key===','){e.preventDefault();$('#btn-settings').click()}
            if(e.key==='r'){e.preventDefault();resetLayout();toast('布局已重置','info');sndClick()}
        }
        if(e.key==='/'&&document.activeElement.tagName!=='INPUT'&&document.activeElement.tagName!=='TEXTAREA'){e.preventDefault();$('#chat-input').focus()}
        if(e.key==='?'&&document.activeElement.tagName!=='INPUT'&&document.activeElement.tagName!=='TEXTAREA'){e.preventDefault();$('#shortcuts-modal').classList.toggle('show');sndClick()}
    });
}

function bindResize(){
    document.querySelectorAll('.resize-handle').forEach(handle=>{
        let startPos,startSize,target,prop;
        handle.addEventListener('mousedown',e=>{
            e.preventDefault();handle.classList.add('active');
            const type=handle.dataset.resize;
            if(type==='left-center'){target=$('#left-col');prop='width';startPos=e.clientX;startSize=target.offsetWidth}
            else if(type==='center-right'){target=$('#right-col');prop='width';startPos=e.clientX;startSize=target.offsetWidth}
            else if(type==='node-quick'){target=$('#node-panel');prop='height';startPos=e.clientY;startSize=target.offsetHeight}
            const onMove=ev=>{
                if(!target)return;
                if(prop==='width'){const diff=ev.clientX-startPos;if(type==='left-center')target.style.width=Math.max(160,startSize+diff)+'px';else target.style.width=Math.max(160,startSize-diff)+'px'}
                else{const diff=ev.clientY-startPos;target.style.height=Math.max(80,startSize+diff)+'px';target.style.flex='none'}
            };
            const onUp=()=>{ handle.classList.remove('active');document.removeEventListener('mousemove',onMove);document.removeEventListener('mouseup',onUp);saveLayout() };
            document.addEventListener('mousemove',onMove);document.addEventListener('mouseup',onUp);
        });
    });
}
function saveLayout(){ const l=$('#left-col'),r=$('#right-col'),n=$('#node-panel');localStorage.setItem('synapse-layout',JSON.stringify({leftW:l.style.width||'',rightW:r.style.width||'',nodeH:n.style.height||''})) }
function restoreLayout(){ try{const l=JSON.parse(localStorage.getItem('synapse-layout'));if(!l)return;if(l.leftW)$('#left-col').style.width=l.leftW;if(l.rightW)$('#right-col').style.width=l.rightW;if(l.nodeH){$('#node-panel').style.height=l.nodeH;$('#node-panel').style.flex='none'}}catch(e){} }
function resetLayout(){ const l=$('#left-col'),r=$('#right-col'),n=$('#node-panel');l.style.width='';r.style.width='';n.style.height='';n.style.flex='';localStorage.removeItem('synapse-layout') }
function bindResetLayout(){ $('#btn-reset-layout').addEventListener('click',()=>{ resetLayout();toast('布局已重置','info');sndClick() }) }

document.addEventListener('DOMContentLoaded',init);
})();
