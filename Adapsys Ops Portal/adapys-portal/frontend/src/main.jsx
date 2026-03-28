import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';

if (typeof document !== 'undefined') {
  document.documentElement.lang = 'en-AU';
}

if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      // Keep app functional even if SW registration fails.
    });
  });
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
