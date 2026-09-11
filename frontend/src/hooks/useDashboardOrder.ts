/** Drag-drop hook for dashboard sections. */

import { useState, useCallback, useEffect } from 'react';

export type DashboardSection = 'kpi' | 'charts' | 'categories' | 'calculators' | 'hub' | 'portfolio';

const STORAGE_KEY = 'econojin-dashboard-order';

const DEFAULT_ORDER: DashboardSection[] = [
  'kpi',
  'charts',
  'categories',
  'calculators',
  'hub',
  'portfolio',
];

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

export function useDashboardOrder() {
  const [order, setOrder] = useState<DashboardSection[]>(loadOrder);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(order));
    } catch {
      // ignore
    }
  }, [order]);

  const moveSection = useCallback((fromIndex: number, toIndex: number) => {
    setOrder((prev) => {
      const newOrder = [...prev];
      const [moved] = newOrder.splice(fromIndex, 1);
      newOrder.splice(toIndex, 0, moved);
      return newOrder;
    });
  }, []);

  const resetOrder = useCallback(() => {
    setOrder([...DEFAULT_ORDER]);
  }, []);

  return { order, moveSection, resetOrder };
}
