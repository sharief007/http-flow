
"""
FlatBuffer Serialization/Deserialization Utilities

This module provides clean utilities for converting between Python models 
and FlatBuffer objects, supporting both serialization and deserialization.
"""
import flatbuffers
import time
from typing import Dict, Optional, List, Any
from abc import ABC, abstractmethod

# Import the generated FlatBuffer classes
from backend.models.backend_generated import (
    # Classes
    FilterModel, RuleModel, SyncMessage,
    # Enums
    Operator, RuleAction, OperationType,
    # Builder functions
    FilterModelStart, FilterModelEnd, FilterModelAddId, FilterModelAddFilterName,
    FilterModelAddField, FilterModelAddOperator, FilterModelAddValue,
    RuleModelStart, RuleModelEnd, RuleModelAddId, RuleModelAddRuleName,
    RuleModelAddFilterId, RuleModelAddAction, RuleModelAddTargetKey,
    RuleModelAddTargetValue, RuleModelAddEnabled,
    SyncMessageStart, SyncMessageEnd, SyncMessageAddOperation, SyncMessageAddRulesList,
    SyncMessageAddFiltersData, SyncMessageAddTimestamp, SyncMessageStartRulesListVector,
    SyncMessageStartFiltersDataVector
)

# Import WebSocket event classes
from backend.models.events_generated import (
    # Classes
    HeaderPair, FlowData, ServerEvent, WebSocketMessage,
    # Enums
    WebSocketMessageType,
    # Builder functions
    HeaderPairStart, HeaderPairEnd, HeaderPairAddKey, HeaderPairAddValue,
    FlowDataStart, FlowDataEnd, FlowDataAddId, FlowDataAddMethod, FlowDataAddUrl,
    FlowDataAddStatus, FlowDataAddStartTimestamp, FlowDataAddEndTimestamp,
    FlowDataAddRequestSize, FlowDataAddResponseSize, FlowDataAddRequestHeaders,
    FlowDataAddResponseHeaders, FlowDataAddRequestBody, FlowDataAddResponseBody,
    FlowDataAddIsIntercepted, FlowDataStartRequestHeadersVector, FlowDataStartResponseHeadersVector,
    ServerEventStart, ServerEventEnd, ServerEventAddStatus, ServerEventAddPort,
    WebSocketMessageStart, WebSocketMessageEnd, WebSocketMessageAddType,
    WebSocketMessageAddDataType, WebSocketMessageAddData
)

# Import your Python models
from backend.models.base_models import (
    FlowData as PyFlowData, FilterModel as PyFilterModel, 
    RuleModel as PyRuleModel, SyncMessage as PySyncMessage,
    OperationType as PyOperationType, Operator as PyOperator, RuleAction as PyRuleAction
)

# ============= ENUM MAPPINGS =============

PYTHON_TO_FB_OPERATOR = {
    PyOperator.CONTAINS: Operator.CONTAINS,
    PyOperator.EQUALS: Operator.EQUALS,
    PyOperator.STARTS_WITH: Operator.STARTS_WITH,
    PyOperator.ENDS_WITH: Operator.ENDS_WITH,
    PyOperator.REGEX: Operator.REGEX,
}

FB_TO_PYTHON_OPERATOR = {v: k for k, v in PYTHON_TO_FB_OPERATOR.items()}

PYTHON_TO_FB_ACTION = {
    PyRuleAction.ADD_HEADER: RuleAction.ADD_HEADER,
    PyRuleAction.MODIFY_HEADER: RuleAction.MODIFY_HEADER,
    PyRuleAction.DELETE_HEADER: RuleAction.DELETE_HEADER,
    PyRuleAction.MODIFY_BODY: RuleAction.MODIFY_BODY,
    PyRuleAction.BLOCK_REQUEST: RuleAction.BLOCK_REQUEST,
    PyRuleAction.AUTO_RESPOND: RuleAction.AUTO_RESPOND,
}

FB_TO_PYTHON_ACTION = {v: k for k, v in PYTHON_TO_FB_ACTION.items()}

