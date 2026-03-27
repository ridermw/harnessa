# Harnessa Code Review Dashboard

A real-time code review dashboard showcasing the **Planner → Generator → Evaluator** trio pattern with actual code analysis heuristics.

## Features

- **Real-time Trio Analysis**: Planner → Generator → Evaluator pipeline with live WebSocket progress
- **Real Code Heuristics**: Detects console.log artifacts, TODO/FIXME, hardcoded secrets, missing error handling, deep nesting, magic numbers, and long functions
- **4-Page React App**: Dashboard, New Review, Review Detail, Analytics
- **Live Activity Feed**: WebSocket-powered real-time event stream
- **Dark Theme**: Professional UI with Harnessa purple (#7C3AED) accent
- **Zero Native Deps**: Uses sql.js (pure JS SQLite) — no node-gyp required

## Tech Stack

- **Server**: Express.js + Socket.IO + sql.js (pure JavaScript SQLite)
- **Client**: React 18 + Vite + Tailwind CSS + React Router
- **Real-time**: Socket.IO for live trio progress and activity feed
- **Testing**: Node.js built-in test runner + API tests

## Quick Start

```bash
cd showcase
npm install        # installs server + client deps (workspaces)
npm run dev        # starts server (:3001) + client (:5173) concurrently
```

## Production Build

```bash
npm run build      # builds React client to client/dist/
npm start          # serves API + built client on :3001
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/reviews` | Submit code for trio analysis |
| `GET` | `/api/reviews` | List reviews (paginated) |
| `GET` | `/api/reviews/:id` | Single review with scores + bugs |
| `GET` | `/api/analytics` | Aggregate stats, trends, by-language breakdown |

## WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `trio_phase` | server → client | Phase status update (running/done) |
| `review_complete` | server → client | Full analysis results |
| `activity` | server → client | Activity feed event |

## Testing

```bash
# Start server, then run tests
npm start &
npm test
```

## Architecture

```
showcase/
├── server/                   Express API + sql.js + Socket.IO
│   ├── routes/               REST endpoints (reviews, analytics, health)
│   ├── services/trio.js      Simulated trio with real heuristics
│   └── websocket.js          Socket.IO broadcasting
├── client/                   React + Vite + Tailwind
│   └── src/
│       ├── pages/            Dashboard, NewReview, ReviewDetail, Analytics
│       ├── components/       Header, ScoreCard, TrioProgress, ActivityFeed, CodeEditor, BugList
│       └── hooks/            useSocket (WebSocket hook)
└── tests/                    API integration tests
```