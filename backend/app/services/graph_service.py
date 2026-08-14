from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from schemas import GraphChainSchema
from services.optimizer_service import INTERVENTIONS_DATASET

# Seed Nodes with Parallel Signature Chain
GRAPH_NODES_SEED = [
    {
        "id": "PROB-WASTEWATER",
        "name": "Untreated Municipal & Peri-Urban Wastewater Discharge",
        "node_type": "PROBLEM",
        "domain": "Water",
        "description": "High BOD, pathogen load, and raw sewage discharge into natural water bodies."
    },
    {
        "id": "INT-WETLAND-01",
        "name": "Constructed Wetland Wastewater Treatment",
        "node_type": "INTERVENTION",
        "domain": "Water",
        "description": "Passive bio-filtration wetland system treating municipal wastewater using gravel beds.",
        "attributes_json": {
            "id": "INT-WETLAND-01",
            "name": "Constructed Wetland Wastewater Treatment",
            "domain": "Water",
            "category": "Wastewater Treatment",
            "description": "Passive bio-filtration wetland system treating municipal wastewater using gravel beds.",
            "cost_inr": 42000000.0,
            "water_security_score": 94.1,
            "sdg_alignments": ["6.3", "15.1", "13.2"],
            "jobs_created": 110,
            "co_benefits": ["Natural biodiversity habitat", "Zero electricity requirement"],
            "applicable_conditions": {"min_land_ha": 2.5},
            "implementation_time_months": 18,
            "technology_maturity_lvl": 9,
            "risk_level": "LOW",
            "dependencies": [],
            "compatible_with": ["INT-006"],
            "status": "CANDIDATE"
        }
    },
    {
        "id": "INT-ALGAE-01",
        "name": "Algae-Based Wastewater Treatment & Biomass Recovery",
        "node_type": "INTERVENTION",
        "domain": "Water",
        "description": "High-rate algal pond system treating sewage while harvesting algal biomass.",
        "attributes_json": {
            "id": "INT-ALGAE-01",
            "name": "Algae-Based Wastewater Treatment & Biomass Recovery",
            "domain": "Water",
            "category": "Wastewater Treatment",
            "description": "High-rate algal pond system treating sewage while harvesting algal biomass.",
            "cost_inr": 38000000.0,
            "water_security_score": 96.5,
            "sdg_alignments": ["6.3", "7.2", "12.5"],
            "jobs_created": 145,
            "co_benefits": ["Algal biomass co-product", "High nutrient recovery"],
            "applicable_conditions": {"solar_irradiance": ">4.5 kWh/m2/day"},
            "implementation_time_months": 12,
            "technology_maturity_lvl": 8,
            "risk_level": "MEDIUM",
            "dependencies": [],
            "compatible_with": ["INT-BIOFERTILIZER-01"],
            "status": "CANDIDATE"
        }
    },
    {
        "id": "OUT-CLEAN-WATER",
        "name": "Reclaimed Water for Agriculture",
        "node_type": "OUTPUT",
        "domain": "Water",
        "description": "Treated secondary effluent suitable for non-potable irrigation."
    },
    {
        "id": "OUT-ALGAL-BIOMASS",
        "name": "Harvested Algal Biomass",
        "node_type": "OUTPUT",
        "domain": "Waste/Energy",
        "description": "Raw organic algal slurry rich in nitrogen, phosphorus, and lipids."
    },
    {
        "id": "INT-BIOFERTILIZER-01",
        "name": "Algal Bio-Fertilizer & Soil Conditioner Processing",
        "node_type": "INTERVENTION",
        "domain": "Agriculture",
        "description": "Converts algal biomass into organic bio-fertilizer pellets for local farming.",
        "attributes_json": {
            "id": "INT-BIOFERTILIZER-01",
            "name": "Algal Bio-Fertilizer & Soil Conditioner Processing",
            "domain": "Agriculture",
            "category": "Circular Agriculture",
            "description": "Converts algal biomass into organic bio-fertilizer pellets for local farming.",
            "cost_inr": 12000000.0,
            "water_security_score": 75.0,
            "sdg_alignments": ["2.4", "12.5"],
            "jobs_created": 50,
            "co_benefits": ["Restores soil micro-fauna", "Replaces chemical NPK fertilizers"],
            "applicable_conditions": {"crop_type": "All"},
            "implementation_time_months": 6,
            "technology_maturity_lvl": 9,
            "risk_level": "LOW",
            "dependencies": ["INT-ALGAE-01"],
            "compatible_with": ["INT-ALGAE-01"],
            "status": "CANDIDATE"
        }
    },
    {
        "id": "BENEFIT-LIVELIHOODS",
        "name": "Local Circular Economy & Green Job Creation",
        "node_type": "CO_BENEFIT",
        "domain": "Livelihoods",
        "description": "Sustained rural employment and localized fertilizer & energy revenue."
    }
]

# Seed Edges with Parallel Signature Topology
GRAPH_EDGES_SEED = [
    # Parallel Path A: Wastewater -> Wetland Treatment
    {"source_id": "PROB-WASTEWATER", "target_id": "INT-WETLAND-01", "edge_type": "ADDRESSES"},
    {"source_id": "INT-WETLAND-01", "target_id": "OUT-CLEAN-WATER", "edge_type": "PRODUCES"},

    # Parallel Path B: Wastewater -> Algae Treatment
    {"source_id": "PROB-WASTEWATER", "target_id": "INT-ALGAE-01", "edge_type": "ADDRESSES"},
    {"source_id": "INT-ALGAE-01", "target_id": "OUT-CLEAN-WATER", "edge_type": "PRODUCES"},
    {"source_id": "INT-ALGAE-01", "target_id": "OUT-ALGAL-BIOMASS", "edge_type": "PRODUCES"},

    # Algae Biomass -> Biofertilizer
    {"source_id": "OUT-ALGAL-BIOMASS", "target_id": "INT-BIOFERTILIZER-01", "edge_type": "ENABLES"},
    {"source_id": "INT-BIOFERTILIZER-01", "target_id": "BENEFIT-LIVELIHOODS", "edge_type": "ENABLES"}
]

def traverse_graph_recursive_cte(root_node_id: str, max_depth: int = 5) -> GraphChainSchema:
    nodes_map = {n["id"]: n for n in GRAPH_NODES_SEED}
    
    # Also populate nodes_map with items from INTERVENTIONS_DATASET
    for item in INTERVENTIONS_DATASET:
        if item["id"] not in nodes_map:
            nodes_map[item["id"]] = {
                "id": item["id"],
                "name": item["name"],
                "node_type": "INTERVENTION",
                "domain": item.get("domain", "Water"),
                "description": item.get("description", item["name"]),
                "attributes_json": item
            }

    visited_nodes = set()
    collected_edges = []
    
    queue = [(root_node_id, 1)]
    visited_nodes.add(root_node_id)

    while queue:
        curr_id, depth = queue.pop(0)
        if depth >= max_depth:
            continue

        for e in GRAPH_EDGES_SEED:
            if e["source_id"] == curr_id:
                collected_edges.append(e)
                target_id = e["target_id"]
                if target_id not in visited_nodes:
                    visited_nodes.add(target_id)
                    queue.append((target_id, depth + 1))

    path_nodes = [nodes_map[nid] for nid in visited_nodes if nid in nodes_map]

    return GraphChainSchema(
        root_intervention_id=root_node_id,
        max_depth=max_depth,
        path_nodes=path_nodes,
        edges=collected_edges
    )
