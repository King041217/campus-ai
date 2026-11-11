"""STT 语音识别服务 — 热词管理 + 浏览器 SpeechRecognition 辅助

策略：浏览器 Web Speech Recognition API 直接在前端完成语音识别，本服务提供：
1. 校园场景热词表管理（提升识别准确率）
2. 课程名/教学楼/术语等专业词汇维护
"""

# === 校园热词表 ===
# 按场景分类，前端 SpeechRecognition 可通过 grammar 方式注入

CAMPUS_HOT_WORDS = {
    "courses": [
        "Python编程基础", "数据库原理", "数据结构", "操作系统",
        "计算机网络", "人工智能导论", "软件工程", "高等数学",
        "线性代数", "大学英语", "思想政治", "体育",
    ],
    "buildings": [
        "教学楼", "图书馆", "实验楼", "行政楼", "体育馆",
        "食堂", "宿舍楼", "校医院", "大学生活动中心",
    ],
    "offices": [
        "教务处", "学生处", "财务处", "招生办", "就业指导中心",
        "团委", "学生会", "心理咨询中心",
    ],
    "terms": [
        "学分", "绩点", "重修", "补考", "选课",
        "退课", "奖学金", "助学金", "实习", "毕业论文",
        "答辩", "毕业典礼", "迎新", "社团", "志愿者",
    ],
}


def get_hot_words(category: str = None):
    """获取热词表，可按分类筛选"""
    if category and category in CAMPUS_HOT_WORDS:
        return {"category": category, "words": CAMPUS_HOT_WORDS[category]}
    all_words = set()
    for words in CAMPUS_HOT_WORDS.values():
        all_words.update(words)
    return {"category": "all", "words": sorted(all_words)}


def list_categories():
    """列出热词分类"""
    return {
        "categories": [
            {"key": k, "label": lab, "count": len(v)}
            for k, v, lab in [
                ("courses", CAMPUS_HOT_WORDS["courses"], "课程名称"),
                ("buildings", CAMPUS_HOT_WORDS["buildings"], "教学楼宇"),
                ("offices", CAMPUS_HOT_WORDS["offices"], "行政部门"),
                ("terms", CAMPUS_HOT_WORDS["terms"], "常用术语"),
            ]
        ]
    }


def add_hot_word(category: str, word: str):
    """向指定分类添加热词"""
    if category not in CAMPUS_HOT_WORDS:
        return {"success": False, "message": f"未知分类: {category}"}
    if word in CAMPUS_HOT_WORDS[category]:
        return {"success": False, "message": f"热词已存在: {word}"}
    CAMPUS_HOT_WORDS[category].append(word)
    return {"success": True, "message": f"已添加热词: {word} -> {category}"}
