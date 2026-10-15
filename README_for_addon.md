## Synapse Agent插件文档

Synapse Agent支持程序调用和http server双控制逻辑。

### 程序调用

CNMD类位于./src/main/CNMD.py中。

实例化CNMD对象，将自动创建消息队列，使用CNMD(指令)方法控制。

输出结果将写入到变量msg_stack，通过逐次读取来获取输出。

### http调用

启动server.py后将自动实例化一个CNMD对象，同时开放127.0.0.1:56700/cnmd，可发送http post获取输出。

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

由于回答进程和实际使用为异步关系，建议单开线程用于接收信息，固定时间访问输出结果。

### 工具链穿透

你可以将自己的工具与原生工具混用，通过忽略表使工具调用指令穿透工具调用模块，直接发送到输出文本中。

Synapse Agent使用指令区调用，指令区格式<tool_call>指令</tool_call>。

启动前发送指令#skipable 指令名1 指令名2 ...以指定忽略表。如有需要也可以用于屏蔽某些原生工具。

### 提示词覆写

你可以主动覆盖当前提示词，无需考虑原有预设提示词。

使用指令#bot prompt PROMPTOVERWRITE 新提示词 来覆盖。