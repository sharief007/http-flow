from typing import Dict, Optional, List, Literal
from pydantic import BaseModel, field_validator
from mitmproxy import http
from enum import Enum


class FlowData(BaseModel):
    id: str
    method: str
    url: str
    status: int
    start_timestamp: float
    end_timestamp: float
    request_size: int 
    response_size: int
    request_headers: Dict[str, str]
    response_headers: Dict[str, str]
    request_body: str
    response_body: str
    is_intercepted: bool = False

class Operator(Enum):
    CONTAINS = 0
    EQUALS = 1
    STARTS_WITH = 2
    ENDS_WITH = 3
    REGEX = 4

    @classmethod
    def from_string(cls, value: str) -> 'Operator':
        """Convert string to Operator enum"""
        return cls[value.upper()]
    
    def to_string(self) -> str:
        """Convert Operator enum to string"""
        return self.name
    
    @classmethod
    def from_int(cls, value: int) -> 'Operator':
        """Convert integer to Operator enum"""
        return cls(value)
    
    def to_int(self) -> int:
        """Convert Operator enum to integer"""
        return self.value 

    def apply(self, value: str, target: str) -> bool:
        if self == Operator.CONTAINS:
            return value in target
        elif self == Operator.EQUALS:
            return value == target
        elif self == Operator.STARTS_WITH:
            return target.startswith(value)
        elif self == Operator.ENDS_WITH:
            return target.endswith(value)
        elif self == Operator.REGEX:
            import re
            return re.search(value, target) is not None
        else:
            raise ValueError(f"Unknown operator: {self}")

class FilterModel(BaseModel):
    id: Optional[int] = None
    filter_name: str
    field: str 
    operator: Operator  
    value: str

    @field_validator('filter_name', 'field', 'value')
    @classmethod
    def validate_required_fields(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('This field is required and cannot be empty')
        return v.strip()

    def evaluate(self, mitm_flow: http.HTTPFlow) -> bool:
        """
        Evaluate if a filter matches the given request data
        Now implemented with actual logic!
        """        
        if self.field == "url":
            field_value = mitm_flow.request.pretty_url
        elif self.field == "method":
            field_value = mitm_flow.request.method
        elif self.field.startswith("header:"):
            header_name = self.field[7:]
            headers = mitm_flow.request.headers 
            if (header_value := headers.get(header_name, None)) is None:
                return False
            field_value = header_value
        elif self.field == "body":
            content = mitm_flow.request.content if mitm_flow.request.content else b""
            field_value = content.decode('utf-8', errors='ignore')
        else:
            return False

        return self.operator.apply(self.value, field_value)


class RuleAction(Enum):
    ADD_HEADER = 0
    MODIFY_HEADER = 1
    DELETE_HEADER = 2
    MODIFY_BODY = 3
    BLOCK_REQUEST = 4
    AUTO_RESPOND = 5

    @classmethod
    def from_string(cls, value: str) -> 'RuleAction':
        """Convert string to RuleAction enum"""
        return cls[value.upper()]
    
    def to_string(self) -> str:
        """Convert RuleAction enum to string"""
        return self.name
    
    @classmethod
    def from_int(cls, value: int) -> 'RuleAction':
        """Convert integer to RuleAction enum"""
        return cls(value)
    
    def to_int(self) -> int:
        """Convert RuleAction enum to integer"""
        return self.value


class RuleModel(BaseModel):
    id: Optional[int] = None
    rule_name: str
    filter_id: int
    action: RuleAction
    target_key: str  
    target_value: str  
    enabled: bool = True

    @field_validator('rule_name', 'target_key', 'target_value')
    @classmethod
    def validate_required_fields(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('This field is required and cannot be empty')
        return v.strip()


class OperationType(Enum):
    FULL_SYNC = 0
    ADD = 1
    UPDATE = 2
    DELETE = 3

    @classmethod
    def from_string(cls, value: str) -> 'OperationType':
        """Convert string to OperationType enum"""
        return cls[value.upper()]
    
    def to_string(self) -> str:
        """Convert OperationType enum to string"""
        return self.name
    
    @classmethod
    def from_int(cls, value: int) -> 'OperationType':
        """Convert integer to OperationType enum"""
        return cls(value)
    
    def to_int(self) -> int:
        """Convert OperationType enum to integer"""
        return self.value


class SyncMessage(BaseModel):
    operation: OperationType
    rules_list: List[RuleModel]
    filters_data: List[FilterModel]


# ------------- web socket messages -------------

class ServerEvent:
    type: Literal["server_event"]
    status: str
    port: int

class FlowEvent:
    type: Literal["flow_event"]
    flow_data: FlowData
