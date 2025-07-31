
"""
FlatBuffer Builder Utilities

This module provides builder classes and helper functions for creating
FlatBuffer messages from Python models in a clean, organized way.
"""
import flatbuffers
import time
from typing import Dict, Optional, List
from abc import ABC, abstractmethod

# Import generated FlatBuffer classes for WebSocket messages
from backend.HttpInterceptor.FlowData import FlowDataStart, FlowDataEnd
from backend.HttpInterceptor.FlowData import (
    FlowDataAddId, FlowDataAddMethod, FlowDataAddUrl, FlowDataAddStatus,
    FlowDataAddStartTimestamp, FlowDataAddEndTimestamp,
    FlowDataAddRequestSize, FlowDataAddResponseSize,
    FlowDataAddRequestHeaders, FlowDataAddResponseHeaders,
    FlowDataAddRequestBody, FlowDataAddResponseBody,
    FlowDataAddIsIntercepted,
    FlowDataStartRequestHeadersVector
)

from backend.HttpInterceptor.HeaderPair import HeaderPairStart, HeaderPairEnd
from backend.HttpInterceptor.HeaderPair import HeaderPairAddKey, HeaderPairAddValue

from backend.HttpInterceptor.WebSocketMessage import WebSocketMessageStart, WebSocketMessageEnd
from backend.HttpInterceptor.WebSocketMessage import WebSocketMessageAddType, WebSocketMessageAddDataType, WebSocketMessageAddData

from backend.HttpInterceptor.ServerEvent import ServerEventStart, ServerEventEnd
from backend.HttpInterceptor.ServerEvent import ServerEventAddStatus, ServerEventAddPort

from backend.HttpInterceptor.WebSocketMessageType import WebSocketMessageType

# Import generated FlatBuffer classes for Core Models
from backend.HttpInterceptor.FilterModel import FilterModelStart, FilterModelEnd
from backend.HttpInterceptor.FilterModel import (
    FilterModelAddId, FilterModelAddFilterName, FilterModelAddField, 
    FilterModelAddOperator, FilterModelAddValue
)

from backend.HttpInterceptor.RuleModel import RuleModelStart, RuleModelEnd
from backend.HttpInterceptor.RuleModel import (
    RuleModelAddId, RuleModelAddRuleName, RuleModelAddFilterId,
    RuleModelAddAction, RuleModelAddTargetKey, RuleModelAddTargetValue, RuleModelAddEnabled
)

from backend.HttpInterceptor.SyncMessage import SyncMessageStart, SyncMessageEnd
from backend.HttpInterceptor.SyncMessage import (
    SyncMessageAddOperation, SyncMessageAddRulesList, SyncMessageAddFiltersData,
    SyncMessageAddTimestamp, SyncMessageStartRulesListVector, SyncMessageStartFiltersDataVector
)

from backend.HttpInterceptor.CoreMessage import CoreMessageStart, CoreMessageEnd
from backend.HttpInterceptor.CoreMessage import CoreMessageAddMessage, CoreMessageAddTimestamp

from backend.HttpInterceptor.Operator import Operator
from backend.HttpInterceptor.RuleAction import RuleAction
from backend.HttpInterceptor.OperationType import OperationType
from backend.HttpInterceptor.CoreMessageType import CoreMessageType

# Import your regular Python models
from backend.utils.base_models import FlowData as PyFlowData, FilterModel as PyFilterModel, RuleModel as PyRuleModel, SyncMessage as PySyncMessage
from backend.utils.base_models import (
    OperationType as PyOperationType,
    Operator as PyOperator,
    RuleAction as PyRuleAction
)

action_mapping = {
    PyRuleAction.ADD_HEADER: RuleAction.ADD_HEADER,
    PyRuleAction.MODIFY_HEADER: RuleAction.MODIFY_HEADER,
    PyRuleAction.DELETE_HEADER: RuleAction.DELETE_HEADER,
    PyRuleAction.MODIFY_BODY: RuleAction.MODIFY_BODY,
    PyRuleAction.BLOCK_REQUEST: RuleAction.BLOCK_REQUEST,
    PyRuleAction.AUTO_RESPOND: RuleAction.AUTO_RESPOND,
}

