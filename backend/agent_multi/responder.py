"""回复 Agent — 基于检索结果生成专业友好的自然语言回复"""
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings

RESPONDER_SYSTEM_PROMPT = (
    "你是校园AI学伴助手。请根据检索结果回答学生的问题。\n"
    "规则：1) 优先基于检索结果回答，数据库查询结果优先于课件检索结果；"
    "2) 检索结果不足时如实告知；3) 不编造数据；4) 回复友好简洁；5) 中文回答。\n"
    "输出格式：先直接回答问题，然后用要点列出关键信息，最后可附建议。"
)


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="deepseek-v4-flash",
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_API_BASE.rstrip("/"),
        temperature=0.7,
        max_tokens=1024,
    )


def respond(question: str, search_results: str, user_role: str = "student", user_name: str = "", quality_feedback: str = "") -> str:
    """根据检索结果生成回复。"""
    llm = _build_llm()
    role_info = f"\u5f53\u524d\u7528\u6237\u89d2\u8272\uff1a{user_role}\uff0c\u59d3\u540d\uff1a{user_name or '\u672a\u77e5'}"
    if user_role in ("teacher", "admin"):
        role_info += "\n\u4f60\u662f\u6559\u5e08/\u7ba1\u7406\u5458\uff0c\u53ef\u4ee5\u67e5\u8be2\u6240\u6709\u5b66\u751f\u7684\u4fe1\u606f\u3002"
    elif user_role == "decision_maker":
        role_info += "\n\u4f60\u662f\u51b3\u7b56\u8005\uff0c\u53ef\u4ee5\u67e5\u770b\u5b66\u60c5\u5206\u6790\u6570\u636e\u3002"
    else:
        role_info += "\n\u4f60\u662f\u5b66\u751f\uff0c\u53ea\u80fd\u67e5\u770b\u81ea\u5df1\u7684\u4fe1\u606f\u3002"
    user_prompt = f"\u3010\u7528\u6237\u4fe1\u606f\u3011\n{role_info}\n\n\u3010\u5b66\u751f\u95ee\u9898\u3011\n{question}\n\n\u3010\u68c0\u7d22\u7ed3\u679c\u3011\n{search_results}"
    if quality_feedback:
        user_prompt += f"\n\n【上一轮质检反馈】\n{quality_feedback}"
    response = llm.invoke([
        SystemMessage(content=RESPONDER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])
    return response.content if response.content else "抱歉，回复生成失败。"
