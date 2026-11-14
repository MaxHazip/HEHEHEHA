"""Relay для WebRTC-сигналинга.

MVP: backend не хранит медиа и не проксирует звук. Браузеры обмениваются
SDP/ICE через WebSocket, а запись разговора загружается в БД отдельно.
"""

import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class CallSignallingHub:
    def __init__(self) -> None:
        self._rooms: dict[int, set[WebSocket]] = {}

    async def connect(self, call_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms.setdefault(call_id, set()).add(websocket)

    def disconnect(self, call_id: int, websocket: WebSocket) -> None:
        room = self._rooms.get(call_id)
        if not room:
            return
        room.discard(websocket)
        if not room:
            self._rooms.pop(call_id, None)

    def peers_count(self, call_id: int) -> int:
        return len(self._rooms.get(call_id, set()))

    async def relay(
        self, call_id: int, sender: WebSocket, message: str
    ) -> None:
        room = list(self._rooms.get(call_id, set()))
        for peer in room:
            if peer is sender:
                continue
            try:
                await peer.send_text(message)
            except Exception as exc:  # noqa: BLE001
                logger.info("WebRTC peer disconnected: %s", exc)
                self.disconnect(call_id, peer)

    async def broadcast(self, call_id: int, payload: dict) -> None:
        for peer in list(self._rooms.get(call_id, set())):
            try:
                await peer.send_json(payload)
            except Exception as exc:  # noqa: BLE001
                logger.info("WebRTC peer disconnected: %s", exc)
                self.disconnect(call_id, peer)


hub = CallSignallingHub()
