# SynapseAgent（简明版）

> **Think Backward, And Re:Start!**

SynapseAgent 是一个节点式对话管理的 Agent 型 AI 助手，能实际操作文件、执行命令、访问网络。

> 完整文档请见 [README.md](README.md)

---

## 📦 安装

1. 克隆或下载本项目，进入项目根目录。
2. 安装依赖：

```bash
pip install -r requirements.txt
```

依赖项：
- `openai` — LLM API 调用
- `colorama` — 终端彩色输出

---

## ⚙️ 基础设置

配置文件位于 `./database` 目录：

| 文件 | 说明 |
|------|------|
| `config.json` | 主配置，默认为空，首次启动自动进入引导程序创建 |
| `config_model.json` | 模型参数（如 `temperature`），可留空 |
| `config_mcp.json` | MCP 服务配置，可留空 |

### 首次启动

直接运行 `start.bat`，CLI 会启动配置引导程序，按提示填入信息后自动生成 `config.json` 并启动。

### 手动配置 `config.json`

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
| `API_KEY` | API 密钥（支持任何 OpenAI 兼容接口） |
| `BASE_URL` | API 基础 URL |
| `MODEL` | 模型名称 |
| `base_path` | Agent 操作文件的根目录 |
| `lang` | 提示语言，支持 `zh_cn`、`en_us` 等 |
| `break` | 重复执行相同命令时是否中断任务 |
| `cmd_check` | 系统命令是否需要用户确认 |

### 启动

```bash
start.bat
```

如使用自定义预设：

```bash
python SynapseAgent.py [预设名称]
```

---

## 📄 许可证

本项目采用 [Apache 2.0](LICENSE) 许可证。