import express from 'express';
import http from 'http';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import compression from 'compression';
import { Server } from 'socket.io';
import initSqlJs, { Database as SqlJsDatabase } from 'sql.js';
import { v4 as uuidv4 } from 'uuid';

// Types
interface Review {
  id: string;
  title: string;
  code: string;
  language: string;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  submitted_by?: string;
  github_pr_url?: string;
  tags?: string;
  submitted_at: string;
  started_at?: string;
  completed_at?: string;
  overall_score?: number;
  planner_output?: string;
  generator_output?: string;
  evaluator_output?: string;
  analysis_data?: string;
  error_message?: string;
}

interface ActivityLog {
  id: string;
  user_id?: string;
  action_type: string;
  resource_id?: string;
  description: string;
  created_at: string;
}

// Database Service (sql.js — pure JS SQLite, no native deps)
class DatabaseService {
  private db!: SqlJsDatabase;

  async initialize() {
    const SQL = await initSqlJs();
    this.db = new SQL.Database();
    this.createTables();
    this.createIndexes();
    console.log('✅ Database initialized (sql.js in-memory)');
  }

  private createTables() {
    this.db.run(`
      CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        github_id INTEGER UNIQUE,
        username TEXT NOT NULL,
        email TEXT,
        avatar_url TEXT,
        name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    this.db.run(`
      CREATE TABLE IF NOT EXISTS reviews (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        code TEXT NOT NULL,
        language TEXT NOT NULL,
        status TEXT CHECK (status IN ('pending', 'analyzing', 'completed', 'failed')) DEFAULT 'pending',
        submitted_by TEXT,
        github_pr_url TEXT,
        tags TEXT,
        submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        started_at DATETIME,
        completed_at DATETIME,
        overall_score REAL,
        planner_output TEXT,
        generator_output TEXT,
        evaluator_output TEXT,
        analysis_data TEXT,
        error_message TEXT
      )
    `);

    this.db.run(`
      CREATE TABLE IF NOT EXISTS activity_log (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        action_type TEXT NOT NULL,
        resource_id TEXT,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
  }

  private createIndexes() {
    this.db.run('CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews(status)');
    this.db.run('CREATE INDEX IF NOT EXISTS idx_reviews_submitted_at ON reviews(submitted_at)');
    this.db.run('CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON activity_log(created_at)');
  }

  private queryAll(sql: string, params: any[] = []): any[] {
    const stmt = this.db.prepare(sql);
    if (params.length) stmt.bind(params);
    const rows: any[] = [];
    while (stmt.step()) {
      rows.push(stmt.getAsObject());
    }
    stmt.free();
    return rows;
  }

  private queryOne(sql: string, params: any[] = []): any | undefined {
    const rows = this.queryAll(sql, params);
    return rows[0];
  }

  createReview(review: Omit<Review, 'id' | 'submitted_at'>): Review {
    const id = uuidv4();
    const now = new Date().toISOString();
    const newReview = { id, submitted_at: now, ...review };

    this.db.run(`
      INSERT INTO reviews (
        id, title, code, language, status, submitted_by, github_pr_url, tags, submitted_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `, [
      newReview.id, newReview.title, newReview.code, newReview.language,
      newReview.status, newReview.submitted_by ?? null, newReview.github_pr_url ?? null,
      newReview.tags ?? null, newReview.submitted_at
    ]);

    return newReview as Review;
  }

  getReview(id: string): Review | undefined {
    return this.queryOne('SELECT * FROM reviews WHERE id = ?', [id]) as Review | undefined;
  }

  getReviews(limit = 20, offset = 0): Review[] {
    return this.queryAll(
      'SELECT * FROM reviews ORDER BY submitted_at DESC LIMIT ? OFFSET ?',
      [limit, offset]
    ) as Review[];
  }

  updateReview(id: string, updates: Partial<Review>): boolean {
    const fields = Object.keys(updates).filter(key => key !== 'id');
    if (fields.length === 0) return false;

    const setClause = fields.map(field => `${field} = ?`).join(', ');
    const values: any[] = fields.map(field => updates[field as keyof Review] ?? null);

    this.db.run(`UPDATE reviews SET ${setClause} WHERE id = ?`, [...values, id]);
    return this.db.getRowsModified() > 0;
  }

  deleteReview(id: string): boolean {
    this.db.run('DELETE FROM reviews WHERE id = ?', [id]);
    return this.db.getRowsModified() > 0;
  }

  logActivity(activity: Omit<ActivityLog, 'id' | 'created_at'>): ActivityLog {
    const id = uuidv4();
    const now = new Date().toISOString();
    const newActivity = { id, created_at: now, ...activity };

    this.db.run(`
      INSERT INTO activity_log (id, user_id, action_type, resource_id, description, created_at)
      VALUES (?, ?, ?, ?, ?, ?)
    `, [
      newActivity.id, newActivity.user_id ?? null, newActivity.action_type,
      newActivity.resource_id ?? null, newActivity.description, newActivity.created_at
    ]);

    return newActivity;
  }

  getRecentActivity(limit = 50): ActivityLog[] {
    return this.queryAll(
      'SELECT * FROM activity_log ORDER BY created_at DESC LIMIT ?',
      [limit]
    ) as ActivityLog[];
  }

  getReviewStats() {
    const totalReviews = this.queryOne('SELECT COUNT(*) as count FROM reviews') as { count: number };
    const completedReviews = this.queryOne('SELECT COUNT(*) as count FROM reviews WHERE status = ?', ['completed']) as { count: number };
    const avgScore = this.queryOne('SELECT AVG(overall_score) as avg FROM reviews WHERE overall_score IS NOT NULL') as { avg: number | null };
    const recentReviews = this.queryOne('SELECT COUNT(*) as count FROM reviews WHERE submitted_at > datetime("now", "-7 days")') as { count: number };

    return {
      total: totalReviews.count,
      completed: completedReviews.count,
      averageScore: Math.round((avgScore.avg || 0) * 10) / 10,
      recentCount: recentReviews.count
    };
  }

  close() {
    this.db.close();
  }
}

// Trio Analysis Service
class TrioAnalysisService {
  constructor(private dbService: DatabaseService) {}

  async analyzeCode(reviewId: string, code: string, language: string, io: Server): Promise<void> {
    const phases = ['planner', 'generator', 'evaluator'];
    let currentProgress = 0;
    
    for (const phase of phases) {
      // Update status
      io.emit('analysis:progress', {
        reviewId,
        phase,
        progress: currentProgress,
        status: `Running ${phase} analysis...`
      });

      // Simulate analysis time
      await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));
      
      // Generate mock analysis results
      const result = await this.simulatePhaseAnalysis(phase, code, language);
      
      // Update review with phase result
      const updateField = `${phase}_output`;
      this.dbService.updateReview(reviewId, { [updateField]: result } as any);
      
      currentProgress += 33.33;
      
      // Emit progress update
      io.emit('analysis:progress', {
        reviewId,
        phase,
        progress: Math.min(currentProgress, 100),
        result,
        status: `${phase} analysis complete`
      });
    }
    
    // Generate final analysis
    const finalAnalysis = await this.generateFinalAnalysis(code, language);
    
    // Update review as completed
    this.dbService.updateReview(reviewId, {
      status: 'completed',
      completed_at: new Date().toISOString(),
      overall_score: finalAnalysis.overallScore,
      analysis_data: JSON.stringify(finalAnalysis)
    });
    
    // Log activity
    this.dbService.logActivity({
      action_type: 'review_completed',
      resource_id: reviewId,
      description: `Code review completed with score ${finalAnalysis.overallScore}`
    });
    
    // Final completion event
    io.emit('analysis:complete', {
      reviewId,
      analysis: finalAnalysis
    });
  }

