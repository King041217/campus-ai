"""Agent 聊天 API - POST /api/agent/chat（SSE 流式 + 非流式）"""
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.core.dependencies import get_current_user
from app.models.user import User
from agent.agent import CampusAgent
from agent.tools import set_user_context
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

router = APIRouter(prefix="/api/agent", tags=["Agent智能体"])

_agent = CampusAgent()

# Server-side session memory
session_store: dict[int, list] = {}

SYSTEM_PROMPT = (
    "你是校园AI智能助手。你可以调用以下工具获取真实数据：\n"
    "1. query_course(course_name) - 查询课程信息\n"
    "2. query_grade(student_id) - 查询成绩（学生查自己，教师/管理员需先用 lookup_student 查学号）\n"
    "3. lookup_student(name) - 根据姓名查找学生学号（教师/管理员用）\n"
    "4. query_study_room() - 查询自习室空闲情况\n"
    "5. query_announcement(limit) - 查询校园公告\n"
    "重要规则：\n"
    "- 学生说「我的成绩」「查成绩」→ 调用 query_grade() 不传参数\n"
    "- 教师/管理员说「查成绩」→ 先问查哪个学生，不要说「查我的成绩」\n"
    "- 教师/管理员说「查XX的成绩」→ 先调 lookup_student(name=\"XX\") 再调 query_grade(student_id=学号)\n"
    "- 管理员/教师本身没有成绩数据，不要尝试查自己的成绩\n"
    "- 先调用工具获取数据，再根据数据回复用户\n"
    "- 回复简洁清晰，用中文"
)


class AgentChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    history: list[dict] = Field(default_factory=list, description="历史消息")
    stream: bool = Field(default=True, description="是否流式返回")


class AgentChatResponse(BaseModel):
    reply: str


@router.post("/chat")
async def agent_chat(
    req: AgentChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Agent 智能体对话接口"""
    # Set user context for tool permission checks
    set_user_context(current_user.id, current_user.username, current_user.role)

    if req.stream:
        return StreamingResponse(
            _agent_stream_generator(_agent, req.message, req.history, current_user),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    try:
        messages = _build_messages_with_session(current_user, req.message, req.history)
        result = _agent.graph.invoke({"messages": messages})
        reply = result["messages"][-1].content or ""
        if current_user.id not in session_store:
            session_store[current_user.id] = messages.copy()
        session_store[current_user.id].append(result["messages"][-1])
        return AgentChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 调用失败: {str(e)}")


async def _agent_stream_generator(agent: CampusAgent, message: str, history: list[dict], current_user: User):
    """SSE 流式生成器，带服务端会话记忆"""
    try:
        messages = _build_messages_with_session(current_user, message, history)
        result = agent.graph.invoke({"messages": messages})
        full_content = result["messages"][-1].content or ""

        # Save to session
        uid = current_user.id
        if uid not in session_store:
            session_store[uid] = messages.copy()
        session_store[uid].append(result["messages"][-1])

        # Simulate streaming by chunking
        chunk_size = 5
        for i in range(0, len(full_content), chunk_size):
            chunk = full_content[i:i + chunk_size]
            yield f"data: {json.dumps({'delta': chunk}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'delta': '', 'done': True, 'full_content': full_content}, ensure_ascii=False)}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"


def _build_messages_with_session(current_user: User, user_input: str, history: list[dict] | None) -> list:
    """Build LangChain messages with server-side session memory"""
    user_id = current_user.id
    role_labels = {"student": "学生", "teacher": "教师", "admin": "管理员", "decision_maker": "决策者"}
    role_label = role_labels.get(current_user.role, current_user.role)
    name = current_user.full_name or current_user.username
    user_info = f"当前对话用户：{name}（{role_label}，用户ID: {user_id}）。学生查成绩时只能查自己的，教师/管理员可查任意学生。"
    # Init session with system prompt
    if user_id not in session_store:
        session_store[user_id] = [SystemMessage(content=SYSTEM_PROMPT + "\n\n" + user_info)]

    msgs = session_store[user_id]
    existing_user_msgs = {m.content for m in msgs if isinstance(m, HumanMessage)}

    if history:
        for h in history[-20:]:
            role = h.get("role", "")
            c = h.get("content", "")
            if role == "user" and c not in existing_user_msgs:
                msg = HumanMessage(content=c)
                msgs.append(msg)
                existing_user_msgs.add(c)
            elif role == "assistant":
                msgs.append(AIMessage(content=c))

    # Append current user message
    if user_input not in existing_user_msgs:
        msgs.append(HumanMessage(content=user_input))

    # Trim: keep system prompt + last 20 messages
    if len(msgs) > 22:
        msgs[1:-20] = []

    return msgs


def _build_messages(user_input: str, history: list[dict] | None) -> list:
    """构建 LangChain Message 列表（无会话场景）"""
    messages = []
    if history:
        for h in history[-20:]:
            role = h.get("role", "")
            content = h.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=user_input))
    return messages
