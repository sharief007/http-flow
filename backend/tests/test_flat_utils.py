import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.models.flat_utils import (
    MessageFactory, 
    FlowDataBuilder, 
    FilterModelBuilder, 
    RuleModelBuilder,
    HeaderPairBuilder,
    HeadersVectorBuilder,
    create_flow_message,
    create_server_started_message,
    create_server_stopped_message
)
from backend.models.base_models import FlowData, FilterModel, RuleModel, Operator, RuleAction


class TestMessageFactory:
    """Test MessageFactory class"""
    
    def test_create_flow_data_message(self):
        """Test creating flow data message"""
        flow_data = FlowData(
            id="test-flow-123",
            method="GET",
            url="https://example.com/api/users",
            status=200,
            start_timestamp=1234567890.123,
            end_timestamp=1234567891.456,
            request_size=512,
            response_size=1024,
            request_headers={"User-Agent": "test-agent", "Accept": "application/json"},
            response_headers={"Content-Type": "application/json", "Cache-Control": "no-cache"},
            request_body='{"query": "users"}',
            response_body='{"users": [{"id": 1, "name": "John"}]}',
            is_intercepted=False
        )
        
        # Create message using MessageFactory
        buffer_data = MessageFactory.create_flow_data_message(flow_data)
        
        assert isinstance(buffer_data, bytes)
        assert len(buffer_data) > 0

    def test_create_filter_message(self):
        """Test creating filter message"""
        filter_model = FilterModel(
            id=42,
            filter_name="API Endpoint Filter",
            field="url",
            operator=Operator.CONTAINS,
            value="/api/"
        )
        
        buffer_data = MessageFactory.create_filter_message(filter_model)
        
        assert isinstance(buffer_data, bytes)
        assert len(buffer_data) > 0

    def test_create_rule_message(self):
        """Test creating rule message"""
        rule_model = RuleModel(
            id=123,
            rule_name="Add Custom Header",
            filter_id=42,
            action=RuleAction.ADD_HEADER,
            target_key="X-Custom-Header",
            target_value="custom-value",
            enabled=True
        )
        
        buffer_data = MessageFactory.create_rule_message(rule_model)
        
        assert isinstance(buffer_data, bytes)
        assert len(buffer_data) > 0

    def test_create_server_event_message(self):
        """Test creating server event message"""
        buffer_data = MessageFactory.create_server_event_message("started", 8080)
        
        assert isinstance(buffer_data, bytes)
        assert len(buffer_data) > 0

    def test_create_full_sync_message(self):
        """Test creating full sync message"""
        rules = [
            RuleModel(
                id=1,
                rule_name="Test Rule 1",
                filter_id=1,
                action=RuleAction.ADD_HEADER,
                target_key="X-Test-1",
                target_value="value-1",
                enabled=True
            ),
            RuleModel(
                id=2,
                rule_name="Test Rule 2",
                filter_id=2,
                action=RuleAction.MODIFY_HEADER,
                target_key="User-Agent",
                target_value="Modified-Agent",
                enabled=False
            )
        ]
        
        filters = [
            FilterModel(
                id=1,
                filter_name="API Filter",
                field="url",
                operator=Operator.CONTAINS,
                value="/api/"
            ),
            FilterModel(
                id=2,
                filter_name="Method Filter",
                field="method",
                operator=Operator.EQUALS,
                value="POST"
            )
        ]
        
        buffer_data = MessageFactory.create_full_sync_message(rules, filters)
        
        assert isinstance(buffer_data, bytes)
        assert len(buffer_data) > 0


class TestFlowDataBuilder:
    """Test FlowDataBuilder class"""
    
    def test_build_flow_data(self):
        """Test building flow data"""
        flow_data = FlowData(
            id="builder-test",
            method="POST",
            url="https://api.example.com/posts",
            status=201,
            start_timestamp=1234567890.0,
            end_timestamp=1234567891.0,
            request_size=256,
            response_size=128,
            request_headers={"Content-Type": "application/json"},
            response_headers={"Location": "https://api.example.com/posts/123"},
            request_body='{"title": "New Post"}',
            response_body='{"id": 123, "title": "New Post"}',
            is_intercepted=True
        )
        
        builder = FlowDataBuilder(flow_data)
        buffer_offset = builder.build()
        
        # Builder returns an offset (integer), not bytes
        assert isinstance(buffer_offset, int)
        assert buffer_offset > 0

    def test_build_minimal_flow_data(self):
        """Test building minimal flow data"""
        minimal_flow = FlowData(
            id="minimal",
            method="GET",
            url="https://minimal.com",
            status=200,
            start_timestamp=0.0,
            end_timestamp=0.0,
            request_size=0,
            response_size=0,
            request_headers={},
            response_headers={},
            request_body="",
            response_body="",
            is_intercepted=False
        )
        
        builder = FlowDataBuilder(minimal_flow)
        buffer_offset = builder.build()
        
        # Builder returns an offset (integer), not bytes
        assert isinstance(buffer_offset, int)
        assert buffer_offset > 0

    def test_build_unicode_flow_data(self):
        """Test building flow data with Unicode characters"""
        unicode_flow = FlowData(
            id="unicode-test",
            method="POST",
            url="https://example.com/unicode/测试",
            status=200,
            start_timestamp=1234567890.0,
            end_timestamp=1234567891.0,
            request_size=100,
            response_size=200,
            request_headers={"Content-Type": "application/json; charset=utf-8"},
            response_headers={"Content-Language": "zh-CN"},
            request_body='{"message": "Hello 世界", "emoji": "🌍"}',
            response_body='{"response": "成功", "status": "✅"}',
            is_intercepted=False
        )
        
        builder = FlowDataBuilder(unicode_flow)
        buffer_offset = builder.build()
        
        # Builder returns an offset (integer), not bytes
        assert isinstance(buffer_offset, int)
        assert buffer_offset > 0


