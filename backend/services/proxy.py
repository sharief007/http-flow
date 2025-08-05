from typing import Optional, Any
import asyncio
import socket
import queue
from multiprocessing import Process, SimpleQueue, Event
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
import logging
from backend.services.addon import HTTPInterceptorAddon
from backend.services.ws import ConnectionManager
from backend.services.storage import CacheStore 
from backend.models.flat_utils import (
    serialize_sync_message,
    create_full_sync_message
)
from backend.models.base_models import (
    FilterModel as PyFilterModel,
    RuleModel as PyRuleModel,
    SyncMessage as PySyncMessage, 
    OperationType, 
)

logger = logging.getLogger(__name__)
sentinel = object()  # Sentinel value for stopping message handler

def run_mitmproxy_process(proxy_port: int, flow_queue: SimpleQueue, rule_queue: SimpleQueue, stop_event: Any):
    """Run mitmproxy in a separate process with two-queue system"""

    async def _handle_rule_updates():
        """Continuously read from rule queue and update cache"""
        cache_storage = CacheStore()
        while not stop_event.is_set():
            try:
                if not rule_queue.empty():
                    raw_msg = rule_queue.get()
                    if raw_msg and isinstance(raw_msg, bytes) and len(raw_msg) > 0:
                        # logger.info(f"Processing sync message of {len(raw_msg)} bytes")
                        cache_storage.handle_sync_msg(raw_msg)
                    else:
                        logger.warning("Received invalid sync message")
                else:
                    # No messages available, yield control back to event loop
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing rule updates: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(0.1)
        
        logger.info("Rule update handler stopped")

    async def _run_async():
        try:            
            # Start the rule update handler as a background task
            rule_handler_task = asyncio.create_task(
                _handle_rule_updates()
            )
            
            # Create mitmproxy options
            opts = options.Options(listen_port=proxy_port)
            
            # Create dump master with addon
            addon_instance = HTTPInterceptorAddon(flow_queue, stop_event)
            dump_master = DumpMaster(opts, with_termlog=False, with_dumper=False)
            dump_master.addons.add(addon_instance)
            
            # Store dump_master in addon for graceful shutdown
            addon_instance.dump_master = dump_master            
            # Run until stop event is set
            try:
                await dump_master.run()
            except KeyboardInterrupt:
                logger.info("Mitmproxy process interrupted")
            finally:
                # Cancel the rule handler task
                rule_handler_task.cancel()
                try:
                    await rule_handler_task
                except asyncio.CancelledError:
                    logger.info("Rule handler task cancelled")
                
                # Ensure proper shutdown
                if hasattr(dump_master, 'shutdown'):
                    dump_master.shutdown()
            
        except Exception as e:
            logger.error(f"Error in mitmproxy process: {e}")
        finally:
            logger.info("Mitmproxy process finished")
    
    try:
        # Set up logging for the new process
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        # Run the async function in the new process's event loop
        asyncio.run(_run_async())
    except Exception as e:
        logger.error(f"Error in mitmproxy process: {e}")

