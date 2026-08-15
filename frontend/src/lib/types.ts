// NEXUS API type definitions — mirrors backend/API.md (v2.0.0) and live payloads.

// ---------- Module 1: Auth & Workspace ----------

export type Persona =
  | "GOVERNMENT"
  | "CSR_FUNDER"
  | "NGO"
  | "STUDENT"
  | "RESEARCHER"
  | "COMMUNITY";

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}
export interface RegisterResponse {
  status: string;
  user_id: number;
  email: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}
export interface LoginResponse {
  status: string;
  access_token: string;
  user_id: number;
  persona: Persona;
}

export interface UserProfile {
  id: number;
  email: string;
  name: string;
  persona: Persona;
  organization: string;
  jurisdiction: string;
}

export interface OnboardingRequest {
  persona: Persona;
  government?: {
    organization: string;
    department_agency: string;
    admin_level: string;
    role: string;
    target_district?: string;
  };
  csr_funder?: {
    organization: string;
    focus_areas: string[];
    target_geography: string;
    budget?: number;
  };
  ngo?: {
    organization: string;
    operating_regions: string[];
    focus_areas: string[];
    implementation_capacity: string;
  };
  student?: { name: string; institution: string; region_of_interest: string };
  researcher?: { name: string; institution: string; region_of_interest: string };
  community?: { problem_category: string; location?: string };
}

export interface PermissionScope {
  persona: Persona;
  read_map: boolean;
  run_optimization: boolean;
  view_provenance: boolean;
  admin_level?: string;
  role?: string;
}

export interface WorkspaceContext {
  user_id: number;
  persona: Persona;
  geography_name: string;
  bbox: [number, number, number, number];
  center: [number, number];
  zoom: number;
  permission_scope: PermissionScope;
}

// ---------- Module 2: Earth Observation ----------

export type LayerType = "ndvi" | "ndwi" | "groundwater";

export interface EOLayerResponse {
  layer_type: LayerType;
  tile_url: string;
  bounds: [number, number, number, number];
  stac_metadata: {
    scene_id?: string;
    acquisition_date?: string;
    cloud_cover_percent?: number;
    source_api?: string;
    provenance_tag?: string;
    [k: string]: unknown;
  };
  provenance_tag: string;
}

// ---------- Module 3: Water Intelligence ----------

export interface WaterIndicator {
  indicator_name: string;
  value: number;
  unit: string;
  source: string;
  measurement_type: string;
  direct_measurement: boolean;
  confidence: number;
  limitations?: string;
  pedigree: string;
  disclaimer?: string;
}

export interface DetectedSignal {
  id: string;
  domain: string;
  severity: string;
  affected_villages_count: number;
  provenance_tag: string;
  direct_measurement: boolean;
  title?: string;
  description?: string;
  source?: string;
  limitations?: string;
}

export interface Evidence {
  citation: string;
  type: string;
  confidence: number;
  direct_measurement: boolean;
}

export interface WaterAnalyzeRequest {
  geography_id: string;
  bbox?: [number, number, number, number];
  date_range_start?: string;
  date_range_end?: string;
  data_sources?: string[];
  budget_inr?: number;
  time_horizon_months?: number;
  risk_tolerance?: string;
}

export interface WaterAnalyzeResponse {
  geography_id: string;
  water_indicators: WaterIndicator[];
  detected_signals: DetectedSignal[];
  problem_categories: string[];
  evidence_used: Evidence[];
  relevant_observations: unknown[];
  confidence_metadata: Record<string, unknown>;
}

export interface ContextSignals {
  geography_id: string;
  water_stress_index: number;
  vegetation_condition_index: number;
  flood_risk_score: number;
  groundwater_drawdown_rate_m_yr: number;
  signals: DetectedSignal[];
}

// ---------- Module 4: Knowledge Graph ----------

export interface InterventionCard {
  id: string;
  name: string;
  domain: string;
  category: string;
  description?: string;
  cost_inr: number;
  water_security_score: number;
  sdg_alignments: string[];
  jobs_created: number;
  co_benefits?: string[];
  applicable_conditions?: Record<string, unknown>;
  implementation_time_months: number;
  technology_maturity_lvl: number;
  risk_level: string;
  dependencies: string[];
  compatible_with: string[];
  status?: string;
}

// ---------- Module 5: Feasibility ----------

export interface FilterMatrixRow {
  intervention_id: string;
  intervention_name: string;
  passed_all: boolean;
  geographic_filter_pass: boolean;
  budget_filter_pass: boolean;
  time_filter_pass: boolean;
  risk_filter_pass: boolean;
  failure_reasons: string[];
}

export interface FeasibilityFilterRequest {
  candidate_intervention_ids?: string[];
  geography_id: string;
  budget_limit_inr: number;
  time_horizon_months: number;
  max_risk_level: string;
}

export interface FeasibilityFilterResponse {
  total_candidates: number;
  viable_candidates_count: number;
  viable_interventions: InterventionCard[];
  filter_matrix: FilterMatrixRow[];
}

// ---------- Module 6: Optimizer ----------

export interface Portfolio {
  id: string;
  name: string;
  focus: string;
  total_cost_inr: number;
  cost_crores: number;
  water_security_score: number;
  jobs_created: number;
  sdg_alignments: string[];
  sdg_count: number;
  intervention_count: number;
  interventions: InterventionCard[];
  co_benefits: string[];
  applicable_conditions: Record<string, unknown>;
  provenance: Record<string, unknown>;
}

export interface OptimizeRunRequest {
  geography_id: string;
  budget_limit_inr: number;
  time_horizon_months: number;
  objective_weights?: number[] | null;
}

export interface OptimizeRunResponse {
  status: string;
  budget_inr: number;
  pareto_solutions_count: number;
  portfolios: Portfolio[];
}

