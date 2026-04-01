import { readFileSync, existsSync } from 'fs';
import { execSync } from 'child_process';
import { resolve } from 'path';
import { describe, it, expect, beforeAll } from 'vitest';

const distDir = resolve(__dirname, '..', 'dist');
const indexPath = resolve(distDir, 'index.html');

describe('GitHub Pages build', () => {
  beforeAll(() => {
    execSync('npm run build', {
      cwd: resolve(__dirname, '..'),
      env: { ...process.env, GITHUB_ACTIONS: 'true', GITHUB_REPOSITORY: 'owner/harnessa' },
      stdio: 'pipe',
    });
  });

  it('produces dist/index.html', () => {
    expect(existsSync(indexPath)).toBe(true);
  });

  it('uses /harnessa/ base path for asset references', () => {
    const html = readFileSync(indexPath, 'utf-8');

    // Script tags should use /harnessa/ prefix
    const scriptSrcs = [...html.matchAll(/src="([^"]+)"/g)].map((m) => m[1]);
    for (const src of scriptSrcs) {
      if (src.startsWith('http')) continue;
      expect(src, `script src="${src}" missing base path`).toMatch(/^\/harnessa\//);
    }

    // CSS link tags should use /harnessa/ prefix
    const linkHrefs = [...html.matchAll(/href="([^"]+\.css[^"]*)"/g)].map((m) => m[1]);
    for (const href of linkHrefs) {
      if (href.startsWith('http')) continue;
      expect(href, `link href="${href}" missing base path`).toMatch(/^\/harnessa\//);
    }
  });
});