operator_mapping = {
    PyOperator.CONTAINS: Operator.CONTAINS,
    PyOperator.EQUALS: Operator.EQUALS,
    PyOperator.STARTS_WITH: Operator.STARTS_WITH,
    PyOperator.ENDS_WITH: Operator.ENDS_WITH,
    PyOperator.REGEX: Operator.REGEX,
}

sync_operation_mapping = {
    PyOperationType.FULL_SYNC: OperationType.FULL_SYNC,
    PyOperationType.ADD: OperationType.ADD,
    PyOperationType.UPDATE: OperationType.UPDATE,
    PyOperationType.DELETE: OperationType.DELETE,
}

# ============= BASE BUILDER CLASS =============

class FlatBufferBuilder(ABC):
    """Base class for all FlatBuffer builders"""
    
    def __init__(self, initial_size: int = 1024):
        self.builder = flatbuffers.Builder(initial_size)
    
    @abstractmethod
    def build(self) -> int:
        """Build the FlatBuffer object and return its offset"""
        pass
    
    def get_bytes(self, root_offset: int) -> bytes:
        """Finish building and return bytes"""
        self.builder.Finish(root_offset)
        return bytes(self.builder.Output())


# ============= HELPER BUILDERS =============

class HeaderPairBuilder(FlatBufferBuilder):
    """Builder for HeaderPair FlatBuffer objects"""
    
    def __init__(self, key: str, value: str, builder: Optional[flatbuffers.Builder] = None):
        if builder:
            self.builder = builder
        else:
            super().__init__(256)
        self.key = key
        self.value = value
    
    def build(self) -> int:
        """Build HeaderPair and return its offset"""
        key_fb = self.builder.CreateString(self.key)
        value_fb = self.builder.CreateString(self.value)
        
        HeaderPairStart(self.builder)
        HeaderPairAddKey(self.builder, key_fb)
        HeaderPairAddValue(self.builder, value_fb)
        return HeaderPairEnd(self.builder)


class HeadersVectorBuilder:
    """Builder for creating vectors of HeaderPair objects"""
    
    def __init__(self, headers_dict: Dict[str, str], builder: flatbuffers.Builder):
        self.headers_dict = headers_dict
        self.builder = builder
    
    def build(self) -> int:
        """Build headers vector and return its offset"""
        if not self.headers_dict:
            return None
            
        # Create all HeaderPair objects first
        header_pairs = []
        for key, value in self.headers_dict.items():
            header_builder = HeaderPairBuilder(key, value, self.builder)
            header_pair = header_builder.build()
            header_pairs.append(header_pair)
        
        # Create vector of HeaderPairs (built in reverse order)
        FlowDataStartRequestHeadersVector(self.builder, len(header_pairs))
        for header_pair in reversed(header_pairs):
            self.builder.PrependUOffsetTRelative(header_pair)
        return self.builder.EndVector(len(header_pairs))


class FlowDataBuilder(FlatBufferBuilder):
    """Builder for FlowData FlatBuffer objects"""
    
    def __init__(self, flow_data: PyFlowData, builder: Optional[flatbuffers.Builder] = None):
        if builder:
            self.builder = builder
        else:
            super().__init__(2048)
        self.flow_data = flow_data
    
    def build(self) -> int:
        """Build FlowData and return its offset"""
        # Create strings first (FlatBuffers requirement)
        id_fb = self.builder.CreateString(self.flow_data.id)
        method_fb = self.builder.CreateString(self.flow_data.method)
        url_fb = self.builder.CreateString(self.flow_data.url)
        request_body_fb = self.builder.CreateString(self.flow_data.request_body or "")
        response_body_fb = self.builder.CreateString(self.flow_data.response_body or "")
        
        # Create header vectors
        request_headers_builder = HeadersVectorBuilder(self.flow_data.request_headers, self.builder)
        response_headers_builder = HeadersVectorBuilder(self.flow_data.response_headers, self.builder)
        
        request_headers_fb = request_headers_builder.build()
        response_headers_fb = response_headers_builder.build()
        
        # Create FlowData object
        FlowDataStart(self.builder)
        FlowDataAddId(self.builder, id_fb)
        FlowDataAddMethod(self.builder, method_fb)
        FlowDataAddUrl(self.builder, url_fb)
        FlowDataAddStatus(self.builder, self.flow_data.status)
        FlowDataAddStartTimestamp(self.builder, self.flow_data.start_timestamp)
        FlowDataAddEndTimestamp(self.builder, self.flow_data.end_timestamp)
        FlowDataAddRequestSize(self.builder, self.flow_data.request_size)
        FlowDataAddResponseSize(self.builder, self.flow_data.response_size)
        
        if request_headers_fb:
            FlowDataAddRequestHeaders(self.builder, request_headers_fb)
        if response_headers_fb:
            FlowDataAddResponseHeaders(self.builder, response_headers_fb)
            
        FlowDataAddRequestBody(self.builder, request_body_fb)
        FlowDataAddResponseBody(self.builder, response_body_fb)
        FlowDataAddIsIntercepted(self.builder, self.flow_data.is_intercepted)
        
        return FlowDataEnd(self.builder)


