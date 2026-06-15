import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Vite + React + Tailwind v4 (via the official Vite plugin).
export default defineConfig({
  plugins: [react(), tailwindcss()],
})
