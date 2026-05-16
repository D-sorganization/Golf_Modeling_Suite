/**
 * ChatPanel - minimum-viable chat UI wired to the FastAPI chat WebSocket.
 *
 * #5469 - cross-shell parity: retry-on-error + quick-action buttons.
 * #5470 - app-state context injection is handled server-side in chat_ws.py.
 *
 * See issue #3505.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from 'react';
import { Send, MessageSquare, RotateCcw } from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ChatRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
}

export type ConnectionStatus =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'error';

interface ServerMessage {
  type: string;
  session_id?: string;
  content?: string;
  detail?: string;
  messages?: Array<{ role: ChatRole; content: string }>;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const RECONNECT_BASE_MS = 500;
const RECONNECT_MAX_MS = 30_000;

/**
 * Quick-action prompts surfaced as one-click buttons.
 * Mirrors QUICK_ACTIONS in AIAssistantPanel (PyQt) for #5469 cross-shell parity.
 */
// eslint-disable-next-line react-refresh/only-export-components
export const QUICK_ACTIONS: ReadonlyArray<{ label: string; prompt: string }> = [
  { label: 'Run Diagnostics', prompt: 'Run full launcher diagnostics and summarise the results.' },
  { label: 'Explain Error', prompt: 'Explain the last error message in simple terms.' },
  { label: 'Show Status', prompt: 'What is the current application health status?' },
];

/**
 * Resolve the chat WebSocket URL.
 *
 * Precondition: returns a non-empty ws:// or wss:// URL pointing at the
 * /ws/chat/{session_id} endpoint.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function resolveChatUrl(sessionId: string = 'new'): string {
  if (!sessionId || sessionId.trim().length === 0) {
    throw new Error('sessionId must be a non-empty string');
  }
  // Vite injects import.meta.env at build time. Default to localhost:8000.
  const base =
    (import.meta.env?.VITE_API_URL as string | undefined) ??
    'ws://localhost:8000';
  // Allow callers to set http(s) URLs for the API; convert to ws(s).
  const wsBase = base
    .replace(/^http:\/\//i, 'ws://')
    .replace(/^https:\/\//i, 'wss://')
    .replace(/\/+$/, '');
  return `${wsBase}/ws/chat/${sessionId}`;
}

function makeId(): string {
  // Lightweight unique id suitable for React keys.
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface ChatPanelProps {
  /** Optional engine context tag forwarded with each user message. */
  engineContext?: string;
  /** Override the resolved WebSocket URL (mostly for tests). */
  url?: string;
}

