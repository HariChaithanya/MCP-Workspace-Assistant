"""Filesystem tool helpers — read paths are validated by path_guard before I/O."""

from pathlib import Path

from app.security.path_guard import PathAccessError, guard_read_path


def read_file(path: str, *, workspace_root: Path | None = None) -> str:
    """Read a text file after safety checks. Used by tests and Step 4 tools."""
    safe_path = guard_read_path(path, workspace_root=workspace_root)
    return safe_path.read_text(encoding="utf-8")


__all__ = ["PathAccessError", "read_file"]