  private async simulatePhaseAnalysis(phase: string, code: string, language: string): Promise<string> {
    const lines = code.split('\n').length;
    
    switch (phase) {
      case 'planner':
        return `Analyzed ${language} code with ${lines} lines. Identified focus areas: code structure, error handling, performance patterns, and security considerations.`;
      
      case 'generator':
        const bugCount = Math.floor(Math.random() * 3) + 1;
        return `Generated analysis with ${bugCount} potential issues found. Reviewed coding patterns, identified optimization opportunities, and suggested improvements for maintainability.`;
      
      case 'evaluator':
        const confidence = Math.floor(Math.random() * 20) + 80;
        return `Evaluated findings with ${confidence}% confidence. Validated issue severity, assessed code quality metrics, and provided final recommendations.`;
      
      default:
        return 'Analysis completed';
    }
  }

  private async generateFinalAnalysis(code: string, language: string) {
    const baseScore = 6 + Math.random() * 3; // Random score between 6-9
    const bugs = this.generateMockBugs(code);
    const suggestions = this.generateMockSuggestions();
    
    return {
      overallScore: Math.round(baseScore * 10) / 10,
      scores: {
        readability: Math.round((baseScore + Math.random() - 0.5) * 10) / 10,
        maintainability: Math.round((baseScore + Math.random() - 0.5) * 10) / 10,
        performance: Math.round((baseScore + Math.random() - 0.5) * 10) / 10,
        security: Math.round((baseScore + Math.random() - 0.5) * 10) / 10,
      },
      bugsFound: bugs,
      suggestions: suggestions,
      summary: `Analyzed ${language} code. Found ${bugs.length} issues and ${suggestions.length} improvement opportunities.`
    };
  }

