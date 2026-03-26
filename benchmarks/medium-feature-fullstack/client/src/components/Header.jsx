import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  const navLinks = [
    { path: '/', label: 'Dashboard' },
    { path: '/users', label: 'Users' },
  ];

  return (
    <header style={styles.header}>
      <div style={styles.left}>
        <h1 style={styles.logo} onClick={() => navigate('/')}>
          📊 Dashboard
        </h1>
        <nav style={styles.nav}>
          {navLinks.map((link) => (
            <button
              key={link.path}
              onClick={() => navigate(link.path)}
              style={{
                ...styles.navLink,
                ...(location.pathname === link.path ? styles.navLinkActive : {}),
              }}
            >
              {link.label}
            </button>
          ))}
        </nav>
      </div>

      <div style={styles.right}>
        {user && (
          <div style={styles.userInfo}>
            <div style={styles.avatar}>
              {user.username?.charAt(0).toUpperCase() || '?'}
            </div>
            <div style={styles.userDetails}>
              <span style={styles.username}>{user.username}</span>
              <span style={styles.role}>{user.role}</span>
            </div>
          </div>
        )}
        <button style={styles.logoutButton} onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}

const styles = {
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: '64px',
    padding: '0 24px',
    backgroundColor: '#fff',
    borderBottom: '1px solid #e2e8f0',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
    zIndex: 100,
  },
  left: {
    display: 'flex',
    alignItems: 'center',
    gap: '32px',
  },
  logo: {
    fontSize: '20px',
    fontWeight: '700',
    color: '#1a202c',
    cursor: 'pointer',
    margin: 0,
  },
  nav: {
    display: 'flex',
    gap: '4px',
  },
  navLink: {
    padding: '8px 14px',
    fontSize: '14px',
    fontWeight: '500',
    color: '#718096',
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'all 0.15s',
  },
  navLinkActive: {
    color: '#4a90d9',
    backgroundColor: '#ebf4ff',
  },
  right: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  avatar: {
    width: '36px',
    height: '36px',
    borderRadius: '50%',
    backgroundColor: '#4a90d9',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '15px',
    fontWeight: '600',
  },
  userDetails: {
    display: 'flex',
    flexDirection: 'column',
  },
  username: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#2d3748',
    lineHeight: '1.2',
  },
  role: {
    fontSize: '11px',
    color: '#a0aec0',
    textTransform: 'capitalize',
  },
  logoutButton: {
    padding: '6px 14px',
    fontSize: '13px',
    fontWeight: '500',
    color: '#718096',
    backgroundColor: '#f7fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'all 0.15s',
  },
};
