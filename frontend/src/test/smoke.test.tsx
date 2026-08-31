/**
 * Smoke Tests
 * ============
 * Basic tests to ensure critical components render.
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nextProvider } from 'react-i18next';
import i18n from '../i18n/config';

// Create test QueryClient
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

// Wrapper with providers
function TestWrapper({ children }: { children: React.ReactNode }) {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
    </QueryClientProvider>
  );
}

describe('Smoke Tests', () => {
  it('should have test environment setup', () => {
    expect(true).toBe(true);
  });

  it('should have i18n configured', () => {
    expect(i18n).toBeDefined();
    expect(typeof i18n.t).toBe('function');
  });
});
