import './index.css';
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { LanguageProvider } from './i18n/LanguageContext';
import App from './App'
import './styles/global.css'
import './i18n/config'; // Initialize i18n

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
    <BrowserRouter>
    <LanguageProvider>
      <App />
    </LanguageProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
