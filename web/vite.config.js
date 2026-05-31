import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
const repoName = process.env.GITHUB_REPOSITORY?.split('/')[1] || 'snes-studio';
// The desktop/installer build is served from the app's own root (http://127.0.0.1:<port>/),
// so it must use base '/'. Only the GitHub Pages deploy needs the /<repo>/ subpath.
// SNES_STUDIO_DESKTOP=1 forces base '/' even when building inside GitHub Actions.
const isPagesDeploy = process.env.GITHUB_ACTIONS && !process.env.SNES_STUDIO_DESKTOP;
export default defineConfig({
  plugins: [react()],
  base: isPagesDeploy ? `/${repoName}/` : '/',
  server: { port: 5173, proxy: { '/api': 'http://127.0.0.1:8765' } }
});
