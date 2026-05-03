"""Rate limiting service (Redis-first with in-process fallback).

Implements per-identifier limits for minute/day windows.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from redis import Redis
from redis.exceptions import RedisError

from ..config import REDIS_URL

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RateLimitDecision:
    allowed: bool
    reason: str | None
    minute_count: int
    day_count: int
    backend: str


_redis_lock = threading.RLock()
_redis_client: Redis | None = None
_redis_retry_after: float = 0.0

_fallback_lock = threading.RLock()
_fallback_counter: dict[str, tuple[int, float]] = {}


def _get_redis_client() -> Redis | None:
    """Returns a Redis client or None when unavailable (with short backoff)."""
    global _redis_client, _redis_retry_after

    now = time.monotonic()
    with _redis_lock:
        if _redis_client is not None:
            return _redis_client

        if _redis_retry_after > now:
            return None

        try:
            _redis_client = Redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
                health_check_interval=30,
            )
            _redis_client.ping()
            return _redis_client
        except RedisError as exc:
            _redis_client = None
            _redis_retry_after = now + 30.0
            logger.warning("Rate limiter Redis unavailable, using fallback: %s", exc)
            return None


def _fallback_incr(key: str, ttl_seconds: int) -> int:
    now = time.monotonic()
    with _fallback_lock:
        current = _fallback_counter.get(key)
        if current is None or current[1] <= now:
            _fallback_counter[key] = (1, now + ttl_seconds)
            return 1

        next_count = current[0] + 1
        _fallback_counter[key] = (next_count, current[1])
        return next_count


def _fallback_consume(identifier: str, rpm: int | None, rpd: int | None, now: datetime) -> RateLimitDecision:
    minute_count = 0
    day_count = 0

    minute_bucket = now.strftime("%Y%m%d%H%M")
    day_bucket = now.strftime("%Y%m%d")

    if rpm is not None:
        minute_key = f"rl:{identifier}:m:{minute_bucket}"
        minute_count = _fallback_incr(minute_key, ttl_seconds=120)
        if minute_count > rpm:
            return RateLimitDecision(False, "rate_limit_minute", minute_count, day_count, "fallback")

    if rpd is not None:
        day_key = f"rl:{identifier}:d:{day_bucket}"
        day_count = _fallback_incr(day_key, ttl_seconds=172800)
        if day_count > rpd:
            return RateLimitDecision(False, "rate_limit_day", minute_count, day_count, "fallback")

    return RateLimitDecision(True, None, minute_count, day_count, "fallback")


def consume_rate_limit(identifier: str, rpm: int | None, rpd: int | None) -> RateLimitDecision:
    """Consumes one request in minute/day windows.

    Returns a decision with `allowed` and optional reason:
    - rate_limit_minute
    - rate_limit_day
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    redis_client = _get_redis_client()
    if redis_client is None:
        return _fallback_consume(identifier=identifier, rpm=rpm, rpd=rpd, now=now)

    minute_count = 0
    day_count = 0
    minute_bucket = now.strftime("%Y%m%d%H%M")
    day_bucket = now.strftime("%Y%m%d")

    try:
        if rpm is not None:
            minute_key = f"rl:{identifier}:m:{minute_bucket}"
            minute_count = int(redis_client.incr(minute_key))
            if minute_count == 1:
                redis_client.expire(minute_key, 120)
            if minute_count > rpm:
                return RateLimitDecision(False, "rate_limit_minute", minute_count, day_count, "redis")

        if rpd is not None:
            day_key = f"rl:{identifier}:d:{day_bucket}"
            day_count = int(redis_client.incr(day_key))
            if day_count == 1:
                redis_client.expire(day_key, 172800)
            if day_count > rpd:
                return RateLimitDecision(False, "rate_limit_day", minute_count, day_count, "redis")

        return RateLimitDecision(True, None, minute_count, day_count, "redis")
    except RedisError as exc:
        logger.warning("Rate limiter Redis error, fallback engaged: %s", exc)
        with _redis_lock:
            global _redis_client, _redis_retry_after
            _redis_client = None
            _redis_retry_after = time.monotonic() + 15.0
        return _fallback_consume(identifier=identifier, rpm=rpm, rpd=rpd, now=now)
