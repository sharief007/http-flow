import json
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    _instance = None

    def __new__(cls, logger):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, logger):
        if self._initialized:
            return
        self.active_connections: List[WebSocket] = []
        self.logger = logger
        self.logger.info("WebSocket Connection Manager initialized.")
        self._initialized = True

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def pong(self, websocket: WebSocket):
        await websocket.send_json(json.dumps({'type': 'pong'}))

    async def broadcast(self, message: bytes):
        for connection in self.active_connections[:]:  # Copy list to avoid modification during iteration
            try:
                await connection.send_bytes(message)
            except Exception as e:
                self.logger.error(f"Error sending message to WebSocket: {e}")
                self.active_connections.remove(connection)
