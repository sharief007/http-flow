import pytest
from unittest.mock import Mock, patch
from mitmproxy import http
from pydantic import ValidationError
from backend.models.base_models import (
    FlowData, FilterModel, RuleModel, 
    Operator, RuleAction, OperationType, SyncMessage
)


class TestFlowData:
    """Test FlowData model"""
    
    def test_flow_data_creation(self):
        """Test FlowData model creation"""
        flow_data = FlowData(
            id="test-123",
            method="GET",
            url="https://example.com/api/users",
            status=200,
            start_timestamp=1234567890.123,
            end_timestamp=1234567891.456,
            request_size=512,
            response_size=1024,
            request_headers={"User-Agent": "test"},
            response_headers={"Content-Type": "application/json"},
            request_body="",
            response_body='{"users": []}',
            is_intercepted=False
        )
        
        assert flow_data.id == "test-123"
        assert flow_data.method == "GET"
        assert flow_data.url == "https://example.com/api/users"
        assert flow_data.status == 200
        assert flow_data.start_timestamp == 1234567890.123
        assert flow_data.end_timestamp == 1234567891.456
        assert flow_data.request_size == 512
        assert flow_data.response_size == 1024
        assert flow_data.request_headers == {"User-Agent": "test"}
        assert flow_data.response_headers == {"Content-Type": "application/json"}
        assert flow_data.request_body == ""
        assert flow_data.response_body == '{"users": []}'
        assert flow_data.is_intercepted is False

    def test_flow_data_validation(self):
        """Test FlowData validation"""
        # Test with minimal valid data
        flow_data = FlowData(
            id="test",
            method="POST",
            url="https://api.test.com",
            status=201,
            start_timestamp=1234567890.0,
            end_timestamp=1234567891.0,
            request_size=0,
            response_size=0,
            request_headers={},
            response_headers={},
            request_body="",
            response_body="",
            is_intercepted=True
        )
        
        assert flow_data.method == "POST"
        assert flow_data.status == 201
        assert flow_data.is_intercepted is True


class TestOperator:
    """Test Operator enum"""
    
    def test_operator_values(self):
        """Test Operator enum values"""
        assert Operator.CONTAINS.value == 0
        assert Operator.EQUALS.value == 1
        assert Operator.STARTS_WITH.value == 2
        assert Operator.ENDS_WITH.value == 3
        assert Operator.REGEX.value == 4

    def test_operator_from_int(self):
        """Test Operator from_int method"""
        assert Operator.from_int(0) == Operator.CONTAINS
        assert Operator.from_int(1) == Operator.EQUALS
        assert Operator.from_int(2) == Operator.STARTS_WITH
        assert Operator.from_int(3) == Operator.ENDS_WITH
        assert Operator.from_int(4) == Operator.REGEX

    def test_operator_from_int_invalid(self):
        """Test Operator from_int with invalid value"""
        with pytest.raises(ValueError, match="999 is not a valid Operator"):
            Operator.from_int(999)


