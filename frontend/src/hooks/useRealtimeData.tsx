// Real-time Data Pipeline - WebSocket/SSE with automatic fallback

import { useState, useCallback, useRef, useEffect } from 'react';
import { useLang } from '../i18n/LanguageContext';
import type { Lang } from '../content/site';

export type ConnectionState =
  'connecting' | 'connected' | 'disconnected' | 'error' | 'reconnecting';

interface RealtimeOptions<T> {
  url: string;
  fallbackUrl?: string;
  onMessage?: (data: T) => void;
  onError?: (error: Error) => void;
  onStateChange?: (state: ConnectionState) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

interface RealtimeReturn<T> {
  data: T | null;
  state: ConnectionState;
  error: Error | null;
  send: (message: unknown) => void;
  reconnect: () => void;
  disconnect: () => void;
}

export function useRealtimeData<T = unknown>(options: RealtimeOptions<T>): RealtimeReturn<T> {
  const {
    url,
    fallbackUrl,
    onMessage,
    onError,
    onStateChange,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10,
    heartbeatInterval = 30000,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [state, setState] = useState<ConnectionState>('connecting');
  const [error, setError] = useState<Error | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const useSSEFallbackRef = useRef(false);
  const mountedRef = useRef(true);

  const updateState = useCallback(
    (newState: ConnectionState) => {
      if (!mountedRef.current) return;
      setState(newState);
      onStateChange?.(newState);
    },
    [onStateChange],
  );

  const handleMessage = useCallback(
    (message: MessageEvent | Event) => {
      if (!mountedRef.current) return;

      try {
        const parsed =
          typeof message === 'string'
            ? JSON.parse(message)
            : JSON.parse((message as MessageEvent).data);
        setData(parsed);
        onMessage?.(parsed);
      } catch (err) {
        console.warn('[Realtime] Failed to parse message:', err);
      }
    },
    [onMessage],
  );

  const handleError = useCallback(
    (err: Error) => {
      if (!mountedRef.current) return;
      setError(err);
      onError?.(err);
    },
    [onError],
  );

  const clearTimers = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback(() => {
    clearTimers();
    heartbeatTimerRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, heartbeatInterval);
  }, [clearTimers, heartbeatInterval]);

  const connectWebSocket = useCallback(() => {
    if (!mountedRef.current) return;

    try {
      updateState('connecting');
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        reconnectAttemptsRef.current = 0;
        updateState('connected');
        startHeartbeat();
      };

      ws.onmessage = handleMessage;

      ws.onerror = () => {
        if (!mountedRef.current) return;
        const err = new Error('WebSocket error');
        handleError(err);
        updateState('error');
      };

      ws.onclose = (event) => {
        if (!mountedRef.current) return;
        clearTimers();

        if (event.code !== 1000) {
          // Not a clean close
          if (reconnectAttemptsRef.current < maxReconnectAttempts) {
            updateState('reconnecting');
            reconnectAttemptsRef.current++;
            reconnectTimerRef.current = setTimeout(
              () => {
                if (!useSSEFallbackRef.current && fallbackUrl) {
                  // Try SSE fallback after a few WebSocket attempts
                  if (reconnectAttemptsRef.current >= 3) {
                    useSSEFallbackRef.current = true;
                    connectSSE();
                    return;
                  }
                }
                connectWebSocket();
              },
              reconnectInterval * Math.min(reconnectAttemptsRef.current, 5),
            );
          } else {
            updateState('disconnected');
            handleError(new Error('Max reconnection attempts reached'));
          }
        } else {
          updateState('disconnected');
        }
      };
    } catch (err) {
      if (!mountedRef.current) return;
      handleError(err instanceof Error ? err : new Error('Failed to create WebSocket'));
      updateState('error');
    }
  }, [
    url,
    fallbackUrl,
    maxReconnectAttempts,
    reconnectInterval,
    updateState,
    handleMessage,
    handleError,
    startHeartbeat,
    clearTimers,
  ]);

