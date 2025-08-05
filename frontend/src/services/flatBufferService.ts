import { ByteBuffer } from 'flatbuffers';
import  { HttpFlow } from '../store/types';
import { HttpInterceptor } from '../models/events';

class FlatBufferService {
    /**
     * Deserialize incoming HTTP flow data from WebSocket (FlatBuffers)
     * This is the ONLY use case for FlatBuffers - high-frequency flow data
     */
    parseFlowMessage(binaryData: Uint8Array): HttpFlow | null {
        try {
            console.log("I am here")
            const buf = new ByteBuffer(binaryData);
            const message = HttpInterceptor.WebSocketMessage.getRootAsWebSocketMessage(buf);;
            const messageType = message.dataType();

            if (messageType !== HttpInterceptor.WebSocketMessageType.FlowData) {
                console.warn('Expected FLOW message, got:', messageType);
                return null;
            }

            const flowData = message.data(new HttpInterceptor.FlowData());
            if (!flowData) return null;

            // Extract headers
            const requestHeaders: Record<string, string>[] = [];
            for (let i = 0; i < flowData.requestHeadersLength(); i++) {
                const header = flowData.requestHeaders(i);
                const name = header?.key();
                const value = header?.value();
                if (name && value) {
                    requestHeaders.push({ name, value });
                }
            }

            const responseHeaders: Record<string, string>[] = [];
            for (let i = 0; i < flowData.responseHeadersLength(); i++) {
                const header = flowData.responseHeaders(i);
                const name = header?.key();
                const value = header?.value();
                if (name && value) {
                    responseHeaders.push({ name, value });
                }
            }

            const requestSize = flowData.requestSize() || 0;
            const responseSize = flowData.responseSize() || 0;

            return {
                id: flowData.id() ?? '',
                method: flowData.method() ?? '',
                url: flowData.url() ?? '',
                status: flowData.status(),
                duration: this.getDuration(flowData.startTimestamp(), flowData.endTimestamp()),
                requestSize: this.formatBytes(requestSize),
                responseSize: this.formatBytes(responseSize),
                requestHeaders,
                responseHeaders,
                requestBody: flowData.requestBody() ?? '',
                responseBody: flowData.responseBody() ?? '',
                cookies: this.getCookies(responseHeaders),
                isIntercepted: flowData.isIntercepted() ?? false
            };
        } catch (error) {
            console.error('Failed to parse FlatBuffer flow message:', error);
            return null;
        }
    }

    private getDuration(startTime: number, endTime: number): string {
        const start = new Date(startTime);
        const end = new Date(endTime);
        const duration = end.getTime() - start.getTime();
        return `${duration} ms`;
    }

    private getCookies(headers: Record<string, string>[]): Record<string, string>[] {
        const cookies: Record<string, string>[] = [];
        headers.forEach(header => {
            if (header.name.toLowerCase() === 'set-cookie') {
                const cookieParts = header.value.split(';');
                cookieParts.forEach(part => {
                    const [key, value] = part.split('=');
                    if (key && value) {
                        cookies.push({ name: key.trim(), value: value.trim() });
                    }
                });
            }
        });
        return cookies;
    }

    private formatBytes(bytes: number): string {
      if (bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
}

export default new FlatBufferService();
