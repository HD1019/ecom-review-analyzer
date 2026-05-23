"""
鉴权依赖模块 — 多密钥验证 + 配额检查 + RapidAPI 支持
"""
from fastapi import HTTPException, Request, status

from keystore import check_quota, increment_calls, lookup_key


async def verify_api_key(request: Request) -> str:
    """
    FastAPI 依赖：鉴权中间件。

    1. RapidAPI 过来的请求（带 X-RapidAPI-Host 头）直接放行
    2. 直接调用需要 Bearer Token 鉴权
    """
    # RapidAPI 代理请求 —— 平台已做鉴权，直接放行
    if request.headers.get("X-RapidAPI-Host"):
        return "rapidapi"

    # Bearer Token 鉴权
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少有效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key = auth_header[len("Bearer "):]

    info = lookup_key(api_key)
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    allowed, msg = check_quota(api_key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=msg,
        )

    return api_key


async def consume_quota(api_key: str) -> None:
    """扣减配额。RapidAPI 模式跳过（平台管理配额）。"""
    if api_key == "rapidapi":
        return
    increment_calls(api_key)
