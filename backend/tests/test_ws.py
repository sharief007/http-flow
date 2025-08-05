import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from backend.services.ws import ConnectionManager
from backend.models.base_models import FlowData, FilterModel, RuleModel, Operator, RuleAction


@pytest.fixture
def ws_manager():
    """Create WebSocketManager instance for testing"""
    from unittest.mock import Mock
    # Reset singleton instance before each test
    ConnectionManager._instance = None
    mock_logger = Mock()
    manager = ConnectionManager(mock_logger)
    yield manager
    # Clean up after test
    ConnectionManager._instance = None


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket connection"""
    websocket = AsyncMock()
    websocket.send = AsyncMock()
    websocket.recv = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


class TestWebSocketManager:
    """Test WebSocketManager class"""
    
    def test_ws_manager_init(self, ws_manager):
        """Test WebSocketManager initialization"""
        assert ws_manager.active_connections == []
        assert hasattr(ws_manager, 'logger')
        assert ws_manager._initialized is True

    @pytest.mark.asyncio
    async def test_connect_websocket(self, ws_manager, mock_websocket):
        """Test connecting WebSocket"""
        await ws_manager.connect(mock_websocket)
        
        assert mock_websocket in ws_manager.active_connections
        assert len(ws_manager.active_connections) == 1
        mock_websocket.accept.assert_called_once()

    def test_disconnect_websocket(self, ws_manager, mock_websocket):
        """Test disconnecting WebSocket"""
        # Ensure clean state
        ws_manager.active_connections.clear()
        
        # Add connection first
        ws_manager.active_connections.append(mock_websocket)
        assert mock_websocket in ws_manager.active_connections
        
        # Disconnect
        ws_manager.disconnect(mock_websocket)
        assert mock_websocket not in ws_manager.active_connections
        assert len(ws_manager.active_connections) == 0

    def test_disconnect_nonexistent_connection(self, ws_manager, mock_websocket):
        """Test disconnecting connection that doesn't exist"""
        # Ensure clean state
        ws_manager.active_connections.clear()
        
        # Should not raise error
        ws_manager.disconnect(mock_websocket)
        assert len(ws_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_broadcast_message(self, ws_manager):
        """Test broadcasting message to all connections"""
        # Ensure clean state
        ws_manager.active_connections.clear()
        
        # Create multiple mock connections
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws3 = AsyncMock()
        
        ws_manager.active_connections = [mock_ws1, mock_ws2, mock_ws3]
        
        test_message = b"test broadcast message"
        
        await ws_manager.broadcast(test_message)
        
        # Verify all connections received the message
        mock_ws1.send_bytes.assert_called_once_with(test_message)
        mock_ws2.send_bytes.assert_called_once_with(test_message)
        mock_ws3.send_bytes.assert_called_once_with(test_message)

    @pytest.mark.asyncio
    async def test_broadcast_message_no_connections(self, ws_manager):
        """Test broadcasting when no connections exist"""
        test_message = b"no connections test"
        
        # Should not raise error
        await ws_manager.broadcast(test_message)

    @pytest.mark.asyncio
    async def test_broadcast_message_connection_error(self, ws_manager):
        """Test broadcasting when a connection fails"""
        # Ensure clean state
        ws_manager.active_connections.clear()
        
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        
        # Make one connection fail
        mock_ws1.send_bytes.side_effect = ConnectionError("Connection lost")
        
        ws_manager.active_connections = [mock_ws1, mock_ws2]
        
        test_message = b"error test message"
        
        await ws_manager.broadcast(test_message)
        
        # Failed connection should be removed
        assert mock_ws1 not in ws_manager.active_connections
        assert mock_ws2 in ws_manager.active_connections
        
        # Working connection should still receive message
        mock_ws2.send_bytes.assert_called_once_with(test_message)

    @pytest.mark.asyncio
    async def test_pong_response(self, ws_manager, mock_websocket):
        """Test pong response to websocket"""
        await ws_manager.pong(mock_websocket)
        
        # Verify pong response was sent
        expected_pong = json.dumps({'type': 'pong'})
        mock_websocket.send_json.assert_called_once_with(expected_pong)

    def test_singleton_pattern(self):
        """Test that ConnectionManager follows singleton pattern"""
        from unittest.mock import Mock
        mock_logger1 = Mock()
        mock_logger2 = Mock()
        
        # Clean state
        ConnectionManager._instance = None
        manager1 = ConnectionManager(mock_logger1)
        manager2 = ConnectionManager(mock_logger2)
        assert manager1 is manager2
        
        # Clean up after test
        ConnectionManager._instance = None

    def test_get_connection_count(self, ws_manager):
        """Test getting connection count"""
        # Ensure clean state
        ws_manager.active_connections.clear()
        assert len(ws_manager.active_connections) == 0
        
        # Add some mock connections
        mock_ws1 = Mock()
        mock_ws2 = Mock()
        ws_manager.active_connections.append(mock_ws1)
        ws_manager.active_connections.append(mock_ws2)
        
        assert len(ws_manager.active_connections) == 2

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, ws_manager):
        """Test handling multiple concurrent connections"""
        # Ensure clean state
        ws_manager.active_connections.clear()
        
        connections = []
        for i in range(5):
            mock_ws = AsyncMock()
            connections.append(mock_ws)
            ws_manager.active_connections.append(mock_ws)
        
        assert len(ws_manager.active_connections) == 5
        
        # Broadcast to all connections
        test_message = b"concurrent test"
        await ws_manager.broadcast(test_message)
        
        # Verify all connections received the message
        for mock_ws in connections:
            mock_ws.send_bytes.assert_called_once_with(test_message)
