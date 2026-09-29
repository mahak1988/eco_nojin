import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { RecordTable } from './RecordTable';

afterEach(() => {
  cleanup();
});

describe('RecordTable', () => {
  it('builds its header from the columns the response carried', () => {
    render(
      <RecordTable
        records={[
          { site_id: 12, lat: 36.3 },
          { site_id: 13, koppen: 'Csa' },
        ]}
        caption="rows"
      />,
    );

    const headers = screen.getAllByRole('columnheader').map((cell) => cell.textContent);
    expect(headers).toEqual(['site_id', 'lat', 'koppen']);
    // A column the dataset never sent must not appear.
    expect(headers).not.toContain('elevation_m');
  });

  it('renders a dash for a missing value instead of a fabricated number', () => {
    // `b` is absent from the payload, so the cell has no value to show at all.
    render(<RecordTable records={[{ a: null, c: 0 }]} caption="rows" />);
    const cells = screen.getAllByRole('cell').map((cell) => cell.textContent);
    expect(cells).toEqual(['—', '0']);
  });

  it('links only the requested column and only when a builder is given', () => {
    render(
      <RecordTable
        records={[{ site_id: 12, lat: 36.3 }]}
        caption="rows"
        linkColumn="site_id"
        hrefFor={(row) => `/learn/manual/sites/${row.site_id}`}
      />,
    );

    const link = screen.getByRole('link', { name: '12' });
    expect(link.getAttribute('href')).toBe('/learn/manual/sites/12');
    expect(screen.getAllByRole('link')).toHaveLength(1);
  });

  it('caps the rendered rows and never claims to show more than it received', () => {
    render(
      <RecordTable
        records={Array.from({ length: 5 }, (_, index) => ({ n: index }))}
        caption="rows"
        maxRows={2}
      />,
    );
    expect(screen.getAllByRole('row')).toHaveLength(3);
  });

  it('renders nothing when the dataset carried no columns', () => {
    const { container } = render(<RecordTable records={[]} caption="rows" />);
    expect(container.querySelector('table')).toBeNull();
  });
});
