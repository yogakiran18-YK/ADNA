import React, { useState, useMemo } from 'react';
import { 
  User, Target, Play, Check, Plus, X, BookOpen, 
  Award, Search, RotateCcw, CheckCircle2
} from 'lucide-react';

// ============================================================================
// EXPANDED PREDEFINED INDUSTRY ROLES
// ============================================================================
export const PREDEFINED_ROLES = [
  // --- AI & DATA ---
  {
    id: 'ROLE_AIML',
    title: 'AI / Machine Learning Engineer',
    category: 'AI & Data',
    description: 'Specializes in training neural architectures, computer vision, NLP, and deploying ML models.',
    defaultSkills: ['Python', 'PyTorch', 'TensorFlow', 'MLOps', 'Natural Language Processing', 'Data Structures']
  },
  {
    id: 'ROLE_GENAI',
    title: 'Generative AI & LLM Solutions Engineer',
    category: 'AI & Data',
    description: 'Builds RAG systems, agentic workflows, prompt architectures, and fine-tunes open-source LLMs.',
    defaultSkills: ['Python', 'Large Language Models', 'LangChain', 'PyTorch', 'Vector Databases', 'Prompt Engineering']
  },
  {
    id: 'ROLE_DS',
    title: 'Data Scientist & Analytics Specialist',
    category: 'AI & Data',
    description: 'Applies statistical modeling, exploratory analytics, and machine learning for predictive insights.',
    defaultSkills: ['Python', 'SQL', 'Machine Learning', 'Data Structures', 'Statistics', 'Data Visualization']
  },
  {
    id: 'ROLE_DATA_ANALYST',
    title: 'Business Intelligence & Data Analyst',
    category: 'AI & Data',
    description: 'Analyzes enterprise data warehouses, creates executive dashboards, and models KPI trends.',
    defaultSkills: ['SQL', 'Python', 'PowerBI', 'Tableau', 'Data Visualization', 'Statistics']
  },
  {
    id: 'ROLE_DE',
    title: 'Data Engineer & Big Data Architect',
    category: 'AI & Data',
    description: 'Designs scalable ETL/ELT pipelines, distributed data warehouses, and streaming workflows.',
    defaultSkills: ['SQL', 'Python', 'AWS', 'Data Warehousing', 'ETL', 'Distributed Systems', 'Apache Spark']
  },

  // --- SOFTWARE & WEB ---
  {
    id: 'ROLE_FSD',
    title: 'Full Stack Web Developer',
    category: 'Software & Web',
    description: 'Builds end-to-end responsive web applications with modern frontend and scalable backends.',
    defaultSkills: ['Python', 'FastAPI', 'React', 'SQL', 'Docker', 'JavaScript', 'TypeScript']
  },
  {
    id: 'ROLE_BACKEND',
    title: 'Backend Systems Engineer',
    category: 'Software & Web',
    description: 'Focuses on high-throughput microservices, concurrency, API design, and DB persistence.',
    defaultSkills: ['Python', 'FastAPI', 'SQL', 'Docker', 'C++', 'Algorithms', 'Microservices']
  },
  {
    id: 'ROLE_UIUX_ENG',
    title: 'Frontend & UI/UX Engineer',
    category: 'Software & Web',
    description: 'Crafts high-performance, accessible, responsive client interfaces with modern UI systems.',
    defaultSkills: ['React', 'TypeScript', 'Next.js', 'JavaScript', 'UI/UX Design', 'CSS/Tailwind']
  },
  {
    id: 'ROLE_MOBILE',
    title: 'Mobile Application Engineer',
    category: 'Software & Web',
    description: 'Builds responsive cross-platform and native mobile applications for iOS and Android ecosystems.',
    defaultSkills: ['React Native', 'Flutter', 'JavaScript', 'TypeScript', 'Mobile UI/UX', 'REST APIs']
  },
  {
    id: 'ROLE_DEV',
    title: 'Core Software Engineer',
    category: 'Software & Web',
    description: 'Writes scalable application logic, system design abstractions, and optimized algorithms.',
    defaultSkills: ['Python', 'Data Structures', 'Algorithms', 'SQL', 'System Design', 'C++']
  },

  // --- CLOUD & DEVOPS ---
  {
    id: 'ROLE_DEVOPS',
    title: 'DevOps & SRE Engineer',
    category: 'Cloud & DevOps',
    description: 'Manages CI/CD pipelines, container orchestration, and cloud infrastructure reliability.',
    defaultSkills: ['Docker', 'AWS', 'Kubernetes', 'Linux', 'Python', 'CI/CD', 'Terraform']
  },
  {
    id: 'ROLE_CLOUD_ARCH',
    title: 'Cloud Solutions Architect',
    category: 'Cloud & DevOps',
    description: 'Designs resilient multi-cloud architectures, serverless frameworks, and cost-effective scaling.',
    defaultSkills: ['AWS', 'Docker', 'Kubernetes', 'Terraform', 'System Design', 'Microservices', 'Linux']
  },

  // --- SECURITY & SYSTEMS ---
  {
    id: 'ROLE_SEC',
    title: 'Cybersecurity Analyst & Systems Auditor',
    category: 'Security & Systems',
    description: 'Audits software security, cryptographic protocols, network defenses, and threat vectors.',
    defaultSkills: ['Network Security', 'Linux', 'Python', 'Cryptography', 'Security Auditing', 'Operating Systems']
  },

  // --- EMERGING TECH ---
  {
    id: 'ROLE_BLOCKCHAIN',
    title: 'Web3 & Blockchain Engineer',
    category: 'Emerging Tech',
    description: 'Develops smart contracts, decentralized applications (dApps), and token cryptoeconomics.',
    defaultSkills: ['Solidity', 'Smart Contracts', 'Cryptography', 'Ethereum', 'Web3.js', 'Distributed Systems']
  },
  {
    id: 'ROLE_EMBEDDED_IOT',
    title: 'Embedded Systems & IoT Engineer',
    category: 'Emerging Tech',
    description: 'Programs low-level firmware, microcontrollers, sensor networks, and edge computing nodes.',
    defaultSkills: ['C', 'C++', 'Embedded Linux', 'Microcontrollers', 'RTOS', 'IoT Protocols']
  },

  // --- CUSTOM ---
  {
    id: 'ROLE_CUSTOM',
    title: 'Custom Career Goal',
    category: 'Custom',
    description: 'Define your own unique role title, identifier, and custom required skills.',
    defaultSkills: ['Python', 'SQL']
  }
];

