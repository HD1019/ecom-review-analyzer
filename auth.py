"""
鉴权依赖模块 — 多密钥验证 + 配额检查 + RapidAPI Proxy 支持
"""
import os

from fastapi import HTTPException, Request, status

from keystore import check_quota, increment_calls, lookup_key

RAPIDAPI_PROXY_SECRET = os.getenv("RAPIDAPI_PROXY_SECRET", "")


async def verify_api_key(request: Request) -> str:
    """
    FastAPI 依赖：鉴权中间件。

    支持两种鉴权方式：
    1. RapidAPI Proxy —— 通过 X-RapidAPI-Proxy-Secret 头验证
    2. Bearer Token —— 查 keystore 表验证 + 配额检查

    返回经过验证的 api_key 字符串（RapidAPI 模式返回 "rapidapi"）。
    """
    # ---- RapidAPI Proxy 鉴权（优先级最高） ----
    proxy_secret = request.headers.get("X-RapidAPI-Proxy-Secret", "")
    if proxy_secret and RAPIDAPI_PROXY_SECRET and proxy_secret == RAPIDAPI_PROXY_SECRET:
        return "rapidapi"

    # ---- Bearer Token 鉴权 ----
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
    """调用成功后扣减配额，RapidAPI 模式跳过（由平台管理配额）。"""
    if api_key == "rapidapi":
        return
    increment_calls(api_key)
