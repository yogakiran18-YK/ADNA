import React, { useState } from 'react';
import { Target, TrendingUp, HelpCircle } from 'lucide-react';

export default function GapReportView({ data, trends }) {
  const [activeTab, setActiveTab] = useState('role_required'); // 'role_required' | 'broader_market' | 'all'

  if (!data) return null;

  const demandMap = {};
  if (trends && trends.top_skills) {
    trends.top_skills.forEach(item => {
      demandMap[item.skill_name.toLowerCase()] = item.demand_score;
      demandMap[item.skill_id.toLowerCase()] = item.demand_score;
    });
  }

  // Derive role-required gaps vs broader market gaps
  const roleRequiredGaps = data.role_required_gaps || [];
  const broaderMarketGaps = data.broader_market_gaps || [];
  const unmappedSkills = data.unmapped_skills || [];

  // Fallback for older responses
  const legacyGaps = (!data.role_required_gaps && data.gaps) ? data.gaps : [];
  const hasStructuredGaps = roleRequiredGaps.length > 0 || broaderMarketGaps.length > 0 || legacyGaps.length > 0;

  const isSampleData = data.is_sample_data || trends?.is_sample_data;

  const renderDemandBadge = (demandVal, skillName) => {
    let finalDemand = (demandVal !== undefined && demandVal !== null)
      ? demandVal
      : demandMap[skillName.toLowerCase()];

    if (finalDemand === undefined || finalDemand === null) {
      return (
        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontStyle: 'italic' }}>
          Not Available
        </span>
      );
    }

    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#38bdf8' }}>
        <TrendingUp size={14} />
        {(finalDemand * 100).toFixed(1)}%
      </div>
    );
  };

  const currentDisplayList = activeTab === 'role_required'
    ? (roleRequiredGaps.length > 0 ? roleRequiredGaps : legacyGaps)
    : activeTab === 'broader_market'
      ? broaderMarketGaps
      : [...roleRequiredGaps, ...broaderMarketGaps, ...legacyGaps];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '8px' }}>
        <div className="panel-title" style={{ margin: 0 }}>
          <Target size={20} color="var(--warning)" /> 
          Skill Gap Analysis
        </div>
        <span style={{
          fontSize: '0.72rem',
          padding: '0.2rem 0.55rem',
          borderRadius: '999px',
          fontWeight: 600,
          backgroundColor: isSampleData ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)',
          color: isSampleData ? '#f59e0b' : '#10b981',
          border: `1px solid ${isSampleData ? 'rgba(245, 158, 11, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`
        }}>
          {isSampleData ? 'Sample Baseline Signal' : 'Live Ingested Market Signal'}
        </span>
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '6px' }}>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
          Target Role: <strong style={{ color: 'var(--text-main)' }}>{data.target_role_title || data.target_role_id || data.target_role}</strong>
        </p>
        <span style={{ fontSize: '0.75rem', color: '#818cf8' }}>
          {roleRequiredGaps.length} Role-Required Gaps • {broaderMarketGaps.length} Market Gaps
        </span>
      </div>

      {/* TABS: Role-Required vs Broader Market */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '0.75rem' }}>
        <button
          type="button"
          onClick={() => setActiveTab('role_required')}
          className={`sem-tab-pill ${activeTab === 'role_required' ? 'active' : ''}`}
          style={{ fontSize: '0.78rem', padding: '0.3rem 0.65rem' }}
        >
          Role-Required ({roleRequiredGaps.length || legacyGaps.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('broader_market')}
          className={`sem-tab-pill ${activeTab === 'broader_market' ? 'active' : ''}`}
          style={{ fontSize: '0.78rem', padding: '0.3rem 0.65rem' }}
        >
          Broader Market ({broaderMarketGaps.length})
        </button>
      </div>

      {!hasStructuredGaps ? (
        <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--success)', border: '1px solid var(--success)', borderRadius: '0.5rem', backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
          No missing skills detected for this target role!
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ fontSize: '0.85rem', width: '100%' }}>
            <thead>
              <tr>
                <th>Skill</th>
                <th>Relevance</th>
                <th>Market Demand</th>
                <th>Gap Score G(s)</th>
              </tr>
            </thead>
            <tbody>
              {currentDisplayList.map((item, idx) => {
                const sName = item.skill_name || item.skill_id || Object.keys(item)[0];
                const gapScore = item.gap_score !== undefined ? item.gap_score : item[sName];
                const isReq = item.is_role_required ?? (activeTab === 'role_required');

                return (
                  <tr key={idx}>
                    <td style={{ fontWeight: 500 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {isReq && <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#f59e0b' }} />}
                        {sName}
                      </div>
                    </td>
                    <td>
                      <span style={{
                        fontSize: '0.7rem',
                        padding: '0.15rem 0.4rem',
                        borderRadius: '4px',
                        backgroundColor: isReq ? 'rgba(245, 158, 11, 0.12)' : 'rgba(99, 102, 241, 0.12)',
                        color: isReq ? '#f59e0b' : '#818cf8',
                        fontWeight: 600
                      }}>
                        {isReq ? 'Role Required' : 'Market Elective'}
                      </span>
                    </td>
                    <td>
                      {renderDemandBadge(item.market_demand_score, sName)}
                    </td>
                    <td style={{ color: 'var(--warning)', fontWeight: 600 }}>
                      {typeof gapScore === 'number' ? gapScore.toFixed(4) : gapScore}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* UNMAPPED SKILLS DISCLOSURE */}
      {unmappedSkills.length > 0 && (
        <div style={{
          marginTop: '0.75rem',
          padding: '0.5rem 0.75rem',
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          borderRadius: '6px',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#94a3b8', fontWeight: 600, marginBottom: '2px' }}>
            <HelpCircle size={13} /> Unmapped Role Skills:
          </div>
          <span>{unmappedSkills.join(', ')} (no calibrated market demand signal in current taxonomy)</span>
        </div>
      )}
    </div>
  );
}