class TestFilterModelBuilder:
    """Test FilterModelBuilder class"""
    
    def test_build_filter_model(self):
        """Test building filter model"""
        filter_model = FilterModel(
            id=99,
            filter_name="Method Filter",
            field="method",
            operator=Operator.EQUALS,
            value="POST"
        )
        
        builder = FilterModelBuilder(filter_model)
        buffer_offset = builder.build()
        
        # Builder returns an offset (integer), not bytes
        assert isinstance(buffer_offset, int)
        assert buffer_offset > 0

    def test_build_regex_filter(self):
        """Test building regex filter model"""
        regex_filter = FilterModel(
            id=100,
            filter_name="Regex Filter",
            field="url",
            operator=Operator.REGEX,
            value=r"^https://api\.example\.com/v\d+/"
        )
        
        builder = FilterModelBuilder(regex_filter)
        buffer_offset = builder.build()
        
        # Builder returns an offset (integer), not bytes
        assert isinstance(buffer_offset, int)
        assert buffer_offset > 0


class TestRuleModelBuilder:
    """Test RuleModelBuilder class"""
    
    def test_build_rule_model(self):
        """Test building rule model"""
        rule_model = RuleModel(
            id=456,
            rule_name="Block Requests",
            filter_id=99,
            action=RuleAction.BLOCK_REQUEST,
            target_key="unused",
            target_value="unused",
            enabled=False
        )
        
        builder = RuleModelBuilder(rule_model)
        buffer_offset = builder.build()
        
        # Builder returns an offset (integer), not bytes
        assert isinstance(buffer_offset, int)
        assert buffer_offset > 0

    def test_build_header_rule(self):
        """Test building header manipulation rule"""
        header_rule = RuleModel(
            id=789,
            rule_name="Add Authorization Header",
            filter_id=1,
            action=RuleAction.ADD_HEADER,
            target_key="Authorization",
            target_value="Bearer token123",
            enabled=True
        )
        
        builder = RuleModelBuilder(header_rule)
        buffer_offset = builder.build()
        
        # Builder returns an offset (integer), not bytes
        assert isinstance(buffer_offset, int)
        assert buffer_offset > 0


