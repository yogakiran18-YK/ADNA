import React, { useState, useEffect } from 'react';
import { Search, ChevronDown, ChevronRight, CheckCircle2, TrendingUp, GitCommit } from 'lucide-react';

export default function ReasonChainInspector({ studentId, roadmapId, runId, apiBase }) {
  const [trace, setTrace] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedRows, setExpandedRows] = useState({});

  const targetIdentifier = studentId || roadmapId || runId;

  useEffect(() => {
    if (!targetIdentifier) {
      setTrace([]);
      setLoading(false);
      setError(null);
      return;
    }
    
    setLoading(true);
    setError(null);

    // Call canonical roadmap trace endpoint
    fetch(`${apiBase}/api/v1/roadmap/${encodeURIComponent(targetIdentifier)}/trace`)
      .then(res => {
        if (!res.ok) {
          if (res.status === 404) {
            throw new Error(`No canonical roadmap trace records found for identifier '${targetIdentifier}'.`);
          }
          throw new Error(`Failed to fetch canonical roadmap trace (${res.status})`);
        }
        return res.json();
      })
      .then(data => {
        setTrace(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setTrace([]);
        setLoading(false);
      });
  }, [targetIdentifier, apiBase]);

  const toggleRow = (idx) => {
    setExpandedRows(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  return (
    <div>
      <div className="panel-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Search size={20} color="var(--accent)" /> 
          Canonical Roadmap Traceability Log (Defensibility & Attribution)
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {studentId && (
            <span className="badge" style={{ fontSize: '0.75rem', fontWeight: 500, backgroundColor: 'rgba(59, 130, 246, 0.1)', color: 'var(--accent)', border: 'none' }}>
              Student: {studentId}
            </span>
          )}
          {(roadmapId || runId) && (
            <span className="badge" style={{ fontSize: '0.75rem', fontWeight: 500, backgroundColor: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', border: 'none' }}>
              Plan ID: {roadmapId || runId}
            </span>
          )}
        </div>
      </div>

      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem', marginBottom: '1rem' }}>
        Verifiable factor attribution explaining why each course was scheduled by the multi-criteria optimization planner.
      </p>

      {loading && (
        <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
          <div className="spinner-small" /> Loading Canonical Roadmap Trace...
        </div>
      )}

      {error && !loading && (
        <div style={{ 
          padding: '1.25rem', 
          backgroundColor: 'rgba(239, 68, 68, 0.1)', 
          border: '1px solid rgba(239, 68, 68, 0.25)', 
          borderRadius: '0.5rem', 
          color: 'var(--danger)',
          fontSize: '0.9rem' 
        }}>
          <strong>Trace Unavailable:</strong> {error}
        </div>
      )}

      {!loading && !error && trace.length === 0 && (
        <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', textAlign: 'center', padding: '2.5rem', border: '1px dashed var(--border-color)', borderRadius: '0.5rem' }}>
          No trace logs available for this roadmap. Generate a new roadmap plan to inspect its decision chain.
        </div>
      )}

      {!loading && !error && trace.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          {trace.map((step, idx) => {
            const courseCode = step.course_code || step.decision || `Step ${idx + 1}`;
            const targetSkill = step.target_skill_id || step.input_summary || 'General Competency';
            const demandScore = step.market_signal_demand !== undefined ? (step.market_signal_demand * 100).toFixed(1) : null;
            const scoreContr = step.score_contribution !== undefined ? step.score_contribution.toFixed(4) : (step.score_used !== undefined ? step.score_used.toFixed(4) : null);
            const explanation = step.explanation_prose || step.justification || '';
            const prereqPath = step.prerequisite_feasibility_path && step.prerequisite_feasibility_path.length > 0
              ? step.prerequisite_feasibility_path.join(' → ')
              : 'Directly Feasible (No Unmet Prerequisites)';

            return (
              <div key={idx} style={{ 
                borderBottom: '1px solid var(--border-color)',
                padding: '0.85rem 0'
              }}>
                <div 
                  style={{ display: 'flex', gap: '1rem', cursor: 'pointer', alignItems: 'center' }}
                  onClick={() => toggleRow(idx)}
                >
                  <div style={{ color: 'var(--text-muted)' }}>
                    {expandedRows[idx] ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                  </div>
                  <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                    <CheckCircle2 size={16} color="var(--success)" />
                    <span className="badge" style={{ backgroundColor: 'rgba(56, 189, 248, 0.15)', borderColor: 'rgba(56, 189, 248, 0.3)', color: '#38bdf8', fontWeight: 700 }}>
                      {courseCode}
                    </span>
                    <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>
                      Addresses Target Skill: <strong style={{ color: 'var(--text-main)' }}>{targetSkill}</strong>
                    </span>
                  </div>
                  {demandScore !== null && (
                    <div style={{ fontSize: '0.8rem', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <TrendingUp size={13} /> Demand: {demandScore}%
                    </div>
                  )}
                </div>

                {expandedRows[idx] && (
                  <div style={{ 
                    marginTop: '0.85rem', 
                    marginLeft: '2.5rem', 
                    padding: '1rem', 
                    backgroundColor: 'var(--bg-dark)', 
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                    border: '1px solid rgba(255, 255, 255, 0.05)'
                  }}>
                    <div>
                      <strong style={{ color: 'var(--text-muted)' }}>Decision Rationale:</strong>
                      <div style={{ color: 'var(--text-main)', marginTop: '0.25rem', lineHeight: 1.5 }}>{explanation}</div>
                    </div>
                    <div>
                      <strong style={{ color: 'var(--text-muted)' }}>Prerequisite Feasibility Path:</strong>
                      <div style={{ color: '#10b981', marginTop: '0.25rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <GitCommit size={14} /> {prereqPath}
                      </div>
                    </div>
                    {scoreContr !== null && (
                      <div>
                        <strong style={{ color: 'var(--text-muted)' }}>Objective Optimization Score Contribution:</strong>
                        <div style={{ color: 'var(--accent)', marginTop: '0.25rem', fontFamily: 'monospace', fontWeight: 600 }}>
                          {scoreContr}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
