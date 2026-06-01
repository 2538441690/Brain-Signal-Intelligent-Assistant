import asyncio
import concurrent.futures
from typing import List, Dict, Any
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from langchain_core.tools import BaseTool, StructuredTool
from utils.logger_handler import logger


class MCPClient:
    """管理一个 MCP 服务，自动发现并创建工具"""
    def __init__(self, server_url: str):
        self.server_url = server_url

    async def _list_tools(self) -> List[Dict[str, Any]]:
        async with streamablehttp_client(self.server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                tools = []
                for tool in result.tools:
                    logger.info(f"[MCP] 发现工具: {tool.name}, 描述: {tool.description}")
                    tools.append({
                        "name": tool.name,
                        "description": tool.description or "",
                        "input_schema": tool.inputSchema
                    })
                return tools

    def list_tools(self) -> List[Dict[str, Any]]:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, self._list_tools())
            return future.result()

    def to_langchain_tools(self) -> List[BaseTool]:
        tool_defs = self.list_tools()
        langchain_tools = []
        for tool_def in tool_defs:
            tool = MCPToolInstance(
                name=tool_def["name"],
                description=tool_def["description"],
                server_url=self.server_url,
                input_schema=tool_def.get("input_schema")
            )
            langchain_tools.append(tool.to_langchain_tool())
        return langchain_tools


class MCPToolInstance:
    """单个 MCP 工具的封装"""
    def __init__(self, name: str, description: str, server_url: str, input_schema: dict = None):
        self.name = name
        self.description = description
        self.server_url = server_url
        self.input_schema = input_schema

    async def _arun(self, **kwargs) -> str:
        try:
            async with streamablehttp_client(self.server_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(self.name, arguments=kwargs)
                    if result.content and len(result.content) > 0:
                        # 直接返回原始文本，不做任何额外解析
                        return result.content[0].text
                    return str(result)
        except Exception as e:
            logger.error(f"MCP工具 '{self.name}' 调用失败: {e}")
            return f"工具 '{self.name}' 调用失败: {e}"

    def _run(self, **kwargs) -> str:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, self._arun(**kwargs))
            return future.result()

    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(
            func=self._run,
            coroutine=self._arun,
            name=self.name,
            description=self.description,
            args_schema=self.input_schema
        )