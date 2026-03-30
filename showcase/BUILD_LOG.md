# Build Log — How the Trio Built This App

> This showcase app was built using the Harnessa Planner→Generator→Evaluator
> trio pattern to demonstrate the framework's capabilities. This document
> records each phase of the build process.

## The Prompt (5 sentences)

> Build a full-stack web application where teams can submit code snippets for AI-powered review. The app should:
>
> 1. Accept code paste or GitHub PR URL
> 2. Run a Planner→Generator→Evaluator trio analysis on the submitted code
> 3. Display scores, bugs found, and improvement suggestions in real-time
> 4. Show a live activity feed of reviews happening across the team
> 5. Track quality trends over time with charts
>
> Stack: React frontend + Express/Node backend + SQLite. Self-contained, runs locally.

## Phase 1: Planner

**Model:** claude-sonnet-4 via Copilot CLI
**Input:** TASK.md (12 lines)
**Output:** spec.md (520 lines)

### What the Planner Produced

The planner expanded a 12-line prompt into a comprehensive specification with:
- **12 user stories** across 3 personas (Developer, Team Lead, Product Manager)
- **18 API endpoints** across 5 domains (Auth, Reviews, GitHub, Analytics, Activity)
- **19 UI component specs** with TypeScript interfaces
- **5 database tables** with full schemas and indexes
- **7 acceptance criteria sections** totaling 40+ individual requirements

Selected user stories:
- *"As a Developer, I want to paste code snippets and get instant AI-powered feedback"*
- *"As a Team Lead, I want to monitor team code quality metrics"*
- *"As a Product Manager, I want visibility into development velocity and quality"*

### Planner's Ambition

The planner went well beyond the prompt in several ways:

1. **Three user personas** — the prompt mentioned "teams" once; the planner invented Developer, Team Lead, and Product Manager personas with distinct needs.
2. **GitHub OAuth + JWT auth** — the prompt said nothing about authentication. The planner added a full auth system with GitHub OAuth integration.
3. **Collaborative tools** — comments, annotations, and team discussions were added despite no mention of collaboration features.
4. **Docker containerization** — deployment infrastructure specs that weren't requested.
5. **Export functionality** — JSON and CSV data export for review reports.
6. **19 UI components** — from `ErrorBoundary` to `TeamLeaderboard` to `NotificationCenter`, far beyond what "display scores and bugs" requires.

This validates the article's observation that *"the planner should dream bigger than the user"* — the 12-line prompt became a 520-line spec with features the user never asked for but would want.

## Phase 2: Generator (Iteration 1)

**Model:** claude-sonnet-4 via Copilot CLI
**Input:** spec.md
**Output:** Single 1,206-line `index.ts` monolith

*Git commit:* `882b87b` — "feat: Dream project — AI Code Review Dashboard"

### What Happened

The generator crammed the entire application into a single TypeScript file — Express server, database layer, WebSocket handling, trio analysis service, and a ~630-line HTML string template with inline React (loaded via CDN `<script>` tags and Babel standalone transpilation).

The 10 files committed were:
- `index.ts` (1,206 lines — the entire app)
- `package.json` with 10 dependencies
- `spec.md`, `TASK.md`, `README.md`
- `tsconfig.json`, `tsconfig.server.json`
- `sql.js.d.ts` (type definitions)
- `start.sh` (launch script)
- `package-lock.json`

Key problems:
- **No component separation** — server, client, database, and WebSocket all in one file
- **React via CDN + Babel standalone** — not real JSX components, but a massive HTML string template with inline `<script type="text/babel">` blocks
- **12 references to React** in the file, but zero `.jsx`/`.tsx` component files
- **No tests at all**
- **Untestable, unmaintainable** — modifying one feature risks breaking everything

### Self-Assessment

A solo agent would have shipped this. The monolith technically worked — it defined all the database tables, had REST endpoints, included WebSocket support, and rendered a UI. The generator's implicit self-evaluation was "this satisfies the spec." This is precisely the self-evaluation failure the article describes: the agent can't objectively assess its own architectural quality.

## Phase 3: Evaluator (Iteration 1)

**Verdict:** FAIL

**Key Findings:**
1. **Architecture:** Single file with 1,206 lines — violates every code quality and maintainability principle the spec's own acceptance criteria demand
2. **Client:** React UI rendered as an inline HTML string template with CDN-loaded Babel — not real JSX components, not buildable, not testable
3. **Structure:** No file separation — 10 files total, only 1 containing actual application code
4. **Testing:** Zero test files despite spec requiring unit, integration, and E2E tests
5. **Developer Experience:** No `npm run dev` with hot reload, no Vite, no Tailwind build pipeline

### Evaluator Feedback

The evaluator's feedback was specific and actionable: rebuild with separate `server/` and `client/` directories, real React JSX components compiled by Vite, proper file structure with 30+ files, and actual test coverage.

## Phase 4: Generator (Iteration 2)

**Model:** claude-sonnet-4 via Copilot CLI
**Input:** spec.md + evaluator feedback
**Output:** 32-file full-stack application

