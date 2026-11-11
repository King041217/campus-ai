"""LangGraph 多智能体协作 StateGraph — 分类→检索→回复→质检 流水线"""
from typing import Literal
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END

from agent_multi.classifier import classify
from agent_multi.retriever import retrieve
from agent_multi.responder import respond
from agent_multi.quality import check_quality

MAX_RETRIES = 3
QUALITY_THRESHOLD = 60


class MultiAgentState(TypedDict):
    """多 Agent 共享状态，在节点间传递"""
    user_question: str
    category: str
    category_reasoning: str
    search_results: str
    final_response: str
    quality_score: int
    quality_passed: bool
    quality_feedback: str
    retry_count: int
    user_role: str
    user_name: str


def classifier_node(state: MultiAgentState) -> dict:
    """Node 1: 分类 — 判断问题属于哪个校园领域"""
    question = state["user_question"]
    result = classify(question, user_role=state.get("user_role", "student"))
    return {
        "category": result["category"],
        "category_reasoning": result["reasoning"],
    }


def retriever_node(state: MultiAgentState) -> dict:
    """Node 2: 检索 — 根据分类结果查询知识库/数据库"""
    category = state["category"]
    question = state["user_question"]
    results = retrieve(category, question, user_role=state.get("user_role", "student"))
    return {"search_results": results}


def responder_node(state: MultiAgentState) -> dict:
    """Node 3: 回复 — 基于检索结果生成自然语言回复"""
    question = state["user_question"]
    search_results = state["search_results"]
    feedback = state.get("quality_feedback", "")
    retry_count = state.get("retry_count", 0)

    if retry_count > 0 and feedback:
        response = respond(question, search_results, user_role=state.get("user_role", "student"), user_name=state.get("user_name", ""), quality_feedback=feedback)
    else:
        response = respond(question, search_results, user_role=state.get("user_role", "student"), user_name=state.get("user_name", ""))

    return {"final_response": response}


def quality_node(state: MultiAgentState) -> dict:
    """Node 4: 质检 — 检查回复质量，评分并给出反馈"""
    question = state["user_question"]
    response = state["final_response"]
    search_results = state["search_results"]
    retry_count = state.get("retry_count", 0)

    result = check_quality(question, response, search_results)
    return {
        "quality_score": result["score"],
        "quality_passed": result["passed"],
        "quality_feedback": result["feedback"],
        "retry_count": retry_count + 1,
    }


def should_retry(state: MultiAgentState) -> Literal["responder", "__end__"]:
    """条件路由：质检不通过且未超最大重试次数 → 重新生成回复"""
    passed = state.get("quality_passed", True)
    retries = state.get("retry_count", 0)

    if not passed and retries < MAX_RETRIES:
        return "responder"
    return "__end__"


# ===== 构建 StateGraph =====

graph_builder = StateGraph(MultiAgentState)

# 添加节点
graph_builder.add_node("classifier", classifier_node)
graph_builder.add_node("retriever", retriever_node)
graph_builder.add_node("responder", responder_node)
graph_builder.add_node("quality", quality_node)

# 设置入口
graph_builder.set_entry_point("classifier")

# 连线：分类 → 检索 → 回复 → 质检
graph_builder.add_edge("classifier", "retriever")
graph_builder.add_edge("retriever", "responder")
graph_builder.add_edge("responder", "quality")

# 条件边：质检不通过 → 回到回复节点重试；通过 → 结束
graph_builder.add_conditional_edges(
    "quality",
    should_retry,
    {
        "responder": "responder",
        "__end__": END,
    },
)

# 编译
compiled_multi_graph = graph_builder.compile()
