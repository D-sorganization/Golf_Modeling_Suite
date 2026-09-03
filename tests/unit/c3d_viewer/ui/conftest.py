"""Per-directory conftest that pivots sys.path for the C3D viewer tests.

Mirrors the pivot used by ``tests/unit/engines/simscape/three_d_gui``
so the engine's ``src.apps.*`` namespace shadows the repo's top-level
``src.`` package when collecting/running the C3D viewer plot-style tests.

Issue: the bare top-level ``sys.modules["src"]`` entry is process-global.
Under ``pytest-xdist`` every worker is a single long-lived process that
collects and runs tests from *every* directory in the suite, so permanently
rebinding ``sys.modules["src"]`` here (as this file used to do at import
time, with no restore) leaked into unrelated tests that run later in the
same worker -- most visibly ``tests/scripts/test_validate_suite.py``, whose
``launch_upstream_drift._retry_parent_shared_alias_installer()`` does a bare
``import src`` and expects the *real* ``src/__init__.py``
(``_install_parent_shared_aliases``). If this directory's tests were
collected first in a given worker, that bare ``import src`` silently
resolved to this engine's package instead, which lacks the attribute.

The fix: every piece of process-global state the pivot touches -- the
``src``/``src.*`` and top-level ``shared``/``shared.*`` entries in
``sys.modules`` (including the unrelated ``src.<sub>`` modules the pivot
*evicts*) plus its ``sys.path`` additions -- is snapshotted on the
outermost enter and restored verbatim on the outermost exit, so the pivot
is only active while collecting or running an item that lives under this
directory. ``pytest_make_collect_report``, ``pytest_runtest_setup``,
and ``pytest_runtest_teardown`` are all directory-scoped by pytest itself
(a conftest's hooks are only consulted for collectors/items at or below its
own directory -- see the hookspec docs), so entering/exiting the pivot here
can never affect collection or tests anywhere else in the suite, regardless
of how xdist interleaves work across workers.
"""

from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("PYTEST_QT_API", "pyqt6")


def _pivot_sys_path() -> None:
    here = Path(__file__).resolve()
    # tests/unit/c3d_viewer/ui/conftest.py -> repo root is parents[4].
    repo_root = here.parents[4]
    engine_python = (
        repo_root
        / "src"
        / "engines"
        / "Simscape_Multibody_Models"
        / "3D_Golf_Model"
        / "python"
    )
    engine_src = engine_python / "src"
    if not engine_src.is_dir():
        return

    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
    import importlib

    # Pre-cache ``src``, ``src.shared``, ``src.shared.python`` and a few key
    # leaf modules so they survive the pivot below. Without ``src.shared``
    # itself in the keep set, ``from src import shared`` after the rebind
    # fails because the engine ``src/__init__.py`` has no ``shared`` attr.
    for qual in (
        "src",
        "src.shared",
        "src.shared.python",
        "sidekick.lab.bio.c3d_reader",
        "src.shared.python.qt_utils.wheel_event_filter",
        "src.shared.python.motion_matching.body_skeleton",
        "src.shared.python.plot_style",
    ):
        with contextlib.suppress(ImportError):
            sys.modules[qual] = importlib.import_module(qual)

    # Drop everything under ``src.`` that we don't want to keep, but keep
    # ``src.shared`` and everything beneath it so downstream conftests that
    # import ``src.shared.python.*`` still resolve.
    keep_prefix = "src.shared"
    for modname in list(sys.modules):
        if modname == "src" or modname.startswith("src."):
            if modname == keep_prefix or modname.startswith(keep_prefix + "."):
                continue
            del sys.modules[modname]

    import importlib.util as _util

    spec = _util.spec_from_file_location(
        "src",
        str(engine_src / "__init__.py"),
        submodule_search_locations=[str(engine_src)],
    )
    if spec is None or spec.loader is None:
        return
    src_mod = _util.module_from_spec(spec)
    sys.modules["src"] = src_mod
    spec.loader.exec_module(src_mod)
    repo_src = repo_root / "src"
    src_mod.__path__ = [str(engine_src), str(repo_src)]

    # Re-attach preserved ``src.<sub>`` modules as attributes on the freshly
    # rebound ``src`` package. CPython's ``from src import shared`` walks
    # ``src.__dict__`` first and raises ImportError if missing, even when
    # the submodule is present in ``sys.modules``.
    for modname, mod in list(sys.modules.items()):
        if not modname.startswith("src."):
            continue
        parts = modname.split(".")
        if len(parts) != 2:
            continue  # only attach direct children; nested attrs cascade
        setattr(src_mod, parts[1], mod)

    repo_src_str = str(repo_src)
    if repo_src_str not in sys.path:
        sys.path.append(repo_src_str)


