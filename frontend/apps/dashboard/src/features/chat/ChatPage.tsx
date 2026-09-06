import { useEffect, useRef, useState } from 'react';
import { EcoWebSocket, type WebSocketMessage } from '@eco/api';
import { Badge, Button, Card, CardBody, CardHeader, Input, Spinner } from '@eco/ui';

type ConnectionState = 'idle' | 'connecting' | 'connected' | 'disconnected';

export function ChatPage() {
  const wsRef = useRef<EcoWebSocket | null>(null);
  const [state, setState] = useState<ConnectionState>('idle');
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [input, setInput] = useState('');

  useEffect(() => {
    const ws = new EcoWebSocket();
    wsRef.current = ws;
    setState('connecting');

    const offOpen = ws.on('open', () => setState('connected'));
    const offClose = ws.on('close', () => setState('disconnected'));
    const offError = ws.on('error', () => setState('disconnected'));
    const offMessage = ws.on('message', (data: unknown) => {
      const message = data as WebSocketMessage;
      if (message && typeof message === 'object' && 'type' in message) {
        setMessages((prev) => [...prev, message]);
      }
    });

    ws.connect();

    return () => {
      offOpen();
      offClose();
      offError();
      offMessage();
      ws.disconnect();
    };
  }, []);

  const send = () => {
    if (!input.trim() || state !== 'connected') return;
    wsRef.current?.send('chat', { text: input, from: 'dashboard-user' });
    setInput('');
  };

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">💬 Real-time chat</h1>
        <p className="text-sm text-ink-muted">
          WebSocket session against <code className="rounded bg-surface-muted px-1">/ws/chat</code>.
        </p>
      </header>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <h2 className="text-base font-semibold">Session</h2>
            <Badge
              tone={
                state === 'connected'
                  ? 'success'
                  : state === 'connecting'
                    ? 'info'
                    : state === 'disconnected'
                      ? 'danger'
                      : 'neutral'
              }
              variant="soft"
            >
              {state}
            </Badge>
            {state === 'connecting' && <Spinner size="sm" />}
          </div>
        </CardHeader>
        <CardBody>
          <div className="mb-3 flex h-80 flex-col gap-2 overflow-y-auto rounded bg-surface-muted p-3 text-sm">
            {messages.length === 0 ? (
              <p className="m-auto text-ink-muted">No messages yet.</p>
            ) : (
              messages.map((m, idx) => (
                <div key={`${m.timestamp}-${idx}`} className="rounded bg-surface-raised px-3 py-2 shadow-soft">
                  <div className="text-[10px] uppercase tracking-wide text-ink-muted">
                    {m.type} · {new Date(m.timestamp).toLocaleTimeString()}
                  </div>
                  <pre className="overflow-auto text-[11px] text-ink">
                    {JSON.stringify(m.data, null, 2)}
                  </pre>
                </div>
              ))
            )}
          </div>

          <div className="flex gap-2">
            <Input
              placeholder="Type a message…"
              value={input}
              onChange={(e) => setInput((e.target as HTMLInputElement).value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              disabled={state !== 'connected'}
            />
            <Button onClick={send} disabled={state !== 'connected' || !input.trim()}>
              Send
            </Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}