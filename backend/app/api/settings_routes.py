from fastapi import APIRouter, HTTPException

from app.config import get_app_settings
from app.models import SettingsResponse, WorkspaceUpdateRequest
from app.settings_store import get_settings_store

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings() -> SettingsResponse:
    store = get_settings_store()
    app_settings = get_app_settings()

    try:
        workspace = store.get_workspace_path()
        workspace_exists = workspace.is_dir()
        workspace_path = str(workspace)
    except ValueError:
        workspace_exists = False
        workspace_path = app_settings.workspace_path

    return SettingsResponse(
        workspace_path=workspace_path,
        workspace_exists=workspace_exists,
        github_configured=bool(app_settings.github_personal_access_token.strip()),
    )


@router.post("/workspace", response_model=SettingsResponse)
def update_workspace(body: WorkspaceUpdateRequest) -> SettingsResponse:
    store = get_settings_store()
    app_settings = get_app_settings()

    try:
        resolved = store.set_workspace_path(body.workspace_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SettingsResponse(
        workspace_path=str(resolved),
        workspace_exists=True,
        github_configured=bool(app_settings.github_personal_access_token.strip()),
    )
