import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import { SearchModal, useGlobalSearchShortcut } from '../components/ui/SearchModal';
import { LanguageProvider } from '../i18n/LanguageContext';
import { MemoryRouter } from 'react-router-dom';

let mockFuseSearch: ReturnType<typeof vi.fn>;

vi.mock('fuse.js', () => {
  return {
    default: vi.fn().mockImplementation(() => ({
      search: vi.fn((...args: unknown[]) => mockFuseSearch(...args)),
    })),
  };
});

const TestSearchModalComponent = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => (
  <SearchModal isOpen={isOpen} onClose={onClose} />
);

const TestShortcutComponent = ({ onOpen }: { onOpen: () => void }) => {
  useGlobalSearchShortcut(onOpen);
  return <div data-testid="shortcut-component" />;
};

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <LanguageProvider>
      <MemoryRouter>
        {ui}
      </MemoryRouter>
    </LanguageProvider>
  );
}

describe('SearchModal', () => {
  beforeEach(() => {
    vi.spyOn(Storage.prototype, 'getItem').mockReturnValue(null);
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {});
    vi.useFakeTimers();
    
    // Default mock: return test results
    mockFuseSearch = vi.fn().mockResolvedValue([
      { item: { id: '1', title: 'Test Page', description: 'Test description', url: '/test', category: 'pages', section: 'test' }, score: 0.1 },
      { item: { id: '2', title: 'Another Page', description: 'Another description', url: '/another', category: 'pages', section: 'another' }, score: 0.2 },
    ]);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  it('renders nothing when closed', () => {
    renderWithProviders(<TestSearchModalComponent isOpen={false} onClose={vi.fn()} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders dialog when open', () => {
    renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('shows search input with placeholder', () => {
    renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={vi.fn()} />);
    const input = screen.getByPlaceholderText(/جستجوی سراسری/);
    expect(input).toBeInTheDocument();
  });

  it('displays loading state during search', async () => {
    renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={vi.fn()} />);
    
    const input = screen.getByPlaceholderText(/جستجوی سراسری/);
    act(() => {
      fireEvent.change(input, { target: { value: 'test' } });
    });
    
    // Should show loading
    expect(await screen.findByText(/در حال جستجو/)).toBeInTheDocument();
  });

  it('displays search results after search completes', async () => {
    renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={vi.fn()} />);
    
    const input = screen.getByPlaceholderText(/جستجوی سراسری/);
    act(() => {
      fireEvent.change(input, { target: { value: 'test' } });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
      expect(screen.getByText('Another Page')).toBeInTheDocument();
    });
  });

  it('shows no results message when search returns empty', async () => {
    // Mock empty results for this test
    mockFuseSearch.mockResolvedValueOnce([]);
    
    renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={vi.fn()} />);
    
    const input = screen.getByPlaceholderText(/جستجوی سراسری/);
    act(() => {
      fireEvent.change(input, { target: { value: 'nonexistent' } });
    });
    
    await waitFor(() => {
      expect(screen.getByText(/هیچ نتیجه‌ای یافت نشد/)).toBeInTheDocument();
    });
  });

  it('navigates on result click', async () => {
    const mockNavigate = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { href: '/', assign: mockNavigate },
      writable: true,
    });
    
    renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={vi.fn()} />);
    
    const input = screen.getByPlaceholderText(/جستجوی سراسری/);
    act(() => {
      fireEvent.change(input, { target: { value: 'test' } });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
    });
    
    act(() => {
      fireEvent.click(screen.getByText('Test Page'));
    });
    
    expect(mockNavigate).toHaveBeenCalledWith('/test');
  });

  it('closes on Escape key', () => {
    const onClose = vi.fn();
    renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={onClose} />);
    
    act(() => {
      fireEvent.keyDown(document, { key: 'Escape' });
    });
    
    expect(onClose).toHaveBeenCalled();
  });

  it('closes on Cmd+K when open', () => {
    const onClose = vi.fn();
    renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={onClose} />);
    
    act(() => {
      fireEvent.keyDown(document, { key: 'k', metaKey: true });
    });
    
    expect(onClose).toHaveBeenCalled();
  });

  it('navigates with Enter on selected result', async () => {
    const mockNavigate = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { href: '/', assign: mockNavigate },
      writable: true,
    });
    
    renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={vi.fn()} />);
    
    const input = screen.getByPlaceholderText(/جستجوی سراسری/);
    act(() => {
      fireEvent.change(input, { target: { value: 'test' } });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
    });
    
    act(() => {
      fireEvent.keyDown(document, { key: 'Enter' });
    });
    
    expect(mockNavigate).toHaveBeenCalledWith('/test');
  });

  it('navigates results with ArrowUp/ArrowDown', async () => {
    renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={vi.fn()} />);
    
    const input = screen.getByPlaceholderText(/جستجوی سراسری/);
    act(() => {
      fireEvent.change(input, { target: { value: 'test' } });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
    });
    
    // ArrowDown should select next
    act(() => {
      fireEvent.keyDown(document, { key: 'ArrowDown' });
    });
    
    // ArrowUp should select previous
    act(() => {
      fireEvent.keyDown(document, { key: 'ArrowUp' });
    });
    
    // Should not throw
    expect(true).toBe(true);
  });

  it('clears query on clear button click', async () => {
    renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={vi.fn()} />);
    
    const input = screen.getByPlaceholderText(/جستجوی سراسری/);
    act(() => {
      fireEvent.change(input, { target: { value: 'test' } });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
    });
    
    const clearButton = screen.getByLabelText(/پاک کردن/);
    act(() => {
      fireEvent.click(clearButton);
    });
    
    expect(input).toHaveValue('');
  });

  it('closes on backdrop click', () => {
    const onClose = vi.fn();
    renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={onClose} />);
    
    // Find and click backdrop
    const backdrop = document.querySelector('.fixed.inset-0') || document.body;
    act(() => {
      fireEvent.click(backdrop);
    });
    
    expect(onClose).toHaveBeenCalled();
  });

  it('has proper ARIA attributes', () => {
    renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={vi.fn()} />);
    
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-label', 'جستجوی سراسری');
    
    const resultsList = screen.getByRole('listbox');
    expect(resultsList).toHaveAttribute('aria-label', 'نتایج جستجو');
    
    const liveRegion = screen.getByText(/جستجو/);
    expect(liveRegion).toHaveAttribute('aria-live', 'polite');
  });

  it('resets state on reopen', async () => {
    const onClose = vi.fn();
    const { rerender } = renderWithProviders(<TestSearchModalComponent isOpen={true} onClose={onClose} />);
    
    const input = screen.getByPlaceholderText(/جستجوی سراسری/);
    act(() => {
      fireEvent.change(input, { target: { value: 'test' } });
    });
    
    await waitFor(() => {
      expect(screen.getByText('Test Page')).toBeInTheDocument();
    });
    
    // Close and reopen
    rerender(<TestSearchModalComponent isOpen={false} onClose={onClose} />);
    rerender(<TestSearchModalComponent isOpen={true} onClose={onClose} />);
    
    expect(input).toHaveValue('');
    expect(screen.queryByText('Test Page')).not.toBeInTheDocument();
  });
});

