import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.services.auth import decode_token
from app.websockets.manager import connection_manager

router = APIRouter(tags=["WebSockets"])


async def _authenticate_websocket(websocket: WebSocket) -> str | None:
    token = websocket.query_params.get("token")
    if not token:
        return None

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    try:
        parsed_user_id = uuid.UUID(user_id)
    except ValueError:
        return None

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User.id, User.is_active).where(User.id == parsed_user_id)
        )
        user = result.one_or_none()

    if not user or not user.is_active:
        return None

    return str(parsed_user_id)


@router.websocket("/api/v1/ws/orders")
async def order_updates_websocket(websocket: WebSocket) -> None:
    user_id = await _authenticate_websocket(websocket)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await connection_manager.connect(user_id, websocket)

    try:
        while True:
            # Keep the connection alive and optionally handle client ping messages.
            message = await websocket.receive_text()
            if message.lower() == "ping":
                await websocket.send_json({"message": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass
    finally:
        await connection_manager.disconnect(user_id, websocket)
