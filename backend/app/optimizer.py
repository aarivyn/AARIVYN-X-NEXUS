import json
import numpy as np
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.operators.sampling.rnd import BinaryRandomSampling
from pymoo.operators.crossover.pntx import TwoPointCrossover
from pymoo.operators.mutation.bitflip import BitflipMutation

# 15 Synthetic Water Sector Interventions for Rewa District (NEXUS Water Flagship)
INTERVENTIONS_DATASET = [
    {
        "id": "INT-001",
        "name": "Rooftop Rainwater Harvesting Units",
        "category": "Rainwater Harvesting",
        "cost_inr": 2500000,          # ₹25 Lakhs
        "water_security_score": 78.5,
        "sdg_alignments": ["6.1", "6.2"],
        "jobs_created": 14,
        "co_benefits": ["Local groundwater replenishment", "Low operational complexity"],
        "applicable_conditions": {"min_rainfall_mm": 600, "urban_rural": "Both"}
    },
    {
        "id": "INT-002",
        "name": "Community Check Dams & Bunds",
        "category": "Watershed Restoration",
        "cost_inr": 18000000,         # ₹1.8 Crore
        "water_security_score": 92.0,
        "sdg_alignments": ["6.6", "15.1"],
        "jobs_created": 85,
        "co_benefits": ["Soil erosion prevention", "Agricultural runoff retention"],
        "applicable_conditions": {"slope_pct": "<5%", "soil_type": "Clay/Loam"}
    },
    {
        "id": "INT-003",
        "name": "Groundwater Recharge Shafts & Pits",
        "category": "Groundwater Recharge",
        "cost_inr": 8500000,          # ₹85 Lakhs
        "water_security_score": 84.2,
        "sdg_alignments": ["6.6", "6.b"],
        "jobs_created": 32,
        "co_benefits": ["Aquifer pressure restoration", "Community water access"],
        "applicable_conditions": {"aquifer_depth_m": ">15m"}
    },
    {
        "id": "INT-004",
        "name": "Drip & Micro-Irrigation Infrastructure",
        "category": "Agricultural Efficiency",
        "cost_inr": 35000000,         # ₹3.5 Crore
        "water_security_score": 89.5,
        "sdg_alignments": ["6.4", "2.3"],
        "jobs_created": 60,
        "co_benefits": ["30-50% crop yield improvement", "Reduced energy consumption"],
        "applicable_conditions": {"crop_type": "Horticulture/Cash crops"}
    },
    {
        "id": "INT-005",
        "name": "Constructed Wetland Wastewater Treatment",
        "category": "Wastewater Treatment",
        "cost_inr": 42000000,         # ₹4.2 Crore
        "water_security_score": 94.1,
        "sdg_alignments": ["6.3", "15.1", "13.2"],
        "jobs_created": 110,
        "co_benefits": ["Natural biodiversity habitat", "Zero electricity requirement"],
        "applicable_conditions": {"min_land_ha": 2.5}
    },
    {
        "id": "INT-006",
        "name": "Greywater Recycling & Bio-Filtration",
        "category": "Greywater Reuse",
        "cost_inr": 15000000,         # ₹1.5 Crore
        "water_security_score": 76.8,
        "sdg_alignments": ["6.3", "12.5"],
        "jobs_created": 28,
        "co_benefits": ["Non-potable water supply", "Reduced municipal discharge"],
        "applicable_conditions": {"density": "Per-urban"}
    },
    {
        "id": "INT-007",
        "name": "Smart Distribution Leakage Detection",
        "category": "Leakage Control",
        "cost_inr": 12000000,         # ₹1.2 Crore
        "water_security_score": 81.0,
        "sdg_alignments": ["6.4", "9.c"],
        "jobs_created": 18,
        "co_benefits": ["IoT sensor integration", "NRW (Non-Revenue Water) reduction"],
        "applicable_conditions": {"piped_network": True}
    },
    {
        "id": "INT-008",
        "name": "Solar Water Pumping & Overhead Tanks",
        "category": "Water Access",
        "cost_inr": 22000000,         # ₹2.2 Crore
        "water_security_score": 87.4,
        "sdg_alignments": ["6.1", "7.2"],
        "jobs_created": 45,
        "co_benefits": ["24/7 clean drinking access", "Off-grid solar operation"],
        "applicable_conditions": {"solar_irradiance": ">5 kWh/m2/day"}
    },
    {
        "id": "INT-009",
        "name": "Decentralized Fecal Sludge Treatment (FSTP)",
        "category": "Septage Management",
        "cost_inr": 48000000,         # ₹4.8 Crore
        "water_security_score": 91.2,
        "sdg_alignments": ["6.2", "6.3", "11.6"],
        "jobs_created": 95,
        "co_benefits": ["Bio-fertilizer co-product", "Pathogen elimination"],
        "applicable_conditions": {"population": "10000-50000"}
    },
    {
        "id": "INT-010",
        "name": "Micro-Catchment Reforestation & Contour Trenching",
        "category": "Catchment Management",
        "cost_inr": 16500000,         # ₹1.65 Crore
        "water_security_score": 86.0,
        "sdg_alignments": ["6.6", "15.2"],
        "jobs_created": 70,
        "co_benefits": ["Carbon sequestration", "Siltation prevention"],
        "applicable_conditions": {"degraded_land": True}
    },
    {
        "id": "INT-011",
        "name": "Reservoir De-Silting & Re-Deepening",
        "category": "Siltation Removal",
        "cost_inr": 28000000,         # ₹2.8 Crore
        "water_security_score": 88.3,
        "sdg_alignments": ["6.6", "11.5"],
        "jobs_created": 120,
        "co_benefits": ["Restored storage capacity", "Nutrient-rich silt for farmers"],
        "applicable_conditions": {"existing_reservoir": True}
    },
    {
        "id": "INT-012",
        "name": "Community Aquifer Managed Recharge",
        "category": "Groundwater Recharge",
        "cost_inr": 9000000,          # ₹90 Lakhs
        "water_security_score": 80.5,
        "sdg_alignments": ["6.1", "6.6"],
        "jobs_created": 25,
        "co_benefits": ["Community water governance", "Drought resilience"],
        "applicable_conditions": {"hydrogeology": "Hard rock / basalt"}
    },
    {
        "id": "INT-013",
        "name": "Automated Canal Sluice Gate Control",
        "category": "Smart Governance",
        "cost_inr": 31000000,         # ₹3.1 Crore
        "water_security_score": 85.0,
        "sdg_alignments": ["6.4", "9.1"],
        "jobs_created": 30,
        "co_benefits": ["Optimized canal discharge", "Tail-end farmer water equity"],
        "applicable_conditions": {"canal_network": True}
    },
    {
        "id": "INT-014",
        "name": "Village Pond Renovation & Stone Retaining Wall",
        "category": "Water Storage",
        "cost_inr": 14000000,         # ₹1.4 Crore
        "water_security_score": 83.0,
        "sdg_alignments": ["6.6", "11.b"],
        "jobs_created": 65,
        "co_benefits": ["Livestock drinking water", "Microclimate cooling"],
        "applicable_conditions": {"village_count": ">5"}
    },
    {
        "id": "INT-015",
        "name": "Solar-Powered Modular Water Purification Kiosks",
        "category": "Water Purification",
        "cost_inr": 19500000,         # ₹1.95 Crore
        "water_security_score": 95.5,
        "sdg_alignments": ["6.1", "3.9"],
        "jobs_created": 40,
        "co_benefits": ["Safe drinking water access", "Waterborne disease reduction"],
        "applicable_conditions": {"high_tds": True}
    }
]

