import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { AuthProvider } from '@eco/auth';
import { DirectionProvider, setupI18n } from '@eco/i18n';
import { App } from './app/App';
import './app.css';

setupI18n('fa');

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 15_000, refetchOnWindowFocus: true, retry: 1 },
  },
});

const root = document.getElementById('root');
if (!root) throw new Error('Root element missing');

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <DirectionProvider>
          <App />
        </DirectionProvider>
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
);