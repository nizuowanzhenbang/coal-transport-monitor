"""通用工具函数"""
from typing import Any, Optional


def api_response(
    code: int = 200,
    message: str = "success",
    data: Any = None,
) -> dict:
    """
    统一API响应格式

    返回格式：{"code": 200, "message": "success", "data": {...}}
    """
    resp = {"code": code, "message": message}
    if data is not None:
        resp["data"] = data
    return resp


def paginate_response(
    items: list,
    total: int,
    page: int,
    page_size: int,
) -> dict:
    """分页响应包装"""
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }
