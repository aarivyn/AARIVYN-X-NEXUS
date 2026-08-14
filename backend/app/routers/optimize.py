from fastapi import APIRouter
from schemas import OptimizeRunRequest, OptimizeRunResponse
from services.optimizer_service import run_nsga2_optimization, INTERVENTIONS_DATASET
from services.feasibility_service import run_feasibility_filters, FeasibilityFilterRequest
from mapdata import context_store

router = APIRouter(prefix="/optimize", tags=["Module 6: NSGA-II Multi-Objective Optimizer"])

@router.post("/run", response_model=OptimizeRunResponse)
def run_optimization_pipeline(payload: OptimizeRunRequest):
    # Module 6 consumes the ingested budget singleton when present.
    budget = context_store.resolve_budget_limit(payload.budget_limit_inr)

    filter_req = FeasibilityFilterRequest(
        candidate_intervention_ids=[],
        geography_id=payload.geography_id,
        budget_limit_inr=payload.budget_limit_inr,
        time_horizon_months=payload.time_horizon_months,
        max_risk_level="HIGH"
    )
    filter_res = run_feasibility_filters(filter_req)
    viable_dicts = [i.dict() for i in filter_res.viable_interventions]
    
    portfolios_raw = run_nsga2_optimization(
        interventions=viable_dicts if len(viable_dicts) >= 3 else INTERVENTIONS_DATASET,
        budget=payload.budget_limit_inr,
        pop_size=40,
        n_gen=50
    )
    
    return OptimizeRunResponse(
        status="success",
        budget_inr=budget,
        pareto_solutions_count=len(portfolios_raw),
        portfolios=portfolios_raw
    )
