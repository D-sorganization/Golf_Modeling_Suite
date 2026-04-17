# [CRITICAL] API security hardening: disabled-auth defaults, CORS, path-traversal, CSRF, input validation

## Summary

`src/api/` is the FastAPI server that fronts the simulation suite.
A number of security defaults, subtle bugs, and missing middlewares
mean the local-mode server is effectively open, and the production
path has several sharp edges.

## Findings

### 1. `GOLF_AUTH_DISABLED=true` is hardcoded in local-mode bootstrap

`src/api/local_server.py:42-43`

```python
os.environ.setdefault("GOLF_SUITE_MODE", "local")
os.environ.setdefault("GOLF_AUTH_DISABLED", "true")
```

This executes before any imports and disables auth for any process
that runs `local_server.py`. There is no way to re-enable it without
editing source. Make it configurable via the environment with
`local` being the *preferred* default, not a hard-wired constant.

### 2. CORS allows wildcard methods and headers with `allow_credentials=True`

`src/api/local_server.py:100-113`

```python
allow_origins=[...localhost...],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
```

Permissive for local only, but `allow_credentials=True` + wildcard
methods/headers is an anti-pattern. Enumerate the methods and headers
actually needed.

### 3. No CSRF middleware despite `allow_credentials=True`

If the auth token is in a cookie (any future plan where this could
be), credentialed cross-origin requests need CSRF protection. Nothing
currently protects state-changing POST / PATCH routes.

### 4. Path-traversal check is bypassable

`src/api/routes/launcher.py:156`

```python
if ".." in filename or "/" in filename or "\\" in filename:
```

URL-encoded traversal (`%2e%2e`) bypasses this; null bytes are not
checked. Replace with
`pathlib.Path(filename).resolve().is_relative_to(ASSETS_DIR)`.

### 5. API-key / JWT ambiguity at auth layer

`src/api/auth/dependencies.py:200-204` — `get_current_user_flexible`
treats prefixes starting with `gms_` as API keys and everything else
as JWT. An attacker crafting a JWT with any prefix gets it interpreted
as JWT; the branch logic does not fail closed.

### 6. Email lookup is case-sensitive

`src/api/routes/auth.py:51`

```python
db.query(User).filter(User.email == user_data.email)
```

RFC 5321 says local parts may be case-sensitive but domain is not.
Standard practice: store emails lowercased. Current code allows
`Alice@Example.com` and `alice@example.com` to be different users.

### 7. DB admin-user bootstrap is not idempotent

`src/api/database.py:66-98` — `init_db` creates an admin user; if
called twice, UNIQUE-constraint fails. Use `get_or_create` pattern.

### 8. `_TileModel` allows arbitrary attribute injection

`src/api/local_server.py:225-231` — `setattr(self, k, v)` from a
dict. A user-provided payload could inject `__dict__`, `__class__`
and other magic attrs. Use a pydantic model with `extra="forbid"`.

### 9. CORS origin / host validation is missing

`src/api/config.py:54-64` — split comma-separated env var, no
validation. `"localhost, *"` is accepted and silently bypasses
origin allow-listing.

### 10. Diagnostics endpoint has `response_model=None`

`src/api/routes/core.py:60` — `@router.get("/api/diagnostics",
response_model=None)` returns whatever internal state leaks. Use a
pydantic response model and explicitly name what ships to clients.

### 11. Logo / asset endpoint allows arbitrary filename

`src/api/routes/launcher.py:117, 159-173` — `FileResponse` without
restricting to whitelisted logo files. Symlinks inside ASSETS_DIR
could expose files outside.

### 12. Random JWT secret regenerated per-process in dev mode

`src/api/auth/security.py:47-52` — good as a fail-safe, but the
comment only surfaces in logs; users never see that tokens will die
on every restart. Emit a `DeprecationWarning`-level notice at each
endpoint access.

### 13. Upload-limits middleware does not catch `OverflowError`

`src/api/middleware/upload_limits.py:24` — `int(content_length)`
can raise `OverflowError` for `content_length = str(2**64)`.

### 14. `server.py:156` swallows programming errors

`except (TypeError, AttributeError): ... logger.error("Unexpected error")` —
these are programming errors that should bubble up, not be logged
and swallowed.

### 15. Docker image pinning relies on mutable tags

`Dockerfile:5` — `FROM continuumio/miniconda3:24.11.1-0`. Pin by
`sha256:` digest to prevent upstream drift.

### 16. Dockerfile runtime stage inherits builder toolchain

`Dockerfile:90-…` — copies from builder but builder still has
dev tools; risk of leaking build tools into runtime. Use explicit
COPY statements or a distroless base.

### 17. `docker-compose.yml` binds API to `0.0.0.0` without auth

`docker-compose.yml:21-23` — API_HOST=0.0.0.0 with
`GOLF_AUTH_DISABLED=true` inherited from local defaults.

### 18. CheckConstraint uses f-string with enum values

`src/api/auth/models.py:59-67` — `CheckConstraint(f"role IN
('{UserRole.FREE.value}', ...)")`. Enum values are safe now, but the
pattern is fragile. Use SQLAlchemy's `in_()`.

### 19. `install.sh` runs via `pipx install .` / `pip install .` without signature verification

Common pattern, but with no `--require-hashes`, `pip-audit`, or
checksum. Document the threat model.

## Impact

The local server is designed to be open on loopback, which is fine,
but the hard-wired-ness of "open" and the path-traversal and
attribute-injection defects are not OK even for local. Production
deployment is blocked by the cumulative findings.

## Acceptance Criteria

- [ ] Make `GOLF_AUTH_DISABLED` honored from the environment; default
      to `true` only if `GOLF_SUITE_MODE == local` AND the env var is
      unset.
- [ ] Enumerate explicit CORS methods/headers; keep `allow_credentials`
      only where needed.
- [ ] Add a minimal CSRF middleware on state-changing endpoints or
      switch to Authorization-header auth only.
- [ ] Rewrite path-traversal check using `pathlib.resolve().is_relative_to`.
- [ ] Fix API-key/JWT routing to fail-closed on ambiguous prefixes.
- [ ] Store emails lowercased; add a migration.
- [ ] `init_db` uses `get_or_create` for admin.
- [ ] Replace `_TileModel.setattr` with a strict pydantic model.
- [ ] Validate CORS origins / allowed hosts against `ipaddress` /
      URL parsing; reject wildcards where not intended.
- [ ] Diagnostics endpoint uses a named pydantic response model.
- [ ] Restrict logo endpoint to a fixed allow-list of filenames.
- [ ] Emit per-endpoint warning log when random JWT secret is in use.
- [ ] Handle `OverflowError` in upload-limits middleware.
- [ ] Remove `except (TypeError, AttributeError)` swallow in `server.py`.
- [ ] Pin Docker base image by digest; consider distroless runtime.
- [ ] Compose file: don't expose API on `0.0.0.0` by default.
- [ ] Replace `CheckConstraint` f-string with SQLAlchemy `in_()`.
- [ ] Document install.sh threat model in `SECURITY.md`.

## Related

- Issue #030 — launcher / subprocess / process-manager races.
- Issue #032 — repo hygiene & CI (pre-commit, dependency pinning).