class ServerEventBuilder(FlatBufferBuilder):
    """Builder for ServerEvent FlatBuffer objects"""
    
    def __init__(self, status: str, port: int, builder: Optional[flatbuffers.Builder] = None):
        if builder:
            self.builder = builder
        else:
            super().__init__(256)
        self.status = status
        self.port = port
    
    def build(self) -> int:
        """Build ServerEvent and return its offset"""
        status_fb = self.builder.CreateString(self.status)
        
        ServerEventStart(self.builder)
        ServerEventAddStatus(self.builder, status_fb)
        ServerEventAddPort(self.builder, self.port)
        
        return ServerEventEnd(self.builder)


# ============= CORE MODEL BUILDERS =============

class FilterModelBuilder(FlatBufferBuilder):
    """Builder for FilterModel FlatBuffer objects"""
    
    def __init__(self, filter_model: PyFilterModel, builder: Optional[flatbuffers.Builder] = None):
        if builder:
            self.builder = builder
        else:
            super().__init__(512)
        self.filter_model = filter_model
    
    def build(self) -> int:
        """Build FilterModel and return its offset"""
        filter_name_fb = self.builder.CreateString(self.filter_model.filter_name)
        field_fb = self.builder.CreateString(self.filter_model.field)
        value_fb = self.builder.CreateString(self.filter_model.value)
        
        # Convert Python enum to FlatBuffer enum
        operator_enum = operator_mapping.get(self.filter_model.operator, Operator.CONTAINS)
        
        FilterModelStart(self.builder)
        if self.filter_model.id is not None:
            FilterModelAddId(self.builder, self.filter_model.id)
        FilterModelAddFilterName(self.builder, filter_name_fb)
        FilterModelAddField(self.builder, field_fb)
        FilterModelAddOperator(self.builder, operator_enum)
        FilterModelAddValue(self.builder, value_fb)
        
        return FilterModelEnd(self.builder)


class RuleModelBuilder(FlatBufferBuilder):
    """Builder for RuleModel FlatBuffer objects"""
    
    def __init__(self, rule_model: PyRuleModel, builder: Optional[flatbuffers.Builder] = None):
        if builder:
            self.builder = builder
        else:
            super().__init__(512)
        self.rule_model = rule_model
    
    def build(self) -> int:
        """Build RuleModel and return its offset"""
        rule_name_fb = self.builder.CreateString(self.rule_model.rule_name)
        target_key_fb = self.builder.CreateString(self.rule_model.target_key)
        target_value_fb = self.builder.CreateString(self.rule_model.target_value)
        
        # Convert Python enum to FlatBuffer enum
        action_enum = action_mapping.get(self.rule_model.action, RuleAction.ADD_HEADER)
        
        RuleModelStart(self.builder)
        if self.rule_model.id is not None:
            RuleModelAddId(self.builder, self.rule_model.id)
        RuleModelAddRuleName(self.builder, rule_name_fb)
        RuleModelAddFilterId(self.builder, self.rule_model.filter_id)
        RuleModelAddAction(self.builder, action_enum)
        RuleModelAddTargetKey(self.builder, target_key_fb)
        RuleModelAddTargetValue(self.builder, target_value_fb)
        RuleModelAddEnabled(self.builder, self.rule_model.enabled)
        
        return RuleModelEnd(self.builder)


