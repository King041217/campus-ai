"""TTS 文字转语音服务 — 后端预处理 + 浏览器 SpeechSynthesis 播放

策略：浏览器内置 Web Speech API 直接在前端完成语音合成，本服务提供：
1. 长文本智能分段（适配浏览器 TTS 限制）
2. 音色风格管理
3. 校园场景化语音模板
"""
import re
from pydantic import BaseModel


# === 音色风格定义 ===

VOICE_STYLES = {
    "formal": {
        "name": "正式播报",
        "rate": 0.9,
        "pitch": 1.0,
        "desc": "适合课程通知、成绩公告等正式场景",
    },
    "friendly": {
        "name": "亲切关怀",
        "rate": 1.0,
        "pitch": 1.1,
        "desc": "适合校园生活、学伴交流等互动场景",
    },
    "lively": {
        "name": "活泼生动",
        "rate": 1.15,
        "pitch": 1.2,
        "desc": "适合活动宣传、趣味通知等场景",
    },
}

# === 文本分段配置 ===

MAX_CHUNK_CHARS = 800          # 浏览器 SpeechSynthesis 建议上限
CHUNK_BREAK_PATTERN = re.compile(r"(?<=[。！？\n])(?=[^。！？\n])")


class TTSChunk(BaseModel):
    index: int
    text: str
    char_count: int


class TTSSegmentResult(BaseModel):
    style: str
    rate: float
    pitch: float
    total_chars: int
    chunks: list[TTSChunk]


def segment_text(text: str, style: str = "friendly") -> TTSSegmentResult:
    """将长文本按标点/换行智能分段，适配浏览器 TTS 限制。

    分段规则：
    1. 优先在句号、问号、感叹号、换行处切分
    2. 每段不超过 MAX_CHUNK_CHARS
    3. 如果一句话超过上限，按逗号/分号再次切分
    """
    voice_cfg = VOICE_STYLES.get(style, VOICE_STYLES["friendly"])
    raw_chunks = _split_by_markers(text)
    chunks: list[TTSChunk] = []
    idx = 0
    for raw in raw_chunks:
        sub_parts = _force_split(raw, MAX_CHUNK_CHARS)
        for part in sub_parts:
            cleaned = part.strip()
            if not cleaned:
                continue
            idx += 1
            chunks.append(TTSChunk(index=idx, text=cleaned, char_count=len(cleaned)))
    return TTSSegmentResult(
        style=style,
        rate=voice_cfg["rate"],
        pitch=voice_cfg["pitch"],
        total_chars=sum(c.char_count for c in chunks),
        chunks=chunks,
    )


def _split_by_markers(text: str) -> list[str]:
    """按主要标点符号切分文本"""
    parts = CHUNK_BREAK_PATTERN.split(text)
    return [p for p in parts if p.strip()]


def _force_split(text: str, max_len: int) -> list[str]:
    """对超长段落，按逗号/分号/空格再次切分"""
    if len(text) <= max_len:
        return [text]
    result = []
    current = ""
    sentences = re.split(r"(?<=[，；；,;])", text)
    for s in sentences:
        if len(current) + len(s) <= max_len:
            current += s
        else:
            if current:
                result.append(current)
            # 如果单句还超长，硬切
            if len(s) > max_len:
                for i in range(0, len(s), max_len):
                    result.append(s[i : i + max_len])
                current = ""
            else:
                current = s
    if current:
        result.append(current)
    return result


def list_voice_styles():
    """列出所有可用音色风格"""
    return {
        "styles": [
            {"key": k, **v} for k, v in VOICE_STYLES.items()
        ]
    }