PYTHON_TO_FB_OPERATION = {
    PyOperationType.FULL_SYNC: OperationType.FULL_SYNC,
    PyOperationType.ADD: OperationType.ADD,
    PyOperationType.UPDATE: OperationType.UPDATE,
    PyOperationType.DELETE: OperationType.DELETE,
}

FB_TO_PYTHON_OPERATION = {v: k for k, v in PYTHON_TO_FB_OPERATION.items()}

# ============= SERIALIZATION UTILITIES =============

class FlatBufferSerializer:
    """Serializes Python models to FlatBuffer bytes"""
    
    def __init__(self):
        self.builder = flatbuffers.Builder()
    
    def _create_header_pair(self, key: str, value: str) -> int:
        """Create a HeaderPair FlatBuffer object"""
        key_fb = self.builder.CreateString(key)
        value_fb = self.builder.CreateString(value)
        
        HeaderPairStart(self.builder)
        HeaderPairAddKey(self.builder, key_fb)
        HeaderPairAddValue(self.builder, value_fb)
        return HeaderPairEnd(self.builder)
    
    def _create_headers_vector(self, headers: Dict[str, str]) -> Optional[int]:
        """Create a vector of HeaderPair objects"""
        if not headers:
            return None
        
        # Create all HeaderPair objects
        header_offsets = []
        for key, value in headers.items():
            header_offset = self._create_header_pair(key, value)
            header_offsets.append(header_offset)
        
        # Create vector (in reverse order)
        FlowDataStartRequestHeadersVector(self.builder, len(header_offsets))
        for offset in reversed(header_offsets):
            self.builder.PrependUOffsetTRelative(offset)
        return self.builder.EndVector(len(header_offsets))
    
    def serialize_flow_data(self, flow_data: PyFlowData) -> bytes:
        """Serialize FlowData to FlatBuffer bytes"""
        self.builder = flatbuffers.Builder()
        
        # Create strings
        id_fb = self.builder.CreateString(flow_data.id)
        method_fb = self.builder.CreateString(flow_data.method)
        url_fb = self.builder.CreateString(flow_data.url)
        request_body_fb = self.builder.CreateString(flow_data.request_body or "")
        response_body_fb = self.builder.CreateString(flow_data.response_body or "")
        
        # Create header vectors
        request_headers_fb = self._create_headers_vector(flow_data.request_headers)
        response_headers_fb = self._create_headers_vector(flow_data.response_headers)
        
        # Create FlowData
        FlowDataStart(self.builder)
        FlowDataAddId(self.builder, id_fb)
        FlowDataAddMethod(self.builder, method_fb)
        FlowDataAddUrl(self.builder, url_fb)
        FlowDataAddStatus(self.builder, flow_data.status)
        FlowDataAddStartTimestamp(self.builder, flow_data.start_timestamp)
        FlowDataAddEndTimestamp(self.builder, flow_data.end_timestamp)
        FlowDataAddRequestSize(self.builder, flow_data.request_size)
        FlowDataAddResponseSize(self.builder, flow_data.response_size)
        
        if request_headers_fb:
            FlowDataAddRequestHeaders(self.builder, request_headers_fb)
        if response_headers_fb:
            FlowDataAddResponseHeaders(self.builder, response_headers_fb)
        
        FlowDataAddRequestBody(self.builder, request_body_fb)
        FlowDataAddResponseBody(self.builder, response_body_fb)
        FlowDataAddIsIntercepted(self.builder, flow_data.is_intercepted)
        
        flow_offset = FlowDataEnd(self.builder)
        self.builder.Finish(flow_offset)
        return bytes(self.builder.Output())
    
    def serialize_filter_model(self, filter_model: PyFilterModel) -> bytes:
        """Serialize FilterModel to FlatBuffer bytes"""
        self.builder = flatbuffers.Builder()
        
        # Create strings
        filter_name_fb = self.builder.CreateString(filter_model.filter_name)
        field_fb = self.builder.CreateString(filter_model.field)
        value_fb = self.builder.CreateString(filter_model.value)
        
        # Convert enum
        operator_fb = PYTHON_TO_FB_OPERATOR.get(filter_model.operator, Operator.CONTAINS)
        
        FilterModelStart(self.builder)
        if filter_model.id is not None:
            FilterModelAddId(self.builder, filter_model.id)
        FilterModelAddFilterName(self.builder, filter_name_fb)
        FilterModelAddField(self.builder, field_fb)
        FilterModelAddOperator(self.builder, operator_fb)
        FilterModelAddValue(self.builder, value_fb)
        
        filter_offset = FilterModelEnd(self.builder)
        self.builder.Finish(filter_offset)
        return bytes(self.builder.Output())
    
    def serialize_rule_model(self, rule_model: PyRuleModel) -> bytes:
        """Serialize RuleModel to FlatBuffer bytes"""
        self.builder = flatbuffers.Builder()
        
        # Create strings
        rule_name_fb = self.builder.CreateString(rule_model.rule_name)
        target_key_fb = self.builder.CreateString(rule_model.target_key)
        target_value_fb = self.builder.CreateString(rule_model.target_value)
        
        # Convert enum
        action_fb = PYTHON_TO_FB_ACTION.get(rule_model.action, RuleAction.ADD_HEADER)
        
        RuleModelStart(self.builder)
        if rule_model.id is not None:
            RuleModelAddId(self.builder, rule_model.id)
        RuleModelAddRuleName(self.builder, rule_name_fb)
        RuleModelAddFilterId(self.builder, rule_model.filter_id)
        RuleModelAddAction(self.builder, action_fb)
        RuleModelAddTargetKey(self.builder, target_key_fb)
        RuleModelAddTargetValue(self.builder, target_value_fb)
        RuleModelAddEnabled(self.builder, rule_model.enabled)
        
        rule_offset = RuleModelEnd(self.builder)
        self.builder.Finish(rule_offset)
        return bytes(self.builder.Output())
    
    def _create_rules_vector(self, rules: List[PyRuleModel]) -> Optional[int]:
        """Create a vector of RuleModel objects"""
        if not rules:
            return None
        
        # Create all RuleModel objects
        rule_offsets = []
        for rule in rules:
            # Create strings
            rule_name_fb = self.builder.CreateString(rule.rule_name)
            target_key_fb = self.builder.CreateString(rule.target_key)
            target_value_fb = self.builder.CreateString(rule.target_value)
            
            # Convert enum
            action_fb = PYTHON_TO_FB_ACTION.get(rule.action, RuleAction.ADD_HEADER)
            
            RuleModelStart(self.builder)
            if rule.id is not None:
                RuleModelAddId(self.builder, rule.id)
            RuleModelAddRuleName(self.builder, rule_name_fb)
            RuleModelAddFilterId(self.builder, rule.filter_id)
            RuleModelAddAction(self.builder, action_fb)
            RuleModelAddTargetKey(self.builder, target_key_fb)
            RuleModelAddTargetValue(self.builder, target_value_fb)
            RuleModelAddEnabled(self.builder, rule.enabled)
            
            rule_offset = RuleModelEnd(self.builder)
            rule_offsets.append(rule_offset)
        
        # Create vector (in reverse order)
        SyncMessageStartRulesListVector(self.builder, len(rule_offsets))
        for offset in reversed(rule_offsets):
            self.builder.PrependUOffsetTRelative(offset)
        return self.builder.EndVector(len(rule_offsets))
    
    def _create_filters_vector(self, filters: List[PyFilterModel]) -> Optional[int]:
        """Create a vector of FilterModel objects"""
        if not filters:
            return None
        
        # Create all FilterModel objects
        filter_offsets = []
        for filter_model in filters:
            # Create strings
            filter_name_fb = self.builder.CreateString(filter_model.filter_name)
            field_fb = self.builder.CreateString(filter_model.field)
            value_fb = self.builder.CreateString(filter_model.value)
            
            # Convert enum
            operator_fb = PYTHON_TO_FB_OPERATOR.get(filter_model.operator, Operator.CONTAINS)
            
            FilterModelStart(self.builder)
            if filter_model.id is not None:
                FilterModelAddId(self.builder, filter_model.id)
            FilterModelAddFilterName(self.builder, filter_name_fb)
            FilterModelAddField(self.builder, field_fb)
            FilterModelAddOperator(self.builder, operator_fb)
            FilterModelAddValue(self.builder, value_fb)
            
            filter_offset = FilterModelEnd(self.builder)
            filter_offsets.append(filter_offset)
        
        # Create vector (in reverse order)
        SyncMessageStartFiltersDataVector(self.builder, len(filter_offsets))
        for offset in reversed(filter_offsets):
            self.builder.PrependUOffsetTRelative(offset)
        return self.builder.EndVector(len(filter_offsets))
    
    def serialize_sync_message(self, sync_message: PySyncMessage) -> bytes:
        """Serialize SyncMessage to FlatBuffer bytes"""
        self.builder = flatbuffers.Builder()
        
        # Convert enum
        operation_fb = PYTHON_TO_FB_OPERATION.get(sync_message.operation, OperationType.FULL_SYNC)
        
        # Create vectors
        rules_vector_fb = self._create_rules_vector(sync_message.rules_list)
        filters_vector_fb = self._create_filters_vector(sync_message.filters_data)
        
        SyncMessageStart(self.builder)
        SyncMessageAddOperation(self.builder, operation_fb)
        if rules_vector_fb:
            SyncMessageAddRulesList(self.builder, rules_vector_fb)
        if filters_vector_fb:
            SyncMessageAddFiltersData(self.builder, filters_vector_fb)
        SyncMessageAddTimestamp(self.builder, time.time())
        
        sync_offset = SyncMessageEnd(self.builder)
        self.builder.Finish(sync_offset)
        return bytes(self.builder.Output())
    
    def serialize_server_event(self, status: str, port: int) -> bytes:
        """Serialize ServerEvent to FlatBuffer bytes"""
        self.builder = flatbuffers.Builder()
        
        # Create string
        status_fb = self.builder.CreateString(status)
        
        ServerEventStart(self.builder)
        ServerEventAddStatus(self.builder, status_fb)
        ServerEventAddPort(self.builder, port)
        
        server_event_offset = ServerEventEnd(self.builder)
        self.builder.Finish(server_event_offset)
        return bytes(self.builder.Output())
    
    def serialize_websocket_message(self, message_type: str, data_type: int, data_offset: int) -> bytes:
        """Serialize WebSocketMessage to FlatBuffer bytes"""
        self.builder = flatbuffers.Builder()
        
        # Create string
        type_fb = self.builder.CreateString(message_type)
        
        WebSocketMessageStart(self.builder)
        WebSocketMessageAddType(self.builder, type_fb)
        WebSocketMessageAddDataType(self.builder, data_type)
        WebSocketMessageAddData(self.builder, data_offset)
        
        ws_message_offset = WebSocketMessageEnd(self.builder)
        self.builder.Finish(ws_message_offset)
        return bytes(self.builder.Output())
    
    def create_server_event_message(self, status: str, port: int) -> bytes:
        """Create a complete WebSocket message containing ServerEvent"""
        self.builder = flatbuffers.Builder()
        
        # Create ServerEvent first
        status_fb = self.builder.CreateString(status)
        
        ServerEventStart(self.builder)
        ServerEventAddStatus(self.builder, status_fb)
        ServerEventAddPort(self.builder, port)
        server_event_offset = ServerEventEnd(self.builder)
        
        # Create WebSocketMessage
        type_fb = self.builder.CreateString("server_event")
        
        WebSocketMessageStart(self.builder)
        WebSocketMessageAddType(self.builder, type_fb)
        WebSocketMessageAddDataType(self.builder, WebSocketMessageType.ServerEvent)
        WebSocketMessageAddData(self.builder, server_event_offset)
        
        ws_message_offset = WebSocketMessageEnd(self.builder)
        self.builder.Finish(ws_message_offset)
        return bytes(self.builder.Output())
    
    def create_flow_data_message(self, flow_data: PyFlowData) -> bytes:
        """Create a complete WebSocket message containing FlowData"""
        self.builder = flatbuffers.Builder()
        
        # Create FlowData first
        id_fb = self.builder.CreateString(flow_data.id)
        method_fb = self.builder.CreateString(flow_data.method)
        url_fb = self.builder.CreateString(flow_data.url)
        request_body_fb = self.builder.CreateString(flow_data.request_body or "")
        response_body_fb = self.builder.CreateString(flow_data.response_body or "")
        
        # Create header vectors
        request_headers_fb = self._create_headers_vector(flow_data.request_headers)
        response_headers_fb = self._create_headers_vector(flow_data.response_headers)
        
        # Create FlowData
        FlowDataStart(self.builder)
        FlowDataAddId(self.builder, id_fb)
        FlowDataAddMethod(self.builder, method_fb)
        FlowDataAddUrl(self.builder, url_fb)
        FlowDataAddStatus(self.builder, flow_data.status)
        FlowDataAddStartTimestamp(self.builder, flow_data.start_timestamp)
        FlowDataAddEndTimestamp(self.builder, flow_data.end_timestamp)
        FlowDataAddRequestSize(self.builder, flow_data.request_size)
        FlowDataAddResponseSize(self.builder, flow_data.response_size)
        
        if request_headers_fb:
            FlowDataAddRequestHeaders(self.builder, request_headers_fb)
        if response_headers_fb:
            FlowDataAddResponseHeaders(self.builder, response_headers_fb)
        
        FlowDataAddRequestBody(self.builder, request_body_fb)
        FlowDataAddResponseBody(self.builder, response_body_fb)
        FlowDataAddIsIntercepted(self.builder, flow_data.is_intercepted)
        
        flow_data_offset = FlowDataEnd(self.builder)
        
        # Create WebSocketMessage
        type_fb = self.builder.CreateString("flow_event")
        
        WebSocketMessageStart(self.builder)
        WebSocketMessageAddType(self.builder, type_fb)
        WebSocketMessageAddDataType(self.builder, WebSocketMessageType.FlowData)
        WebSocketMessageAddData(self.builder, flow_data_offset)
        
        ws_message_offset = WebSocketMessageEnd(self.builder)
        self.builder.Finish(ws_message_offset)
        return bytes(self.builder.Output())


