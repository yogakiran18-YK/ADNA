import React, { useState } from 'react';
import { Settings, Play, Database, FileText, BarChart3, GraduationCap, Link2 } from 'lucide-react';
import './index.css';
import ProfileForm from './components/ProfileForm';
import RoadmapView from './components/RoadmapView';
import GapReportView from './components/GapReportView';
import CareerSimulationView from './components/CareerSimulationView';
import ReasonChainInspector from './components/ReasonChainInspector';

const API_BASE = 'http://127.0.0.1:8000';
const AUTH_HEADER = 'Basic ' + btoa('admin:viva2026');

function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [roadmapData, setRoadmapData] = useState(null);
  const [gapData, setGapData] = useState(null);
  const [simData, setSimData] = useState(null);
  const [runId, setRunId] = useState(null);

  const handleGenerate = async (studentId, completedCourses, targetRoleId, targetRoleTitle, targetRoleSkills) => {
    setLoading(true);
    setError(null);
    setRoadmapData(null);
    setGapData(null);
    setSimData(null);
    setRunId(null);

    const profilePayload = {
      student: {
        student_id: studentId,
        current_skills: [],
        completed_courses: completedCourses
      },
      target_role: {
        role_id: targetRoleId,
        title: targetRoleTitle,
        required_skills: targetRoleSkills
      }
    };

    const headers = {
      'Content-Type': 'application/json',
      'Authorization': AUTH_HEADER
    };

    try {
      // Execute the deterministic pipeline natively by hitting all 3 endpoints concurrently.
      const [roadmapRes, gapRes, simRes] = await Promise.all([
        fetch(`${API_BASE}/students/${studentId}/roadmap`, {
          method: 'POST',
          headers,
          body: JSON.stringify(profilePayload)
        }),
        fetch(`${API_BASE}/students/${studentId}/gap-report`, {
          method: 'POST',
          headers,
          body: JSON.stringify(profilePayload)
        }),
        fetch(`${API_BASE}/students/${studentId}/career-simulation`, {
          method: 'POST',
          headers,
          body: JSON.stringify(profilePayload)
        })
      ]);

      if (!roadmapRes.ok) throw new Error("Failed to generate roadmap.");
      if (!gapRes.ok) throw new Error("Failed to generate gap report.");
      if (!simRes.ok) throw new Error("Failed to generate career simulation.");

      const roadmapData = await roadmapRes.json();
      const gapData = await gapRes.json();
      const simData = await simRes.json();

      setRoadmapData(roadmapData.roadmap);
      setRunId(roadmapData.run_id);
      setGapData(gapData);
      setSimData(simData);

    } catch (err) {
      console.error(err);
      setError(err.message || 'An error occurred during pipeline execution.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-layout">
      {/* LEFT SIDEBAR */}
      <div className="sidebar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
          <GraduationCap size={32} color="#3b82f6" />
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.025em' }}>ADNA Core</h1>
        </div>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          Autonomous Degree Navigator Agent<br />Viva Defense Demo
        </p>

        <ProfileForm onGenerate={handleGenerate} isLoading={loading} />
        
        {error && (
          <div style={{ padding: '1rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: '0.5rem', fontSize: '0.875rem', marginTop: '1rem' }}>
            {error}
          </div>
        )}
      </div>

      {/* RIGHT MAIN CONTENT */}
      <div className="main-content">
        {!roadmapData && !loading && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            <Database size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
            <h2>System Idle</h2>
            <p>Input a student profile and click Generate Plan to execute the orchestration pipeline.</p>
          </div>
        )}

        {loading && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)' }}>
            <div className="spinner" style={{ border: '4px solid rgba(59,130,246,0.1)', borderLeftColor: 'var(--accent)', borderRadius: '50%', width: '40px', height: '40px', animation: 'spin 1s linear infinite', marginBottom: '1rem' }} />
            <h2>Executing Deterministic Pipeline...</h2>
            <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
          </div>
        )}

        {roadmapData && !loading && (
          <>
            <div className="split-pane">
              <div className="panel" style={{ gridColumn: 'span 2' }}>
                <CareerSimulationView data={simData} />
              </div>
              
              <div className="panel">
                <GapReportView data={gapData} />
              </div>

              <div className="panel">
                <RoadmapView data={roadmapData} />
              </div>
            </div>

            <div className="panel" style={{ marginTop: 'auto' }}>
              <ReasonChainInspector runId={runId} apiBase={API_BASE} authHeader={AUTH_HEADER} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
