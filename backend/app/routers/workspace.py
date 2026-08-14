from fastapi import APIRouter, Query
from schemas import WorkspaceContextResponse, PersonaType
from services.auth_service import resolve_workspace_context

router = APIRouter(prefix="/workspace", tags=["Module 1: Workspace Resolver"])

@router.get("/current", response_model=WorkspaceContextResponse)
def get_current_workspace(persona: PersonaType = Query(PersonaType.GOVERNMENT)):
    return resolve_workspace_context(persona=persona, user_id=1)
