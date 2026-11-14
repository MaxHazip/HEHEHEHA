import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import basicSsl from '@vitejs/plugin-basic-ssl'
import path from 'path'

const useHttps = process.env.VITE_HTTPS === '1'
const backendTarget =
  process.env.VITE_API_TARGET ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react(), ...(useHttps ? [basicSsl()] : [])],
  server: {
    host: useHttps ? true : undefined,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        ws: true,
        // Локальные ИИ-модели на CPU могут отвечать минутами.
        timeout: 600_000,
        proxyTimeout: 600_000,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})