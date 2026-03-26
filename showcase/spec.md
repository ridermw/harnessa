# Code Review Dashboard - Comprehensive Specification

## 1. Product Overview and User Stories

### Product Overview
A real-time collaborative code review dashboard that leverages AI-powered trio analysis (Planner→Generator→Evaluator) to provide instant feedback on code quality. Teams can submit code snippets or GitHub PR URLs and receive comprehensive analysis including bug detection, quality scores, and improvement suggestions.

### Core User Stories

**As a Developer:**
- I want to paste code snippets and get instant AI-powered feedback
- I want to submit GitHub PR URLs for automated review
- I want to see quality scores and specific improvement suggestions
- I want to track my code quality trends over time
- I want to see what my teammates are reviewing in real-time

**As a Team Lead:**
- I want to monitor team code quality metrics
- I want to see trending issues across our codebase
- I want to track improvement over time with visualizations
- I want to identify patterns in code review feedback

**As a Product Manager:**
- I want visibility into development velocity and quality
- I want to understand common pain points in our codebase
- I want to track the ROI of code review processes

### Key Features
- **Real-time Analysis**: Instant feedback using Planner→Generator→Evaluator workflow
- **Multiple Input Methods**: Code paste, GitHub PR integration, file upload
- **Live Activity Feed**: See team reviews as they happen
- **Quality Metrics**: Comprehensive scoring and trend analysis
- **Collaborative Tools**: Comments, annotations, and team discussions
- **Historical Tracking**: Quality trends and improvement over time

## 2. Technical Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React SPA     │    │  Express API    │    │   Harnessa      │
│                 │    │                 │    │   Trio Engine   │
│ • Dashboard     │◄──►│ • REST API      │◄──►│ • Planner       │
│ • Real-time UI  │    │ • WebSockets    │    │ • Generator     │
│ • Charts/Viz    │    │ • GitHub API    │    │ • Evaluator     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   SQLite DB     │
                       │                 │
                       │ • Reviews       │
                       │ • Users         │
                       │ • Metrics       │
                       │ • Activity      │
                       └─────────────────┘
```

### Technology Stack
- **Frontend**: React 18+ with TypeScript, Socket.IO client, Chart.js/Recharts
- **Backend**: Express.js with TypeScript, Socket.IO, GitHub API integration
- **Database**: SQLite with better-sqlite3 for performance
- **AI Engine**: Harnessa trio workflow integration
- **Real-time**: WebSocket communication for live updates
- **Authentication**: JWT-based auth with GitHub OAuth integration

### Folder Structure
```
src/
├── client/                 # React frontend
│   ├── components/         # Reusable UI components
│   ├── pages/             # Main page components
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API client services
│   ├── types/             # TypeScript definitions
│   └── utils/             # Helper functions
├── server/                # Express backend
│   ├── routes/            # API route handlers
│   ├── services/          # Business logic
│   ├── models/            # Database models
│   ├── middleware/        # Express middleware
│   ├── sockets/           # Socket.IO handlers
│   └── integrations/      # External service integrations
└── shared/                # Shared types and utilities
    ├── types/             # Common TypeScript definitions
    └── constants/         # Shared constants
```

## 3. API Endpoints

### Authentication
```
POST   /api/auth/login          # GitHub OAuth login
POST   /api/auth/logout         # Logout user
GET    /api/auth/me             # Get current user
```

### Code Review
```
POST   /api/reviews            # Submit code for review
GET    /api/reviews            # List reviews (paginated)
GET    /api/reviews/:id        # Get specific review
PUT    /api/reviews/:id        # Update review (add comments)
DELETE /api/reviews/:id        # Delete review
POST   /api/reviews/:id/retry  # Retry failed review
```

### GitHub Integration
```
POST   /api/github/pr          # Submit PR URL for review
GET    /api/github/repos       # List user's repositories
GET    /api/github/prs/:repo   # List PRs for a repository
```

### Analytics
```
GET    /api/analytics/trends           # Quality trends over time
GET    /api/analytics/summary         # Dashboard summary stats
GET    /api/analytics/team-metrics    # Team-wide metrics
GET    /api/analytics/user/:id/stats  # Individual user statistics
```

### Activity Feed
```
GET    /api/activity                  # Recent activity feed
GET    /api/activity/subscribe        # WebSocket subscription endpoint
```

### Request/Response Examples
```typescript
// POST /api/reviews
{
  "code": "function example() { ... }",
  "language": "javascript",
  "title": "Review my React component",
  "tags": ["react", "frontend"]
}

