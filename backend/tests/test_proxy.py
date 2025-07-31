import pytest
import socket
from unittest.mock import Mock, patch, MagicMock
from multiprocessing import SimpleQueue, Process
from backend.services.proxy import ProxyManager, run_mitmproxy_process
from backend.HttpInterceptor.FilterModel import FilterModel as PyFilterModel
from backend.HttpInterceptor.RuleModel import RuleModel as PyRuleModel
from backend.HttpInterceptor.OperationType import OperationType
from backend.services.ws import ConnectionManager


@pytest.fixture
def mock_connection_manager():
    """Create mock ConnectionManager for testing"""
    return Mock(spec=ConnectionManager)


@pytest.fixture
def proxy_manager(mock_connection_manager):
    """Create ProxyManager instance for testing"""
    return ProxyManager(mock_connection_manager)


@pytest.fixture
def mock_filter():
    """Create mock PyFilterModel for testing"""
    mock_filter = Mock(spec=PyFilterModel)
    mock_filter.id = 1
    mock_filter.filter_name = "Test Filter"
    return mock_filter


@pytest.fixture
def mock_rule():
    """Create mock PyRuleModel for testing"""
    mock_rule = Mock(spec=PyRuleModel)
    mock_rule.id = 1
    mock_rule.rule_name = "Test Rule"
    return mock_rule


class TestProxyManager:
    """Test ProxyManager class"""
    
    def test_proxy_manager_init(self, proxy_manager):
        """Test ProxyManager initialization"""
        assert proxy_manager.proxy_port == 8888  # Default port is 8888
        assert proxy_manager.connection_manager is not None
        assert hasattr(proxy_manager, 'flow_queue')
        assert hasattr(proxy_manager, 'rule_queue')
        assert hasattr(proxy_manager, 'stop_event')

    def test_proxy_manager_init_with_port(self, mock_connection_manager):
        """Test ProxyManager initialization with custom port"""
        proxy_manager = ProxyManager(mock_connection_manager, proxy_port=9090)
        assert proxy_manager.proxy_port == 9090

    def test_check_port_available_free_port(self, proxy_manager):
        """Test checking if port is available when free"""
        # Use a high port number that's likely to be free
        result = proxy_manager._check_port_available(65432)
        assert result is True

    def test_check_port_available_occupied_port(self, proxy_manager):
        """Test checking if port is available when occupied"""
        # Create a socket to occupy a port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', 0))  # Bind to any available port
        port = sock.getsockname()[1]
        
        try:
            result = proxy_manager._check_port_available(port)
            assert result is False
        finally:
            sock.close()

    def test_find_available_port_default(self, proxy_manager):
        """Test finding available port starting from default"""
        port = proxy_manager._find_available_port()
        assert port >= 8888
        assert proxy_manager._check_port_available(port) is True

    def test_find_available_port_custom_start(self, proxy_manager):
        """Test finding available port with custom start port"""
        port = proxy_manager._find_available_port(start_port=9000)
        assert port >= 9000
        assert proxy_manager._check_port_available(port) is True

    def test_get_status_default(self, proxy_manager):
        """Test getting status with default values"""
        status = proxy_manager.get_status()
        
        assert isinstance(status, dict)
        assert "port" in status  # Changed from "proxy_port" to "port"
        assert "is_running" in status
        assert status["port"] == 8888  # Changed from "proxy_port" to "port"
        assert status["is_running"] is False

    def test_sync_filter_add(self, proxy_manager, mock_filter):
        """Test syncing filter with ADD operation when proxy is not running"""
        result = proxy_manager.sync_filter(mock_filter, OperationType.ADD)
        
        # Should return False when proxy is not running
        assert result is False

    def test_sync_filter_update(self, proxy_manager, mock_filter):
        """Test syncing filter with UPDATE operation when proxy is not running"""
        result = proxy_manager.sync_filter(mock_filter, OperationType.UPDATE)
        
        assert result is False

    def test_sync_filter_delete(self, proxy_manager, mock_filter):
        """Test syncing filter with DELETE operation when proxy is not running"""
        result = proxy_manager.sync_filter(mock_filter, OperationType.DELETE)
        
        assert result is False

    def test_sync_rule_add(self, proxy_manager, mock_rule):
        """Test syncing rule with ADD operation when proxy is not running"""
        result = proxy_manager.sync_rule(mock_rule, OperationType.ADD)
        
        assert result is False

    def test_sync_rule_update(self, proxy_manager, mock_rule):
        """Test syncing rule with UPDATE operation when proxy is not running"""
        result = proxy_manager.sync_rule(mock_rule, OperationType.UPDATE)
        
        assert result is False

    def test_sync_rule_delete(self, proxy_manager, mock_rule):
        """Test syncing rule with DELETE operation when proxy is not running"""
        result = proxy_manager.sync_rule(mock_rule, OperationType.DELETE)
        
        assert result is False

    def test_full_sync(self, proxy_manager, mock_filter, mock_rule):
        """Test full sync with filters and rules when proxy is not running"""
        filters = [mock_filter]
        rules = [mock_rule]
        
        result = proxy_manager.full_sync(filters, rules)
        
        assert result is False

    @patch('backend.proxy.Process')
    @patch('backend.proxy.MessageFactory')
    def test_sync_filter_when_running(self, mock_message_factory, mock_process, proxy_manager, mock_filter):
        """Test syncing filter when proxy process is running"""
        # Mock the process to appear running
        mock_process_instance = Mock()
        mock_process_instance.is_alive.return_value = True
        mock_process.return_value = mock_process_instance
        
        # Mock the message factory
        mock_message_factory.create_sync_message.return_value = b'mocked_message'
        
        # Set up proxy manager to appear running with proper queue initialization
        proxy_manager.proxy_process = mock_process_instance
        proxy_manager.is_running = True
        # Initialize the queues like they would be in the start method
        proxy_manager.rule_queue = SimpleQueue()
        proxy_manager.flow_queue = SimpleQueue()
        
        # Mock the PySyncMessage creation to avoid validation errors
        with patch('backend.proxy.PySyncMessage') as mock_sync_message:
            mock_sync_message.return_value = Mock()
            
            result = proxy_manager.sync_filter(mock_filter, OperationType.ADD)
            
            # Should return True when proxy is running
            assert result is True
            # Verify message was sent to rule queue
            assert not proxy_manager.rule_queue.empty()
            # Verify message factory was called
            mock_message_factory.create_sync_message.assert_called_once()


