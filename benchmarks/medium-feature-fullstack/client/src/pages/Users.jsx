import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import api from '../services/api';
import UserTable from '../components/UserTable';

export default function Users() {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    if (!isAdmin) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function fetchUsers() {
      try {
        setLoading(true);
        setError(null);

        const params = { page, limit: 20 };
        if (search.trim()) {
          params.search = search.trim();
        }

        const response = await api.get('/api/users', { params });

        if (!cancelled) {
          setUsers(response.data.users);
          setTotalPages(response.data.totalPages);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.response?.data?.error || 'Failed to load users.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchUsers();
    return () => { cancelled = true; };
  }, [isAdmin, page, search]);

  if (!isAdmin) {
    return (
      <div style={styles.accessDenied}>
        <div style={styles.lockIcon}>🔒</div>
        <h2 style={styles.accessTitle}>Access Denied</h2>
        <p style={styles.accessMessage}>
          You need administrator privileges to view the users list.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div style={styles.pageHeader}>
        <h1 style={styles.pageTitle}>Users</h1>
        <span style={styles.badge}>{users.length} users</span>
      </div>

      {/* Search */}
      <div style={styles.searchContainer}>
        <input
          type="text"
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          style={styles.searchInput}
        />
      </div>

      {/* Error */}
      {error && (
        <div style={styles.errorBanner}>
          <p>{error}</p>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div style={styles.loadingContainer}>
          <p>Loading users...</p>
        </div>
      ) : (
        <>
          <UserTable
            users={users}
            onRowClick={(u) => console.log('User clicked:', u.id)}
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={styles.pagination}>
              <button
                style={{
                  ...styles.pageButton,
                  opacity: page <= 1 ? 0.5 : 1,
                }}
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                ← Previous
              </button>
              <span style={styles.pageInfo}>
                Page {page} of {totalPages}
              </span>
              <button
                style={{
                  ...styles.pageButton,
                  opacity: page >= totalPages ? 0.5 : 1,
                }}
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

const styles = {
  pageHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '24px',
  },
  pageTitle: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#1a202c',
  },
  badge: {
    backgroundColor: '#e2e8f0',
    color: '#4a5568',
    padding: '4px 12px',
    borderRadius: '999px',
    fontSize: '13px',
    fontWeight: '500',
  },
  searchContainer: {
    marginBottom: '20px',
  },
  searchInput: {
    width: '100%',
    maxWidth: '400px',
    padding: '10px 16px',
    fontSize: '14px',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    outline: 'none',
    backgroundColor: '#fff',
  },
  loadingContainer: {
    display: 'flex',
    justifyContent: 'center',
    padding: '48px',
    color: '#718096',
  },
  errorBanner: {
    backgroundColor: '#fff5f5',
    border: '1px solid #fed7d7',
    borderRadius: '8px',
    padding: '12px 16px',
    color: '#c53030',
    marginBottom: '16px',
  },
  pagination: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '16px',
    marginTop: '20px',
    padding: '16px 0',
  },
  pageButton: {
    padding: '8px 16px',
    backgroundColor: '#fff',
    border: '1px solid #e2e8f0',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
    color: '#4a5568',
  },
  pageInfo: {
    fontSize: '14px',
    color: '#718096',
  },
  accessDenied: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '400px',
    textAlign: 'center',
  },
  lockIcon: {
    fontSize: '48px',
    marginBottom: '16px',
  },
  accessTitle: {
    fontSize: '24px',
    fontWeight: '600',
    color: '#2d3748',
    marginBottom: '8px',
  },
  accessMessage: {
    color: '#718096',
    fontSize: '16px',
  },
};
