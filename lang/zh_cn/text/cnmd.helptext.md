---
description: cnmd helptext
---
可用命令：
1. 节点操作 (#node)
#node save <节点名称>      - 保存当前对话状态到指定节点
#node load <节点名称>      - 从内存中加载指定节点的对话状态
#node delete <节点名称>    - 删除指定节点的索引
#node list                - 列出所有已保存的节点
#node backward <轮数>     - 回退指定轮数的对话（默认回退1轮）
#node backwardms          - 回退一次事件操作

2. 系统命令
#backup                   - 备份当前工作目录
#help                     - 显示此帮助信息

3. Agent命令
#bot reasoning <状态>     - 开关返回思考内容 (1/0)
#bot reset                - 清空对话记录
#bot reload               - 重载模型参数
#bot prompt <人设名>      - 切换人设（测试接口）

4. 记忆能力
#mem save                 - 总结记忆
#mem analyse              - 整理记忆
#mem compress             - 压缩上文

5. 执行任务
#execute <序号>            - 执行Agent申请的指令
#e <序号>                  - 同上