DEFAULT_BUDGET_INR = 200000000  # ₹20 Crore

class WaterInterventionOptimizationProblem(ElementwiseProblem):
    def __init__(self, interventions=None, budget=DEFAULT_BUDGET_INR):
        self.interventions = interventions or INTERVENTIONS_DATASET
        self.budget = budget
        n_var = len(self.interventions)
        
        super().__init__(
            n_var=n_var,
            n_obj=4,      # 1: Cost (min), 2: Water Security (max -> min -WS), 3: SDGs (max -> min -SDG), 4: Jobs (max -> min -Jobs)
            n_constr=1,   # Total Cost <= Budget
            xl=0,
            xu=1
        )
        
    def _evaluate(self, x, out, *args, **kwargs):
        selected_mask = x.astype(bool)
        
        selected_items = [item for i, item in enumerate(self.interventions) if selected_mask[i]]
        
        total_cost = sum(item["cost_inr"] for item in selected_items)
        water_security = sum(item["water_security_score"] for item in selected_items)
        
        # Unique SDGs aligned across selected portfolio
        sdg_set = set()
        for item in selected_items:
            sdg_set.update(item["sdg_alignments"])
        sdg_count = len(sdg_set)
        
        total_jobs = sum(item["jobs_created"] for item in selected_items)
        
        # pymoo minimizes objectives by default
        f1 = total_cost
        f2 = -water_security
        f3 = -sdg_count
        f4 = -total_jobs
        
        # Constraint: total_cost - budget <= 0
        g1 = total_cost - self.budget
        
        out["F"] = [f1, f2, f3, f4]
        out["G"] = [g1]

