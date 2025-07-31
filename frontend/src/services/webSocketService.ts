// WebSocket Service with FlatBuffers support
// import flatBufferService from './flatBufferService.js';

import { AbstractWebSocketService } from "../models/types";
import flatBufferService from './flatBufferService';

class WebSocketService implements AbstractWebSocketService {
  private ws: WebSocket | null = null;
  private isConnecting: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;
  private listeners: Map<string, Set<Function>> = new Map();
  private messageQueue: any[] = [];
  private connectionPromise: Promise<void> | null = null;

  async connect(url: string = 'ws://localhost:8000/ws'): Promise<void> {
    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return Promise.resolve();
    }

    if (this.isConnecting) {
      console.log('WebSocket connection already in progress');
      return this.connectionPromise!;
    }

    this.connectionPromise = new Promise((resolve, reject) => {
      this.isConnecting = true;
      console.log(`Connecting to WebSocket: ${url}`);

      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('WebSocket connected successfully');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.connectionPromise = null;
        
        // Process queued messages
        this._processMessageQueue();
        
        // Notify listeners
        this._notifyListeners('connected', { status: 'connected' });
        
        resolve();
      };

      this.ws.onmessage = async (event: MessageEvent) => {
        try {
          // Check if it's binary data (FlatBuffers) - ONLY for HTTP flow data
          if (event.data instanceof Blob) {
            const arrayBuffer = await event.data.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);
            const flowData = flatBufferService.parseFlowMessage(uint8Array);
            
            if (flowData) {
              console.log('🚀 FlatBuffer HTTP flow received:', flowData.id);
              this._notifyListeners('http_flow', flowData);
            }
          } else {
            // Handle JSON data - for control messages, status, etc.
            const data = JSON.parse(event.data);
            console.log('📝 JSON message received:', data.type);
            this._notifyListeners('message', data);
            
            // Handle specific JSON message types (backward compatibility)
            if (data.type === 'new_request') {
              this._notifyListeners('request_intercepted', data.data);
            } else if (data.type === 'request_complete') {
              this._notifyListeners('request_updated', data.data);
            } else if (data.type === 'interception_status') {
              if (data.status === 'started') {
                this._notifyListeners('intercepting_started');
              } else if (data.status === 'stopped') {
                this._notifyListeners('intercepting_stopped');
              }
            }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = (event: CloseEvent) => {
        console.log('WebSocket connection closed:', event.code, event.reason);
        this.isConnecting = false;
        this.connectionPromise = null;
        this._notifyListeners('disconnected', { code: event.code, reason: event.reason });
        
        if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
          this._scheduleReconnect();
        }
      };

      this.ws.onerror = (error: Event) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        this.connectionPromise = null;
        this._notifyListeners('error', { error });
        reject(error);
      };
    });

    return this.connectionPromise;
  }

  disconnect(): void {
    if (this.ws) {
      console.log('Disconnecting WebSocket');
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.isConnecting = false;
    this.connectionPromise = null;
  }

  send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(typeof message === 'string' ? message : JSON.stringify(message));
    } else {
      console.log('WebSocket not connected, queuing message');
      this.messageQueue.push(message);
    }
  }

  // Event listener methods
  on(event: string, listener: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(listener);
  }

  off(event: string, listener: Function): void {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.delete(listener);
    }
  }

  private _notifyListeners(event: string, data?: any): void {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.forEach(listener => {
        try {
          listener(data);
        } catch (error) {
          console.error('Error in WebSocket listener:', error);
        }
      });
    }
  }

  private _processMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }

  private _scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  // Convenience methods
  ping(): void {
    this.send({ type: 'ping' });
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  getReadyState(): number {
    return this.ws ? this.ws.readyState : WebSocket.CLOSED;
  }
}

// Export singleton instance
export default new WebSocketService();