# ============= DESERIALIZATION UTILITIES =============

class FlatBufferDeserializer:
    """Deserializes FlatBuffer bytes to Python models"""
    
    @staticmethod
    def _extract_headers(fb_object, get_headers_func, get_headers_length_func) -> Dict[str, str]:
        """Extract headers from FlatBuffer object to Python dict"""
        headers = {}
        length = get_headers_length_func()
        for i in range(length):
            header_pair = get_headers_func(i)
            if header_pair:
                key = header_pair.Key()
                value = header_pair.Value()
                if key and value:
                    headers[key.decode('utf-8')] = value.decode('utf-8')
        return headers
    
    @staticmethod
    def deserialize_flow_data(buffer: bytes) -> PyFlowData:
        """Deserialize FlatBuffer bytes to FlowData Python model"""
        fb_flow = FlowData.GetRootAs(buffer)
        
        # Extract headers
        request_headers = FlatBufferDeserializer._extract_headers(
            fb_flow, fb_flow.RequestHeaders, fb_flow.RequestHeadersLength
        )
        response_headers = FlatBufferDeserializer._extract_headers(
            fb_flow, fb_flow.ResponseHeaders, fb_flow.ResponseHeadersLength
        )
        
        return PyFlowData(
            id=fb_flow.Id().decode('utf-8') if fb_flow.Id() else "",
            method=fb_flow.Method().decode('utf-8') if fb_flow.Method() else "",
            url=fb_flow.Url().decode('utf-8') if fb_flow.Url() else "",
            status=fb_flow.Status(),
            start_timestamp=fb_flow.StartTimestamp(),
            end_timestamp=fb_flow.EndTimestamp(),
            request_size=fb_flow.RequestSize(),
            response_size=fb_flow.ResponseSize(),
            request_headers=request_headers,
            response_headers=response_headers,
            request_body=fb_flow.RequestBody().decode('utf-8') if fb_flow.RequestBody() else "",
            response_body=fb_flow.ResponseBody().decode('utf-8') if fb_flow.ResponseBody() else "",
            is_intercepted=fb_flow.IsIntercepted()
        )
    
    @staticmethod
    def deserialize_filter_model(buffer: bytes) -> PyFilterModel:
        """Deserialize FlatBuffer bytes to FilterModel Python model"""
        fb_filter = FilterModel.GetRootAs(buffer)
        
        # Convert enum
        operator_py = FB_TO_PYTHON_OPERATOR.get(fb_filter.Operator(), PyOperator.CONTAINS)
        
        return PyFilterModel(
            id=fb_filter.Id() if fb_filter.Id() != 0 else None,
            filter_name=fb_filter.FilterName().decode('utf-8') if fb_filter.FilterName() else "",
            field=fb_filter.Field().decode('utf-8') if fb_filter.Field() else "",
            operator=operator_py,
            value=fb_filter.Value().decode('utf-8') if fb_filter.Value() else ""
        )
    
    @staticmethod
    def deserialize_rule_model(buffer: bytes) -> PyRuleModel:
        """Deserialize FlatBuffer bytes to RuleModel Python model"""
        fb_rule = RuleModel.GetRootAs(buffer)
        
        # Convert enum
        action_py = FB_TO_PYTHON_ACTION.get(fb_rule.Action(), PyRuleAction.ADD_HEADER)
        
        return PyRuleModel(
            id=fb_rule.Id() if fb_rule.Id() != 0 else None,
            rule_name=fb_rule.RuleName().decode('utf-8') if fb_rule.RuleName() else "",
            filter_id=fb_rule.FilterId(),
            action=action_py,
            target_key=fb_rule.TargetKey().decode('utf-8') if fb_rule.TargetKey() else "",
            target_value=fb_rule.TargetValue().decode('utf-8') if fb_rule.TargetValue() else "",
            enabled=fb_rule.Enabled()
        )
    
    @staticmethod
    def _extract_rules_list(fb_sync: SyncMessage) -> List[PyRuleModel]:
        """Extract rules list from SyncMessage"""
        rules = []
        length = fb_sync.RulesListLength()
        for i in range(length):
            fb_rule = fb_sync.RulesList(i)
            if fb_rule:
                # Convert enum
                action_py = FB_TO_PYTHON_ACTION.get(fb_rule.Action(), PyRuleAction.ADD_HEADER)
                
                rule = PyRuleModel(
                    id=fb_rule.Id() if fb_rule.Id() != 0 else None,
                    rule_name=fb_rule.RuleName().decode('utf-8') if fb_rule.RuleName() else "",
                    filter_id=fb_rule.FilterId(),
                    action=action_py,
                    target_key=fb_rule.TargetKey().decode('utf-8') if fb_rule.TargetKey() else "",
                    target_value=fb_rule.TargetValue().decode('utf-8') if fb_rule.TargetValue() else "",
                    enabled=fb_rule.Enabled()
                )
                rules.append(rule)
        return rules
    
    @staticmethod
    def _extract_filters_list(fb_sync: SyncMessage) -> List[PyFilterModel]:
        """Extract filters list from SyncMessage"""
        filters = []
        length = fb_sync.FiltersDataLength()
        for i in range(length):
            fb_filter = fb_sync.FiltersData(i)
            if fb_filter:
                # Convert enum
                operator_py = FB_TO_PYTHON_OPERATOR.get(fb_filter.Operator(), PyOperator.CONTAINS)
                
                filter_model = PyFilterModel(
                    id=fb_filter.Id() if fb_filter.Id() != 0 else None,
                    filter_name=fb_filter.FilterName().decode('utf-8') if fb_filter.FilterName() else "",
                    field=fb_filter.Field().decode('utf-8') if fb_filter.Field() else "",
                    operator=operator_py,
                    value=fb_filter.Value().decode('utf-8') if fb_filter.Value() else ""
                )
                filters.append(filter_model)
        return filters
    
    @staticmethod
    def deserialize_sync_message(buffer: bytes) -> PySyncMessage:
        """Deserialize FlatBuffer bytes to SyncMessage Python model"""
        fb_sync = SyncMessage.GetRootAs(buffer)
        
        # Convert enum
        operation_py = FB_TO_PYTHON_OPERATION.get(fb_sync.Operation(), PyOperationType.FULL_SYNC)
        
        # Extract lists
        rules_list = FlatBufferDeserializer._extract_rules_list(fb_sync)
        filters_data = FlatBufferDeserializer._extract_filters_list(fb_sync)
        
        return PySyncMessage(
            operation=operation_py,
            rules_list=rules_list,
            filters_data=filters_data,
            timestamp=fb_sync.Timestamp()
        )
    
    @staticmethod
    def deserialize_server_event(buffer: bytes) -> dict:
        """Deserialize FlatBuffer bytes to ServerEvent dict"""
        fb_server_event = ServerEvent.GetRootAs(buffer)
        
        return {
            "status": fb_server_event.Status().decode('utf-8') if fb_server_event.Status() else "",
            "port": fb_server_event.Port()
        }
    
    @staticmethod
    def deserialize_websocket_message(buffer: bytes) -> dict:
        """Deserialize FlatBuffer bytes to WebSocketMessage dict"""
        fb_ws_message = WebSocketMessage.GetRootAs(buffer)
        
        message_type = fb_ws_message.Type().decode('utf-8') if fb_ws_message.Type() else ""
        data_type = fb_ws_message.DataType()
        data_table = fb_ws_message.Data()
        
        result = {
            "type": message_type,
            "data_type": data_type,
            "data": None
        }
        
        if data_table and data_type == WebSocketMessageType.ServerEvent:
            # Extract ServerEvent from the union
            server_event = ServerEvent()
            server_event.Init(data_table.Bytes, data_table.Pos)
            result["data"] = {
                "status": server_event.Status().decode('utf-8') if server_event.Status() else "",
                "port": server_event.Port()
            }
        elif data_table and data_type == WebSocketMessageType.FlowData:
            # Extract FlowData from the union
            flow_data = FlowData()
            flow_data.Init(data_table.Bytes, data_table.Pos)
            
            # Extract headers
            request_headers = {}
            for i in range(flow_data.RequestHeadersLength()):
                header_pair = flow_data.RequestHeaders(i)
                if header_pair:
                    key = header_pair.Key()
                    value = header_pair.Value()
                    if key and value:
                        request_headers[key.decode('utf-8')] = value.decode('utf-8')
            
            response_headers = {}
            for i in range(flow_data.ResponseHeadersLength()):
                header_pair = flow_data.ResponseHeaders(i)
                if header_pair:
                    key = header_pair.Key()
                    value = header_pair.Value()
                    if key and value:
                        response_headers[key.decode('utf-8')] = value.decode('utf-8')
            
            result["data"] = {
                "id": flow_data.Id().decode('utf-8') if flow_data.Id() else "",
                "method": flow_data.Method().decode('utf-8') if flow_data.Method() else "",
                "url": flow_data.Url().decode('utf-8') if flow_data.Url() else "",
                "status": flow_data.Status(),
                "start_timestamp": flow_data.StartTimestamp(),
                "end_timestamp": flow_data.EndTimestamp(),
                "request_size": flow_data.RequestSize(),
                "response_size": flow_data.ResponseSize(),
                "request_headers": request_headers,
                "response_headers": response_headers,
                "request_body": flow_data.RequestBody().decode('utf-8') if flow_data.RequestBody() else "",
                "response_body": flow_data.ResponseBody().decode('utf-8') if flow_data.ResponseBody() else "",
                "is_intercepted": flow_data.IsIntercepted()
            }
        
        return result


