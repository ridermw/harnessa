const Database = require('better-sqlite3');
const path = require('path');

const DB_PATH = process.env.DB_PATH || path.join(__dirname, 'dashboard.db');

let db;

function getDb() {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
  }
  return db;
}

// Pre-computed bcryptjs hash for "password123"
const PASSWORD_HASH = '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi';

function initDb() {
  const database = getDb();

  database.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT DEFAULT 'user',
      created_at TEXT DEFAULT (datetime('now')),
      last_login TEXT
    )
  `);

  database.exec(`
    CREATE TABLE IF NOT EXISTS dashboard_stats (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      metric_name TEXT UNIQUE NOT NULL,
      metric_value REAL NOT NULL,
      updated_at TEXT DEFAULT (datetime('now'))
    )
  `);

  // Seed users if table is empty
  const userCount = database.prepare('SELECT COUNT(*) as count FROM users').get();
  if (userCount.count === 0) {
    const insertUser = database.prepare(`
      INSERT INTO users (username, email, password_hash, role, created_at, last_login)
      VALUES (@username, @email, @password_hash, @role, @created_at, @last_login)
    `);

    const seedUsers = [
      {
        username: 'admin',
        email: 'admin@example.com',
        password_hash: PASSWORD_HASH,
        role: 'admin',
        created_at: '2024-01-01T10:00:00.000Z',
        last_login: '2024-01-15T08:30:00.000Z',
      },
      {
        username: 'jsmith',
        email: 'user1@example.com',
        password_hash: PASSWORD_HASH,
        role: 'user',
        created_at: '2024-01-02T11:00:00.000Z',
        last_login: '2024-01-14T09:15:00.000Z',
      },
      {
        username: 'jdoe',
        email: 'user2@example.com',
        password_hash: PASSWORD_HASH,
        role: 'user',
        created_at: '2024-01-03T14:30:00.000Z',
        last_login: '2024-01-13T16:45:00.000Z',
      },
      {
        username: 'mwilson',
        email: 'user3@example.com',
        password_hash: PASSWORD_HASH,
        role: 'user',
        created_at: '2024-01-05T09:00:00.000Z',
        last_login: '2024-01-12T11:20:00.000Z',
      },
      {
        username: 'klee',
        email: 'user4@example.com',
        password_hash: PASSWORD_HASH,
        role: 'user',
        created_at: '2024-01-07T16:00:00.000Z',
        last_login: null,
      },
    ];

    const insertMany = database.transaction((users) => {
      for (const user of users) {
        insertUser.run(user);
      }
    });

    insertMany(seedUsers);
  }

  // Seed dashboard stats if table is empty
  const statsCount = database.prepare('SELECT COUNT(*) as count FROM dashboard_stats').get();
  if (statsCount.count === 0) {
    const insertStat = database.prepare(`
      INSERT INTO dashboard_stats (metric_name, metric_value, updated_at)
      VALUES (@metric_name, @metric_value, @updated_at)
    `);

    const seedStats = [
      {
        metric_name: 'total_users',
        metric_value: 1284,
        updated_at: '2024-01-15T08:00:00.000Z',
      },
      {
        metric_name: 'active_sessions',
        metric_value: 342,
        updated_at: '2024-01-15T08:00:00.000Z',
      },
      {
        metric_name: 'total_orders',
        metric_value: 5621,
        updated_at: '2024-01-15T08:00:00.000Z',
      },
      {
        metric_name: 'revenue',
        metric_value: 128450.75,
        updated_at: '2024-01-15T08:00:00.000Z',
      },
    ];

    const insertManyStats = database.transaction((stats) => {
      for (const stat of stats) {
        insertStat.run(stat);
      }
    });

    insertManyStats(seedStats);
  }

  return database;
}

function closeDb() {
  if (db) {
    db.close();
    db = null;
  }
}

module.exports = { getDb, initDb, closeDb };
