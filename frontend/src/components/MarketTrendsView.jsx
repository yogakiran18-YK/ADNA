import React, { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, Database, RefreshCw, Briefcase, 
  Search, Sparkles, CheckCircle2, Flame, 
  ArrowUpRight, Clock, Layers, Zap
} from 'lucide-react';

export default function MarketTrendsView({ apiBase }) {
  const [trends, setTrends] = useState(null);
  const [recentPostings, setRecentPostings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [ingesting, setIngesting] = useState(false);
  const [ingestCount, setIngestCount] = useState(50);
  const [notification, setNotification] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [sortBy, setSortBy] = useState('demand'); // 'demand' | 'frequency' | 'recency'

  const fetchTrendsData = useCallback(async () => {
    try {
      setLoading(true);
      setFetchError(null);
      const [trendsRes, postingsRes] = await Promise.all([
        fetch(`${apiBase}/api/v1/market/trends`),
        fetch(`${apiBase}/api/v1/market/postings/recent?limit=8`)
      ]);

      if (!trendsRes.ok) {
        throw new Error(`Failed to load market trends (${trendsRes.status})`);
      }
      const data = await trendsRes.json();
      setTrends(data);

      if (postingsRes.ok) {
        const posts = await postingsRes.json();
        setRecentPostings(posts);
      }
    } catch (err) {
      console.error('Failed to load market trends', err);
      setFetchError(err.message || 'Failed to load market trends from server.');
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  useEffect(() => {
    fetchTrendsData();
  }, [fetchTrendsData]);

  const handleIngestKaggle = async () => {
    setIngesting(true);
    setNotification(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/market/kaggle/ingest?limit=${ingestCount}`, {
        method: 'POST'
      });
      if (!res.ok) throw new Error('Failed to ingest Kaggle postings');
      const data = await res.json();
      setTrends(data);
      
      // Refresh recent postings preview
      const postingsRes = await fetch(`${apiBase}/api/v1/market/postings/recent?limit=8`);
      if (postingsRes.ok) {
        setRecentPostings(await postingsRes.json());
      }

      setNotification({
        type: 'success',
        message: `Successfully ingested ${data.total_postings_analyzed} Kaggle job postings! Skills recalculated with recency decay.`
      });
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Error ingesting Kaggle dataset'
      });
    } finally {
      setIngesting(false);
      setTimeout(() => setNotification(null), 6000);
    }
  };

  const categories = ['All', 'Programming', 'AI/ML', 'Cloud/DevOps', 'Databases', 'Core CS', 'Backend'];

  // Filter & sort skills
  const filteredSkills = (trends?.top_skills || [])
    .filter(skill => {
      const matchesCategory = selectedCategory === 'All' || skill.category === selectedCategory;
      const matchesSearch = skill.skill_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            skill.category.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesCategory && matchesSearch;
    })
    .sort((a, b) => {
      if (sortBy === 'demand') return b.demand_score - a.demand_score;
      if (sortBy === 'frequency') return b.raw_frequency - a.raw_frequency;
      if (sortBy === 'recency') return b.recency_decay_score - a.recency_decay_score;
      return 0;
    });

  const getDemandColor = (score) => {
    if (score >= 0.8) return 'linear-gradient(90deg, #10b981, #06b6d4)';
    if (score >= 0.5) return 'linear-gradient(90deg, #6366f1, #8b5cf6)';
    if (score >= 0.25) return 'linear-gradient(90deg, #f59e0b, #f97316)';
    return 'linear-gradient(90deg, #64748b, #94a3b8)';
  };

  const getTrendBadge = (score) => {
    if (score >= 0.85) return { label: 'Surging High', color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)' };
    if (score >= 0.55) return { label: 'Strong Demand', color: '#6366f1', bg: 'rgba(99, 102, 241, 0.15)' };
    if (score >= 0.25) return { label: 'Consistent', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)' };
    return { label: 'Emerging / Baseline', color: '#94a3b8', bg: 'rgba(148, 163, 184, 0.15)' };
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* VISIBLE ERROR STATE */}
      {fetchError && (
        <div style={{
          padding: '1.25rem',
          backgroundColor: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.35)',
          borderRadius: '0.75rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '1rem',
          flexWrap: 'wrap'
        }}>
          <div>
            <div style={{ fontWeight: 700, color: '#ef4444', marginBottom: '0.25rem' }}>
              ⚠️ Market Trends Data Unavailable
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {fetchError}
            </div>
          </div>
          <button
            type="button"
            onClick={fetchTrendsData}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#ef4444',
              color: '#ffffff',
              borderRadius: '0.375rem',
              fontWeight: 600,
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <RefreshCw size={14} className={loading ? 'spin' : ''} /> Retry Fetch
          </button>
        </div>
      )}

      {/* HERO METRICS CARDS */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '1.25rem'
      }}>
        {/* Total Postings */}
        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-label">Total Job Postings</div>
              <div className="stat-value">{trends?.total_postings_analyzed || 0}</div>
            </div>
            <div className="stat-icon-wrapper" style={{ backgroundColor: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6' }}>
              <Briefcase size={22} />
            </div>
          </div>
          <div className="stat-sub">
            <span style={{ 
              color: trends?.is_sample_data ? '#f59e0b' : '#10b981', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '3px' 
            }}>
              <ArrowUpRight size={14} /> {trends?.is_sample_data ? 'Sample Baseline' : `Live Ingested (${trends?.data_source || 'Kaggle'})`}
            </span>
            <span>{trends?.is_sample_data ? 'Curated Distribution' : 'Ingested Postings'}</span>
          </div>
        </div>

        {/* Top Demanded Skill */}
        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-label">Top Market Skill</div>
              <div className="stat-value" style={{ fontSize: '1.6rem', color: '#10b981' }}>
                {trends?.top_skills?.[0]?.skill_name || 'Python'}
              </div>
            </div>
            <div className="stat-icon-wrapper" style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>
              <Flame size={22} />
            </div>
          </div>
          <div className="stat-sub">
            <span>Score: <strong>1.0000</strong></span>
            <span>Freq: {trends?.top_skills?.[0]?.raw_frequency || 0} jobs</span>
          </div>
        </div>

        {/* Monitored Skills */}
        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-label">Taxonomy Monitored</div>
              <div className="stat-value">{trends?.top_skills?.length || 10}</div>
            </div>
            <div className="stat-icon-wrapper" style={{ backgroundColor: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6' }}>
              <Layers size={22} />
            </div>
          </div>
          <div className="stat-sub">
            <span>Mapped to ChromaDB Vector Store</span>
          </div>
        </div>

        {/* Recency Decay Half-Life */}
        <div className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div className="stat-label">Recency Decay Factor</div>
              <div className="stat-value">λ = 0.05</div>
            </div>
            <div className="stat-icon-wrapper" style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' }}>
              <Clock size={22} />
            </div>
          </div>
          <div className="stat-sub">
            <span>Exponential half-life: ~14 days</span>
          </div>
        </div>
      </div>

      {/* KAGGLE DATASET INGESTION ACTION BAR */}
      <div className="panel" style={{
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.9))',
        border: '1px solid rgba(99, 102, 241, 0.25)',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '1rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div className="pulse-indicator" />
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Database size={16} color="#38bdf8" />
              Connected Kaggle Dataset: <span style={{ color: '#38bdf8' }}>asaniczka/data-science-job-postings</span>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              12,218 raw LinkedIn listings available for streaming ingestion into SQLite & ChromaDB
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            <span>Batch:</span>
            <select 
              value={ingestCount} 
              onChange={(e) => setIngestCount(Number(e.target.value))}
              style={{ padding: '0.4rem 0.75rem', fontSize: '0.85rem' }}
            >
              <option value={25}>+25 Postings</option>
              <option value={50}>+50 Postings</option>
              <option value={100}>+100 Postings</option>
              <option value={200}>+200 Postings</option>
            </select>
          </div>

          <button 
            onClick={handleIngestKaggle} 
            disabled={ingesting}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '0.6rem 1.25rem',
              backgroundColor: '#6366f1',
              fontWeight: 600
            }}
          >
            {ingesting ? (
              <>
                <RefreshCw size={16} className="spin-icon" />
                Ingesting Kaggle Data...
              </>
            ) : (
              <>
                <Zap size={16} />
                Ingest & Rescore Trends
              </>
            )}
          </button>

          <button 
            onClick={fetchTrendsData} 
            disabled={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '0.6rem 1rem',
              backgroundColor: 'transparent',
              border: '1px solid var(--border-color)',
              color: 'var(--text-main)'
            }}
            title="Refresh Trends"
          >
            <RefreshCw size={16} className={loading ? 'spin-icon' : ''} />
          </button>
        </div>
      </div>

      {notification && (
        <div style={{
          padding: '1rem',
          borderRadius: '0.5rem',
          backgroundColor: notification.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          color: notification.type === 'success' ? '#10b981' : '#ef4444',
          border: `1px solid ${notification.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '0.9rem'
        }}>
          <CheckCircle2 size={18} />
          {notification.message}
        </div>
      )}

      {/* FILTER & SEARCH CONTROLS */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '1rem'
      }}>
        {/* Category Pills */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`pill-btn ${selectedCategory === cat ? 'active' : ''}`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search & Sort */}
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search skill..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ paddingLeft: '32px', width: '180px', padding: '0.5rem 0.5rem 0.5rem 32px', fontSize: '0.85rem' }}
            />
          </div>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{ padding: '0.5rem 0.75rem', fontSize: '0.85rem' }}
          >
            <option value="demand">Sort: Demand Score</option>
            <option value="frequency">Sort: Job Count</option>
            <option value="recency">Sort: Recency Score</option>
          </select>
        </div>
      </div>

      {/* SKILL DEMAND TRENDS LIST */}
      <div className="panel">
        <div className="panel-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={20} color="#3b82f6" />
            Ranked Industry Skill Demand
          </div>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 400 }}>
            Showing {filteredSkills.length} of {trends?.top_skills?.length || 0} skills
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', marginTop: '1.5rem' }}>
          {filteredSkills.map((skill, idx) => {
            const badge = getTrendBadge(skill.demand_score, skill.raw_frequency);
            const percentWidth = Math.max(8, Math.round(skill.demand_score * 100));

            return (
              <div key={skill.skill_id} className="skill-trend-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  
                  {/* Left: Rank & Title */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div className="rank-badge" style={{
                      backgroundColor: idx === 0 ? 'rgba(234, 179, 8, 0.2)' : idx === 1 ? 'rgba(148, 163, 184, 0.2)' : idx === 2 ? 'rgba(202, 138, 4, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                      color: idx === 0 ? '#eab308' : idx === 1 ? '#cbd5e1' : idx === 2 ? '#ca8a04' : 'var(--text-muted)',
                      border: idx < 3 ? '1px solid currentColor' : 'none'
                    }}>
                      #{idx + 1}
                    </div>
                    <div>
                      <span style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text-main)' }}>
                        {skill.skill_name}
                      </span>
                      <span className="category-tag" style={{ marginLeft: '8px' }}>
                        {skill.category}
                      </span>
                    </div>
                  </div>

                  {/* Right: Score Metrics */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      color: badge.color,
                      backgroundColor: badge.bg,
                      padding: '0.2rem 0.6rem',
                      borderRadius: '999px'
                    }}>
                      {badge.label}
                    </span>

                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      <strong>{skill.raw_frequency}</strong> jobs
                    </span>

                    <div style={{ textAlign: 'right', minWidth: '70px' }}>
                      <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--text-main)' }}>
                        {(skill.demand_score * 100).toFixed(1)}%
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        Score: {skill.demand_score.toFixed(4)}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Demand Bar */}
                <div className="progress-container" style={{ height: '8px', backgroundColor: 'rgba(255,255,255,0.06)' }}>
                  <div 
                    className="progress-bar"
                    style={{ 
                      width: `${percentWidth}%`, 
                      background: getDemandColor(skill.demand_score),
                      borderRadius: '4px',
                      transition: 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)'
                    }} 
                  />
                </div>
              </div>
            );
          })}

          {filteredSkills.length === 0 && (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              No skills match the selected filter or search query.
            </div>
          )}
        </div>
      </div>

      {/* RECENT KAGGLE JOB POSTINGS PREVIEW */}
      <div className="panel">
        <div className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Briefcase size={20} color="#10b981" />
          Live Kaggle Postings Stream Sample
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          Real job listings parsed from the Kaggle dataset with extracted skill tokens and posting recency.
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: '1rem'
        }}>
          {recentPostings.map((job) => (
            <div key={job.posting_id} className="job-card">
              <div style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '0.25rem', color: 'var(--text-main)' }}>
                {job.title}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#38bdf8', marginBottom: '0.5rem' }}>
                {job.company} • <span style={{ color: 'var(--text-muted)' }}>{job.posting_date}</span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {job.extracted_skills.map((s) => (
                  <span key={s} className="skill-pill">
                    {s.replace('skill_', '')}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* MATHEMATICAL FOUNDATION FORMULA CARD */}
      <div className="panel" style={{ backgroundColor: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, marginBottom: '0.5rem', color: '#a5b4fc' }}>
          <Sparkles size={16} /> Market Trends Agent Mathematical Formulation
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
          Skill demand D(s) is evaluated by aggregating job listing mentions I(s in p) weighted by an exponential recency decay kernel exp(-λ · Δt_p), normalized by maximum frequency demand:
        </div>
        <div style={{
          margin: '0.75rem 0',
          padding: '0.75rem 1rem',
          backgroundColor: 'rgba(0,0,0,0.3)',
          borderRadius: '0.5rem',
          fontFamily: 'monospace',
          fontSize: '0.9rem',
          color: '#38bdf8'
        }}>
          D(s) = [ ∑_p ( I(s ∈ p) · exp(-λ · Δt_p) ) ] / MaxDemand
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          where λ = 0.05, ensuring recently posted jobs exert a higher influence than stale historical records.
        </div>
      </div>

    </div>
  );
}
