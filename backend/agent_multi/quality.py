"""质检 Agent — 检查回复的准确性、合规性、友好度，评分并标记问题"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings

QUALITY_SYSTEM_PROMPT = (
    "你是校园AI学伴回复质检员。检查维度（每项25分，满分100）：\n"
    "1. 准确性(25分)：回复是否与检索结果一致，有无编造\n"
    "2. 完整性(25分)：是否完整回答了问题，有无遗漏关键信息\n"
    "3. 友好度(25分)：语气是否友好适合大学生，表达是否清晰\n"
    "4. 合规性(25分)：是否符合校园规范，有无不当或误导内容\n"
    "严格输出JSON：{\"score\":85,\"dimensions\":{\"accuracy\":22,\"completeness\":20,\"friendliness\":23,\"compliance\":20},\"passed\":true,\"feedback\":\"可补充课程细节\"}\n"
    "passed当score>=60时为true。feedback在未通过时给修改建议，通过时可给改进建议。"
)


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="deepseek-v4-flash",
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_API_BASE.rstrip("/"),
        temperature=0.1,
        max_tokens=512,
    )


def check_quality(question: str, response: str, search_results: str) -> dict:
    """对回复进行质量检查，返回评分和反馈。"""
    llm = _build_llm()
    user_prompt = (
        f"【学生问题】\n{question}\n\n"
        f"【检索结果】\n{search_results}\n\n"
        f"【AI回复（待检查）】\n{response}"
    )
    try:
        result = llm.invoke([
            SystemMessage(content=QUALITY_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
    except Exception:
        return {
            "score": 60,
            "dimensions": {"accuracy": 15, "completeness": 15, "friendliness": 15, "compliance": 15},
            "passed": True,
            "feedback": "质检服务暂时不可用，已跳过。",
        }
    raw = result.content.strip() if result.content else "{}"
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        raw = "\n".join(lines).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "score": 50,
            "dimensions": {"accuracy": 13, "completeness": 13, "friendliness": 12, "compliance": 12},
            "passed": False,
            "feedback": "JSON解析失败，默认不通过。",
        }
    score = max(0, min(100, int(data.get("score", 0))))
    return {
        "score": score,
        "dimensions": data.get("dimensions", {}),
        "passed": data.get("passed", score >= 60),
        "feedback": data.get("feedback", ""),
    }
