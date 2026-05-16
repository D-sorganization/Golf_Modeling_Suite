"""Launcher preferences subpages.

This package is the UpstreamDrift launcher's collection of preferences
panes. Most heavy lifting lives in shared Tools (`src/shared/python/...`)
— the modules here are thin embed wrappers so this launcher and the
Gasification_Model launcher render the same widget for shared concerns.

Public exports:
    * :class:`McpServersSection` — preferences pane for MCP server
      management. Wraps :class:`McpServersPrefsWidget` from Tools.
"""

from __future__ import annotations

from src.launchers.preferences.mcp_servers_section import McpServersSection

__all__ = ["McpServersSection"]