// Response
{
  "id": "rev_123",
  "status": "analyzing",
  "submittedAt": "2024-03-26T13:55:00Z",
  "estimatedCompletion": "2024-03-26T13:57:00Z"
}

// GET /api/reviews/rev_123 (completed)
{
  "id": "rev_123",
  "status": "completed",
  "code": "...",
  "language": "javascript",
  "title": "Review my React component",
  "tags": ["react", "frontend"],
  "submittedAt": "2024-03-26T13:55:00Z",
  "completedAt": "2024-03-26T13:56:45Z",
  "analysis": {
    "plannerOutput": "Analyzed component structure...",
    "generatorOutput": "Suggested improvements...",
    "evaluatorOutput": "Quality assessment...",
    "overallScore": 8.5,
    "scores": {
      "readability": 9,
      "maintainability": 8,
      "performance": 8,
      "security": 9
    },
    "bugsFound": [
      {
        "type": "potential-memory-leak",
        "line": 15,
        "description": "useEffect missing dependency",
        "severity": "medium",
        "suggestion": "Add 'data' to dependency array"
      }
    ],
    "suggestions": [
      {
        "category": "performance",
        "description": "Consider using useMemo for expensive calculations",
        "line": 22,
        "priority": "low"
      }
    ]
  },
  "submittedBy": "user_456",
  "comments": []
}
```

## 4. Database Schema

### Users Table
```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  github_id INTEGER UNIQUE,
  username TEXT NOT NULL,
  email TEXT,
  avatar_url TEXT,
  name TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Reviews Table
```sql
CREATE TABLE reviews (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  code TEXT NOT NULL,
  language TEXT NOT NULL,
  status TEXT CHECK (status IN ('pending', 'analyzing', 'completed', 'failed')),
  submitted_by TEXT REFERENCES users(id),
  github_pr_url TEXT,
  tags TEXT, -- JSON array
  submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  started_at DATETIME,
  completed_at DATETIME,
  overall_score REAL,
  planner_output TEXT,
  generator_output TEXT,
  evaluator_output TEXT,
  analysis_data TEXT, -- JSON blob for scores, bugs, suggestions
  error_message TEXT
);
```

