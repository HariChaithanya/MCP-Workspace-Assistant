from pathlib import Path

import pytest

from app.tools.filesystem_tools import (
    find_todos_impl,
    get_project_tree_impl,
    list_files_impl,
    read_file_impl,
    search_files_impl,
)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "README.md").write_text("# Demo project\n", encoding="utf-8")
    (root / "backend").mkdir()
    (root / "backend" / "main.py").write_text(
        "def run():\n    # TODO: implement handler\n    pass\n",
        encoding="utf-8",
    )
    (root / "frontend").mkdir()
    (root / "frontend" / "App.tsx").write_text(
        "// FIXME: add routing\nexport default function App() {}\n",
        encoding="utf-8",
    )
    return root


def test_list_files(workspace: Path) -> None:
    result = list_files_impl(".", workspace_root=workspace)
    assert result["status"] == "success"
    assert any("README.md" in entry for entry in result["files"])


def test_read_file(workspace: Path) -> None:
    result = read_file_impl("README.md", workspace_root=workspace)
    assert result["status"] == "success"
    assert "# Demo project" in result["content"]
    assert result["files"] == ["README.md"]


def test_search_files(workspace: Path) -> None:
    result = search_files_impl("TODO", workspace_root=workspace)
    assert result["status"] == "success"
    assert "backend/main.py" in result["files"]
    assert "TODO" in result["content"]


def test_get_project_tree(workspace: Path) -> None:
    result = get_project_tree_impl(".", max_depth=2, workspace_root=workspace)
    assert result["status"] == "success"
    assert "backend" in result["content"]
    assert any(path.startswith("backend/") for path in result["files"])


def test_find_todos(workspace: Path) -> None:
    result = find_todos_impl(".", workspace_root=workspace)
    assert result["status"] == "success"
    assert "backend/main.py" in result["files"]
    assert "frontend/App.tsx" in result["files"]
    assert "TODO" in result["content"]
    assert "FIXME" in result["content"]
