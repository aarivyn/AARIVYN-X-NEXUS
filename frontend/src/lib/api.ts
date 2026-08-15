// Typed client for the NEXUS backend API.
import type {
  BudgetRecord,
  ContextSignals,
  EOLayerResponse,
  FeasibilityFilterRequest,
  FeasibilityFilterResponse,
  ImplementationPlan,
  IngestRecordMeta,
  InterventionCard,
  LayerType,
  ListResponse,
  LocationRecord,
  LoginRequest,
  LoginResponse,
  MapsHealth,
  NexusAnalyzeRequest,
  NexusJobStatus,
  OnboardingRequest,
  OptimizeRunRequest,
  OptimizeRunResponse,
  Persona,
  Portfolio,
  ProvenanceAudit,
  RegisterRequest,
  RegisterResponse,
  SocialGroup,
  SocialGroupProfile,
  SocialTaxonomy,
  TimelineRecord,
  UploadResponse,
  UserProfile,
  WaterAnalyzeRequest,
  WaterAnalyzeResponse,
  WorkspaceContext,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, message: string, detail = "") {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  token?: string | null,
  isForm = false
): Promise<T> {
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  let payload: BodyInit | undefined;
  if (body !== undefined) {
    if (isForm) {
      payload = body as FormData;
    } else {
      headers["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }
  }
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, { method, headers, body: payload });
  } catch {
    throw new ApiError(0, "Cannot reach the NEXUS backend", `Is the API running at ${API_BASE}? Start it with: uvicorn app.main:app --port 8000`);
  }
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const err = (data as { error?: string; message?: string; detail?: string }) ?? {};
    throw new ApiError(
      res.status,
      err.error || err.message || `Request failed (${res.status})`,
      err.detail || (typeof data === "string" ? data : "")
    );
  }
  return data as T;
}

