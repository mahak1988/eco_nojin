import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { ContractList, RecordList, SummaryList, UnavailableNotice } from './ResearchParts';

afterEach(() => {
  cleanup();
});

describe('SummaryList', () => {
  it('renders a missing fact as the shared unavailable label', () => {
    render(
      <SummaryList
        items={[
          { id: 'route', label: 'Service', value: 'research-workspace' },
          { id: 'endpoint', label: 'Endpoint', value: null },
        ]}
        unavailableLabel="Unavailable"
      />,
    );

    expect(screen.getByText('research-workspace')).not.toBeNull();
    expect(screen.getByText('Unavailable')).not.toBeNull();
    expect(screen.getByText('research-workspace').getAttribute('title')).toBe('research-workspace');
  });

  it('renders nothing for an empty fact list', () => {
    const { container } = render(<SummaryList items={[]} unavailableLabel="Unavailable" />);
    expect(container.firstChild).toBeNull();
  });
});

describe('ContractList', () => {
  it('labels every endpoint and keeps the state of unwired contracts', () => {
    render(
      <ContractList
        endpointLabel="Endpoint"
        unavailableLabel="Unavailable"
        items={[
          {
            id: 'research-datasets',
            label: 'Science and evidence',
            endpoint: null,
            state: 'down',
            stateLabel: 'Unavailable',
          },
          {
            id: 'cpp-kernel-status',
            label: 'Kernels',
            endpoint: '/api/v1/models/cpp-status',
            state: 'ok',
            stateLabel: 'Live',
          },
        ]}
      />,
    );

    expect(screen.getAllByText('Endpoint:')).toHaveLength(2);
    expect(screen.getByText('/api/v1/models/cpp-status')).not.toBeNull();
    expect(screen.getAllByText('Unavailable').length).toBeGreaterThan(0);
    expect(screen.getByText('Live')).not.toBeNull();
  });
});

describe('RecordList', () => {
  it('shows a named record list with its facts and status', () => {
    render(
      <RecordList
        label="Source"
        unavailableLabel="Unavailable"
        emptyLabel="No record"
        items={[
          {
            id: 'era5-cds',
            title: 'ERA5 Reanalysis (CDS)',
            technical: 'era5-cds',
            state: 'ok',
            stateLabel: 'live',
            facts: [{ id: 'doi', label: 'Evidence', value: null }],
          },
        ]}
      />,
    );

    expect(screen.getByRole('region', { name: 'Source' })).not.toBeNull();
    expect(screen.getByText('ERA5 Reanalysis (CDS)')).not.toBeNull();
    expect(screen.getByText('era5-cds')).not.toBeNull();
    expect(screen.getByText('live')).not.toBeNull();
    expect(screen.getByText('Unavailable')).not.toBeNull();
  });

  it('falls back to the empty label when the endpoint returned no record', () => {
    render(
      <RecordList
        label="Source"
        unavailableLabel="Unavailable"
        emptyLabel="No record"
        items={[]}
      />,
    );

    expect(screen.getByText('No record')).not.toBeNull();
  });
});

describe('UnavailableNotice', () => {
  it('states the missing contract without inventing a value', () => {
    render(<UnavailableNotice title="Not connected yet" detail="No unverified data is shown." />);

    expect(screen.getByText('Not connected yet')).not.toBeNull();
    expect(screen.getByText('No unverified data is shown.')).not.toBeNull();
  });
});
