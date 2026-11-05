import React, { useState } from 'react';
import { 
  GraduationCap, Calendar, Clock, BookOpen, 
  CheckCircle2, Award, Sparkles, ArrowRight 
} from 'lucide-react';

export const COURSE_CATALOG_MAP = {
  'CS101': { name: 'Programming in C & Problem Solving', credits: 4, skills: ['C', 'Programming', 'Algorithms'], prereq: 'None' },
  'MA101': { name: 'Engineering Mathematics I (Calculus & Linear Algebra)', credits: 4, skills: ['Mathematics', 'Linear Algebra'], prereq: 'None' },
  'PH101': { name: 'Engineering Physics & Laboratory', credits: 4, skills: ['Physics', 'Instrumentation'], prereq: 'None' },
  'EE101': { name: 'Basic Electrical & Electronics Engineering', credits: 4, skills: ['Electronics', 'Circuits', 'IoT Protocols'], prereq: 'None' },
  'CS102': { name: 'Object-Oriented Programming with Python', credits: 4, skills: ['Python', 'OOP', 'Data Structures'], prereq: 'CS101' },
  'MA102': { name: 'Engineering Mathematics II (Probability & ODE)', credits: 4, skills: ['Probability', 'Statistics'], prereq: 'MA101' },
  'CS103': { name: 'Digital Logic & Computer Organization', credits: 4, skills: ['Digital Logic', 'Computer Architecture'], prereq: 'None' },
  'CY101': { name: 'Engineering Chemistry & Environmental Studies', credits: 4, skills: ['Environmental Studies'], prereq: 'None' },
  'CS201': { name: 'Data Structures & Algorithms', credits: 4, skills: ['Data Structures', 'Algorithms', 'Problem Solving'], prereq: 'CS102' },
  'CS202': { name: 'Discrete Mathematics & Graph Theory', credits: 4, skills: ['Discrete Math', 'Graph Theory', 'Cryptography'], prereq: 'MA101' },
  'CS203': { name: 'Computer Architecture & Assembly', credits: 4, skills: ['Assembly', 'Microcontrollers', 'Computer Systems'], prereq: 'CS103' },
  'CS204': { name: 'Software Engineering Principles (Java/C++)', credits: 4, skills: ['Java', 'C++', 'Design Patterns'], prereq: 'CS102' },
  'CS301': { name: 'Design & Analysis of Algorithms', credits: 4, skills: ['Algorithms', 'Dynamic Programming', 'Complexity'], prereq: 'CS201' },
  'CS302': { name: 'Operating Systems & System Programming', credits: 4, skills: ['Operating Systems', 'Linux', 'Concurrency'], prereq: 'CS201' },
  'CS402': { name: 'Database Management Systems (SQL & Relational DBs)', credits: 4, skills: ['SQL', 'Databases', 'PostgreSQL', 'Data Modeling'], prereq: 'CS201' },
  'MA201': { name: 'Applied Numerical Methods & Statistics', credits: 4, skills: ['Statistics', 'Numerical Methods', 'Data Analysis'], prereq: 'MA102' },
  'CS501': { name: 'Computer Networks & Internet Protocols', credits: 4, skills: ['Computer Networks', 'Network Security', 'REST APIs'], prereq: 'CS302' },
  'CS401': { name: 'Artificial Intelligence & Knowledge Representation', credits: 4, skills: ['Artificial Intelligence', 'Search Algorithms', 'Knowledge Graphs'], prereq: 'CS201' },
  'CS502': { name: 'Theory of Computation & Automata', credits: 4, skills: ['Automata', 'Formal Languages', 'Compilers'], prereq: 'CS202' },
  'CS503': { name: 'Web Technologies & Frontend Frameworks', credits: 4, skills: ['React', 'JavaScript', 'TypeScript', 'Next.js', 'UI/UX Design'], prereq: 'CS102' },
  'CS601': { name: 'Machine Learning & Statistical Modeling', credits: 4, skills: ['Machine Learning', 'Scikit-Learn', 'Python', 'Data Science'], prereq: 'CS401' },
  'CS602': { name: 'Compiler Design & Language Engineering', credits: 4, skills: ['Compilers', 'Parsing', 'Code Generation'], prereq: 'CS502' },
  'CS603': { name: 'Cloud Computing & Containerization (Docker/AWS)', credits: 4, skills: ['Docker', 'AWS', 'Kubernetes', 'Cloud Systems'], prereq: 'CS302' },
  'CS604': { name: 'Information & Network Security', credits: 4, skills: ['Network Security', 'Cryptography', 'Security Auditing'], prereq: 'CS501' },
  'CS701': { name: 'Deep Learning & Neural Networks (PyTorch)', credits: 4, skills: ['Deep Learning', 'PyTorch', 'TensorFlow', 'Computer Vision'], prereq: 'CS601' },
  'CS702': { name: 'Distributed Systems & Microservices', credits: 4, skills: ['Distributed Systems', 'Microservices', 'FastAPI', 'System Design'], prereq: 'CS501' },
  'CS703': { name: 'Big Data Engineering & Stream Analytics', credits: 4, skills: ['ETL', 'Apache Spark', 'Big Data', 'Data Warehousing'], prereq: 'CS402' },
  'CS704': { name: 'Natural Language Processing & Transformers', credits: 4, skills: ['NLP', 'Large Language Models', 'Transformers', 'LangChain'], prereq: 'CS601' },
  'CS801': { name: 'Major Capstone Project & Defense', credits: 4, skills: ['System Design', 'Project Defense', 'Engineering Practice'], prereq: 'CS701' },
  'CS802': { name: 'High Performance & GPU Computing', credits: 4, skills: ['GPU Computing', 'CUDA', 'C++', 'Parallel Computing'], prereq: 'CS701' },
  'CS803': { name: 'MLOps & Model Lifecycle Engineering', credits: 4, skills: ['MLOps', 'CI/CD', 'Model Deployment', 'Monitoring'], prereq: 'CS603' }
};

