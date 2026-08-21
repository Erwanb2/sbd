import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Dès que React essaie d'appeler /api...
      '/api': {
        target: 'http://localhost:8000', // ...on redirige vers le backend FastAPI
        changeOrigin: true,
        // Caddy enlève le "/api" avant d'envoyer au backend, on fait pareil ici :
        rewrite: (path) => path.replace(/^\/api/, '') 
      }
    }
  }
})