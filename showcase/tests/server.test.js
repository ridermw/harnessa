const { describe, it, before, after } = require('node:test');
const assert = require('node:assert');
const http = require('http');

const BASE_URL = 'http://localhost:3001';

function request(method, path, body) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE_URL);
    const options = {
      method,
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      headers: { 'Content-Type': 'application/json' },
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

describe('Harnessa Showcase API', () => {
  it('GET /api/health returns ok', async () => {
    const res = await request('GET', '/api/health');
    assert.strictEqual(res.status, 200);
    assert.strictEqual(res.body.status, 'ok');
    assert.strictEqual(res.body.service, 'harnessa-showcase');
  });

  it('GET /api/reviews returns empty list initially', async () => {
    const res = await request('GET', '/api/reviews');
    assert.strictEqual(res.status, 200);
    assert.ok(Array.isArray(res.body.reviews));
    assert.ok(res.body.pagination);
  });

  it('POST /api/reviews validates input', async () => {
    const res = await request('POST', '/api/reviews', { code: '', language: 'js' });
    assert.strictEqual(res.status, 400);
  });

  it('POST /api/reviews starts analysis', async () => {
    const res = await request('POST', '/api/reviews', {
      code: 'function foo() { console.log(x); }',
      language: 'javascript',
    });
    assert.strictEqual(res.status, 201);
    assert.ok(res.body.id);
    assert.strictEqual(res.body.status, 'analyzing');
  });

  it('Review completes after waiting', async () => {
    const post = await request('POST', '/api/reviews', {
      code: `function bar() {
  const secret = "password123";
  console.log("debug");
  // TODO: fix this
  async function inner() {
    await fetch("/api");
  }
}`,
      language: 'javascript',
    });
    assert.strictEqual(post.status, 201);

    // Wait for trio analysis to complete
    await sleep(10000);

    const get = await request('GET', `/api/reviews/${post.body.id}`);
    assert.strictEqual(get.status, 200);
    assert.strictEqual(get.body.status, 'completed');
    assert.ok(get.body.scores);
    assert.ok(get.body.bugs);
    assert.ok(get.body.verdict);
    assert.ok(get.body.overall_score > 0);
    assert.ok(get.body.bugs.length > 0, 'Should find bugs in problematic code');
  });

  it('GET /api/analytics returns stats', async () => {
    const res = await request('GET', '/api/analytics');
    assert.strictEqual(res.status, 200);
    assert.ok(typeof res.body.totalReviews === 'number');
    assert.ok(typeof res.body.averageScore === 'number');
    assert.ok(typeof res.body.passRate === 'number');
  });

  it('GET /api/reviews/:id returns 404 for missing', async () => {
    const res = await request('GET', '/api/reviews/nonexistent-id');
    assert.strictEqual(res.status, 404);
  });
});
