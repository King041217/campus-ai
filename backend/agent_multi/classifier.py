"""分类 Agent — 将用户问题归类到 5 个校园领域之一"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings

CATEGORIES = ["course", "grade", "studyroom", "campus_life", "other"]

CATEGORY_DESCRIPTIONS = {
    "course": "课程相关（课程信息、课程内容、课程安排、教师、选课、教材、课件知识点等）",
    "grade": "成绩相关（考试成绩、绩点、成绩查询、分数统计、挂科等）",
    "studyroom": "自习室相关（自习室位置、空闲座位、开放时间、预约等）",
    "campus_life": "校园生活相关（校园公告、食堂、宿舍、社团、活动、校历、规章制度等）",
    "other": "其他（闲聊、问候、与技术/学习无关的问题等）",
}


CLASSIFIER_PROMPT = """你是一个校园问题分类专家。请将学生的问题归类为以下5个类别之一：

- course: 课程相关（课程信息、课程内容、课程安排、教师、选课、教材、课件知识点等）
- grade: 成绩相关（考试成绩、绩点、成绩查询、分数统计、挂科等）
- studyroom: 自习室相关（自习室位置、空闲座位、开放时间、预约等）
- campus_life: 校园生活相关（校园公告、食堂、宿舍、社团、活动、校历、规章制度等）
- other: 其他（闲聊、问候、与技术/学习无关的问题等）

请严格按以下 JSON 格式输出，不要输出其他内容：
{"category": "类别代码", "reasoning": "分类依据（一句话）"}

用户问题："""


def classify(question: str, user_role: str = "student") -> dict:
    """使用 LLM 对用户问题进行领域分类。"""
    llm = ChatOpenAI(
        model="deepseek-v4-flash",
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_API_BASE.rstrip("/"),
        temperature=0.1,
        max_tokens=256,
    )

    response = llm.invoke([
        SystemMessage(content="你是一个严谨的分类器。你必须只输出 JSON，不要有任何其他文字。"),
        HumanMessage(content=CLASSIFIER_PROMPT + question),
    ])

    raw = response.content.strip() if response.content else "{}"

    # 清洗可能的 markdown code fence
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        raw = "\n".join(lines).strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return {"category": "other", "reasoning": "JSON 解析失败，默认归类为 other"}

    category = result.get("category", "other")
    if category not in CATEGORIES:
        category = "other"

    return {"category": category, "reasoning": result.get("reasoning", "")}
