"""In-process sliding-window rate limiter (develop uses memory storage per design Section 11.5)."""
import threading
import time
from collections import defaultdict, deque

_buckets: dict[str, deque] = defaultdict(deque)
_lock = threading.Lock()


def _clean(key: str, window: float, now: float) -> None:
    dq = _buckets[key]
    while dq and dq[0] <= now - window:
        dq.popleft()


def hit(key: str, max_calls: int, window_seconds: float) -> tuple[bool, int]:
    """Record a call for *key*. Returns (allowed, retry_after_seconds)."""
    now = time.monotonic()
    with _lock:
        _clean(key, window_seconds, now)
        dq = _buckets[key]
        if len(dq) >= max_calls:
            retry = int(window_seconds - (now - dq[0])) + 1
            return False, max(1, retry)
        dq.append(now)
        return True, 0


def reset_all() -> None:  # used by tests
    with _lock:
        _buckets.clear()
