from typing import List
from schemas import (
    FeasibilityFilterRequest, FeasibilityFilterResponse,
    InterventionFilterResult, InterventionCardSchema
)
from services.optimizer_service import INTERVENTIONS_DATASET
from mapdata import context_store

def run_feasibility_filters(payload: FeasibilityFilterRequest) -> FeasibilityFilterResponse:
    filter_matrix: List[InterventionFilterResult] = []
    viable_interventions: List[InterventionCardSchema] = []
    
    # Module 5 consumes ingested site-data when present and falls back to the
    # request-provided values otherwise (graceful fallback, non-breaking).
    budget_limit_inr = context_store.resolve_budget_limit(payload.budget_limit_inr)
    time_horizon_months = context_store.resolve_time_horizon_months(payload.time_horizon_months)

    candidates = [
        item for item in INTERVENTIONS_DATASET 
        if not payload.candidate_intervention_ids or item["id"] in payload.candidate_intervention_ids
    ]
    
    risk_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    max_risk_score = risk_rank.get(payload.max_risk_level.upper(), 3)

    for item in candidates:
        reasons = []
        
        # 1. Geographic Filter
        geo_pass = True
        if item.get("applicable_conditions"):
            conds = item["applicable_conditions"]
            if conds.get("piped_network") and payload.geography_id == "rural_only":
                geo_pass = False
                reasons.append("Requires urban/semi-urban piped distribution network.")
                
        # 2. Budget Filter (ingested target/max budget wins when present)
        budget_pass = item["cost_inr"] <= budget_limit_inr
        if not budget_pass:
            reasons.append(f"Cost ₹{(item['cost_inr']/1e7):.2f}Cr exceeds budget limit ₹{(budget_limit_inr/1e7):.2f}Cr.")

        # 3. Time Filter (ingested timeline wins when present)
        impl_time = item.get("implementation_time_months", 12)
        time_pass = impl_time <= time_horizon_months
        if not time_pass:
            reasons.append(f"Implementation time {impl_time} months exceeds {time_horizon_months}-month limit.")

        # 4. Risk & Regulatory Filter
        risk_lvl = item.get("risk_level", "LOW")
        risk_pass = risk_rank.get(risk_lvl, 1) <= max_risk_score
        if not risk_pass:
            reasons.append(f"Risk level '{risk_lvl}' exceeds maximum permitted '{payload.max_risk_level}'.")

        passed_all = geo_pass and budget_pass and time_pass and risk_pass

        filter_result = InterventionFilterResult(
            intervention_id=item["id"],
            intervention_name=item["name"],
            passed_all=passed_all,
            geographic_filter_pass=geo_pass,
            budget_filter_pass=budget_pass,
            time_filter_pass=time_pass,
            risk_filter_pass=risk_pass,
            failure_reasons=reasons
        )
        filter_matrix.append(filter_result)

        if passed_all:
            viable_interventions.append(InterventionCardSchema(**item))

    return FeasibilityFilterResponse(
        total_candidates=len(candidates),
        viable_candidates_count=len(viable_interventions),
        viable_interventions=viable_interventions,
        filter_matrix=filter_matrix
    )
