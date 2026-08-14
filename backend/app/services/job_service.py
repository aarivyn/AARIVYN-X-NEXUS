import uuid
import datetime
import threading
import logging
from typing import Dict, Any, Optional
from schemas import (
    NexusAnalyzeRequest, NexusJobStatusResponse,
    WaterAnalyzeRequest, FeasibilityFilterRequest, OptimizeRunRequest,
    PortfolioSchema
)
from services.water_service import run_water_analysis
from services.graph_service import traverse_graph_recursive_cte
from services.feasibility_service import run_feasibility_filters
from services.optimizer_service import run_nsga2_optimization
from services.portfolio_service import generate_implementation_plan
from cache import set_cache, get_cache
from mapdata import context_store

logger = logging.getLogger("nexus.jobs")

# In-memory store for active job status tracking
JOBS_DB: Dict[str, Dict[str, Any]] = {}

def execute_nexus_pipeline(job_id: str, request: NexusAnalyzeRequest):
    try:
        # Stage 1: EO Acquisition & Processing
        JOBS_DB[job_id]["stage"] = "Stage 1/7: Earth Observation Acquisition & Processing"
        JOBS_DB[job_id]["progress_percent"] = 15
        water_req = WaterAnalyzeRequest(
            geography_id=request.geography_id,
            bbox=request.bbox,
            date_range_start=request.date_range_start,
            date_range_end=request.date_range_end,
            data_sources=request.data_sources,
            budget_inr=request.budget_limit_inr,
            time_horizon_months=request.time_horizon_months,
            risk_tolerance=request.max_risk_level
        )
        water_res = run_water_analysis(water_req)

        # Stage 2: Problem Detection & Signals
        JOBS_DB[job_id]["stage"] = "Stage 2/7: Problem Signals & Context Processing"
        JOBS_DB[job_id]["progress_percent"] = 30

        # Stage 3: Intervention Knowledge Graph Discovery
        JOBS_DB[job_id]["stage"] = "Stage 3/7: Intervention Knowledge Graph Multi-Hop Discovery"
        JOBS_DB[job_id]["progress_percent"] = 45
        graph_chain = traverse_graph_recursive_cte(root_node_id="PROB-WASTEWATER", max_depth=5)

        # Stage 4: Feasibility Filter Engine
        JOBS_DB[job_id]["stage"] = "Stage 4/7: 6-Stage Feasibility Constraint Filtering"
        JOBS_DB[job_id]["progress_percent"] = 60
        feas_req = FeasibilityFilterRequest(
            candidate_intervention_ids=[],
            geography_id=request.geography_id,
            budget_limit_inr=request.budget_limit_inr,
            time_horizon_months=request.time_horizon_months,
            max_risk_level=request.max_risk_level
        )
        feas_res = run_feasibility_filters(feas_req)

        # Stage 5: NSGA-II Multi-Objective Optimization
        JOBS_DB[job_id]["stage"] = "Stage 5/7: pymoo NSGA-II Multi-Objective Portfolio Optimization"
        JOBS_DB[job_id]["progress_percent"] = 80
        viable_dicts = [i.dict() for i in feas_res.viable_interventions]
        
        # Optimize pop_size=20, n_gen=20 for fast background execution
        portfolios = run_nsga2_optimization(
            interventions=viable_dicts,
            budget=request.budget_limit_inr,
            pop_size=20,
            n_gen=20
        )

        # Stage 6 & 7: Portfolio Selection & Implementation Plan Generator
        JOBS_DB[job_id]["stage"] = "Stage 6/7: Implementation Plan Generation & Telemetry Assembly"
        JOBS_DB[job_id]["progress_percent"] = 95

        # No Pareto-optimal portfolio exists under the given constraints (e.g.
        # every viable intervention exceeds the budget cap). Fail soft with an
        # explanatory result instead of crashing on an empty portfolios list.
        if not portfolios:
            impl_plan = None
            no_solution_reason = (
                f"No feasible intervention portfolio could be assembled within the given "
                f"constraints (budget ₹{(request.budget_limit_inr/1e7):.2f}Cr, "
                f"{request.time_horizon_months}-month horizon, max risk "
                f"'{request.max_risk_level}'). {feas_res.viable_candidates_count} of "
                f"{feas_res.total_candidates} candidate interventions passed feasibility "
                f"filtering. Consider raising the budget, extending the timeline, or "
                f"relaxing the risk tolerance."
            )
        else:
            top_portfolio = PortfolioSchema(**portfolios[0])
            impl_plan = generate_implementation_plan(top_portfolio)
            no_solution_reason = None

        full_result = {
            "orchestration_id": job_id,
            "geography_id": request.geography_id,
            "site_data": {
                "budget": context_store.budget_snapshot(),
                "timeline": context_store.timeline_snapshot(),
                "social_groups": context_store.get_social_summary(),
                "locations": context_store.locations_snapshot(),
            },
            "earth_observation": {
                "observations_count": len(water_res.relevant_observations),
                "indicators": [i.dict() for i in water_res.water_indicators],
                "confidence": water_res.confidence_metadata
            },
            "water_intelligence": {
                "detected_signals": [s.dict() for s in water_res.detected_signals],
                "problem_categories": water_res.problem_categories,
                "evidence": water_res.evidence_used
            },
            "intervention_graph": {
                "discovered_nodes_count": len(graph_chain.path_nodes),
                "discovered_edges_count": len(graph_chain.edges)
            },
            "feasibility": {
                "total_candidates": feas_res.total_candidates,
                "viable_candidates_count": feas_res.viable_candidates_count,
                "filter_matrix": [m.dict() for m in feas_res.filter_matrix]
            },
            "optimization": {
                "pareto_solutions_count": len(portfolios),
                "top_portfolios": portfolios[:3],
                "no_solution_reason": no_solution_reason
            },
            "implementation_plan": impl_plan.dict() if impl_plan else None,
            "provenance": {
                "orchestration_engine": "NEXUS Master Pipeline Orchestrator v2.0",
                "stac_provider": "Microsoft Planetary Computer STAC (sentinel-2-l2a, landsat-c2-l2)",
                "optimizer": "pymoo NSGA-II Genetic Solver",
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
        }

        JOBS_DB[job_id]["status"] = "COMPLETED"
        JOBS_DB[job_id]["stage"] = "Stage 7/7: Master Pipeline Complete"
        JOBS_DB[job_id]["progress_percent"] = 100
        JOBS_DB[job_id]["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        JOBS_DB[job_id]["result"] = full_result
        set_cache(f"job_{job_id}", JOBS_DB[job_id])

    except Exception as e:
        logger.error(f"Nexus Pipeline execution failed for {job_id}: {e}")
        JOBS_DB[job_id]["status"] = "FAILED"
        JOBS_DB[job_id]["error_message"] = str(e)
        JOBS_DB[job_id]["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"

def submit_nexus_job(request: NexusAnalyzeRequest) -> NexusJobStatusResponse:
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    now = datetime.datetime.utcnow().isoformat() + "Z"
    
    job_record = {
        "job_id": job_id,
        "status": "PROCESSING",
        "progress_percent": 5,
        "stage": "Stage 0/7: Initializing Pipeline & Background Worker",
        "created_at": now,
        "updated_at": now,
        "error_message": None,
        "result": None
    }
    JOBS_DB[job_id] = job_record
    
    # Spawn thread worker for non-blocking execution
    thread = threading.Thread(target=execute_nexus_pipeline, args=(job_id, request))
    thread.daemon = True
    thread.start()
    
    return NexusJobStatusResponse(**job_record)

def get_job_status(job_id: str) -> Optional[NexusJobStatusResponse]:
    rec = JOBS_DB.get(job_id)
    if rec:
        return NexusJobStatusResponse(**rec)
    cached = get_cache(f"job_{job_id}")
    if cached:
        return NexusJobStatusResponse(**cached)
    return None
