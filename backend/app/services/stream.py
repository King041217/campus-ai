"""SSE 流式响应封装"""
import json
from app.services.llm import get_llm_client, parse_stream_chunk


async def sse_chat_generator(messages: list[dict]):
    """将 LLM 流式响应转换为 SSE 事件流。
    chat_stream 现在返回字符串行（每行都是完整的 SSE 数据），
    用 parse_stream_chunk 解析后包装成前端期待的 data: {...} 格式。
    """
    client = get_llm_client()
    full_content = ""
    try:
        async for line in client.chat_stream(messages=messages):
            content = parse_stream_chunk(line)
            if content is not None:
                full_content += content
                yield f"data: {json.dumps({'delta': content}, ensure_ascii=False)}\n\n"
        # 发送结束信号
        yield f"data: {json.dumps({'delta': '', 'done': True, 'full_content': full_content}, ensure_ascii=False)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