# ============= CONVENIENCE FUNCTIONS =============

# Serialization shortcuts
def serialize_flow_data(flow_data: PyFlowData) -> bytes:
    """Serialize FlowData to bytes"""
    return FlatBufferSerializer().serialize_flow_data(flow_data)

def serialize_filter_model(filter_model: PyFilterModel) -> bytes:
    """Serialize FilterModel to bytes"""
    return FlatBufferSerializer().serialize_filter_model(filter_model)

def serialize_rule_model(rule_model: PyRuleModel) -> bytes:
    """Serialize RuleModel to bytes"""
    return FlatBufferSerializer().serialize_rule_model(rule_model)

def serialize_sync_message(sync_message: PySyncMessage) -> bytes:
    """Serialize SyncMessage to bytes"""
    return FlatBufferSerializer().serialize_sync_message(sync_message)

def create_full_sync_message(rules: List[PyRuleModel], filters: List[PyFilterModel]) -> bytes:
    """Create a full sync message with all rules and filters"""
    sync_msg = PySyncMessage(
        operation=PyOperationType.FULL_SYNC,
        rules_list=rules,
        filters_data=filters
    )
    return serialize_sync_message(sync_msg)

# Deserialization shortcuts
def deserialize_flow_data(buffer: bytes) -> PyFlowData:
    """Deserialize bytes to FlowData"""
    return FlatBufferDeserializer.deserialize_flow_data(buffer)

