import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { LanguageProvider } from '../i18n/LanguageContext';
import UniversalCard from '../components/ui/UniversalCard';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => <div {...props}>{children}</div>,
  },
  useReducedMotion: () => false,
}));

// Mock useLang with proper content structure
const mockContent = {
  impact: {
    liveCounters: {
      title: 'آمار لحظه‌ای',
      note: 'شمارش معکوس به پایلوت — داده‌های زنده پس از آغاز عملیات منتشر می‌شود',
      items: [
        { label: 'هکتار زیر پایش', metricKey: 'area_ha', unit: 'هکتار', icon: 'satellite' },
        { label: 'کشاورز آموزش‌دیده', metricKey: 'farmers_trained', unit: 'نفر', icon: 'people' },
        { label: 'CO₂ جلوگیری‌شده', metricKey: 'co2_sequestered_tco2e', unit: 'تن', icon: 'co2' },
        { label: 'اعتبار کربن', metricKey: 'credits_issued', unit: 'اعتبار', icon: 'leaf' },
      ],
    },
  },
};

vi.mock('../i18n/LanguageContext', () => ({
  useLang: () => ({ lang: 'fa', dir: 'rtl', t: mockContent }),
  LanguageProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Mock Icon
vi.mock('../components/ui/Icon', () => ({
  default: ({ name }: { name: string }) => <span data-testid={`icon-${name}`} />,
}));

function renderWithProvider(ui: React.ReactElement) {
  return render(<LanguageProvider>{ui}</LanguageProvider>);
}

describe('UniversalCard', () => {
  const defaultProps = {
    title: 'Test Card',
    desc: 'Test description',
    icon: 'satellite' as const,
    theme: 'leaf' as const,
  };

  it('renders card with title and description', () => {
    renderWithProvider(<UniversalCard {...defaultProps} />);
    expect(screen.getByText('Test Card')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });

  it('renders icon when provided', () => {
    renderWithProvider(<UniversalCard {...defaultProps} />);
    expect(screen.getByTestId('icon-satellite')).toBeInTheDocument();
  });

  it('applies theme gradient', () => {
    renderWithProvider(<UniversalCard {...defaultProps} theme="aqua" />);
    const card = screen.getByText('Test Card').closest('div');
    expect(card).toHaveStyle({ backgroundImage: expect.stringContaining('aqua') });
  });

  it('renders badge when provided', () => {
    renderWithProvider(<UniversalCard {...defaultProps} badge="NEW" />);
    expect(screen.getByText('NEW')).toBeInTheDocument();
  });

  it('renders unit when provided', () => {
    renderWithProvider(<UniversalCard {...defaultProps} unit="ha" />);
    expect(screen.getByText('ha')).toBeInTheDocument();
  });

  describe('Keyboard accessibility', () => {
    it('is focusable when onClick provided', () => {
      renderWithProvider(<UniversalCard {...defaultProps} onClick={vi.fn()} />);
      const card = screen.getByRole('button', { name: 'Test Card Test description' });
      expect(card).toBeInTheDocument();
      expect(card).toHaveAttribute('tabIndex', '0');
    });

    it('is not focusable when no onClick', () => {
      renderWithProvider(<UniversalCard {...defaultProps} />);
      const card = screen.getByText('Test Card').closest('div');
      expect(card).not.toHaveAttribute('tabIndex');
    });

    it('calls onClick on Enter key', () => {
      const onClick = vi.fn();
      renderWithProvider(<UniversalCard {...defaultProps} onClick={onClick} />);
      const card = screen.getByRole('button', { name: 'Test Card Test description' });
      
      act(() => {
        fireEvent.keyDown(card, { key: 'Enter' });
      });
      
      expect(onClick).toHaveBeenCalled();
    });

    it('calls onClick on Space key', () => {
      const onClick = vi.fn();
      renderWithProvider(<UniversalCard {...defaultProps} onClick={onClick} />);
      const card = screen.getByRole('button', { name: 'Test Card Test description' });
      
      act(() => {
        fireEvent.keyDown(card, { key: ' ' });
      });
      
      expect(onClick).toHaveBeenCalled();
    });
  });

  describe('Flip variant (flipOnHover=true with backContent)', () => {
    const flipProps = {
      ...defaultProps,
      icon: 'satellite' as const,
      flipOnHover: true,
      backContent: {
        source: 'Test Source',
        method: 'Test Method',
        standard: 'ISO 14064',
        frequency: 'Daily',
        apiField: 'metrics/area',
      },
    };

    it('renders front face with title and description', () => {
      renderWithProvider(<UniversalCard {...flipProps} />);
      expect(screen.getByText('Test Card')).toBeInTheDocument();
      expect(screen.getByText('Test description')).toBeInTheDocument();
    });

    it('renders flip hint in Persian (default lang)', () => {
      renderWithProvider(<UniversalCard {...flipProps} />);
      expect(screen.getByText('چرخاندن برای جزئیات')).toBeInTheDocument();
    });

    it('renders front face elements', () => {
      renderWithProvider(<UniversalCard {...flipProps} />);
      expect(screen.getByText('Test Card')).toBeInTheDocument();
      expect(screen.getByTestId('icon-satellite')).toBeInTheDocument();
    });
  });

  describe('Non-flip variant (flipOnHover=false or no backContent)', () => {
    it('renders simple card without flip', () => {
      renderWithProvider(<UniversalCard {...defaultProps} flipOnHover={false} />);
      expect(screen.getByText('Test Card')).toBeInTheDocument();
      expect(screen.queryByText('Hover to reveal')).not.toBeInTheDocument();
      expect(screen.queryByText('چرخاندن برای جزئیات')).not.toBeInTheDocument();
    });

    it('renders children when provided', () => {
      renderWithProvider(
        <UniversalCard {...defaultProps} flipOnHover={false}>
          <span data-testid="children">Custom content</span>
        </UniversalCard>
      );
      expect(screen.getByTestId('children')).toBeInTheDocument();
    });
  });

  describe('Theme variants', () => {
    const themes: Array<'leaf' | 'aqua' | 'sand' | 'night' | 'default'> = ['leaf', 'aqua', 'sand', 'night', 'default'];
    
    themes.forEach(theme => {
      it(`applies ${theme} theme`, () => {
        renderWithProvider(<UniversalCard {...defaultProps} theme={theme} />);
        const card = screen.getByText('Test Card').closest('div');
        expect(card).toBeInTheDocument();
      });
    });
  });

  describe('Animation', () => {
    it('renders card with initial state', () => {
      renderWithProvider(<UniversalCard {...defaultProps} index={0} />);
      expect(screen.getByText('Test Card')).toBeInTheDocument();
    });
  });
});