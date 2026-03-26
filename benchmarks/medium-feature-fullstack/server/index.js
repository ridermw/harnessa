const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const { initDb, closeDb } = require('./db');
const { errorHandler } = require('./middleware/errorHandler');
const dashboardRoutes = require('./routes/dashboard');
const userRoutes = require('./routes/users');

// Initialize the database (creates tables & seeds data)
initDb();

const app = express();

// ─── Middleware ───────────────────────────────────────────────────────────────

app.use(cors({
  origin: process.env.CLIENT_URL || 'http://localhost:5173',
  credentials: true,
}));
app.use(express.json());

// Only log HTTP requests when not in test mode
if (process.env.NODE_ENV !== 'test') {
  app.use(morgan('dev'));
}

// ─── Routes ──────────────────────────────────────────────────────────────────

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Dashboard routes
app.use('/api/dashboard', dashboardRoutes);

// User & auth routes — userRoutes handles both /api/auth/* and /api/users/*
app.use('/api', userRoutes);

// ─── Error Handler ───────────────────────────────────────────────────────────

app.use(errorHandler);

// ─── Server ──────────────────────────────────────────────────────────────────

const PORT = process.env.PORT || 3001;
let server;

if (process.env.NODE_ENV !== 'test') {
  server = app.listen(PORT, () => {
    console.log(`Dashboard API server running on http://localhost:${PORT}`);
  });
}

// Graceful shutdown
function shutdown() {
  console.log('\nShutting down gracefully...');
  closeDb();
  if (server) {
    server.close(() => {
      console.log('Server closed.');
      process.exit(0);
    });
  } else {
    process.exit(0);
  }
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

module.exports = { app, server };
