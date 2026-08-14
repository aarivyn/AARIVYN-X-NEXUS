import json
import numpy as np
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.operators.sampling.rnd import BinaryRandomSampling
from pymoo.operators.crossover.pntx import TwoPointCrossover
from pymoo.operators.mutation.bitflip import BitflipMutation
from mapdata import context_store

# 15 Water Sector Interventions for Rewa District (NEXUS Water Flagship)
INTERVENTIONS_DATASET = [
    {
        "id": "INT-001",
        "name": "Rooftop Rainwater Harvesting Units",
        "domain": "Water",
        "category": "Rainwater Harvesting",
        "description": "Rooftop rainwater capture tanks for village households.",
        "cost_inr": 2500000,
        "water_security_score": 78.5,
        "sdg_alignments": ["6.1", "6.2"],
        "jobs_created": 14,
        "co_benefits": ["Local groundwater replenishment", "Low operational complexity"],
        "applicable_conditions": {"min_rainfall_mm": 600, "urban_rural": "Both"},
        "implementation_time_months": 6,
        "technology_maturity_lvl": 9,
        "risk_level": "LOW",
        "dependencies": [],
        "compatible_with": ["INT-002", "INT-003"]
    },
    {
        "id": "INT-002",
        "name": "Community Check Dams & Bunds",
        "domain": "Water",
        "category": "Watershed Restoration",
        "description": "Check dams on local streams to retain monsoon runoff.",
        "cost_inr": 18000000,
        "water_security_score": 92.0,
        "sdg_alignments": ["6.6", "15.1"],
        "jobs_created": 85,
        "co_benefits": ["Soil erosion prevention", "Agricultural runoff retention"],
        "applicable_conditions": {"slope_pct": "<5%", "soil_type": "Clay/Loam"},
        "implementation_time_months": 12,
        "technology_maturity_lvl": 9,
        "risk_level": "LOW",
        "dependencies": [],
        "compatible_with": ["INT-003"]
    },
    {
        "id": "INT-003",
        "name": "Groundwater Recharge Shafts & Pits",
        "domain": "Water",
        "category": "Groundwater Recharge",
        "description": "Deep recharge shafts injecting surface water into depleted aquifers.",
        "cost_inr": 8500000,
        "water_security_score": 84.2,
        "sdg_alignments": ["6.6", "6.b"],
        "jobs_created": 32,
        "co_benefits": ["Aquifer pressure restoration", "Community water access"],
        "applicable_conditions": {"aquifer_depth_m": ">15m"},
        "implementation_time_months": 8,
        "technology_maturity_lvl": 9,
        "risk_level": "LOW",
        "dependencies": [],
        "compatible_with": ["INT-002"]
    },
    {
        "id": "INT-004",
        "name": "Drip & Micro-Irrigation Infrastructure",
        "domain": "Water",
        "category": "Agricultural Efficiency",
        "description": "High-efficiency drip irrigation networks for smallholder farms.",
        "cost_inr": 35000000,
        "water_security_score": 89.5,
        "sdg_alignments": ["6.4", "2.3"],
        "jobs_created": 60,
        "co_benefits": ["30-50% crop yield improvement", "Reduced energy consumption"],
        "applicable_conditions": {"crop_type": "Horticulture/Cash crops"},
        "implementation_time_months": 14,
        "technology_maturity_lvl": 9,
        "risk_level": "LOW",
        "dependencies": [],
        "compatible_with": ["INT-008"]
    },
    {
        "id": "INT-WETLAND-01",
        "name": "Constructed Wetland Wastewater Treatment",
        "domain": "Water",
        "category": "Wastewater Treatment",
        "description": "Passive wetland bio-filtration system treating municipal sewage.",
        "cost_inr": 42000000,
        "water_security_score": 94.1,
        "sdg_alignments": ["6.3", "15.1", "13.2"],
        "jobs_created": 110,
        "co_benefits": ["Natural biodiversity habitat", "Zero electricity requirement"],
        "applicable_conditions": {"min_land_ha": 2.5},
        "implementation_time_months": 18,
        "technology_maturity_lvl": 9,
        "risk_level": "LOW",
        "dependencies": [],
        "compatible_with": ["INT-006"]
    },
    {
        "id": "INT-ALGAE-01",
        "name": "Algae-Based Wastewater Treatment & Biomass Recovery",
        "domain": "Water",
        "category": "Wastewater Treatment",
        "description": "High-rate algal pond system treating sewage while harvesting biomass.",
        "cost_inr": 38000000,
        "water_security_score": 96.5,
        "sdg_alignments": ["6.3", "7.2", "12.5"],
        "jobs_created": 145,
        "co_benefits": ["Algal biomass co-product", "High nutrient recovery"],
        "applicable_conditions": {"solar_irradiance": ">4.5 kWh/m2/day"},
        "implementation_time_months": 12,
        "technology_maturity_lvl": 8,
        "risk_level": "MEDIUM",
        "dependencies": [],
        "compatible_with": ["INT-BIOFERTILIZER-01"]
    },
    {
        "id": "INT-BIOFERTILIZER-01",
        "name": "Algal Bio-Fertilizer & Soil Conditioner Processing",
        "domain": "Agriculture",
        "category": "Circular Agriculture",
        "description": "Converts algal biomass into organic bio-fertilizer pellets for local farming.",
        "cost_inr": 12000000,
        "water_security_score": 75.0,
        "sdg_alignments": ["2.4", "12.5"],
        "jobs_created": 50,
        "co_benefits": ["Restores soil micro-fauna", "Replaces chemical NPK fertilizers"],
        "applicable_conditions": {"crop_type": "All"},
        "implementation_time_months": 6,
        "technology_maturity_lvl": 9,
        "risk_level": "LOW",
        "dependencies": ["INT-ALGAE-01"],
        "compatible_with": ["INT-ALGAE-01"]
    },
    {
        "id": "INT-006",
        "name": "Greywater Recycling & Bio-Filtration",
        "domain": "Water",
        "category": "Greywater Reuse",
        "description": "Decentralized greywater filtration systems for residential clusters.",
        "cost_inr": 15000000,
        "water_security_score": 76.8,
        "sdg_alignments": ["6.3", "12.5"],
        "jobs_created": 28,
        "co_benefits": ["Non-potable water supply", "Reduced municipal discharge"],
        "applicable_conditions": {"density": "Peri-urban"},
        "implementation_time_months": 6,
        "technology_maturity_lvl": 9,
        "risk_level": "LOW",
        "dependencies": [],
        "compatible_with": ["INT-WETLAND-01"]
    },
    {
        "id": "INT-007",
        "name": "Smart Distribution Leakage Detection",
        "domain": "Water",
        "category": "Leakage Control",
        "description": "IoT pressure monitoring and acoustic sensors on main supply lines.",
        "cost_inr": 12000000,
        "water_security_score": 81.0,
        "sdg_alignments": ["6.4", "9.c"],
        "jobs_created": 18,
        "co_benefits": ["IoT sensor integration", "NRW (Non-Revenue Water) reduction"],
        "applicable_conditions": {"piped_network": True},
        "implementation_time_months": 9,
        "technology_maturity_lvl": 9,
        "risk_level": "LOW",
        "dependencies": [],
        "compatible_with": ["INT-008"]
    },
    {
        "id": "INT-008",
        "name": "Solar Water Pumping & Overhead Tanks",
        "domain": "Water",
        "category": "Water Access",
        "description": "Solar-powered drinking water pumping and elevated storage tanks.",
        "cost_inr": 22000000,
        "water_security_score": 87.4,
        "sdg_alignments": ["6.1", "7.2"],
        "jobs_created": 45,
        "co_benefits": ["24/7 clean drinking access", "Off-grid solar operation"],
        "applicable_conditions": {"solar_irradiance": ">5 kWh/m2/day"},
        "implementation_time_months": 10,
        "technology_maturity_lvl": 9,
        "risk_level": "LOW",
        "dependencies": [],
        "compatible_with": ["INT-004"]
    },
    {
        "id": "INT-009",
        "name": "Solar Desalination & Brackish Water Treatment",
        "domain": "Water",
        "category": "Water Purification",
        "description": "Solar membrane distillation units for saline groundwater zones.",
        "cost_inr": 28000000,
        "water_security_score": 83.1,
        "sdg_alignments": ["6.1", "7.2"],
        "jobs_created": 22,
        "co_benefits": ["High-purity potable drinking water", "Zero carbon footprint"],
        "applicable_conditions": {"tds_ppm": ">1500"},
        "implementation_time_months": 12,
        "technology_maturity_lvl": 8,
        "risk_level": "MEDIUM",
        "dependencies": [],
        "compatible_with": ["INT-008"]
    },
    {
        "id": "INT-010",
        "name": "Aquifer Automated Telemetry Monitoring",
        "domain": "Water",
        "category": "Resource Monitoring",
        "description": "Automated piezometers tracking groundwater level fluctuations.",
        "cost_inr": 6000000,
        "water_security_score": 72.0,
        "sdg_alignments": ["6.a", "9.c"],
        "jobs_created": 12,
        "co_benefits": ["Real-time data feeds", "Early drought warning system"],
        "applicable_conditions": {"telecom_coverage": "2G/4G"},
        "implementation_time_months": 4,
        "technology_maturity_lvl": 9,
        "risk_level": "LOW",
        "dependencies": [],
        "compatible_with": ["INT-003"]
    },
    {
        "id": "INT-011",
        "name": "Reservoir De-Silting & Capacity Expansion",
        "domain": "Water",
        "category": "Surface Water Storage",
        "description": "Dredging silt from existing water reservoirs to restore storage capacity.",
        "cost_inr": 28000000,
        "water_security_score": 88.3,
        "sdg_alignments": ["6.6", "11.5"],
        "jobs_created": 95,
        "co_benefits": ["Nutrient-rich silt for farm soil", "Increased flood buffer"],
        "applicable_conditions": {"reservoir_age_years": ">20"},
        "implementation_time_months": 15,
        "technology_maturity_lvl": 9,
        "risk_level": "LOW",
        "dependencies": [],
        "compatible_with": ["INT-002"]
    },
    {
        "id": "INT-012",
        "name": "Community RO & UV Drinking Water Kiosks",
        "domain": "Water",
        "category": "Drinking Water Purification",
        "description": "Water ATM kiosks providing purified drinking water at ₹0.20/liter.",
        "cost_inr": 9500000,
        "water_security_score": 80.5,
        "sdg_alignments": ["6.1", "3.9"],
        "jobs_created": 30,
        "co_benefits": ["Reduced waterborne disease incidence", "Women time-use savings"],
        "applicable_conditions": {"population_density": "High"},
        "implementation_time_months": 5,
        "technology_maturity_lvl": 9,
        "risk_level": "LOW",
        "dependencies": [],
        "compatible_with": ["INT-008"]
    },
    {
        "id": "INT-013",
        "name": "Farmer Water Users Association Capacity Building",
        "domain": "Water",
        "category": "Governance & Capacity",
        "description": "Training programs for local water stewardship committees.",
        "cost_inr": 4000000,
        "water_security_score": 69.0,
        "sdg_alignments": ["6.b", "5.5"],
        "jobs_created": 20,
        "co_benefits": ["Community ownership", "Conflict reduction over canal sharing"],
        "applicable_conditions": {"existing_wua": False},
        "implementation_time_months": 12,
        "technology_maturity_lvl": 9,
        "risk_level": "LOW",
        "dependencies": [],
        "compatible_with": ["INT-001", "INT-004"]
    }
]