class TestFilterModel:
    """Test FilterModel"""
    
    def test_filter_creation(self):
        """Test FilterModel creation"""
        filter_model = FilterModel(
            filter_name="API Filter",
            field="url",
            operator=Operator.CONTAINS,
            value="api"
        )
        
        assert filter_model.filter_name == "API Filter"
        assert filter_model.field == "url"
        assert filter_model.operator == Operator.CONTAINS
        assert filter_model.value == "api"
        assert filter_model.id is None

    def test_filter_with_id(self):
        """Test FilterModel with ID"""
        filter_model = FilterModel(
            id=123,
            filter_name="Test Filter",
            field="method",
            operator=Operator.EQUALS,
            value="GET"
        )
        
        assert filter_model.id == 123

    def test_filter_validation_empty_name(self):
        """Test FilterModel validation with empty name"""
        with pytest.raises(ValidationError, match="This field is required and cannot be empty"):
            FilterModel(
                filter_name="",
                field="url",
                operator=Operator.CONTAINS,
                value="test"
            )

    def test_filter_validation_empty_field(self):
        """Test FilterModel validation with empty field"""
        with pytest.raises(ValidationError, match="This field is required and cannot be empty"):
            FilterModel(
                filter_name="Test",
                field="",
                operator=Operator.CONTAINS,
                value="test"
            )

    def test_filter_validation_empty_value(self):
        """Test FilterModel validation with empty value"""
        with pytest.raises(ValidationError, match="This field is required and cannot be empty"):
            FilterModel(
                filter_name="Test",
                field="url",
                operator=Operator.CONTAINS,
                value=""
            )

    def test_filter_evaluate_contains(self):
        """Test FilterModel evaluate with CONTAINS operator"""
        filter_model = FilterModel(
            filter_name="URL Filter",
            field="url",
            operator=Operator.CONTAINS,
            value="api"
        )
        
        # Create mock flow
        mock_flow = Mock(spec=http.HTTPFlow)
        mock_flow.request = Mock()
        mock_flow.request.pretty_url = "https://example.com/api/users"
        
        result = filter_model.evaluate(mock_flow)
        assert result is True
        
        # Test negative case
        mock_flow.request.pretty_url = "https://example.com/web/users"
        result = filter_model.evaluate(mock_flow)
        assert result is False

    def test_filter_evaluate_equals(self):
        """Test FilterModel evaluate with EQUALS operator"""
        filter_model = FilterModel(
            filter_name="Method Filter",
            field="method",
            operator=Operator.EQUALS,
            value="GET"
        )
        
        mock_flow = Mock(spec=http.HTTPFlow)
        mock_flow.request = Mock()
        mock_flow.request.method = "GET"
        
        result = filter_model.evaluate(mock_flow)
        assert result is True
        
        # Test negative case
        mock_flow.request.method = "POST"
        result = filter_model.evaluate(mock_flow)
        assert result is False

    def test_filter_evaluate_starts_with(self):
        """Test FilterModel evaluate with STARTS_WITH operator"""
        filter_model = FilterModel(
            filter_name="URL Starts Filter",
            field="url",
            operator=Operator.STARTS_WITH,
            value="https://api"
        )
        
        mock_flow = Mock(spec=http.HTTPFlow)
        mock_flow.request = Mock()
        mock_flow.request.pretty_url = "https://api.example.com/users"
        
        result = filter_model.evaluate(mock_flow)
        assert result is True

    def test_filter_evaluate_ends_with(self):
        """Test FilterModel evaluate with ENDS_WITH operator"""
        filter_model = FilterModel(
            filter_name="URL Ends Filter",
            field="url",
            operator=Operator.ENDS_WITH,
            value="/users"
        )
        
        mock_flow = Mock(spec=http.HTTPFlow)
        mock_flow.request = Mock()
        mock_flow.request.pretty_url = "https://example.com/api/users"
        
        result = filter_model.evaluate(mock_flow)
        assert result is True

    def test_filter_evaluate_regex(self):
        """Test FilterModel evaluate with REGEX operator"""
        filter_model = FilterModel(
            filter_name="Regex Filter",
            field="url",
            operator=Operator.REGEX,
            value=r"https://\w+\.com"
        )
        
        mock_flow = Mock(spec=http.HTTPFlow)
        mock_flow.request = Mock()
        mock_flow.request.pretty_url = "https://example.com/api"
        
        result = filter_model.evaluate(mock_flow)
        assert result is True

    def test_filter_evaluate_header_field(self):
        """Test FilterModel evaluate with header field"""
        filter_model = FilterModel(
            filter_name="Header Filter",
            field="header:User-Agent",
            operator=Operator.CONTAINS,
            value="Mozilla"
        )
        
        mock_flow = Mock(spec=http.HTTPFlow)
        mock_flow.request = Mock()
        mock_flow.request.headers = {"User-Agent": "Mozilla/5.0"}
        
        result = filter_model.evaluate(mock_flow)
        assert result is True

    def test_filter_evaluate_invalid_field(self):
        """Test FilterModel evaluate with invalid field"""
        filter_model = FilterModel(
            filter_name="Invalid Filter",
            field="invalid_field",
            operator=Operator.EQUALS,
            value="test"
        )
        
        mock_flow = Mock(spec=http.HTTPFlow)
        
        result = filter_model.evaluate(mock_flow)
        assert result is False


