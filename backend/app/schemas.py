from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import datetime

class PersonaType(str, Enum):
    GOVERNMENT = "GOVERNMENT"
    CSR_FUNDER = "CSR_FUNDER"
    NGO = "NGO"
    STUDENT = "STUDENT"
    RESEARCHER = "RESEARCHER"
    COMMUNITY = "COMMUNITY"

class ProvenanceTag(str, Enum):
    REAL_DATA = "REAL_DATA"
    REAL_STAC_METADATA = "REAL_STAC_METADATA"
    REAL_RASTER = "REAL_RASTER"
    MODELLED_SATELLITE_PROXY = "MODELLED_SATELLITE_PROXY"
    SYNTHETIC_TEST = "SYNTHETIC_TEST"
    CACHED_DATA = "CACHED_DATA"
    
    # Backwards compatibility tags
    LIVE = "LIVE"
    RECENT = "RECENT"
    HISTORICAL = "HISTORICAL"
    SYNTHETIC_MODELED = "SYNTHETIC_MODELED"

class AdminLevel(str, Enum):
    NATIONAL = "National"
    STATE = "State"
    DISTRICT = "District"
    MUNICIPALITY = "Municipality"
    BLOCK = "Block"
    VILLAGE = "Village"

class GovernmentRole(str, Enum):
    DISTRICT_OFFICER = "District Officer"
    PLANNING_OFFICER = "Planning Officer"
    WATER_RESOURCES_OFFICER = "Water Resources Officer"
    DISASTER_MANAGEMENT = "Disaster Management"
    AGRICULTURE_OFFICER = "Agriculture Officer"
    ENVIRONMENT_OFFICER = "Environment Officer"
    OTHER = "Other"

# --- AUTH SCHEMAS ---

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class OnboardingGovernmentPayload(BaseModel):
    organization: str
    department_agency: str
    admin_level: AdminLevel
    role: GovernmentRole
    target_district: Optional[str] = "Rewa"

class OnboardingCSRFunderPayload(BaseModel):
    organization: str
    funding_program: str
    available_budget: Optional[float] = None
    available_budget_inr: Optional[float] = None
    focus_areas: List[str]
    target_geography: str
    time_horizon: Optional[str] = None
    time_horizon_years: Optional[int] = None

class OnboardingNGOPayload(BaseModel):
    organization: str
    operating_regions: List[str]
    communities_served: str
    focus_areas: List[str]
    implementation_capacity: str

class OnboardingStudentPayload(BaseModel):
    name: str
    institution: str
    region_of_interest: str

class OnboardingResearcherPayload(BaseModel):
    name: str
    institution: str
    region_of_interest: str

class OnboardingCommunityPayload(BaseModel):
    location: Optional[str] = None
    location_name: Optional[str] = None
    problem_category: str

class OnboardingRequest(BaseModel):
    persona: PersonaType
    government: Optional[OnboardingGovernmentPayload] = None
    csr_funder: Optional[OnboardingCSRFunderPayload] = None
    csr: Optional[OnboardingCSRFunderPayload] = None
    ngo: Optional[OnboardingNGOPayload] = None
    student: Optional[OnboardingStudentPayload] = None
    researcher: Optional[OnboardingResearcherPayload] = None
    community: Optional[OnboardingCommunityPayload] = None

class WorkspaceContextResponse(BaseModel):
    user_id: int
    persona: PersonaType
    geography_name: str
    bbox: List[float]
    center: List[float]
    zoom: int
    permission_scope: Dict[str, Any]

# --- GEOSPATIAL & STAC SCHEMAS ---

class LocationSchema(BaseModel):
    id: Optional[int] = None
    name: str
    district: str
    state: str
    bbox: List[float]
    geometry: Optional[Dict[str, Any]] = None
    administrative_level: Optional[str] = "District"

class STACMetadataSchema(BaseModel):
    scene_id: str
    acquisition_date: str
    cloud_cover_percent: float
    source_api: str
    provenance_tag: ProvenanceTag

