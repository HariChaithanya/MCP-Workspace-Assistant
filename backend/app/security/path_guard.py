"""Path access control for filesystem and MCP tools."""

from __future__ import annotations

import os
import sys
from fnmatch import fnmatch
from pathlib import Path

from app.settings_store import get_settings_store

FORBIDDEN_TOOLS: frozenset[str] = frozenset({"delete_file", "execute_command"})

SECRET_FILENAMES: frozenset[str] = frozenset(
    {
        ".env",
        "credentials.json",
        "secrets.json",
        "id_rsa",
        "id_ed25519",
        "id_ecdsa",
        "id_dsa",
    }
)

SECRET_SUFFIXES: frozenset[str] = frozenset({".pem", ".key", ".p12", ".pfx"})

BLOCKED_DIR_NAMES: frozenset[str] = frozenset({".ssh"})


def _blocked_system_roots() -> list[Path]:
    roots: list[Path] = []

    if sys.platform == "win32":
        windir = os.environ.get("SystemRoot", r"C:\Windows")
        roots.extend(
            [
                Path(windir),
                Path(r"C:\Program Files"),
                Path(r"C:\Program Files (x86)"),
            ]
        )
    else:
        roots.extend(
            [
                Path("/etc"),
                Path("/usr"),
                Path("/var"),
                Path("/Users"),
                Path("/System"),
                Path("/Library"),
            ]
        )

    return [path.resolve() for path in roots if path.exists()]


def _normalize(path: Path) -> Path:
    return Path(os.path.normcase(str(path.resolve())))


class PathAccessError(PermissionError):
    """Raised when a path or tool is not allowed by the safety layer."""


class PathGuard:
    """Enforces workspace boundaries and blocks sensitive or system paths."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self._blocked_system_roots = [_normalize(path) for path in _blocked_system_roots()]

    @classmethod
    def from_settings(cls) -> PathGuard:
        workspace = get_settings_store().get_workspace_path()
        return cls(workspace)

    def resolve_read_path(self, path: str | Path) -> Path:
        """Resolve and validate a path for read access within the workspace."""
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            candidate = self.workspace_root / candidate

        resolved = candidate.resolve()

        if self._is_blocked_system_path(resolved):
            raise PathAccessError(f"Access to system path is blocked: {resolved}")

        if not self._is_within_workspace(resolved):
            raise PathAccessError(
                f"Path is outside the configured workspace ({self.workspace_root}): {resolved}"
            )

        if self._is_secret_path(resolved):
            raise PathAccessError(f"Access to sensitive file is blocked: {resolved}")

        return resolved

    def _is_within_workspace(self, path: Path) -> bool:
        normalized_path = _normalize(path)
        normalized_root = _normalize(self.workspace_root)
        try:
            normalized_path.relative_to(normalized_root)
            return True
        except ValueError:
            return False

    def _is_blocked_system_path(self, path: Path) -> bool:
        normalized_path = _normalize(path)
        for blocked_root in self._blocked_system_roots:
            try:
                normalized_path.relative_to(blocked_root)
                return True
            except ValueError:
                continue
        return False

    def _is_secret_path(self, path: Path) -> bool:
        if path.name == ".env.example":
            return False

        for part in path.parts:
            lowered = part.lower()
            if part in BLOCKED_DIR_NAMES or lowered in BLOCKED_DIR_NAMES:
                return True
            if part in SECRET_FILENAMES or lowered in SECRET_FILENAMES:
                return True
            if part.startswith(".env.") or lowered.startswith(".env."):
                return True

        name = path.name
        lowered_name = name.lower()
        if name in SECRET_FILENAMES or lowered_name in SECRET_FILENAMES:
            return True
        if name.startswith(".env.") or lowered_name.startswith(".env."):
            return True
        if fnmatch(lowered_name, ".env*") and lowered_name != ".env.example":
            return True

        suffix = path.suffix.lower()
        return suffix in SECRET_SUFFIXES


def assert_tool_permitted(tool_name: str) -> None:
    """Reject tools that must never run in the MVP."""
    if tool_name in FORBIDDEN_TOOLS:
        raise PathAccessError(f"Tool '{tool_name}' is disabled for safety reasons.")


def guard_read_path(path: str | Path, *, workspace_root: Path | None = None) -> Path:
    """Validate a read path using the configured or provided workspace root."""
    guard = PathGuard(workspace_root) if workspace_root else PathGuard.from_settings()
    return guard.resolve_read_path(path)