export const ROLE_CATEGORIES = [
  'All',
  'AI & Data',
  'Software & Web',
  'Cloud & DevOps',
  'Security & Systems',
  'Emerging Tech',
  'Custom'
];

// ============================================================================
// EXPANDED & CATEGORIZED SKILLS CATALOG
// ============================================================================
export const SKILL_CATEGORIES = {
  'Languages': [
    'Python', 'JavaScript', 'TypeScript', 'C++', 'Java', 'Go', 'Rust', 'C', 'SQL', 'Solidity'
  ],
  'AI / Machine Learning': [
    'PyTorch', 'TensorFlow', 'Scikit-Learn', 'Large Language Models', 'LangChain', 
    'Computer Vision', 'Natural Language Processing', 'MLOps', 'Prompt Engineering', 
    'Vector Databases', 'Deep Learning', 'Machine Learning'
  ],
  'Cloud & DevOps': [
    'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'CI/CD', 'Linux', 
    'Terraform', 'Microservices', 'System Design'
  ],
  'Web & Mobile': [
    'React', 'Next.js', 'FastAPI', 'Node.js', 'Django', 'Vue.js', 
    'React Native', 'Flutter', 'REST APIs', 'GraphQL', 'CSS/Tailwind', 'UI/UX Design', 'Mobile UI/UX'
  ],
  'Data & Analytics': [
    'PostgreSQL', 'MongoDB', 'Redis', 'Apache Spark', 'Data Warehousing', 
    'ETL', 'Snowflake', 'Tableau', 'PowerBI', 'Statistics', 'Data Visualization'
  ],
  'Core CS & Security': [
    'Data Structures', 'Algorithms', 'Cryptography', 'Network Security', 
    'Security Auditing', 'Operating Systems', 'Computer Networks', 'Distributed Systems',
    'Smart Contracts', 'Web3.js', 'Embedded Linux', 'Microcontrollers', 'RTOS', 'IoT Protocols'
  ]
};

// Flattened popular skills for quick access
export const POPULAR_SKILLS = Object.values(SKILL_CATEGORIES).flat();

