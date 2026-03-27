const express = require('express');
const { getDb, queryAll, queryOne } = require('../db');

const router = express.Router();

// GET /api/analytics — aggregate stats
router.get('/', async (req, res) => {
  try {
    const db = await getDb();

    const totalRow = queryOne(db, `SELECT COUNT(*) as total FROM reviews`);
    const completedRow = queryOne(db, `SELECT COUNT(*) as total FROM reviews WHERE status = 'completed'`);
    const avgRow = queryOne(db, `SELECT AVG(overall_score) as avg FROM reviews WHERE status = 'completed'`);
    const passRow = queryOne(db, `SELECT COUNT(*) as total FROM reviews WHERE verdict = 'PASS'`);
    const todayRow = queryOne(
      db,
      `SELECT COUNT(*) as total FROM reviews WHERE created_at >= date('now', 'start of day')`
    );

    const byLanguage = queryAll(
      db,
      `SELECT language, COUNT(*) as count, AVG(overall_score) as avgScore FROM reviews WHERE status = 'completed' GROUP BY language ORDER BY count DESC`
    );

    const recentScores = queryAll(
      db,
      `SELECT id, overall_score, language, created_at FROM reviews WHERE status = 'completed' ORDER BY created_at DESC LIMIT 10`
    );

    const recentActivity = queryAll(
      db,
      `SELECT * FROM activity_log ORDER BY created_at DESC LIMIT 20`
    );

    const completed = completedRow?.total || 0;
    const passRate = completed > 0 ? Math.round(((passRow?.total || 0) / completed) * 100) : 0;

    res.json({
      totalReviews: totalRow?.total || 0,
      completedReviews: completed,
      averageScore: avgRow?.avg ? Math.round(avgRow.avg * 10) / 10 : 0,
      passRate,
      reviewsToday: todayRow?.total || 0,
      byLanguage,
      recentScores,
      recentActivity,
    });
  } catch (err) {
    console.error('GET /api/analytics error:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