  private generateMockBugs(code: string) {
    const possibleBugs = [
      {
        type: 'potential-null-reference',
        line: Math.floor(Math.random() * 20) + 1,
        description: 'Potential null reference exception',
        severity: 'medium',
        suggestion: 'Add null check before accessing properties'
      },
      {
        type: 'unused-variable',
        line: Math.floor(Math.random() * 15) + 5,
        description: 'Variable declared but never used',
        severity: 'low',
        suggestion: 'Remove unused variable or implement its usage'
      },
      {
        type: 'performance-issue',
        line: Math.floor(Math.random() * 25) + 1,
        description: 'Inefficient loop operation',
        severity: 'medium',
        suggestion: 'Consider using more efficient array methods'
      }
    ];
    
    const bugCount = Math.floor(Math.random() * 3);
    return possibleBugs.slice(0, bugCount);
  }

  private generateMockSuggestions() {
    const allSuggestions = [
      {
        category: 'readability',
        description: 'Consider adding more descriptive variable names',
        priority: 'medium'
      },
      {
        category: 'performance',
        description: 'Use const for values that don\'t change',
        priority: 'low'
      },
      {
        category: 'maintainability',
        description: 'Break down large functions into smaller ones',
        priority: 'high'
      },
      {
        category: 'security',
        description: 'Validate user input before processing',
        priority: 'high'
      }
    ];
    
    const suggestionCount = Math.floor(Math.random() * 3) + 1;
    return allSuggestions.slice(0, suggestionCount);
  }
}

// Express App Setup
const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: process.env.CLIENT_URL || "http://localhost:3000",
    methods: ["GET", "POST", "PUT", "DELETE"]
  }
});

const PORT = process.env.PORT || 3001;
const dbService = new DatabaseService();

async function main() {
  await dbService.initialize();
  const trioService = new TrioAnalysisService(dbService);

  // Middleware
  app.use(helmet({ contentSecurityPolicy: false }));
  app.use(cors({ origin: process.env.CLIENT_URL || "http://localhost:3000", credentials: true }));
  app.use(compression());
  app.use(morgan('combined'));
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true }));

  // Routes
  const router = express.Router();

