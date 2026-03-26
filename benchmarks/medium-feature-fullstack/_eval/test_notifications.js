/**
 * Acceptance tests for the real-time notifications feature.
 *
 * These tests verify that the notifications system has been correctly
 * implemented on top of the existing dashboard application:
 *   - REST API endpoints for CRUD operations on notifications
 *   - WebSocket server for real-time delivery
 *   - Proper authentication and per-user scoping
 *
 * The feature under test does NOT exist in the base codebase.
 * All 8 tests are expected to fail until the feature is implemented.
 */

const request = require('supertest');
const path = require('path');
const fs = require('fs');
const WebSocket = require('ws');

// Use a dedicated test database so we don't pollute dev data
const TEST_DB_PATH = path.join(__dirname, '..', 'server', 'eval_test_dashboard.db');
process.env.DB_PATH = TEST_DB_PATH;
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'eval-test-secret';

// Clean up any leftover test database
if (fs.existsSync(TEST_DB_PATH)) {
  fs.unlinkSync(TEST_DB_PATH);
}

const { app } = require('../server/index');
const { generateToken } = require('../server/auth');
const { getDb, closeDb } = require('../server/db');

const PORT = 3099;
let server;
let adminToken;
let userToken;
let adminUser;
let regularUser;

beforeAll((done) => {
  const db = getDb();
  adminUser = db.prepare('SELECT * FROM users WHERE role = ?').get('admin');
  regularUser = db.prepare('SELECT * FROM users WHERE role = ?').get('user');

  adminToken = generateToken(adminUser);
  userToken = generateToken(regularUser);

  server = app.listen(PORT, done);
});

afterAll((done) => {
  closeDb();
  if (fs.existsSync(TEST_DB_PATH)) {
    fs.unlinkSync(TEST_DB_PATH);
  }
  if (server) {
    server.close(done);
  } else {
    done();
  }
});

// ─── Helpers ─────────────────────────────────────────────────────────────────

function connectWebSocket(token) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(`ws://localhost:${PORT}/ws?token=${token}`);
    ws.on('open', () => resolve(ws));
    ws.on('error', (err) => reject(err));
    setTimeout(() => reject(new Error('WebSocket connection timeout')), 5000);
  });
}

function waitForMessage(ws, timeoutMs = 5000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('WebSocket message timeout')), timeoutMs);
    ws.once('message', (data) => {
      clearTimeout(timer);
      resolve(JSON.parse(data.toString()));
    });
  });
}

// ─── 1. WebSocket Connection ─────────────────────────────────────────────────

describe('Notifications - WebSocket', () => {
  test('WebSocket connects with valid auth token', async () => {
    const ws = await connectWebSocket(adminToken);
    expect(ws.readyState).toBe(WebSocket.OPEN);
    ws.close();
  });
});

// ─── 2. Create Notification ──────────────────────────────────────────────────