  const connectSSE = useCallback(() => {
    if (!mountedRef.current) return;

    try {
      updateState('connecting');
      const sseUrl = fallbackUrl || url;
      const es = new EventSource(sseUrl);
      esRef.current = es;

      es.onopen = () => {
        if (!mountedRef.current) return;
        reconnectAttemptsRef.current = 0;
        updateState('connected');
      };

      es.onmessage = (event) => {
        if (!mountedRef.current) return;
        handleMessage(event as unknown as MessageEvent);
      };

      es.onerror = () => {
        if (!mountedRef.current) return;
        es.close();
        clearTimers();

        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          updateState('reconnecting');
          reconnectAttemptsRef.current++;
          reconnectTimerRef.current = setTimeout(
            connectSSE,
            reconnectInterval * Math.min(reconnectAttemptsRef.current, 5),
          );
        } else {
          updateState('disconnected');
          handleError(new Error('Max SSE reconnection attempts reached'));
        }
      };
    } catch (err) {
      if (!mountedRef.current) return;
      handleError(err instanceof Error ? err : new Error('Failed to create EventSource'));
      updateState('error');
    }
  }, [
    url,
    fallbackUrl,
    maxReconnectAttempts,
    reconnectInterval,
    updateState,
    handleMessage,
    handleError,
    clearTimers,
  ]);

  const connect = useCallback(() => {
    useSSEFallbackRef.current = false;
    reconnectAttemptsRef.current = 0;
    if ('WebSocket' in window) {
      connectWebSocket();
    } else if (fallbackUrl) {
      connectSSE();
    }
  }, [connectWebSocket, connectSSE, fallbackUrl]);

  const send = useCallback((message: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const disconnect = useCallback(() => {
    mountedRef.current = false;
    clearTimers();
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
    updateState('disconnected');
  }, [clearTimers, updateState]);

  const reconnect = useCallback(() => {
    mountedRef.current = true;
    reconnectAttemptsRef.current = 0;
    useSSEFallbackRef.current = false;
    connect();
  }, [connect]);

  // Initial connection
  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [connect, disconnect]);

  return { data, state, error, send, reconnect, disconnect };
}

// Specialized hook for metrics
interface MetricData {
  area_ha: number;
  farmers_trained: number;
  co2_sequestered_tco2e: number;
  credits_issued: number;
  [key: string]: number;
}

export function useLiveMetrics(_language: Lang = 'fa') {
  void _language;
  const wsUrl = import.meta.env.VITE_WS_METRICS_URL || '';
  const sseUrl = import.meta.env.VITE_SSE_METRICS_URL || '';

  const { data, state, error, reconnect } = useRealtimeData<MetricData>({
    url: wsUrl,
    fallbackUrl: sseUrl,
    reconnectInterval: 10000,
    maxReconnectAttempts: 20,
    heartbeatInterval: 30000,
    onStateChange: (newState) => {
      console.log('[LiveMetrics] State:', newState);
    },
  });

  // Transform data for display
  const metrics = data
    ? {
        area_ha: data.area_ha || 0,
        farmers_trained: data.farmers_trained || 0,
        co2_sequestered_tco2e: data.co2_sequestered_tco2e || 0,
        credits_issued: data.credits_issued || 0,
      }
    : {
        area_ha: 0,
        farmers_trained: 0,
        co2_sequestered_tco2e: 0,
        credits_issued: 0,
      };

  return { metrics, state, error, reconnect, isLive: state === 'connected' };
}

// Connection status component
export function ConnectionStatusIndicator({ state }: { state: ConnectionState }) {
  const { lang } = useLang();

  const statusConfig = {
    connecting: {
      label: lang === 'fa' ? 'در حال اتصال...' : 'Connecting...',
      color: 'text-[var(--color-sand-400)]',
      icon: '⏳',
      pulse: true,
    },
    connected: {
      label: lang === 'fa' ? 'متصل' : 'Connected',
      color: 'text-[var(--color-leaf-400)]',
      icon: '🟢',
      pulse: false,
    },
    disconnected: {
      label: lang === 'fa' ? 'قطع شده' : 'Disconnected',
      color: 'text-red-400',
      icon: '🔴',
      pulse: false,
    },
    error: {
      label: lang === 'fa' ? 'خطا' : 'Error',
      color: 'text-red-400',
      icon: '⚠️',
      pulse: false,
    },
    reconnecting: {
      label: lang === 'fa' ? 'باز اتصال...' : 'Reconnecting...',
      color: 'text-[var(--color-sand-400)]',
      icon: '🔄',
      pulse: true,
    },
  };

  const config = statusConfig[state];

  return (
    <span
      className={`inline-flex items-center gap-1.5 ${config.color} font-medium text-sm`}
      role="status"
      aria-live="polite"
      aria-atomic="true"
      aria-label={config.label}
    >
      <span className={`transition-opacity ${config.pulse ? 'animate-pulse' : ''}`} aria-hidden>
        {config.icon}
      </span>
      <span>{config.label}</span>
    </span>
  );
}
