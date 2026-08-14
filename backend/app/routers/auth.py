from fastapi import APIRouter, HTTPException
from schemas import (
    RegisterRequest, LoginRequest, OnboardingRequest,
    WorkspaceContextResponse, PersonaType
)
from services.auth_service import resolve_workspace_context

router = APIRouter(prefix="/auth", tags=["Module 1: Auth & Onboarding"])

USERS_DB = {}

@router.post("/register")
def register_user(payload: RegisterRequest):
    if payload.email in USERS_DB:
        raise HTTPException(status_code=400, detail="User email already registered")
    
    user_id = len(USERS_DB) + 1
    user_record = {
        "id": user_id,
        "email": payload.email,
        "name": payload.name,
        "persona": PersonaType.GOVERNMENT.value
    }
    USERS_DB[payload.email] = user_record
    return {"status": "registered", "user_id": user_id, "email": payload.email}

@router.post("/login")
def login_user(payload: LoginRequest):
    return {
        "status": "authenticated",
        "access_token": f"mock_bearer_token_for_{payload.email}",
        "user_id": 1,
        "persona": PersonaType.GOVERNMENT.value
    }

@router.get("/me")
def get_current_user_profile():
    return {
        "id": 1,
        "email": "officer@mp.gov.in",
        "name": "District Officer — Rewa",
        "persona": PersonaType.GOVERNMENT.value,
        "organization": "Madhya Pradesh Water Resources Dept",
        "jurisdiction": "Rewa District"
    }

@router.post("/onboarding", response_model=WorkspaceContextResponse)
def persona_onboarding(payload: OnboardingRequest):
    return resolve_workspace_context(
        persona=payload.persona,
        onboarding_data=payload,
        user_id=1
    )
