"""WebSocket端点：实时推送新预警通知"""
import asyncio
import json
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt

from app.config import settings

router = APIRouter(tags=["WebSocket"])

# 全局连接池
_connections: Set[WebSocket] = set()


async def broadcast_alert(alert_data: dict) -> None:
    """向所有在线客户端广播新预警（供 risk_engine 回调调用）"""
    if not _connections:
        return
    message = json.dumps(alert_data, ensure_ascii=False, default=str)
    dead = set()
    for ws in list(_connections):
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    _connections.difference_update(dead)


@router.websocket("/api/ws/alerts")
async def alerts_websocket(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket 实时预警推送

    连接方式：ws://host/api/ws/alerts?token=<jwt>

    消息格式：{"type": "new_alert", "data": {...}}
    心跳格式：{"type": "ping"} → 回复 {"type": "pong"}
    """
    # JWT 验证
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if not payload.get("sub"):
            await websocket.close(code=4001)
            return
    except JWTError:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    _connections.add(websocket)
    try:
        while True:
            try:
                text = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if text == '{"type":"ping"}' or text.strip() == "ping":
                    await websocket.send_text('{"type":"pong"}')
            except asyncio.TimeoutError:
                # 超时发送 keep-alive
                try:
                    await websocket.send_text('{"type":"ping"}')
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        _connections.discard(websocket)