describe('Notifications - CRUD', () => {
  test('POST /api/notifications creates a notification', async () => {
    const payload = {
      title: 'New Order',
      message: 'Order #1234 has been placed',
      type: 'info',
      user_id: regularUser.id,
    };

    const res = await request(app)
      .post('/api/notifications')
      .set('Authorization', `Bearer ${adminToken}`)
      .send(payload);

    expect(res.status).toBe(201);
    expect(res.body).toHaveProperty('id');
    expect(res.body).toHaveProperty('title', 'New Order');
    expect(res.body).toHaveProperty('message', 'Order #1234 has been placed');
    expect(res.body).toHaveProperty('type', 'info');
    expect(res.body).toHaveProperty('read', false);
    expect(res.body).toHaveProperty('created_at');
  });

  // ─── 3. List Notifications ───────────────────────────────────────────────

  test('GET /api/notifications returns user notifications', async () => {
    // Create a couple of notifications for the regular user
    await request(app)
      .post('/api/notifications')
      .set('Authorization', `Bearer ${adminToken}`)
      .send({
        title: 'Test Notification 1',
        message: 'First test message',
        type: 'info',
        user_id: regularUser.id,
      });

    await request(app)
      .post('/api/notifications')
      .set('Authorization', `Bearer ${adminToken}`)
      .send({
        title: 'Test Notification 2',
        message: 'Second test message',
        type: 'success',
        user_id: regularUser.id,
      });

    const res = await request(app)
      .get('/api/notifications')
      .set('Authorization', `Bearer ${userToken}`);

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('notifications');
    expect(Array.isArray(res.body.notifications)).toBe(true);
    expect(res.body.notifications.length).toBeGreaterThanOrEqual(2);
    expect(res.body).toHaveProperty('total');

    const notification = res.body.notifications[0];
    expect(notification).toHaveProperty('id');
    expect(notification).toHaveProperty('title');
    expect(notification).toHaveProperty('message');
    expect(notification).toHaveProperty('type');
    expect(notification).toHaveProperty('read');
    expect(notification).toHaveProperty('created_at');
  });

  // ─── 4. Real-time Notification via WebSocket ─────────────────────────────

  test('Creating a notification delivers it via WebSocket', async () => {
    const ws = await connectWebSocket(userToken);

    // Give the connection a moment to stabilize
    await new Promise((r) => setTimeout(r, 200));

    const messagePromise = waitForMessage(ws);

    await request(app)
      .post('/api/notifications')
      .set('Authorization', `Bearer ${adminToken}`)
      .send({
        title: 'Real-time Test',
        message: 'This should arrive via WebSocket',
        type: 'warning',
        user_id: regularUser.id,
      });

    const wsMessage = await messagePromise;

    expect(wsMessage).toHaveProperty('type', 'notification');
    expect(wsMessage).toHaveProperty('data');
    expect(wsMessage.data).toHaveProperty('title', 'Real-time Test');

    ws.close();
  });

  // ─── 5. Mark Notification as Read ────────────────────────────────────────

  test('PATCH /api/notifications/:id marks notification as read', async () => {
    // Create a notification
    const createRes = await request(app)
      .post('/api/notifications')
      .set('Authorization', `Bearer ${adminToken}`)
      .send({
        title: 'To Be Read',
        message: 'This will be marked as read',
        type: 'info',
        user_id: regularUser.id,
      });

    const notificationId = createRes.body.id;

    const res = await request(app)
      .patch(`/api/notifications/${notificationId}`)
      .set('Authorization', `Bearer ${userToken}`)
      .send({ read: true });

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('id', notificationId);
    expect(res.body).toHaveProperty('read', true);
  });

  // ─── 6. Unread Count ────────────────────────────────────────────────────

  test('GET /api/notifications/unread-count returns correct count', async () => {
    const res = await request(app)
      .get('/api/notifications/unread-count')
      .set('Authorization', `Bearer ${userToken}`);

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('count');
    expect(typeof res.body.count).toBe('number');
    expect(res.body.count).toBeGreaterThanOrEqual(0);
  });
});

// ─── 7-8. Data contract tests (stand-in for React component tests) ──────────

describe('Notifications - Data Contracts', () => {
  /**
   * Test 7: Verifies the unread-count endpoint returns the proper shape
   * that a NotificationBell component would consume.
   * (Stand-in for a React component test: "NotificationBell renders with badge count")
   */
  test('Unread-count endpoint returns shape suitable for NotificationBell', async () => {
    const res = await request(app)
      .get('/api/notifications/unread-count')
      .set('Authorization', `Bearer ${userToken}`);

    expect(res.status).toBe(200);
    expect(res.body).toEqual(
      expect.objectContaining({
        count: expect.any(Number),
      })
    );
    // The count should be a non-negative integer
    expect(Number.isInteger(res.body.count)).toBe(true);
    expect(res.body.count).toBeGreaterThanOrEqual(0);
  });

  /**
   * Test 8: Verifies the notification list endpoint returns the proper shape
   * that a NotificationDropdown component would consume.
   * (Stand-in for a React component test: "NotificationDropdown shows notification list")
   */
  test('Notification list returns shape suitable for NotificationDropdown', async () => {
    const res = await request(app)
      .get('/api/notifications')
      .set('Authorization', `Bearer ${userToken}`);

    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('notifications');
    expect(res.body).toHaveProperty('total');
    expect(Array.isArray(res.body.notifications)).toBe(true);

    if (res.body.notifications.length > 0) {
      const item = res.body.notifications[0];
      // Every field the dropdown component would need
      expect(item).toEqual(
        expect.objectContaining({
          id: expect.any(Number),
          title: expect.any(String),
          message: expect.any(String),
          type: expect.any(String),
          read: expect.any(Boolean),
          created_at: expect.any(String),
        })
      );
      // Type should be one of the valid notification types
      expect(['info', 'success', 'warning', 'error']).toContain(item.type);
    }
  });
});
