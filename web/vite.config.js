import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
const repoName = process.env.GITHUB_REPOSITORY?.split('/')[1] || 'snes-studio';
export default defineConfig({
  plugins: [react()],
  base: process.env.GITHUB_ACTIONS ? `/${repoName}/` : '/',
  server: { port: 5173, proxy: { '/api': 'http://127.0.0.1:8765' } }
});
