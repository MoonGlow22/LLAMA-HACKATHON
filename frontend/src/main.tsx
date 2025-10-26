import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

// Uygulamayı root elementine render et
const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found. index.html içinde <div id="root"></div> olduğundan emin olun.');
}

createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);