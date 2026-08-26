import React, { useState } from 'react';
import { User, Target, Play } from 'lucide-react';

export default function ProfileForm({ onGenerate, isLoading }) {
  const [studentId, setStudentId] = useState('STU_001');
  const [completedStr, setCompletedStr] = useState('CS101');
  
  const [roleId, setRoleId] = useState('ROLE_DEV');
  const [roleTitle, setRoleTitle] = useState('Software Engineer');
  const [roleSkills, setRoleSkills] = useState('Python, DataStructures');

  const handleSubmit = (e) => {
    e.preventDefault();
    const courses = completedStr.split(',').map(s => s.trim()).filter(Boolean);
    const skills = roleSkills.split(',').map(s => s.trim()).filter(Boolean);
    onGenerate(studentId, courses, roleId, roleTitle, skills);
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      <div className="panel" style={{ padding: '1rem', backgroundColor: 'var(--bg-dark)' }}>
        <div className="panel-title" style={{ fontSize: '1rem', marginBottom: '1rem' }}><User size={18} /> Student Profile</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="form-group">
            <label>Student ID</label>
            <input value={studentId} onChange={e => setStudentId(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Completed Courses (comma-separated)</label>
            <input value={completedStr} onChange={e => setCompletedStr(e.target.value)} placeholder="e.g. CS101, CS102" />
          </div>
        </div>
      </div>

      <div className="panel" style={{ padding: '1rem', backgroundColor: 'var(--bg-dark)' }}>
        <div className="panel-title" style={{ fontSize: '1rem', marginBottom: '1rem' }}><Target size={18} /> Target Role</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="form-group">
            <label>Role ID</label>
            <input value={roleId} onChange={e => setRoleId(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Role Title</label>
            <input value={roleTitle} onChange={e => setRoleTitle(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Required Skills (comma-separated)</label>
            <input value={roleSkills} onChange={e => setRoleSkills(e.target.value)} required />
          </div>
        </div>
      </div>

      <button type="submit" disabled={isLoading}>
        <Play size={18} /> {isLoading ? 'Executing...' : 'Generate Plan'}
      </button>

    </form>
  );
}
