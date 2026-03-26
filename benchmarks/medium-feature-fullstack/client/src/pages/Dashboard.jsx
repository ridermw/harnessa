import React, { useState, useEffect } from 'react';
import api from '../services/api';
import StatsCard from '../components/StatsCard';

const STAT_CARDS_CONFIG = [
  { key: 'total_users', title: 'Total Users', color: '#4a90d9', icon: '👥' },
  { key: 'active_sessions', title: 'Active Sessions', color: '#50c878', icon: '🔗' },
  { key: 'total_orders', title: 'Total Orders', color: '#f5a623', icon: '📦' },
  { key: 'revenue', title: 'Revenue', color: '#e74c3c', icon: '💰', prefix: '$' },
];

function formatTimeAgo(timestamp) {
  const seconds = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function getActivityIcon(type) {
  const icons = {
    user_registered: '🆕',
    order_placed: '🛒',
    payment_received: '💳',
    user_login: '🔑',
    settings_updated: '⚙️',
    order_shipped: '🚚',
    user_updated: '✏️',
    report_generated: '📊',
  };
  return icons[type] || '📋';
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchDashboardData() {
      try {
        setLoading(true);
        setError(null);

        const [statsRes, activityRes] = await Promise.all([
          api.get('/api/dashboard'),
          api.get('/api/dashboard/activity'),
        ]);

        if (!cancelled) {
          setStats(statsRes.data.stats);
          setActivities(activityRes.data.activities);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.response?.data?.error || 'Failed to load dashboard data.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchDashboardData();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div style={styles.loadingContainer}>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.errorContainer}>
        <h3>Error</h3>
        <p>{error}</p>
        <button style={styles.retryButton} onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <h1 style={styles.pageTitle}>Dashboard</h1>

      {/* Stats Cards */}
      <div style={styles.statsGrid}>
        {STAT_CARDS_CONFIG.map((config) => {
          const stat = stats?.[config.key];
          return (
            <StatsCard
              key={config.key}
              title={config.title}
              value={stat?.value ?? 0}
              color={config.color}
              icon={config.icon}
              prefix={config.prefix}
            />
          );
        })}
      </div>

      {/* Recent Activity */}
      <div style={styles.activitySection}>
        <h2 style={styles.sectionTitle}>Recent Activity</h2>
        <div style={styles.activityList}>
          {activities.length === 0 ? (
            <p style={styles.emptyMessage}>No recent activity.</p>
          ) : (
            activities.map((activity) => (
              <div key={activity.id} style={styles.activityItem}>
                <span style={styles.activityIcon}>
                  {getActivityIcon(activity.type)}
                </span>
                <div style={styles.activityContent}>
                  <p style={styles.activityMessage}>{activity.message}</p>
                  <span style={styles.activityTime}>
                    {formatTimeAgo(activity.timestamp)}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  pageTitle: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#1a202c',
    marginBottom: '24px',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: '20px',
    marginBottom: '32px',
  },
  activitySection: {
    backgroundColor: '#fff',
    borderRadius: '12px',
    padding: '24px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  sectionTitle: {
    fontSize: '20px',
    fontWeight: '600',
    color: '#1a202c',
    marginBottom: '16px',
  },
  activityList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  activityItem: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
    padding: '12px',
    borderRadius: '8px',
    backgroundColor: '#f7fafc',
    transition: 'background-color 0.15s',
  },
  activityIcon: {
    fontSize: '20px',
    flexShrink: 0,
    width: '32px',
    textAlign: 'center',
  },
  activityContent: {
    flex: 1,
    minWidth: 0,
  },
  activityMessage: {
    fontSize: '14px',
    color: '#2d3748',
    marginBottom: '2px',
  },
  activityTime: {
    fontSize: '12px',
    color: '#a0aec0',
  },
  loadingContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '300px',
    color: '#718096',
    fontSize: '16px',
  },
  errorContainer: {
    backgroundColor: '#fff5f5',
    border: '1px solid #fed7d7',
    borderRadius: '12px',
    padding: '24px',
    textAlign: 'center',
    color: '#c53030',
  },
  retryButton: {
    marginTop: '12px',
    padding: '8px 20px',
    backgroundColor: '#4a90d9',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  emptyMessage: {
    color: '#a0aec0',
    textAlign: 'center',
    padding: '24px',
  },
};
