import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 120000,
  expect: { timeout: 20000 },
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
  },
  webServer: [
    {
      command: 'powershell -NoProfile -ExecutionPolicy Bypass -Command "New-Item -ItemType Directory -Force tmp-e2e | Out-Null; Copy-Item examples/hello-human/project.snesproj tmp-e2e/project.snesproj -Force; python -m snesstudio.cli serve tmp-e2e/project.snesproj --host 127.0.0.1 --port 8765"',
      url: 'http://127.0.0.1:8765/api/health',
      reuseExistingServer: false,
      cwd: '..',
      timeout: 120000,
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5173',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: false,
      timeout: 120000,
    },
  ],
});
