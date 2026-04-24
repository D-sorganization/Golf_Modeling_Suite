# Review Comments Archive - 2026-04-24

Generated: 2026-04-24T14:05:49.410926

## Reviewer (chatgpt-codex-connector[bot]) (2 comments)

### PR #3240: ui/README.md:27

Actionable: Yes
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Update quick-start URL to the configured Vite port**

The quick-start section says the UI is at `http://localhost:5173`, but `ui/package.json` defines `npm run dev` as `vite --port 5180`. Following this README step leads developers to the wrong address and makes a successful dev-server startup look broken.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3240#discussion_r3140284531)

---

### PR #3240: ui/README.md:72

Actionable: No
Has Suggestion: No

```
**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Replace invalid npm command for Tauri build**

The documented command `npm run tauri build` is not a valid script invocation and fails with `Missing script: "tauri"`; `npm run --help` shows the form `npm run <command> [-- <args>]`. In this repo the actual script is `tauri:build`, so the current instruction blocks desktop build setup.

Useful? React with 👍 / 👎.
```

[View on GitHub](https://github.com/D-sorganization/UpstreamDrift/pull/3240#discussion_r3140284533)

---