def deserialize_filter_model(buffer: bytes) -> PyFilterModel:
    """Deserialize bytes to FilterModel"""
    return FlatBufferDeserializer.deserialize_filter_model(buffer)

def deserialize_rule_model(buffer: bytes) -> PyRuleModel:
    """Deserialize bytes to RuleModel"""
    return FlatBufferDeserializer.deserialize_rule_model(buffer)

def deserialize_sync_message(buffer: bytes) -> PySyncMessage:
    """Deserialize bytes to SyncMessage"""
    return FlatBufferDeserializer.deserialize_sync_message(buffer)

# WebSocket message utilities
def serialize_server_event(status: str, port: int) -> bytes:
    """Serialize ServerEvent to bytes"""
    return FlatBufferSerializer().serialize_server_event(status, port)

def create_server_event_message(status: str, port: int) -> bytes:
    """Create a complete WebSocket message containing ServerEvent"""
    return FlatBufferSerializer().create_server_event_message(status, port)

def create_flow_data_message(flow_data: PyFlowData) -> bytes:
    """Create a complete WebSocket message containing FlowData"""
    return FlatBufferSerializer().create_flow_data_message(flow_data)

def deserialize_server_event(buffer: bytes) -> dict:
    """Deserialize bytes to ServerEvent dict"""
    return FlatBufferDeserializer.deserialize_server_event(buffer)

