from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from schemas import InterventionCardSchema, GraphChainSchema, GraphDiscoverRequest
from services.graph_service import traverse_graph_recursive_cte, GRAPH_NODES_SEED
from services.optimizer_service import INTERVENTIONS_DATASET
from mapdata import context_store

router = APIRouter(prefix="/graph", tags=["Module 4: Intervention Knowledge Graph"])

@router.get("/interventions", response_model=List[InterventionCardSchema])
def get_graph_interventions(
    problem: Optional[str] = Query(None),
    domain: Optional[str] = Query("Water")
):
    results = []
    for item in INTERVENTIONS_DATASET:
        if domain and item.get("domain", "").lower() != domain.lower():
            continue
        results.append(InterventionCardSchema(**item))
    return results

@router.get("/chains/{intervention_id}", response_model=GraphChainSchema)
def get_intervention_chain(
    intervention_id: str,
    max_depth: int = Query(5, ge=1, le=10, description="Max depth for recursive CTE traversal")
):
    chain = traverse_graph_recursive_cte(root_node_id=intervention_id, max_depth=max_depth)
    return chain

@router.post("/discover")
def discover_reachable_interventions(payload: GraphDiscoverRequest):
    root_id = "PROB-WASTEWATER" if "water" in payload.detected_problem.lower() else "PROB-WASTEWATER"
    chain = traverse_graph_recursive_cte(root_node_id=root_id, max_depth=payload.max_depth or 5)
    
    reachable_interventions = [
        node for node in chain.path_nodes 
        if node.get("node_type") == "INTERVENTION" or "attributes_json" in node
    ]
    
    # Module 4 consumes ingested social-group data: when a rural/semi-urban
    # service area is recorded, surface it so the discovered interventions
    # can be judged for applicability to the community profile.
    social_summary = context_store.get_social_summary()
    
    return {
        "status": "discovered",
        "detected_problem": payload.detected_problem,
        "geography_id": payload.geography_id,
        "reachable_interventions_count": len(reachable_interventions),
        "social_context": social_summary,
        "rural_service_area": context_store.has_rural_service_area(),
        "chain_graph": chain
    }
