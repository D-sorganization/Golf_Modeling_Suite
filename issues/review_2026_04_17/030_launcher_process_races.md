# [HIGH] Launcher / process-manager: races, UI thread blocking, unclean subprocess handling

## Summary

`src/launchers/` and the task / docker managers have a number of
concurrency and resource-management defects that will manifest as
zombie processes, frozen UIs, or lost log output in production use.

## Findings

### 1. `running_processes` dict is not thread-safe

`src/launchers/launcher_process_manager.py:103-112` — used across
threads without a lock.

### 2. Subprocess failure does not clean up the `running_processes` entry

`launcher_process_manager.py` — if `Popen` raises after assignment,
a stale entry remains.

### 3. UI timer cleanup runs in the Qt event loop and does subprocess waits

`src/launchers/golf_launcher.py:130-132` — `QTimer` every 10 s calls
`_cleanup_processes()`. If cleanup does I/O, the GUI freezes.

### 4. Docker build thread is never joined

`src/launchers/docker_dialog.py:92-108` — thread started, never
waited for on dialog close. Orphan thread continues in background.

### 5. Race in `DockerBuildThread.start_build`

Multiple rapid calls can overwrite `self.build_thread` while the
previous is still running.

### 6. `DockerBuildThread.run` does not handle `subprocess.TimeoutExpired`

`src/launchers/docker_manager.py:70-131` — missing timeout exception
in the except clause; can hang indefinitely.

### 7. Task manager mixes sync Lock with asyncio Semaphore

`src/api/task_manager.py:76-78, 128-133` — `threading.Lock` held
while acquiring `asyncio.Semaphore`; easy to deadlock under load.

### 8. `PYTHONPATH` built by string concatenation from user paths

`launcher_process_manager.py:122-162` — user-provided paths not
`shlex.quote`d before concatenation. Paths containing `:` (drive
letter on Windows) or spaces break downstream.

### 9. `cwd` for subprocess is user-controlled but unvalidated

`launcher_process_manager.py:102-113` — if `context_path` is
attacker-controlled, arbitrary cwd.

### 10. Log-file truncation reads the entire file

`launcher_process_manager.py:200-212` — reads the whole log into
RAM to keep the last 500 lines. OOM risk on long-running processes.

### 11. Stacked `Process()` semaphore, no explicit cleanup

`task_manager.py:76-78` — `asyncio.Semaphore()` created; multiple
TaskManager instances accumulate.

### 12. Dashboard GUI calls physics engines on the UI thread

Multiple dashboards (`cross_engine_dashboard.py`, `drake_dashboard.py`,
`mujoco_dashboard.py`, `pinocchio_dashboard.py`) directly invoke
long-running simulations from button callbacks. Use
`QThreadPool`/`QRunnable` or `concurrent.futures` with a progress
signal.

### 13. Archive directory is committed

`src/launchers/_archive/` is in the tree. Either integrate it or
delete.

### 14. UI launchers shell out to python with relative paths that assume repo layout

`src/launchers/golf_suite_launcher.py` and friends assume a repo
layout; moving the installation breaks them.

## Impact

Users will observe frozen UIs on slow machines, orphan processes on
dialog close, and occasional deadlocks under concurrent load.

## Acceptance Criteria

- [ ] Guard `running_processes` with a `threading.Lock`.
- [ ] Clean up failed entries on `Popen` exception.
- [ ] Move cleanup timer work to a `QThreadPool` worker; UI only
      receives completed signals.
- [ ] Docker build thread: join on dialog close with a timeout;
      disable the Build button while running.
- [ ] Serialize `start_build` via a lock; block rapid repeats.
- [ ] Add `subprocess.TimeoutExpired` to the Docker build except.
- [ ] Task manager: drop the `threading.Lock`, use only
      `asyncio.Lock`, or use an `asyncio.Queue` for serialization.
- [ ] `shlex.quote` all subprocess path arguments.
- [ ] Validate `context_path` against an allow-list; reject symlinks.
- [ ] Rotate log files with `logging.handlers.RotatingFileHandler`;
      do not slurp the full log for truncation.
- [ ] Close the asyncio semaphore on TaskManager shutdown.
- [ ] Move every physics-engine call in dashboards to a worker
      thread/process; show a spinner while running.
- [ ] Either resurrect or remove `src/launchers/_archive/`.
- [ ] Launchers discover repo root via `importlib.resources` or a
      packaged data lookup, not hard-coded `Path(__file__).parent.parent`.

## Related

- Issue #029 — API server security.
- Issue #031 — repo-wide code quality including `except Exception:
  pass` patterns.