// ============================================================================
// COMPLETE 8-SEMESTER CURRICULUM CATALOG
// ============================================================================
export const CURRICULUM_SEMESTERS = [
  {
    semester: 1,
    title: 'Semester 1: Foundation in Computing & Sciences',
    courses: [
      { code: 'CS101', name: 'Programming in C & Problem Solving' },
      { code: 'MA101', name: 'Engineering Mathematics I (Calculus & Linear Algebra)' },
      { code: 'PH101', name: 'Engineering Physics & Laboratory' },
      { code: 'EE101', name: 'Basic Electrical & Electronics Engineering' }
    ]
  },
  {
    semester: 2,
    title: 'Semester 2: Object-Oriented Principles & Logic',
    courses: [
      { code: 'CS102', name: 'Object-Oriented Programming with Python' },
      { code: 'MA102', name: 'Engineering Mathematics II (Probability & ODE)' },
      { code: 'CS103', name: 'Digital Logic & Computer Organization' },
      { code: 'CY101', name: 'Engineering Chemistry & Environmental Studies' }
    ]
  },
  {
    semester: 3,
    title: 'Semester 3: Core Data Structures & Systems',
    courses: [
      { code: 'CS201', name: 'Data Structures & Algorithms' },
      { code: 'CS202', name: 'Discrete Mathematics & Graph Theory' },
      { code: 'CS203', name: 'Computer Architecture & Assembly' },
      { code: 'CS204', name: 'Software Engineering Principles (Java/C++)' }
    ]
  },
  {
    semester: 4,
    title: 'Semester 4: Advanced Systems & Databases',
    courses: [
      { code: 'CS301', name: 'Design & Analysis of Algorithms' },
      { code: 'CS302', name: 'Operating Systems & System Programming' },
      { code: 'CS402', name: 'Database Management Systems (SQL & Relational DBs)' },
      { code: 'MA201', name: 'Applied Numerical Methods & Statistics' }
    ]
  },
  {
    semester: 5,
    title: 'Semester 5: Networks & Artificial Intelligence',
    courses: [
      { code: 'CS501', name: 'Computer Networks & Internet Protocols' },
      { code: 'CS401', name: 'Artificial Intelligence & Knowledge Representation' },
      { code: 'CS502', name: 'Theory of Computation & Automata' },
      { code: 'CS503', name: 'Web Technologies & Frontend Frameworks' }
    ]
  },
  {
    semester: 6,
    title: 'Semester 6: Machine Learning & Cloud Architectures',
    courses: [
      { code: 'CS601', name: 'Machine Learning & Statistical Modeling' },
      { code: 'CS602', name: 'Compiler Design & Language Engineering' },
      { code: 'CS603', name: 'Cloud Computing & Containerization (Docker/AWS)' },
      { code: 'CS604', name: 'Information & Network Security' }
    ]
  },
  {
    semester: 7,
    title: 'Semester 7: Deep Learning & Distributed Systems',
    courses: [
      { code: 'CS701', name: 'Deep Learning & Neural Networks (PyTorch)' },
      { code: 'CS702', name: 'Distributed Systems & Microservices' },
      { code: 'CS703', name: 'Big Data Engineering & Stream Analytics' },
      { code: 'CS704', name: 'Natural Language Processing & Transformers' }
    ]
  },
  {
    semester: 8,
    title: 'Semester 8: Advanced Production & Capstone',
    courses: [
      { code: 'CS801', name: 'Major Capstone Project & Defense' },
      { code: 'CS802', name: 'High Performance & GPU Computing' },
      { code: 'CS803', name: 'MLOps & Model Lifecycle Engineering' }
    ]
  }
];

const GRADE_POINTS = {
  'A+': 10.0,
  'A': 9.0,
  'B': 8.0,
  'C': 7.0,
  'D': 6.0,
  'P': null,
  'UNKNOWN': null
};

