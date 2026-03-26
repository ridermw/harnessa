const express = require('express');
const { requireAuth, requireAdmin } = require('../middleware/auth');
const { generateToken, hashPassword, comparePassword } = require('../auth');
const { getDb } = require('../db');
const { ValidationError, NotFoundError } = require('../middleware/errorHandler');

const router = express.Router();

// ─── Helper ──────────────────────────────────────────────────────────────────

function sanitizeUser(user) {
  if (!user) return null;
  const { password_hash, ...safe } = user;
  return safe;
}

// ─── Auth Routes ─────────────────────────────────────────────────────────────

/**
 * POST /api/auth/login
 * Authenticate a user and return a JWT token.
 */
router.post('/auth/login', async (req, res, next) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      throw new ValidationError('Email and password are required.');
    }

    const db = getDb();
    const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email);

    if (!user) {
      return res.status(401).json({ error: 'Invalid email or password.' });
    }

    const isValid = await comparePassword(password, user.password_hash);
    if (!isValid) {
      return res.status(401).json({ error: 'Invalid email or password.' });
    }

    // Update last_login
    db.prepare('UPDATE users SET last_login = datetime(\'now\') WHERE id = ?').run(user.id);

    const token = generateToken(user);

    res.json({
      token,
      user: sanitizeUser(user),
    });
  } catch (err) {
    next(err);
  }
});

/**
 * POST /api/auth/register
 * Create a new user account and return a JWT token.
 */
router.post('/auth/register', async (req, res, next) => {
  try {
    const { username, email, password } = req.body;

    if (!username || !email || !password) {
      throw new ValidationError('Username, email, and password are required.');
    }

    if (username.length < 3) {
      throw new ValidationError('Username must be at least 3 characters.');
    }

    if (password.length < 6) {
      throw new ValidationError('Password must be at least 6 characters.');
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      throw new ValidationError('Invalid email format.');
    }

    const db = getDb();

    // Check for existing user
    const existing = db.prepare('SELECT id FROM users WHERE email = ? OR username = ?').get(email, username);
    if (existing) {
      return res.status(409).json({ error: 'A user with that email or username already exists.' });
    }

    const password_hash = await hashPassword(password);

    const result = db.prepare(`
      INSERT INTO users (username, email, password_hash, role, created_at)
      VALUES (?, ?, ?, 'user', datetime('now'))
    `).run(username, email, password_hash);

    const newUser = db.prepare('SELECT * FROM users WHERE id = ?').get(result.lastInsertRowid);
    const token = generateToken(newUser);

    res.status(201).json({
      token,
      user: sanitizeUser(newUser),
    });
  } catch (err) {
    next(err);
  }
});

// ─── User Routes ─────────────────────────────────────────────────────────────

/**
 * GET /api/users/me/profile
 * Get the current authenticated user's profile.
 * Must be defined before the :id route to avoid conflict.
 */
router.get('/users/me/profile', requireAuth, (req, res, next) => {
  try {
    const db = getDb();
    const user = db.prepare('SELECT * FROM users WHERE id = ?').get(req.user.id);

    if (!user) {
      throw new NotFoundError('User not found.');
    }

    res.json({ user: sanitizeUser(user) });
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/users
 * List all users. Requires admin role.
 */
router.get('/users', requireAuth, requireAdmin, (req, res, next) => {
  try {
    const db = getDb();

    const page = Math.max(1, parseInt(req.query.page, 10) || 1);
    const limit = Math.min(100, Math.max(1, parseInt(req.query.limit, 10) || 20));
    const offset = (page - 1) * limit;

    const search = req.query.search || '';

    let users;
    let total;

    if (search) {
      const pattern = `%${search}%`;
      users = db
        .prepare(
          `SELECT * FROM users
           WHERE username LIKE ? OR email LIKE ?
           ORDER BY created_at DESC
           LIMIT ? OFFSET ?`
        )
        .all(pattern, pattern, limit, offset);

      total = db
        .prepare(
          `SELECT COUNT(*) as count FROM users
           WHERE username LIKE ? OR email LIKE ?`
        )
        .get(pattern, pattern).count;
    } else {
      users = db
        .prepare('SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?')
        .all(limit, offset);

      total = db.prepare('SELECT COUNT(*) as count FROM users').get().count;
    }

    res.json({
      users: users.map(sanitizeUser),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    });
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/users/:id
 * Get a single user by ID. Users can view their own profile; admins can view any.
 */
router.get('/users/:id', requireAuth, (req, res, next) => {
  try {
    const userId = parseInt(req.params.id, 10);

    if (isNaN(userId)) {
      throw new ValidationError('Invalid user ID.');
    }

    // Non-admins can only view their own profile
    if (req.user.role !== 'admin' && req.user.id !== userId) {
      return res.status(403).json({ error: 'Access denied. You can only view your own profile.' });
    }

    const db = getDb();
    const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);

    if (!user) {
      throw new NotFoundError('User not found.');
    }

    res.json({ user: sanitizeUser(user) });
  } catch (err) {
    next(err);
  }
});

/**
 * PUT /api/users/:id
 * Update a user's profile. Users can update their own; admins can update any.
 */
router.put('/users/:id', requireAuth, async (req, res, next) => {
  try {
    const userId = parseInt(req.params.id, 10);

    if (isNaN(userId)) {
      throw new ValidationError('Invalid user ID.');
    }

    if (req.user.role !== 'admin' && req.user.id !== userId) {
      return res.status(403).json({ error: 'Access denied. You can only update your own profile.' });
    }

    const db = getDb();
    const existingUser = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);

    if (!existingUser) {
      throw new NotFoundError('User not found.');
    }

    const { username, email, password, role } = req.body;
    const updates = [];
    const params = [];

    if (username !== undefined) {
      if (username.length < 3) {
        throw new ValidationError('Username must be at least 3 characters.');
      }
      updates.push('username = ?');
      params.push(username);
    }

    if (email !== undefined) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        throw new ValidationError('Invalid email format.');
      }
      updates.push('email = ?');
      params.push(email);
    }

    if (password !== undefined) {
      if (password.length < 6) {
        throw new ValidationError('Password must be at least 6 characters.');
      }
      const password_hash = await hashPassword(password);
      updates.push('password_hash = ?');
      params.push(password_hash);
    }

    // Only admins can change roles
    if (role !== undefined && req.user.role === 'admin') {
      if (!['admin', 'user'].includes(role)) {
        throw new ValidationError('Role must be "admin" or "user".');
      }
      updates.push('role = ?');
      params.push(role);
    }

    if (updates.length === 0) {
      throw new ValidationError('No valid fields to update.');
    }

    params.push(userId);
    db.prepare(`UPDATE users SET ${updates.join(', ')} WHERE id = ?`).run(...params);

    const updatedUser = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);

    res.json({ user: sanitizeUser(updatedUser) });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
