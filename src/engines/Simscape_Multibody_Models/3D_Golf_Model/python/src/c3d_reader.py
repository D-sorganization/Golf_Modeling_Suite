"""Backwards-compatible shim. Use the canonical reader instead.

This module re-exports the canonical C3DDataReader from
src/shared/python/upstream_drift_tools/lab/bio/c3d_reader.py

See issue #4484 for the consolidation of duplicate C3D readers.
"""
from src.shared.python.upstream_drift_tools.lab.bio.c3d_reader import *  # noqa: F401,F403