class ObservationSchema(BaseModel):
    id: Optional[str] = None
    source: str
    satellite: str
    acquisition_time: str
    cloud_quality: Optional[float] = None
    geometry_reference: Optional[List[float]] = None
    processing_status: str = "PROCESSED"

class IndicatorSchema(BaseModel):
    location_id: str
    timestamp: str
    indicator_name: str
    value: float
    unit: str
    source: str
    provider: Optional[str] = "Microsoft Planetary Computer"
    acquisition_time: Optional[str] = None
    processing_method: Optional[str] = "Band Ratio Algebra"
    measurement_type: str = "proxy"
    direct_measurement: bool = False
    confidence: Optional[float] = 0.95
    limitations: Optional[str] = None
    pedigree: ProvenanceTag = ProvenanceTag.MODELLED_SATELLITE_PROXY
    disclaimer: Optional[str] = None

class MapMetadataResponse(BaseModel):
    scene_id: str
    acquisition_date: str
    cloud_cover_percent: float
    bbox: List[float]
    spatial_extent_bounds: List[float]
    crs: str
    provenance: Dict[str, Any]
    statistics: Dict[str, Any]

class EOLayerResponse(BaseModel):
    layer_type: str
    tile_url: str
    bounds: List[float]
    stac_metadata: STACMetadataSchema
    provenance_tag: ProvenanceTag

# --- WATER INTELLIGENCE SCHEMAS ---

class WaterAnalyzeRequest(BaseModel):
    geography_id: str = "rewa"
    bbox: Optional[List[float]] = [81.1, 24.4, 81.5, 24.8]
    date_range_start: Optional[str] = "2026-01-01"
    date_range_end: Optional[str] = "2026-08-01"
    data_sources: Optional[List[str]] = ["Sentinel-2", "Sentinel-1", "Landsat"]
    budget_inr: Optional[float] = 200000000.0
    time_horizon_months: Optional[int] = 36
    risk_tolerance: Optional[str] = "MEDIUM"

class ContextSignalSchema(BaseModel):
    id: str
    title: str
    domain: str
    severity: str
    description: str
    underlying_data_citation: str
    provenance_tag: ProvenanceTag
    affected_villages_count: int
    measurement_type: str = "proxy"
    direct_measurement: bool = False
    source: str = "Sentinel-2 spectral indices"
    limitations: str = "Spectral proxy observation; does not establish chemical contamination or direct aquifer depth."

class WaterAnalyzeResponse(BaseModel):
    geography_id: str
    water_indicators: List[IndicatorSchema]
    detected_signals: List[ContextSignalSchema]
    problem_categories: List[str]
    evidence_used: List[Dict[str, Any]]
    relevant_observations: List[ObservationSchema]
    confidence_metadata: Dict[str, Any]

class DerivedIndicatorsResponse(BaseModel):
    geography_id: str
    water_stress_index: float
    vegetation_condition_index: float
    flood_risk_score: float
    groundwater_drawdown_rate_m_yr: float
    signals: List[ContextSignalSchema]

# --- INTERVENTION GRAPH SCHEMAS ---

class InterventionCardSchema(BaseModel):
    id: str
    name: str
    domain: str = "Water"
    category: str = "Infrastructure"
    description: str = "Geospatial development intervention"
    cost_inr: float
    water_security_score: float
    sdg_alignments: List[str] = []
    jobs_created: int = 50
    co_benefits: List[str] = []
    applicable_conditions: Dict[str, Any] = {}
    implementation_time_months: int = 12
    technology_maturity_lvl: int = 9
    risk_level: str = "LOW"
    dependencies: List[str] = []
    compatible_with: List[str] = []
    status: str = "CANDIDATE"

InterventionSchema = InterventionCardSchema

class GraphChainSchema(BaseModel):
    root_intervention_id: str
    max_depth: int
    path_nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class GraphDiscoverRequest(BaseModel):
    detected_problem: str
    geography_id: str
    max_depth: Optional[int] = 5

