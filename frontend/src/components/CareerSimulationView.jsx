import React from 'react';
import { BarChart3, MessageSquare } from 'lucide-react';

export default function CareerSimulationView({ data }) {
  if (!data) return null;

  return (
    <div>
      <div className="panel-title" style={{ marginBottom: '1.5rem' }}>
        Hybrid Career Simulator (Phase 5)
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        
        {/* ML Component */}
        <div style={{ borderRight: '1px solid var(--border-color)', paddingRight: '2rem' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1rem', marginBottom: '1rem', color: 'var(--accent)' }}>
            <BarChart3 size={18} /> Component B: ML Ranking
          </h3>
          
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginBottom: '1.5rem' }}>
            <span style={{ fontSize: '2.5rem', fontWeight: 700 }}>{(data.ml_ranking_score * 100).toFixed(1)}%</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Match Score</span>
          </div>

          <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.75rem', textTransform: 'uppercase' }}>
            SHAP Feature Drivers
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {Object.entries(data.shap_explanations || {}).map(([feature, value], idx) => {
              const isPositive = value >= 0;
              const barColor = isPositive ? 'var(--success)' : 'var(--danger)';
              const width = Math.min(Math.abs(value) * 100, 100) + '%';
              
              return (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.25rem' }}>
                    <span>{feature}</span>
                    <span style={{ color: barColor, fontWeight: 600 }}>{value > 0 ? '+' : ''}{value.toFixed(3)}</span>
                  </div>
                  <div className="progress-container" style={{ height: '6px' }}>
                    <div className="progress-bar" style={{ width: width, backgroundColor: barColor }}></div>
                  </div>
                </div>
              );
            })}
            
            {Object.keys(data.shap_explanations || {}).length === 0 && (
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                No SHAP features generated in mock mode.
              </div>
            )}
          </div>
        </div>

        {/* LLM Component */}
        <div>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1rem', marginBottom: '1rem', color: 'var(--success)' }}>
            <MessageSquare size={18} /> Component A: Advisory LLM Narrative
          </h3>
          
          <div style={{ 
            backgroundColor: 'var(--bg-dark)', 
            padding: '1.25rem', 
            borderRadius: '0.5rem', 
            border: '1px solid var(--border-color)',
            fontSize: '0.95rem',
            lineHeight: 1.6,
            color: 'var(--text-main)',
            whiteSpace: 'pre-wrap'
          }}>
            {data.llm_narrative}
          </div>
        </div>

      </div>
    </div>
  );
}
