import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const isAdmin = user?.role === 'admin';

  const menuItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    ...(isAdmin
      ? [{ path: '/users', label: 'Users', icon: '👥' }]
      : []),
    { path: '/settings', label: 'Settings', icon: '⚙️', disabled: true },
  ];

  return (
    <aside style={styles.sidebar}>
      <nav style={styles.nav}>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <button
              key={item.path}
              onClick={() => !item.disabled && navigate(item.path)}
              disabled={item.disabled}
              style={{
                ...styles.menuItem,
                ...(isActive ? styles.menuItemActive : {}),
                ...(item.disabled ? styles.menuItemDisabled : {}),
              }}
            >
              <span style={styles.menuIcon}>{item.icon}</span>
              <span style={styles.menuLabel}>{item.label}</span>
              {item.disabled && (
                <span style={styles.comingSoon}>Soon</span>
              )}
            </button>
          );
        })}
      </nav>

      <div style={styles.footer}>
        <p style={styles.version}>v1.0.0</p>
      </div>
    </aside>
  );
}

const styles = {
  sidebar: {
    width: '240px',
    minHeight: 'calc(100vh - 64px)',
    backgroundColor: '#fff',
    borderRight: '1px solid #e2e8f0',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    padding: '16px 0',
    flexShrink: 0,
  },
  nav: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
    padding: '0 12px',
  },
  menuItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '10px 14px',
    fontSize: '14px',
    fontWeight: '500',
    color: '#4a5568',
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    textAlign: 'left',
    width: '100%',
    transition: 'all 0.15s',
  },
  menuItemActive: {
    color: '#4a90d9',
    backgroundColor: '#ebf4ff',
    fontWeight: '600',
  },
  menuItemDisabled: {
    color: '#cbd5e0',
    cursor: 'not-allowed',
  },
  menuIcon: {
    fontSize: '18px',
    width: '24px',
    textAlign: 'center',
  },
  menuLabel: {
    flex: 1,
  },
  comingSoon: {
    fontSize: '10px',
    fontWeight: '600',
    color: '#a0aec0',
    backgroundColor: '#f7fafc',
    padding: '2px 6px',
    borderRadius: '4px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  footer: {
    padding: '16px 24px',
    borderTop: '1px solid #f0f0f0',
  },
  version: {
    fontSize: '12px',
    color: '#cbd5e0',
  },
};
