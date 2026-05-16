/**
 * ChatPanel — minimum-viable chat UI wired to the FastAPI chat WebSocket.
 *
 * Backend protocol (see src/api/routes/chat_ws.py):
 *   Client -> Server:
 *     {"action": "send", "message": "...", "engine_context": "mujoco"?}
 *     {"action": "history"}
 *     {"action": "new_session"}
 *   Server -> Client:
 *     {"type": "session_info", "session_id": "..."}
 *     {"type": "chunk", "content": "..."}
 *     {"type": "complete", "session_id": "..."}
 *     {"type": "history", "messages": [...]}
 *     {"type": "error", "detail": "..."}
 *
 * Connects to {VITE_API_URL || ws://localhost:8000}/ws/chat/new with
 * exponential backoff reconnect (capped at 30 s).
 *
 * See issue #3505.
 *
 * Added in #5491:
 *   - react-markdown rendering for assistant bubbles
 *   - Retry connection button when status is error/disconnected
 *   - Quick-action buttons in empty state
 *   - onPaste clipboard image capture in composer
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ClipboardEvent,
  type FormEvent,
  type KeyboardEvent,
} from 'react';
import { Send, MessageSquare, RefreshCw, Paperclip, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';

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


interface PastedImage {
  /** Object URL for preview — revoke on removal. */
  objectUrl: string;
  /** Original filename or a generated fallback. */
  name: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const RECONNECT_BASE_MS = 500;
const RECONNECT_MAX_MS = 30_000;

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
// Quick-action definitions (#5491)
// ---------------------------------------------------------------------------

interface QuickAction {
  label: string;
  message: string;
}

