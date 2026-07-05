import json
from pathlib import Path

from app.config import PROJECT_ROOT, SETTINGS_FILE, get_app_settings, validate_workspace_directory


class SettingsStore:
    """Persists workspace selection to backend/data/settings.json."""

    def __init__(self, settings_file: Path = SETTINGS_FILE) -> None:
        self._settings_file = settings_file

    def _ensure_data_dir(self) -> None:
        self._settings_file.parent.mkdir(parents=True, exist_ok=True)

    def _read_raw(self) -> dict:
        if not self._settings_file.exists():
            return {}
        with self._settings_file.open(encoding="utf-8") as f:
            return json.load(f)

    def _write_raw(self, data: dict) -> None:
        self._ensure_data_dir()
        with self._settings_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

    def get_workspace_path(self) -> Path:
        stored = self._read_raw().get("workspace_path")
        if stored:
            return Path(stored)
        env_default = get_app_settings().workspace_path
        return validate_workspace_directory(env_default)

    def set_workspace_path(self, workspace_path: str) -> Path:
        resolved = validate_workspace_directory(workspace_path)
        self._write_raw({"workspace_path": str(resolved)})
        return resolved


_settings_store: SettingsStore | None = None


def get_settings_store() -> SettingsStore:
    global _settings_store
    if _settings_store is None:
        _settings_store = SettingsStore()
    return _settings_store