class TestHeadersVectorBuilder:
    """Test HeadersVectorBuilder class"""
    
    def test_build_headers_vector(self):
        """Test building headers vector"""
        import flatbuffers
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "test-agent",
            "Accept": "application/json"
        }
        
        builder = flatbuffers.Builder(1024)
        headers_builder = HeadersVectorBuilder(headers, builder)
        headers_vector = headers_builder.build()
        
        assert headers_vector is not None

    def test_build_empty_headers_vector(self):
        """Test building empty headers vector"""
        import flatbuffers
        
        headers = {}
        
        builder = flatbuffers.Builder(1024)
        headers_builder = HeadersVectorBuilder(headers, builder)
        headers_vector = headers_builder.build()
        
        # Empty headers returns None as expected
        assert headers_vector is None

    def test_build_large_headers_vector(self):
        """Test building large headers vector"""
        import flatbuffers
        
        # Create a large headers dictionary
        headers = {f"Header-{i}": f"Value-{i}" * 10 for i in range(50)}
        
        builder = flatbuffers.Builder(1024)
        headers_builder = HeadersVectorBuilder(headers, builder)
        headers_vector = headers_builder.build()
        
        assert headers_vector is not None


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_create_flow_message(self):
        """Test create_flow_message convenience function"""
        flow_data = FlowData(
            id="convenience-test",
            method="GET",
            url="https://example.com/test",
            status=200,
            start_timestamp=1234567890.0,
            end_timestamp=1234567891.0,
            request_size=100,
            response_size=200,
            request_headers={"User-Agent": "test"},
            response_headers={"Content-Type": "application/json"},
            request_body="",
            response_body='{"result": "success"}',
            is_intercepted=False
        )
        
        buffer_data = create_flow_message(flow_data)
        
        assert isinstance(buffer_data, bytes)
        assert len(buffer_data) > 0

    def test_create_server_started_message(self):
        """Test create_server_started_message convenience function"""
        buffer_data = create_server_started_message(8080)
        
        assert isinstance(buffer_data, bytes)
        assert len(buffer_data) > 0

    def test_create_server_stopped_message(self):
        """Test create_server_stopped_message convenience function"""
        buffer_data = create_server_stopped_message(8080)
        
        assert isinstance(buffer_data, bytes)
        assert len(buffer_data) > 0


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_invalid_flow_data(self):
        """Test handling invalid flow data"""
        # This test verifies that the builders handle edge cases gracefully
        try:
            flow_data = FlowData(
                id="",  # Empty ID
                method="INVALID_METHOD",
                url="not-a-valid-url",
                status=-1,  # Invalid status
                start_timestamp=-1.0,
                end_timestamp=-1.0,
                request_size=-1,
                response_size=-1,
                request_headers={},
                response_headers={},
                request_body="",
                response_body="",
                is_intercepted=False
            )
            
            buffer_data = create_flow_message(flow_data)
            assert isinstance(buffer_data, bytes)
            
        except Exception as e:
            # If validation fails, that's also acceptable behavior
            assert isinstance(e, (ValueError, TypeError))

    def test_builder_reuse(self):
        """Test that builders can be reused"""
        flow_data1 = FlowData(
            id="reuse-test-1",
            method="GET",
            url="https://example.com/1",
            status=200,
            start_timestamp=1234567890.0,
            end_timestamp=1234567891.0,
            request_size=100,
            response_size=200,
            request_headers={},
            response_headers={},
            request_body="",
            response_body="",
            is_intercepted=False
        )
        
        flow_data2 = FlowData(
            id="reuse-test-2",
            method="POST",
            url="https://example.com/2",
            status=201,
            start_timestamp=1234567892.0,
            end_timestamp=1234567893.0,
            request_size=150,
            response_size=250,
            request_headers={},
            response_headers={},
            request_body="",
            response_body="",
            is_intercepted=True
        )
        
        # Create multiple messages
        buffer1 = create_flow_message(flow_data1)
        buffer2 = create_flow_message(flow_data2)
        
        assert isinstance(buffer1, bytes)
        assert isinstance(buffer2, bytes)
        assert len(buffer1) > 0
        assert len(buffer2) > 0


class TestPerformance:
    """Test performance characteristics"""
    
    def test_message_creation_performance(self):
        """Test message creation performance with multiple objects"""
        import time
        
        # Create a batch of flows
        flows = [
            FlowData(
                id=f"perf-test-{i}",
                method=["GET", "POST", "PUT", "DELETE"][i % 4],
                url=f"https://api.example.com/endpoint/{i}",
                status=[200, 201, 204, 404][i % 4],
                start_timestamp=1234567890.0 + i,
                end_timestamp=1234567891.0 + i,
                request_size=100 + i,
                response_size=200 + i,
                request_headers={f"Header-{i}": f"value-{i}"},
                response_headers={f"Response-{i}": f"response-{i}"},
                request_body=f'{{"request": {i}}}',
                response_body=f'{{"response": {i}}}',
                is_intercepted=i % 2 == 0
            )
            for i in range(100)
        ]
        
        # Measure message creation time
        start_time = time.time()
        buffers = [create_flow_message(flow) for flow in flows]
        creation_time = time.time() - start_time
        
        # Verify all messages were created
        assert len(buffers) == 100
        assert all(isinstance(buffer, bytes) and len(buffer) > 0 for buffer in buffers)
        
        # Performance should be reasonable (less than 2 seconds for 100 objects)
        assert creation_time < 2.0

    def test_large_data_handling(self):
        """Test handling large data efficiently"""
        large_body = "x" * 50000  # 50KB of data
        large_headers = {f"Header-{i}": f"Value-{i}" * 100 for i in range(100)}
        
        large_flow = FlowData(
            id="large-data-test",
            method="POST",
            url="https://example.com/large",
            status=200,
            start_timestamp=1234567890.0,
            end_timestamp=1234567891.0,
            request_size=len(large_body),
            response_size=len(large_body),
            request_headers=large_headers,
            response_headers=large_headers.copy(),
            request_body=large_body,
            response_body=large_body,
            is_intercepted=True
        )
        
        import time
        start_time = time.time()
        buffer_data = create_flow_message(large_flow)
        creation_time = time.time() - start_time
        
        assert isinstance(buffer_data, bytes)
        assert len(buffer_data) > 0
        # Should handle large data reasonably quickly
        assert creation_time < 1.0

