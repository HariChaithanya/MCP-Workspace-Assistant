"""MCP path wrapper — all MCP filesystem calls must pass through path_guard."""

from pathlib import Path

from app.security.path_guard import PathAccessError, guard_read_path


def secure_mcp_read_path(path: str | Path, *, workspace_root: Path | None = None) -> Path:
    """Validate an MCP filesystem read path before tool execution."""
    return guard_read_path(path, workspace_root=workspace_root)


__all__ = ["PathAccessError", "secure_mcp_read_path"]
