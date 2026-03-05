import asyncio
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._active_connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._active_connections[user_id].add(websocket)

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            if user_id not in self._active_connections:
                return
            self._active_connections[user_id].discard(websocket)
            if not self._active_connections[user_id]:
                del self._active_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict) -> None:
        async with self._lock:
            sockets = list(self._active_connections.get(user_id, set()))

        stale: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_json(message)
            except Exception:
                stale.append(websocket)

        for websocket in stale:
            await self.disconnect(user_id, websocket)
            try:
                await websocket.close()
            except Exception:
                pass


connection_manager = ConnectionManager()