### Comments Table
```sql
CREATE TABLE comments (
  id TEXT PRIMARY KEY,
  review_id TEXT REFERENCES reviews(id) ON DELETE CASCADE,
  user_id TEXT REFERENCES users(id),
  content TEXT NOT NULL,
  line_number INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Quality Metrics Table
```sql
CREATE TABLE quality_metrics (
  id TEXT PRIMARY KEY,
  review_id TEXT REFERENCES reviews(id) ON DELETE CASCADE,
  metric_name TEXT NOT NULL,
  metric_value REAL NOT NULL,
  recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Activity Log Table
```sql
CREATE TABLE activity_log (
  id TEXT PRIMARY KEY,
  user_id TEXT REFERENCES users(id),
  action_type TEXT NOT NULL, -- 'review_submitted', 'review_completed', 'comment_added'
  resource_id TEXT, -- review_id, comment_id, etc.
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes for Performance
```sql
CREATE INDEX idx_reviews_status ON reviews(status);
CREATE INDEX idx_reviews_submitted_by ON reviews(submitted_by);
CREATE INDEX idx_reviews_submitted_at ON reviews(submitted_at);
CREATE INDEX idx_comments_review_id ON comments(review_id);
CREATE INDEX idx_activity_log_user_id ON activity_log(user_id);
CREATE INDEX idx_activity_log_created_at ON activity_log(created_at);
CREATE INDEX idx_quality_metrics_review_id ON quality_metrics(review_id);
```

## 5. UI Components

### Page Components
```
Dashboard/
├── DashboardPage.tsx           # Main dashboard with stats overview
├── ReviewSubmissionForm.tsx    # Code input and GitHub PR form
├── ReviewDetailPage.tsx        # Individual review results
├── AnalyticsPage.tsx          # Charts and trend analysis
├── ActivityFeedPage.tsx       # Live team activity
└── ProfilePage.tsx            # User profile and personal stats
```

### Shared Components
```
components/
├── layout/
│   ├── Navigation.tsx         # Top navigation bar
│   ├── Sidebar.tsx           # Left sidebar with quick actions
│   └── Layout.tsx            # Main layout wrapper
├── review/
│   ├── CodeEditor.tsx        # Syntax-highlighted code display
│   ├── ReviewCard.tsx        # Review summary card
│   ├── ScoreDisplay.tsx      # Visual score representation
│   ├── BugReport.tsx         # Bug findings display
│   ├── SuggestionList.tsx    # Improvement suggestions
│   └── CommentThread.tsx     # Review comments
├── charts/
│   ├── QualityTrendChart.tsx # Time-series quality chart
│   ├── ScoreDistribution.tsx # Score histogram
│   ├── MetricComparison.tsx  # Multi-metric comparison
│   └── TeamLeaderboard.tsx   # Team ranking display
├── common/
│   ├── LoadingSpinner.tsx    # Loading states
│   ├── ErrorBoundary.tsx     # Error handling
│   ├── Toast.tsx             # Notifications
│   ├── Modal.tsx             # Modal dialogs
│   ├── Button.tsx            # Consistent button styles
│   └── Badge.tsx             # Status badges
└── realtime/
    ├── ActivityFeed.tsx      # Live activity stream
    ├── NotificationCenter.tsx # Real-time notifications
    └── LiveCounter.tsx       # Live user/review counters
```

### Component Examples
```typescript
// ReviewCard.tsx
interface ReviewCardProps {
  review: Review;
  onViewDetails: (id: string) => void;
  onAddComment?: (id: string, content: string) => void;
}

// ScoreDisplay.tsx
interface ScoreDisplayProps {
  scores: {
    overall: number;
    readability: number;
    maintainability: number;
    performance: number;
    security: number;
  };
  size?: 'small' | 'medium' | 'large';
  showDetails?: boolean;
}

// ActivityFeed.tsx
interface ActivityFeedProps {
  activities: Activity[];
  realTimeEnabled?: boolean;
  maxItems?: number;
}
```

### State Management
- **React Context** for user authentication state
- **React Query** for server state management and caching
- **Local State** for UI interactions and form data
- **WebSocket State** for real-time updates

## 6. Trio Integration

### Integration Architecture
The app integrates with the Harnessa trio system as a core feature:

```typescript
// Trio Workflow Service
class TrioAnalysisService {
  async analyzeCode(code: string, language: string): Promise<AnalysisResult> {
    // 1. Submit to Planner
    const plan = await this.runPlanner(code, language);
    
    // 2. Execute with Generator  
    const generated = await this.runGenerator(plan);
    
    // 3. Evaluate with Evaluator
    const evaluation = await this.runEvaluator(generated);
    
    return this.combineResults(plan, generated, evaluation);
  }
}
```

### Trio Workflow Steps

**1. Planner Phase**
- Analyzes code structure and identifies review scope
- Creates review plan with focus areas
- Estimates complexity and required analysis depth
- Output: Structured review plan with priorities

**2. Generator Phase**
- Executes the review plan systematically
- Identifies bugs, code smells, and improvement opportunities
- Generates specific suggestions and alternatives
- Output: Detailed findings with code examples

**3. Evaluator Phase**
- Critically assesses Generator's findings
- Validates bug reports and suggestion quality
- Assigns confidence scores to each finding
- Output: Final quality score and validated recommendations

### Real-time Progress Tracking
```typescript
interface TrioProgress {
  phase: 'planner' | 'generator' | 'evaluator';
  progress: number; // 0-100
  currentTask: string;
  estimatedTimeRemaining: number;
  phaseResults?: {
    planner?: PlannerOutput;
    generator?: GeneratorOutput;
    evaluator?: EvaluatorOutput;
  };
}
```

### Trio Configuration
```typescript
interface TrioConfig {
  models: {
    planner: 'claude-3.5-sonnet' | 'gpt-4' | 'gemini-pro';
    generator: 'claude-3.5-sonnet' | 'gpt-4' | 'gemini-pro';
    evaluator: 'claude-3.5-sonnet' | 'gpt-4' | 'gemini-pro';
  };
  criteria: {
    focus: string[]; // ['security', 'performance', 'readability']
    severity: 'low' | 'medium' | 'high';
    includeStyle: boolean;
  };
  timeouts: {
    plannerTimeout: number;
    generatorTimeout: number;
    evaluatorTimeout: number;
  };
}
```

### Integration Points
- **API Endpoint**: `/api/reviews` triggers trio analysis
- **WebSocket Events**: Real-time progress updates
- **Database Storage**: Separate storage for each phase output
- **Error Handling**: Graceful degradation if trio phases fail
- **Retry Logic**: Automatic retry for failed phases

## 7. Acceptance Criteria

### Core Functionality
- [ ] Users can submit code snippets for AI analysis
- [ ] Users can submit GitHub PR URLs for review
- [ ] Trio analysis (Planner→Generator→Evaluator) completes successfully
- [ ] Results display comprehensive scores and specific feedback
- [ ] Real-time progress updates during analysis
- [ ] Live activity feed shows team reviews
- [ ] Quality trends charts display historical data

### User Experience
- [ ] Code submission form with syntax highlighting
- [ ] Responsive design works on desktop and mobile
- [ ] Loading states provide clear feedback during analysis
- [ ] Error handling provides helpful messages
- [ ] Search and filter functionality for review history
- [ ] Export functionality for review reports

### Real-time Features
- [ ] WebSocket connection for live updates
- [ ] Activity feed updates in real-time
- [ ] Notification system for review completions
- [ ] Live user presence indicators
- [ ] Real-time collaboration on review comments

### Performance Requirements
- [ ] Review analysis completes within 3 minutes for typical code snippets
- [ ] Dashboard loads within 2 seconds
- [ ] Real-time updates have <500ms latency
- [ ] Supports 50+ concurrent users
- [ ] Database queries complete within 100ms

### Security & Authentication
- [ ] GitHub OAuth integration for secure login
- [ ] JWT-based session management
- [ ] Input validation prevents code injection
- [ ] Rate limiting on API endpoints
- [ ] Secure handling of GitHub tokens

### Data & Analytics
- [ ] Quality metrics stored with historical tracking
- [ ] Trend analysis shows improvement over time
- [ ] Team-level aggregated metrics
- [ ] Individual user performance tracking
- [ ] Data export in standard formats (JSON, CSV)

### Integration & Deployment
- [ ] Self-contained deployment (no external dependencies)
- [ ] SQLite database with migration system
- [ ] Environment-based configuration
- [ ] Docker containerization support
- [ ] Health check endpoints for monitoring

### Edge Cases & Error Handling
- [ ] Graceful handling of malformed code input
- [ ] Timeout handling for long-running analyses
- [ ] Network failure recovery
- [ ] GitHub API rate limit handling
- [ ] Concurrent user session management
- [ ] Database connection failure recovery

### Testing Requirements
- [ ] Unit tests for critical business logic
- [ ] Integration tests for API endpoints
- [ ] E2E tests for core user workflows
- [ ] WebSocket connection testing
- [ ] Performance benchmarking
- [ ] Security vulnerability scanning

### Documentation
- [ ] API documentation with examples
- [ ] User guide for getting started
- [ ] Development setup instructions
- [ ] Deployment and configuration guide
- [ ] Architecture decision records

This specification provides a comprehensive foundation for building a production-ready collaborative code review dashboard that leverages AI-powered analysis through the Harnessa trio system.