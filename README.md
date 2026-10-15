# SynapseAgent

> **Think Backward, And Re:Start!**

> **只想快速上手？** 请看简明版文档：[README_short.md](README_short.md)（仅含安装与基础设置）

> **插件开发须知** 插件文档文档：[README_for_addon.md](README_for_addon.md)

![](logo.png)

SynapseAgent 是一个**节点式对话管理**的 Agent 型 AI 助手，让 AI 不仅仅是聊天，而是真正能**操作文件、执行命令、访问网络**的工作伙伴。 

它借鉴 Git 分支思想，允许你在任意位置**保存、回退对话状态**，随时探索不同对话分支，再也不用担心对话走偏无法回头。

本项目为[CNMD-Agent](https://github.com/MichaelHyan/Cluster-Node-Manager-DataSystem)的改进版，使用相同的控制逻辑，针对CLI模式进行优化。

---

## ✨ 核心特性

- **🔗 节点式管理**：像 Git 一样保存、加载、回退对话状态，安全探索不同方向。
- **⚡ 事件驱动 Agent**：AI 可自主调用工具（文件、终端、网络）完成多步任务，而非仅仅回答问题。
- **📁 文件操作**：目录浏览、文件读写、删除等，直接操作工作目录。
- **💻 命令执行**：支持 CMD / PowerShell 命令，可执行系统任务。
- **🌐 网络访问**：内置网页抓取、Ping 检测，可获取网络信息。
- **🖼️ 多模态支持**：通过编码传递图片、音频、视频数据（依赖模型能力）。
- **🧠 记忆数据库**：持久化记忆，智能提取与检索，让 Agent 拥有长期记忆。
- **🧩 技能模块**：可扩展的 Skill 系统，Agent 可动态学习新技能。
- **🎭 提示词自定义**：灵活组合 persona、skills、extra 模块，打造专属 Agent。
- **📝 自动日志**：每次会话保存完整记录，方便回溯分析。
- **🔄 节点回溯**：支持按事件或轮数回退，精准控制对话走向。

---

## 📌 核心概念

### 节点（Node）

在每次 Agent 开始处理任务前，你可以将当前对话状态存档为一个“节点”。  
之后无论对话如何发展，你都可以随时加载之前的节点，从那里重新开始，就像 Git 分支一样。

```text
    #node save eventb
          ↓
eventA-eventB-eventC-eventD->...
(init)    |
          | -> #node load eventb
          |
       eventE->eventF->....
      (->eventB)
```

### 事件（Event）

你的输入 → Agent 可能调用工具 → 工具返回结果 → Agent 最终回答  
这一整个闭环称为一个事件。事件驱动模式下，Agent 会持续调用工具直到任务完成。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

依赖项：
- `openai` — LLM API 调用
- `colorama` — 终端彩色输出

### 2. 配置

主要配置文件位于`./config`目录下，包含：
- config.json 默认为空，初次启动CLI会自动进入引导程序辅助创建
- config_model.json 默认为空，可加入openai接口参数
- config_mcp.json 保存mcp配置信息

首次运行时将启动配置引导程序。根据引导填入信息，结束后将在本地保存`config.json`并启动程序。

你可以随时修改`config.json`。

```json
{
    "API_KEY": "sk-your-api-key",
    "BASE_URL": "https://api.deepseek.com/v1",
    "MODEL": "deepseek-v4-pro",
    "base_path": "你的工作目录路径",
    "lang": "zh_cn",
    "break": true,
    "cmd_check": false
}
```

| 配置项 | 说明 |
|--------|------|
| `API_KEY` | 你的 API 密钥（支持任何 OpenAI 兼容接口） |
| `BASE_URL` | API 基础 URL |
| `MODEL` | 模型名称 |
| `base_path` | Agent 操作文件的根目录，Agent 将视该目录为你的项目目录 |
| `lang` | 工具提示语言，支持 `zh_cn`、`en_us` 等 |
| `break` | 重复执行相同命令时是否中断任务（`true` 中断/`false` 拒绝但继续） |
| `cmd_check` | 系统命令是否需要用户确认（`true` 需要/`false` 不需要） |

> 如需调整模型参数（如 `temperature`），可修改 `config_model.json`（仅对支持该参数的模型生效）。

### 3. 启动

直接启动start.bat。

如果你有自定义的预设，则：

```bash
python SynapseAgent.py [预设名称]
```

你可以一次输入多行文字，输入结束后回车两次将信息发送给Agent。

---

## 🎛️ 用户控制命令

在对话中，你可以使用以 `#` 开头的命令：

| 命令 | 说明 |
|------|------|
| `#node save <名称>` | 保存当前对话状态到指定节点 |
| `#node load <名称>` | 从指定节点加载对话状态 |
| `#node delete <名称>` | 删除指定节点存储的索引 |
| `#node list` | 列出所有已保存的节点 |
| `#node savef <名称>` | 将当前上下文和工具调用记录保存到本地文件 |
| `#node loadf <名称>` | 从本地文件载入对话状态 |
| `#node backward <轮数>` | 回退指定轮数的对话（默认1轮） |
| `#node backwardms` | 回退一次事件（回退到本次工具调用前） |
| `#mem save` | 提取当前对话关键信息并存入记忆数据库 |
| `#mem analyse` | 对记忆数据库进行整理、去重和压缩 |
| `#mem compress` | 直接压缩上文，谨慎使用 |
| `#bot reset` | 清空对话记录 |
| `#bot reload` | 重新加载模型参数（API 热更新） |
| `#bot prompt <预设名>` | 切换系统提示词预设（需在 `prompt_loader/config.json` 中定义） |
| `#pause` | 强制暂停当前任务 |
| `#execute` | 确认命令 |
| `#help` | 显示帮助信息 |
| `#exit` | 退出程序 |

---

## 🧩 技能模块系统

`./skills/` 目录下存放了 Agent 可学习的技能文档。系统会根据需要自动查询。

**如何添加自定义技能？**
1. 在 `./skills/` 目录下创建一个新的 `.md` 文件。
2. 用清晰的自然语言描述该技能的用途、参数、步骤、期望返回格式。
3. Agent 即可在需要时读取并学习该技能。

> ⚠️ 技能文件应描述**技能的调用方式**，而不是存放对话记录或记忆内容。

---

## 🧠 系统提示词自定义

系统提示词由三个模块组成，均存放在 `prompt_loader/` 目录：
1. **persona**（基础人设）  
2. **skills**（基础能力，建议保留 `skill_base`）  
3. **extra**（额外规则）

### 配置步骤

1. 在 `prompt_loader/config.json` 中添加你的预设名称：

```json
"我的预设": {
    "persona": "my_persona",
    "skills": "skill_base",
    "extra": "none"
}
```

- 文件名为 `prompt_loader/persona/my_persona.md` 等。
- 若不需要某个模块，可以填 `"none"`。

2. 启动时指定预设：

```bash
python SynapseAgent.py 我的预设
```

也可以在对话中使用 `#bot prompt 我的预设` 动态切换。

---

## 🧰 自定义工具链

你可以为 Agent 添加新的工具。

1. 编写可调用的 Python 函数（或脚本），放置于 `tools/` 目录。
2. 在 `tool_handler.py` 中注册该工具，返回格式：
```json
{
    "sys": "给 LLM 的返回信息",
    "cli": "给用户的可见信息"
}
```
3. （可选）添加多语言支持：在 `lang/` 目录下添加对应语言键。
4. 通过技能文档或提示词，告知 Agent 该工具的调用方式。

---

## MCP服务

你可以自定义MCP服务。

将你的配置信息复制进config_mcp.json，默认如下：

```json
{
    "chrome-devtools": {
        "command": "npx",
        "args": ["-y", "chrome-devtools-mcp@latest"],
        "description": "Chrome DevTools 自动化与调试工具"
    },
    "bocha-mcp": {
      "url": "https://mcp.bochaai.com/mcp",
      "headers": {
        "Authorization": "Bearer sk-xxxx"
      }
    }
}
```

注意：
- 由于突触助理使用的基本工具来自自身工具链而不是本地MCP服务器，所以默认情况下不会主动调用MCP服务，可在系统提示词中自行调整优先级。
- 暂不支持SSE类型MCP

## 🎭 记忆数据库

不同于普通的 `Memory.md`，记忆数据库具备独立的向量式存储，支持智能检索与关联。

- **存储**：`database/mem.json` 存放记忆键值。
- **检索**：Agent 在需要时可自动使用 `$mem` 关键词搜索记忆。
- **手动管理**：
  - `#mem save`  将当前对话关键信息写入记忆库
  - `#mem analyse`  整理压缩记忆库

记忆搜索系统使用本地向量数据库，使用语义向量搜索。

当前数据来源：[TX-WORD2VEC-SMALL](https://github.com/cliuxinxin/TX-WORD2VEC-SMALL)，使用45000-small.txt。

**使用时，如果需要准确的语义查询，请先将其替换为更完善的语义向量文件！**

---

## 📂 日志系统

每次会话自动保存日志于 `./logs/` 目录：
- `{时间戳}.json` — 完整对话记录
- `{时间戳}_node.json` — 节点状态快照
- `{时间戳}_tool.json` — 工具调用记录

---

## 👥 子智能体/多智能体

已整合至相关skill。

使用统一配置的任务-简报结构，根据分配任务创建子智能体线程，各智能体独立处理任务并提交简报。

**并不建议使用该功能。突触助理的设计定位为协作助手，而并非任务规划者，也并不应当有自主决策的权力。子智能体仅为技术验证和特殊需要情况下使用。**

---

## 💻 服务器模式

SynapseAgent可使用http服务器实现本地/局域网信息交换。

使用server.py启动服务器模式，默认端口号56700。

body参数：
```json
/*连通性测试*/
{
    "method":"ping"
}
/*返回结果*/
{
    "status": 0,
    "response": ""
}

/*向Agent发送信息*/
{
    "method":"ask",
    "params":{
        "content": [发送信息]
    }
}
/*返回结果*/
{
    "status": 1,
    "response": ""
}

/*接收信息，同时更新消息队列(接收队列中第一条信息，同时删除队列最晚的信息)*/
{
    "method":"answer",
    "params":{
        "type":"rp"
    }
}
/*返回结果*/
{
    "status": [回答状体],
    "response": [返回信息]
}

/*接收所有记录信息，不更改消息队列(接受整个消息队列)*/
{
    "method":"answer",
    "params":{
        "type":"rl"
    }
}
/*返回结果*/
{
    "status": [回答状态],
    "response": [全部信息]
}
```

回答状态表示agent当前是否在回答循环中，0表示不在循环状态，1表示循环中。

rp模式下，如仍有未接受的信息，或Agent未结束作答，回答状态均返回1。

rl模式下，回答状态仅表示Agent是否正在回答。

调用示例(powershell)

```bash
Invoke-RestMethod -Uri "http://127.0.0.1:56700/cnmd" `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body '{"method":"ask","params":{"content":"你好"}}'
```

---

## **测试中内容**键鼠操作

**该功能极不稳定，强烈不推荐，仅可测试用**

通知Agent读取键鼠操作技能。

注意：

由于大模型自身定位能理极差，突触助理使用纯视觉方案，捕获屏幕，自动标记操作区，根据操作区控制坐标。

算法使用文字区识别来定位可操作区域，因此精度有限。

**完整操作需多次屏幕识别，注意token消耗**

---

## 📄 许可证

本项目采用 [Apache 2.0](LICENSE) 许可证。