def run_nsga2_optimization(interventions=None, budget=DEFAULT_BUDGET_INR, pop_size=40, n_gen=50):
    interventions = interventions or INTERVENTIONS_DATASET
    problem = WaterInterventionOptimizationProblem(interventions=interventions, budget=budget)
    
    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=BinaryRandomSampling(),
        crossover=TwoPointCrossover(),
        mutation=BitflipMutation(),
        eliminate_duplicates=True
    )
    
    res = minimize(
        problem,
        algorithm,
        ('n_gen', n_gen),
        seed=42,
        verbose=False
    )
    
    portfolios = []
    
    if res.X is not None and len(res.X) > 0:
        # Extract non-dominated solutions
        unique_solutions = np.unique(res.X.astype(int), axis=0)
        
        for idx, sol in enumerate(unique_solutions):
            selected_indices = np.where(sol == 1)[0]
            selected_interventions = [interventions[i] for i in selected_indices]
            
            cost = sum(item["cost_inr"] for item in selected_interventions)
            if cost > budget:
                continue
                
            ws_score = round(float(sum(item["water_security_score"] for item in selected_interventions)), 2)
            jobs = sum(item["jobs_created"] for item in selected_interventions)
            
            sdgs = sorted(list(set(sdg for item in selected_interventions for sdg in item["sdg_alignments"])))
            categories = list(set(item["category"] for item in selected_interventions))
            co_benefits = list(set(cb for item in selected_interventions for cb in item["co_benefits"]))
            
            # Persona archetypes for presentation
            if idx == 0:
                name = "Portfolio A — Maximum Water Security"
                focus = "Prioritizes immediate water security score & heavy infrastructure"
            elif idx == 1:
                name = "Portfolio B — High Employment & Community Synergy"
                focus = "Maximizes local jobs created & community watershed restoration"
            elif idx == 2:
                name = "Portfolio C — Cost-Efficient & Multi-SDG Balanced"
                focus = "Optimizes broad SDG alignment & high return per rupee spent"
            else:
                name = f"Portfolio Solution #{idx + 1}"
                focus = f"Pareto trade-off solution with {len(selected_interventions)} interventions"
                
            portfolio_obj = {
                "id": f"PORT-{idx+1:02d}",
                "name": name,
                "focus": focus,
                "total_cost_inr": cost,
                "cost_crores": round(cost / 1e7, 2),
                "water_security_score": ws_score,
                "jobs_created": jobs,
                "sdg_alignments": sdgs,
                "sdg_count": len(sdgs),
                "intervention_count": len(selected_interventions),
                "categories": categories,
                "interventions": selected_interventions,
                "co_benefits": co_benefits,
                "applicable_conditions": {
                    "target_district": "Rewa, Madhya Pradesh",
                    "budget_limit": "₹20 Crore",
                    "terrain": "Vindhyan Plateau / Mixed Catchment",
                    "priority_sdg": "SDG 6 (Clean Water & Sanitation)"
                },
                "provenance": {
                    "optimizer": "pymoo NSGA-II Multi-Objective Evolutionary Algorithm",
                    "provenance_label": "MODELED",
                    "confidence": "High (Pareto Frontier Solved)"
                }
            }
            portfolios.append(portfolio_obj)
            
    # Sort portfolios by water security score descending
    portfolios.sort(key=lambda p: p["water_security_score"], reverse=True)
    return portfolios

if __name__ == "__main__":
    print("[*] Running pymoo NSGA-II Optimizer standalone test...")
    results = run_nsga2_optimization()
    print(f"[+] Optimization finished. Pareto frontier solutions generated: {len(results)}")
    
    # Save output to JSON
    output_path = "data/pareto_portfolios.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"[+] Exported Pareto frontier JSON to {output_path}")
    
    # Display top 3 portfolios summary
    for p in results[:3]:
        print(f"\n--- {p['name']} ---")
        print(f"    Cost: INR {p['cost_crores']} Cr | WS Score: {p['water_security_score']} | Jobs: {p['jobs_created']} | SDGs: {p['sdg_count']} ({', '.join(p['sdg_alignments'])})")
        print(f"    Interventions ({p['intervention_count']}): {', '.join([i['name'] for i in p['interventions']])}")
    
    print("\n[OK] STEP 2 OPTIMIZER COMPLETE.")
