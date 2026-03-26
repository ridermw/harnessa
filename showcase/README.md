# Code Review Dashboard

A real-time collaborative code review dashboard powered by AI trio analysis (Planner→Generator→Evaluator).

## Features

- **Real-time Analysis**: Instant feedback using Planner→Generator→Evaluator workflow
- **Multiple Language Support**: JavaScript, TypeScript, Python, Java, C#, Go, Rust
- **Live Activity Feed**: See team reviews as they happen via WebSocket
- **Quality Metrics**: Comprehensive scoring and trend analysis
- **Professional UI**: Tailwind CSS with responsive design
- **Self-contained**: SQLite database with no external dependencies

## Tech Stack

- **Backend**: Express.js + TypeScript + Socket.IO + SQLite
- **Frontend**: React 18 + Tailwind CSS (served from CDN)
- **Database**: SQLite with better-sqlite3
- **Real-time**: WebSocket communication
- **AI Simulation**: Mock trio analysis workflow

## Quick Start

### Option 1: Using the start script
```bash
chmod +x start.sh
./start.sh
```

### Option 2: Manual setup
```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

### Option 3: Production build
```bash
# Build and run
npm run build
npm start
```

## Usage

1. Open http://localhost:3001 in your browser
2. Submit code for review using the form
3. Watch real-time analysis progress
4. View detailed results with scores, bugs, and suggestions
5. Monitor team activity in the live feed

## API Endpoints

- `POST /api/reviews` - Submit code for review
- `GET /api/reviews` - List all reviews
- `GET /api/reviews/:id` - Get specific review
- `DELETE /api/reviews/:id` - Delete review
- `GET /api/analytics/summary` - Get analytics summary
- `GET /api/activity` - Get recent activity
- `GET /api/health` - Health check

## WebSocket Events

- `analysis:progress` - Real-time analysis progress
- `analysis:complete` - Analysis completion notification

## Trio Analysis Workflow

The dashboard simulates the Harnessa trio analysis:

1. **Planner Phase**: Analyzes code structure and creates review plan
2. **Generator Phase**: Identifies bugs and improvement opportunities  
3. **Evaluator Phase**: Validates findings and assigns quality scores

Each phase provides real-time progress updates via WebSocket.

## Database Schema

The application uses SQLite with the following tables:
- `reviews` - Code review submissions and results
- `activity_log` - User activity tracking
- `quality_metrics` - Historical quality data
- `users` - User management (for future auth)
- `comments` - Review comments (for future collaboration)

## Environment Variables

- `PORT` - Server port (default: 3001)
- `DATABASE_PATH` - SQLite database file path
- `CLIENT_URL` - Frontend URL for CORS (default: http://localhost:3000)

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React SPA     │    │  Express API    │    │   Mock Trio     │
│                 │    │                 │    │   Engine        │
│ • Dashboard     │◄──►│ • REST API      │◄──►│ • Planner       │
│ • Real-time UI  │    │ • WebSockets    │    │ • Generator     │
│ • Code Editor   │    │ • Database      │    │ • Evaluator     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   SQLite DB     │
                       │                 │
                       │ • Reviews       │
                       │ • Activity      │
                       │ • Metrics       │
                       └─────────────────┘
```

This is a complete, self-contained application that demonstrates the power of AI-driven code review with real-time collaboration features.