class RulesVectorBuilder:
    """Builder for creating vectors of RuleModel objects"""
    
    def __init__(self, rules_list: List[PyRuleModel], builder: flatbuffers.Builder):
        self.rules_list = rules_list
        self.builder = builder
    
    def build(self) -> int:
        """Build rules vector and return its offset"""
        if not self.rules_list:
            return None
        
        # Create all RuleModel objects first
        rule_objects = []
        for rule in self.rules_list:
            rule_builder = RuleModelBuilder(rule, self.builder)
            rule_object = rule_builder.build()
            rule_objects.append(rule_object)
        
        # Create vector of RuleModels (built in reverse order)
        SyncMessageStartRulesListVector(self.builder, len(rule_objects))
        for rule_object in reversed(rule_objects):
            self.builder.PrependUOffsetTRelative(rule_object)
        return self.builder.EndVector(len(rule_objects))


class FiltersVectorBuilder:
    """Builder for creating vectors of FilterModel objects"""
    
    def __init__(self, filters_list: List[PyFilterModel], builder: flatbuffers.Builder):
        self.filters_list = filters_list
        self.builder = builder
    
    def build(self) -> int:
        """Build filters vector and return its offset"""
        if not self.filters_list:
            return None
        
        # Create all FilterModel objects first
        filter_objects = []
        for filter_model in self.filters_list:
            filter_builder = FilterModelBuilder(filter_model, self.builder)
            filter_object = filter_builder.build()
            filter_objects.append(filter_object)
        
        # Create vector of FilterModels (built in reverse order)
        SyncMessageStartFiltersDataVector(self.builder, len(filter_objects))
        for filter_object in reversed(filter_objects):
            self.builder.PrependUOffsetTRelative(filter_object)
        return self.builder.EndVector(len(filter_objects))


class SyncMessageBuilder(FlatBufferBuilder):
    """Builder for SyncMessage FlatBuffer objects"""
    
    def __init__(self, sync_message: PySyncMessage, builder: Optional[flatbuffers.Builder] = None):
        if builder:
            self.builder = builder
        else:
            super().__init__(4096)  # Larger buffer for sync messages with multiple rules/filters
        self.sync_message = sync_message
    
    def build(self) -> int:
        """Build SyncMessage and return its offset"""
        # Convert Python enum to FlatBuffer enum
        operation_enum = sync_operation_mapping.get(self.sync_message.operation, OperationType.FULL_SYNC)
        
        # Create vectors for rules and filters
        rules_vector_builder = RulesVectorBuilder(self.sync_message.rules_list, self.builder)
        filters_vector_builder = FiltersVectorBuilder(self.sync_message.filters_data, self.builder)
        
        rules_vector_fb = rules_vector_builder.build()
        filters_vector_fb = filters_vector_builder.build()
        
        SyncMessageStart(self.builder)
        SyncMessageAddOperation(self.builder, operation_enum)
        if rules_vector_fb:
            SyncMessageAddRulesList(self.builder, rules_vector_fb)
        if filters_vector_fb:
            SyncMessageAddFiltersData(self.builder, filters_vector_fb)
        SyncMessageAddTimestamp(self.builder, time.time())
        
        return SyncMessageEnd(self.builder)


class CoreMessageBuilder(FlatBufferBuilder):
    """Builder for CoreMessage FlatBuffer objects"""
    
    def __init__(self, initial_size: int = 4096):
        super().__init__(initial_size)
        self.message_object: Optional[int] = None
        self.message_type: Optional[int] = None
    
    def with_filter_model(self, filter_model: PyFilterModel) -> 'CoreMessageBuilder':
        """Add FilterModel to the core message"""
        filter_builder = FilterModelBuilder(filter_model, self.builder)
        self.message_object = filter_builder.build()
        self.message_type = CoreMessageType.FilterModel
        return self
    
    def with_rule_model(self, rule_model: PyRuleModel) -> 'CoreMessageBuilder':
        """Add RuleModel to the core message"""
        rule_builder = RuleModelBuilder(rule_model, self.builder)
        self.message_object = rule_builder.build()
        self.message_type = CoreMessageType.RuleModel
        return self
    
    def with_sync_message(self, sync_message: PySyncMessage) -> 'CoreMessageBuilder':
        """Add SyncMessage to the core message"""
        sync_builder = SyncMessageBuilder(sync_message, self.builder)
        self.message_object = sync_builder.build()
        self.message_type = CoreMessageType.SyncMessage
        return self
    
    def build(self) -> int:
        """Build CoreMessage and return its offset"""
        if self.message_object is None or self.message_type is None:
            raise ValueError("Core message must have a message object and type")
        
        CoreMessageStart(self.builder)
        CoreMessageAddMessage(self.builder, self.message_object)
        CoreMessageAddTimestamp(self.builder, time.time())
        
        return CoreMessageEnd(self.builder)
    
    def build_message(self) -> bytes:
        """Build complete core message and return as bytes"""
        message_offset = self.build()
        return self.get_bytes(message_offset)