class TestRuleAction:
    """Test RuleAction enum"""
    
    def test_rule_action_values(self):
        """Test RuleAction enum values"""
        assert RuleAction.ADD_HEADER.value == 0
        assert RuleAction.MODIFY_HEADER.value == 1
        assert RuleAction.DELETE_HEADER.value == 2
        assert RuleAction.MODIFY_BODY.value == 3
        assert RuleAction.BLOCK_REQUEST.value == 4
        assert RuleAction.AUTO_RESPOND.value == 5

    def test_rule_action_from_int(self):
        """Test RuleAction from_int method"""
        assert RuleAction.from_int(0) == RuleAction.ADD_HEADER
        assert RuleAction.from_int(1) == RuleAction.MODIFY_HEADER
        assert RuleAction.from_int(2) == RuleAction.DELETE_HEADER
        assert RuleAction.from_int(3) == RuleAction.MODIFY_BODY
        assert RuleAction.from_int(4) == RuleAction.BLOCK_REQUEST
        assert RuleAction.from_int(5) == RuleAction.AUTO_RESPOND

    def test_rule_action_from_int_invalid(self):
        """Test RuleAction from_int with invalid value"""
        with pytest.raises(ValueError, match="999 is not a valid RuleAction"):
            RuleAction.from_int(999)


class TestRuleModel:
    """Test RuleModel"""
    
    def test_rule_creation(self):
        """Test RuleModel creation"""
        rule = RuleModel(
            rule_name="Add Test Header",
            filter_id=1,
            action=RuleAction.ADD_HEADER,
            target_key="X-Test",
            target_value="test-value",
            enabled=True
        )
        
        assert rule.rule_name == "Add Test Header"
        assert rule.filter_id == 1
        assert rule.action == RuleAction.ADD_HEADER
        assert rule.target_key == "X-Test"
        assert rule.target_value == "test-value"
        assert rule.enabled is True
        assert rule.id is None

    def test_rule_with_id(self):
        """Test RuleModel with ID"""
        rule = RuleModel(
            id=456,
            rule_name="Test Rule",
            filter_id=1,
            action=RuleAction.MODIFY_HEADER,
            target_key="Content-Type",
            target_value="application/json",
            enabled=False
        )
        
        assert rule.id == 456
        assert rule.enabled is False

    def test_rule_validation_empty_name(self):
        """Test RuleModel validation with empty name"""
        with pytest.raises(ValidationError, match="This field is required and cannot be empty"):
            RuleModel(
                rule_name="",
                filter_id=1,
                action=RuleAction.ADD_HEADER,
                target_key="X-Test",
                target_value="test"
            )

    def test_rule_validation_empty_target_key(self):
        """Test RuleModel validation with empty target key"""
        with pytest.raises(ValidationError, match="This field is required and cannot be empty"):
            RuleModel(
                rule_name="Test Rule", 
                filter_id=1,
                action=RuleAction.ADD_HEADER,
                target_key="",
                target_value="test"
            )

    def test_rule_validation_empty_target_value(self):
        """Test RuleModel validation with empty target value"""
        with pytest.raises(ValidationError, match="This field is required and cannot be empty"):
            RuleModel(
                rule_name="Test Rule",
                filter_id=1,
                action=RuleAction.ADD_HEADER,
                target_key="X-Test",
                target_value=""
            )


class TestOperationType:
    """Test OperationType enum"""
    
    def test_operation_type_values(self):
        """Test OperationType enum values"""
        assert OperationType.FULL_SYNC.value == 0
        assert OperationType.ADD.value == 1
        assert OperationType.UPDATE.value == 2
        assert OperationType.DELETE.value == 3


class TestSyncMessage:
    """Test SyncMessage model"""
    
    def test_sync_message_creation(self):
        """Test SyncMessage creation"""
        sync_msg = SyncMessage(
            operation=OperationType.FULL_SYNC,
            rules_list=[],
            filters_data=[]
        )
        
        assert sync_msg.operation == OperationType.FULL_SYNC
        assert sync_msg.rules_list == []
        assert sync_msg.filters_data == []

    def test_sync_message_with_data(self):
        """Test SyncMessage with rules and filters"""
        rule = RuleModel(
            rule_name="Test Rule",
            filter_id=1,
            action=RuleAction.ADD_HEADER,
            target_key="X-Test",
            target_value="test"
        )
        
        filter_model = FilterModel(
            filter_name="Test Filter",
            field="url",
            operator=Operator.CONTAINS,
            value="api"
        )
        
        sync_msg = SyncMessage(
            operation=OperationType.ADD,
            rules_list=[rule],
            filters_data=[filter_model]
        )
        
        assert sync_msg.operation == OperationType.ADD
        assert len(sync_msg.rules_list) == 1
        assert len(sync_msg.filters_data) == 1
        assert sync_msg.rules_list[0] == rule
        assert sync_msg.filters_data[0] == filter_model