class ProxyManager:
    def __init__(self, connection_manager: ConnectionManager, proxy_port: int = 8888):
        self.connection_manager = connection_manager
        self.proxy_port = proxy_port
        self.proxy_process: Optional[Process] = None
        

        self.flow_queue: Optional[SimpleQueue] = None  # Proxy -> Main (flow data)
        self.rule_queue: Optional[SimpleQueue] = None  # Main -> Proxy (rule updates)
        
        self.stop_event: Optional[Any] = None
        self.message_handler_task: Optional[asyncio.Task] = None
        self.is_running = False


    def _check_port_available(self, port: int) -> bool:
        """Check if a specific port is available"""
        # First, try to connect to see if something is already listening
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_sock:
                test_sock.settimeout(1)  # 1 second timeout
                result = test_sock.connect_ex(('127.0.0.1', port))
                if result == 0:  # Connection successful, port is in use
                    logger.debug(f"Port {port} is in use (something is listening)")
                    return False
        except Exception:
            pass  # Connection failed, which is good for availability check
        
        # Second, try to bind to see if we can use the port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('127.0.0.1', port))
                return True
        except OSError as e:
            logger.debug(f"Port {port} is not available: {e}")
            return False

    def _find_available_port(self, start_port: int = 8888, max_attempts: int = 100) -> int:
        """Find an available port starting from the given port"""
        for port in range(start_port, start_port + max_attempts):
            if self._check_port_available(port):
                return port
        raise RuntimeError(f"Could not find available port after {max_attempts} attempts")

    async def _handle_messages(self):
        while self.is_running:
            try:
                # Use non-blocking get to avoid blocking the event loop
                if not self.flow_queue.empty():
                    binary_message = self.flow_queue.get()
                    if binary_message == sentinel:  # Sentinel value to stop
                        return
                    await self.connection_manager.broadcast(binary_message)
                else:
                    # No messages available, yield control back to event loop
                    await asyncio.sleep(0.1)
            except queue.Empty:
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error handling flow message: {e}")
                await asyncio.sleep(0.1)

    async def start_proxy(self) -> bool:
        """Start the mitmproxy server in a separate process"""
        if self.is_running:
            logger.info("Proxy already running.")
            return True
        try:
            # Check if the requested port is available first
            if not self._check_port_available(self.proxy_port):
                # Find available port only if requested port is not available
                logger.info(f"Port {self.proxy_port} not available, searching for alternative port")
                actual_port = self._find_available_port(self.proxy_port + 1)
                logger.info(f"Using port {actual_port} instead of {self.proxy_port}")
                self.proxy_port = actual_port

            # Create two-queue system for high performance
            self.flow_queue = SimpleQueue()  # Proxy -> Main (flow data)
            self.rule_queue = SimpleQueue()  # Main -> Proxy (rule updates)
            self.stop_event = Event()

            # Start the mitmproxy process
            self.proxy_process = Process(
                target=run_mitmproxy_process,
                args=(self.proxy_port, self.flow_queue, self.rule_queue, self.stop_event),
                daemon=True
            )
            self.proxy_process.start()
            
            logger.info(f"Proxy process spawned.")

            # Start message handler task
            self.is_running = True
            self.message_handler_task = asyncio.create_task(self._handle_messages())
            
            # Give the process a moment to start - reduced sleep time
            await asyncio.sleep(0.5)
            
            # Verify process is still alive
            if not self.proxy_process.is_alive():
                logger.error("Mitmproxy process failed to start")
                self.is_running = False
                return {"success": False, "message": "Failed to start mitmproxy process"}
                
            logger.info(f"Proxy started successfully on port {self.proxy_port}")
            return True
        except Exception as e:
            logger.error(f"Error starting proxy: {e}")
            self.is_running = False
            return False

    async def stop_proxy(self) -> bool:
        """Stop the mitmproxy server process"""
        if not self.is_running:
            logger.info("Proxy not running.")
            return True

        logger.info("Stopping proxy server...")
        try:
            self.is_running = False
            
            # First, signal the addon to stop processing new requests
            if self.stop_event:
                self.stop_event.set()
            
            # Send sentinel value to stop message handler
            if self.flow_queue:
                self.flow_queue.put(sentinel) 
            
            # Cancel message handler task
            if self.message_handler_task:
                self.message_handler_task.cancel()
                try:
                    await self.message_handler_task
                except asyncio.CancelledError:
                    pass
            
            # Now stop the proxy process - it should shutdown gracefully
            if self.proxy_process and self.proxy_process.is_alive():
                # Give it time for graceful shutdown
                # self.proxy_process.join(timeout=3)
                
                # If still running, terminate
                if self.proxy_process.is_alive():
                    logger.warning("Terminating mitmproxy process")
                    self.proxy_process.terminate()
                    self.proxy_process.join(timeout=2)
                    
                    # Last resort - kill
                    if self.proxy_process.is_alive():
                        logger.warning("Force killing mitmproxy process")
                        self.proxy_process.kill()
                        self.proxy_process.join()
            
            # Clean up resources
            self.proxy_process = None
            self.flow_queue = None
            self.rule_queue = None
            self.stop_event = None
            self.message_handler_task = None
            
            logger.info("Proxy stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping proxy: {e}")
            return False

    def get_status(self) -> dict:
        """Get proxy status"""
        return {
            "is_running": self.is_running,
            "port": self.proxy_port,
            "process_alive": self.proxy_process.is_alive() if self.proxy_process else False,
            "port_available": self._check_port_available(self.proxy_port)
        }
    
    def sync_filter(self, filter: PyFilterModel, op_type: OperationType) -> bool:
        if not self.is_running:
            logger.error("Cannot update filter, proxy is not running")
            return False

        sync_message = PySyncMessage(operation=op_type, rules_list=[], filters_data=[filter])
        flat_sync_msg = serialize_sync_message(sync_message)
        self.rule_queue.put(flat_sync_msg)
        logger.info(f"Filter {filter.filter_name} synced to proxy")
        return True

    def sync_rule(self, rule: PyRuleModel, op_type: OperationType) -> bool:
        if not self.is_running:
            logger.error("Cannot sync rules, proxy is not running")
            return False

        sync_message = PySyncMessage(operation=op_type, rules_list=[rule], filters_data=[])
        flat_sync_msg = serialize_sync_message(sync_message)
        self.rule_queue.put(flat_sync_msg)
        logger.info(f"Rules {rule.rule_name} synced to proxy")
        return True
    
    def full_sync(self, filters: list[PyFilterModel], rules: list[PyRuleModel]) -> bool:
        if not self.is_running:
            logger.error("Cannot perform full sync, proxy is not running")
            return False

        logger.info(f"Creating full sync with {len(rules)} rules and {len(filters)} filters")
        flat_sync_msg = create_full_sync_message(rules, filters)        
        self.rule_queue.put(flat_sync_msg)
        logger.info("Full sync message sent to proxy")
        return True
