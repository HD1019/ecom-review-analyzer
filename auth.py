"""
鉴权依赖模块 — 多密钥验证 + 配额检查
"""
from fastapi import HTTPException, Request, status

from keystore import check_quota, increment_calls, lookup_key


async def verify_api_key(request: Request) -> str:
    """
    FastAPI 依赖：从请求头提取 Bearer Token，
    查表验证密钥有效性，检查本月配额，超限返回 429。

    返回经过验证的 api_key 字符串。
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少有效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key = auth_header[len("Bearer "):]

    # 查表
    info = lookup_key(api_key)
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证令牌无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查配额
    allowed, msg = check_quota(api_key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=msg,
        )

    return api_key


async def consume_quota(api_key: str) -> None:
    """
    调用成功后执行配额扣减（当前月 +1）。
    通常在业务逻辑执行完成后调用。
    """
    increment_calls(api_key)
