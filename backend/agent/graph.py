"""LangGraph StateGraph — Agent 核心状态图"""
from typing import Annotated, Literal
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from agent.tools import ALL_TOOLS


class AgentState(TypedDict):
    """Agent 状态：messages 列表会通过 add_messages 自动合并"""
    messages: Annotated[list[BaseMessage], add_messages]


def _build_llm() -> ChatOpenAI:
    """创建绑定工具的 ChatOpenAI 实例"""
    llm = ChatOpenAI(
        model="deepseek-v4-flash",
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_API_BASE.rstrip("/"),
        temperature=0.7,
        max_tokens=2048,
    )
    return llm.bind_tools(ALL_TOOLS)


def chatbot(state: AgentState) -> dict:
    """LLM 推理节点：调用模型并返回 AI 消息（可能包含 tool_calls）"""
    llm = _build_llm()
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """条件路由：检查最后一条消息是否有 tool_calls"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "__end__"


# 构建 StateGraph
_tool_node = ToolNode(ALL_TOOLS)

graph_builder = StateGraph(AgentState)

# 添加节点
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", _tool_node)

# 设置入口
graph_builder.set_entry_point("chatbot")

# 条件边：chatbot → tools 或 END
graph_builder.add_conditional_edges(
    "chatbot",
    should_continue,
    {"tools": "tools", "__end__": END},
)

# 工具执行后回到 chatbot 继续推理
graph_builder.add_edge("tools", "chatbot")

# 编译
compiled_graph = graph_builder.compile()
