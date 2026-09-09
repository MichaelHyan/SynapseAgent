import asyncio, json
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
import httpx
import tools.lang as lang

USE_CN_MIRROR = True
CN_NPM_REGISTRY = "https://registry.npmmirror.com"

with open('config_mcp.json', 'r', encoding='utf-8') as f:
    MCP_SERVERS = json.load(f)

def _build_server_params(server_config: dict) -> StdioServerParameters:
    command = server_config["command"]
    args = list(server_config.get("args", []))
    env = dict(server_config.get("env") or {})
    if USE_CN_MIRROR and command == "npx":
        env.setdefault("NPM_CONFIG_REGISTRY", CN_NPM_REGISTRY)
    return StdioServerParameters(command=command, args=args, env=env)

def _is_remote(server_config: dict) -> bool:
    return "url" in server_config

@asynccontextmanager
async def _open_session(server_config):
    if _is_remote(server_config):
        url = server_config["url"]
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        headers.update(server_config.get("headers") or {})
        async with httpx.AsyncClient(headers=headers) as client:
            async with streamable_http_client(url, http_client=client) as (read, write):
                async with ClientSession(read, write) as session:
                    yield session
    else:
        server = _build_server_params(server_config)
        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                yield session

async def _list_tools_async(server_config: dict) -> list[dict]:
    async with _open_session(server_config) as session:
        await session.initialize()
        tools_result = await session.list_tools()
        return [
            {
                "name": tool.name,
                "description": getattr(tool, "description", None),
                "inputSchema": getattr(
                    tool,
                    "inputSchema",
                    getattr(tool, "input_schema", None),
                ),
            }
            for tool in tools_result.tools
        ]

def list_tools(config: str) -> list[dict]:
    return asyncio.run(_list_tools_async(MCP_SERVERS[config]))

def get_mcp_list() -> list:
    result = []
    for server_name, server_config in MCP_SERVERS.items():
        result.append({
            'name': server_name,
            'description': server_config.get("description")
        })
    return result

async def _call_tool_async(
    server_config: dict,
    tool_name: str,
    arguments: dict | None = None,
) -> str:
    async with _open_session(server_config) as session:
        await session.initialize()
        result = await session.call_tool(
            tool_name,
            arguments=arguments or {},
        )
        text_parts = []
        for item in result.content:
            if hasattr(item, "text"):
                text_parts.append(item.text)
            else:
                text_parts.append(str(item))
        return "\n".join(text_parts)

def call_tool(
    config: str,
    tool_name: str,
    arguments: dict | None = None,
) -> str:
    server_config = MCP_SERVERS[config]
    return asyncio.run(_call_tool_async(server_config, tool_name, arguments or {}))