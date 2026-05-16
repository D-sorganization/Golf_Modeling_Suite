# Sidekick Chat Surface Parity

Tracks the parity status between the React (browser) and PyQt (desktop) chat
surfaces. Both surfaces connect to the same FastAPI WebSocket endpoint at
`/ws/chat/{session_id}`.

## Current state: PyQt surface

File: `src/shared/python/chat/_chat_dock_widget_qt.py`

| Feature | Status |
|---------|--------|
| WebSocket connect / reconnect (3 s fixed) | Present |
| Session ID — file-persisted + class-level shared | Present |
| `session_info` server message | Handled |
| `chunk` streaming | Handled (append_content) |
| `complete` message | Handled |
| `session_created` message | Handled |
| `history` message | Handled |
| `model_list` message | Handled (emits `models_refreshed` signal) |
| `index_status` message | Handled (emits `index_status_changed` signal) |
| `error` message | Handled (shown in status label) |
| `refresh_models` action | Sends |
| `index_codebase` action | Sends |
| Outgoing context field name | `app_context` |

## Current state: React surface

File: `ui/src/components/ui/ChatPanel.tsx`

| Feature | Status |
|---------|--------|
| WebSocket connect / reconnect (exp. backoff, 500ms..30s) | Present |
| Session ID — component state (not persisted to disk) | Present |
| `session_info` server message | Handled |
| `chunk` streaming | Handled (append to assistant message) |
| `complete` message | Handled |
| `session_created` message | Handled |
| `history` message | Handled |
| `model_list` message | **Missing** |
| `index_status` message | **Missing** |
| `error` message | Handled (shown as system role message) |
| `refresh_models` action | **Not sent** |
| `index_codebase` action | **Not sent** |
| Outgoing context field name | `engine_context` |

## Server surfaces

| File | `app_context` key | `engine_context` key |
|------|-------------------|---------------------|
| `src/api/routes/chat_ws.py` | Not read | Read |
| `src/shared/python/chat/router_factory.py` | Read (with `or` fallback) | Read (with `or` fallback) |

## Parity gaps found

### Gap 1 — `app_context` vs `engine_context` field name drift (CRITICAL)

- PyQt sends `app_context`; React sends `engine_context`.
- The shared `router_factory.py` correctly accepts both via
  `msg.get("app_context") or msg.get("engine_context")`.
- The app-level `src/api/routes/chat_ws.py` only reads `engine_context`,
  silently discarding `app_context` from PyQt clients.

**Fix:** Align `chat_ws.py` to read both keys, matching `router_factory.py`.
No client changes needed.

### Gap 2 — React missing `model_list` and `index_status` handler (MEDIUM)

The server pushes `model_list` responses to `refresh_models` requests and
periodic `index_status` events after `index_codebase`. React currently ignores
these frames (falls through the `default: break` branch), so:
- Model list updates are silently dropped.
- Codebase indexing progress is invisible in the browser UI.

**Fix:** Add `model_list` and `index_status` handlers to `handleServerMessage`
and expose them via the `ServerMessage` TypeScript interface.

### Gap 3 — React missing `refresh_models` / `index_codebase` actions (LOW)

PyQt auto-sends `refresh_models` on connect and can send `index_codebase`.
React never sends these. Until a React settings panel is added, this gap is
acceptable but must be documented.

**Deferred:** Sending `refresh_models` on connect is a low-risk improvement;
`index_codebase` requires a settings UI not yet present.

### Gap 4 — Reconnect strategy divergence (LOW)

PyQt uses a fixed 3-second reconnect timer. React uses exponential backoff
(500 ms → 30 s). Both strategies are valid; the divergence is intentional
and does not affect protocol correctness.

**No fix required.** Documented for awareness.

## What PR #5469 fixes

1. `src/api/routes/chat_ws.py` — accept both `app_context` and `engine_context`
   keys (Gap 1).
2. `ui/src/components/ui/ChatPanel.tsx` — add `model_list` and `index_status`
   to `ServerMessage` interface and `handleServerMessage` switch (Gap 2).
3. `tests/unit/chat/test_chat_parity.py` — TDD test suite covering the fixed
   gaps plus a schema round-trip test.
