"""通义万相文生图服务 — DashScope API 封装

调用阿里云 DashScope text2image API，支持：
- 文本生成图片（通义万相 2.1）
- 风格/尺寸/反向提示词参数
- 校园场景：教学插图、活动海报、知识图谱
"""
import httpx
import base64
from pydantic import BaseModel, Field
from app.core.config import settings


class ImageGenRequest(BaseModel):
    prompt: str = Field(..., description="正向提示词，描述要生成的图像")
    negative_prompt: str = Field(
        default="low quality, blurry, watermark, text, signature, distorted, ugly, bad anatomy",
        description="反向提示词"
    )
    style: str = Field(default="default", description="风格: default/photograph/anime/sketch/3d")
    size: str = Field(default="1024x1024", description="尺寸: 1024x1024 / 720x1280 / 1280x720")
    n: int = Field(default=1, ge=1, le=4, description="生成数量")


class ImageGenResult(BaseModel):
    success: bool
    images: list[str] = []     # base64 编码的图片
    message: str = ""


class ImageGenClient:
    """通义万相文生图客户端"""

    DASHSCOPE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.QWEN_API_KEY
        self.http = httpx.AsyncClient(timeout=120.0)

    async def generate(self, req: ImageGenRequest) -> ImageGenResult:
        """调用通义万相生成图片"""
        if not self.api_key:
            return ImageGenResult(
                success=False,
                message="未配置 QWEN_API_KEY（DashScope API Key），请在 .env 中设置"
            )

        payload = {
            "model": "wanx2.1-t2i-turbo",
            "input": {
                "prompt": req.prompt,
                "negative_prompt": req.negative_prompt,
            },
            "parameters": {
                "style": req.style,
                "size": req.size,
                "n": req.n,
            },
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }

        try:
            response = await self.http.post(self.DASHSCOPE_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data.get("output", {}).get("task_status") == "FAILED":
                err_msg = data.get("output", {}).get("message", "未知错误")
                return ImageGenResult(success=False, message=f"生成失败: {err_msg}")

            task_id = data.get("output", {}).get("task_id")
            if not task_id:
                return ImageGenResult(success=False, message="未获取到 task_id，响应异常")

            # 轮询等待异步任务完成
            result = await self._poll_task(task_id)
            return result

        except httpx.HTTPStatusError as e:
            return ImageGenResult(success=False, message=f"API 请求失败 (HTTP {e.response.status_code})")
        except Exception as e:
            return ImageGenResult(success=False, message=f"请求异常: {str(e)}")

    async def _poll_task(self, task_id: str, max_retries: int = 30, interval: float = 2.0) -> ImageGenResult:
        """轮询异步任务状态，直到完成或超时"""
        import asyncio
        headers = {"Authorization": f"Bearer {self.api_key}"}
        task_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

        for _ in range(max_retries):
            await asyncio.sleep(interval)
            resp = await self.http.get(task_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("output", {}).get("task_status")

            if status == "SUCCEEDED":
                results = data.get("output", {}).get("results", [])
                images = [r.get("url", "") for r in results if r.get("url")]
                return ImageGenResult(success=True, images=images, message="生成成功")
            elif status == "FAILED":
                return ImageGenResult(
                    success=False,
                    message=data.get("output", {}).get("message", "任务失败"),
                )
            # 其他状态（PENDING/RUNNING）继续轮询

        return ImageGenResult(success=False, message="任务超时，请稍后重试")

    async def close(self):
        await self.http.aclose()


# === 校园场景提示词模板 ===

SCENE_TEMPLATES = {
    "teaching_illustration": {
        "name": "教学插图",
        "prompt": "教育风格插画，简洁清晰的知识点示意，温暖明亮的配色，适合课堂展示",
        "style": "sketch",
    },
    "event_poster": {
        "name": "活动海报",
        "prompt": "校园活动宣传海报风格，活力配色，现代设计感，吸引学生注意",
        "style": "default",
    },
    "knowledge_graph": {
        "name": "知识图谱",
        "prompt": "结构化知识可视化，清晰的层级关系，学术风格，蓝白配色",
        "style": "sketch",
    },
    "campus_scenery": {
        "name": "校园风景",
        "prompt": "美丽的大学校园景色，温馨自然光线，写实摄影风格",
        "style": "photograph",
    },
}


def get_scene_templates():
    """获取校园场景提示词模板"""
    return {"templates": [{"key": k, **v} for k, v in SCENE_TEMPLATES.items()]}


_image_gen_client = None


def get_image_gen_client() -> ImageGenClient:
    global _image_gen_client
    if _image_gen_client is None:
        _image_gen_client = ImageGenClient()
    return _image_gen_client
