# NEXUS — Technical Explanation & Architecture Defense

## 1. Real-World Applicability
* **Active Decision System over Passive Dashboards:** Replaces passive satellite maps and hallucinating LLMs with a constraint-driven decision engine backed by real Earth Observation data (Sentinel, Landsat, GRACE).
* **Auditable Governance ("Why Not?" Ledger):** Converts hidden algorithmic filtering into transparent, numerically justified records (e.g., *Cost ₹25 Cr exceeds ₹20 Cr limit*), giving public officials complete auditability.
* **Role-Based Single Source of Truth:** Serves Governments, CSR Funders, and NGOs on one shared engine with context and permissions dynamically tailored by role.
* **Systemic Solution Chains:** Maps interconnected environmental and economic value chains (e.g., wastewater → algae biomass → biofertilizers → local livelihoods) aligned with UN SDGs.

## 2. Scalability
* **Domain-Agnostic Core Engine:** Proven on water resilience (groundwater, floods, drinking water), the core pipeline scales seamlessly to Agriculture (SDG 2), Energy, or Health by simply loading new intervention ontologies.
* **O(N) Short-Circuit Filtering:** Evaluates constraints sequentially (`geographic` → `budget` → `time` → `risk_regulatory`) and exits on first failure, reducing compute overhead before passing candidates to multi-objective NSGA-II optimization.
* **Partition Invariants & Crash-Safety:** Guarantees every candidate is cleanly partitioned (`included` + `excluded` = `total`) and safely handles edge cases (like 100% exclusions) without crashing downstream optimizers.

## 3. Technological Sustainability
* **Strict Data Contracts & Azure Stack:** Modular architecture built on FastAPI, Azure Container Apps, PostgreSQL + PostGIS, and Redis with strongly-typed schemas that prevent architectural drift.
* **Evidence Before Assertion:** Enforces strict data provenance (`LIVE`, `MODELLED`, `SYNTHETIC`), ensuring LLMs never generate raw scientific evidence.
* **Zero Breaking Changes:** Extends existing pipelines via an additive API contract (`excluded` array), preserving backward compatibility and baseline test suites.
