import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { SustainabilityDashboardPrototype } from './SustainabilityDashboardPrototype';

afterEach(() => {
  cleanup();
});

describe('SustainabilityDashboardPrototype', () => {
  it('renders the Persian RTL prototype', () => {
    render(<SustainabilityDashboardPrototype locale="fa" />);

    expect(screen.getByRole('heading', { name: 'از داده‌های زنده تا تصمیم پایدار' })).not.toBeNull();
    expect(screen.getByRole('main').getAttribute('dir')).toBe('rtl');
    expect(screen.getAllByText('عدسی اثر پایدار').length).toBeGreaterThan(0);
  });

  it('updates evidence layers and goals through accessible controls', () => {
    render(<SustainabilityDashboardPrototype locale="fa" />);

    fireEvent.click(screen.getByRole('button', { name: 'خاک' }));
    expect(screen.getByRole('heading', { name: 'مواد آلی و ساختار' })).not.toBeNull();

    fireEvent.click(screen.getByRole('button', { name: /اقلیم/ }));
    expect(screen.getByText('اثر 13 · اقلیم')).not.toBeNull();
  });

  it('updates scenario values and theme without losing context', () => {
    render(<SustainabilityDashboardPrototype locale="fa" />);

    fireEvent.click(screen.getByRole('button', { name: 'شتاب‌دار' }));
    expect(screen.getByText('−۱۵٪')).not.toBeNull();
    expect(screen.getByText('مدل پیشنهادی، نه پیش‌بینی قطعی')).not.toBeNull();

    fireEvent.click(screen.getAllByLabelText('Use light theme')[0]);
    expect(screen.getByRole('main').getAttribute('data-theme')).toBe('light');
  });

  it('provides an English LTR fallback for non-Persian locales', () => {
    render(<SustainabilityDashboardPrototype locale="en" />);

    expect(
      screen.getByRole('heading', { name: 'From living data to sustainable action' }),
    ).not.toBeNull();
    expect(screen.getByRole('main').getAttribute('dir')).toBe('ltr');
  });
});
