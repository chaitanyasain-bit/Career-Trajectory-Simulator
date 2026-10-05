import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls to the FastAPI backend during development
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('/node_modules/three-stdlib/')) return 'vendor-three-stdlib'
          if (id.includes('/node_modules/three/')) return 'vendor-three'
          if (id.includes('/node_modules/@react-three/fiber/')) return 'vendor-r3f'
          if (id.includes('/node_modules/@react-three/drei/')) return 'vendor-drei'
        },
      },
    },
  },
})