// ---------- Module 7: Implementation Plan & Provenance ----------

export interface ImplementationPlan {
  portfolio_id: string;
  portfolio_name: string;
  total_cost_inr: number;
  total_duration_months: number;
  stakeholder_allocation: Record<string, number>;
  intervention_sequence: Array<{
    phase: number;
    phase_name: string;
    intervention_id: string;
    intervention_name: string;
    duration_months: number;
    estimated_cost_inr: number;
    responsible_stakeholder: string;
    dependencies: string[];
    key_milestones: string[];
  }>;
  monitoring_indicators: Array<{ indicator: string; frequency: string; target: string }>;
  created_at: string;
}

export interface ProvenanceAudit {
  portfolio_id: string;
  portfolio_name: string;
  optimizer_engine: string;
  objective_weights_applied: Record<string, number> | null;
  feasibility_filter_audit: Array<{
    stage: string;
    passed_candidates: number;
    rejections: number;
  }>;
  knowledge_graph_chain_sources: unknown[];
  earth_observation_scene_ids: string[];
  satellite_stac_provenance: Record<string, unknown>;
  confidence_score: string;
}

// ---------- Master Pipeline ----------

export interface NexusAnalyzeRequest {
  geography_id: string;
  bbox: [number, number, number, number];
  date_range_start: string;
  date_range_end: string;
  data_sources: string[];
  budget_limit_inr: number;
  time_horizon_months: number;
  max_risk_level: string;
}

export interface NexusJobStatus {
  job_id: string;
  status: "PROCESSING" | "COMPLETED" | "FAILED";
  progress_percent: number;
  stage: string | null;
  created_at: string;
  updated_at: string;
  error_message: string | null;
  result: NexusResult | null;
}

export interface NexusResult {
  orchestration_id: string;
  geography_id: string;
  site_data: Record<string, unknown>;
  earth_observation: {
    observations_count: number;
    indicators: Array<Record<string, unknown>>;
    confidence: Record<string, unknown>;
  };
  water_intelligence: {
    detected_signals: Array<Record<string, unknown>>;
    problem_categories: string[];
    evidence: Evidence[];
  };
  intervention_graph: {
    discovered_nodes_count: number;
    discovered_edges_count: number;
  };
  feasibility: {
    total_candidates: number;
    viable_candidates_count: number;
    filter_matrix: FilterMatrixRow[];
  };
  optimization: {
    pareto_solutions_count: number;
    top_portfolios: Portfolio[];
    no_solution_reason: string | null;
  };
  implementation_plan: ImplementationPlan;
  provenance: Record<string, unknown>;
}

// ---------- Map Data Ingest / Site Data ----------

export interface BudgetRecord {
  id: string;
  name?: string;
  target_budget: number;
  maximum_budget: number;
  intensity: number;
  details?: string;
  created_at: string;
  updated_at: string;
}

export interface LocationRecord {
  id: string;
  name?: string;
  state: string;
  district: string;
  city: string;
  intensity: number;
  details?: string;
  created_at: string;
  updated_at: string;
}

export interface ListResponse<T> {
  count: number;
  items: T[];
}

export interface SocialGroupProfile {
  gender?: string;
  income_group?: string;
  employment_status?: string;
  age?: number;
  caste?: string;
  area_type?: string;
  religion?: string;
}

export interface SocialGroup {
  id: string;
  name: string;
  intensity: number;
  details?: string;
  profiles: SocialGroupProfile[];
  created_at: string;
  updated_at: string;
}

export interface TaxonomyEntry {
  key: string;
  label: string;
}

export interface SocialTaxonomy {
  income_groups: TaxonomyEntry[];
  employment_statuses: TaxonomyEntry[];
  genders: TaxonomyEntry[];
  caste_categories: TaxonomyEntry[];
  area_types: TaxonomyEntry[];
  religions: TaxonomyEntry[];
}

export interface TimelineRecord {
  id: string;
  name?: string;
  urgency: number;
  expected_duration: string;
  deadline: string;
  details?: string;
  created_at: string;
  updated_at: string;
}

export interface IngestRecordMeta {
  id: string;
  name: string;
  category: string;
  source_type: string;
  source_filename: string;
  representation: string;
  target_crs: string;
  feature_count: number | null;
  size_bytes: number;
  confidence: string;
}

export interface UploadResponse {
  records: IngestRecordMeta[];
  summary: {
    uploaded: number;
    records: number;
    representations: string[];
    errors: string[];
  };
}

export interface MapsHealth {
  status: string;
  service: string;
  version: string;
  supported_types: string[];
}

export const MAP_CATEGORIES = [
  "base_maps",
  "utilities",
  "imagery",
  "geological",
  "water_demand",
  "field_observations",
  "engineering",
  "weather",
  "general",
] as const;

export const PERSONAS: { value: Persona; label: string; blurb: string }[] = [
  { value: "GOVERNMENT", label: "Government", blurb: "District / state water authority" },
  { value: "CSR_FUNDER", label: "CSR Funder", blurb: "Corporate social responsibility" },
  { value: "NGO", label: "NGO", blurb: "Non-profit implementer" },
  { value: "STUDENT", label: "Student", blurb: "Academic / coursework" },
  { value: "RESEARCHER", label: "Researcher", blurb: "Academic research" },
  { value: "COMMUNITY", label: "Community", blurb: "Local community member" },
];

export const PIPELINE_STAGES = [
  "Initializing Pipeline & Background Worker",
  "Earth Observation Acquisition & Processing",
  "Water Intelligence & Signal Detection",
  "Problem Detection & Context Assembly",
  "Intervention Knowledge Graph Discovery",
  "Feasibility Filtering",
  "NSGA-II Multi-Objective Optimization",
  "Implementation Plan & Telemetry",
];
