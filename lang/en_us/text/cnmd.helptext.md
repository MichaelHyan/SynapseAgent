---
description: cnmd helptext
---
Available commands:
1. Node operations (#node)
#node save <node name>      - Save the current conversation state to the specified node
#node load <node name>      - Load the conversation state of the specified node from memory
#node delete <node name>    - Delete the index of the specified node
#node list                  - List all saved nodes
#node backward <rounds>     - Roll back the specified number of conversation rounds (default 1 round)
#node backwardms            - Roll back one event operation

2. System commands
#backup                   - Back up the current working directory
#help                     - Show this help information

3. Agent commands
#bot reasoning <state>     - Toggle returning reasoning content (1/0)
#bot reset                 - Clear conversation history
#bot reload                - Reload model parameters
#bot prompt <persona name> - Switch persona (test interface)

4. Memory capabilities
#mem save                  - Summarize memory
#mem analyse               - Organize memory
#mem compress              - Compress context

5. Execute tasks
#execute <index>           - Execute the command requested by Agent
#e <index>                 - Same as above