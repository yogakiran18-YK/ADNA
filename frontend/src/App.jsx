import React, { useState, useEffect } from 'react';
import { 
  GraduationCap, TrendingUp, Database, Compass, 
  Sparkles, Layers, ArrowRight
} from 'lucide-react';
import './index.css';
import ProfileForm from './components/ProfileForm';
import RoadmapView from './components/RoadmapView';
import GapReportView from './components/GapReportView';
import CareerSimulationView from './components/CareerSimulationView';
import MarketTrendsView from './components/MarketTrendsView';
import KaggleDatasetsHub from './components/KaggleDatasetsHub';
import ReasonChainInspector from './components/ReasonChainInspector';

const API_BASE = 'http://127.0.0.1:8000';
const AUTH_HEADER = 'Basic ' + btoa('admin:viva2026');

function App() {
  const [activeTab, setActiveTab] = useState('trends'); // 'trends' | 'navigator' | 'datasets'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [marketTrends, setMarketTrends] = useState(null);
  
  const [roadmapData, setRoadmapData] = useState(null);
  const [gapData, setGapData] = useState(null);
  const [simData, setSimData] = useState(null);
  const [runId, setRunId] = useState(null);

  const [trendsError, setTrendsError] = useState(null);

  // Load market trends on mount so it's always ready
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/market/trends`)
      .then(res => {
        if (!res.ok) throw new Error(`Market API returned HTTP ${res.status}`);
        return res.json();
      })
      .then(data => {
        setMarketTrends(data);
        setTrendsError(null);
      })
      .catch(err => {
        console.error('Error fetching trends on mount', err);
        setTrendsError(err.message || 'Failed to load market trends');
      });
  }, []);

  const handleGenerate = async (studentId, completedCourses, targetRoleId, targetRoleTitle, targetRoleSkills, currentSemester) => {
    setLoading(true);
    setError(null);
    setRoadmapData(null);
    setGapData(null);
    setSimData(null);
    setRunId(null);

    const effectiveRoleTitle = targetRoleTitle || targetRoleId || "AI / Machine Learning Engineer";
    const effectiveRoleId = targetRoleId || "ROLE_DEV";

    // 1. Sync Student Profile to Canonical API truthfully without fabricated grades
    const profilePayload = {
      student_id: studentId,
      name: studentId,
      department: "CSE",
      current_semester: currentSemester || (completedCourses.length > 0 ? Math.min(8, Math.floor(completedCourses.length / 4) + 1) : 1),
      target_role: effectiveRoleTitle,
      interests: targetRoleSkills && targetRoleSkills.length > 0 ? targetRoleSkills : ["Machine Learning", "System Design"],
      completed_courses: completedCourses.map(c => {
        if (typeof c === 'string') {
          return {
            course_code: c,
            semester_taken: null,
            grade: null,
            grade_point: null,
            credits: null,
            grade_estimated: false,
            credits_estimated: false
          };
        }
        return {
          course_code: c.course_code,
          semester_taken: c.semester_taken ?? null,
          grade: c.grade ?? null,
          grade_point: c.grade_point ?? null,
          credits: c.credits ?? null,
          grade_estimated: false,
          credits_estimated: false
        };
      })
    };

    try {
      // Step 1: Save student profile
      const profRes = await fetch(`${API_BASE}/api/v1/student/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profilePayload)
      });
      if (!profRes.ok) {
        const errData = await profRes.json().catch(() => ({}));
        throw new Error(`Profile synchronization failed (${profRes.status}): ${errData.detail || "Unable to save profile"}`);
      }

      // Step 2 & 3: Run Gap Analysis with role awareness and Career Simulation concurrently
      const [gapRes, simRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/skills/gap-analysis/${encodeURIComponent(studentId)}?target_role_id=${encodeURIComponent(effectiveRoleId)}&target_role=${encodeURIComponent(effectiveRoleTitle)}`),
        fetch(`${API_BASE}/api/v1/career/simulate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: studentId,
            target_role_override: effectiveRoleTitle
          })
        })
      ]);

      if (!gapRes.ok) {
        const errData = await gapRes.json().catch(() => ({}));
        throw new Error(`Skill gap analysis failed (${gapRes.status}): ${errData.detail || "Unable to compute skill gaps"}`);
      }
      if (!simRes.ok) {
        const errData = await simRes.json().catch(() => ({}));
        throw new Error(`Career simulation failed (${simRes.status}): ${errData.detail || "Unable to compute career fit"}`);
      }

      const gData = await gapRes.json();
      const sData = await simRes.json();

      // Step 4: Generate Roadmap Plan
      const roadmapRes = await fetch(`${API_BASE}/api/v1/roadmap/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          max_credits_per_sem: 24
        })
      });

      if (!roadmapRes.ok) {
        const errData = await roadmapRes.json().catch(() => ({}));
        throw new Error(`Roadmap generation failed (${roadmapRes.status}): ${errData.detail || "Unable to generate roadmap"}`);
      }

      const rData = await roadmapRes.json();
      if (rData.status === "infeasible" || rData.error) {
        throw new Error(`Roadmap constraint failure: ${rData.error}`);
      }

      setRoadmapData(rData);
      setGapData(gData);
      setSimData(sData);
      setRunId(rData.run_id || `run_${rData.roadmap_id}`);

      // Switch to navigator tab
      setActiveTab('navigator');

    } catch (err) {
      console.error(err);
      setError(err.message || 'An error occurred during pipeline execution.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* GLOBAL NAVBAR */}
      <header className="navbar">
        <div className="nav-brand">
          <div className="brand-icon">
            <GraduationCap size={24} color="#38bdf8" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="brand-title">ADNA</span>
              <span className="brand-version">v2.0 Kaggle-Linked</span>
            </div>
            <div className="brand-subtitle">Autonomous Degree Navigator Agent</div>
          </div>
        </div>

        {/* NAVIGATION TABS */}
        <nav className="nav-tabs">
          <button 
            className={`nav-tab-btn ${activeTab === 'trends' ? 'active' : ''}`}
            onClick={() => setActiveTab('trends')}
          >
            <TrendingUp size={18} />
            Market Trends
            <span className="live-dot" />
          </button>

          <button 
            className={`nav-tab-btn ${activeTab === 'navigator' ? 'active' : ''}`}
            onClick={() => setActiveTab('navigator')}
          >
            <Compass size={18} />
            Degree Navigator
            {roadmapData && <span className="tab-pill">Active Plan</span>}
          </button>

          <button 
            className={`nav-tab-btn ${activeTab === 'datasets' ? 'active' : ''}`}
            onClick={() => setActiveTab('datasets')}
          >
            <Database size={18} />
            Kaggle Datasets Hub
          </button>
        </nav>

        {/* SYSTEM STATUS BADGES */}
        <div className="nav-status">
          <div className="status-pill status-online">
            <span className="pulse-indicator-small" />
            <span>FastAPI: Online</span>
          </div>
          <div className="status-pill status-kaggle">
            <Database size={13} color="#38bdf8" />
            <span>{marketTrends?.is_sample_data ? 'Market: Sample Baseline' : 'Market: Ingested Active'}</span>
          </div>
        </div>
      </header>

      {/* BODY CONTENT ROUTING */}
      <main className="app-main">

        {/* TAB 1: MARKET TRENDS VIEW */}
        {activeTab === 'trends' && (
          <div style={{ maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              marginBottom: '1.5rem',
              flexWrap: 'wrap',
              gap: '1rem'
            }}>
              <div>
                <h1 style={{ fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.025em', display: 'flex', alignItems: 'center', gap: '10px' }}>
                  Industry Skill Trends & Market Signals
                  {marketTrends?.is_sample_data ? (
                    <span className="badge-kaggle" style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', border: '1px solid rgba(245, 158, 11, 0.3)' }}>
                      Sample Baseline Data
                    </span>
                  ) : (
                    <span className="badge-kaggle">
                      Live Ingested ({marketTrends?.data_source || 'Kaggle'})
                    </span>
                  )}
                </h1>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                  {marketTrends?.is_sample_data
                    ? "Showing sample job postings baseline data. Ingest live Kaggle postings in the Datasets Hub or Market Trends view to calibrate real market signals."
                    : `Derived from ${marketTrends?.total_postings_analyzed || 0} job postings with real-time exponential recency decay scoring.`}
                </p>
                {trendsError && (
                  <div style={{ marginTop: '0.5rem', color: '#ef4444', fontSize: '0.85rem' }}>
                    ⚠️ {trendsError}. Unable to load market trends.
                  </div>
                )}
              </div>

              <button 
                onClick={() => setActiveTab('navigator')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  padding: '0.65rem 1.25rem',
                  borderRadius: '0.5rem',
                  boxShadow: '0 4px 14px rgba(59, 130, 246, 0.35)'
                }}
              >
                Plan Degree Based On These Trends <ArrowRight size={16} />
              </button>
            </div>

            <MarketTrendsView apiBase={API_BASE} />
          </div>
        )}

        {/* TAB 2: DEGREE NAVIGATOR */}
        {activeTab === 'navigator' && (
          <div className="dashboard-layout">
            {/* LEFT SIDEBAR: STUDENT PROFILE FORM */}
            <aside className="sidebar">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.5rem' }}>
                <Compass size={22} color="#38bdf8" />
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Student Profile</h2>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Configure academic standing, completed courses, and career role target to execute multi-agent planning.
              </p>

              <ProfileForm onGenerate={handleGenerate} isLoading={loading} />

              {error && (
                <div style={{
                  padding: '1rem',
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  color: 'var(--danger)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  marginTop: '1rem'
                }}>
                  {error}
                </div>
              )}
            </aside>

            {/* RIGHT WORKSPACE */}
            <div className="main-content">
              {!roadmapData && !loading && (
                <div className="empty-state-card">
                  <div className="empty-icon-wrapper">
                    <Compass size={40} color="#38bdf8" />
                  </div>
                  <h2 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                    Degree Navigator Ready
                  </h2>
                  <p style={{ maxWidth: '480px', color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: 1.6 }}>
                    Select a student profile and click <strong>Generate Plan</strong> to execute the full multi-agent orchestration pipeline.
                  </p>
                  
                  <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                    <div className="quick-spec-card">
                      <TrendingUp size={18} color="#10b981" />
                      <div>
                        <strong>Market-Aligned</strong>
                        <p>Optimizes against real Kaggle job trends</p>
                      </div>
                    </div>
                    <div className="quick-spec-card">
                      <Layers size={18} color="#6366f1" />
                      <div>
                        <strong>Graph Feasibility</strong>
                        <p>Strict prerequisite constraint checking</p>
                      </div>
                    </div>
                    <div className="quick-spec-card">
                      <Sparkles size={18} color="#f59e0b" />
                      <div>
                        <strong>Explainable AI</strong>
                        <p>Transparent Factor Attribution</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {loading && (
                <div className="empty-state-card">
                  <div className="spinner-large" />
                  <h2 style={{ fontSize: '1.35rem', fontWeight: 700, marginTop: '1.5rem', marginBottom: '0.5rem' }}>
                    Executing Multi-Agent Orchestration Pipeline...
                  </h2>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    Curriculum Agent → Market Trends Agent → Skill Gap Agent → Career Simulator → Planner Agent
                  </p>
                </div>
              )}

              {roadmapData && !loading && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  <div className="split-pane">
                    <div className="panel" style={{ gridColumn: 'span 2' }}>
                      <CareerSimulationView data={simData} />
                    </div>

                    <div className="panel">
                      <GapReportView data={gapData} trends={marketTrends} />
                    </div>

                    <div className="panel">
                      <RoadmapView data={roadmapData} />
                    </div>
                  </div>

                  <div className="panel" style={{ width: '100%' }}>
                    <ReasonChainInspector 
                      studentId={roadmapData?.student_id}
                      roadmapId={roadmapData?.roadmap_id}
                      runId={runId || roadmapData?.run_id} 
                      apiBase={API_BASE} 
                      authHeader={AUTH_HEADER} 
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 3: KAGGLE DATASETS HUB */}
        {activeTab === 'datasets' && (
          <div style={{ maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
            <KaggleDatasetsHub apiBase={API_BASE} />
          </div>
        )}

      </main>
    </div>
  );
}

export default App;
