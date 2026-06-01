#基于LangChain构建ReAct推理循环
'''
关键实现：

使用 from langchain.agents import create_agent 创建ReAct架构的Agent。

ReactAgent.__init__ 中调用 create_agent，传入模型、系统提示词、工具列表和中间件。

execute_stream 方法调用 self.agent.stream 实现流式推理，支持多步骤问答中的工具选择与执行顺序自主决策。

通过 stream_mode="values" 和 context 参数实现状态传递。
'''

#工具封装、注册、调用与中间件日志/异常处理
'''
关键实现：

react_agent.py 中将所有工具通过 tools 参数注册到 create_agent。
'''

#动态提示词切换（Function Calling + 多轮对话上下文管理）
'''
关键实现：

react_agent.py 的 execute_stream 中初始化 context={"report": False}，实现场景自适应的提示词切换。
'''

from langchain.agents import create_agent
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts
from agent.tools.agent_tools import (
    rag_summarize, get_decoding_accuracy, get_signal_quality,
    list_available_features, run_realtime_decoding, get_subject_id,
    get_current_month, fetch_external_data, fill_context_for_report
)
from agent.tools.middleware import monitor_tool, log_before_model, report_prompt_switch
from utils.conversation_db import get_messages, add_message
from utils.logger_handler import logger
from agent.tools.tool_registry import tool_registry


class ReactAgent:
    def __init__(self):
        # 从注册中心获取所有工具
        all_tools = tool_registry.get_all_tools()
        logger.info(f"[ReactAgent] 加载了 {len(all_tools)} 个工具: {[t.name for t in all_tools]}")
        self.agent = create_agent(
            model=chat_model,
            system_prompt=load_system_prompts(),
            tools=all_tools,   # 动态获取
            middleware=[monitor_tool, log_before_model, report_prompt_switch],
        )

        # 不再使用内存 self.memory，所有会话历史从数据库读取

    def execute_stream(self, query: str, conv_id: str, user_id: int):
        """
        执行流式推理，需要传入 user_id 以关联消息到特定用户
        """
        # 1. 从数据库加载历史消息（需要传入 user_id）
        history_messages = get_messages(conv_id, user_id)

        # 2. 构建 LangChain 消息列表
        messages = []
        for msg in history_messages:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": query})

        # 3. 添加用户消息到数据库（传入 user_id）
        add_message(conv_id, user_id, "user", query)

        input_dict = {"messages": messages}
        response_content = ""

        try:
            for chunk in self.agent.stream(input_dict, stream_mode="values", context={"report": False}):
                latest_message = chunk["messages"][-1]
                if latest_message.content:
                    content_piece = latest_message.content.strip()
                    response_content += content_piece
                    yield content_piece + "\n"
        except Exception as e:
            logger.error(f"Agent 执行出错: {e}")
            yield f"出错: {str(e)}"
            return

        # 5. 将助手回复保存到数据库（传入 user_id）
        if response_content:
            add_message(conv_id, user_id, "assistant", response_content)

if __name__ == '__main__':
    agent = ReactAgent()

    for chunk in agent.execute_stream("给我生成我的使用报告"):
        print(chunk, end="", flush=True)