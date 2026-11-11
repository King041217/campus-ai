"""LangChain ChatModel 封装 — 兼容 DeepSeek / 通义千问（OpenAI 协议）"""
from langchain_openai import ChatOpenAI
from app.core.config import settings


def get_chat_model(
    model: str = "deepseek-v4-flash",
    temperature: float = 0.0,
    max_tokens: int = 2048,
    streaming: bool = True,
) -> ChatOpenAI:
    """创建 LangChain ChatOpenAI 实例，指向 DeepSeek API。

    deepseek-v4-flash / deepseek-reasoner 均兼容 OpenAI 协议，
    所以直接复用 langchain_openai.ChatOpenAI。
    """
    return ChatOpenAI(
        model=model,
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_API_BASE.rstrip("/"),
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
    )
