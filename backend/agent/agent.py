"""CampusAgent — 校园助手智能体封装"""
import json
from typing import AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage
from agent.graph import compiled_graph, _build_llm


class CampusAgent:
    """校园 AI 助手 Agent，封装 LangGraph 编译后的图的调用"""

    def __init__(self):
        self.graph = compiled_graph

    def run(self, user_input: str, history: list[dict] | None = None, user_id: int = 0) -> str:
        """同步非流式调用 Agent。

        Args:
            user_input: 用户输入文本
            history: 历史消息列表 [{"role": "user/assistant", "content": "..."}]
        """
        messages = _build_messages(user_input, history)
        result = self.graph.invoke({"messages": messages})
        last = result["messages"][-1]
        return last.content if last.content else ""

    async def astream(
        self, user_input: str, history: list[dict] | None = None
    ) -> AsyncGenerator[str, None]:
        """异步流式调用 Agent（使用 LLM 流式输出）。

        不对图本身做流式，而是在最后一步 chatbot 回复时使用流式 LLM。
        做法：先用非流式走到 chatbot 返回 tool_calls 或最终回复，然后对最终回复做流式输出。
        """
        messages = _build_messages(user_input, history)

        # 1. 先用非流式图拿到完整结果（包含可能的 tool_calls 循环）
        result = self.graph.invoke({"messages": messages})
        final_message = result["messages"][-1]

        # 2. 如果最后一条是 AI 文本回复，用流式 LLM 重新生成以支持流式输出
        if isinstance(final_message, AIMessage):
            # 用原始消息列表 + 最后的 tool 交互结果，让 LLM 流式生成最终回复
            llm = _build_llm()
            stream = llm.astream(result["messages"])
            async for chunk in stream:
                if chunk.content:
                    yield chunk.content
        elif final_message.content:
            yield final_message.content


def _build_messages(
    user_input: str, history: list[dict] | None
) -> list:
    """将历史和用户输入构建为 LangChain Message 列表"""
    messages = []
    if history:
        for h in history[-20:]:  # 限制上下文
            role = h.get("role", "")
            content = h.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=user_input))
    return messages
