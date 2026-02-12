import logging
import json
from typing import Dict, List, Set, Any
from uuid import UUID
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Manages active WebSocket connections scoped by tenant_id.
    Standardized per FORSEE Architecture.
    """
    def __init__(self):
        # tenant_id -> { user_id -> set(WebSocket) }
        self.active_connections: Dict[str, Dict[str, Set[WebSocket]]] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str, user_id: str):
        await websocket.accept()
        
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = {}
        
        if user_id not in self.active_connections[tenant_id]:
            self.active_connections[tenant_id][user_id] = set()
            
        self.active_connections[tenant_id][user_id].add(websocket)
        logger.info(f"WebSocket connected: Tenant {tenant_id} | User {user_id}")

    def disconnect(self, websocket: WebSocket, tenant_id: str, user_id: str):
        if tenant_id in self.active_connections:
            if user_id in self.active_connections[tenant_id]:
                self.active_connections[tenant_id][user_id].remove(websocket)
                if not self.active_connections[tenant_id][user_id]:
                    del self.active_connections[tenant_id][user_id]
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
        logger.info(f"WebSocket disconnected: Tenant {tenant_id} | User {user_id}")

    async def broadcast_to_tenant(self, tenant_id: str, message: Dict[str, Any]):
        """
        Pushes message to all connected users of a specific tenant.
        Enforces Multi-Tenant Isolation.
        """
        if tenant_id not in self.active_connections:
            return

        payload = json.dumps(message, default=str)
        
        # Identify all users in tenant
        for user_id, connections in self.active_connections[tenant_id].items():
            for connection in list(connections): # avoid concurrent modification error
                try:
                    await connection.send_text(payload)
                except Exception as e:
                    logger.warning(f"Failed to send WS to user {user_id} in tenant {tenant_id}: {e}")
                    # In a real app, we might trigger disconnect here if connection is dead

    async def push_to_user(self, tenant_id: str, user_id: str, message: Dict[str, Any]):
        """
        Targeted push to specific user (e.g. personal reminder).
        """
        if tenant_id in self.active_connections and user_id in self.active_connections[tenant_id]:
            payload = json.dumps(message, default=str)
            for connection in self.active_connections[tenant_id][user_id]:
                try:
                    await connection.send_text(payload)
                except Exception as e:
                    logger.warning(f"Failed to send WS to user {user_id}: {e}")

ws_manager = WebSocketManager()
