import React, { useState, useEffect } from 'react';
import { Search, ChevronDown, ChevronRight, CheckCircle2 } from 'lucide-react';

export default function ReasonChainInspector({ runId, apiBase, authHeader }) {
  const [trace, setTrace] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedRows, setExpandedRows] = useState({});

  useEffect(() => {
    if (!runId) return;
    
    setLoading(true);
    fetch(`${apiBase}/reason-chain/${runId}`, {
      headers: { 'Authorization': authHeader }
    })
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch reason chain trace");
        return res.json();
      })
      .then(data => {
        setTrace(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [runId, apiBase, authHeader]);

  const toggleRow = (idx) => {
    setExpandedRows(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  if (loading) return <div style={{ color: 'var(--text-muted)' }}>Loading Agent Trace...</div>;
  if (error) return <div style={{ color: 'var(--danger)' }}>Trace Error: {error}</div>;

  return (
    <div>
      <div className="panel-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Search size={20} color="var(--accent)" /> 
          Aggregated Agent Trace (Defensibility Log)
        </div>
        <span className="badge" style={{ fontSize: '0.75rem', fontWeight: 500, backgroundColor: 'rgba(59, 130, 246, 0.1)', color: 'var(--accent)', border: 'none' }}>
          Run ID: {runId}
        </span>
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        {trace.map((step, idx) => (
          <div key={idx} style={{ 
            borderBottom: '1px solid var(--border-color)',
            padding: '1rem 0'
          }}>
            <div 
              style={{ display: 'flex', gap: '1rem', cursor: 'pointer', alignItems: 'center' }}
              onClick={() => toggleRow(idx)}
            >
              <div style={{ color: 'var(--text-muted)' }}>
                {expandedRows[idx] ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
              </div>
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <CheckCircle2 size={16} color="var(--success)" />
                <span className="badge" style={{ backgroundColor: 'var(--bg-dark)', borderColor: 'var(--border-color)' }}>
                  {step.agent_name}
                </span>
                <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>
                  {step.input_summary}
                </span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {new Date(step.timestamp).toISOString().split('T')[1].slice(0, -1)}
              </div>
            </div>

            {expandedRows[idx] && (
              <div style={{ 
                marginTop: '1rem', 
                marginLeft: '2.5rem', 
                padding: '1rem', 
                backgroundColor: 'var(--bg-dark)', 
                borderRadius: '0.5rem',
                fontSize: '0.875rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem'
              }}>
                <div>
                  <strong style={{ color: 'var(--text-muted)' }}>Decision Made:</strong>
                  <div style={{ color: 'var(--text-main)', marginTop: '0.25rem' }}>{step.decision}</div>
                </div>
                <div>
                  <strong style={{ color: 'var(--text-muted)' }}>Justification:</strong>
                  <div style={{ color: 'var(--warning)', marginTop: '0.25rem' }}>{step.justification}</div>
                </div>
                {step.score_used !== null && step.score_used !== undefined && (
                  <div>
                    <strong style={{ color: 'var(--text-muted)' }}>Score Used:</strong>
                    <div style={{ color: 'var(--accent)', marginTop: '0.25rem', fontFamily: 'monospace' }}>{step.score_used.toFixed(4)}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {trace.length === 0 && (
          <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', textAlign: 'center', padding: '2rem' }}>
            No trace logs found for this run.
          </div>
        )}
      </div>
    </div>
  );
}
