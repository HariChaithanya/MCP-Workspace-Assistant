from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Monorepo root (parent of backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SETTINGS_FILE = PROJECT_ROOT / "backend" / "data" / "settings.json"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    workspace_path: str = Field(default="./sample-workspace", alias="WORKSPACE_PATH")
    github_personal_access_token: str = Field(
        default="", alias="GITHUB_PERSONAL_ACCESS_TOKEN"
    )


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()


def resolve_path(path: str, *, base: Path | None = None) -> Path:
    """Resolve a path to absolute. Relative paths use monorepo root as base."""
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = (base or PROJECT_ROOT) / candidate
    return candidate.resolve()


def validate_workspace_directory(path: str | Path) -> Path:
    """Ensure workspace exists and is a directory. Returns resolved absolute path."""
    resolved = resolve_path(str(path)) if not isinstance(path, Path) else path.resolve()

    if not resolved.exists():
        raise ValueError(f"Workspace path does not exist: {resolved}")
    if not resolved.is_dir():
        raise ValueError(f"Workspace path is not a directory: {resolved}")
    return resolved