# --- FEASIBILITY SCHEMAS ---

class FeasibilityFilterRequest(BaseModel):
    candidate_intervention_ids: List[str] = []
    geography_id: str = "rewa"
    budget_limit_inr: float = 200000000.0
    time_horizon_months: int = 36
    max_risk_level: str = "HIGH"

class InterventionFilterResult(BaseModel):
    intervention_id: str
    intervention_name: str
    passed_all: bool
    geographic_filter_pass: bool
    budget_filter_pass: bool
    time_filter_pass: bool
    risk_filter_pass: bool
    failure_reasons: List[str]

class FeasibilityFilterResponse(BaseModel):
    total_candidates: int
    viable_candidates_count: int
    viable_interventions: List[InterventionCardSchema]
    filter_matrix: List[InterventionFilterResult]

# --- OPTIMIZER SCHEMAS ---

class OptimizeRunRequest(BaseModel):
    geography_id: str = "rewa"
    budget_limit_inr: float = 200000000.0
    time_horizon_months: int = 36
    objective_weights: Optional[Dict[str, float]] = None

OptimizeRequest = OptimizeRunRequest

class PortfolioSchema(BaseModel):
    id: str
    name: str
    focus: str
    total_cost_inr: float
    cost_crores: float
    water_security_score: float
    jobs_created: int
    sdg_alignments: List[str]
    sdg_count: int
    intervention_count: int
    interventions: List[InterventionCardSchema]
    co_benefits: List[str]
    applicable_conditions: Dict[str, Any]
    provenance: Dict[str, Any]

class OptimizeRunResponse(BaseModel):
    status: str
    budget_inr: float
    pareto_solutions_count: int
    portfolios: List[PortfolioSchema]

# --- IMPLEMENTATION PLAN SCHEMAS ---

class PlanStepSchema(BaseModel):
    phase: int
    phase_name: str
    intervention_id: str
    intervention_name: str
    duration_months: int
    estimated_cost_inr: float
    responsible_stakeholder: str
    dependencies: List[str]
    key_milestones: List[str]

class ImplementationPlanResponse(BaseModel):
    portfolio_id: str
    portfolio_name: str
    total_cost_inr: float
    total_duration_months: int
    stakeholder_allocation: Dict[str, float]
    intervention_sequence: List[PlanStepSchema]
    monitoring_indicators: List[Dict[str, Any]]
    created_at: str

# --- PROVENANCE & MONITORING SCHEMAS ---

class ProvenanceAuditSchema(BaseModel):
    portfolio_id: str
    portfolio_name: str
    optimizer_engine: str
    objective_weights_applied: Dict[str, Any]
    feasibility_filter_audit: List[Dict[str, Any]]
    knowledge_graph_chain_sources: List[Dict[str, Any]]
    earth_observation_scene_ids: List[str]
    satellite_stac_provenance: Dict[str, Any]
    confidence_score: str

class SystemStatusResponse(BaseModel):
    status: str
    api_status: str
    database_status: str
    eo_provider_status: str
    intelligence_engine_status: str
    optimizer_status: str
    background_worker_status: str
    timestamp: str
    application_version: str

# --- MASTER ORCHESTRATION & JOB SCHEMAS ---

class NexusAnalyzeRequest(BaseModel):
    geography_id: str = "rewa"
    bbox: List[float] = [81.1, 24.4, 81.5, 24.8]
    date_range_start: str = "2024-01-01"
    date_range_end: str = "2026-08-01"
    data_sources: List[str] = ["Sentinel-2", "Sentinel-1", "Landsat"]
    budget_limit_inr: float = 200000000.0
    time_horizon_months: int = 36
    max_risk_level: str = "HIGH"

class NexusJobStatusResponse(BaseModel):
    job_id: str
    status: str  # QUEUED, PROCESSING, COMPLETED, FAILED
    progress_percent: int
    stage: str
    created_at: str
    updated_at: str
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
