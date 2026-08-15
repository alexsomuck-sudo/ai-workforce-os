import React from 'react';
import { useApi } from '../hooks/useApi';
import api from '../services/api';
import { HealthStatus } from '../types';

export default function Dashboard() {
  const { data: health, loading, error, refetch } = useApi(healthFetcher);

  function healthFetcher() {
    return api.health();
  }

  const statusColors: Record<string, string> = {
    healthy: '#22c55e',
    degraded: '#eab308',
    unhealthy: '#ef4444',
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={sectionTitleStyle}>Dashboard</h2>
        <button onClick={refetch} style={refreshBtnStyle}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* System Status */}
      <section style={cardStyle}>
        <h3 style={cardTitleStyle}>System Status</h3>
        {loading && !health && <p style={{ color: '#94a3b8' }}>Loading system status...</p>}
        {error && <p style={{ color: '#ef4444' }}>Error: {error}</p>}
        {health && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
          }}>
            <StatusCard
              label="Status"
              value={health.status}
              color={statusColors[health.status] || '#64748b'}
            />
            <StatusCard label="Version" value={health.version} color="#3b82f6" />
            {Object.entries(health.services).map(([key, value]) => (
              <StatusCard
                key={key}
                label={key}
                value={value}
                color={value === 'healthy' ? '#22c55e' : '#ef4444'}
              />
            ))}
          </div>
        )}
      </section>

      {/* Quick Stats */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginTop: '1.5rem' }}>
        <QuickCard title="Production Niche" value="FuturePulse AI" subtitle="Global Mystery & Wisdom" />
        <QuickCard title="Auto-Post Status" value="Active" subtitle="4 Posts / Day" />
        <QuickCard title="Connected Channel" value="@AI-Pro-Workflow" subtitle="YouTube Data API v3" />
        <QuickCard title="Active Character" value="Aera" subtitle="AI Oracle / Future Guide" />
      </section>

      {/* System Info */}
      <section style={{ ...cardStyle, marginTop: '1.5rem' }}>
        <h3 style={cardTitleStyle}>System Information</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
          <InfoRow label="Application" value="AI Workforce OS" />
          <InfoRow label="Backend" value="FastAPI + Python 3.11" />
          <InfoRow label="Frontend" value="React 18 + TypeScript" />
          <InfoRow label="Database" value="SQLAlchemy (SQLite/PostgreSQL)" />
          <InfoRow label="LLM Providers" value="OpenAI, Gemini, DeepSeek" />
          <InfoRow label="TTS Providers" value="OpenAI TTS, Deepgram" />
        </div>
      </section>
    </div>
  );
}

function StatusCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ background: '#0f172a', borderRadius: '8px', padding: '1rem', borderLeft: `3px solid ${color}` }}>
      <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '0.25rem' }}>{label}</div>
      <div style={{ fontSize: '1.25rem', fontWeight: 700, color }}>{value}</div>
    </div>
  );
}

function QuickCard({ title, value, subtitle }: { title: string; value: string; subtitle: string }) {
  return (
    <div style={cardStyle}>
      <div style={{ fontSize: '0.875rem', color: '#94a3b8', marginBottom: '0.5rem' }}>{title}</div>
      <div style={{ fontSize: '2rem', fontWeight: 700, color: '#f8fafc' }}>{value}</div>
      <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.5rem' }}>{subtitle}</div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid #1e293b' }}>
      <span style={{ color: '#94a3b8' }}>{label}</span>
      <span style={{ color: '#e2e8f0', fontWeight: 500 }}>{value}</span>
    </div>
  );
}

const sectionTitleStyle: React.CSSProperties = {
  fontSize: '1.75rem',
  fontWeight: 700,
  marginBottom: '1.5rem',
};

const cardStyle: React.CSSProperties = {
  background: '#1e293b',
  borderRadius: '12px',
  padding: '1.5rem',
};

const cardTitleStyle: React.CSSProperties = {
  fontSize: '1.125rem',
  fontWeight: 600,
  marginBottom: '1rem',
  color: '#f8fafc',
};

const refreshBtnStyle: React.CSSProperties = {
  padding: '0.5rem 1rem',
  borderRadius: '6px',
  border: '1px solid #334155',
  background: 'transparent',
  color: '#94a3b8',
  cursor: 'pointer',
  fontSize: '0.875rem',
  fontWeight: 500,
  transition: 'all 0.2s',
};