const QUICK_ACTIONS: QuickAction[] = [
  { label: 'Summarize last run', message: 'Summarize the last simulation run.' },
  { label: 'Show FSP metrics', message: 'Show the current FSP metrics.' },
  { label: 'Compare engines', message: 'Compare the available physics engines for this scenario.' },
  { label: 'List parameters', message: 'List all configurable parameters for the active engine.' },
];

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
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [pastedImage, setPastedImage] = useState<PastedImage | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedByUserRef = useRef(false);
  const assistantIdRef = useRef<string | null>(null);
  const listEndRef = useRef<HTMLDivElement | null>(null);
  // Stable ref so the retry callback can always access the latest connect fn.
  const connectRef = useRef<(() => void) | null>(null);

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
        case 'error':
          setMessages((prev) => [
            ...prev,
            {
              id: makeId(),
              role: 'system',
              content: payload.detail ?? 'Unknown error',
            },
          ]);
          setStreaming(false);
          assistantIdRef.current = null;
          break;
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
      reconnectTimerRef.current = setTimeout(connect, delay); // tracked: #3505
    };

    connectRef.current = connect;
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


  // Revoke object URL on unmount to avoid memory leaks.
  useEffect(() => {
    return () => {
      if (pastedImage) {
        URL.revokeObjectURL(pastedImage.objectUrl);
      }
    };
  }, [pastedImage]);

  const sendMessage = useCallback(
    (overrideText?: string) => {
      const text = (overrideText ?? input).trim();
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

      setMessages((prev) => [
        ...prev,
        { id: makeId(), role: 'user', content: text },
      ]);
      const payload: Record<string, string> = { action: 'send', message: text };
      if (engineContext) {
        payload.engine_context = engineContext;
      }
      socket.send(JSON.stringify(payload));
      assistantIdRef.current = null;
      setStreaming(true);
      if (!overrideText) {
        setInput('');
      }
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


  /** Capture image/* items from clipboard paste in the composer (#5491). */
  const handlePaste = useCallback(
    (event: ClipboardEvent<HTMLTextAreaElement>) => {
      const items = Array.from(event.clipboardData?.items ?? []);
      const imageItem = items.find((item) => item.type.startsWith('image/'));
      if (!imageItem) return;

      event.preventDefault(); // do not paste as text
      const file = imageItem.getAsFile();
      if (!file) return;

      if (pastedImage) {
        URL.revokeObjectURL(pastedImage.objectUrl);
      }
      const objectUrl = URL.createObjectURL(file);
      const name =
        file.name && file.name !== 'image.png' ? file.name : 'pasted-image.png';
      setPastedImage({ objectUrl, name });
    },
    [pastedImage],
  );

  const removePastedImage = useCallback(() => {
    if (pastedImage) {
      URL.revokeObjectURL(pastedImage.objectUrl);
      setPastedImage(null);
    }
  }, [pastedImage]);

  /** Manual retry — cancel any pending backoff timer and reconnect now (#5491). */
  const handleRetry = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    reconnectAttemptsRef.current = 0;
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch {
        // ignore
      }
      wsRef.current = null;
    }
    connectRef.current?.();
  }, []);

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

  const showRetry = status === 'error' || status === 'disconnected';

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
        <div className="flex items-center gap-2">
          {/* Retry button — visible when disconnected or errored (#5491) */}
          {showRetry && (
            <button
              type="button"
              onClick={handleRetry}
              aria-label="Retry connection"
              data-testid="chat-retry"
              className="sidekick-focus-ring flex items-center gap-1 px-2 py-1 rounded border text-xs transition-colors"
              style={{
                backgroundColor: 'transparent',
                borderColor: 'var(--sidekick-color-warning, #f59e0b)',
                color: 'var(--sidekick-color-warning, #f59e0b)',
              }}
            >
              <RefreshCw className="w-3 h-3" aria-hidden="true" />
              Retry
            </button>
          )}

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
          <div className="flex flex-col items-center gap-4 pt-6">
            <p
              className="text-center text-sm"
              style={{ color: 'var(--sidekick-color-text-subtle)' }}
            >
              Start a conversation. Press Enter to send, Shift+Enter for newline.
            </p>

            {/* Quick-action buttons (#5491) */}
            <div
              className="flex flex-wrap justify-center gap-2"
              aria-label="Quick actions"
              data-testid="chat-quick-actions"
            >
              {QUICK_ACTIONS.map((qa) => (
                <button
                  key={qa.label}
                  type="button"
                  onClick={() => {
                    setInput(qa.message);
                    sendMessage(qa.message);
                  }}
                  disabled={status !== 'connected'}
                  className="sidekick-focus-ring px-3 py-1.5 rounded border text-xs transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  style={{
                    backgroundColor: 'var(--sidekick-color-surface-raised, #374151)',
                    borderColor: 'var(--sidekick-color-border)',
                    color: 'var(--sidekick-color-text)',
                  }}
                >
                  {qa.label}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex ${
              m.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
            data-role={m.role}
          >
            <div
              className={`sidekick-chat-bubble max-w-[80%] rounded-lg px-3 py-2 break-words border${
                m.role === 'assistant'
                  ? ' prose prose-invert prose-sm max-w-none'
                  : ' whitespace-pre-wrap'
              }`}
              style={{
                backgroundColor:
                  m.role === 'user'
                    ? 'var(--sidekick-color-accent)'
                    : m.role === 'assistant'
                      ? 'var(--sidekick-color-surface-raised)'
                      : 'var(--sidekick-color-warning)',
                borderColor:
                  m.role === 'system'
                    ? 'var(--sidekick-color-warning)'
                    : 'var(--sidekick-color-border)',
                color: 'var(--sidekick-color-text)',
              }}
              data-role={m.role}
            >
              {/* Render markdown for assistant messages only (#5491) */}
              {m.role === 'assistant' ? (
                <ReactMarkdown rehypePlugins={[rehypeSanitize]}>
                  {m.content}
                </ReactMarkdown>
              ) : (
                m.content
              )}
            </div>
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

      {/* Pasted image preview (#5491) */}
      {pastedImage && (
        <div
          className="flex items-center gap-2 px-3 py-2 border-t text-xs"
          style={{
            borderTopColor: 'var(--sidekick-color-border)',
            backgroundColor: 'var(--sidekick-color-surface-raised, #1f2937)',
          }}
          data-testid="chat-image-preview"
        >
          <Paperclip className="w-3 h-3 flex-shrink-0" aria-hidden="true" />
          <img
            src={pastedImage.objectUrl}
            alt="Pasted attachment preview"
            className="h-10 w-10 object-cover rounded border"
            style={{ borderColor: 'var(--sidekick-color-border)' }}
          />
          <span
            className="flex-1 truncate font-mono"
            style={{ color: 'var(--sidekick-color-text-subtle)' }}
            title={pastedImage.name}
          >
            {pastedImage.name}
          </span>
          <button
            type="button"
            onClick={removePastedImage}
            aria-label="Remove attachment"
            className="sidekick-focus-ring rounded p-0.5 transition-colors"
            style={{ color: 'var(--sidekick-color-text-subtle)' }}
          >
            <X className="w-3 h-3" aria-hidden="true" />
          </button>
        </div>
      )}

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
          onPaste={handlePaste}
          placeholder={
            status === 'connected'
              ? 'Ask a question... (paste an image to attach)'
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
