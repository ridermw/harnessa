import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const repoName = process.env.GITHUB_REPOSITORY?.split('/')[1] ?? 'harnessa';

export default defineConfig({
  base: process.env.GITHUB_ACTIONS ? `/${repoName}/` : '/',
  plugins: [react()],
  server: {
    port: 4173,
    host: '0.0.0.0',
  },
});
