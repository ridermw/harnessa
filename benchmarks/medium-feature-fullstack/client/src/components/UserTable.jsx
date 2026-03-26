import React, { useState } from 'react';

function formatDate(dateStr) {
  if (!dateStr) return 'Never';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function UserTable({ users, onRowClick }) {
  const [sortField, setSortField] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');

  function handleSort(field) {
    if (sortField === field) {
      setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  }

  const sortedUsers = [...users].sort((a, b) => {
    const aVal = a[sortField] ?? '';
    const bVal = b[sortField] ?? '';

    let comparison = 0;
    if (typeof aVal === 'string') {
      comparison = aVal.localeCompare(bVal);
    } else {
      comparison = aVal - bVal;
    }

    return sortDirection === 'asc' ? comparison : -comparison;
  });

  const columns = [
    { key: 'username', label: 'Name' },
    { key: 'email', label: 'Email' },
    { key: 'role', label: 'Role' },
    { key: 'last_login', label: 'Last Login' },
  ];

  function getSortIndicator(field) {
    if (sortField !== field) return '';
    return sortDirection === 'asc' ? ' ↑' : ' ↓';
  }

  if (users.length === 0) {
    return (
      <div style={styles.empty}>
        <p>No users found.</p>
      </div>
    );
  }

  return (
    <div style={styles.tableContainer}>
      <table style={styles.table}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                style={styles.th}
                onClick={() => handleSort(col.key)}
              >
                {col.label}{getSortIndicator(col.key)}
              </th>
            ))}
            <th style={styles.th}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {sortedUsers.map((u) => (
            <tr
              key={u.id}
              style={styles.tr}
              onClick={() => onRowClick?.(u)}
            >
              <td style={styles.td}>
                <div style={styles.nameCell}>
                  <div style={styles.avatar}>
                    {u.username?.charAt(0).toUpperCase() || '?'}
                  </div>
                  <span style={styles.username}>{u.username}</span>
                </div>
              </td>
              <td style={styles.td}>
                <span style={styles.email}>{u.email}</span>
              </td>
              <td style={styles.td}>
                <span
                  style={{
                    ...styles.roleBadge,
                    ...(u.role === 'admin' ? styles.adminBadge : styles.userBadge),
                  }}
                >
                  {u.role}
                </span>
              </td>
              <td style={styles.td}>
                <span style={styles.lastLogin}>{formatDate(u.last_login)}</span>
              </td>
              <td style={styles.td}>
                <button
                  style={styles.actionButton}
                  onClick={(e) => {
                    e.stopPropagation();
                    onRowClick?.(u);
                  }}
                >
                  View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const styles = {
  tableContainer: {
    backgroundColor: '#fff',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    overflow: 'hidden',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    padding: '14px 20px',
    textAlign: 'left',
    fontSize: '12px',
    fontWeight: '600',
    color: '#718096',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    borderBottom: '1px solid #e2e8f0',
    backgroundColor: '#fafbfc',
    cursor: 'pointer',
    userSelect: 'none',
  },
  tr: {
    cursor: 'pointer',
    transition: 'background-color 0.15s',
    borderBottom: '1px solid #f0f0f0',
  },
  td: {
    padding: '14px 20px',
    fontSize: '14px',
    color: '#2d3748',
  },
  nameCell: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  avatar: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    backgroundColor: '#4a90d9',
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '13px',
    fontWeight: '600',
    flexShrink: 0,
  },
  username: {
    fontWeight: '600',
  },
  email: {
    color: '#718096',
  },
  roleBadge: {
    display: 'inline-block',
    padding: '3px 10px',
    borderRadius: '999px',
    fontSize: '12px',
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  adminBadge: {
    backgroundColor: '#ebf4ff',
    color: '#4a90d9',
  },
  userBadge: {
    backgroundColor: '#f0fff4',
    color: '#38a169',
  },
  lastLogin: {
    color: '#a0aec0',
    fontSize: '13px',
  },
  actionButton: {
    padding: '5px 12px',
    fontSize: '13px',
    fontWeight: '500',
    color: '#4a90d9',
    backgroundColor: '#ebf4ff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
  },
  empty: {
    display: 'flex',
    justifyContent: 'center',
    padding: '48px',
    color: '#a0aec0',
    backgroundColor: '#fff',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
};
