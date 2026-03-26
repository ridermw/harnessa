import React from 'react';

function formatValue(value, prefix) {
  if (typeof value !== 'number') return value;

  const formatted = value >= 1000
    ? value.toLocaleString('en-US', { maximumFractionDigits: 2 })
    : String(value);

  return prefix ? `${prefix}${formatted}` : formatted;
}

export default function StatsCard({ title, value, color, icon, prefix }) {
  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <span style={styles.icon}>{icon}</span>
        <div
          style={{
            ...styles.indicator,
            backgroundColor: color || '#4a90d9',
          }}
        />
      </div>
      <div style={styles.body}>
        <p style={styles.value}>{formatValue(value, prefix)}</p>
        <p style={styles.title}>{title}</p>
      </div>
    </div>
  );
}

const styles = {
  card: {
    backgroundColor: '#fff',
    borderRadius: '12px',
    padding: '20px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    transition: 'box-shadow 0.2s, transform 0.2s',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '16px',
  },
  icon: {
    fontSize: '28px',
  },
  indicator: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  body: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  value: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#1a202c',
    lineHeight: '1.2',
    margin: 0,
  },
  title: {
    fontSize: '14px',
    color: '#718096',
    fontWeight: '500',
    margin: 0,
  },
};
