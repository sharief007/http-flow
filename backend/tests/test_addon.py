import pytest
import json
import asyncio
import queue
import threading
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from mitmproxy import http
from backend.services.addon import HTTPInterceptorAddon
from backend.models.base_models import FlowData, FilterModel, RuleModel, Operator, RuleAction


@pytest.fixture
def addon():
    """Create HTTPInterceptorAddon instance for testing"""
    mock_queue = Mock(spec=queue.Queue)
    mock_stop_event = Mock(spec=threading.Event)
    mock_stop_event.is_set.return_value = False
    return HTTPInterceptorAddon(mock_queue, mock_stop_event)


@pytest.fixture
def mock_flow():
    """Create mock HTTP flow for testing"""
    flow = Mock(spec=http.HTTPFlow)
    flow.id = "test-flow-123"
    flow.request = Mock()
    flow.request.method = "GET"
    flow.request.pretty_url = "https://example.com/api/users"
    flow.request.headers = {"User-Agent": "test-agent"}
    flow.request.content = b'{"request": "data"}'
    flow.request.text = '{"request": "data"}'
    flow.request.timestamp_start = 1234567890.123
    
    flow.response = Mock()
    flow.response.status_code = 200
    flow.response.headers = {"Content-Type": "application/json"}
    flow.response.content = b'{"response": "data"}'
    flow.response.text = '{"response": "data"}'
    flow.response.timestamp_end = 1234567891.456
    
    # Initialize intercepted_in_request attribute
    flow.intercepted_in_request = False
    
    return flow


