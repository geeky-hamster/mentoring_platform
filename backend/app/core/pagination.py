"""Pagination helpers matching the contract Meta object."""
import math

from app import config


def meta(page: int, page_size: int, total: int) -> dict:
    return {"page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, math.ceil(total / max(1, page_size)))}


def paginate(items: list, page: int = 1, page_size: int | None = None) -> list:
    cfg = config.cfg
    page_size = page_size or cfg.DEFAULT_PAGE_SIZE
    page = max(1, page)
    page_size = max(1, min(page_size, cfg.MAX_PAGE_SIZE))
    start = (page - 1) * page_size
    return items[start:start + page_size]
