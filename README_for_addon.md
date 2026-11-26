## Synapse Agent插件文档

Synapse Agent 支持**程序调用**、**内置 HTTP 服务**与**插件（Addon）机制**三种扩展方式。

---

## 一、程序调用

CNMD 类位于 `./src/main/CNMD.py` 中。

实例化 CNMD 对象，将自动创建消息队列，使用 `CNMD(指令)` 方法控制。

输出结果将写入到变量 `msg_stack`，通过逐次读取来获取输出。

注意：
- CNMD 对象的回答循环有急停设置，将 `mslock` 属性设为 `False` 则在当轮拦截并退出循环。
- CNMD 对象拥有回答状态，`status` 属性为 1 时表示未结束回答循环，结束后归零。

> `src/main/CNMD.py` 也可作为**启动入口**直接运行（`python src/main/CNMD.py [预设名]`），此时会自动切到项目根目录并以主程序方式拉起 `SynapseAgent.py`；作为模块被 `import` 时该入口逻辑不生效，不影响类调用。

---

## 二、内置 HTTP 服务

自本版本起，HTTP 服务**已整合进主程序**，启动 SynapseAgent（默认 `start.bat` → `python src\main\CNMD.py`）时自动开启，无需再单独运行 `server.py`。

- 地址：`http://127.0.0.1:56700/cnmd`，**单端口**
- **端口占用策略**：若 56700 已被占用，则不启用网络服务，主程序静默以纯 CLI 运行
- **并发模型**：CLI 输入与网络 `ask` 共用同一任务队列，由唯一 worker 串行处理，同一时刻只跑一条任务
- **输出分发**：
  - 模型输出在 CLI 正常显示，同时**镜像**进**网络独立缓冲**，供网络端 `answer` 获取
  - 网络端输入会在 CLI 以 `[NET Input]` 前缀原样显示，执行结束后与 CLI 一致显示结果
- 网络端只从**独立缓冲**取回复，不干扰 CLI 输出；网络暂停指令 `#p` / `#pause` 直接释放 `mslock` 并返回 `paused`

body 参数：
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

/*接收信息：从网络缓冲取出最早一条回复*/
{
    "method":"answer",
    "params":{
        "type":"rp"
    }
}
/*返回结果*/
{
    "status": [回答状态],
    "response": [返回信息]
}

/*接收所有记录信息：读取整个网络缓冲，不消费*/
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

回答状态表示 Agent 当前是否仍在处理，0 表示空闲，1 表示仍在处理（含队列未清空、缓冲未取完等情况）。

调用示例(powershell)

```bash
Invoke-RestMethod -Uri "http://127.0.0.1:56700/cnmd" `
    -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body '{"method":"ask","params":{"content":"你好"}}'
```

由于回答进程和实际使用为异步关系，建议单开线程用于接收信息，固定时间访问输出结果。

---

## 三、插件（Addon）标准化

### 目录与入口规范

| 规则 | 约定 |
|---|---|
| 插件目录 | `addon/<插件名>/` |
| 启动入口 | `addon/<插件名>/main.py`（固定） |
| 启动清单 | `addon/config.json` 的 `enabled` 列表 |
| 运行方式 | 由主程序以**独立控制台窗口（独立进程）**拉起 |

`addon/config.json` 示例：

```json
{
    "enabled": ["live2d"]
}
```

主程序在**网络服务就绪之后**按清单逐个启动插件，等价于：

```python
subprocess.Popen(
    [sys.executable, main_py],
    cwd=插件目录,
    creationflags=0x00000010  # CREATE_NEW_CONSOLE，单开窗口
)
```

启动成功在 CLI 打印 `[ADDON] 已启动插件: <名>`；未找到 `main.py` 则打印跳过提示，不影响主程序。

### 插件编写约定

1. `main.py` 视为**独立程序入口**，需自行完成 `sys.path` 与工作目录设置，例如：
   ```python
   import os, sys
   BASE_DIR = os.path.dirname(os.path.abspath(__file__))
   sys.path.insert(0, BASE_DIR)
   os.chdir(BASE_DIR)   # 保证插件内相对路径（配置、模型、提示词）正确
   ```
2. 插件与主程序通过 `http://127.0.0.1:56700/cnmd` 通讯（即上面的 `ping / ask / answer`）。
3. 插件是**独立进程**，关闭主程序**不会**自动结束插件窗口。
4. 若主程序因端口占用未启用网络服务，插件将无法连接主程序——这是端口占用策略的**预期结果**。

### 最小插件骨架

```
addon/
├── config.json          # {"enabled": ["demo"]}
└── demo/
    └── main.py          # 固定入口
```

`addon/demo/main.py`：

```python
# -*- coding: utf-8 -*-
import os, sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.chdir(BASE_DIR)

def main():
    # 在此实现插件逻辑，通过 HTTP 与主程序交互
    print('demo addon started')

if __name__ == '__main__':
    main()
```

---

## 四、工具链穿透

你可以将自己的工具与原生工具混用，通过忽略表使工具调用指令穿透工具调用模块，直接发送到输出文本中。

Synapse Agent 使用指令区调用，指令区格式 `指令