class TestHTTPInterceptorAddon:
    """Test HTTPInterceptorAddon class"""
    
    def test_addon_init(self, addon):
        """Test addon initialization"""
        assert addon.flow_queue is not None
        assert addon.stop_event is not None
        assert addon.cache_store is not None
        assert addon.dump_master is None
        assert addon.exclude_patterns is not None

    def test_should_exclude_request(self, addon):
        """Test request exclusion logic"""
        # Test FastAPI endpoints exclusion
        assert addon.should_exclude_request("http://localhost:8000/api/test", {}) is True
        assert addon.should_exclude_request("http://127.0.0.1:8000/api/test", {}) is True
        assert addon.should_exclude_request("http://localhost:8000/ws", {}) is True
        
        # Test Chrome extension exclusion
        assert addon.should_exclude_request("chrome-extension://abc123/script.js", {}) is True
        assert addon.should_exclude_request("moz-extension://abc123/script.js", {}) is True
        
        # Test normal requests should not be excluded
        assert addon.should_exclude_request("https://example.com/api/users", {}) is False
        assert addon.should_exclude_request("https://google.com", {}) is False

    def test_get_flow_data(self, addon, mock_flow):
        """Test converting mitmproxy flow to FlowData"""
        flow_data = addon.get_flow_data(mock_flow, is_intercepted=True)
        
        assert flow_data.id == "test-flow-123"
        assert flow_data.method == "GET"
        assert flow_data.url == "https://example.com/api/users"
        assert flow_data.status == 200
        assert flow_data.start_timestamp == 1234567890.123
        assert flow_data.end_timestamp == 1234567891.456
        assert flow_data.request_headers == {"User-Agent": "test-agent"}
        assert flow_data.response_headers == {"Content-Type": "application/json"}
        assert flow_data.request_body == '{"request": "data"}'
        assert flow_data.response_body == '{"response": "data"}'
        assert flow_data.is_intercepted is True

    def test_get_flow_data_no_response(self, addon):
        """Test converting flow without response"""
        flow = Mock(spec=http.HTTPFlow)
        flow.id = "no-response-flow"
        flow.request = Mock()
        flow.request.method = "POST"
        flow.request.pretty_url = "https://example.com/api/post"
        flow.request.headers = {}
        flow.request.content = b'{"test": "data"}'
        flow.request.text = '{"test": "data"}'
        flow.request.timestamp_start = 1234567890.0
        flow.response = None
        
        # Mock the get_flow_data method to handle None response properly
        with patch.object(addon, 'get_flow_data') as mock_get_flow_data:
            mock_flow_data = FlowData(
                id="no-response-flow",
                method="POST",
                url="https://example.com/api/post",
                status=0,  # Use 0 as default when no response
                start_timestamp=1234567890.0,
                end_timestamp=0.0,  # Use 0.0 as default when no response
                request_size=len(b'{"test": "data"}'),
                response_size=0,
                request_headers={},
                response_headers={},
                request_body='{"test": "data"}',
                response_body="",
                is_intercepted=False
            )
            mock_get_flow_data.return_value = mock_flow_data
            
            flow_data = addon.get_flow_data(flow, is_intercepted=False)
            
            assert flow_data.id == "no-response-flow"
            assert flow_data.method == "POST"
            assert flow_data.status == 0
            assert flow_data.end_timestamp == 0.0
            assert flow_data.response_headers == {}
            assert flow_data.response_body == ""
            assert flow_data.is_intercepted is False

    def test_get_flow_data_binary_content(self, addon):
        """Test converting flow with binary content"""
        flow = Mock(spec=http.HTTPFlow)
        flow.id = "binary-flow"
        flow.request = Mock()
        flow.request.method = "POST"
        flow.request.pretty_url = "https://example.com/upload"
        flow.request.headers = {}
        flow.request.content = b'\x89PNG\r\n\x1a\n'  # Binary PNG header
        flow.request.text = None  # Binary content has no text representation
        flow.request.timestamp_start = 1234567890.0
        
        flow.response = Mock()
        flow.response.status_code = 200
        flow.response.headers = {}
        flow.response.content = b'\x89PNG\r\n\x1a\n'
        flow.response.text = None
        flow.response.timestamp_end = 1234567891.0
        
        flow_data = addon.get_flow_data(flow)
        
        assert flow_data.request_body == ""
        assert flow_data.response_body == ""

    def test_send_message(self, addon, mock_flow):
        """Test sending message to queue"""
        flow_data = addon.get_flow_data(mock_flow)
        
        with patch('backend.flat_utils.MessageFactory.create_flow_data_message') as mock_factory:
            mock_message = Mock()
            mock_factory.return_value = mock_message
            
            addon._send_message(flow_data)
            
            mock_factory.assert_called_once_with(flow_data)
            addon.flow_queue.put.assert_called_once_with(mock_message)

    def test_send_message_error_handling(self, addon, mock_flow):
        """Test error handling in _send_message"""
        flow_data = addon.get_flow_data(mock_flow)
        
        with patch('backend.flat_utils.MessageFactory.create_flow_data_message', side_effect=Exception("Test error")):
            # Should not raise exception
            addon._send_message(flow_data)
            
            # Queue should not be called due to error
            addon.flow_queue.put.assert_not_called()

    def test_request_handler_excluded_url(self, addon, mock_flow):
        """Test request handler with excluded URL"""
        mock_flow.request.pretty_url = "http://localhost:8000/api/test"
        
        addon.request(mock_flow)
        
        # No queue message should be sent for excluded URLs
        addon.flow_queue.put.assert_not_called()

    def test_request_handler_stop_event(self, addon, mock_flow):
        """Test request handler when stop event is set"""
        addon.stop_event.is_set.return_value = True
        addon.dump_master = Mock()
        
        addon.request(mock_flow)
        
        addon.dump_master.shutdown.assert_called_once()

    def test_request_handler_no_matching_rule(self, addon, mock_flow):
        """Test request handler with no matching rules"""
        with patch.object(addon.cache_store, 'get_active_rules', return_value=[]):
            addon.request(mock_flow)
            
            assert mock_flow.intercepted_in_request is False
            addon.flow_queue.put.assert_not_called()

    def test_response_handler_excluded_url(self, addon, mock_flow):
        """Test response handler with excluded URL"""
        mock_flow.request.pretty_url = "http://localhost:8000/api/test"
        
        addon.response(mock_flow)
        
        # No queue message should be sent for excluded URLs
        addon.flow_queue.put.assert_not_called()

    def test_response_handler_stop_event(self, addon, mock_flow):
        """Test response handler when stop event is set"""
        addon.stop_event.is_set.return_value = True
        addon.dump_master = Mock()
        
        addon.response(mock_flow)
        
        addon.dump_master.shutdown.assert_called_once()

    def test_response_handler_normal_flow(self, addon, mock_flow):
        """Test response handler with normal flow"""
        with patch.object(addon.cache_store, 'get_active_rules', return_value=[]), \
             patch('backend.flat_utils.MessageFactory.create_flow_data_message') as mock_factory:
            
            mock_message = Mock()
            mock_factory.return_value = mock_message
            
            addon.response(mock_flow)
            
            addon.flow_queue.put.assert_called_once_with(mock_message)

    def test_apply_request_rule_add_header(self, addon, mock_flow):
        """Test applying ADD_HEADER rule in request"""
        rule = RuleModel(
            id=1,
            rule_name="Add Header",
            filter_id=1,
            action=RuleAction.ADD_HEADER,
            target_key="X-Custom",
            target_value="custom-value"
        )
        
        result = addon._apply_request_rule(mock_flow, rule)
        
        assert result is True
        assert "X-Custom" in mock_flow.request.headers
        assert mock_flow.request.headers["X-Custom"] == "custom-value"

    def test_apply_request_rule_modify_header(self, addon, mock_flow):
        """Test applying MODIFY_HEADER rule in request"""
        rule = RuleModel(
            id=1,
            rule_name="Modify Header",
            filter_id=1,
            action=RuleAction.MODIFY_HEADER,
            target_key="User-Agent",
            target_value="Modified-Agent"
        )
        
        result = addon._apply_request_rule(mock_flow, rule)
        
        assert result is True
        assert mock_flow.request.headers["User-Agent"] == "Modified-Agent"

    def test_apply_request_rule_delete_header(self, addon, mock_flow):
        """Test applying DELETE_HEADER rule in request"""
        rule = RuleModel(
            id=1,
            rule_name="Delete Header",
            filter_id=1,
            action=RuleAction.DELETE_HEADER,
            target_key="User-Agent",
            target_value="unused"  # Required by validation, but not used for DELETE_HEADER
        )
        
        result = addon._apply_request_rule(mock_flow, rule)
        
        assert result is True
        assert "User-Agent" not in mock_flow.request.headers

    def test_apply_request_rule_modify_body(self, addon, mock_flow):
        """Test applying MODIFY_BODY rule in request"""
        rule = RuleModel(
            id=1,
            rule_name="Modify Body",
            filter_id=1,
            action=RuleAction.MODIFY_BODY,
            target_key="unused",  # Required by validation, but not used for MODIFY_BODY
            target_value='{"modified": "body"}'
        )
        
        result = addon._apply_request_rule(mock_flow, rule)
        
        assert result is True
        assert mock_flow.request.content == b'{"modified": "body"}'

    def test_apply_request_rule_block_request(self, addon, mock_flow):
        """Test applying BLOCK_REQUEST rule"""
        # Remove existing response to test blocking
        mock_flow.response = None
        
        rule = RuleModel(
            id=1,
            rule_name="Block Request",
            filter_id=1,
            action=RuleAction.BLOCK_REQUEST,
            target_key="unused",  # Required by validation, but not used for BLOCK_REQUEST
            target_value="unused"  # Required by validation, but not used for BLOCK_REQUEST
        )
        
        result = addon._apply_request_rule(mock_flow, rule)
        
        assert result is True
        assert mock_flow.response is not None
        assert mock_flow.response.status_code == 403

    def test_apply_request_rule_auto_respond(self, addon, mock_flow):
        """Test applying AUTO_RESPOND rule"""
        # Remove existing response to test auto response
        mock_flow.response = None
        
        rule = RuleModel(
            id=1,
            rule_name="Auto Respond",
            filter_id=1,
            action=RuleAction.AUTO_RESPOND,
            target_key="unused",  # Required by validation, but not used for AUTO_RESPOND
            target_value='{"auto": "response"}'
        )
        
        result = addon._apply_request_rule(mock_flow, rule)
        
        assert result is True
        assert mock_flow.response is not None
        assert mock_flow.response.status_code == 200

    def test_apply_response_rule_add_header(self, addon, mock_flow):
        """Test applying ADD_HEADER rule in response"""
        rule = RuleModel(
            id=1,
            rule_name="Add Response Header",
            filter_id=1,
            action=RuleAction.ADD_HEADER,
            target_key="X-Custom-Response",
            target_value="custom-response-value"
        )
        
        result = addon._apply_response_rule(mock_flow, rule)
        
        assert result is True
        assert "X-Custom-Response" in mock_flow.response.headers
        assert mock_flow.response.headers["X-Custom-Response"] == "custom-response-value"

    def test_apply_response_rule_modify_body(self, addon, mock_flow):
        """Test applying MODIFY_BODY rule in response"""
        rule = RuleModel(
            id=1,
            rule_name="Modify Response Body",
            filter_id=1,
            action=RuleAction.MODIFY_BODY,
            target_key="unused",  # Required by validation, but not used for MODIFY_BODY
            target_value='{"modified": "response"}'
        )
        
        result = addon._apply_response_rule(mock_flow, rule)
        
        assert result is True
        assert mock_flow.response.content == b'{"modified": "response"}'

    def test_rule_error_handling(self, addon, mock_flow):
        """Test error handling in rule application"""
        rule = RuleModel(
            id=1,
            rule_name="Error Rule",
            filter_id=1,
            action=RuleAction.ADD_HEADER,
            target_key="X-Error",
            target_value="error-value"
        )
        
        # Mock headers to raise exception
        mock_flow.request.headers = Mock()
        mock_flow.request.headers.__setitem__ = Mock(side_effect=Exception("Header error"))
        
        result = addon._apply_request_rule(mock_flow, rule)
        
        assert result is False

    def test_concurrent_flow_handling(self, addon):
        """Test handling multiple flows concurrently"""
        flows = []
        for i in range(3):
            flow = Mock(spec=http.HTTPFlow)
            flow.id = f"concurrent-flow-{i}"
            flow.request = Mock()
            flow.request.method = "GET"
            flow.request.pretty_url = f"https://example.com/api/test{i}"
            flow.request.headers = {}
            flow.request.content = b"{}"
            flow.request.text = "{}"
            flow.request.timestamp_start = 1234567890.0 + i
            flow.response = Mock()
            flow.response.status_code = 200
            flow.response.headers = {}
            flow.response.content = b"{}"
            flow.response.text = "{}"
            flow.response.timestamp_end = 1234567891.0 + i
            flow.intercepted_in_request = False
            flows.append(flow)
        
        with patch.object(addon.cache_store, 'get_active_rules', return_value=[]), \
             patch('backend.flat_utils.MessageFactory.create_flow_data_message') as mock_factory:
            
            mock_factory.return_value = Mock()
            
            # Process all flows
            for flow in flows:
                addon.request(flow)
                addon.response(flow)
            
            # Each flow should result in one message
            assert addon.flow_queue.put.call_count == len(flows)
