import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/search': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/items': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/random': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/browse': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/metadata': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
