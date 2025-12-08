import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    react(),
  ],
  server: {
    port: 3003,
    host: true,
    allowedHosts: [
      '0.0.0.0',
      'adorona.amitwithaws.site',
    ],
    hmr: false, // disable hot reload to prevent websocket errors
  },
})
