# SynapseAgent Web UI

SynapseAgent 的 Web 前端界面，基于 Flask + SocketIO 构建，提供可视化的节点式对话管理体验。

## 快速启动

```bash
cd SynapseAgent/web
pip install -r requirements.txt
python server.py
```

浏览器自动打开 `http://localhost:5001`，或双击 `start.bat`。

## 项目结构

```
web/
├── server.py              # Flask 后端服务
├── requirements.txt       # Python 依赖
├── start.bat              # Windows 一键启动
├── models.json            # 保存的模型配置
└── static/
    ├── index.html         # 主页面
    ├── logo.jpg           # Logo 图片
    ├── css/
    │   └── style.css      # 全局样式
    └── js/
        └── app.js         # 前端逻辑
```

## 核心功能

### 节点式对话管理

借鉴 Git 分支思想，支持对话状态的保存、加载和回退。

- **保存节点**：将当前对话状态存档
- **加载节点**：从指定节点恢复对话
- **回退**：按轮数或事件回退对话
- **节点图**：SVG 可视化节点树，支持拖拽、缩放、平移

### 实时对话

通过 WebSocket 实现前后端实时通信：

- 消息发送与接收
- 思考状态指示器
- 推理内容显示（需模型支持 `reasoning_content`）
- 急停功能

### 文件管理

- 浏览项目目录结构
- 查看/编辑文本文件
- 图片预览
- 路径复制

### 配置管理

与后端共享 `SynapseAgent/config.json`，前端修改实时生效：

- API Key / Base URL / Model
- 系统开关（推理显示、重复指令中断、指令确认、日志记录）
- 人设/提示词切换
- 模型快速切换（支持保存多个模型配置）

## 系统开关

| 开关 | 配置键 | 说明 |
|------|--------|------|
| 输出思考显示 | `allow_reasoning` | 显示 AI 推理过程（需模型支持） |
| 重复指令中断 | `break` | 相同命令重复执行时是否中断 |
| 指令确认 | `cmd_check` | 系统命令是否需要用户确认 |
| 启用日志 | `enable_log` | 是否保存会话日志到 `logs/` |

开关操作会同时写入配置文件并更新引擎运行时状态。

## 彩蛋

- **双击 Logo**：旋转动画 + 随机祝福语，每 5 圈触发五彩纸屑
- **右键 Logo**：硬币翻转动画
- **拖拽 Logo**：带物理惯性的拖拽效果 + 悬停辉光
- **秘籍**：`↑↑↓↓←→←→BABA` 触发全局色相旋转 + 彩纸 + 音效
- 赞美万机之神欧姆弥赛亚

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Enter` | 发送消息 |
| `Shift+Enter` | 换行 |
| `/` | 聚焦输入框 |
| `?` | 显示快捷键 |
| `Ctrl+L` | 清空聊天 |
| `Ctrl+,` | 打开设置 |
| `Ctrl+R` | 重置布局 |
| `Esc` | 关闭弹窗 |

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/config` | 获取配置 |
| POST | `/api/config` | 更新配置 |
| GET | `/api/models` | 获取模型列表 |
| POST | `/api/models` | 添加模型 |
| POST | `/api/models/apply` | 应用模型配置 |
| GET | `/api/files` | 列出文件 |
| GET | `/api/file` | 读取文件 |
| POST | `/api/file/save` | 保存文件 |
| GET | `/api/skills` | 列出技能 |
| GET | `/api/prompts` | 列出提示词 |
| GET | `/api/status` | 引擎状态 |
| GET | `/api/node/list` | 节点列表 |

## SocketIO 事件

### 客户端 → 服务端

| 事件 | 数据 | 说明 |
|------|------|------|
| `send_message` | `{message}` | 发送消息 |
| `pause` | - | 急停 |
| `node_action` | `{action, name}` | 节点操作 |
| `reset_engine` | - | 重置引擎 |
| `file_action` | `{action, new_path}` | 文件操作 |
| `update_setting` | `{key, value}` | 更新配置+引擎 |

### 服务端 → 客户端

| 事件 | 数据 | 说明 |
|------|------|------|
| `new_message` | `{id, content, type, timestamp}` | 新消息 |
| `thinking` | `{content, timestamp}` | 思考指示器 |
| `processing` | `{active}` | 处理状态 |
| `nodes_updated` | `{nodes}` | 节点树更新 |
| `system_notice` | `{type, msg}` | 系统通知 |
| `setting_updated` | `{key, value}` | 配置已更新 |

## 消息类型

| type | 说明 | 样式 |
|------|------|------|
| `user` | 用户消息 | 蓝色气泡，右对齐 |
| `assistant` | AI 回复 | 深色气泡，左对齐 |
| `thinking` | 推理内容 | 青色斜体等宽字体 |
| `system` | 系统消息 | 橙色等宽字体 |
| `debug` | 调试信息 | 紫色等宽字体 |

## 配置文件

前端与后端共享 `SynapseAgent/config.json`：

```json
{
    "API_KEY": "sk-xxx",
    "BASE_URL": "https://api.example.com/v1",
    "MODEL": "model-name",
    "base_path": "E:/SynapseAgent/SynapseAgent",
    "lang": "zh_cn",
    "break": true,
    "cmd_check": false,
    "enable_log": true
}
```

## 依赖

- Flask >= 2.3.0
- Flask-SocketIO >= 5.3.0
- OpenAI >= 1.0.0