export const api = {
  // ---- Auth & Workspace ----
  register: (r: RegisterRequest) =>
    request<RegisterResponse>("POST", "/auth/register", r),
  login: (r: LoginRequest) => request<LoginResponse>("POST", "/auth/login", r),
  me: (token: string) => request<UserProfile>("GET", "/auth/me", undefined, token),
  onboarding: (r: OnboardingRequest, token?: string | null) =>
    request<{ user_id: number; persona: Persona; geography_name: string }>("POST", "/auth/onboarding", r, token),
  workspaceCurrent: (persona: Persona, token?: string | null) =>
    request<WorkspaceContext>("GET", `/workspace/current?persona=${persona}`, undefined, token),

  // ---- Earth Observation ----
  eoLayer: (layer: LayerType, bbox?: [number, number, number, number], token?: string | null) => {
    const q = bbox
      ? `&min_lon=${bbox[0]}&min_lat=${bbox[1]}&max_lon=${bbox[2]}&max_lat=${bbox[3]}`
      : "";
    return request<EOLayerResponse>("GET", `/eo/layers?layer_type=${layer}${q}`, undefined, token);
  },
  overlayUrl: (layer: LayerType) => `${API_BASE}/map/overlay/${layer}`,

  // ---- Water Intelligence ----
  waterAnalyze: (r: WaterAnalyzeRequest, token?: string | null) =>
    request<WaterAnalyzeResponse>("POST", "/water/analyze", r, token),
  contextSignals: (geographyId: string, token?: string | null) =>
    request<ContextSignals>("GET", `/context/${geographyId}/signals`, undefined, token),

  // ---- Knowledge Graph ----
  interventions: (domain = "Water", token?: string | null) =>
    request<InterventionCard[]>("GET", `/graph/interventions?domain=${domain}`, undefined, token),
  graphDiscover: (
    body: { detected_problem: string; geography_id: string; max_depth?: number },
    token?: string | null
  ) => request<Record<string, unknown>>("POST", "/graph/discover", body, token),

  // ---- Feasibility ----
  feasibility: (r: FeasibilityFilterRequest, token?: string | null) =>
    request<FeasibilityFilterResponse>("POST", "/feasibility/filter", r, token),

  // ---- Optimizer ----
  optimize: (r: OptimizeRunRequest, token?: string | null) =>
    request<OptimizeRunResponse>("POST", "/optimize/run", r, token),
  pareto: (token?: string | null) =>
    request<{ status: string; portfolios: Portfolio[] }>("GET", "/portfolio/pareto", undefined, token),

  // ---- Implementation Plan & Provenance ----
  implementationPlan: (portfolioId: string, token?: string | null) =>
    request<ImplementationPlan>("POST", `/portfolio/${portfolioId}/implementation-plan`, {}, token),
  provenance: (portfolioId: string, token?: string | null) =>
    request<ProvenanceAudit>("GET", `/provenance/${portfolioId}`, undefined, token),

  // ---- Master pipeline ----
  nexusAnalyze: (r: NexusAnalyzeRequest, token?: string | null) =>
    request<NexusJobStatus>("POST", "/api/v1/nexus/analyze", r, token),
  nexusJob: (jobId: string, token?: string | null) =>
    request<NexusJobStatus>("GET", `/api/v1/nexus/jobs/${jobId}`, undefined, token),

  // ---- Site data ----
  getBudget: (token?: string | null) => request<BudgetRecord>("GET", "/api/v1/budget", undefined, token),
  putBudget: (r: Partial<BudgetRecord>, token?: string | null) =>
    request<BudgetRecord>("PUT", "/api/v1/budget", r, token),

  listLocations: (token?: string | null) =>
    request<ListResponse<LocationRecord>>("GET", "/api/v1/locations", undefined, token),
  createLocation: (r: Partial<LocationRecord>, token?: string | null) =>
    request<LocationRecord>("POST", "/api/v1/locations", r, token),
  deleteLocation: (id: string, token?: string | null) =>
    request<null>("DELETE", `/api/v1/locations/${id}`, undefined, token),

  socialTaxonomy: (token?: string | null) =>
    request<SocialTaxonomy>("GET", "/api/v1/social/taxonomy", undefined, token),
  listSocialGroups: (token?: string | null) =>
    request<ListResponse<SocialGroup>>("GET", "/api/v1/social/groups", undefined, token),
  createSocialGroup: (
    r: { name: string; intensity: number; details?: string; profiles: SocialGroupProfile[] },
    token?: string | null
  ) => request<SocialGroup>("POST", "/api/v1/social/groups", r, token),
  deleteSocialGroup: (id: string, token?: string | null) =>
    request<null>("DELETE", `/api/v1/social/groups/${id}`, undefined, token),

  getTimeline: (token?: string | null) => request<TimelineRecord>("GET", "/api/v1/timeline", undefined, token),
  putTimeline: (r: Partial<TimelineRecord>, token?: string | null) =>
    request<TimelineRecord>("PUT", "/api/v1/timeline", r, token),

  // ---- Map ingest ----
  mapsHealth: (token?: string | null) =>
    request<MapsHealth>("GET", "/api/v1/maps/health", undefined, token),
  uploadMaps: (form: FormData, token?: string | null) =>
    request<UploadResponse>("POST", "/api/v1/maps", form, token, true),
  listMaps: (token?: string | null) =>
    request<IngestRecordMeta[]>("GET", "/api/v1/maps", undefined, token),
  deleteMap: (id: string, token?: string | null) =>
    request<null>("DELETE", `/api/v1/maps/${id}`, undefined, token),
  mapGeoJson: (id: string, token?: string | null) =>
    request<unknown>("GET", `/api/v1/maps/${id}/geojson`, undefined, token),
};

/** Error message helper: prefers backend message, falls back to generic.
 *  Backend `detail` may be an object/array (e.g. pydantic errors) — stringify it. */
export function errMsg(e: unknown): string {
  if (e instanceof ApiError) {
    const detail =
      typeof e.detail === "string" && e.detail
        ? e.detail
        : e.detail && typeof e.detail === "object"
          ? JSON.stringify(e.detail).slice(0, 400)
          : "";
    return detail ? `${e.message} — ${detail}` : e.message;
  }
  if (e instanceof Error) return e.message;
  return String(e);
}
