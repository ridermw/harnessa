const express = require('express');
const http = require('http');
const cors = require('cors');
const path = require('path');
const { getDb } = require('./db');
const { setupWebSocket } = require('./websocket');
const reviewsRouter = require('./routes/reviews');
const analyticsRouter = require('./routes/analytics');
const healthRouter = require('./routes/health');

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json({ limit: '1mb' }));

// API routes
app.use('/api/health', healthRouter);
app.use('/api/reviews', reviewsRouter);
app.use('/api/analytics', analyticsRouter);

// Serve built client in production
const clientDist = path.join(__dirname, '..', 'client', 'dist');
app.use(express.static(clientDist));
app.get('*', (req, res) => {
  if (!req.path.startsWith('/api') && !req.path.startsWith('/socket.io')) {
    res.sendFile(path.join(clientDist, 'index.html'));
  }
});

async function start() {
  await getDb();
  const io = setupWebSocket(server);
  app.set('io', io);

  server.listen(PORT, () => {
    console.log(`🚀 Harnessa Showcase server running on http://localhost:${PORT}`);
  });
}

start().catch((err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});

module.exports = { app, server };
