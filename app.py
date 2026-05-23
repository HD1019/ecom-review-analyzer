"""
AI电商评论分析 API 服务
========================
使用 FastAPI + Pydantic 构建，调用大模型对用户评论进行结构化分析。
支持多用户多密钥鉴权 + 月度配额管理。
"""
import json
import logging
import os
import re
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from auth import consume_quota, verify_api_key
from keystore import init_db

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("review_analyzer")

# ---------------------------------------------------------------------------
# 配置常量（从环境变量读取）
# ---------------------------------------------------------------------------
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# ---------------------------------------------------------------------------
# FastAPI 应用实例
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI电商评论分析服务",
    description="对电商用户评论进行AI驱动的结构化分析，支持多用户配额管理",
    version="1.1.0",
)


# 启动时初始化数据库
@app.on_event("startup")
def startup():
    init_db()
    logger.info("数据库初始化完成")


# 注册管理员路由
from admin_routes import router as admin_router

app.include_router(admin_router)


# ============================= 数据模型 ======================================

class AnalyzeRequest(BaseModel):
    """评论分析请求体"""
    product_name: Optional[str] = Field(
        default=None,
        description="商品名称（可选）",
        example="无线蓝牙耳机 Pro Max",
    )
    reviews: list[str] = Field(
        ...,
        description="用户评论列表，每条是一条用户评论",
        min_length=1,
        example=["音质很好，续航也不错", "戴久了耳朵疼，降噪一般"],
    )
    max_reviews: int = Field(
        default=100,
        ge=1,
        le=300,
        description="最多分析的评论数量，默认100，最大300",
        example=50,
    )

    @field_validator("reviews")
    @classmethod
    def reviews_must_not_be_empty(cls, v: list[str]) -> list[str]:
        """过滤空字符串，保证至少有一条有效评论"""
        cleaned = [r.strip() for r in v if r.strip()]
        if not cleaned:
            raise ValueError("评论列表不能全为空")
        return cleaned


# ============================= LLM 调用逻辑 =================================

# 分析提示词 —— 要求模型严格按照 JSON 结构输出
SYSTEM_PROMPT = (
    "你是一位顶级电商运营顾问。"
    "请根据以下用户评论，严格按照JSON格式返回分析结果，不要包含任何其他文本。"
    "JSON结构为："
    '{"strengths": ["优点1及代表性原话", ...],'
    '"weaknesses": ["缺点1及严重程度(高/中/低)和原话", ...],'
    '"improvement_suggestions": "一条最有效的改进建议",'
    '"user_profile": "买家画像，50字内",'
    '"sentiment_distribution": {"positive": 0.6, "negative": 0.2, "neutral": 0.2}}'
)


async def call_llm(reviews_text: str, product_name: Optional[str] = None) -> dict:
    """
    调用 OpenAI 兼容的大模型 API 分析评论。
    base_url / api_key / model 均从环境变量读取。
    """
    user_prompt = f"商品名称：{product_name or '未提供'}\n\n用户评论：\n{reviews_text}"

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,       # 低温度以获得稳定结构化输出
        "max_tokens": 2048,
    }

    llm_auth_headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    # 拼接完整的 chat completions 端点地址
    base = LLM_BASE_URL.rstrip("/")
    url = f"{base}/v1/chat/completions"

    logger.info("调用 LLM: model=%s, url=%s", LLM_MODEL, url)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload, headers=llm_auth_headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("LLM API 返回错误: status=%d, body=%s",
                         exc.response.status_code, exc.response.text)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"大模型服务返回错误: {exc.response.status_code}",
            )
        except httpx.RequestError as exc:
            logger.error("连接 LLM API 失败: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="无法连接到大模型服务",
            )

    data = response.json()
    raw_content = data["choices"][0]["message"]["content"]
    logger.debug("LLM 原始返回内容: %s", raw_content)

    # ---- 解析 LLM 返回的 JSON ----
    try:
        result = json.loads(raw_content)
    except json.JSONDecodeError:
        # 尝试从 Markdown 代码块中提取 JSON（模型可能包裹了 ```json）
        match = re.search(r"```(?:json)?\s*\n?(.*?)```", raw_content, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                logger.error("JSON 解析失败: %s", raw_content)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="大模型返回结果解析失败",
                )
        else:
            logger.error("JSON 解析失败: %s", raw_content)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="大模型返回结果解析失败",
            )

    return result


# ============================= 路由端点 =====================================

@app.get("/")
async def health_check():
    """根路径 —— 返回健康检查信息"""
    return {
        "status": "healthy",
        "service": "AI电商评论分析服务",
        "version": "1.1.0",
        "llm_model": LLM_MODEL,
    }


@app.get("/debug-headers")
async def debug_headers(request: Request):
    """临时调试接口 —— 查看 RapidAPI 转发的请求头"""
    return {k: v for k, v in request.headers.items()}


@app.post("/api/v1/analyze-reviews")
async def analyze_reviews(body: AnalyzeRequest, request: Request):
    """
    分析电商用户评论。

    鉴权:  Bearer Token（通过管理员接口 /admin/generate-key 生成）
    限流:  根据套餐月度配额，超限返回 429

    返回 AI 驱动的结构化分析结果。
    """
    # 1. 多密钥鉴权 + 配额检查
    api_key = await verify_api_key(request)

    # 2. 取前 max_reviews 条评论
    selected = body.reviews[: body.max_reviews]

    # 3. 拼接为带序号的文本块
    reviews_text = "\n".join(
        f"【评论{i + 1}】{review}" for i, review in enumerate(selected)
    )

    logger.info("收到分析请求: api_key=%s..., product=%s, 分析%d/%d条",
                 api_key[:8], body.product_name or "N/A",
                 len(selected), len(body.reviews))

    # 4. 调用大模型分析
    try:
        result = await call_llm(reviews_text, body.product_name)
    except HTTPException:
        raise  # 直接透传已定义的 HTTP 异常
    except Exception as exc:
        logger.exception("分析过程发生未预期的异常: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析服务内部错误",
        )

    # 5. 成功后扣减配额
    await consume_quota(api_key)

    # 6. 返回分析结果
    return JSONResponse(content={
        "product_name": body.product_name,
        "analyzed_count": len(selected),
        "total_count": len(body.reviews),
        "analysis": result,
    })
