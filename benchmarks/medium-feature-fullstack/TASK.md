# Task: Add Real-Time Notifications System

## Overview
Add a complete real-time notifications system to the existing dashboard application. Users should receive notifications in real-time via WebSocket and be able to manage them through the UI and API.

## Requirements

### Backend

#### Notification Model (SQLite)
- Create a notifications table: id, user_id (FK), title, message, type (info/success/warning/error), read (boolean), created_at

#### WebSocket Server
- Add WebSocket support to the Express server (use `ws` library)
- Authenticate WebSocket connections using JWT token (passed as query param or in first message)
- Broadcast notifications to connected users (only to the target user)
- Handle connection/disconnection gracefully

#### New API Endpoints
1. **POST /api/notifications** — Create a new notification (admin or system)
2. **GET /api/notifications** — Get current user's notifications (with pagination)
3. **PATCH /api/notifications/:id** — Mark notification as read
4. **GET /api/notifications/unread-count** — Get current user's unread notification count

### Frontend

#### NotificationBell Component
- Add to Header component
- Shows bell icon with unread count badge
- Clicking opens notification dropdown
- Badge disappears when count is 0

#### NotificationDropdown Component
- Shows list of recent notifications
- Each notification shows: title, message, time ago, read/unread indicator
- Click to mark as read
- "Mark all as read" button
- Link to "View all notifications" page

#### WebSocket Integration
- Connect to WebSocket on app mount (when authenticated)
- Update notification count in real-time
- Show toast/popup for new notifications
- Reconnect on disconnect

### Constraints
- All existing tests must continue to pass
- WebSocket must authenticate connections
- Notifications are per-user (users only see their own)
- Follow existing code style and patterns
- Add `ws` package to server dependencies
