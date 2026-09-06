/**
 * Lightweight WebSocket client with auto-reconnect + typed event listeners.
 *
 * Used by the AI chat panel (`/ws/chat` per backend).
 */

export interface WebSocketMessage {
  type: string;
  data: unknown;
  timestamp: string;
}

type EventName = 'open' | 'message' | 'close' | 'error' | string;
type Listener = (data: unknown) => void;

const DEFAULT_URL = (() => {
  const base =
    (typeof import.meta !== 'undefined' &&
      (import.meta as { env?: Record<string, string | undefined> }).env?.['VITE_WS_URL']) ||
    'ws://localhost:8000';
  return `${base}/ws/chat`;
})();

export class EcoWebSocket {
  private ws: WebSocket | null = null;
  private listeners = new Map<EventName, Set<Listener>>();
  private retryHandle: ReturnType<typeof setTimeout> | null = null;
  private destroyed = false;

  constructor(private readonly url: string = DEFAULT_URL) {}

  connect(): void {
    if (this.destroyed) return;
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.emit('open', null);
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const parsed = JSON.parse(event.data) as WebSocketMessage;
        this.emit(parsed.type, parsed.data);
        this.emit('message', parsed);
      } catch (error) {
        this.emit('error', error);
      }
    };

    this.ws.onerror = (error) => {
      this.emit('error', error);
    };

    this.ws.onclose = () => {
      this.emit('close', null);
      if (!this.destroyed) {
        this.retryHandle = setTimeout(() => this.connect(), 5000);
      }
    };
  }

  disconnect(): void {
    this.destroyed = true;
    if (this.retryHandle) clearTimeout(this.retryHandle);
    this.ws?.close();
    this.ws = null;
  }

  send(type: string, data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const message: WebSocketMessage = {
        type,
        data,
        timestamp: new Date().toISOString(),
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  on(event: EventName, callback: Listener): () => void {
    let set = this.listeners.get(event);
    if (!set) {
      set = new Set();
      this.listeners.set(event, set);
    }
    set.add(callback);
    return () => {
      set?.delete(callback);
    };
  }

  private emit(event: EventName, data: unknown): void {
    this.listeners.get(event)?.forEach((cb) => {
      try {
        cb(data);
      } catch (err) {
        // Listener errors must not crash the socket
        console.error(`EcoWebSocket listener error for "${event}":`, err);
      }
    });
  }
}

export const ecoWebSocket = new EcoWebSocket();