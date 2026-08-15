"use client";

// Global app state: auth, workspace, site-data, pipeline result.
// Persisted to localStorage so a refresh keeps the session.
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api } from "./api";
import type {
  BudgetRecord,
  NexusJobStatus,
  NexusResult,
  Persona,
  TimelineRecord,
  UserProfile,
  WorkspaceContext,
} from "./types";

interface AppState {
  token: string | null;
  user: UserProfile | null;
  persona: Persona | null;
  workspace: WorkspaceContext | null;
  budget: BudgetRecord | null;
  timeline: TimelineRecord | null;
  job: NexusJobStatus | null;
  result: NexusResult | null;
  selectedPortfolioId: string | null;
}

const STORAGE_KEY = "nexus-app-state-v1";

function loadState(): Partial<AppState> {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Partial<AppState>) : {};
  } catch {
    return {};
  }
}

interface AppContextValue extends AppState {
  setAuth: (token: string, user: UserProfile, persona: Persona) => void;
  setPersona: (p: Persona) => void;
  setWorkspace: (w: WorkspaceContext) => void;
  setBudget: (b: BudgetRecord | null) => void;
  setTimeline: (t: TimelineRecord | null) => void;
  setJob: (j: NexusJobStatus | null) => void;
  setResult: (r: NexusResult | null) => void;
  selectPortfolio: (id: string | null) => void;
  logout: () => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>(() => ({
    token: null,
    user: null,
    persona: null,
    workspace: null,
    budget: null,
    timeline: null,
    job: null,
    result: null,
    selectedPortfolioId: null,
    ...loadState(),
  }));

  // Persist (omit nothing — all fields are JSON-safe).
  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      /* storage full / private mode — ignore */
    }
  }, [state]);

  const setAuth = useCallback((token: string, user: UserProfile, persona: Persona) => {
    setState((s) => ({ ...s, token, user, persona }));
  }, []);
  const setPersona = useCallback((persona: Persona) => {
    setState((s) => ({ ...s, persona }));
  }, []);
  const setWorkspace = useCallback((workspace: WorkspaceContext) => {
    setState((s) => ({ ...s, workspace }));
  }, []);
  const setBudget = useCallback((budget: BudgetRecord | null) => {
    setState((s) => ({ ...s, budget }));
  }, []);
  const setTimeline = useCallback((timeline: TimelineRecord | null) => {
    setState((s) => ({ ...s, timeline }));
  }, []);
  const setJob = useCallback((job: NexusJobStatus | null) => {
    setState((s) => ({ ...s, job }));
  }, []);
  const setResult = useCallback((result: NexusResult | null) => {
    setState((s) => ({ ...s, result }));
  }, []);
  const selectPortfolio = useCallback((selectedPortfolioId: string | null) => {
    setState((s) => ({ ...s, selectedPortfolioId }));
  }, []);
  const logout = useCallback(() => {
    setState({
      token: null, user: null, persona: null, workspace: null,
      budget: null, timeline: null, job: null, result: null, selectedPortfolioId: null,
    });
  }, []);

  const value = useMemo<AppContextValue>(
    () => ({
      ...state,
      setAuth, setPersona, setWorkspace, setBudget, setTimeline, setJob, setResult,
      selectPortfolio, logout,
    }),
    [state, setAuth, setPersona, setWorkspace, setBudget, setTimeline, setJob, setResult, selectPortfolio, logout]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppContextValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}

/** True once a user has authenticated. */
export function useAuthed(): boolean {
  const { token, user } = useApp();
  return Boolean(token && user);
}

export { api };
