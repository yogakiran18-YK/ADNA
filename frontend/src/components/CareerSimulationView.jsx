import React, { useState } from 'react';
import { 
  BarChart3, MessageSquare, TrendingUp, Compass, Zap, Layers 
} from 'lucide-react';

export default function CareerSimulationView({ data }) {
  const [hoveredSem, setHoveredSem] = useState(null);

  if (!data) return null;

  const mlScore = data.ml_ranking_score ?? 0;
  const scorePercent = (mlScore * 100).toFixed(1);
  const matchTier = data.match_tier || (
    mlScore >= 0.82 ? "Tier 1: Placement-Ready" :
    mlScore >= 0.68 ? "Tier 2: Competitive Candidate" :
    mlScore >= 0.48 ? "Tier 3: Emerging Trajectory" : "Tier 4: Foundation Building"
  );

  // Fallback defaults for semester readiness curve if empty
  const semesterReadiness = data.semester_readiness && Object.keys(data.semester_readiness).length > 0 
    ? data.semester_readiness 
    : {
        'Sem 1': 0.18, 'Sem 2': 0.28, 'Sem 3': 0.42, 'Sem 4': mlScore,
        'Sem 5': Math.min(0.92, mlScore + 0.12),
        'Sem 6': Math.min(0.94, mlScore + 0.22),
        'Sem 7': Math.min(0.96, mlScore + 0.30),
        'Sem 8': Math.min(0.98, mlScore + 0.38)
      };

  // Domain competencies
  const domainCompetency = data.domain_competency && Object.keys(data.domain_competency).length > 0
    ? data.domain_competency
    : {
        'Foundations & Math': 0.70,
        'Core Data Structures & Systems': 0.65,
        'Role Specialization Subjects': mlScore,
        'Applied Engineering & Systems': 0.55
      };

  // Adjacent benchmark roles
  const adjacentRoles = data.adjacent_role_scores && Object.keys(data.adjacent_role_scores).length > 0
    ? data.adjacent_role_scores
    : {
        'AI / ML Engineer': Math.min(0.95, mlScore * 1.02),
        'Data Scientist': Math.min(0.95, mlScore * 1.08),
        'Full Stack Developer': Math.min(0.95, mlScore * 0.92),
        'Cloud & DevOps SRE': Math.min(0.95, mlScore * 0.88),
        'Core Software Engineer': Math.min(0.95, mlScore * 1.04)
      };

  // Status Color for Tier
  const getTierColor = (score) => {
    if (score >= 0.82) return { text: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.35)' };
    if (score >= 0.68) return { text: '#38bdf8', bg: 'rgba(56, 189, 248, 0.15)', border: 'rgba(56, 189, 248, 0.35)' };
    if (score >= 0.48) return { text: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.35)' };
    return { text: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.35)' };
  };

  const tierTheme = getTierColor(mlScore);

  // Gauge Angle Calculation (Semi-circle 180 degrees)
  const gaugePercent = Math.max(0, Math.min(100, mlScore * 100));
  const gaugeCircumference = Math.PI * 80; // Radius = 80
  const gaugeStrokeDash = (gaugePercent / 100) * gaugeCircumference;

  // SVG Semester Line / Area Chart Points
  const semEntries = Object.entries(semesterReadiness);
  const chartWidth = 560;
  const chartHeight = 160;
  const paddingLeft = 45;
  const paddingRight = 30;
  const paddingTop = 20;
  const paddingBottom = 30;

  const innerWidth = chartWidth - paddingLeft - paddingRight;
  const innerHeight = chartHeight - paddingTop - paddingBottom;

  const points = semEntries.map(([sem, val], idx) => {
    const x = paddingLeft + (idx / Math.max(1, semEntries.length - 1)) * innerWidth;
    const y = paddingTop + (1 - Math.min(1.0, val)) * innerHeight;
    return { sem, val, x, y };
  });

  const pathD = points.reduce((acc, p, i) => {
    return i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
  }, '');

  const areaD = `${pathD} L ${points[points.length - 1].x} ${paddingTop + innerHeight} L ${points[0].x} ${paddingTop + innerHeight} Z`;

  // Threshold Y for 80% (0.80)
  const thresholdY = paddingTop + (1 - 0.80) * innerHeight;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* 1. TOP HEADER & SUMMARY SCORE BANNER */}
      <div style={{
        padding: '1.5rem',
        borderRadius: '12px',
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.7) 100%)',
        border: '1px solid rgba(56, 189, 248, 0.2)',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
        display: 'grid',
        gridTemplateColumns: '1.2fr 1.8fr',
        gap: '2rem',
        alignItems: 'center'
      }}>
        {/* Left: Semi-circular Gauge & Target Role */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
          
          <div style={{ position: 'relative', width: '200px', height: '115px', display: 'flex', justifyContent: 'center' }}>
            <svg width="200" height="110" viewBox="0 0 200 110">
              <defs>
                <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="50%" stopColor="#38bdf8" />
                  <stop offset="100%" stopColor="#10b981" />
                </linearGradient>
              </defs>
              {/* Background Arch Track */}
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke="rgba(255, 255, 255, 0.08)"
                strokeWidth="16"
                strokeLinecap="round"
              />
              {/* Value Arch Track */}
              <path
                d="M 20 100 A 80 80 0 0 1 180 100"
                fill="none"
                stroke="url(#scoreGradient)"
                strokeWidth="16"
                strokeLinecap="round"
                strokeDasharray={`${gaugeStrokeDash} ${gaugeCircumference}`}
                style={{ transition: 'stroke-dasharray 1s ease' }}
              />
            </svg>
            
            {/* Center Score Label */}
            <div style={{
              position: 'absolute',
              bottom: '0px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center'
            }}>
              <span style={{ fontSize: '2.2rem', fontWeight: 800, color: '#f8fafc', lineHeight: 1 }}>
                {scorePercent}%
              </span>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '2px' }}>
                Role Match Score
              </span>
            </div>
          </div>

          <div style={{ marginTop: '0.75rem' }}>
            <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc', marginBottom: '4px' }}>
              {data.role_title || data.target_role_id}
            </div>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '0.25rem 0.75rem',
              borderRadius: '999px',
              backgroundColor: tierTheme.bg,
              border: `1px solid ${tierTheme.border}`,
              color: tierTheme.text,
              fontSize: '0.75rem',
              fontWeight: 700
            }}>
              <Zap size={13} /> {matchTier}
            </div>
          </div>
        </div>

        {/* Right: Key Role-Aligned Metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
          <div style={{ padding: '0.85rem', borderRadius: '8px', background: 'rgba(10, 15, 29, 0.6)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Academic Degree Stage
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#38bdf8', marginTop: '4px' }}>
              {data.critical_enablers_summary?.stage || "Undergraduate Degree"}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Standard 8-Semester Curriculum
            </div>
          </div>

          <div style={{ padding: '0.85rem', borderRadius: '8px', background: 'rgba(10, 15, 29, 0.6)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Role Prerequisite Enablers
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#10b981', marginTop: '4px' }}>
              {data.critical_enablers_summary?.completed_count ?? 2} Cleared / {data.critical_enablers_summary?.missing_count ?? 4} Upcoming
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Critical upper-division subjects
            </div>
          </div>

          <div style={{ padding: '0.85rem', borderRadius: '8px', background: 'rgba(10, 15, 29, 0.6)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Simulation Engine
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#818cf8', marginTop: '4px' }}>
              Transparent Heuristic Model
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Multi-Factor Attribution (Illustrative Estimate)
            </div>
          </div>

          <div style={{ padding: '0.85rem', borderRadius: '8px', background: 'rgba(10, 15, 29, 0.6)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Readiness Projection
            </div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f59e0b', marginTop: '4px' }}>
              Sem 8: {(Math.min(98, mlScore * 100 + 35)).toFixed(0)}% Forecasted
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Target: ≥ 80% Placement Readiness
            </div>
          </div>
        </div>
      </div>

      {/* 2. GRAPH A: 8-SEMESTER CAREER READINESS PROGRESSION CURVE */}
      <div className="panel" style={{ padding: '1.25rem', backgroundColor: 'rgba(10, 15, 29, 0.7)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.95rem', color: '#38bdf8', fontWeight: 700 }}>
              <TrendingUp size={16} /> 8-Semester Career Readiness Progression Curve (Trajectory Graph)
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Tracks score evolution from foundational Semester 1 through senior graduation, adapted to {data.role_title || data.target_role_id}.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#38bdf8' }}></span>
              Projected Trajectory
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '10px', height: '2px', background: '#f59e0b', borderTop: '2px dashed #f59e0b' }}></span>
              80% Employability Milestone
            </span>
          </div>
        </div>

        {/* Responsive SVG Progression Chart */}
        <div style={{ width: '100%', overflowX: 'auto' }}>
          <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
            <defs>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.35" />
                <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid horizontal lines */}
            {[0, 0.25, 0.5, 0.75, 1.0].map((frac, idx) => {
              const y = paddingTop + (1 - frac) * innerHeight;
              return (
                <g key={idx}>
                  <line 
                    x1={paddingLeft} 
                    y1={y} 
                    x2={chartWidth - paddingRight} 
                    y2={y} 
                    stroke="rgba(255, 255, 255, 0.06)" 
                    strokeDasharray="3 3"
                  />
                  <text 
                    x={paddingLeft - 8} 
                    y={y + 3} 
                    textAnchor="end" 
                    fill="var(--text-muted)" 
                    fontSize="10"
                    fontFamily="inherit"
                  >
                    {Math.round(frac * 100)}%
                  </text>
                </g>
              );
            })}

            {/* 80% Employability Threshold Benchmark Line */}
            <line
              x1={paddingLeft}
              y1={thresholdY}
              x2={chartWidth - paddingRight}
              y2={thresholdY}
              stroke="#f59e0b"
              strokeWidth="1.5"
              strokeDasharray="4 4"
            />
            <text
              x={chartWidth - paddingRight}
              y={thresholdY - 5}
              textAnchor="end"
              fill="#f59e0b"
              fontSize="9"
              fontWeight="600"
            >
              80% Placement Threshold
            </text>

            {/* Area Fill */}
            <path d={areaD} fill="url(#areaGradient)" />

            {/* Main Progression Line */}
            <path d={pathD} fill="none" stroke="#38bdf8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

            {/* Interactive Points on Line */}
            {points.map((p) => {
              const isHovered = hoveredSem === p.sem;
              const isCurrent = Math.abs(p.val - mlScore) < 0.03;
              return (
                <g 
                  key={p.sem} 
                  onMouseEnter={() => setHoveredSem(p.sem)} 
                  onMouseLeave={() => setHoveredSem(null)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Outer Glow Ring if current or hovered */}
                  {(isCurrent || isHovered) && (
                    <circle cx={p.x} cy={p.y} r="10" fill="rgba(56, 189, 248, 0.25)" />
                  )}
                  {/* Main Point Circle */}
                  <circle 
                    cx={p.x} 
                    cy={p.y} 
                    r={isHovered ? "5.5" : "4"} 
                    fill={isCurrent ? "#10b981" : "#38bdf8"} 
                    stroke="#0a0f1d" 
                    strokeWidth="2" 
                  />
                  
                  {/* Semester Label on X-axis */}
                  <text
                    x={p.x}
                    y={chartHeight - 8}
                    textAnchor="middle"
                    fill={isCurrent ? "#10b981" : "var(--text-muted)"}
                    fontSize="10"
                    fontWeight={isCurrent ? "700" : "500"}
                  >
                    {p.sem}
                  </text>

                  {/* Score Tooltip Box on hover or current */}
                  {(isHovered || isCurrent) && (
                    <g>
                      <rect
                        x={p.x - 22}
                        y={p.y - 24}
                        width="44"
                        height="18"
                        rx="4"
                        fill="rgba(15, 23, 42, 0.95)"
                        stroke="#38bdf8"
                        strokeWidth="1"
                      />
                      <text
                        x={p.x}
                        y={p.y - 12}
                        textAnchor="middle"
                        fill="#38bdf8"
                        fontSize="9.5"
                        fontWeight="700"
                      >
                        {(p.val * 100).toFixed(0)}%
                      </text>
                    </g>
                  )}
                </g>
              );
            })}
          </svg>
        </div>
      </div>

      {/* 3. TWO-COLUMN GRAPHS: DOMAIN COMPETENCY & ADJACENT ROLE BENCHMARKS */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
        
        {/* GRAPH B: DOMAIN COMPETENCY BREAKDOWN */}
        <div className="panel" style={{ padding: '1.25rem', backgroundColor: 'rgba(10, 15, 29, 0.7)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', marginBottom: '0.35rem', color: '#10b981', fontWeight: 700 }}>
            <Layers size={16} /> Domain Competency Breakdown
          </h3>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Curriculum mastery across foundational sciences, core computing, and specialized electives.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {Object.entries(domainCompetency).map(([domain, val]) => {
              const pct = (val * 100).toFixed(0);
              const color = val >= 0.75 ? '#10b981' : val >= 0.50 ? '#38bdf8' : '#f59e0b';
              return (
                <div key={domain}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.3rem' }}>
                    <span style={{ color: 'var(--text-main)', fontWeight: 500 }}>{domain}</span>
                    <span style={{ color, fontWeight: 700 }}>{pct}%</span>
                  </div>
                  <div className="progress-container" style={{ height: '7px', background: 'rgba(255,255,255,0.06)' }}>
                    <div 
                      className="progress-bar" 
                      style={{ 
                        width: `${pct}%`, 
                        backgroundColor: color,
                        boxShadow: `0 0 8px ${color}40`,
                        transition: 'width 0.6s ease'
                      }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* GRAPH C: BENCHMARK ADJACENT ROLES COMPARISON */}
        <div className="panel" style={{ padding: '1.25rem', backgroundColor: 'rgba(10, 15, 29, 0.7)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', marginBottom: '0.35rem', color: '#818cf8', fontWeight: 700 }}>
            <Compass size={16} /> Cross-Role Fit Benchmark Comparison
          </h3>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Shows how student coursework translates dynamically across different tech domains.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {Object.entries(adjacentRoles).map(([roleName, score]) => {
              const isTarget = (data.role_title && data.role_title.toLowerCase().includes(roleName.toLowerCase())) ||
                               (data.target_role_id && data.target_role_id.toLowerCase().includes(roleName.toLowerCase()));
              const pct = (score * 100).toFixed(1);
              const barColor = isTarget ? '#38bdf8' : 'rgba(148, 163, 184, 0.5)';
              return (
                <div key={roleName}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem', marginBottom: '0.25rem' }}>
                    <span style={{ 
                      color: isTarget ? '#38bdf8' : 'var(--text-main)', 
                      fontWeight: isTarget ? 700 : 500,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px'
                    }}>
                      {roleName}
                      {isTarget && (
                        <span style={{ 
                          fontSize: '0.62rem', 
                          padding: '0.1rem 0.35rem', 
                          borderRadius: '999px', 
                          background: 'rgba(56, 189, 248, 0.2)', 
                          color: '#38bdf8' 
                        }}>
                          Target
                        </span>
                      )}
                    </span>
                    <span style={{ color: isTarget ? '#38bdf8' : 'var(--text-muted)', fontWeight: 600 }}>
                      {pct}%
                    </span>
                  </div>
                  <div className="progress-container" style={{ height: '6px', background: 'rgba(255,255,255,0.06)' }}>
                    <div 
                      className="progress-bar" 
                      style={{ 
                        width: `${pct}%`, 
                        backgroundColor: barColor,
                        boxShadow: isTarget ? '0 0 10px rgba(56, 189, 248, 0.4)' : 'none',
                        transition: 'width 0.6s ease'
                      }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>

      {/* 4. TWO-COLUMN: COMPONENT B (SHAP DRIVERS) & COMPONENT A (LLM NARRATIVE) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
        
        {/* SHAP DIVERGING BAR GRAPH */}
        <div className="panel" style={{ padding: '1.25rem', backgroundColor: 'rgba(10, 15, 29, 0.7)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', marginBottom: '0.35rem', color: 'var(--accent)', fontWeight: 700 }}>
            <BarChart3 size={16} /> Component B: Feature Contribution Attribution
          </h3>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
            Explainable heuristic attribution: Shows relative contribution of each academic factor to the overall fit estimate.
          </p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem' }}>
            {Object.entries(data.shap_explanations || {}).map(([feature, value], idx) => {
              const isPositive = value >= 0;
              const barColor = isPositive ? '#10b981' : '#ef4444';
              const magnitude = Math.min(Math.abs(value) * 160, 95);
              
              return (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.35rem' }}>
                    <span style={{ fontWeight: 500 }}>{feature}</span>
                    <span style={{ color: barColor, fontWeight: 700 }}>
                      {value > 0 ? '+' : ''}{value.toFixed(3)}
                    </span>
                  </div>
                  
                  {/* Center-aligned diverging bar */}
                  <div style={{ 
                    position: 'relative', 
                    height: '8px', 
                    backgroundColor: 'rgba(255, 255, 255, 0.06)', 
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center'
                  }}>
                    {/* Center 0-axis line */}
                    <div style={{ 
                      position: 'absolute', 
                      left: '50%', 
                      top: '-2px', 
                      bottom: '-2px', 
                      width: '2px', 
                      backgroundColor: 'rgba(255, 255, 255, 0.2)',
                      zIndex: 2
                    }}></div>

                    {/* Left negative bar or Right positive bar */}
                    {isPositive ? (
                      <div style={{
                        position: 'absolute',
                        left: '50%',
                        width: `${magnitude / 2}%`,
                        height: '100%',
                        backgroundColor: '#10b981',
                        borderRadius: '0 4px 4px 0',
                        boxShadow: '0 0 8px rgba(16, 185, 129, 0.3)',
                        transition: 'width 0.5s ease'
                      }}></div>
                    ) : (
                      <div style={{
                        position: 'absolute',
                        right: '50%',
                        width: `${magnitude / 2}%`,
                        height: '100%',
                        backgroundColor: '#ef4444',
                        borderRadius: '4px 0 0 4px',
                        boxShadow: '0 0 8px rgba(239, 68, 68, 0.3)',
                        transition: 'width 0.5s ease'
                      }}></div>
                    )}
                  </div>
                </div>
              );
            })}
            
            {Object.keys(data.shap_explanations || {}).length === 0 && (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic', textAlign: 'center', padding: '1rem' }}>
                SHAP explanations not generated for this profile run.
              </div>
            )}
          </div>
        </div>

        {/* COMPONENT A: ADVISORY NARRATIVE */}
        <div className="panel" style={{ padding: '1.25rem', backgroundColor: 'rgba(10, 15, 29, 0.7)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', marginBottom: '0.35rem', color: '#10b981', fontWeight: 700 }}>
            <MessageSquare size={16} /> Component A: Grounded Curriculum Advisory Narrative
          </h3>
          <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.85rem' }}>
            Automated qualitative advisory synthesized from completed coursework and market skill gaps (illustrative estimate).
          </p>
          
          <div style={{ 
            backgroundColor: 'rgba(15, 23, 42, 0.85)', 
            padding: '1.1rem', 
            borderRadius: '8px', 
            border: '1px solid rgba(255, 255, 255, 0.08)',
            fontSize: '0.85rem',
            lineHeight: 1.65,
            color: 'var(--text-main)',
            whiteSpace: 'pre-wrap',
            maxHeight: '280px',
            overflowY: 'auto'
          }}>
            {data.llm_narrative}
          </div>
        </div>

      </div>

    </div>
  );
}