// Reviews endpoints
router.post('/reviews', async (req, res) => {
  try {
    const { title, code, language, tags } = req.body;
    
    if (!title || !code || !language) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const review = dbService.createReview({
      title,
      code,
      language,
      status: 'pending',
      tags: tags ? JSON.stringify(tags) : undefined
    });

    // Log activity
    dbService.logActivity({
      action_type: 'review_submitted',
      resource_id: review.id,
      description: `New ${language} code review: ${title}`
    });

    // Start trio analysis in background
    setTimeout(async () => {
      dbService.updateReview(review.id, { 
        status: 'analyzing', 
        started_at: new Date().toISOString() 
      });
      
      await trioService.analyzeCode(review.id, code, language, io);
    }, 1000);

    res.status(201).json(review);
  } catch (error) {
    console.error('Error creating review:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/reviews', (req, res) => {
  try {
    const limit = parseInt(req.query.limit as string) || 20;
    const offset = parseInt(req.query.offset as string) || 0;
    
    const reviews = dbService.getReviews(limit, offset);
    res.json(reviews);
  } catch (error) {
    console.error('Error fetching reviews:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.get('/reviews/:id', (req, res) => {
  try {
    const review = dbService.getReview(req.params.id);
    
    if (!review) {
      return res.status(404).json({ error: 'Review not found' });
    }
    
    res.json(review);
  } catch (error) {
    console.error('Error fetching review:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

router.delete('/reviews/:id', (req, res) => {
  try {
    const deleted = dbService.deleteReview(req.params.id);
    
    if (!deleted) {
      return res.status(404).json({ error: 'Review not found' });
    }
    
    // Log activity
    dbService.logActivity({
      action_type: 'review_deleted',
      resource_id: req.params.id,
      description: `Code review deleted`
    });
    
    res.status(204).send();
  } catch (error) {
    console.error('Error deleting review:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Analytics endpoints
router.get('/analytics/summary', (req, res) => {
  try {
    const stats = dbService.getReviewStats();
    res.json(stats);
  } catch (error) {
    console.error('Error fetching analytics:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Activity endpoints
router.get('/activity', (req, res) => {
  try {
    const limit = parseInt(req.query.limit as string) || 50;
    const activities = dbService.getRecentActivity(limit);
    res.json(activities);
  } catch (error) {
    console.error('Error fetching activity:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Health check
router.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

  app.use('/api', router);

  // WebSocket handlers
  io.on('connection', (socket) => {
    console.log('Client connected:', socket.id);
    
    socket.on('subscribe:activity', () => {
      socket.join('activity-feed');
    });
    
    socket.on('subscribe:reviews', (reviewId: string) => {
      socket.join(`review-${reviewId}`);
    });
    
    socket.on('disconnect', () => {
      console.log('Client disconnected:', socket.id);
    });
  });

  // Serve static HTML for frontend
  app.get('*', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Code Review Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
        <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
        <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        <script src="https://cdn.socket.io/4.7.4/socket.io.min.js"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
        <style>
          .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          }
          .card-hover {
            transition: all 0.3s ease;
          }
          .card-hover:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
          }
          .pulse-animation {
            animation: pulse 2s infinite;
          }
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
          .code-container {
            max-height: 400px;
            overflow-y: auto;
          }
        </style>
    </head>
    <body class="bg-gray-50">
        <div id="root"></div>
        
        <script type="text/babel">
          const { useState, useEffect, useCallback } = React;
          
          // Socket connection
          const socket = io();
          
          // API functions
          const api = {
            async createReview(reviewData) {
              const response = await fetch('/api/reviews', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(reviewData)
              });
              return response.json();
            },
            
            async getReviews() {
              const response = await fetch('/api/reviews');
              return response.json();
            },
            
            async getReview(id) {
              const response = await fetch('/api/reviews/' + id);
              return response.json();
            },
            
            async getAnalytics() {
              const response = await fetch('/api/analytics/summary');
              return response.json();
            },
            
            async getActivity() {
              const response = await fetch('/api/activity');
              return response.json();
            }
          };
          
          // Components
          function ScoreDisplay({ score, size = 'medium' }) {
            const sizeClasses = {
              small: 'w-12 h-12 text-sm',
              medium: 'w-16 h-16 text-lg',
              large: 'w-24 h-24 text-xl'
            };
            
            const getScoreColor = (score) => {
              if (score >= 8) return 'text-green-600';
              if (score >= 6) return 'text-yellow-600';
              return 'text-red-600';
            };
            
            return (
              <div className={"relative inline-flex items-center justify-center rounded-full border-4 border-gray-200 " + sizeClasses[size]}>
                <span className={"font-bold " + getScoreColor(score)}>
                  {score ? score.toFixed(1) : 'N/A'}
                </span>
              </div>
            );
          }
          
          function ReviewCard({ review, onClick }) {
            const getStatusBadge = (status) => {
              const badges = {
                pending: 'bg-yellow-100 text-yellow-800',
                analyzing: 'bg-blue-100 text-blue-800',
                completed: 'bg-green-100 text-green-800',
                failed: 'bg-red-100 text-red-800'
              };
              
              return (
                <span className={"px-2 py-1 rounded-full text-xs font-medium " + (badges[status] || badges.pending)}>
                  {status}
                </span>
              );
            };
            
            return (
              <div 
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 card-hover cursor-pointer"
                onClick={() => onClick(review)}
              >
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 truncate">{review.title}</h3>
                  {getStatusBadge(review.status)}
                </div>
                
                <div className="flex items-center space-x-4 mb-4">
                  <span className="text-sm text-gray-500">Language:</span>
                  <span className="text-sm font-medium text-gray-900 capitalize">{review.language}</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">
                    {new Date(review.submitted_at).toLocaleDateString()}
                  </span>
                  
                  {review.overall_score && (
                    <ScoreDisplay score={review.overall_score} size="small" />
                  )}
                </div>
              </div>
            );
          }
          
          function CodeEditor({ code, language, readOnly = true }) {
            useEffect(() => {
              if (window.Prism) {
                window.Prism.highlightAll();
              }
            }, [code, language]);
            
            return (
              <div className="code-container bg-gray-900 rounded-lg p-4">
                <pre className="text-sm">
                  <code className={"language-" + language}>
                    {code}
                  </code>
                </pre>
              </div>
            );
          }
          
          function ProgressBar({ progress, phase }) {
            return (
              <div className="w-full">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span className="capitalize">{phase} Phase</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: progress + '%' }}
                  ></div>
                </div>
              </div>
            );
          }
          
          function ActivityFeed({ activities }) {
            return (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
                <div className="space-y-3">
                  {activities.length === 0 ? (
                    <p className="text-gray-500 text-sm">No recent activity</p>
                  ) : (
                    activities.slice(0, 10).map((activity, index) => (
                      <div key={activity.id || index} className="flex items-start space-x-3">
                        <div className="flex-shrink-0 w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                        <div className="flex-1">
                          <p className="text-sm text-gray-900">{activity.description}</p>
                          <p className="text-xs text-gray-500">
                            {new Date(activity.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          }
          
          function ReviewForm({ onSubmit, loading }) {
            const [formData, setFormData] = useState({
              title: '',
              code: '',
              language: 'javascript',
              tags: ''
            });
            
            const handleSubmit = (e) => {
              e.preventDefault();
              const tags = formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag);
              onSubmit({ ...formData, tags });
            };
            
            return (
              <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Submit Code for Review</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Title
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={formData.title}
                      onChange={(e) => setFormData({...formData, title: e.target.value})}
                      placeholder="Describe your code..."
                      required
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Language
                      </label>
                      <select
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={formData.language}
                        onChange={(e) => setFormData({...formData, language: e.target.value})}
                      >
                        <option value="javascript">JavaScript</option>
                        <option value="typescript">TypeScript</option>
                        <option value="python">Python</option>
                        <option value="java">Java</option>
                        <option value="csharp">C#</option>
                        <option value="go">Go</option>
                        <option value="rust">Rust</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Tags (comma separated)
                      </label>
                      <input
                        type="text"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={formData.tags}
                        onChange={(e) => setFormData({...formData, tags: e.target.value})}
                        placeholder="react, frontend, bug-fix"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Code
                    </label>
                    <textarea
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                      rows="10"
                      value={formData.code}
                      onChange={(e) => setFormData({...formData, code: e.target.value})}
                      placeholder="Paste your code here..."
                      required
                    />
                  </div>
                  
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Submitting...' : 'Submit for Review'}
                  </button>
                </div>
              </form>
            );
          }
          
          function ReviewDetails({ review, analysisProgress, onBack }) {
            if (!review) return null;
            
            let analysis = null;
            if (review.analysis_data) {
              try {
                analysis = JSON.parse(review.analysis_data);
              } catch (e) {
                console.error('Failed to parse analysis data:', e);
              }
            }
            
            return (
              <div className="space-y-6">
                <div className="flex items-center space-x-4">
                  <button
                    onClick={onBack}
                    className="text-blue-600 hover:text-blue-700"
                  >
                    ← Back to Reviews
                  </button>
                  <h2 className="text-2xl font-bold text-gray-900">{review.title}</h2>
                </div>
                
                {/* Review Progress */}
                {review.status === 'analyzing' && analysisProgress && (
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis in Progress</h3>
                    <ProgressBar progress={analysisProgress.progress} phase={analysisProgress.phase} />
                    <p className="text-sm text-gray-600 mt-2">{analysisProgress.status}</p>
                  </div>
                )}
                
                {/* Code Display */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Code</h3>
                  <CodeEditor code={review.code} language={review.language} />
                </div>
                
                {/* Analysis Results */}
                {analysis && (
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis Results</h3>
                    
                    {/* Overall Score */}
                    <div className="mb-6">
                      <div className="flex items-center space-x-4">
                        <ScoreDisplay score={analysis.overallScore} size="large" />
                        <div>
                          <h4 className="text-xl font-semibold text-gray-900">Overall Score</h4>
                          <p className="text-gray-600">{analysis.summary}</p>
                        </div>
                      </div>
                    </div>
                    
                    {/* Detailed Scores */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      {Object.entries(analysis.scores).map(([metric, score]) => (
                        <div key={metric} className="text-center">
                          <ScoreDisplay score={score} size="medium" />
                          <p className="text-sm text-gray-600 mt-1 capitalize">{metric}</p>
                        </div>
                      ))}
                    </div>
                    
                    {/* Bugs Found */}
                    {analysis.bugsFound.length > 0 && (
                      <div className="mb-6">
                        <h4 className="text-lg font-semibold text-gray-900 mb-3">Issues Found</h4>
                        <div className="space-y-3">
                          {analysis.bugsFound.map((bug, index) => (
                            <div key={index} className="border border-red-200 rounded-lg p-4 bg-red-50">
                              <div className="flex justify-between items-start">
                                <div>
                                  <h5 className="font-medium text-red-900">{bug.type}</h5>
                                  <p className="text-sm text-red-700">{bug.description}</p>
                                  <p className="text-sm text-red-600 mt-1">Line {bug.line}</p>
                                </div>
                                <span className={"px-2 py-1 rounded text-xs font-medium " + 
                                  (bug.severity === 'high' ? 'bg-red-100 text-red-800' :
                                   bug.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                   'bg-gray-100 text-gray-800')}>
                                  {bug.severity}
                                </span>
                              </div>
                              <p className="text-sm text-gray-700 mt-2">
                                <strong>Suggestion:</strong> {bug.suggestion}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Suggestions */}
                    {analysis.suggestions.length > 0 && (
                      <div>
                        <h4 className="text-lg font-semibold text-gray-900 mb-3">Improvement Suggestions</h4>
                        <div className="space-y-3">
                          {analysis.suggestions.map((suggestion, index) => (
                            <div key={index} className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                              <div className="flex justify-between items-start">
                                <div>
                                  <h5 className="font-medium text-blue-900 capitalize">{suggestion.category}</h5>
                                  <p className="text-sm text-blue-700">{suggestion.description}</p>
                                </div>
                                <span className={"px-2 py-1 rounded text-xs font-medium " + 
                                  (suggestion.priority === 'high' ? 'bg-red-100 text-red-800' :
                                   suggestion.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                   'bg-green-100 text-green-800')}>
                                  {suggestion.priority}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Trio Phases Output */}
                {(review.planner_output || review.generator_output || review.evaluator_output) && (
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Trio Analysis Phases</h3>
                    
                    {review.planner_output && (
                      <div className="mb-4">
                        <h4 className="font-medium text-gray-900 mb-2">Planner Output</h4>
                        <p className="text-sm text-gray-700 bg-gray-50 rounded p-3">{review.planner_output}</p>
                      </div>
                    )}
                    
                    {review.generator_output && (
                      <div className="mb-4">
                        <h4 className="font-medium text-gray-900 mb-2">Generator Output</h4>
                        <p className="text-sm text-gray-700 bg-gray-50 rounded p-3">{review.generator_output}</p>
                      </div>
                    )}
                    
                    {review.evaluator_output && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Evaluator Output</h4>
                        <p className="text-sm text-gray-700 bg-gray-50 rounded p-3">{review.evaluator_output}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          }
          
          function Dashboard() {
            const [reviews, setReviews] = useState([]);
            const [selectedReview, setSelectedReview] = useState(null);
            const [activities, setActivities] = useState([]);
            const [analytics, setAnalytics] = useState({});
            const [loading, setLoading] = useState(false);
            const [analysisProgress, setAnalysisProgress] = useState(null);
            
            // Load initial data
            useEffect(() => {
              loadReviews();
              loadActivities();
              loadAnalytics();
            }, []);
            
            // Socket event listeners
            useEffect(() => {
              socket.on('analysis:progress', (data) => {
                setAnalysisProgress(data);
                // Update review status in list
                setReviews(prev => prev.map(review => 
                  review.id === data.reviewId 
                    ? { ...review, status: 'analyzing' }
                    : review
                ));
              });
              
              socket.on('analysis:complete', (data) => {
                setAnalysisProgress(null);
                // Refresh reviews and analytics
                loadReviews();
                loadAnalytics();
                loadActivities();
              });
              
              return () => {
                socket.off('analysis:progress');
                socket.off('analysis:complete');
              };
            }, []);
            
            const loadReviews = async () => {
              try {
                const data = await api.getReviews();
                setReviews(data);
              } catch (error) {
                console.error('Failed to load reviews:', error);
              }
            };
            
            const loadActivities = async () => {
              try {
                const data = await api.getActivity();
                setActivities(data);
              } catch (error) {
                console.error('Failed to load activities:', error);
              }
            };
            
            const loadAnalytics = async () => {
              try {
                const data = await api.getAnalytics();
                setAnalytics(data);
              } catch (error) {
                console.error('Failed to load analytics:', error);
              }
            };
            
            const handleSubmitReview = async (reviewData) => {
              setLoading(true);
              try {
                await api.createReview(reviewData);
                loadReviews();
                loadActivities();
              } catch (error) {
                console.error('Failed to submit review:', error);
              } finally {
                setLoading(false);
              }
            };
            
            const handleSelectReview = async (review) => {
              try {
                const fullReview = await api.getReview(review.id);
                setSelectedReview(fullReview);
              } catch (error) {
                console.error('Failed to load review details:', error);
              }
            };
            
            if (selectedReview) {
              return (
                <div className="min-h-screen bg-gray-50 py-8">
                  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <ReviewDetails 
                      review={selectedReview}
                      analysisProgress={analysisProgress}
                      onBack={() => setSelectedReview(null)}
                    />
                  </div>
                </div>
              );
            }
            
            return (
              <div className="min-h-screen bg-gray-50">
                {/* Header */}
                <div className="gradient-bg">
                  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <h1 className="text-3xl font-bold text-white">Code Review Dashboard</h1>
                    <p className="text-blue-100 mt-2">AI-powered trio analysis for better code quality</p>
                  </div>
                </div>
                
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                  {/* Analytics Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                      <h3 className="text-sm font-medium text-gray-500">Total Reviews</h3>
                      <p className="text-2xl font-bold text-gray-900">{analytics.total || 0}</p>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                      <h3 className="text-sm font-medium text-gray-500">Completed</h3>
                      <p className="text-2xl font-bold text-green-600">{analytics.completed || 0}</p>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                      <h3 className="text-sm font-medium text-gray-500">Average Score</h3>
                      <p className="text-2xl font-bold text-blue-600">{analytics.averageScore || '0.0'}</p>
                    </div>
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                      <h3 className="text-sm font-medium text-gray-500">This Week</h3>
                      <p className="text-2xl font-bold text-purple-600">{analytics.recentCount || 0}</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Review Form */}
                    <div className="lg:col-span-2">
                      <ReviewForm onSubmit={handleSubmitReview} loading={loading} />
                      
                      {/* Recent Reviews */}
                      <div className="mt-8">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Reviews</h3>
                        <div className="space-y-4">
                          {reviews.length === 0 ? (
                            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-center">
                              <p className="text-gray-500">No reviews yet. Submit your first code review above!</p>
                            </div>
                          ) : (
                            reviews.map((review) => (
                              <ReviewCard 
                                key={review.id} 
                                review={review} 
                                onClick={handleSelectReview}
                              />
                            ))
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {/* Activity Feed */}
                    <div>
                      <ActivityFeed activities={activities} />
                    </div>
                  </div>
                </div>
              </div>
            );
          }
          
          // Render the app
          ReactDOM.render(<Dashboard />, document.getElementById('root'));
        </script>
    </body>
    </html>
  `);
});

// Start server
  server.listen(PORT, () => {
    console.log(`🚀 Code Review Dashboard running on port ${PORT}`);
    console.log(`📊 Open http://localhost:${PORT} to access the dashboard`);
    console.log(`🔌 WebSocket server ready for real-time updates`);
    console.log(`🤖 Trio analysis service initialized`);
  });
}

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  dbService.close();
  server.close(() => {
    console.log('Process terminated');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  dbService.close();
  server.close(() => {
    console.log('Process terminated');
    process.exit(0);
  });
});

main().catch(err => {
  console.error('Failed to start server:', err);
  process.exit(1);
});

export { app, server, io };