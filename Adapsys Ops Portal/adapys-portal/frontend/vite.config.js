import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Temporary production debug build to avoid minifier TDZ errors like
// "Cannot access 'me' before initialization" and to provide sourcemaps.
export default defineConfig({
  plugins: [react()],
  esbuild: {
    jsxInject: "import React from 'react'",
  },
  build: {
    sourcemap: 'inline',
    minify: false,
    target: 'es2020'
  }
})