*Git commit:* `cd42e3b` — "feat: Rebuild showcase as proper full-stack app"

### What Changed

The generator completely rebuilt the application. The diff: **+4,335 lines / −2,973 lines** across 36 file changes (including deletions of iter 1 files).

| Aspect | Iteration 1 | Iteration 2 |
|--------|------------|------------|
| Files | 1 (`index.ts`) | 32 source files |
| Architecture | Monolith | `server/` + `client/` workspaces |
| Client framework | CDN React + Babel string template | Real React 18 + Vite + Tailwind CSS |
| Database | sql.js (in-memory, correct) | sql.js (persisted, still correct) |
| Components | 0 `.jsx` files | 6 (Header, ScoreCard, TrioProgress, ActivityFeed, CodeEditor, BugList) |
| Pages | 0 | 4 (Dashboard, NewReview, ReviewDetail, Analytics) |
| Routing | Inline string HTML | React Router with 4 routes |
| Real-time | Inline Socket.IO | Dedicated `useSocket` hook + `websocket.js` |
| Code analysis | Basic stubs | 7 real heuristics (console.log, secrets, TODOs, error handling, nesting, magic numbers, long functions) |
| Tests | 0 | 7 API integration tests |
| Dev workflow | `start.sh` | `npm run dev` (concurrent server + Vite) |

### Key Architectural Decisions in Iteration 2

- **npm workspaces** — root `package.json` manages `server/` and `client/` as workspaces
- **sql.js (pure JS)** — zero native dependencies, `npm install` works everywhere
- **Real heuristics in `trio.js`** — the trio service runs actual regex-based code analysis (not just random scores), detecting 7 categories of code issues
- **WebSocket progress** — each trio phase emits `trio_phase` events so the UI shows live Planner→Generator→Evaluator progress
- **Dark theme** — professional UI with Harnessa purple (`#7C3AED`) accent

## Phase 5: Evaluator (Iteration 2)

**Verdict:** PASS

**Verified:**
- `npm install` ✅ — zero native dependencies, clean install
- `npm run build` ✅ — Vite builds React client to `client/dist/`
- Server starts ✅ — Express on `:3001`, serves API + built client
- `GET /api/health` ✅ — returns health status
- `POST /api/reviews` ✅ — trio analysis runs, returns scores and bugs
- Real code analysis ✅ — detects console.log, hardcoded secrets, TODOs, missing error handling, deep nesting, magic numbers, long functions
- WebSocket events ✅ — live `trio_phase` progress updates
- 7 API tests ✅ — health, submit review, list reviews, get review, analytics

## Lessons Demonstrated

### 1. The Evaluator Caught What Solo Would Have Shipped

The first iteration was a functioning application — it had endpoints, a database, WebSocket support, and rendered a UI. A solo agent would have declared victory. The evaluator looked at the 1,206-line monolith with its inline HTML string template and said *"no, this isn't acceptable for a showcase."* This is exactly the self-evaluation failure described in the Anthropic article.

### 2. Feedback Drove a Complete Rebuild

Iteration 1 → Iteration 2 wasn't incremental polish — it was a total rebuild. 1 file → 32 files. CDN script tags → Vite build pipeline. String template → real JSX. No tests → 7 tests. The evaluator's feedback was specific enough that the generator knew exactly what to fix and produced a categorically different result.

### 3. The Spec Survived Both Iterations

The planner's 520-line spec guided both the monolith and the rebuild. Both iterations implemented the same features (reviews, analytics, activity feed, trio analysis) — the spec defined *what* to build while the evaluator ensured *how* it was built met quality standards. This separation of concerns is the trio pattern's core strength.

### 4. Real Heuristics Over Mock Data

Iteration 2's trio service (`server/services/trio.js`) runs genuine code analysis — regex-based detection of 7 issue categories with severity scoring, not random number generation. The evaluator phase computes weighted quality scores based on actual findings. This makes the showcase a credible demonstration rather than a Potemkin village.

## Timeline

| Phase | Output |
|-------|--------|
| Planner | 520-line spec.md with 12 user stories, 18 endpoints, 5 tables |
| Generator (iter 1) | 1-file, 1,206-line TypeScript monolith (**rejected**) |
| Evaluator (iter 1) | **FAIL** — monolith architecture, no real components, no tests |
| Generator (iter 2) | 32-file full-stack app with React + Express + sql.js |
| Evaluator (iter 2) | **PASS** — all checks green |

## Connecting to RESULTS.md

This showcase build directly demonstrates findings from the Harnessa benchmark experiments:

- **Section 6.1** confirms *"Separating generator from evaluator is a strong lever"* — the evaluator rejected iter 1 and the generator fixed it, just like Benchmark 4 where scores went from 3.25 → 8.0 after feedback.
- **Section 6.2** notes *"The planner's primary value is structure, not scope expansion"* — the planner's 520-line spec gave the generator a clear roadmap, and the spec's structure was what made iter 2's rebuild possible without re-planning.
- **Section 6.1** confirms *"Solo agents exhibit self-evaluation failure"* — the iter 1 monolith is exactly the kind of output a solo agent would ship and call done.
