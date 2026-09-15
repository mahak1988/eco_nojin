import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act, fireEvent } from '@testing-library/react';
import {
  DashboardProvider,
  useDashboard,
  useDashboardVisibility,
  useDashboardOrder,
  useDashboardDragMode,
} from '../context/DashboardContext';

const TestComponent = () => {
  const { visibleSections, order, dragMode, toggleSection, moveSection, setDragMode, resetDefaults } = useDashboard();
  return (
    <div>
      <div data-testid="visible-sections">{JSON.stringify(visibleSections)}</div>
      <div data-testid="order">{JSON.stringify(order)}</div>
      <div data-testid="drag-mode">{String(dragMode)}</div>
      <button onClick={() => toggleSection('kpi')}>Toggle KPI</button>
      <button onClick={() => moveSection(0, 2)}>Move</button>
      <button onClick={() => setDragMode(true)}>Enable Drag</button>
      <button onClick={resetDefaults}>Reset</button>
    </div>
  );
};

const SelectorTestComponent = () => {
  const { visibleSections, toggleSection, resetDefaults } = useDashboardVisibility();
  const { order, moveSection } = useDashboardOrder();
  const { dragMode, setDragMode } = useDashboardDragMode();
  return (
    <div>
      <div data-testid="visible-sections">{JSON.stringify(visibleSections)}</div>
      <div data-testid="order">{JSON.stringify(order)}</div>
      <div data-testid="drag-mode">{String(dragMode)}</div>
      <button onClick={() => toggleSection('kpi')}>Toggle KPI</button>
      <button onClick={() => moveSection(0, 2)}>Move</button>
      <button onClick={() => setDragMode(true)}>Enable Drag</button>
      <button onClick={resetDefaults}>Reset</button>
    </div>
  );
};

function renderWithProvider(ui: React.ReactElement) {
  return render(<DashboardProvider>{ui}</DashboardProvider>);
}

