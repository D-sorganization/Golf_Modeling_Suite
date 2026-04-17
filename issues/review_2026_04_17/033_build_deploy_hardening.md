# [MEDIUM] Build / deploy hardening: Dockerfile pinning, Cargo cross-repo path, requirements hygiene

## Summary

The build and deploy path has a number of smaller issues that add up:
a relative path to a sibling Git repo for Rust dependencies, an
unpinned conda base image, mixed conda+pip installs, no CI matrix
for platform coverage, and some compose-file defaults that should
be spelled out.

## Findings

### 1. `Cargo.toml` has a hard relative path to `../Tools/rust_core/tools-core`

`Cargo.toml:20` — this breaks local builds for anyone who does not
have Tools checked out side-by-side. CI appears to override it, but
there is no `git submodule` or `workspace = "../Tools"` — if the
other repo moves, every checkout breaks.

### 2. Dockerfile base image unpinned by digest

`Dockerfile:5` — `FROM continuumio/miniconda3:24.11.1-0`. Digest pin
(`@sha256:...`) prevents silent upstream drift.

### 3. Mixed conda + pip installs without coordinated pinning

`Dockerfile:58-86` — conda installs base packages, pip installs the
rest. No explicit separation or hash verification on the pip step.
If conda bumps transitive deps, pip may fight it.

### 4. Runtime stage inherits dev tools

`Dockerfile:90-…` — copies from builder stage; builder still has
compilers and toolchain. Consider a distroless final layer.

### 5. Docker CMD default is `/bin/bash`

`Dockerfile:168` — running the container as a service will fall into
a bash shell instead of starting the API. Set a sensible default
`CMD ["python", "-m", "uvicorn", "src.api.local_server:app", ...]`.

### 6. `docker-compose.yml` binds API to `0.0.0.0` with auth disabled

See also issue #029: `API_HOST=0.0.0.0` + `GOLF_AUTH_DISABLED=true`
inherited makes the compose'd API listen on all interfaces without
auth. Acceptable only if this compose file is strictly for local
dev and that is loudly documented.

### 7. Frontend compose service runs `npm install && npm run dev` per start

`docker-compose.yml:47` — `npm install` every start pulls nodemod
dependencies live. Pre-build a Docker image or mount a `node_modules`
volume.

### 8. No CI test of the produced Docker image

The `docker-security-scan.yml` workflow exists but does not follow
with an integration smoke test against the built image.

### 9. No CI matrix for macOS / Windows

`ci-standard.yml` is ubuntu-latest only; Drake and Pinocchio have
platform-specific APIs, and MuJoCo has known GL-context issues on
macOS. See also issue #032.

### 10. Windows / PowerShell launcher scripts are untested

- `launch_urdf_generator.bat`
- `src/engines/physics_engines/mujoco/run_gui.bat`
- `scripts/create_shortcut.ps1`
- `scripts/create_golf_robot_shortcut.ps1`
- `scripts/docker_migrate_names.ps1`
- `scripts/populate_refactor_issues.ps1`

Not exercised by CI. Likely rot over time.

### 11. No Linux equivalents of `.bat`/`.ps1` launchers

Users on Linux/Mac cannot use the shortcut patterns the Windows docs
advertise.

### 12. `install.sh` uses `pipx install .` or `pip3 install .` without hash verification

Good-faith script; tighten by calling with `--require-hashes` and
ship a `requirements-app.txt` with hashes, or document the install
threat model.

### 13. `requirements.lock` and `requirements-dev.lock` committed but stale

See also issue #032. These merge-conflict on every dep bump.

### 14. `build_hooks.py` is undocumented

`pyproject.toml` `[tool.hatch.build]` delegates to `build_hooks.py`
for UI bundling; `build_hooks.py` itself has no top-level docstring
explaining the process or failure modes.

### 15. Alembic migrations exist but no auto-migration on startup

`alembic.ini` + `src/api/migrations/` — `init_db` in
`src/api/database.py` creates tables via `SQLAlchemy.Base.create_all`
rather than running alembic. Schemas will drift unless alembic is
the source of truth.

### 16. `environment.yml` vs. `requirements.lock` — two install paths

Conda users and pip users see different resolved environments.
Document which is canonical and auto-regenerate the other.

## Impact

Builds are reproducible only in the CI environment that happened to
work. New contributors hit paper-cut after paper-cut.

## Acceptance Criteria

- [ ] Replace `Cargo.toml` relative path with a git submodule or a
      workspace-style pin; document how CI overrides.
- [ ] Pin Docker base image by `@sha256:` digest; document rotation
      policy.
- [ ] Separate conda `environment.yml` and pip `requirements.txt`
      explicitly; hash-pin the pip deps.
- [ ] Use a distroless runtime stage; do not include compilers in
      the final image.
- [ ] Set a concrete Docker CMD for production.
- [ ] Document or rework the compose services so default `up` is
      safe for local dev only, with loopback-only bind.
- [ ] Pre-build the frontend image; do not run `npm install` on
      each start.
- [ ] Follow the Docker security scan with an image-smoke-test in CI.
- [ ] Extend CI matrix to macOS and Windows (unit + headless GUI).
- [ ] Add shell-style or PowerShell-style CI to at least lint the
      Windows scripts.
- [ ] Create Linux/Mac equivalents for the `.bat`/`.ps1` launchers
      (shell scripts in `scripts/`).
- [ ] Tighten `install.sh` with hash-pinning or document threat model.
- [ ] Move lock-file generation to CI; remove from tree or pin per
      release tag (see issue #032).
- [ ] Document `build_hooks.py` at the top of the file with a
      description of the bundle steps.
- [ ] Make Alembic the canonical schema tool; run migrations on
      startup, remove `create_all`.

## Related

- Issue #029 — API-security hardening.
- Issue #032 — CI / docs / hygiene.