// ============================================================================
// PROFILE FORM COMPONENT
// ============================================================================
export default function ProfileForm({ onGenerate, isLoading }) {
  const [studentId, setStudentId] = useState('STU_001');
  const [currentSemester, setCurrentSemester] = useState(5);
  
  // ROLE STATE
  const [selectedRoleIndex, setSelectedRoleIndex] = useState(0);
  const [roleCategoryFilter, setRoleCategoryFilter] = useState('All');
  const [roleSearchQuery, setRoleSearchQuery] = useState('');
  const [customRoleId, setCustomRoleId] = useState('ROLE_CUSTOM');
  const [customRoleTitle, setCustomRoleTitle] = useState('Custom Tech Role');

  // SKILLS STATE (2 or more required)
  const [selectedSkills, setSelectedSkills] = useState(PREDEFINED_ROLES[0].defaultSkills);
  const [skillCategoryFilter, setSkillCategoryFilter] = useState('All');
  const [skillSearchQuery, setSkillSearchQuery] = useState('');
  const [newSkillInput, setNewSkillInput] = useState('');

  // COMPLETED COURSES STATE (Sem 1 to 8) - Captures actual records without hardcoded grades
  const [completedRecords, setCompletedRecords] = useState({
    'CS101': { course_code: 'CS101', semester_taken: 1, grade: null, grade_point: null, credits: 4 },
    'CS102': { course_code: 'CS102', semester_taken: 2, grade: null, grade_point: null, credits: 4 },
    'CS201': { course_code: 'CS201', semester_taken: 3, grade: null, grade_point: null, credits: 4 },
    'CS301': { course_code: 'CS301', semester_taken: 5, grade: null, grade_point: null, credits: 4 }
  });
  const [activeSemTab, setActiveSemTab] = useState(1);
  const [showAllSemesters, setShowAllSemesters] = useState(false);

  // Filtered Roles based on Category and Search
  const filteredRoles = useMemo(() => {
    return PREDEFINED_ROLES.map((role, originalIndex) => ({ ...role, originalIndex })).filter(role => {
      const matchesCategory = roleCategoryFilter === 'All' || role.category === roleCategoryFilter;
      const matchesSearch = !roleSearchQuery.trim() || 
        role.title.toLowerCase().includes(roleSearchQuery.toLowerCase()) ||
        role.description.toLowerCase().includes(roleSearchQuery.toLowerCase()) ||
        role.defaultSkills.some(s => s.toLowerCase().includes(roleSearchQuery.toLowerCase()));
      return matchesCategory && matchesSearch;
    });
  }, [roleCategoryFilter, roleSearchQuery]);

  // Filtered Skills based on Category and Search
  const availableSkills = useMemo(() => {
    let pool = [];
    if (skillCategoryFilter === 'All') {
      pool = POPULAR_SKILLS;
    } else {
      pool = SKILL_CATEGORIES[skillCategoryFilter] || [];
    }

    if (!skillSearchQuery.trim()) {
      return pool;
    }

    const query = skillSearchQuery.toLowerCase();
    return pool.filter(skill => skill.toLowerCase().includes(query));
  }, [skillCategoryFilter, skillSearchQuery]);

  // Handle Role Selection Click
  const handleSelectRole = (originalIndex) => {
    setSelectedRoleIndex(originalIndex);
    const role = PREDEFINED_ROLES[originalIndex];
    if (role.id !== 'ROLE_CUSTOM') {
      setSelectedSkills([...role.defaultSkills]);
    }
  };

  // Skill Add / Remove Handlers
  const handleAddSkill = (skill) => {
    const trimmed = skill.trim();
    if (!trimmed) return;
    if (!selectedSkills.some(s => s.toLowerCase() === trimmed.toLowerCase())) {
      setSelectedSkills([...selectedSkills, trimmed]);
    }
    setNewSkillInput('');
  };

  const handleRemoveSkill = (skillToRemove) => {
    setSelectedSkills(selectedSkills.filter(s => s !== skillToRemove));
  };

  const toggleSkill = (skill) => {
    const exists = selectedSkills.some(s => s.toLowerCase() === skill.toLowerCase());
    if (exists) {
      handleRemoveSkill(skill);
    } else {
      handleAddSkill(skill);
    }
  };

  const resetSkillsToDefaults = () => {
    const currentRole = PREDEFINED_ROLES[selectedRoleIndex];
    setSelectedSkills([...currentRole.defaultSkills]);
  };

  // Course Toggle: Add or Remove from completedRecords
  const toggleCourse = (courseCode, semNumber) => {
    setCompletedRecords(prev => {
      const next = { ...prev };
      if (next[courseCode]) {
        delete next[courseCode];
      } else {
        next[courseCode] = {
          course_code: courseCode,
          semester_taken: semNumber || 1,
          grade: null,
          grade_point: null,
          credits: 4
        };
      }
      return next;
    });
  };

  const updateCourseGrade = (courseCode, gradeVal) => {
    setCompletedRecords(prev => {
      if (!prev[courseCode]) return prev;
      return {
        ...prev,
        [courseCode]: {
          ...prev[courseCode],
          grade: gradeVal === 'UNKNOWN' ? null : gradeVal,
          grade_point: gradeVal in GRADE_POINTS ? GRADE_POINTS[gradeVal] : null
        }
      };
    });
  };

  const updateCourseSem = (courseCode, semVal) => {
    setCompletedRecords(prev => {
      if (!prev[courseCode]) return prev;
      return {
        ...prev,
        [courseCode]: {
          ...prev[courseCode],
          semester_taken: Number(semVal)
        }
      };
    });
  };

  // Quick Preset Handlers
  const applyCohortPreset = (maxSem) => {
    const next = {};
    CURRICULUM_SEMESTERS.forEach(sem => {
      if (sem.semester <= maxSem) {
        sem.courses.forEach(c => {
          next[c.code] = {
            course_code: c.code,
            semester_taken: sem.semester,
            grade: null,
            grade_point: null,
            credits: 4
          };
        });
      }
    });
    setCompletedRecords(next);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedSkills.length < 2) {
      alert('Please select at least 2 required skills for your target career role.');
      return;
    }

    const currentRole = PREDEFINED_ROLES[selectedRoleIndex];
    const roleId = currentRole.id === 'ROLE_CUSTOM' ? customRoleId : currentRole.id;
    const roleTitle = currentRole.id === 'ROLE_CUSTOM' ? customRoleTitle : currentRole.title;

    const courseList = Object.values(completedRecords);
    onGenerate(studentId, courseList, roleId, roleTitle, selectedSkills, currentSemester);
  };

  const currentRole = PREDEFINED_ROLES[selectedRoleIndex];
  const isCustomRole = currentRole.id === 'ROLE_CUSTOM';

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      
      {/* 1. STUDENT IDENTITY */}
      <div className="panel" style={{ padding: '1.25rem', backgroundColor: 'rgba(10, 15, 29, 0.7)' }}>
        <div className="panel-title" style={{ fontSize: '0.95rem', marginBottom: '0.75rem', color: '#38bdf8' }}>
          <User size={16} /> Student Identity
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
          <div className="form-group">
            <label>Student ID</label>
            <input 
              value={studentId} 
              onChange={e => setStudentId(e.target.value)} 
              placeholder="e.g. STU_001" 
              required 
            />
          </div>
          <div className="form-group">
            <label>Current Semester</label>
            <select
              value={currentSemester}
              onChange={e => setCurrentSemester(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '0.55rem',
                backgroundColor: '#0f172a',
                color: '#f8fafc',
                border: '1px solid #334155',
                borderRadius: '0.375rem',
                fontSize: '0.85rem'
              }}
            >
              {[1, 2, 3, 4, 5, 6, 7, 8].map(s => (
                <option key={s} value={s}>Semester {s}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* 2. TARGET CAREER ROLE (RICH INTERACTIVE OPTION CARDS) */}
      <div className="panel" style={{ padding: '1.25rem', backgroundColor: 'rgba(10, 15, 29, 0.7)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <div className="panel-title" style={{ fontSize: '0.95rem', color: '#818cf8' }}>
            <Target size={16} /> Target Career Role Options ({PREDEFINED_ROLES.length})
          </div>
          <span style={{ 
            fontSize: '0.75rem', 
            fontWeight: 700, 
            color: '#38bdf8', 
            backgroundColor: 'rgba(56, 189, 248, 0.12)', 
            padding: '0.2rem 0.55rem', 
            borderRadius: '999px',
            border: '1px solid rgba(56, 189, 248, 0.25)'
          }}>
            Selected: {currentRole.title}
          </span>
        </div>

        {/* Role Category Filter Tabs */}
        <div className="options-category-tabs" style={{ marginBottom: '0.65rem' }}>
          {ROLE_CATEGORIES.map(cat => {
            const count = cat === 'All' 
              ? PREDEFINED_ROLES.length 
              : PREDEFINED_ROLES.filter(r => r.category === cat).length;
            return (
              <button
                key={cat}
                type="button"
                onClick={() => setRoleCategoryFilter(cat)}
                className={`options-category-tab ${roleCategoryFilter === cat ? 'active' : ''}`}
              >
                {cat} ({count})
              </button>
            );
          })}
        </div>

        {/* Role Search Bar */}
        <div className="options-search-container" style={{ marginBottom: '0.75rem' }}>
          <Search size={14} className="options-search-icon" />
          <input
            type="text"
            className="options-search-input"
            placeholder="Search roles by title, keyword, or skills (e.g. LLM, DevOps, Cloud)..."
            value={roleSearchQuery}
            onChange={e => setRoleSearchQuery(e.target.value)}
          />
          {roleSearchQuery && (
            <button
              type="button"
              onClick={() => setRoleSearchQuery('')}
              style={{
                position: 'absolute',
                right: '0.75rem',
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center'
              }}
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Role Option Cards Grid */}
        <div className="role-options-grid">
          {filteredRoles.map(role => {
            const isSelected = selectedRoleIndex === role.originalIndex;
            return (
              <div
                key={role.id}
                onClick={() => handleSelectRole(role.originalIndex)}
                className={`role-option-card ${isSelected ? 'selected' : ''}`}
                role="button"
                tabIndex={0}
              >
                <div>
                  <div className="role-card-header">
                    <span className="role-card-title">{role.title}</span>
                    <div className="role-radio-circle">
                      {isSelected && <Check size={12} />}
                    </div>
                  </div>
                  <div style={{ marginTop: '4px', marginBottom: '6px' }}>
                    <span className="role-card-category-badge">{role.category}</span>
                  </div>
                  <p className="role-card-desc">{role.description}</p>
                </div>

                <div className="role-card-skills-preview">
                  {role.defaultSkills.slice(0, 4).map(skill => (
                    <span key={skill} className="role-card-skill-tag">{skill}</span>
                  ))}
                  {role.defaultSkills.length > 4 && (
                    <span className="role-card-skill-tag" style={{ color: '#38bdf8' }}>
                      +{role.defaultSkills.length - 4} more
                    </span>
                  )}
                </div>
              </div>
            );
          })}
          {filteredRoles.length === 0 && (
            <div style={{ gridColumn: '1 / -1', padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No roles match "{roleSearchQuery}". Try adjusting your search query or category filter.
            </div>
          )}
        </div>

        {/* Custom Role Fields if Custom selected */}
        {isCustomRole && (
          <div style={{ 
            marginTop: '0.85rem', 
            padding: '0.85rem', 
            borderRadius: '8px', 
            background: 'rgba(99, 102, 241, 0.1)', 
            border: '1px solid rgba(99, 102, 241, 0.25)',
            display: 'grid', 
            gridTemplateColumns: '1fr 1fr', 
            gap: '0.65rem' 
          }}>
            <div className="form-group" style={{ margin: 0 }}>
              <label>Custom Role Identifier</label>
              <input 
                value={customRoleId} 
                onChange={e => setCustomRoleId(e.target.value)} 
                placeholder="e.g. ROLE_ROBOTICS"
                required 
              />
            </div>
            <div className="form-group" style={{ margin: 0 }}>
              <label>Custom Role Title</label>
              <input 
                value={customRoleTitle} 
                onChange={e => setCustomRoleTitle(e.target.value)} 
                placeholder="e.g. Autonomous Robotics Specialist"
                required 
              />
            </div>
          </div>
        )}
      </div>

      {/* 3. TARGET SKILLS (INTERACTIVE CATEGORIZED OPTIONS & MULTI-PICKER) */}
      <div className="panel" style={{ padding: '1.25rem', backgroundColor: 'rgba(10, 15, 29, 0.7)' }}>
        
        {/* Header with Count & Actions */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <div className="panel-title" style={{ fontSize: '0.95rem', color: '#10b981' }}>
            <Award size={16} /> Target Skills ({selectedSkills.length} Selected)
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              onClick={resetSkillsToDefaults}
              className="preset-btn"
              style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem' }}
              title="Reset to default skills for selected role"
            >
              <RotateCcw size={12} /> Reset to Role Defaults
            </button>
            <button
              type="button"
              onClick={() => setSelectedSkills([])}
              className="preset-btn clear"
              style={{ fontSize: '0.72rem' }}
              title="Clear all selected skills"
            >
              Clear All
            </button>
          </div>
        </div>

        {/* Minimum Threshold Badge */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          marginBottom: '0.75rem',
          fontSize: '0.75rem',
          padding: '0.35rem 0.65rem',
          borderRadius: '6px',
          background: selectedSkills.length >= 2 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.12)',
          border: `1px solid ${selectedSkills.length >= 2 ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.3)'}`,
          color: selectedSkills.length >= 2 ? '#10b981' : '#f59e0b'
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 600 }}>
            {selectedSkills.length >= 2 ? <CheckCircle2 size={13} /> : '⚠️'}
            {selectedSkills.length >= 2 
              ? `Ready: ${selectedSkills.length} target skills configured (Minimum ≥ 2 met)` 
              : 'Please select at least 2 target skills to compute market alignment.'}
          </span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
            Click any skill option below to toggle
          </span>
        </div>

        {/* Selected Skills Tray (Chips) */}
        <div style={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          gap: '6px', 
          marginBottom: '1rem', 
          minHeight: '42px',
          padding: '0.65rem',
          borderRadius: '8px',
          backgroundColor: 'rgba(15, 23, 42, 0.65)',
          border: '1px solid rgba(255, 255, 255, 0.08)'
        }}>
          {selectedSkills.map(skill => (
            <span key={skill} className="skill-chip-removable">
              {skill}
              <button 
                type="button" 
                onClick={() => handleRemoveSkill(skill)}
                className="chip-remove-btn"
                title={`Remove ${skill}`}
              >
                <X size={12} />
              </button>
            </span>
          ))}
          {selectedSkills.length === 0 && (
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic', alignSelf: 'center' }}>
              No skills selected yet. Click option chips below or type a custom skill.
            </span>
          )}
        </div>

        {/* Skill Category Filter Tabs */}
        <div className="options-category-tabs" style={{ marginBottom: '0.65rem' }}>
          <button
            type="button"
            onClick={() => setSkillCategoryFilter('All')}
            className={`options-category-tab ${skillCategoryFilter === 'All' ? 'active' : ''}`}
          >
            All Skills ({POPULAR_SKILLS.length})
          </button>
          {Object.keys(SKILL_CATEGORIES).map(cat => (
            <button
              key={cat}
              type="button"
              onClick={() => setSkillCategoryFilter(cat)}
              className={`options-category-tab ${skillCategoryFilter === cat ? 'active' : ''}`}
            >
              {cat} ({SKILL_CATEGORIES[cat].length})
            </button>
          ))}
        </div>

        {/* Skill Search & Custom Skill Input Bar */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <div className="options-search-container">
            <Search size={14} className="options-search-icon" />
            <input
              type="text"
              className="options-search-input"
              placeholder="Filter skill options (e.g. PyTorch, React, AWS)..."
              value={skillSearchQuery}
              onChange={e => setSkillSearchQuery(e.target.value)}
            />
            {skillSearchQuery && (
              <button
                type="button"
                onClick={() => setSkillSearchQuery('')}
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <X size={14} />
              </button>
            )}
          </div>

          <div style={{ display: 'flex', gap: '6px' }}>
            <input
              type="text"
              placeholder="Add unlisted skill..."
              value={newSkillInput}
              onChange={e => setNewSkillInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleAddSkill(newSkillInput);
                }
              }}
              style={{ fontSize: '0.8rem', padding: '0.45rem 0.65rem' }}
            />
            <button
              type="button"
              onClick={() => handleAddSkill(newSkillInput)}
              style={{
                padding: '0.45rem 0.85rem',
                backgroundColor: '#10b981',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                whiteSpace: 'nowrap'
              }}
            >
              <Plus size={14} /> Add
            </button>
          </div>
        </div>

        {/* Interactive Skill Options Grid */}
        <div className="skill-options-grid">
          {availableSkills.map(skill => {
            const isSelected = selectedSkills.some(s => s.toLowerCase() === skill.toLowerCase());
            return (
              <button
                key={skill}
                type="button"
                onClick={() => toggleSkill(skill)}
                className={`skill-option-btn ${isSelected ? 'selected' : ''}`}
                title={isSelected ? `Click to remove ${skill}` : `Click to add ${skill}`}
              >
                <span className="skill-option-icon">
                  {isSelected ? <Check size={12} /> : <Plus size={12} />}
                </span>
                {skill}
              </button>
            );
          })}
          {availableSkills.length === 0 && (
            <div style={{ width: '100%', padding: '1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              No skills found matching "{skillSearchQuery}". You can add it using the "Add unlisted skill" input above!
            </div>
          )}
        </div>
      </div>

      {/* 4. COMPLETED COURSES (SEM 1 TO SEM 8 SUBJECTS CATALOG) */}
      <div className="panel" style={{ padding: '1.25rem', backgroundColor: 'rgba(10, 15, 29, 0.7)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <div className="panel-title" style={{ fontSize: '0.95rem', color: '#f59e0b' }}>
            <BookOpen size={16} /> Completed Courses
          </div>
          <span style={{ 
            fontSize: '0.75rem', 
            fontWeight: 700, 
            color: '#38bdf8', 
            backgroundColor: 'rgba(56, 189, 248, 0.12)', 
            padding: '0.15rem 0.5rem', 
            borderRadius: '999px' 
          }}>
            {Object.keys(completedRecords).length} Completed
          </span>
        </div>

        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
          Select the subjects you have already completed from Semester 1 through Semester 8. You can optionally record your actual grade; unrecorded grades are treated truthfully as unrecorded.
        </p>

        {/* Fast Cohort Preset Buttons */}
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '0.85rem' }}>
          <button 
            type="button" 
            onClick={() => applyCohortPreset(2)} 
            className="preset-btn"
            title="Complete Sem 1 & 2"
          >
            Freshman (Sem 1-2)
          </button>
          <button 
            type="button" 
            onClick={() => applyCohortPreset(4)} 
            className="preset-btn"
            title="Complete Sem 1-4"
          >
            Sophomore (Sem 1-4)
          </button>
          <button 
            type="button" 
            onClick={() => applyCohortPreset(6)} 
            className="preset-btn"
            title="Complete Sem 1-6"
          >
            Junior (Sem 1-6)
          </button>
          <button 
            type="button" 
            onClick={() => setCompletedRecords({})} 
            className="preset-btn clear"
            title="Clear all selected courses"
          >
            Clear
          </button>
        </div>

        {/* View Mode Toggle: Tabbed vs All Semesters */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.65rem' }}>
          <div style={{ display: 'flex', gap: '3px', flexWrap: 'wrap', flex: 1 }}>
            {!showAllSemesters && CURRICULUM_SEMESTERS.map(s => {
              const semCourseCodes = s.courses.map(c => c.code);
              const completedInSem = semCourseCodes.filter(c => !!completedRecords[c]).length;
              return (
                <button
                  key={s.semester}
                  type="button"
                  onClick={() => setActiveSemTab(s.semester)}
                  className={`sem-tab-pill ${activeSemTab === s.semester ? 'active' : ''}`}
                >
                  S{s.semester} {completedInSem > 0 && <span className="sem-count-dot">{completedInSem}</span>}
                </button>
              );
            })}
          </div>

          <button
            type="button"
            onClick={() => setShowAllSemesters(!showAllSemesters)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#38bdf8',
              fontSize: '0.7rem',
              fontWeight: 600,
              cursor: 'pointer',
              padding: '0.2rem 0.4rem'
            }}
          >
            {showAllSemesters ? 'Tabbed View' : 'View All 8 Sems'}
          </button>
        </div>

        {/* Course List: Tabbed or All 8 Semesters */}
        <div style={{ 
          maxHeight: '280px', 
          overflowY: 'auto', 
          paddingRight: '4px',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem'
        }}>
          {CURRICULUM_SEMESTERS
            .filter(s => showAllSemesters || s.semester === activeSemTab)
            .map(sem => (
              <div key={sem.semester} style={{ marginBottom: showAllSemesters ? '0.75rem' : '0' }}>
                {showAllSemesters && (
                  <div style={{ 
                    fontSize: '0.75rem', 
                    fontWeight: 700, 
                    color: '#818cf8', 
                    marginBottom: '0.35rem',
                    borderBottom: '1px solid rgba(255,255,255,0.06)',
                    paddingBottom: '2px'
                  }}>
                    {sem.title}
                  </div>
                )}
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  {sem.courses.map(course => {
                    const rec = completedRecords[course.code];
                    const isChecked = !!rec;
                    return (
                      <div 
                        key={course.code}
                        className={`course-checkbox-row ${isChecked ? 'checked' : ''}`}
                        style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap' }}
                      >
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, margin: 0, cursor: 'pointer' }}>
                          <input 
                            type="checkbox" 
                            checked={isChecked}
                            onChange={() => toggleCourse(course.code, sem.semester)}
                            style={{ margin: 0, width: '15px', height: '15px', cursor: 'pointer' }}
                          />
                          <span className="course-code-tag">{course.code}</span>
                          <span className="course-name-text">{course.name}</span>
                        </label>

                        {isChecked && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <select
                              value={rec.grade || 'UNKNOWN'}
                              onChange={e => updateCourseGrade(course.code, e.target.value)}
                              title="Grade (Select Unknown if not yet graded)"
                              style={{
                                fontSize: '0.72rem',
                                padding: '0.2rem 0.35rem',
                                backgroundColor: '#1e293b',
                                color: rec.grade ? '#38bdf8' : '#94a3b8',
                                border: '1px solid #475569',
                                borderRadius: '4px'
                              }}
                            >
                              <option value="UNKNOWN">Grade: Unknown</option>
                              <option value="A+">A+ (10.0)</option>
                              <option value="A">A (9.0)</option>
                              <option value="B">B (8.0)</option>
                              <option value="C">C (7.0)</option>
                              <option value="D">D (6.0)</option>
                              <option value="P">P (Pass/No GPA)</option>
                            </select>

                            <select
                              value={rec.semester_taken || sem.semester}
                              onChange={e => updateCourseSem(course.code, e.target.value)}
                              title="Semester taken"
                              style={{
                                fontSize: '0.72rem',
                                padding: '0.2rem 0.3rem',
                                backgroundColor: '#1e293b',
                                color: '#94a3b8',
                                border: '1px solid #475569',
                                borderRadius: '4px'
                              }}
                            >
                              {[1, 2, 3, 4, 5, 6, 7, 8].map(s => (
                                <option key={s} value={s}>Sem {s}</option>
                              ))}
                            </select>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* GENERATE PLAN SUBMIT BUTTON */}
      <button 
        type="submit" 
        disabled={isLoading || selectedSkills.length < 2}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          padding: '0.85rem',
          fontSize: '1rem',
          fontWeight: 700,
          background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
          boxShadow: '0 4px 15px rgba(59, 130, 246, 0.4)'
        }}
      >
        <Play size={18} /> {isLoading ? 'Executing Orchestrator...' : 'Generate Adaptive Degree Plan'}
      </button>

    </form>
  );
}
