import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';

class RootErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: '' };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      message: String(error?.message || error || 'Unknown startup error'),
    };
  }

  componentDidCatch(error) {
    // Keep this visible in DevTools for quick diagnosis.
    console.error('Portal startup error:', error);
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div style={{ fontFamily: 'Poppins, sans-serif', margin: '20px', lineHeight: 1.5 }}>
        <h2 style={{ color: '#740839', marginBottom: 8 }}>Portal could not load</h2>
        <div style={{ marginBottom: 10 }}>
          Please refresh once. If this persists, share this message with support:
        </div>
        <pre
          style={{
            background: '#fff6fb',
            border: '1px solid #ef2b97',
            borderRadius: 8,
            padding: 10,
            whiteSpace: 'pre-wrap',
          }}
        >
          {this.state.message}
        </pre>
      </div>
    );
  }
}

if (typeof document !== 'undefined') {
  document.documentElement.lang = 'en-AU';
}

if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.getRegistrations().then((registrations) => {
      registrations.forEach((registration) => {
        registration.unregister();
      });
    });

    if ('caches' in window) {
      caches.keys().then((keys) => {
        keys.forEach((key) => caches.delete(key));
      });
    }
  });
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RootErrorBoundary>
      <App />
    </RootErrorBoundary>
  </React.StrictMode>
);