class NexusWaterOptimizationProblem(ElementwiseProblem):
    def __init__(self, interventions, budget_limit):
        self.interventions = interventions
        self.budget_limit = budget_limit
        self.n_interventions = len(interventions)
        
        super().__init__(
            n_var=self.n_interventions,
            n_obj=4,
            n_ieq_constr=1,
            vtype=bool
        )

    def _evaluate(self, x, out, *args, **kwargs):
        total_cost = sum(self.interventions[i]["cost_inr"] for i in range(self.n_interventions) if x[i])
        total_water_score = sum(self.interventions[i]["water_security_score"] for i in range(self.n_interventions) if x[i])
        total_jobs = sum(self.interventions[i]["jobs_created"] for i in range(self.n_interventions) if x[i])
        
        sdg_set = set()
        for i in range(self.n_interventions):
            if x[i]:
                sdg_set.update(self.interventions[i].get("sdg_alignments", []))
        total_sdgs = len(sdg_set)
        
        f1 = total_cost
        f2 = -total_water_score
        f3 = -total_jobs
        f4 = -total_sdgs
        
        g1 = total_cost - self.budget_limit
        
        out["F"] = [f1, f2, f3, f4]
        out["G"] = [g1]

def run_nsga2_optimization(interventions=None, budget=200000000, pop_size=40, n_gen=50):
    if interventions is None:
        interventions = INTERVENTIONS_DATASET

    # Module 6 consumes ingested site-data when present: the stored budget
    # singleton wins over the caller-supplied value, and the ingested timeline
    # is surfaced alongside the budget in every portfolio's provenance.
    budget = context_store.resolve_budget_limit(budget)
    budget_commitment = {
        "target_budget_inr": budget,
        "maximum_budget_inr": context_store.get_budget_hard_ceiling(),
        "timeline": context_store.get_timeline(),
        "social_group_count": len(context_store.get_social_groups()),
        "location_count": len(context_store.get_locations()),
    }

    # Guard: pymoo cannot build a problem with zero decision variables. This
    # happens when the feasibility filter stage passes through no viable
    # interventions (e.g. budget too low for every candidate). Fail soft with
    # an empty portfolio list instead of letting pymoo raise a reshape error.
    if not interventions:
        return []

    problem = NexusWaterOptimizationProblem(interventions, budget_limit=budget)
    
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
        solutions = np.atleast_2d(res.X)
        objectives = np.atleast_2d(res.F)
        seq = 0  # sequential portfolio counter (skips empty/dominated-trivial entries)
        
        for x_bool, f_val in zip(solutions, objectives):
            selected_items = [interventions[i] for i in range(len(interventions)) if x_bool[i]]

            # The all-zero solution (no intervention selected, cost == 0) is
            # trivially non-dominated on the cost objective and would otherwise
            # appear as a useless "empty portfolio" at the top of the Pareto
            # front. Skip it so consumers always get actionable portfolios.
            if not selected_items:
                continue

            seq += 1

            cost = float(f_val[0])
            water_score = float(-f_val[1])
            jobs = int(-f_val[2])
            
            sdg_set = sorted(list(set(sdg for item in selected_items for sdg in item.get("sdg_alignments", []))))
            co_benefits_set = sorted(list(set(cb for item in selected_items for cb in item.get("co_benefits", []))))
            
            name = f"Pareto Portfolio #{seq}"
            focus = "Balanced Community Water Security"
            
            if seq == 1:
                name = "Portfolio A — Maximum Water Impact"
                focus = "Prioritizes high-scoring water retention infrastructure"
            elif seq == 2:
                name = "Portfolio B — Balanced & High Employment"
                focus = "Optimizes for rural job creation alongside water security"
            elif seq == 3:
                name = "Portfolio C — Cost-Efficient Essential"
                focus = "Maximizes water impact per Rupee spent under conservative cap"
                
            p_data = {
                "id": f"PORTFOLIO_{seq}",
                "name": name,
                "focus": focus,
                "total_cost_inr": cost,
                "cost_crores": round(cost / 1e7, 2),
                "water_security_score": round(water_score, 1),
                "jobs_created": jobs,
                "sdg_alignments": sdg_set,
                "sdg_count": len(sdg_set),
                "intervention_count": len(selected_items),
                "interventions": selected_items,
                "co_benefits": co_benefits_set,
                "applicable_conditions": {
                    "target_district": "Rewa",
                    "budget_cap_crores": round(budget / 1e7, 2),
                    "budget_commitment": budget_commitment,
                },
                "provenance": {
                    "method": "pymoo NSGA-II Multi-Objective Genetic Algorithm",
                    "provenance_tag": "SYNTHETIC-MODELED",
                    "confidence": "Pareto Non-Dominated Frontier Solved"
                }
            }
            portfolios.append(p_data)
            
    return portfolios
