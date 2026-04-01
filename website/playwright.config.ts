import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  webServer: {
    command: 'npm run build && npx vite preview --port 4174',
    port: 4174,
    reuseExistingServer: !process.env.CI,
  },
  use: {
    baseURL: 'http://localhost:4174',
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
  ],
});
