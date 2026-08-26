import React from 'react';
import { Target } from 'lucide-react';

export default function GapReportView({ data }) {
  if (!data || !data.missing_skills) return null;

  return (
    <div>
      <div className="panel-title">
        <Target size={20} color="var(--warning)" /> 
        Skill Gap Analysis
      </div>
      
      <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
        Target Role: <strong style={{color:'var(--text-main)'}}>{data.target_role_id}</strong>
      </p>

      {data.missing_skills.length === 0 ? (
        <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--success)', border: '1px solid var(--success)', borderRadius: '0.5rem', backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
          No missing skills detected!
        </div>
      ) : (
        <table style={{ fontSize: '0.9rem' }}>
          <thead>
            <tr>
              <th>Missing Skill</th>
              <th>Demand Score</th>
              <th>Total Gap Score</th>
            </tr>
          </thead>
          <tbody>
            {data.missing_skills.map((skillDict, idx) => {
              const skillName = Object.keys(skillDict)[0];
              const score = skillDict[skillName];
              
              return (
                <tr key={idx}>
                  <td style={{ fontWeight: 500 }}>{skillName}</td>
                  {/* Mocking demand_score strictly for visual clarity since GapReport payload only has the final gap score */}
                  <td style={{ color: 'var(--text-muted)' }}>MKT_LOCKED</td>
                  <td style={{ color: 'var(--warning)', fontWeight: 600 }}>{score.toFixed(4)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
