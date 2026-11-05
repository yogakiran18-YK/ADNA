import React, { useState, useEffect, useCallback } from 'react';
import { Database, CheckCircle2, RefreshCw, HardDrive } from 'lucide-react';

export default function KaggleDatasetsHub({ apiBase }) {
  const [datasets, setDatasets] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${apiBase}/api/v1/market/kaggle/status`);
      if (res.ok) {
        const data = await res.json();
        setDatasets(data);
      }
    } catch (err) {
      console.error('Failed to fetch dataset status', err);
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      
      {/* HEADER BANNER */}
      <div className="panel" style={{
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.95))',
        border: '1px solid rgba(56, 189, 248, 0.3)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>
            <Database size={24} color="#38bdf8" />
            ADNA Kaggle Data Registry & Provenance
          </div>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Multi-Agent Grounding Datasets: Raw CSV repositories mapped directly to agent execution pipelines.
          </p>
        </div>

        <button 
          onClick={fetchStatus}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '0.5rem 1rem',
            backgroundColor: 'rgba(56, 189, 248, 0.1)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            color: '#38bdf8',
            borderRadius: '0.5rem'
          }}
        >
          <RefreshCw size={16} className={loading ? 'spin-icon' : ''} />
          Refresh Registry
        </button>
      </div>

      {/* DATASETS GRID */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: '1.25rem'
      }}>
        {datasets && Object.entries(datasets).map(([key, info]) => (
          <div key={key} className="dataset-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
              <div style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                color: '#818cf8',
                backgroundColor: 'rgba(129, 140, 248, 0.12)',
                padding: '0.2rem 0.6rem',
                borderRadius: '4px',
                display: 'inline-block'
              }}>
                {info.agent}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#10b981', fontSize: '0.8rem', fontWeight: 600 }}>
                <CheckCircle2 size={16} />
                Connected
              </div>
            </div>

            <div style={{ fontWeight: 600, fontSize: '1.05rem', color: 'var(--text-main)', marginBottom: '0.25rem' }}>
              {key.replace('_', ' ').toUpperCase()}
            </div>

            <div style={{ fontSize: '0.8rem', color: '#38bdf8', marginBottom: '1rem', wordBreak: 'break-all' }}>
              {info.source}
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '0.5rem',
              padding: '0.75rem',
              backgroundColor: 'rgba(0,0,0,0.25)',
              borderRadius: '0.375rem',
              fontSize: '0.8rem',
              marginBottom: '0.75rem'
            }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Records:</span>{' '}
                <strong style={{ color: 'var(--text-main)' }}>{info.total_records.toLocaleString()}</strong>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Disk Size:</span>{' '}
                <strong style={{ color: 'var(--text-main)' }}>{info.size_mb} MB</strong>
              </div>
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <HardDrive size={13} />
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {info.file_path.split('\\').slice(-3).join('\\')}
              </span>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