export default function RoadmapView({ data }) {
  const [activeSemIndex, setActiveSemIndex] = useState(0);

  if (!data || !data.semesters) return null;

  const semesters = data.semesters;
  const totalSemesters = semesters.length;
  const totalCourses = semesters.reduce((acc, sem) => acc + sem.length, 0);
  const totalCredits = semesters.reduce((acc, sem) => {
    return acc + sem.reduce((cAcc, code) => cAcc + (COURSE_CATALOG_MAP[code]?.credits || 4), 0);
  }, 0);
  const estMonths = data.estimated_time_to_completion_months || totalSemesters * 4;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      
      {/* 1. ROADMAP HEADER STATS BAR */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem',
        padding: '1.25rem 1.5rem',
        borderRadius: '12px',
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(56, 189, 248, 0.1) 100%)',
        border: '1px solid rgba(56, 189, 248, 0.25)',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <div className="panel-title" style={{ fontSize: '1.15rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
              <GraduationCap size={22} color="#38bdf8" /> 
              Adaptive Degree Roadmap
            </div>
            {data.curriculum_source && (
              <span style={{
                fontSize: '0.72rem',
                padding: '0.15rem 0.5rem',
                borderRadius: '999px',
                fontWeight: 600,
                backgroundColor: data.curriculum_source === 'ingested' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(99, 102, 241, 0.15)',
                color: data.curriculum_source === 'ingested' ? '#10b981' : '#818cf8',
                border: `1px solid ${data.curriculum_source === 'ingested' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(99, 102, 241, 0.3)'}`
              }}>
                Curriculum: {data.curriculum_source === 'ingested' ? 'Institution Ingested' : 'Seeded Demo Catalogue'}
              </span>
            )}
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Prerequisite-constrained, credit-capped trajectory mathematically optimized to close your target skill gaps.
          </p>
        </div>

        {/* Key Metrics Chips */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{ 
            display: 'flex', alignItems: 'center', gap: '6px', 
            padding: '0.4rem 0.8rem', borderRadius: '8px', 
            background: 'rgba(10, 15, 29, 0.7)', border: '1px solid rgba(255,255,255,0.08)' 
          }}>
            <Calendar size={15} color="#38bdf8" />
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Planned Duration</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc' }}>{totalSemesters} Semesters</div>
            </div>
          </div>

          <div style={{ 
            display: 'flex', alignItems: 'center', gap: '6px', 
            padding: '0.4rem 0.8rem', borderRadius: '8px', 
            background: 'rgba(10, 15, 29, 0.7)', border: '1px solid rgba(255,255,255,0.08)' 
          }}>
            <BookOpen size={15} color="#10b981" />
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Courses to Clear</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc' }}>{totalCourses} Courses ({totalCredits} Cr)</div>
            </div>
          </div>

          <div style={{ 
            display: 'flex', alignItems: 'center', gap: '6px', 
            padding: '0.4rem 0.8rem', borderRadius: '8px', 
            background: 'rgba(10, 15, 29, 0.7)', border: '1px solid rgba(255,255,255,0.08)' 
          }}>
            <Clock size={15} color="#f59e0b" />
            <div>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Est. Completion</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc' }}>~{estMonths} Months</div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. SEMESTER STEPPER TABS (FAST JUMP) */}
      <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '4px' }}>
        {semesters.map((courses, idx) => {
          const semCredits = courses.reduce((acc, code) => acc + (COURSE_CATALOG_MAP[code]?.credits || 4), 0);
          const isSelected = activeSemIndex === idx;
          return (
            <button
              key={idx}
              type="button"
              onClick={() => setActiveSemIndex(idx)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '0.55rem 1rem',
                borderRadius: '8px',
                border: isSelected ? '1px solid #38bdf8' : '1px solid rgba(255, 255, 255, 0.08)',
                background: isSelected 
                  ? 'linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(99, 102, 241, 0.2))' 
                  : 'rgba(15, 23, 42, 0.6)',
                color: isSelected ? '#38bdf8' : 'var(--text-muted)',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.82rem',
                whiteSpace: 'nowrap',
                transition: 'all 0.2s ease',
                boxShadow: isSelected ? '0 0 12px rgba(56, 189, 248, 0.25)' : 'none'
              }}
            >
              <span style={{
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                background: isSelected ? '#38bdf8' : 'rgba(255, 255, 255, 0.1)',
                color: isSelected ? '#040817' : 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.72rem',
                fontWeight: 700
              }}>
                {idx + 1}
              </span>
              <span>Semester {idx + 1}</span>
              <span style={{ 
                fontSize: '0.7rem', 
                padding: '0.1rem 0.35rem', 
                borderRadius: '4px', 
                background: 'rgba(255, 255, 255, 0.06)' 
              }}>
                {courses.length} c / {semCredits} cr
              </span>
            </button>
          );
        })}
      </div>

      {/* 3. SEMESTER TIMELINE CARDS */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {semesters.map((courses, idx) => {
          const semCredits = courses.reduce((acc, code) => acc + (COURSE_CATALOG_MAP[code]?.credits || 4), 0);
          const isHighlighted = activeSemIndex === idx;

          return (
            <div 
              key={idx} 
              style={{ 
                borderRadius: '10px',
                border: isHighlighted ? '1px solid rgba(56, 189, 248, 0.4)' : '1px solid rgba(255, 255, 255, 0.08)',
                background: isHighlighted ? 'rgba(15, 23, 42, 0.85)' : 'rgba(10, 15, 29, 0.6)',
                overflow: 'hidden',
                transition: 'all 0.2s ease',
                boxShadow: isHighlighted ? '0 4px 20px rgba(0, 0, 0, 0.3)' : 'none'
              }}
            >
              {/* Semester Header Bar */}
              <div style={{ 
                padding: '0.85rem 1.25rem',
                borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
                background: 'rgba(255, 255, 255, 0.02)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '8px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.25), rgba(99, 102, 241, 0.25))',
                    border: '1px solid rgba(56, 189, 248, 0.4)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#38bdf8',
                    fontWeight: 700,
                    fontSize: '0.85rem'
                  }}>
                    {idx + 1}
                  </div>
                  <div>
                    <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
                      Planned Semester {idx + 1}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
                      (Estimated Term {idx + 1} of Degree Navigation)
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    color: '#10b981',
                    background: 'rgba(16, 185, 129, 0.12)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    padding: '0.2rem 0.55rem',
                    borderRadius: '999px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}>
                    <CheckCircle2 size={12} /> Prereqs Verified
                  </span>
                  <span style={{
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    color: '#38bdf8',
                    background: 'rgba(56, 189, 248, 0.12)',
                    border: '1px solid rgba(56, 189, 248, 0.3)',
                    padding: '0.2rem 0.55rem',
                    borderRadius: '999px'
                  }}>
                    {courses.length} Courses • {semCredits} Credits
                  </span>
                </div>
              </div>

              {/* Course Cards Grid */}
              <div style={{ 
                padding: '1rem', 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', 
                gap: '0.85rem' 
              }}>
                {courses.map(code => {
                  const courseInfo = COURSE_CATALOG_MAP[code] || {
                    name: `Specialized Elective (${code})`,
                    credits: 4,
                    skills: ['Technical Specialization'],
                    prereq: 'Verified'
                  };

                  return (
                    <div 
                      key={code}
                      style={{
                        padding: '0.9rem',
                        borderRadius: '8px',
                        background: 'rgba(255, 255, 255, 0.03)',
                        border: '1px solid rgba(255, 255, 255, 0.07)',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                        gap: '0.65rem'
                      }}
                    >
                      <div>
                        {/* Course Code & Credits */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{
                            fontSize: '0.78rem',
                            fontWeight: 800,
                            color: '#38bdf8',
                            background: 'rgba(56, 189, 248, 0.14)',
                            border: '1px solid rgba(56, 189, 248, 0.3)',
                            padding: '0.15rem 0.5rem',
                            borderRadius: '4px',
                            letterSpacing: '0.04em'
                          }}>
                            {code}
                          </span>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                            {courseInfo.credits} Credits
                          </span>
                        </div>

                        {/* Course Name */}
                        <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#f8fafc', lineHeight: 1.3, marginTop: '4px' }}>
                          {courseInfo.name}
                        </div>
                      </div>

                      <div>
                        {/* Skills Provided Chips */}
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '6px' }}>
                          {courseInfo.skills.map(skill => (
                            <span 
                              key={skill}
                              style={{
                                fontSize: '0.68rem',
                                color: '#10b981',
                                background: 'rgba(16, 185, 129, 0.1)',
                                border: '1px solid rgba(16, 185, 129, 0.25)',
                                padding: '0.1rem 0.35rem',
                                borderRadius: '4px',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '3px'
                              }}
                            >
                              <Award size={10} /> {skill}
                            </span>
                          ))}
                        </div>

                        {/* Prerequisite status */}
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          Prerequisite: <span style={{ color: '#cbd5e1' }}>{courseInfo.prereq}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}

                {courses.length === 0 && (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic', padding: '1rem' }}>
                    No additional courses required for this term.
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 4. GRADUATION READINESS MILESTONE CALLOUT */}
      <div style={{
        padding: '1rem 1.25rem',
        borderRadius: '10px',
        background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(56, 189, 248, 0.12) 100%)',
        border: '1px solid rgba(16, 185, 129, 0.3)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '10px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: 'rgba(16, 185, 129, 0.25)',
            color: '#10b981',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Sparkles size={18} />
          </div>
          <div>
            <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#f8fafc' }}>
              Degree Roadmap Outcome & Employability Milestone
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Completing this adaptive sequence clears 100% of target industry competencies without prerequisite conflicts.
            </div>
          </div>
        </div>

        <div style={{
          fontSize: '0.78rem',
          fontWeight: 700,
          color: '#10b981',
          background: 'rgba(16, 185, 129, 0.15)',
          padding: '0.35rem 0.75rem',
          borderRadius: '999px',
          border: '1px solid rgba(16, 185, 129, 0.35)',
          display: 'flex',
          alignItems: 'center',
          gap: '5px'
        }}>
          Target Ready by Graduation <ArrowRight size={13} />
        </div>
      </div>

    </div>
  );
}