def deserialize_websocket_message(buffer: bytes) -> dict:
    """Deserialize bytes to WebSocketMessage dict"""
    return FlatBufferDeserializer.deserialize_websocket_message(buffer)

# Server event convenience functions
def create_server_started_message(port: int) -> bytes:
    """Create a server started WebSocket message"""
    return create_server_event_message("started", port)

def create_server_stopped_message(port: int) -> bytes:
    """Create a server stopped WebSocket message"""
    return create_server_event_message("stopped", port)

# Round-trip utilities
def round_trip_flow_data(flow_data: PyFlowData) -> PyFlowData:
    """Serialize and deserialize FlowData (useful for testing)"""
    buffer = serialize_flow_data(flow_data)
    return deserialize_flow_data(buffer)

def round_trip_sync_message(sync_message: PySyncMessage) -> PySyncMessage:
    """Serialize and deserialize SyncMessage (useful for testing)"""
    buffer = serialize_sync_message(sync_message)
    return deserialize_sync_message(buffer)

def round_trip_server_event(status: str, port: int) -> dict:
    """Serialize and deserialize ServerEvent (useful for testing)"""
    buffer = serialize_server_event(status, port)
    return deserialize_server_event(buffer)

def round_trip_websocket_message(message_type: str, flow_data: PyFlowData = None, status: str = None, port: int = None) -> dict:
    """Serialize and deserialize WebSocketMessage (useful for testing)"""
    if message_type == "flow_event" and flow_data:
        buffer = create_flow_data_message(flow_data)
    elif message_type == "server_event" and status and port:
        buffer = create_server_event_message(status, port)
    else:
        raise ValueError("Invalid message type or missing parameters")
    
    return deserialize_websocket_message(buffer)

