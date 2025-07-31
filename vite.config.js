
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from 'tailwindcss'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    react()
  ],
  resolve: {
    alias: {
      '@': new URL('./frontend/src', import.meta.url).pathname
    }
  },
  server: {
    port: 3000
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./frontend/tests/setup.ts'],
    css: true,
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'frontend/tests/',
        '**/*.d.ts',
        '**/*.config.*',
        'frontend/src/models/ws_models_generated.ts' // Generated files
      ]
    }
  }
})
