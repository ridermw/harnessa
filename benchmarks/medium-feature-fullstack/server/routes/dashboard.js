const express = require('express');
const { requireAuth } = require('../middleware/auth');
const { getDb } = require('../db');

const router = express.Router();

/**
 * GET /api/dashboard
 * Returns all dashboard statistics from the database.
 * Requires authentication.
 */
router.get('/', requireAuth, (req, res) => {
  const db = getDb();

  const stats = db.prepare('SELECT metric_name, metric_value, updated_at FROM dashboard_stats').all();

  const statsMap = {};
  for (const stat of stats) {
    statsMap[stat.metric_name] = {
      value: stat.metric_value,
      updated_at: stat.updated_at,
    };
  }

  res.json({
    stats: statsMap,
    fetched_at: new Date().toISOString(),
  });
});

/**
 * GET /api/dashboard/activity
 * Returns recent activity feed for the dashboard.
 * Requires authentication.
 */
router.get('/activity', requireAuth, (req, res) => {
  // In a real app this would come from an activity log table.
  // For now, return realistic mock data.
  const activities = [
    {
      id: 1,
      type: 'user_registered',
      message: 'New user klee registered',
      user: 'klee',
      timestamp: '2024-01-15T08:30:00.000Z',
    },
    {
      id: 2,
      type: 'order_placed',
      message: 'Order #5621 placed by jsmith',
      user: 'jsmith',
      timestamp: '2024-01-15T07:45:00.000Z',
    },
    {
      id: 3,
      type: 'payment_received',
      message: 'Payment of $249.99 received for Order #5620',
      user: 'jdoe',
      timestamp: '2024-01-15T06:20:00.000Z',
    },
    {
      id: 4,
      type: 'user_login',
      message: 'Admin user logged in',
      user: 'admin',
      timestamp: '2024-01-15T06:00:00.000Z',
    },
    {
      id: 5,
      type: 'settings_updated',
      message: 'Dashboard theme settings updated',
      user: 'admin',
      timestamp: '2024-01-14T22:10:00.000Z',
    },
    {
      id: 6,
      type: 'order_shipped',
      message: 'Order #5619 has been shipped',
      user: 'system',
      timestamp: '2024-01-14T18:30:00.000Z',
    },
    {
      id: 7,
      type: 'user_updated',
      message: 'User mwilson updated their profile',
      user: 'mwilson',
      timestamp: '2024-01-14T15:45:00.000Z',
    },
    {
      id: 8,
      type: 'order_placed',
      message: 'Order #5618 placed by mwilson',
      user: 'mwilson',
      timestamp: '2024-01-14T14:20:00.000Z',
    },
    {
      id: 9,
      type: 'report_generated',
      message: 'Weekly sales report generated',
      user: 'system',
      timestamp: '2024-01-14T12:00:00.000Z',
    },
    {
      id: 10,
      type: 'user_registered',
      message: 'New user mwilson registered',
      user: 'mwilson',
      timestamp: '2024-01-14T09:30:00.000Z',
    },
  ];

  const limit = parseInt(req.query.limit, 10) || 10;
  const offset = parseInt(req.query.offset, 10) || 0;

  const paged = activities.slice(offset, offset + limit);

  res.json({
    activities: paged,
    total: activities.length,
    limit,
    offset,
  });
});

module.exports = router;
