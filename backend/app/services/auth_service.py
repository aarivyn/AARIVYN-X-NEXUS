from typing import Optional
from schemas import PersonaType, OnboardingRequest, WorkspaceContextResponse

def resolve_workspace_context(persona: PersonaType, onboarding_data: Optional[OnboardingRequest] = None, user_id: int = 1) -> WorkspaceContextResponse:
    geography_name = "Rewa District, Madhya Pradesh"
    bbox = [81.1, 24.4, 81.5, 24.8]
    center = [24.6, 81.3]
    zoom = 10
    
    permission_scope = {
        "persona": persona.value,
        "read_map": True,
        "run_optimization": True,
        "view_provenance": True,
        "query_layer_filter": f"geography_id = 'rewa' AND persona_scope = '{persona.value}'"
    }

    if onboarding_data:
        if persona == PersonaType.GOVERNMENT and onboarding_data.government:
            gov = onboarding_data.government
            geography_name = f"{gov.target_district or 'Rewa'} District ({gov.admin_level.value} - {gov.role.value})"
            permission_scope["admin_level"] = gov.admin_level.value
            permission_scope["role"] = gov.role.value
        elif persona == PersonaType.CSR_FUNDER and (onboarding_data.csr_funder or onboarding_data.csr):
            csr = onboarding_data.csr_funder or onboarding_data.csr
            budget = csr.available_budget_inr or csr.available_budget or 100000000.0
            geography_name = f"{csr.target_geography} (Budget: ₹{(budget/1e7):.1f}Cr)"
            permission_scope["budget_cap_inr"] = budget
            permission_scope["focus_areas"] = csr.focus_areas
        elif persona == PersonaType.NGO and onboarding_data.ngo:
            ngo = onboarding_data.ngo
            geography_name = f"NGO Scope: {', '.join(ngo.operating_regions)} (Capacity: {ngo.implementation_capacity})"
            permission_scope["communities_served"] = ngo.communities_served
            permission_scope["focus_areas"] = ngo.focus_areas
        elif persona == PersonaType.STUDENT and onboarding_data.student:
            std = onboarding_data.student
            geography_name = f"Student Workspace: {std.region_of_interest} ({std.institution})"
            permission_scope["academic_mode"] = True
        elif persona == PersonaType.RESEARCHER and onboarding_data.researcher:
            res = onboarding_data.researcher
            geography_name = f"Research Workspace: {res.region_of_interest} ({res.institution})"
            permission_scope["research_mode"] = True
            permission_scope["raw_data_export"] = True
        elif persona == PersonaType.COMMUNITY and onboarding_data.community:
            comm = onboarding_data.community
            loc = comm.location or comm.location_name or "Rewa Village"
            geography_name = f"{loc} (Community Issue: {comm.problem_category.upper()})"
            permission_scope["zero_friction_mode"] = True

    return WorkspaceContextResponse(
        user_id=user_id,
        persona=persona,
        geography_name=geography_name,
        bbox=bbox,
        center=center,
        zoom=zoom,
        permission_scope=permission_scope
    )
