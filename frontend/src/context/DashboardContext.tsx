/** Unified Dashboard context — visibility, order, and drag mode for dashboard sections. */

import { createContext, useContext, useEffect, useState, useCallback } from 'react';

export type DashboardSection = 'kpi' | 'charts' | 'categories' | 'calculators' | 'hub' | 'portfolio';

export interface DashboardState {
  visibleSections: Record<DashboardSection, boolean>;
  order: DashboardSection[];
  dragMode: boolean;
}

export interface DashboardActions {
  toggleSection: (section: DashboardSection) => void;
  moveSection: (fromIndex: number, toIndex: number) => void;
  setDragMode: (enabled: boolean) => void;
  resetDefaults: () => void;
}

export type DashboardContextValue = DashboardState & DashboardActions;

const STORAGE_KEY = 'econojin-dashboard';

const DEFAULT_VISIBILITY: Record<DashboardSection, boolean> = {
  kpi: true,
  charts: true,
  categories: true,
  calculators: true,
  hub: true,
  portfolio: true,
};

const DEFAULT_ORDER: DashboardSection[] = [
  'kpi',
  'charts',
  'categories',
  'calculators',
  'hub',
  'portfolio',
];

const DEFAULT_STATE: DashboardState = {
  visibleSections: DEFAULT_VISIBILITY,
  order: DEFAULT_ORDER,
  dragMode: false,
};

function loadState(): DashboardState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === 'object') {
        return {
          visibleSections: { ...DEFAULT_VISIBILITY, ...(parsed.visibleSections || {}) },
          order: Array.isArray(parsed.order) && parsed.order.every((item: string) => DEFAULT_ORDER.includes(item as DashboardSection))
            ? parsed.order as DashboardSection[]
            : DEFAULT_ORDER,
          dragMode: Boolean(parsed.dragMode),
        };
      }
    }
  } catch {
    // ignore
  }
  return DEFAULT_STATE;
}

const DashboardContext = createContext<DashboardContextValue | null>(null);

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<DashboardState>(loadState);

  // Persist to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // ignore
    }
  }, [state]);

  const toggleSection = useCallback((section: DashboardSection) => {
    setState((prev) => ({
      ...prev,
      visibleSections: { ...prev.visibleSections, [section]: !prev.visibleSections[section] },
    }));
  }, []);

  const moveSection = useCallback((fromIndex: number, toIndex: number) => {
    setState((prev) => {
      const newOrder = [...prev.order];
      const [moved] = newOrder.splice(fromIndex, 1);
      newOrder.splice(toIndex, 0, moved);
      return { ...prev, order: newOrder };
    });
  }, []);

  const setDragMode = useCallback((enabled: boolean) => {
    setState((prev) => ({ ...prev, dragMode: enabled }));
  }, []);

  const resetDefaults = useCallback(() => {
    setState(DEFAULT_STATE);
  }, []);

  return (
    <DashboardContext.Provider value={{ ...state, toggleSection, moveSection, setDragMode, resetDefaults }}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  const ctx = useContext(DashboardContext);
  if (!ctx) {
    throw new Error('useDashboard must be used within DashboardProvider');
  }
  return ctx;
}

// Selector hooks for optimized re-renders
export function useDashboardVisibility() {
  const { visibleSections, toggleSection, resetDefaults } = useDashboard();
  return { visibleSections, toggleSection, resetDefaults };
}

export function useDashboardOrder() {
  const { order, moveSection, resetDefaults } = useDashboard();
  return { order, moveSection, resetDefaults };
}

export function useDashboardDragMode() {
  const { dragMode, setDragMode } = useDashboard();
  return { dragMode, setDragMode };
}