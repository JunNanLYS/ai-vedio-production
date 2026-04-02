"""
缓存管理模块
提供基于 TTLCache 的缓存管理功能，支持装饰器和模式匹配清理
"""

import asyncio
import fnmatch
import functools
import hashlib
from typing import Any, Callable, Dict, List, Optional

from cachetools import TTLCache
from loguru import logger


_global_cache_manager: Optional["CacheManager"] = None


def get_cache_manager() -> "CacheManager":
    """获取全局缓存管理器实例"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager(maxsize=100, ttl=300)
    return _global_cache_manager


class CacheManager:
    """
    缓存管理器类
    使用 TTLCache 实现带过期时间的缓存
    """

    def __init__(self, maxsize: int = 100, ttl: float = 300):
        """
        初始化缓存管理器

        Args:
            maxsize: 缓存最大条目数
            ttl: 缓存过期时间（秒）
        """
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._maxsize = maxsize
        self._ttl = ttl
        self._stats: Dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "sets": 0,
            "deletes": 0,
        }

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在则返回 None
        """
        try:
            value = self._cache.get(key)
            if value is not None:
                self._stats["hits"] += 1
                logger.debug(f"缓存命中: {key}")
                return value
            else:
                self._stats["misses"] += 1
                logger.debug(f"缓存未命中: {key}")
                return None
        except Exception as e:
            logger.error(f"获取缓存失败: {key}, 错误: {e}")
            return None

    def set(self, key: str, value: Any) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值

        Returns:
            是否设置成功
        """
        try:
            self._cache[key] = value
            self._stats["sets"] += 1
            logger.debug(f"设置缓存: {key}")
            return True
        except Exception as e:
            logger.error(f"设置缓存失败: {key}, 错误: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        try:
            if key in self._cache:
                del self._cache[key]
                self._stats["deletes"] += 1
                logger.debug(f"删除缓存: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除缓存失败: {key}, 错误: {e}")
            return False

    def clear(self, pattern: Optional[str] = None) -> int:
        """
        清理缓存

        Args:
            pattern: 缓存键模式（支持通配符 * 和 ?），为 None 时清空所有缓存

        Returns:
            清理的缓存条目数
        """
        try:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                self._stats["evictions"] += count
                logger.info(f"清空所有缓存，共 {count} 条")
                return count

            keys_to_delete = []
            for key in self._cache.keys():
                if fnmatch.fnmatch(str(key), pattern):
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._cache[key]
                self._stats["deletes"] += 1

            logger.info(f"清理缓存模式 '{pattern}'，共 {len(keys_to_delete)} 条")
            return len(keys_to_delete)
        except Exception as e:
            logger.error(f"清理缓存失败: {pattern}, 错误: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        return key in self._cache

    def keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        获取缓存键列表

        Args:
            pattern: 缓存键模式（支持通配符 * 和 ?），为 None 时返回所有键

        Returns:
            缓存键列表
        """
        try:
            if pattern is None:
                return list(self._cache.keys())

            return [key for key in self._cache.keys() if fnmatch.fnmatch(str(key), pattern)]
        except Exception as e:
            logger.error(f"获取缓存键列表失败: {pattern}, 错误: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "ttl": self._ttl,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": f"{hit_rate:.2f}%",
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
            "evictions": self._stats["evictions"],
        }

    def reset_stats(self) -> None:
        """
        重置统计信息
        """
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "sets": 0,
            "deletes": 0,
        }
        logger.info("缓存统计信息已重置")


def _generate_cache_key(func: Callable, args: tuple, kwargs: dict, key_func: Optional[Callable] = None) -> str:
    """
    生成缓存键

    Args:
        func: 被装饰的函数
        args: 位置参数
        kwargs: 关键字参数
        key_func: 自定义缓存键生成函数

    Returns:
        缓存键
    """
    if key_func is not None:
        return key_func(*args, **kwargs)

    func_name = f"{func.__module__}.{func.__qualname__}"

    try:
        key_parts = [func_name]

        if args:
            key_parts.append(str(args))
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.append(str(sorted_kwargs))

        key_string = ":".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()

        return f"{func_name}:{key_hash}"
    except Exception:
        return f"{func_name}:{hash(args)}:{hash(frozenset(kwargs.items()))}"


def cached(
    key_func: Optional[Callable] = None,
    cache_manager: Optional[CacheManager] = None,
    ttl: Optional[float] = None,
):
    """
    缓存装饰器

    Args:
        key_func: 自定义缓存键生成函数
        cache_manager: 缓存管理器实例，为 None 时使用全局实例
        ttl: 缓存过期时间（秒），为 None 时使用缓存管理器的默认值

    Returns:
        装饰器函数

    Example:
        @cached()
        def get_user(user_id: int):
            return fetch_user_from_db(user_id)

        @cached(key_func=lambda user_id, name: f"user:{user_id}:{name}")
        def get_user_by_name(user_id: int, name: str):
            return fetch_user_from_db(user_id)

        @cached(ttl=60)
        async def get_data():
            return await fetch_data()
    """
    manager = cache_manager if cache_manager is not None else get_cache_manager()

    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                cache_key = _generate_cache_key(func, args, kwargs, key_func)

                cached_value = manager.get(cache_key)
                if cached_value is not None:
                    return cached_value

                result = await func(*args, **kwargs)

                manager.set(cache_key, result)

                return result

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                cache_key = _generate_cache_key(func, args, kwargs, key_func)

                cached_value = manager.get(cache_key)
                if cached_value is not None:
                    return cached_value

                result = func(*args, **kwargs)

                manager.set(cache_key, result)

                return result

            return sync_wrapper

    return decorator


def clear_cache(pattern: Optional[str] = None, cache_manager: Optional[CacheManager] = None) -> int:
    """
    清理缓存的全局函数

    Args:
        pattern: 缓存键模式（支持通配符 * 和 ?），为 None 时清空所有缓存
        cache_manager: 缓存管理器实例，为 None 时使用全局实例

    Returns:
        清理的缓存条目数

    Example:
        clear_cache()  # 清空所有缓存
        clear_cache("get_user:*")  # 清理所有 get_user 相关的缓存
        clear_cache("*:user_id=123*")  # 清理包含特定参数的缓存
    """
    manager = cache_manager if cache_manager is not None else get_cache_manager()
    return manager.clear(pattern)


cache_manager = get_cache_manager()
