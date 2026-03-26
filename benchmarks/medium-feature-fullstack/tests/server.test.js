const request = require('supertest');
const path = require('path');
const fs = require('fs');

// Use a separate test database
const TEST_DB_PATH = path.join(__dirname, '..', 'server', 'test_dashboard.db');
process.env.DB_PATH = TEST_DB_PATH;
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-secret-key';

// Clean up any leftover test database
if (fs.existsSync(TEST_DB_PATH)) {
  fs.unlinkSync(TEST_DB_PATH);
}

const { app } = require('../server/index');
const { generateToken } = require('../server/auth');
const { getDb, closeDb } = require('../server/db');

let adminToken;
let userToken;

beforeAll(() => {
  // Generate tokens for test users from the seeded data
  const db = getDb();
  const admin = db.prepare('SELECT * FROM users WHERE role = ?').get('admin');
  const regularUser = db.prepare('SELECT * FROM users WHERE role = ?').get('user');

  adminToken = generateToken(admin);
  userToken = generateToken(regularUser);
});

afterAll(() => {
  closeDb();
  // Clean up test database
  if (fs.existsSync(TEST_DB_PATH)) {
    fs.unlinkSync(TEST_DB_PATH);
  }
});

// ─── 1. Health endpoint ──────────────────────────────────────────────────────

describe('Health', () => {
  test('GET /api/health returns 200 with status ok', async () => {
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('status', 'ok');
    expect(res.body).toHaveProperty('timestamp');
  });
});

// ─── 2-3. Login ──────────────────────────────────────────────────────────────

describe('Auth - Login', () => {
  test('POST /api/auth/login with valid credentials returns token', async () => {
    const res = await request(app)
      .post('/api/auth/login')
      .send({ email: 'admin@example.com', password: 'password123' });

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('token');
    expect(typeof res.body.token).toBe('string');
    expect(res.body).toHaveProperty('user');
    expect(res.body.user).toHaveProperty('username', 'admin');
    expect(res.body.user).not.toHaveProperty('password_hash');
  });

  test('POST /api/auth/login with invalid credentials returns 401', async () => {
    const res = await request(app)
      .post('/api/auth/login')
      .send({ email: 'admin@example.com', password: 'wrongpassword' });

    expect(res.status).toBe(401);
    expect(res.body).toHaveProperty('error');
  });
});

// ─── 4. Register ─────────────────────────────────────────────────────────────

describe('Auth - Register', () => {
  test('POST /api/auth/register creates new user and returns token', async () => {
    const newUser = {
      username: 'newuser',
      email: 'newuser@example.com',
      password: 'securepass123',
    };

    const res = await request(app)
      .post('/api/auth/register')
      .send(newUser);

    expect(res.status).toBe(201);
    expect(res.body).toHaveProperty('token');
    expect(typeof res.body.token).toBe('string');
    expect(res.body).toHaveProperty('user');
    expect(res.body.user).toHaveProperty('username', 'newuser');
    expect(res.body.user).toHaveProperty('email', 'newuser@example.com');
    expect(res.body.user).toHaveProperty('role', 'user');
    expect(res.body.user).not.toHaveProperty('password_hash');
  });
});

// ─── 5-6. Dashboard stats ────────────────────────────────────────────────────

describe('Dashboard', () => {
  test('GET /api/dashboard with valid token returns stats', async () => {
    const res = await request(app)
      .get('/api/dashboard')
      .set('Authorization', `Bearer ${adminToken}`);

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('stats');
    expect(res.body.stats).toHaveProperty('total_users');
    expect(res.body.stats).toHaveProperty('active_sessions');
    expect(res.body.stats).toHaveProperty('total_orders');
    expect(res.body.stats).toHaveProperty('revenue');
    expect(res.body.stats.total_users).toHaveProperty('value');
    expect(typeof res.body.stats.total_users.value).toBe('number');
  });

  test('GET /api/dashboard without token returns 401', async () => {
    const res = await request(app).get('/api/dashboard');
    expect(res.status).toBe(401);
    expect(res.body).toHaveProperty('error');
  });
});

// ─── 7-8. Users list ─────────────────────────────────────────────────────────

describe('Users', () => {
  test('GET /api/users as admin returns users array', async () => {
    const res = await request(app)
      .get('/api/users')
      .set('Authorization', `Bearer ${adminToken}`);

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('users');
    expect(Array.isArray(res.body.users)).toBe(true);
    expect(res.body.users.length).toBeGreaterThanOrEqual(5);
    expect(res.body).toHaveProperty('total');
    expect(res.body).toHaveProperty('page');
    expect(res.body).toHaveProperty('totalPages');

    // Ensure no password hashes are leaked
    for (const u of res.body.users) {
      expect(u).not.toHaveProperty('password_hash');
    }
  });

  test('GET /api/users as regular user returns 403', async () => {
    const res = await request(app)
      .get('/api/users')
      .set('Authorization', `Bearer ${userToken}`);

    expect(res.status).toBe(403);
    expect(res.body).toHaveProperty('error');
  });
});

// ─── 9. User profile ─────────────────────────────────────────────────────────

describe('User Profile', () => {
  test('GET /api/users/me/profile returns current user data', async () => {
    const res = await request(app)
      .get('/api/users/me/profile')
      .set('Authorization', `Bearer ${adminToken}`);

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('user');
    expect(res.body.user).toHaveProperty('id');
    expect(res.body.user).toHaveProperty('username', 'admin');
    expect(res.body.user).toHaveProperty('email', 'admin@example.com');
    expect(res.body.user).toHaveProperty('role', 'admin');
    expect(res.body.user).not.toHaveProperty('password_hash');
  });
});

// ─── 10. Dashboard activity ──────────────────────────────────────────────────

describe('Dashboard Activity', () => {
  test('GET /api/dashboard/activity returns activity array', async () => {
    const res = await request(app)
      .get('/api/dashboard/activity')
      .set('Authorization', `Bearer ${adminToken}`);

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('activities');
    expect(Array.isArray(res.body.activities)).toBe(true);
    expect(res.body.activities.length).toBeGreaterThan(0);
    expect(res.body).toHaveProperty('total');

    const activity = res.body.activities[0];
    expect(activity).toHaveProperty('id');
    expect(activity).toHaveProperty('type');
    expect(activity).toHaveProperty('message');
    expect(activity).toHaveProperty('timestamp');
  });
});
