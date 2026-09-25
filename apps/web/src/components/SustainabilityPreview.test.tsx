import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { SustainabilityPreview } from './SustainabilityPreview';

afterEach(() => {
  cleanup();
});

describe('SustainabilityPreview', () => {
  it('renders the Persian preview and updates the selected layer', () => {
    render(<SustainabilityPreview locale="fa" />);

    expect(screen.getByRole('heading', { name: 'اثر را از داده و شواهد جدا کن' })).not.toBeNull();
    expect(screen.getAllByText('دادهٔ نمونه').length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole('button', { name: 'خاک · لایهٔ نمونه' }));
    expect(screen.getAllByText('مادهٔ آلی و ساختار').length).toBeGreaterThan(0);
  });

  it('shows live platform counts without presenting sample signals as live', () => {
    render(
      <SustainabilityPreview locale="fa" data={{ source: 'live', landscapes: 12, projects: 5 }} />,
    );

    expect(screen.getAllByText('دادهٔ پلتفرم').length).toBeGreaterThan(0);
    expect(screen.getByText('Platform Stats API')).not.toBeNull();
    expect(
      screen.getByText(/کارت‌های آب، خاک و تنوع زیستی در این پیش‌نمایش نمونه‌اند/),
    ).not.toBeNull();
    expect(screen.getByText('۱۲')).not.toBeNull();
    expect(screen.getByText('۵')).not.toBeNull();
  });

  it('renders an English fallback and keeps the compact layout available', () => {
    render(<SustainabilityPreview locale="en" compact />);

    expect(screen.getByRole('heading', { name: 'Separate impact from evidence' })).not.toBeNull();
    expect(screen.getByRole('link', { name: /Open interactive prototype/ })).not.toBeNull();
  });
});
