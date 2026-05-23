"""
管理员路由 — 受超级管理员密钥保护，用于生成/管理 API Key
"""
import os

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from keystore import PLAN_LIMITS, create_api_key, list_keys, reset_monthly_calls

# 超级管理员密钥，从环境变量读取，默认 admin-key-123
ADMIN_KEY = os.getenv("ADMIN_API_KEY", "admin-key-123")

router = APIRouter(prefix="/admin", tags=["管理"])


# ---------------------------------------------------------------------------
# Pydantic 模型
# ---------------------------------------------------------------------------

class GenerateKeyRequest(BaseModel):
    """生成新 API Key 的请求体"""
    user_id: str = Field(..., description="用户ID", min_length=1, example="user_001")
    api_key: str = Field(..., description="自定义 API Key 字符串", min_length=8, example="sk-my-custom-key-123")
    plan: str = Field(
        default="free",
        description="套餐类型",
        example="basic",
    )
    call_limit_per_month: int | None = Field(
        default=None,
        description="自定义月调用上限（不传则按套餐默认值）",
        ge=1,
        example=1000,
    )

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v: str) -> str:
        if v not in PLAN_LIMITS:
            raise ValueError(f"无效套餐: {v}，可选: {list(PLAN_LIMITS.keys())}")
        return v


class ResetRequest(BaseModel):
    """重置月度计数的请求体"""
    api_key: str | None = Field(
        default=None,
        description="要重置的 API Key，不传则重置全部"
    )


# ---------------------------------------------------------------------------
# 管理员鉴权依赖
# ---------------------------------------------------------------------------

async def verify_admin(request: Request) -> None:
    """校验超级管理员密钥"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少管理员认证令牌",
        )
    token = auth_header[len("Bearer "):]
    if token != ADMIN_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员认证令牌无效",
        )


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@router.post("/generate-key")
async def generate_key(body: GenerateKeyRequest, request: Request):
    """
    生成新的 API Key。
    需要超级管理员密钥授权: `Authorization: Bearer <ADMIN_API_KEY>`
    """
    await verify_admin(request)

    try:
        info = create_api_key(
            user_id=body.user_id,
            api_key=body.api_key,
            plan=body.plan,
            call_limit=body.call_limit_per_month,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return {
        "message": "API Key 创建成功",
        "user_id": info.user_id,
        "api_key": info.api_key,
        "plan": info.plan,
        "call_limit_per_month": info.call_limit_per_month,
        "created_at": info.created_at,
    }


@router.get("/list-keys")
async def list_all_keys(request: Request):
    """列出所有 API Key（需要管理员授权）"""
    await verify_admin(request)
    keys = list_keys()
    return {
        "count": len(keys),
        "keys": [
            {
                "user_id": k.user_id,
                "api_key": k.api_key,
                "plan": k.plan,
                "call_limit_per_month": k.call_limit_per_month,
                "current_calls": k.current_calls,
                "usage": f"{k.current_calls}/{k.call_limit_per_month}",
                "created_at": k.created_at,
            }
            for k in keys
        ],
    }


@router.post("/reset-calls")
async def reset_calls(body: ResetRequest, request: Request):
    """
    重置月度调用计数。
    不传 api_key 则重置全部用户。
    """
    await verify_admin(request)
    affected = reset_monthly_calls(body.api_key)
    return {
        "message": "重置成功",
        "affected_rows": affected,
        "target": body.api_key or "全部用户",
    }
