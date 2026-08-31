import './index.css';
import './styles/design-tokens.css';
import './styles/smooth-scroll.css';
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { LanguageProvider } from './i18n/LanguageContext';
import App from './App'
import { usePerformance } from './hooks/usePerformance'
import './styles/global.css'
import './i18n/config'; // Initialize i18n

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// React Query client with sensible defaults
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});


// Font loading helper - prevents invisible text while fonts load
if (typeof document !== 'undefined') {
  document.documentElement.classList.add('fonts-loading');
  if ('fonts' in document) {
    document.fonts.ready.then(() => {
      document.documentElement.classList.remove('fonts-loading');
    });
  } else {
    // Fallback for older browsers
    setTimeout(() => {
      document.documentElement.classList.remove('fonts-loading');
    }, 1000);
  }
}


ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}><BrowserRouter>
    <LanguageProvider>
      <App />
    </LanguageProvider>
    </BrowserRouter></QueryClientProvider>
  </React.StrictMode>,
)
