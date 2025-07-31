import pytest
import asyncio
import tempfile
import os
from unittest.mock import AsyncMock, Mock
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.storage import DatabaseManager, CacheStore


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_db_path = f.name
    
    yield temp_db_path
    
    # Cleanup
    if os.path.exists(temp_db_path):
        os.unlink(temp_db_path)


@pytest.fixture
async def db_manager(temp_db):
    """Create a DatabaseManager instance for testing"""
    manager = DatabaseManager(temp_db)
    await manager.initialize()
    yield manager
    await manager.close()


@pytest.fixture
def cache_store():
    """Create a CacheStore instance for testing"""
    return CacheStore()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing"""
    mock_ws = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


@pytest.fixture
def mock_flow():
    """Create a mock mitmproxy flow for testing"""
    from unittest.mock import Mock
    
    mock_flow = Mock()
    mock_flow.id = "test-flow-123"
    mock_flow.request.method = "GET"
    mock_flow.request.pretty_url = "https://example.com/api/test"
    mock_flow.request.headers = {"User-Agent": "test-agent"}
    mock_flow.request.content = b""
    mock_flow.response = Mock()
    mock_flow.response.status_code = 200
    mock_flow.response.headers = {"Content-Type": "application/json"}
    mock_flow.response.content = b'{"test": "data"}'
    
    return mock_flow


@pytest.fixture
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
