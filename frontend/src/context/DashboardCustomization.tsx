/** Dashboard customization context — allows users to show/hide
 * dashboard sections and reorder them via drag-and-drop. */

import { createContext, useContext, useEffect, useState, useCallback } from 'react';

export type DashboardSection = 'kpi' | 'charts' | 'categories' | 'calculators' | 'hub' | 'portfolio';

interface DashboardCustomization {
  visibleSections: Record<DashboardSection, boolean>;
  order: DashboardSection[];
  dragMode: boolean;
  toggleSection: (section: DashboardSection) => void;
  moveSection: (fromIndex: number, toIndex: number) => void;
  setDragMode: (enabled: boolean) => void;
  resetDefaults: () => void;
}

const STORAGE_KEY = 'econojin-dashboard-customization';

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

function loadVisibility(): Record<DashboardSection, boolean> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return { ...DEFAULT_VISIBILITY, ...parsed };
      }
    }
  } catch {
    // ignore
  }
  return { ...DEFAULT_VISIBILITY };
}

function loadOrder(): DashboardSection[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.every((item): item is DashboardSection => DEFAULT_ORDER.includes(item))) {
        return parsed;
      }
    }
  } catch {
    // ignore
  }
  return [...DEFAULT_ORDER];
}

const DashboardCustomizationContext = createContext<DashboardCustomization | null>(null);

export function DashboardCustomizationProvider({ children }: { children: React.ReactNode }) {
  const [visibleSections, setVisibleSections] = useState<Record<DashboardSection, boolean>>(loadVisibility);
  const [order, setOrder] = useState<DashboardSection[]>(loadOrder);
  const [dragMode, setDragMode] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...visibleSections, order, dragMode }));
    } catch {
      // ignore
    }
  }, [visibleSections, order, dragMode]);

  const toggleSection = useCallback((section: DashboardSection) => {
    setVisibleSections((prev) => ({ ...prev, [section]: !prev[section] }));
  }, []);

  const moveSection = useCallback((fromIndex: number, toIndex: number) => {
    setOrder((prev) => {
      const newOrder = [...prev];
      const [moved] = newOrder.splice(fromIndex, 1);
      newOrder.splice(toIndex, 0, moved);
      return newOrder;
    });
  }, []);

  const resetDefaults = useCallback(() => {
    setVisibleSections({ ...DEFAULT_VISIBILITY });
    setOrder([...DEFAULT_ORDER]);
    setDragMode(false);
  }, []);

  return (
    <DashboardCustomizationContext.Provider value={{ visibleSections, order, dragMode, toggleSection, moveSection, setDragMode, resetDefaults }}>
      {children}
    </DashboardCustomizationContext.Provider>
  );
}

export function useDashboardCustomization() {
  const ctx = useContext(DashboardCustomizationContext);
  if (!ctx) throw new Error('useDashboardCustomization must be used within DashboardCustomizationProvider');
  return ctx;
}
