const initSqlJs = require('sql.js');
const path = require('path');

let db = null;

async function getDb() {
  if (db) return db;

  const SQL = await initSqlJs();
  db = new SQL.Database();

  db.run(`
    CREATE TABLE IF NOT EXISTS reviews (
      id TEXT PRIMARY KEY,
      code TEXT NOT NULL,
      language TEXT NOT NULL DEFAULT 'javascript',
      status TEXT NOT NULL DEFAULT 'pending',
      scores TEXT,
      bugs TEXT,
      planner_output TEXT,
      generator_output TEXT,
      evaluator_output TEXT,
      verdict TEXT,
      overall_score REAL,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS activity_log (
      id TEXT PRIMARY KEY,
      type TEXT NOT NULL,
      description TEXT NOT NULL,
      review_id TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
  `);

  db.run(`CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews(status)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON reviews(created_at)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON activity_log(created_at)`);

  return db;
}

function queryAll(db, sql, params = []) {
  const stmt = db.prepare(sql);
  if (params.length) stmt.bind(params);
  const results = [];
  while (stmt.step()) {
    results.push(stmt.getAsObject());
  }
  stmt.free();
  return results;
}

function queryOne(db, sql, params = []) {
  const results = queryAll(db, sql, params);
  return results[0] || null;
}

function run(db, sql, params = []) {
  db.run(sql, params);
}

module.exports = { getDb, queryAll, queryOne, run };
