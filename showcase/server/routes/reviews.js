const express = require('express');
const { v4: uuidv4 } = require('uuid');
const { getDb, queryAll, queryOne, run } = require('../db');
const { analyzeCode } = require('../services/trio');
const { broadcast } = require('../websocket');

const router = express.Router();

// POST /api/reviews — submit code for trio analysis
router.post('/', async (req, res) => {
  try {
    const { code, language = 'javascript' } = req.body;

    if (!code || typeof code !== 'string' || code.trim().length === 0) {
      return res.status(400).json({ error: 'Code is required' });
    }

    const db = await getDb();
    const id = uuidv4();
    const createdAt = new Date().toISOString();

    run(db, `INSERT INTO reviews (id, code, language, status, created_at) VALUES (?, ?, ?, 'analyzing', ?)`, [
      id,
      code,
      language,
      createdAt,
    ]);

    // Log activity
    run(db, `INSERT INTO activity_log (id, type, description, review_id, created_at) VALUES (?, ?, ?, ?, ?)`, [
      uuidv4(),
      'review_started',
      `Review #${id.substring(0, 8)} started for ${language} code`,
      id,
      createdAt,
    ]);

    broadcast('activity', {
      type: 'review_started',
      reviewId: id,
      description: `Review #${id.substring(0, 8)} started`,
      timestamp: createdAt,
    });

    res.status(201).json({ id, status: 'analyzing', createdAt });

    // Run trio analysis in background
    runAnalysis(id, code, language).catch((err) => {
      console.error(`Analysis failed for review ${id}:`, err);
    });
  } catch (err) {
    console.error('POST /api/reviews error:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

async function runAnalysis(id, code, language) {
  const db = await getDb();

  try {
    const result = await analyzeCode(code, language, (phase, status, output) => {
      const actId = uuidv4();
      const now = new Date().toISOString();

      if (status === 'running') {
        broadcast('trio_phase', { reviewId: id, phase, status: 'running' });
        run(db, `INSERT INTO activity_log (id, type, description, review_id, created_at) VALUES (?, ?, ?, ?, ?)`, [
          actId,
          'phase_started',
          `${phase.charAt(0).toUpperCase() + phase.slice(1)} started for #${id.substring(0, 8)}`,
          id,
          now,
        ]);
      } else if (status === 'done') {
        broadcast('trio_phase', { reviewId: id, phase, status: 'done', output });
        run(db, `INSERT INTO activity_log (id, type, description, review_id, created_at) VALUES (?, ?, ?, ?, ?)`, [
          actId,
          'phase_completed',
          `${phase.charAt(0).toUpperCase() + phase.slice(1)} complete for #${id.substring(0, 8)}`,
          id,
          now,
        ]);
        broadcast('activity', {
          type: 'phase_completed',
          reviewId: id,
          phase,
          description: `${phase.charAt(0).toUpperCase() + phase.slice(1)} complete for #${id.substring(0, 8)}`,
          timestamp: now,
        });
      }
    });

    run(
      db,
      `UPDATE reviews SET status = 'completed', scores = ?, bugs = ?, planner_output = ?, generator_output = ?, evaluator_output = ?, verdict = ?, overall_score = ? WHERE id = ?`,
      [
        JSON.stringify(result.scores),
        JSON.stringify(result.bugs),
        JSON.stringify(result.plannerOutput),
        JSON.stringify(result.generatorOutput),
        JSON.stringify(result.evaluatorOutput),
        result.verdict,
        result.overall,
        id,
      ]
    );

    const now = new Date().toISOString();
    run(db, `INSERT INTO activity_log (id, type, description, review_id, created_at) VALUES (?, ?, ?, ?, ?)`, [
      uuidv4(),
      'review_completed',
      `Review #${id.substring(0, 8)}: ${result.verdict} (${result.overall}/10)`,
      id,
      now,
    ]);

    broadcast('activity', {
      type: 'review_completed',
      reviewId: id,
      verdict: result.verdict,
      score: result.overall,
      description: `Review #${id.substring(0, 8)}: ${result.verdict} (${result.overall}/10)`,
      timestamp: now,
    });

    broadcast('review_complete', { reviewId: id, ...result });
  } catch (err) {
    run(db, `UPDATE reviews SET status = 'failed' WHERE id = ?`, [id]);
    broadcast('activity', {
      type: 'review_failed',
      reviewId: id,
      description: `Review #${id.substring(0, 8)} failed: ${err.message}`,
      timestamp: new Date().toISOString(),
    });
  }
}

// GET /api/reviews — list all reviews with pagination
router.get('/', async (req, res) => {
  try {
    const db = await getDb();
    const page = Math.max(1, parseInt(req.query.page) || 1);
    const limit = Math.min(100, Math.max(1, parseInt(req.query.limit) || 20));
    const offset = (page - 1) * limit;

    const reviews = queryAll(db, `SELECT * FROM reviews ORDER BY created_at DESC LIMIT ? OFFSET ?`, [limit, offset]);
    const countRow = queryOne(db, `SELECT COUNT(*) as total FROM reviews`);

    const parsed = reviews.map((r) => ({
      ...r,
      scores: r.scores ? JSON.parse(r.scores) : null,
      bugs: r.bugs ? JSON.parse(r.bugs) : null,
    }));

    res.json({
      reviews: parsed,
      pagination: {
        page,
        limit,
        total: countRow?.total || 0,
        totalPages: Math.ceil((countRow?.total || 0) / limit),
      },
    });
  } catch (err) {
    console.error('GET /api/reviews error:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/reviews/:id — single review with full detail
router.get('/:id', async (req, res) => {
  try {
    const db = await getDb();
    const review = queryOne(db, `SELECT * FROM reviews WHERE id = ?`, [req.params.id]);

    if (!review) {
      return res.status(404).json({ error: 'Review not found' });
    }

    review.scores = review.scores ? JSON.parse(review.scores) : null;
    review.bugs = review.bugs ? JSON.parse(review.bugs) : null;
    review.planner_output = review.planner_output ? JSON.parse(review.planner_output) : null;
    review.generator_output = review.generator_output ? JSON.parse(review.generator_output) : null;
    review.evaluator_output = review.evaluator_output ? JSON.parse(review.evaluator_output) : null;

    res.json(review);
  } catch (err) {
    console.error('GET /api/reviews/:id error:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
