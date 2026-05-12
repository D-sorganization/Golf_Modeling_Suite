# Review Comments Archive - 2026-05-12

Generated: 2026-05-12T14:33:03.957834

## Reviewer (chatgpt-codex-connector[bot]) (1 comments)

### PR #5306: src/shared/python/ai/gui/assistant_panel.py:1184

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Derive Ollama endpoint paths from host prefix**

Passing `chat_path="/v1/chat/completions"` and `embed_path="/v1/embeddings"` here breaks users who already configured `ollama_host` with a `/v1` suffix (e.g. `http://localhost:11434/v1`): `AIConfig.join_url` concatenates base+path, yielding `.../v1/v1/...` and 404s for both chat and embeddings (`rust_core/ai_backend/src/config.rs`, `join_url`). Before this chan...
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/5306#discussion_r3229979513)

---