# ---------------------------------------------------------------------------
# Directory-scoped pivot lifecycle. ``_pivot_sys_path`` mutates three pieces
# of process-global state: the ``src``/``src.*`` entries in ``sys.modules``
# (including *evicting* unrelated ``src.<sub>`` modules loaded by earlier
# tests in the same worker), the top-level ``shared``/``shared.*`` namespace
# (importable only while ``<repo>/src`` is on ``sys.path``), and ``sys.path``
# itself. The outermost enter snapshots those namespaces and records the
# ``sys.path`` entries the pivot adds; the outermost exit deletes whatever
# the pivot left in the namespaces, reinstates the snapshot verbatim
# (preserving module identity for ``importlib.reload`` and string-target
# ``monkeypatch.setattr`` in unrelated tests), and removes the added path
# entries. A depth counter makes entry/exit reentrant-safe across nested
# collectors (Package -> Module -> Class -> Function).
# ---------------------------------------------------------------------------
_PIVOT_NAMESPACES = ("src", "shared")
_SAVED_PIVOT_MODULES: dict[str, ModuleType] | None = None
_ADDED_SYS_PATH_ENTRIES: list[str] = []
_PIVOT_DEPTH = 0


def _in_pivot_namespace(modname: str) -> bool:
    return any(
        modname == ns or modname.startswith(ns + ".") for ns in _PIVOT_NAMESPACES
    )


def _enter_pivot() -> None:
    global _SAVED_PIVOT_MODULES, _PIVOT_DEPTH
    if _PIVOT_DEPTH == 0:
        _SAVED_PIVOT_MODULES = {
            name: mod for name, mod in sys.modules.items() if _in_pivot_namespace(name)
        }
        path_before = set(sys.path)
        _pivot_sys_path()
        _ADDED_SYS_PATH_ENTRIES[:] = [p for p in sys.path if p not in path_before]
    _PIVOT_DEPTH += 1


def _exit_pivot() -> None:
    global _SAVED_PIVOT_MODULES, _PIVOT_DEPTH
    _PIVOT_DEPTH -= 1
    if _PIVOT_DEPTH <= 0:
        _PIVOT_DEPTH = 0
        saved = _SAVED_PIVOT_MODULES if _SAVED_PIVOT_MODULES is not None else {}
        for modname in [name for name in sys.modules if _in_pivot_namespace(name)]:
            del sys.modules[modname]
        sys.modules.update(saved)
        for entry in _ADDED_SYS_PATH_ENTRIES:
            with contextlib.suppress(ValueError):
                sys.path.remove(entry)
        _ADDED_SYS_PATH_ENTRIES.clear()
        _SAVED_PIVOT_MODULES = None


@pytest.hookimpl(hookwrapper=True)
def pytest_make_collect_report(collector: pytest.Collector):
    """Keep the engine ``src`` shadow active only while collecting this dir.

    Directory-scoped by pytest: only consulted for collectors at or below
    this conftest's own directory, so it never touches unrelated modules'
    collection elsewhere in the suite.
    """
    _enter_pivot()
    try:
        yield
    finally:
        _exit_pivot()


def pytest_runtest_setup(item: pytest.Item) -> None:  # noqa: ARG001
    """Keep the engine ``src`` shadow active only while running this dir's tests.

    Directory-scoped by pytest the same way as ``pytest_make_collect_report``.
    """
    _enter_pivot()


def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> None:  # noqa: ARG001
    _exit_pivot()
