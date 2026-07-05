"""Demo filesystem tools against sample-workspace."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.tools.filesystem_tools import (
    find_todos_impl,
    get_project_tree_impl,
    list_files_impl,
    read_file_impl,
    search_files_impl,
)

SAMPLE_WORKSPACE = BACKEND_ROOT.parent / "sample-workspace"


def run_tool(label: str, result: dict) -> None:
    print(f"\n=== {label} ===")
    print(json.dumps(result, indent=2))


def main() -> None:
    root = SAMPLE_WORKSPACE
    print(f"Using workspace: {root}")

    run_tool("list_files", list_files_impl(".", workspace_root=root))
    run_tool("read_file", read_file_impl("README.md", workspace_root=root))
    run_tool("search_files", search_files_impl("TODO", workspace_root=root))
    run_tool("get_project_tree", get_project_tree_impl(".", max_depth=3, workspace_root=root))
    run_tool("find_todos", find_todos_impl(".", workspace_root=root))


if __name__ == "__main__":
    main()
