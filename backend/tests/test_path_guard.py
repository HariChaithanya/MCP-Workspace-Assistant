import pytest

from app.security.path_guard import PathAccessError, assert_tool_permitted, guard_read_path
from app.tools.filesystem_tools import read_file


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "README.md").write_text("# Demo", encoding="utf-8")
    (root / ".env").write_text("SECRET=1", encoding="utf-8")
    (root / "backend").mkdir()
    (root / "backend" / "main.py").write_text("print('ok')", encoding="utf-8")
    return root


def test_allows_file_inside_workspace(workspace):
    path = guard_read_path("README.md", workspace_root=workspace)
    assert path.name == "README.md"
    assert read_file("README.md", workspace_root=workspace) == "# Demo"


def test_rejects_env_file_even_inside_workspace(workspace):
    with pytest.raises(PathAccessError, match="sensitive file"):
        guard_read_path(".env", workspace_root=workspace)

    with pytest.raises(PathAccessError, match="sensitive file"):
        read_file(".env", workspace_root=workspace)


def test_rejects_path_outside_workspace(workspace):
    with pytest.raises(PathAccessError, match="outside the configured workspace"):
        guard_read_path("../outside.txt", workspace_root=workspace)


def test_rejects_windows_system_path(workspace):
    with pytest.raises(PathAccessError, match="system path|outside the configured workspace"):
        guard_read_path(r"C:\Windows\System32\drivers\etc\hosts", workspace_root=workspace)

    with pytest.raises(PathAccessError, match="system path|outside the configured workspace"):
        read_file(r"C:\Windows\System32\drivers\etc\hosts", workspace_root=workspace)


def test_rejects_forbidden_tools():
    with pytest.raises(PathAccessError, match="delete_file"):
        assert_tool_permitted("delete_file")

    with pytest.raises(PathAccessError, match="execute_command"):
        assert_tool_permitted("execute_command")