class TestRunMitmproxyProcess:
    """Test the run_mitmproxy_process function"""
    
    @patch('backend.proxy.asyncio.run')
    def test_run_mitmproxy_process_setup(self, mock_asyncio_run):
        """Test mitmproxy process setup"""
        # Mock dependencies
        mock_flow_queue = Mock(spec=SimpleQueue)
        mock_rule_queue = Mock(spec=SimpleQueue)
        mock_stop_event = Mock()
        mock_stop_event.is_set.return_value = False
        
        # Mock asyncio.run to prevent actual execution
        mock_asyncio_run.side_effect = KeyboardInterrupt("Test interrupt")
        
        # This should complete without raising an exception (other than the mocked KeyboardInterrupt)
        try:
            run_mitmproxy_process(8888, mock_flow_queue, mock_rule_queue, mock_stop_event)
        except KeyboardInterrupt:
            pass  # Expected when mocking
        
        # Verify asyncio.run was called with some coroutine
        mock_asyncio_run.assert_called_once()
        # Verify the coroutine that was passed is callable
        called_args = mock_asyncio_run.call_args[0]
        assert len(called_args) == 1  # Should have one argument (the coroutine)

    @patch('backend.proxy.asyncio.run')
    def test_run_mitmproxy_process_port_config(self, mock_asyncio_run):
        """Test mitmproxy process with custom port configuration"""
        # Mock dependencies
        mock_flow_queue = Mock(spec=SimpleQueue)
        mock_rule_queue = Mock(spec=SimpleQueue)
        mock_stop_event = Mock()
        mock_stop_event.is_set.return_value = False

        # Test with custom port
        custom_port = 9090

        # Mock asyncio.run to prevent actual execution
        mock_asyncio_run.side_effect = KeyboardInterrupt("Test interrupt")

        # This should complete without raising an exception (other than the mocked KeyboardInterrupt)
        try:
            run_mitmproxy_process(custom_port, mock_flow_queue, mock_rule_queue, mock_stop_event)
        except KeyboardInterrupt:
            pass  # Expected when mocking

        # Verify asyncio.run was called with some coroutine
        mock_asyncio_run.assert_called_once()
        # Verify the coroutine that was passed is callable
        called_args = mock_asyncio_run.call_args[0]
        assert len(called_args) == 1  # Should have one argument (the coroutine)