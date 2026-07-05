"""Filesystem tools for the workspace assistant agent."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from app.security.path_guard import PathAccessError, PathGuard, guard_read_path
from app.settings_store import get_settings_store

MAX_FILE_BYTES = 500 * 1024
DEFAULT_TREE_DEPTH = 4
TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK)\b", re.IGNORECASE)
SKIP_DIR_NAMES = frozenset(
    {".git", "__pycache__", "node_modules", ".venv", "venv", ".pytest_cache"}
)


def _success(tool: str, *, files: list[str] | None = None, content: str = "") -> dict[str, Any]:
    return {
        "tool": tool,
        "files": files or [],
        "content": content,
        "status": "success",
    }


def _error(tool: str, message: str) -> dict[str, Any]:
    return {
        "tool": tool,
        "files": [],
        "content": message,
        "status": "error",
    }


def _guard(workspace_root: Path | None = None) -> PathGuard:
    if workspace_root:
        return PathGuard(workspace_root)
    return PathGuard.from_settings()


def _workspace_root(workspace_root: Path | None = None) -> Path:
    if workspace_root:
        return workspace_root.resolve()
    return get_settings_store().get_workspace_path()


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _is_probably_binary(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            chunk = handle.read(8192)
        if b"\x00" in chunk:
            return True
        chunk.decode("utf-8")
        return False
    except (UnicodeDecodeError, OSError):
        return True


def _read_text(path: Path) -> str:
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise ValueError(
            f"File exceeds maximum size of {MAX_FILE_BYTES // 1024} KB: {path.name}"
        )
    if _is_probably_binary(path):
        raise ValueError(f"Binary file skipped: {path.name}")
    return path.read_text(encoding="utf-8")


def _should_skip(guard: PathGuard, path: Path) -> bool:
    if path.name in SKIP_DIR_NAMES:
        return True
    if guard._is_secret_path(path):
        return True
    return False


def _iter_files(guard: PathGuard, root: Path) -> list[Path]:
    files: list[Path] = []
    for current in root.rglob("*"):
        if not guard._is_within_workspace(current):
            continue
        if any(part in SKIP_DIR_NAMES for part in current.parts):
            continue
        if guard._is_secret_path(current):
            continue
        if current.is_file() and not _is_probably_binary(current):
            files.append(current)
    return files


def list_files_impl(path: str = ".", *, workspace_root: Path | None = None) -> dict[str, Any]:
    tool_name = "list_files"
    try:
        guard = _guard(workspace_root)
        root = _workspace_root(workspace_root)
        target = guard.resolve_read_path(path)
        if not target.is_dir():
            return _error(tool_name, f"Path is not a directory: {path}")

        entries: list[str] = []
        for entry in sorted(target.iterdir(), key=lambda p: p.name.lower()):
            if _should_skip(guard, entry):
                continue
            prefix = "dir" if entry.is_dir() else "file"
            entries.append(f"{prefix}:{_relative(entry, root)}")

        return _success(tool_name, files=entries, content=f"Listed {len(entries)} entries in {path}")
    except PathAccessError as exc:
        return _error(tool_name, str(exc))
    except Exception as exc:
        return _error(tool_name, f"Failed to list files: {exc}")


def read_file_impl(path: str, *, workspace_root: Path | None = None) -> dict[str, Any]:
    tool_name = "read_file"
    try:
        safe_path = guard_read_path(path, workspace_root=workspace_root)
        if not safe_path.is_file():
            return _error(tool_name, f"Path is not a file: {path}")
        content = _read_text(safe_path)
        root = _workspace_root(workspace_root)
        return _success(
            tool_name,
            files=[_relative(safe_path, root)],
            content=content,
        )
    except PathAccessError as exc:
        return _error(tool_name, str(exc))
    except ValueError as exc:
        return _error(tool_name, str(exc))
    except Exception as exc:
        return _error(tool_name, f"Failed to read file: {exc}")


def search_files_impl(query: str, *, workspace_root: Path | None = None) -> dict[str, Any]:
    tool_name = "search_files"
    if not query.strip():
        return _error(tool_name, "Search query must not be empty.")

    try:
        guard = _guard(workspace_root)
        root = _workspace_root(workspace_root)
        query_lower = query.lower()
        matches: list[str] = []
        snippets: list[str] = []

        for file_path in _iter_files(guard, root):
            try:
                if file_path.stat().st_size > MAX_FILE_BYTES:
                    continue
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            rel = _relative(file_path, root)
            file_hits: list[str] = []
            for line_no, line in enumerate(text.splitlines(), start=1):
                if query_lower in line.lower():
                    file_hits.append(f"{rel}:{line_no}: {line.strip()}")
            if file_hits:
                matches.append(rel)
                snippets.extend(file_hits[:5])

        content = "\n".join(snippets) if snippets else f"No matches found for '{query}'."
        return _success(tool_name, files=matches, content=content)
    except PathAccessError as exc:
        return _error(tool_name, str(exc))
    except Exception as exc:
        return _error(tool_name, f"Search failed: {exc}")


def get_project_tree_impl(
    root_path: str = ".",
    max_depth: int = DEFAULT_TREE_DEPTH,
    *,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    tool_name = "get_project_tree"
    try:
        guard = _guard(workspace_root)
        root = _workspace_root(workspace_root)
        start = guard.resolve_read_path(root_path)
        if not start.is_dir():
            return _error(tool_name, f"Path is not a directory: {root_path}")

        lines: list[str] = []
        files: list[str] = []

        def walk(directory: Path, prefix: str, depth: int) -> None:
            if depth > max_depth:
                lines.append(f"{prefix}... (depth limit reached)")
                return

            children = sorted(directory.iterdir(), key=lambda p: p.name.lower())
            visible = [child for child in children if not _should_skip(guard, child)]
            for index, child in enumerate(visible):
                is_last = index == len(visible) - 1
                branch = "└── " if is_last else "├── "
                lines.append(f"{prefix}{branch}{child.name}")
                rel = _relative(child, root)
                if child.is_dir():
                    files.append(rel + "/")
                    extension = "    " if is_last else "│   "
                    walk(child, prefix + extension, depth + 1)
                else:
                    files.append(rel)

        lines.append(start.name + "/")
        walk(start, "", 1)
        return _success(tool_name, files=files, content="\n".join(lines))
    except PathAccessError as exc:
        return _error(tool_name, str(exc))
    except Exception as exc:
        return _error(tool_name, f"Failed to build project tree: {exc}")


def find_todos_impl(root_path: str = ".", *, workspace_root: Path | None = None) -> dict[str, Any]:
    tool_name = "find_todos"
    try:
        guard = _guard(workspace_root)
        root = _workspace_root(workspace_root)
        start = guard.resolve_read_path(root_path)
        scan_root = start if start.is_dir() else start.parent

        matches: list[str] = []
        snippets: list[str] = []

        for file_path in _iter_files(guard, scan_root):
            if not file_path.is_relative_to(scan_root.resolve()):
                continue
            try:
                if file_path.stat().st_size > MAX_FILE_BYTES:
                    continue
                text = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            rel = _relative(file_path, root)
            for line_no, line in enumerate(text.splitlines(), start=1):
                if TODO_PATTERN.search(line):
                    entry = f"{rel}:{line_no}: {line.strip()}"
                    matches.append(rel)
                    snippets.append(entry)

        unique_files = sorted(set(matches))
        content = "\n".join(snippets) if snippets else "No TODO, FIXME, or HACK comments found."
        return _success(tool_name, files=unique_files, content=content)
    except PathAccessError as exc:
        return _error(tool_name, str(exc))
    except Exception as exc:
        return _error(tool_name, f"Failed to find TODOs: {exc}")


@tool
def list_files(path: str = ".") -> dict[str, Any]:
    """List files and directories at a path relative to the workspace root."""
    return list_files_impl(path)


@tool
def read_file(path: str) -> dict[str, Any]:
    """Read a text file from the workspace. Skips binary files and files over 500 KB."""
    return read_file_impl(path)


@tool
def search_files(query: str) -> dict[str, Any]:
    """Search workspace text files for a query string (case-insensitive)."""
    return search_files_impl(query)


@tool
def get_project_tree(root_path: str = ".", max_depth: int = DEFAULT_TREE_DEPTH) -> dict[str, Any]:
    """Return an ASCII directory tree for the workspace, limited by max_depth."""
    return get_project_tree_impl(root_path, max_depth=max_depth)


@tool
def find_todos(root_path: str = ".") -> dict[str, Any]:
    """Find TODO, FIXME, and HACK comments under a workspace path."""
    return find_todos_impl(root_path)


FILESYSTEM_TOOLS = [list_files, read_file, search_files, get_project_tree, find_todos]

__all__ = [
    "FILESYSTEM_TOOLS",
    "find_todos",
    "find_todos_impl",
    "get_project_tree",
    "get_project_tree_impl",
    "list_files",
    "list_files_impl",
    "read_file",
    "read_file_impl",
    "search_files",
    "search_files_impl",
]
