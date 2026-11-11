"""LLM API 调用封装 — 兼容 DeepSeek / 通义千问（OpenAI 协议）"""
import json
import httpx
from app.core.config import settings


class LLMClient:
    """异步 LLM 客户端，支持流式和非流式"""

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_API_BASE.rstrip("/")
        self.http_client = httpx.AsyncClient(timeout=60.0)

    async def chat(
        self,
        messages: list[dict],
        model: str = "deepseek-v4-flash",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> dict:
        """非流式调用，返回完整响应"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        response = await self.http_client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    async def chat_stream(
        self,
        messages: list[dict],
        model: str = "deepseek-v4-flash",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """流式调用，按行迭代（每行是完整的 UTF-8 字符串）"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        async with self.http_client.stream(
            "POST", url, json=payload, headers=headers
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    yield line

    async def close(self):
        await self.http_client.aclose()


_llm_client = None


def get_llm_client():
    """获取全局 LLM 客户端单例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def parse_stream_chunk(line: str):
    """解析一行 SSE 数据，提取 content delta。
    参数 line 必须是完整的一行（不含换行符），如：data: {"choices":[{"delta":{"content":"你好"}}]}
    """
    line = line.strip()
    if not line.startswith("data:"):
        return None
    data = line[5:].strip()
    if not data or data == "[DONE]":
        return None
    try:
        obj = json.loads(data)
        choices = obj.get("choices", [])
        if choices:
            delta = choices[0].get("delta", {})
            return delta.get("content")
    except (json.JSONDecodeError, KeyError, IndexError):
        return None
    return None
