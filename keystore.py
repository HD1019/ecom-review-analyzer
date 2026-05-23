"""
SQLite 密钥存储模块 — 多用户多密钥管理
"""
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

DB_PATH = "api_keys.db"

# 套餐对应的每月调用限额
PLAN_LIMITS = {
    "free": 20,
    "basic": 500,
    "pro": 2_000,
    "enterprise": 10_000,
}

# 线程安全锁，避免并发写入冲突
_lock = threading.Lock()


def init_db() -> None:
    """建表并插入默认管理员 key（如果不存在）"""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                user_id    TEXT PRIMARY KEY,
                api_key    TEXT UNIQUE NOT NULL,
                plan       TEXT NOT NULL DEFAULT 'free',
                call_limit_per_month INTEGER NOT NULL,
                current_calls       INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        # 插入默认管理员（幂等）
        conn.execute("""
            INSERT OR IGNORE INTO api_keys (user_id, api_key, plan, call_limit_per_month)
            VALUES (?, ?, ?, ?)
        """, ("admin", "admin-key-123", "enterprise", 10_000))
        conn.commit()


@contextmanager
def _get_conn() -> sqlite3.Connection:
    """获取数据库连接，启用 WAL 模式以支持并发读"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@dataclass
class ApiKeyInfo:
    """密钥查询结果"""
    user_id: str
    api_key: str
    plan: str
    call_limit_per_month: int
    current_calls: int
    created_at: str


def lookup_key(api_key: str) -> Optional[ApiKeyInfo]:
    """根据 api_key 查找用户信息"""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM api_keys WHERE api_key = ?", (api_key,)
        ).fetchone()
    if row is None:
        return None
    return ApiKeyInfo(
        user_id=row["user_id"],
        api_key=row["api_key"],
        plan=row["plan"],
        call_limit_per_month=row["call_limit_per_month"],
        current_calls=row["current_calls"],
        created_at=row["created_at"],
    )


def check_quota(api_key: str) -> tuple[bool, str]:
    """
    检查配额是否充足。
    返回 (允许调用: bool, 消息: str)
    """
    info = lookup_key(api_key)
    if info is None:
        return False, "无效的 API Key"

    if info.current_calls >= info.call_limit_per_month:
        return False, (
            f"本月调用次数已用完 ({info.current_calls}/{info.call_limit_per_month})，"
            f"当前套餐: {info.plan}"
        )

    return True, f"配额充足 ({info.current_calls}/{info.call_limit_per_month})"


def increment_calls(api_key: str) -> None:
    """调用计数 +1"""
    with _lock:
        with _get_conn() as conn:
            conn.execute(
                "UPDATE api_keys SET current_calls = current_calls + 1 WHERE api_key = ?",
                (api_key,),
            )
            conn.commit()


def create_api_key(
    user_id: str,
    api_key: str,
    plan: str = "free",
    call_limit: Optional[int] = None,
) -> ApiKeyInfo:
    """
    生成新的 API Key。
    如果 call_limit 未指定，则根据套餐自动选取默认值。
    """
    if plan not in PLAN_LIMITS:
        raise ValueError(f"无效套餐: {plan}，可选值: {list(PLAN_LIMITS.keys())}")
    limit = call_limit or PLAN_LIMITS[plan]

    with _lock:
        with _get_conn() as conn:
            try:
                conn.execute(
                    """INSERT INTO api_keys (user_id, api_key, plan, call_limit_per_month)
                       VALUES (?, ?, ?, ?)""",
                    (user_id, api_key, plan, limit),
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                raise ValueError(f"user_id 或 api_key 已存在: {e}") from e

    return lookup_key(api_key)  # type: ignore[return-value]


def reset_monthly_calls(api_key: Optional[str] = None) -> int:
    """
    重置月度调用计数。
    不传 api_key 则重置所有用户。
    返回受影响行数。
    """
    with _lock:
        with _get_conn() as conn:
            if api_key:
                conn.execute(
                    "UPDATE api_keys SET current_calls = 0 WHERE api_key = ?",
                    (api_key,),
                )
            else:
                conn.execute("UPDATE api_keys SET current_calls = 0")
            conn.commit()
            return conn.total_changes


def list_keys() -> list[ApiKeyInfo]:
    """列出所有 API Key（供管理用）"""
    with _get_conn() as conn:
        rows = conn.execute("SELECT * FROM api_keys ORDER BY created_at DESC").fetchall()
    return [
        ApiKeyInfo(
            user_id=r["user_id"],
            api_key=r["api_key"],
            plan=r["plan"],
            call_limit_per_month=r["call_limit_per_month"],
            current_calls=r["current_calls"],
            created_at=r["created_at"],
        )
        for r in rows
    ]
