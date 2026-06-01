"""
工具注册中心 - 整合本地工具和外部 MCP 工具
"""

from typing import List
from langchain_core.tools import BaseTool
from utils.logger_handler import logger
import yaml
from utils.path_tool import get_abs_path

from agent.tools.agent_tools import (
    rag_summarize, get_decoding_accuracy, get_signal_quality,
    list_available_features, run_realtime_decoding, get_subject_id,
    get_current_month, fetch_external_data, fill_context_for_report,
    amap_poi_search, amap_walking_route, amap_driving_route
)


class ToolRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._local_tools: List[BaseTool] = []
        self._external_tools: List[BaseTool] = []
        self._load_local_tools()
        self._load_external_tools()

    def _load_local_tools(self):
        self._local_tools = [
            rag_summarize, get_decoding_accuracy, get_signal_quality,
            list_available_features, run_realtime_decoding, get_subject_id,
            get_current_month, fetch_external_data, fill_context_for_report,
            amap_poi_search, amap_walking_route, amap_driving_route
        ]
        logger.info(f"[ToolRegistry] 加载了 {len(self._local_tools)} 个本地工具")

    def _load_external_tools(self):
        try:
            config_path = get_abs_path("config/tools.yml")
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.info("[ToolRegistry] 未找到 config/tools.yml，跳过外部工具加载")
            return
        except Exception as e:
            logger.error(f"[ToolRegistry] 加载外部工具配置失败: {e}")
            return

        external_tools = config.get("external_tools", [])
        for tool_def in external_tools:
            if tool_def.get("type") == "mcp":
                self._register_mcp_service(tool_def)

    def _register_mcp_service(self, tool_def: dict):
        """注册MCP服务：自动发现所有工具并添加"""
        from agent.tools.mcp_client import MCPClient
        endpoint = tool_def.get("endpoint")
        service_name = tool_def.get("name", endpoint)  # 取 name 字段，没有则用 endpoint
        if not endpoint:
            logger.error(f"MCP服务 {service_name} 缺少 endpoint")
            return
        logger.info(f"[ToolRegistry] 正在注册 MCP 服务: {service_name}")
        try:
            client = MCPClient(endpoint)
            tools = client.to_langchain_tools()
            for tool in tools:
                self._external_tools.append(tool)
                logger.info(f"[ToolRegistry] 注册 MCP 工具: {tool.name} (来自服务 {service_name})")
        except Exception as e:
            logger.error(f"[ToolRegistry] 注册 MCP 服务 {service_name} 失败: {e}", exc_info=True)

    def get_all_tools(self) -> List[BaseTool]:
        return self._local_tools + self._external_tools


tool_registry = ToolRegistry()