class WebSocketMessageBuilder(FlatBufferBuilder):
    """Builder for WebSocket messages containing different event types"""
    
    def __init__(self, message_type: str, initial_size: int = 1024):
        super().__init__(initial_size)
        self.message_type = message_type
        self.data_object: Optional[int] = None
        self.data_type: Optional[int] = None
    
    def with_server_event(self, status: str, port: int) -> 'WebSocketMessageBuilder':
        """Add ServerEvent data to the message"""
        server_event_builder = ServerEventBuilder(status, port, self.builder)
        self.data_object = server_event_builder.build()
        self.data_type = WebSocketMessageType.ServerEvent
        return self
    
    def with_flow_data(self, flow_data: PyFlowData) -> 'WebSocketMessageBuilder':
        """Add FlowData directly to the message"""
        flow_data_builder = FlowDataBuilder(flow_data, self.builder)
        self.data_object = flow_data_builder.build()
        self.data_type = WebSocketMessageType.FlowData  # Assuming FlowEvent maps to FlowData
        return self
    
    def build(self) -> int:
        """Build WebSocket message and return its offset"""
        if self.data_object is None or self.data_type is None:
            raise ValueError("WebSocket message must have data object and type")
        
        type_fb = self.builder.CreateString(self.message_type)
        
        WebSocketMessageStart(self.builder)
        WebSocketMessageAddType(self.builder, type_fb)
        WebSocketMessageAddDataType(self.builder, self.data_type)
        WebSocketMessageAddData(self.builder, self.data_object)
        
        return WebSocketMessageEnd(self.builder)
    
    def build_message(self) -> bytes:
        """Build complete message and return as bytes"""
        message_offset = self.build()
        return self.get_bytes(message_offset)


# ============= FACTORY FUNCTIONS =============

class MessageFactory:
    """Factory class for creating common message types"""
    
    # WebSocket Message Factories
    @staticmethod
    def create_server_event_message(status: str, port: int) -> bytes:
        """Create a server event WebSocket message"""
        return (WebSocketMessageBuilder("server_event")
                .with_server_event(status, port)
                .build_message())
    
    @staticmethod
    def create_flow_data_message(flow_data: PyFlowData) -> bytes:
        """Create a flow data WebSocket message"""
        return (WebSocketMessageBuilder("flow_event")
                .with_flow_data(flow_data)
                .build_message())
    
    # Core Message Factories
    @staticmethod
    def create_filter_message(filter_model: PyFilterModel) -> bytes:
        """Create a core message containing a FilterModel"""
        return (CoreMessageBuilder()
                .with_filter_model(filter_model)
                .build_message())
    
    @staticmethod
    def create_rule_message(rule_model: PyRuleModel) -> bytes:
        """Create a core message containing a RuleModel"""
        return (CoreMessageBuilder()
                .with_rule_model(rule_model)
                .build_message())
    
    @staticmethod
    def create_sync_message(sync_message: PySyncMessage) -> bytes:
        """Create a core message containing a SyncMessage"""
        return (CoreMessageBuilder()
                .with_sync_message(sync_message)
                .build_message())
    
    @staticmethod
    def create_full_sync_message(rules_list: List[PyRuleModel], filters_data: List[PyFilterModel]) -> bytes:
        """Create a full synchronization message with all rules and filters"""
        sync_msg = PySyncMessage(
            operation=PyOperationType.FULL_SYNC,
            rules_list=rules_list,
            filters_data=filters_data
        )
        return MessageFactory.create_sync_message(sync_msg)


# ============= CONVENIENCE FUNCTIONS =============

def create_server_started_message(port: int) -> bytes:
    """Create a server started message"""
    return MessageFactory.create_server_event_message("started", port)


def create_server_stopped_message(port: int) -> bytes:
    """Create a server stopped message"""
    return MessageFactory.create_server_event_message("stopped", port)


def create_flow_message(py_flow_data: PyFlowData) -> bytes:
    """Create a flow data message from Python FlowData model"""
    return MessageFactory.create_flow_data_message(py_flow_data)

