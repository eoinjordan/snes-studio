import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
const repoName = process.env.GITHUB_REPOSITORY?.split('/')[1] || 'snes-studio';
// Relative assets work in desktop mode, GitHub Pages project pages, and Discord
// Activity URL mappings where the app may be served through Discord's proxy.
const base = process.env.SNES_STUDIO_ABSOLUTE_BASE
  ? (process.env.GITHUB_ACTIONS ? `/${repoName}/` : '/')
  : './';
export default defineConfig({
  plugins: [react()],
  base,
  server: { port: 5173, proxy: { '/api': 'http://127.0.0.1:8765' } }
});