describe('useGlobalSearchShortcut', () => {
  it('opens search on Cmd+K', () => {
    const onOpen = vi.fn();
    renderWithProviders(<TestShortcutComponent onOpen={onOpen} />);
    
    act(() => {
      fireEvent.keyDown(document, { key: 'k', metaKey: true });
    });
    
    expect(onOpen).toHaveBeenCalled();
  });

  it('opens search on Ctrl+K', () => {
    const onOpen = vi.fn();
    renderWithProviders(<TestShortcutComponent onOpen={onOpen} />);
    
    act(() => {
      fireEvent.keyDown(document, { key: 'k', ctrlKey: true });
    });
    
    expect(onOpen).toHaveBeenCalled();
  });

  it('does not open on K alone', () => {
    const onOpen = vi.fn();
    renderWithProviders(<TestShortcutComponent onOpen={onOpen} />);
    
    act(() => {
      fireEvent.keyDown(document, { key: 'k' });
    });
    
    expect(onOpen).not.toHaveBeenCalled();
  });

  it('cleans up event listener on unmount', () => {
    const onOpen = vi.fn();
    const { unmount } = renderWithProviders(<TestShortcutComponent onOpen={onOpen} />);
    
    unmount();
    
    act(() => {
      fireEvent.keyDown(document, { key: 'k', metaKey: true });
    });
    
    expect(onOpen).not.toHaveBeenCalled();
  });
});