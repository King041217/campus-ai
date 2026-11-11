# -*- coding: utf-8 -*-
"""检索 Agent —— 根据分类结果查询对应的知识库或数据库"""
from agent.tools import query_course, query_grade, query_study_room, query_announcement
from app.core.database import SessionLocal
from app.models.user import User


def _find_student_by_name(name):
    try:
        db = SessionLocal()
        student = db.query(User).filter(
            User.full_name.contains(name), User.role == "student"
        ).first()
        db.close()
        return student
    except Exception:
        return None


def _extract_student_from_question(question):
    import re

    # 方法1: 数据库姓名列表匹配（最可靠，不会受正则影响）
    try:
        db = SessionLocal()
        rows = db.query(User.full_name, User.id).filter(User.role == "student").all()
        db.close()
        for name, sid in sorted(rows, key=lambda x: -len(x[0])):
            if len(name) >= 2 and name in question:
                return sid, name
    except Exception:
        pass

    # 方法2: 正则兜底
    patterns = [
        r"(?:查|查询|查一下|帮我查|看看)(.{2,4}?)(?:的?成绩|多少分|怎么样)",
        r"(.{2,4}?)(?:的?成绩)(?:多少|怎么样|如何|是多少)",
        r"学号\s*(\d+)",
        r"(\d+)号",
    ]
    for p in patterns:
        m = re.search(p, question)
        if m:
            hint = m.group(1) or ""
            hint = re.sub(r"[的之]", "", hint).strip()
            if hint.isdigit():
                return int(hint), hint
            if len(hint) >= 2:
                student = _find_student_by_name(hint)
                if student:
                    return student.id, hint
            break

    return None, ""


def retrieve(category, question, user_role="student"):
    results = []
    try:
        if category == "course":
            r = query_course.invoke({"course_name": question})
            if r and "not found" not in r.lower():
                results.append(f"数据库课程信息\n{r}")
            try:
                from rag.retriever import retrieve_docs
                docs = retrieve_docs(question, k=3)
                if docs:
                    t = "\n\n".join(
                        f"来源: {d.metadata.get('source', '未知')}\n{d.page_content}"
                        for d in docs
                    )
                    results.append(f"课件知识库检索\n{t}")
            except Exception:
                pass

        elif category == "grade":
            if user_role in ("teacher", "admin", "decision_maker"):
                student_id, hint = _extract_student_from_question(question)
                if student_id is not None and hint:
                    r = query_grade.invoke({"student_id": student_id})
                    results.append(f"学生 {hint} 的成绩\n{r}")
                else:
                    results.append(
                        "未在系统中找到对应学生。"
                        "请直接说出学生姓名（如查张三成绩），或先说清楚要查哪位同学的成绩。"
                    )
            else:
                r = query_grade.invoke({"student_id": None})
                results.append(f"成绩查询结果\n{r}")

        elif category == "studyroom":
            r = query_study_room.invoke({})
            if r:
                results.append(f"自习室信息\n{r}")

        elif category == "campus_life":
            r = query_announcement.invoke({"limit": 5})
            if r and "not found" not in r:
                results.append(f"最新公告\n{r}")
            try:
                from rag.retriever import retrieve_docs
                docs = retrieve_docs(question, k=3)
                if docs:
                    t = "\n\n".join(
                        f"来源: {d.metadata.get('source', '未知')}\n{d.page_content}"
                        for d in docs
                    )
                    results.append(f"课件知识库检索\n{t}")
            except Exception:
                pass

        else:  # other
            try:
                from rag.retriever import retrieve_docs
                docs = retrieve_docs(question, k=3)
                if docs:
                    t = "\n\n".join(
                        f"来源: {d.metadata.get('source', '未知')}\n{d.page_content}"
                        for d in docs
                    )
                    results.append(f"课件知识库检索\n{t}")
            except Exception:
                pass

    except Exception as e:
        return f"检索过程出现错误：{str(e)}"

    if not results:
        return "暂无相关检索结果。"

    return "\n\n---\n\n".join(results)
