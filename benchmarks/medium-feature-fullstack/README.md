# Dashboard Application

A full-stack dashboard application built with React and Express.

## Setup

```bash
npm install
```

## Development

```bash
npm run dev
```

This starts both the server (port 3001) and client (port 5173).

## Test

```bash
npm test
```

## Project Structure

- `client/` — React frontend (Vite)
- `server/` — Express backend
- `tests/` — Server integration tests

## API Endpoints

### Auth
- `POST /api/auth/login` — Login
- `POST /api/auth/register` — Register

### Dashboard
- `GET /api/dashboard` — Dashboard statistics
- `GET /api/dashboard/activity` — Recent activity

### Users
- `GET /api/users` — List users (admin)
- `GET /api/users/:id` — Get user
- `PUT /api/users/:id` — Update user
- `GET /api/users/me/profile` — Current user profile

## Default Credentials

- Admin: admin@example.com / password123
- User: user1@example.com / password123