export function ChatPanel({ engineContext, url }: ChatPanelProps = {}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState<ConnectionStatus>('connecting');
  const [streaming, setStreaming] = useState(false);
  // ID of the most-recent error message eligible for retry (#5469 parity).
  const [retryMessageId, setRetryMessageId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedByUserRef = useRef(false);
  const assistantIdRef = useRef<string | null>(null);
  // Tracks the last user message so the retry button can re-send it (#5469).
  const lastUserMessageRef = useRef<string | null>(null);
  const listEndRef = useRef<HTMLDivElement | null>(null);

  const targetUrl = useMemo(() => url ?? resolveChatUrl('new'), [url]);

  // Append text to the in-flight assistant message (or start a new one).
  const appendAssistantChunk = useCallback((chunk: string) => {
    setMessages((prev) => {
      const currentId = assistantIdRef.current;
      if (currentId) {
        return prev.map((m) =>
          m.id === currentId ? { ...m, content: m.content + chunk } : m,
        );
      }
      const id = makeId();
      assistantIdRef.current = id;
      return [...prev, { id, role: 'assistant', content: chunk }];
    });
  }, []);

  const handleServerMessage = useCallback(
    (raw: string) => {
      let payload: ServerMessage;
      try {
        payload = JSON.parse(raw) as ServerMessage;
      } catch {
        return;
      }

      switch (payload.type) {
        case 'session_info':
        case 'session_created':
          if (payload.session_id) {
            setSessionId(payload.session_id);
          }
          break;
        case 'chunk':
          if (typeof payload.content === 'string') {
            setStreaming(true);
            appendAssistantChunk(payload.content);
          }
          break;
        case 'complete':
          assistantIdRef.current = null;
          setStreaming(false);
          // A successful response clears any pending retry target.
          setRetryMessageId(null);
          break;
        case 'history':
          if (Array.isArray(payload.messages)) {
            setMessages(
              payload.messages.map((m) => ({
                id: makeId(),
                role: m.role,
                content: m.content,
              })),
            );
          }
          break;
        case 'error': {
          // Capture the error message id so the retry button can reference it.
          const errorId = makeId();
          setRetryMessageId(errorId);
          setMessages((prev) => [
            ...prev,
            {
              id: errorId,
              role: 'system',
              content: payload.detail ?? 'Unknown error',
            },
          ]);
          setStreaming(false);
          assistantIdRef.current = null;
          break;
        }
        default:
          break;
      }
    },
    [appendAssistantChunk],
  );

  // Connect (and re-connect with exponential backoff).
  useEffect(() => {
    closedByUserRef.current = false;

    const connect = () => {
      setStatus('connecting');
      let socket: WebSocket;
      try {
        socket = new WebSocket(targetUrl);
      } catch {
        setStatus('error');
        scheduleReconnect();
        return;
      }
      wsRef.current = socket;

      socket.onopen = () => {
        reconnectAttemptsRef.current = 0;
        setStatus('connected');
      };
      socket.onmessage = (event: MessageEvent) => {
        handleServerMessage(String(event.data));
      };
      socket.onerror = () => {
        setStatus('error');
      };
      socket.onclose = () => {
        setStatus('disconnected');
        if (!closedByUserRef.current) {
          scheduleReconnect();
        }
      };
    };

    const scheduleReconnect = () => {
      const attempt = reconnectAttemptsRef.current + 1;
      reconnectAttemptsRef.current = attempt;
      const delay = Math.min(
        RECONNECT_BASE_MS * 2 ** (attempt - 1),
        RECONNECT_MAX_MS,
      );
      reconnectTimerRef.current = setTimeout(connect, delay);
    };

    connect();

    return () => {
      closedByUserRef.current = true;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch {
          // ignore
        }
        wsRef.current = null;
      }
    };
  }, [targetUrl, handleServerMessage]);

  // Auto-scroll to newest message. Guarded for jsdom where scrollIntoView
  // is not implemented.
  useEffect(() => {
    const node = listEndRef.current;
    if (node && typeof node.scrollIntoView === 'function') {
      node.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  /**
   * Core send helper. Optional *override* bypasses the controlled textarea
   * and skips adding a duplicate user bubble (used by quick-actions/retry).
   */
  const sendMessage = useCallback(
    (override?: string) => {
      const text = (override ?? input).trim();
      if (!text) return;
      const socket = wsRef.current;
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        setMessages((prev) => [
          ...prev,
          {
            id: makeId(),
            role: 'system',
            content: 'Not connected. Message not sent.',
          },
        ]);
        return;
      }

      if (!override) {
        // Only add a user bubble for typed messages, not quick-actions/retry.
        setMessages((prev) => [
          ...prev,
          { id: makeId(), role: 'user', content: text },
        ]);
      }

      const payload: Record<string, string> = { action: 'send', message: text };
      if (engineContext) {
        payload.engine_context = engineContext;
      }
      lastUserMessageRef.current = text;
      socket.send(JSON.stringify(payload));
      assistantIdRef.current = null;
      setStreaming(true);
      if (!override) setInput('');
    },
    [input, engineContext],
  );

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    sendMessage();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  /** Handle retry: remove error bubble and re-send the last user message. */
  const handleRetry = useCallback(() => {
    const msg = lastUserMessageRef.current;
    if (!msg) return;
    setMessages((prev) => prev.filter((m) => m.id !== retryMessageId));
    setRetryMessageId(null);
    sendMessage(msg);
  }, [retryMessageId, sendMessage]);

  const statusColor: Record<ConnectionStatus, string> = {
    connecting: 'text-yellow-400',
    connected: 'text-green-400',
    disconnected: 'text-gray-400',
    error: 'text-red-400',
  };
  const statusLabel: Record<ConnectionStatus, string> = {
    connecting: 'Connecting...',
    connected: 'Connected',
    disconnected: 'Disconnected',
    error: 'Error',
  };

  return (
    <div
      className="sidekick-chat-surface flex flex-col h-full w-full max-w-3xl rounded-lg border shadow-xl"
      style={{
        backgroundColor: 'var(--sidekick-color-surface)',
        borderColor: 'var(--sidekick-color-border)',
        color: 'var(--sidekick-color-text)',
      }}
      data-testid="chat-panel"
    >
      {/* Header */}
      <div
        className="sidekick-chat-header flex items-center justify-between p-3 border-b"
        style={{ borderBottomColor: 'var(--sidekick-color-border)' }}
      >
        <div className="flex items-center gap-2">
          <MessageSquare
            className="w-4 h-4"
            aria-hidden="true"
            style={{ color: 'var(--sidekick-color-accent)' }}
          />
          <span
            className="font-semibold text-sm"
            aria-label="Sidekick assistant"
            title="Sidekick assistant"
          >
            Chat
          </span>
          {sessionId && (
            <span
              className="text-[10px] font-mono"
              style={{ color: 'var(--sidekick-color-text-subtle)' }}
              title={`Session ${sessionId}`}
            >
              {sessionId.slice(0, 8)}
            </span>
          )}
        </div>
        <span
          className={`text-xs font-mono flex items-center gap-1 ${statusColor[status]}`}
          aria-live="polite"
          data-testid="chat-status"
        >
          <span
            aria-hidden
            style={{
              display: 'inline-block',
              width: 8,
              height: 8,
              borderRadius: '50%',
              background:
                status === 'connected'
                  ? 'var(--sidekick-color-success, #22c55e)'
                  : 'var(--sidekick-color-warning, #f59e0b)',
            }}
          />
          {statusLabel[status]}
        </span>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto p-3 space-y-2 text-sm"
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        aria-atomic="false"
        aria-label="Chat messages"
        data-testid="chat-messages"
      >
        {messages.length === 0 && (
          <div
            className="text-center pt-6"
            style={{ color: 'var(--sidekick-color-text-subtle)' }}
          >
            Start a conversation. Press Enter to send, Shift+Enter for newline.
          </div>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${
              m.role === 'user' ? 'items-end' : 'items-start'
            }`}
            data-role={m.role}
          >
            <div
              className="sidekick-chat-bubble max-w-[80%] rounded-lg px-3 py-2 whitespace-pre-wrap break-words border"
              data-role={m.role}
            >
              {m.content}
            </div>
            {/* Retry button on the most recent error message (#5469 parity) */}
            {m.id === retryMessageId && lastUserMessageRef.current && (
              <button
                type="button"
                onClick={handleRetry}
                aria-label="Retry last message"
                data-testid="chat-retry"
                disabled={status !== 'connected'}
                className="sidekick-chat-retry mt-1 flex items-center gap-1 text-xs px-2 py-1 rounded border disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <RotateCcw className="w-3 h-3" aria-hidden="true" />
                Retry
              </button>
            )}
          </div>
        ))}
        {streaming && (
          <div
            className="text-xs italic"
            style={{ color: 'var(--sidekick-color-text-subtle)' }}
            data-testid="chat-streaming"
          >
            assistant is typing...
          </div>
        )}
        <div ref={listEndRef} />
      </div>

      {/* Quick actions - mirrors QUICK_ACTIONS in AIAssistantPanel (#5469) */}
      <div
        className="sidekick-chat-quick-actions flex flex-wrap gap-1 px-3 pt-2"
        data-testid="chat-quick-actions"
      >
        {QUICK_ACTIONS.map(({ label, prompt }) => (
          <button
            key={label}
            type="button"
            aria-label={`Quick action: ${label}`}
            data-testid={`quick-action-${label.replace(/\s+/g, '-').toLowerCase()}`}
            disabled={status !== 'connected' || streaming}
            onClick={() => sendMessage(prompt)}
            className="text-xs px-2 py-1 rounded border disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {label}
          </button>
        ))}
      </div>

      {/* Composer */}
      <form
        onSubmit={handleSubmit}
        className="sidekick-chat-composer flex items-end gap-2 p-3 border-t"
        style={{ borderTopColor: 'var(--sidekick-color-border)' }}
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            status === 'connected'
              ? 'Ask a question...'
              : 'Waiting for connection...'
          }
          rows={2}
          aria-label="Message input"
          data-testid="chat-input"
          className="sidekick-focus-ring flex-1 resize-none rounded border px-2 py-1.5 text-sm focus:outline-none disabled:opacity-50"
          style={{
            backgroundColor: 'var(--sidekick-color-input)',
            borderColor: 'var(--sidekick-color-border)',
            color: 'var(--sidekick-color-text)',
          }}
          disabled={status !== 'connected'}
        />
        <button
          type="submit"
          aria-label="Send message"
          data-testid="chat-send"
          disabled={status !== 'connected' || input.trim().length === 0}
          className="sidekick-focus-ring flex items-center gap-1 px-3 py-1.5 rounded border disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-sm"
          style={{
            backgroundColor: 'var(--sidekick-color-accent)',
            borderColor: 'var(--sidekick-color-accent)',
            color: 'var(--sidekick-color-selection-text)',
          }}
        >
          <Send className="w-4 h-4" aria-hidden="true" />
          Send
        </button>
      </form>
    </div>
  );
}

export default ChatPanel;