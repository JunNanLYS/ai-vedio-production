"""
HTTP 客户端管理模块
提供全局 HTTP 客户端的生命周期管理
"""

from typing import Optional
import httpx
from loguru import logger


_http_client: Optional[httpx.AsyncClient] = None


async def init_http_client():
    """初始化 HTTP 客户端"""
    global _http_client
    _http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(120.0, connect=30.0),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        verify=False
    )
    logger.info("HTTP 客户端初始化完成")


async def close_http_client():
    """关闭 HTTP 客户端"""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
        logger.info("HTTP 客户端已关闭")


def get_http_client() -> httpx.AsyncClient:
    """获取全局 HTTP 客户端"""
    if _http_client is None:
        raise RuntimeError("HTTP 客户端未初始化")
    return _http_client
