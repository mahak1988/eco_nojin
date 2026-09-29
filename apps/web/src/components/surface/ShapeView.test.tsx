import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { isPlainObject, objectRowsOf, ShapeView } from './ShapeView';

afterEach(() => {
  cleanup();
});

describe('isPlainObject', () => {
  it('separates a record from the shapes a response may also carry', () => {
    expect(isPlainObject({ a: 1 })).toBe(true);
    expect(isPlainObject([])).toBe(false);
    expect(isPlainObject(null)).toBe(false);
    expect(isPlainObject('text')).toBe(false);
  });
});

describe('objectRowsOf', () => {
  it('keeps object rows and drops the rest without inventing any', () => {
    expect(objectRowsOf([{ a: 1 }, 5, null, ['x'], { b: 2 }])).toEqual([{ a: 1 }, { b: 2 }]);
    expect(objectRowsOf('not an array')).toEqual([]);
  });
});

describe('ShapeView', () => {
  it('names every key the gateway sent and none it did not', () => {
    render(<ShapeView value={{ total_projects: 3, auth_required: false }} />);

    expect(screen.getByText('total_projects')).toBeTruthy();
    expect(screen.getByText('auth_required')).toBeTruthy();
    expect(screen.queryByText('elevation_m')).toBeNull();
  });

  it('renders a missing value as a dash rather than a fabricated number', () => {
    render(<ShapeView value={{ a: null }} />);
    expect(screen.getByText('—')).toBeTruthy();
  });

  it('turns a nested array of records into a table keyed by its own columns', () => {
    render(<ShapeView value={{ data: [{ site_id: 1 }, { site_id: 2, koppen: 'Csa' }] }} />);

    const headers = screen.getAllByRole('columnheader').map((cell) => cell.textContent);
    expect(headers).toEqual(['site_id', 'koppen']);
  });

  it('reads the table out of a top-level array too', () => {
    render(<ShapeView value={[{ id: 'a' }, { id: 'b', name: 'x' }]} />);
    expect(screen.getAllByRole('columnheader').map((c) => c.textContent)).toEqual(['id', 'name']);
  });

  it('shows a scalar list when the payload is a flat array', () => {
    render(<ShapeView value={['/dashboard/public/full', '/dashboard/public/carbon']} />);
    expect(screen.getByText('/dashboard/public/full')).toBeTruthy();
  });

  it('renders a nested object instead of collapsing it to [object Object]', () => {
    render(<ShapeView value={{ data: { total: 7, unit: 'ha' } }} />);
    expect(screen.getByText('total')).toBeTruthy();
    expect(screen.getByText('ha')).toBeTruthy();
  });

  it('does not claim a value for an empty object or an empty array', () => {
    const { container: emptyObject } = render(<ShapeView value={{}} />);
    expect(emptyObject.querySelector('table')).toBeNull();

    cleanup();
    const { container: emptyArray } = render(<ShapeView value={[]} />);
    expect(emptyArray.querySelector('table')).toBeNull();
  });

  it('renders a null payload as a dash', () => {
    render(<ShapeView value={null} />);
    expect(screen.getByText('—')).toBeTruthy();
  });
});
