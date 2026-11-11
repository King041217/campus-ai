"""Agent 工具函数"""
from langchain.tools import tool
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.course import Course
from app.models.grade import Grade
from app.models.study_room import StudyRoom
from app.models.announcement import Announcement

# Current user context, set by router before each request
_current_user_id: int = 0
_current_user_name: str = ""
_current_user_role: str = "student"


def set_user_context(user_id: int, username: str, role: str):
    global _current_user_id, _current_user_name, _current_user_role
    _current_user_id = user_id
    _current_user_name = username
    _current_user_role = role


def _get_db() -> Session:
    return SessionLocal()


@tool
def query_course(course_name: str) -> str:
    """根据课程名称查询课程详细信息，包括授课教师、上课时间和地点。

    Args:
        course_name: 要查询的课程名称（支持模糊匹配）
    """
    db = _get_db()
    try:
        courses = db.query(Course).filter(
            Course.name.ilike(f"%{course_name}%")
        ).all()
        if not courses:
            return f"未找到与{course_name}相关的课程信息。"

        results = []
        for c in courses:
            info = f"- 课程名称: {c.name}\n"
            info += f"  课程代码: {c.code}\n"
            info += f"  授课教师: {c.teacher or '待定'}\n"
            info += f"  学分: {c.credits}\n"
            info += f"  上课安排: {c.schedule or '待定'}\n"
            info += f"  课程简介: {c.description or '暂无'}"
            results.append(info)

        return f"查询到 {len(results)} 门与{course_name}相关的课程：\n\n" + "\n\n".join(results)
    finally:
        db.close()


@tool
def query_grade(student_id: int | None = None) -> str:
    """根据学号查询学生的各科成绩。不提供学号则查自己。
    学生只能看自己的成绩，教师/管理员可查任意学生。

    Args:
        student_id: 学生ID（学号），留空则查自己的
    """
    if _current_user_role not in ("student",) and student_id is None:
        return "您是教师/管理员，请指定要查询的学生姓名，或先调用 lookup_student 工具查找学号。例如：lookup_student(name=\"张三\")。"
    if _current_user_role == "student":
        if student_id is not None and student_id != _current_user_id:
            return "权限不足：学生只能查看自己的成绩。请使用【查询我的成绩】。"
        student_id = _current_user_id
    elif student_id is None:
        student_id = _current_user_id

    db = _get_db()
    try:
        grades = db.query(Grade).filter(Grade.student_id == student_id).all()
        if not grades:
            return f"未找到学号为 {student_id} 的成绩记录。"

        results = []
        total = 0.0
        for g in grades:
            results.append(f"- {g.course_name}: {g.score}分 ({g.term or '未知学期'})")
            total += g.score

        avg = total / len(grades) if grades else 0
        return (
            f"学号 {student_id} 的成绩汇总（共 {len(grades)} 门课，平均分 {avg:.1f}）：\n\n"
            + "\n".join(results)
        )
    finally:
        db.close()


@tool
def query_study_room() -> str:
    """查询当前校园内所有自习室的空闲座位情况，包括位置和可用座位数。"""
    db = _get_db()
    try:
        rooms = db.query(StudyRoom).all()
        if not rooms:
            return "暂无自习室数据。"

        results = []
        total_avail = 0
        for r in rooms:
            status = "开放" if r.is_open else "关闭"
            avail = r.available
            total_avail += avail if r.is_open else 0
            results.append(
                f"- {r.name}（{r.location or '位置未标注'}）\n"
                f"  状态: {status} | 总座位: {r.capacity} | 空闲: {avail} | 已占用: {r.occupied}"
            )

        return f"校园自习室实时情况（开放自习室共 {total_avail} 个空闲座位）：\n\n" + "\n\n".join(results)
    finally:
        db.close()


@tool
def query_announcement(limit: int = 5) -> str:
    """查询最新的校园公告通知。

    Args:
        limit: 返回的公告条数，默认5条
    """
    db = _get_db()
    try:
        announcements = (
            db.query(Announcement)
            .order_by(Announcement.created_at.desc())
            .limit(limit)
            .all()
        )
        if not announcements:
            return "暂无校园公告。"

        results = []
        for a in announcements:
            priority_label = {"normal": "普通", "important": "重要", "urgent": "紧急"}.get(
                a.priority, a.priority
            )
            results.append(
                f"- [{priority_label}] {a.title}\n"
                f"  发布者: {a.author or '未知'} | 内容: {a.content or '暂无详情'}"
            )

        return f"最新校园公告（共 {len(results)} 条）：\n\n" + "\n\n".join(results)
    finally:
        db.close()


ALL_TOOLS = [query_course, query_grade, query_study_room, query_announcement]

@tool
def lookup_student(name: str) -> str:
    """根据学生姓名查找学号。教师和管理员查成绩前需先调用此工具获取学号。

    Args:
        name: 学生姓名（支持模糊匹配）
    """
    db = _get_db()
    try:
        students = db.query(User).filter(
            (User.full_name == name) | (User.full_name.contains(name)),
            User.role == "student"
        ).all()
        if not students:
            return f"未找到姓名为\"{name}\"的学生。请确认姓名是否正确。"
        result = "找到以下学生：\n"
        for s in students:
            result += f"- {s.full_name}，学号: {s.id}\n"
        return result
    finally:
        db.close()


from app.models.user import User
ALL_TOOLS = [query_course, query_grade, query_study_room, query_announcement, lookup_student]
