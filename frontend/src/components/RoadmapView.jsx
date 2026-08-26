import React from 'react';
import { GraduationCap } from 'lucide-react';

export default function RoadmapView({ data }) {
  if (!data || !data.semesters) return null;

  return (
    <div>
      <div className="panel-title">
        <GraduationCap size={20} color="var(--accent)" /> 
        Generated Roadmap
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.5rem' }}>
        {data.semesters.map((courses, idx) => (
          <div key={idx} style={{ 
            border: '1px solid var(--border-color)',
            borderRadius: '0.5rem',
            overflow: 'hidden'
          }}>
            <div style={{ 
              backgroundColor: 'var(--bg-dark)', 
              padding: '0.75rem 1rem', 
              fontSize: '0.875rem', 
              fontWeight: 600,
              borderBottom: '1px solid var(--border-color)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span>Semester {idx + 1}</span>
              <span className="badge">{courses.length} courses</span>
            </div>
            
            <div style={{ padding: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              {courses.map(course => (
                <div key={course} style={{
                  backgroundColor: 'rgba(59, 130, 246, 0.1)',
                  color: 'var(--accent)',
                  padding: '0.5rem 1rem',
                  borderRadius: '0.25rem',
                  fontWeight: 500,
                  fontSize: '0.9rem',
                  border: '1px solid rgba(59, 130, 246, 0.2)'
                }}>
                  {course}
                </div>
              ))}
              {courses.length === 0 && (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', fontStyle: 'italic' }}>No courses assigned.</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
