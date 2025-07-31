import logging
from pathlib import Path
from mitmproxy import http
from typing import Any
import re
from backend.utils.flat_utils import MessageFactory
from backend.utils.base_models import (
    FlowData,
    RuleAction,
    RuleModel
)
from backend.services.storage import CacheStore

logger = logging.getLogger(__name__)

class HTTPInterceptorAddon:
    def __init__(self, flow_queue: Any, stop_event: Any):
        self.flow_queue = flow_queue  # Send flow data to main process
        self.stop_event = stop_event
        self.dump_master = None  # Will be set by the process function
        
        # Get singleton cache store for ultra-fast rule access
        self.cache_store = CacheStore()
        
        # Define patterns to exclude from interception display
        self.exclude_patterns = [
            # FastAPI server endpoints - don't show UI's own API calls
            r'localhost:8000/api/',
            r'127\.0\.0\.1:8000/api/',
            r'localhost:8000/ws',
            r'127\.0\.0\.1:8000/ws',
            r'localhost:8000/docs',
            r'127\.0\.0\.1:8000/docs',
            r'localhost:8000/openapi\.json',
            r'127\.0\.0\.1:8000/openapi\.json',
            
            # Chrome extension internal requests
            r'chrome-extension://',
            r'moz-extension://',
            
            # Browser internal requests
            r'localhost:8000(?:/)?$',  # Base FastAPI URL
            r'127\.0\.0\.1:8000(?:/)?$',
            
            # WebSocket upgrade requests (handled separately)
            r'.*\/ws(?:\?.*)?$',
            
            # Development server requests (if running frontend dev server)
            r'localhost:5173/',  # Vite dev server
            r'127\.0\.0\.1:5173/',
        ]
        
        # Compile regex patterns for better performance
        self.exclude_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.exclude_patterns]


    def should_exclude_request(self, url: str, headers: dict) -> bool:
        """Check if a request should be excluded from interception display"""
        
        # Check URL patterns
        for regex in self.exclude_regex:
            if regex.search(url):
                return True
        
        # Check for API calls by User-Agent (if your frontend sets a specific user-agent)
        user_agent = headers.get('user-agent', '').lower()
        if 'http-interceptor-ui' in user_agent:
            return True
            
        # Check for specific request headers that indicate internal calls
        if headers.get('x-interceptor-internal') == 'true':
            return True
            
        return False


    def _apply_request_rule(self, mitm_flow: http.HTTPFlow, rule: RuleModel) -> bool:
        """
        Apply a rule to the request phase
        Returns True if rule was applied successfully
        Now implemented with actual logic!
        """
        try:
            modified = False
            
            if rule.action == RuleAction.ADD_HEADER:
                # Add header to request
                if rule.target_key and rule.target_value:
                    mitm_flow.request.headers[rule.target_key] = rule.target_value
                    modified = True
                    logger.info(f"Added request header by rule '{rule.rule_name}': {rule.target_key}={rule.target_value}")
                    
            elif rule.action == RuleAction.MODIFY_HEADER:
                # Modify existing header or add if not present
                if rule.target_key and rule.target_value:
                    mitm_flow.request.headers[rule.target_key] = rule.target_value
                    modified = True
                    logger.info(f"Modified request header by rule '{rule.rule_name}': {rule.target_key}={rule.target_value}")
                    
            elif rule.action == RuleAction.DELETE_HEADER:
                # Remove header if present
                if rule.target_key in mitm_flow.request.headers:
                    del mitm_flow.request.headers[rule.target_key]
                    modified = True
                    logger.info(f"Deleted request header by rule '{rule.rule_name}': {rule.target_key}")
                    
            elif rule.action == RuleAction.MODIFY_BODY:
                # Modify request body
                if rule.target_key and Path(rule.target_key).is_file():
                    with open(rule.target_key, mode='rb', encoding='utf-8') as f:
                        mitm_flow.request.content = f.read()
                elif rule.target_value:
                    mitm_flow.request.content = rule.target_value.encode(errors='ignore')
                # Update content-length header
                mitm_flow.request.headers["content-length"] = str(len(mitm_flow.request.content))
                modified = True
                logger.info(f"Modified request body by rule '{rule.rule_name}'")
            elif rule.action == RuleAction.BLOCK_REQUEST:
                # Block the request with a 403 response
                from mitmproxy import http
                mitm_flow.response = http.Response.make(
                    403, 
                    b"Request blocked by HTTP Interceptor rule",
                    {"Content-Type": "text/plain"}
                )
                modified = True
                logger.info(f"Blocked request by rule '{rule.rule_name}': {mitm_flow.request.pretty_url}")
                
            elif rule.action == RuleAction.AUTO_RESPOND:
                # Create automatic response without forwarding to server
                from mitmproxy import http
                response_body = rule.target_value if rule.target_value else "Auto response"
                mitm_flow.response = http.Response.make(
                    200,
                    response_body.encode('utf-8'),
                    {"Content-Type": "text/plain"}
                )
                modified = True
                logger.info(f"Auto-responded by rule '{rule.rule_name}': {mitm_flow.request.pretty_url}")
                
            else:
                logger.warning(f"Unknown request action in rule '{rule.rule_name}': {rule.action}")
                
            return modified
            
        except Exception as e:
            logger.error(f"Failed to apply request rule {rule.rule_name}: {e}")
            return False

    def _apply_response_rule(self, mitm_flow: http.HTTPFlow, rule: RuleModel) -> bool:
        """
        Apply a rule to the response phase
        Returns True if rule was applied successfully
        Now implemented with actual logic!
        """
        # Check if we have a response to modify
        if not mitm_flow.response:
            logger.warning(f"No response available for rule '{rule.rule_name}'")
            return False
            
        try:
            modified = False
            
            if rule.action == RuleAction.ADD_HEADER:
                # Add header to response
                if rule.target_key and rule.target_value:
                    mitm_flow.response.headers[rule.target_key] = rule.target_value
                    modified = True
                    logger.info(f"Added response header by rule '{rule.rule_name}': {rule.target_key}={rule.target_value}")
                    
            elif rule.action == RuleAction.MODIFY_HEADER:
                # Modify existing response header or add if not present
                if rule.target_key and rule.target_value:
                    mitm_flow.response.headers[rule.target_key] = rule.target_value
                    modified = True
                    logger.info(f"Modified response header by rule '{rule.rule_name}': {rule.target_key}={rule.target_value}")
                    
            elif rule.action == RuleAction.DELETE_HEADER:
                # Remove response header if present
                if rule.target_key in mitm_flow.response.headers:
                    del mitm_flow.response.headers[rule.target_key]
                    modified = True
                    logger.info(f"Deleted response header by rule '{rule.rule_name}': {rule.target_key}")
                    
            elif rule.action == RuleAction.MODIFY_BODY:
                # Modify response body
                if rule.target_key and Path(rule.target_key).is_file():
                    with open(rule.target_key, mode='rb', encoding='utf-8') as f:
                        mitm_flow.response.content = f.read()
                elif rule.target_value:
                    mitm_flow.response.content = rule.target_value.encode(errors='ignore')
                # Update content-length header
                mitm_flow.response.headers["content-length"] = str(len(mitm_flow.response.content))
                modified = True
                logger.info(f"Modified response body by rule '{rule.rule_name}'")
            else:
                logger.warning(f"Unknown response action in rule '{rule.rule_name}': {rule.action}")
                
            return modified
            
        except Exception as e:
            logger.error(f"Failed to apply response rule {rule.rule_name}: {e}")
            return False

    def _send_message(self, message: FlowData) -> None:
        """Send structured message to queue"""
        try:
            flat_message = MessageFactory.create_flow_data_message(message)
            self.flow_queue.put(flat_message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    def request(self, mitm_flow: http.HTTPFlow) -> None:
        """Handle request phase with rule processing"""
        # Check for stop signal - important for clean shutdown
        if self.stop_event.is_set():
            if self.dump_master:
                self.dump_master.shutdown()
            return
        
        if self.should_exclude_request(mitm_flow.request.pretty_url, dict(mitm_flow.request.headers)):
            return
        
        def predicate(rule: RuleModel) -> bool:
            if filter := self.cache_store.get_filter_by_id(rule.filter_id):
                return filter.evaluate(mitm_flow)
            return False
        
        matching_rule = next(filter(predicate, self.cache_store.get_active_rules()), None)
        if not matching_rule:
            # Mark flow as not intercepted in request phase
            mitm_flow.intercepted_in_request = False
            return
        
        rule_applied = self._apply_request_rule(mitm_flow, matching_rule)
        # Store whether rule was applied in request phase
        mitm_flow.intercepted_in_request = rule_applied
        
        if matching_rule.action == RuleAction.AUTO_RESPOND:
            self._send_message(self.get_flow_data(mitm_flow, is_intercepted=rule_applied))


    def response(self, mitm_flow: http.HTTPFlow) -> None:
        """Handle response phase with rule processing"""
        # Check for stop signal
        if self.stop_event.is_set():
            if self.dump_master:
                self.dump_master.shutdown()
            return
        
        print("response:", mitm_flow.request.pretty_url)
        request_headers = dict(mitm_flow.request.headers) if mitm_flow.request else {}
        if self.should_exclude_request(mitm_flow.request.pretty_url, request_headers):
            return
        
        def predicate(rule: RuleModel) -> bool:
            if filter := self.cache_store.get_filter_by_id(rule.filter_id):
                return filter.evaluate(mitm_flow)
            return False
        
        # Check if rule was applied in response phase
        rule_applied_in_response = False
        matching_rule = next(filter(predicate, self.cache_store.get_active_rules()), None)
        if matching_rule:
            rule_applied_in_response = self._apply_response_rule(mitm_flow, matching_rule)
        
        # Check if rule was applied in either request or response phase
        request_intercepted = getattr(mitm_flow, 'intercepted_in_request', False)
        is_intercepted = request_intercepted or rule_applied_in_response
        
        self._send_message(self.get_flow_data(mitm_flow, is_intercepted=is_intercepted))

         
    def get_flow_data(self, mitm_flow: http.HTTPFlow, is_intercepted: bool = False) -> FlowData:
        """Convert mitmproxy flow to FlowData model"""
        return FlowData(
            id=mitm_flow.id,
            method=mitm_flow.request.method,
            url=mitm_flow.request.pretty_url,
            status=mitm_flow.response.status_code if mitm_flow.response else None,
            start_timestamp=mitm_flow.request.timestamp_start,
            end_timestamp=mitm_flow.response.timestamp_end if mitm_flow.response else None,
            request_size=len(mitm_flow.request.content) if mitm_flow.request and mitm_flow.request.content else 0,
            response_size=len(mitm_flow.response.content) if mitm_flow.response and mitm_flow.response.content else 0,
            request_headers=dict(mitm_flow.request.headers) if mitm_flow.request else {},
            response_headers=dict(mitm_flow.response.headers) if mitm_flow.response else {},
            request_body=mitm_flow.request.text or "",
            response_body=mitm_flow.response.text or "",
            is_intercepted=is_intercepted
        )