describe('DashboardContext', () => {
  beforeEach(() => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
      if (key === 'econojin-dashboard') return null;
      return null;
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Default State', () => {
    it('provides default visibility for all sections', () => {
      renderWithProvider(<TestComponent />);
      const visible = JSON.parse(screen.getByTestId('visible-sections').textContent!);
      expect(visible.kpi).toBe(true);
      expect(visible.charts).toBe(true);
      expect(visible.categories).toBe(true);
      expect(visible.calculators).toBe(true);
      expect(visible.hub).toBe(true);
      expect(visible.portfolio).toBe(true);
    });

    it('provides default order', () => {
      renderWithProvider(<TestComponent />);
      const order = JSON.parse(screen.getByTestId('order').textContent!);
      expect(order).toEqual(['kpi', 'charts', 'categories', 'calculators', 'hub', 'portfolio']);
    });

    it('dragMode defaults to false', () => {
      renderWithProvider(<TestComponent />);
      expect(screen.getByTestId('drag-mode').textContent).toBe('false');
    });
  });

  describe('toggleSection', () => {
    it('toggles section visibility', () => {
      renderWithProvider(<TestComponent />);
      const btn = screen.getByText('Toggle KPI');
      
      act(() => fireEvent.click(btn));
      
      const visible = JSON.parse(screen.getByTestId('visible-sections').textContent!);
      expect(visible.kpi).toBe(false);
      
      act(() => fireEvent.click(btn));
      
      const visible2 = JSON.parse(screen.getByTestId('visible-sections').textContent!);
      expect(visible2.kpi).toBe(true);
    });
  });

  describe('moveSection', () => {
    it('moves section from one index to another', () => {
      renderWithProvider(<TestComponent />);
      const btn = screen.getByText('Move');
      
      act(() => fireEvent.click(btn));
      
      const order = JSON.parse(screen.getByTestId('order').textContent!);
      expect(order).toEqual(['charts', 'categories', 'kpi', 'calculators', 'hub', 'portfolio']);
    });
  });

  describe('setDragMode', () => {
    it('enables drag mode', () => {
      renderWithProvider(<TestComponent />);
      const btn = screen.getByText('Enable Drag');
      
      act(() => fireEvent.click(btn));
      
      expect(screen.getByTestId('drag-mode').textContent).toBe('true');
    });
  });

  describe('resetDefaults', () => {
    it('resets all state to defaults', () => {
      renderWithProvider(<TestComponent />);
      
      act(() => {
        fireEvent.click(screen.getByText('Toggle KPI'));
        fireEvent.click(screen.getByText('Enable Drag'));
        fireEvent.click(screen.getByText('Move'));
      });
      
      act(() => fireEvent.click(screen.getByText('Reset')));
      
      const visible = JSON.parse(screen.getByTestId('visible-sections').textContent!);
      expect(visible.kpi).toBe(true);
      expect(screen.getByTestId('drag-mode').textContent).toBe('false');
      const order = JSON.parse(screen.getByTestId('order').textContent!);
      expect(order).toEqual(['kpi', 'charts', 'categories', 'calculators', 'hub', 'portfolio']);
    });
  });

  describe('Selector hooks', () => {
    it('useDashboardVisibility provides only visibility-related state', () => {
      renderWithProvider(<SelectorTestComponent />);
      const visible = JSON.parse(screen.getByTestId('visible-sections').textContent!);
      expect(visible.kpi).toBe(true);
    });

    it('useDashboardOrder provides only order-related state', () => {
      renderWithProvider(<SelectorTestComponent />);
      const order = JSON.parse(screen.getByTestId('order').textContent!);
      expect(order).toEqual(['kpi', 'charts', 'categories', 'calculators', 'hub', 'portfolio']);
    });

    it('useDashboardDragMode provides only dragMode state', () => {
      renderWithProvider(<SelectorTestComponent />);
      expect(screen.getByTestId('drag-mode').textContent).toBe('false');
    });
  });

  describe('Persistence', () => {
    it('loads state from localStorage on mount', () => {
      const savedState = {
        visibleSections: { kpi: false, charts: true, categories: false, calculators: true, hub: false, portfolio: true },
        order: ['charts', 'calculators', 'portfolio', 'kpi', 'categories', 'hub'],
        dragMode: true,
      };
      
      vi.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
        if (key === 'econojin-dashboard') return JSON.stringify(savedState);
        return null;
      });
      
      renderWithProvider(<TestComponent />);
      
      const visible = JSON.parse(screen.getByTestId('visible-sections').textContent!);
      expect(visible.kpi).toBe(false);
      expect(visible.charts).toBe(true);
      
      const order = JSON.parse(screen.getByTestId('order').textContent!);
      expect(order).toEqual(['charts', 'calculators', 'portfolio', 'kpi', 'categories', 'hub']);
      
      expect(screen.getByTestId('drag-mode').textContent).toBe('true');
    });

    it('saves state to localStorage on change', () => {
      const setItemSpy = vi.spyOn(Storage.prototype, 'setItem');
      
      renderWithProvider(<TestComponent />);
      act(() => fireEvent.click(screen.getByText('Toggle KPI')));
      
      expect(setItemSpy).toHaveBeenCalledWith(
        'econojin-dashboard',
        expect.stringContaining('"kpi":false')
      );
    });

    it('ignores invalid localStorage data and uses defaults', () => {
      vi.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => {
        if (key === 'econojin-dashboard') return 'invalid json';
        return null;
      });
      
      renderWithProvider(<TestComponent />);
      
      const visible = JSON.parse(screen.getByTestId('visible-sections').textContent!);
      expect(visible.kpi).toBe(true);
    });
  });

  describe('Error boundary', () => {
    it('throws when useDashboard used outside provider', () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      expect(() => {
        render(<TestComponent />);
      }).toThrow('useDashboard must be used within DashboardProvider');
      
      consoleError.mockRestore();
    });
  });
});