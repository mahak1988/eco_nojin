import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { OptimizedImage, HeroImage, generatePlaceholder } from '../components/ui/OptimizedImage';

describe('OptimizedImage', () => {
  beforeEach(() => {
    vi.spyOn(HTMLImageElement.prototype, 'dispatchEvent').mockImplementation(() => true);
  });

  it('renders picture element with img', () => {
    render(<OptimizedImage src="/test.jpg" alt="Test image" />);
    const picture = screen.getByRole('img', { name: 'Test image' }).closest('picture');
    expect(picture).toBeInTheDocument();
  });

  it('generates WebP and AVIF sources for JPEG/PNG', () => {
    render(<OptimizedImage src="/test.jpg" alt="Test image" />);
    const picture = screen.getByRole('img', { name: 'Test image' }).closest('picture');
    const sources = picture?.querySelectorAll('source');
    expect(sources?.length).toBeGreaterThanOrEqual(2); // AVIF + WebP sources
  });

  it('does not generate sources for modern formats', () => {
    render(<OptimizedImage src="/test.webp" alt="Test image" />);
    const picture = screen.getByRole('img', { name: 'Test image' }).closest('picture');
    const sources = picture?.querySelectorAll('source');
    expect(sources?.length).toBe(0);
  });

  it('applies loading="lazy" by default', () => {
    render(<OptimizedImage src="/test.jpg" alt="Test image" />);
    const img = screen.getByRole('img', { name: 'Test image' });
    expect(img).toHaveAttribute('loading', 'lazy');
  });

  it('applies loading="eager" when priority=true', () => {
    render(<OptimizedImage src="/test.jpg" alt="Test image" priority />);
    const img = screen.getByRole('img', { name: 'Test image' });
    expect(img).toHaveAttribute('loading', 'eager');
  });

  it('applies fetchPriority="high" when priority=true', () => {
    render(<OptimizedImage src="/test.jpg" alt="Test image" priority />);
    const img = screen.getByRole('img', { name: 'Test image' });
    expect(img).toHaveAttribute('fetchpriority', 'high');
  });

  it('applies decoding="sync" when priority=true', () => {
    render(<OptimizedImage src="/test.jpg" alt="Test image" priority />);
    const img = screen.getByRole('img', { name: 'Test image' });
    expect(img).toHaveAttribute('decoding', 'sync');
  });

  it('uses provided sizes attribute', () => {
    render(<OptimizedImage src="/test.jpg" alt="Test image" sizes="(max-width: 768px) 100vw, 50vw" />);
    const picture = screen.getByRole('img', { name: 'Test image' }).closest('picture');
    const sources = picture?.querySelectorAll('source');
    sources?.forEach(source => {
      expect(source).toHaveAttribute('sizes', '(max-width: 768px) 100vw, 50vw');
    });
  });

  it('shows placeholder when provided and not loaded', () => {
    const placeholder = generatePlaceholder(20, 20, '#ff0000');
    render(<OptimizedImage src="/test.jpg" alt="Test image" placeholder={placeholder} />);
    const placeholderDiv = document.querySelector('[style*="background-image"]');
    expect(placeholderDiv).toBeInTheDocument();
  });

  it('falls back to original src on error', async () => {
    render(<OptimizedImage src="/test.jpg" alt="Test image" />);
    const img = screen.getByRole('img', { name: 'Test image' });
    
    // Simulate error on modern format
    act(() => {
      fireEvent.error(img);
    });
    
    // Should fall back to original src
    expect(img).toHaveAttribute('src', '/test.jpg');
  });

  it('applies custom className', () => {
    render(<OptimizedImage src="/test.jpg" alt="Test image" className="custom-class" />);
    const picture = screen.getByRole('img', { name: 'Test image' }).closest('picture');
    expect(picture).toHaveClass('custom-class');
  });

  it('applies width and height attributes', () => {
    render(<OptimizedImage src="/test.jpg" alt="Test image" width={800} height={600} />);
    const img = screen.getByRole('img', { name: 'Test image' });
    expect(img).toHaveAttribute('width', '800');
    expect(img).toHaveAttribute('height', '600');
  });

  it('applies sizes to img element', () => {
    render(<OptimizedImage src="/test.jpg" alt="Test image" sizes="(max-width: 768px) 100vw, 50vw" />);
    const img = screen.getByRole('img', { name: 'Test image' });
    expect(img).toHaveAttribute('sizes', '(max-width: 768px) 100vw, 50vw');
  });
});

describe('HeroImage', () => {
  it('renders with priority and eager loading', () => {
    render(<HeroImage src="/hero.jpg" alt="Hero image" />);
    const img = screen.getByRole('img', { name: 'Hero image' });
    expect(img).toHaveAttribute('loading', 'eager');
    expect(img).toHaveAttribute('fetchpriority', 'high');
  });

  it('uses responsive sizes for hero', () => {
    render(<HeroImage src="/hero.jpg" alt="Hero image" />);
    const img = screen.getByRole('img', { name: 'Hero image' });
    expect(img).toHaveAttribute('sizes', '(max-width: 768px) 100vw, 50vw');
  });
});

describe('generatePlaceholder', () => {
  it('generates valid base64 SVG data URL', () => {
    const placeholder = generatePlaceholder(40, 30, '#1a4a3a');
    expect(placeholder).toMatch(/^data:image\/svg\+xml;base64,/);
    
    // Decode and verify SVG content
    const decoded = atob(placeholder.split(',')[1]);
    expect(decoded).toContain('<svg');
    expect(decoded).toContain('width="40"');
    expect(decoded).toContain('height="30"');
    expect(decoded).toContain('fill="#1a4a3a"');
  });

  it('uses default values when not provided', () => {
    const placeholder = generatePlaceholder();
    const decoded = atob(placeholder.split(',')[1]);
    expect(decoded).toContain('width="20"');
    expect(decoded).toContain('height="20"');
    expect(decoded).toContain('fill="#1a4a3a"');
  });
});