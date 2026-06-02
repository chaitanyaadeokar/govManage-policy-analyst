import { useState } from 'react';
import type { PolicyPack } from '../types';
import { API_URL } from '../types';
import { Download, RefreshCw, CheckCircle2, AlertTriangle, ShieldCheck, FileText, Check, ThumbsUp, ThumbsDown, MessageSquare, X } from 'lucide-react';


type Props = {
  pack: PolicyPack;
  onReset: () => void;
};

export default function PolicyPackOutput({ pack, onReset }: Props) {
  
  const handleDownload = () => {
    const a = document.createElement('a');
    a.href = `${API_URL}/policy-packs/${pack.pack_id}/pdf`;
    a.download = `${pack.pack_id}.pdf`;
    a.target = '_blank';
    a.click();
  };

  // ── Inline Feedback State ────────────────────────────────────────────────
  const [feedbackRating, setFeedbackRating] = useState<'positive' | 'negative' | null>(null);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [feedbackAgent, setFeedbackAgent] = useState('all');
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);
  const [feedbackDone, setFeedbackDone] = useState(false);
  const [showCommentBox, setShowCommentBox] = useState(false);

  const handleRatingClick = (rating: 'positive' | 'negative') => {
    setFeedbackRating(rating);
    setShowCommentBox(true);
    setFeedbackDone(false);
  };

  const handleFeedbackSubmit = async () => {
    if (!feedbackRating) return;
    setFeedbackSubmitting(true);
    try {
      await fetch(`${API_URL}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_id: pack.pack_id,
          rating: feedbackRating,
          comment: feedbackComment.trim() || `Pack rated ${feedbackRating}`,
          agent_involved: feedbackAgent,
        }),
      });
      setFeedbackDone(true);
      setShowCommentBox(false);
      setFeedbackComment('');
    } finally {
      setFeedbackSubmitting(false);
    }
  };

  const AGENT_OPTIONS = [
    { value: 'all', label: 'All Agents' },
    { value: 'policy_analyst', label: 'Policy Analyst' },
    { value: 'compliance', label: 'Compliance' },
    { value: 'risk_assessment', label: 'Risk Assessment' },
  ];

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-emerald-500';
    if (score >= 60) return 'text-amber-500';
    return 'text-rose-500';
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in">
      
      {/* Header Panel */}
      <div className="enterprise-panel bg-white border-l-4 border-l-indigo-600 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-5">
           <ShieldCheck size={120} />
        </div>
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="badge-info">{pack.pack_id}</span>
              <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full flex items-center gap-1">
                <CheckCircle2 size={12} /> Generated Successfully
              </span>
            </div>
            <h1 className="text-2xl font-black text-slate-800 mb-2">{pack.policy.name}</h1>
            <div className="flex flex-wrap items-center gap-3 text-sm text-slate-500 font-medium">
              <span>Sector: {pack.sector}</span>
              <span>•</span>
              <span>Country: {pack.country || 'Global'}</span>
              <span>•</span>
              <span className={`badge-${pack.risk_level === 'High' ? 'high' : pack.risk_level === 'Medium' ? 'medium' : 'low'}`}>{pack.risk_level} Risk</span>
            </div>
          </div>
          <div className="flex gap-2 shrink-0">
            <button className="btn-secondary" onClick={onReset}><RefreshCw size={14} /> Start New</button>
            <button className="btn-primary" onClick={handleDownload}><Download size={14} /> Download</button>
          </div>
        </div>

        {/* ── Inline Feedback Bar ── */}
        <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid #e2e8f0' }}>
          {feedbackDone ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#16a34a', fontWeight: 600 }}>
              <CheckCircle2 size={16} />
              Thanks for your feedback! It will improve future agent decisions.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: '#475569', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <MessageSquare size={14} style={{ color: '#818cf8' }} />
                  Rate this policy pack:
                </span>
                <button
                  id={`feedback-positive-${pack.pack_id}`}
                  onClick={() => handleRatingClick('positive')}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 6,
                    padding: '7px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13, fontWeight: 700,
                    border: `2px solid ${feedbackRating === 'positive' ? '#16a34a' : '#d1fae5'}`,
                    background: feedbackRating === 'positive' ? '#dcfce7' : '#f0fdf4',
                    color: feedbackRating === 'positive' ? '#16a34a' : '#4ade80',
                    transition: 'all 0.15s',
                  }}
                >
                  <ThumbsUp size={14} /> Correct
                </button>
                <button
                  id={`feedback-negative-${pack.pack_id}`}
                  onClick={() => handleRatingClick('negative')}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 6,
                    padding: '7px 14px', borderRadius: 8, cursor: 'pointer', fontSize: 13, fontWeight: 700,
                    border: `2px solid ${feedbackRating === 'negative' ? '#dc2626' : '#fecdd3'}`,
                    background: feedbackRating === 'negative' ? '#fee2e2' : '#fff1f2',
                    color: feedbackRating === 'negative' ? '#dc2626' : '#f87171',
                    transition: 'all 0.15s',
                  }}
                >
                  <ThumbsDown size={14} /> Needs Work
                </button>
                <span style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'monospace' }}>ID: {pack.pack_id}</span>
              </div>

              {showCommentBox && (
                <div style={{
                  background: feedbackRating === 'negative' ? '#fff1f2' : '#f0fdf4',
                  border: `1px solid ${feedbackRating === 'negative' ? '#fecdd3' : '#d1fae5'}`,
                  borderRadius: 12, padding: '14px 16px',
                  display: 'flex', flexDirection: 'column', gap: 10,
                  animation: 'slideDown 0.2s ease',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#475569' }}>
                      {feedbackRating === 'negative' ? '🔍 What should be improved?' : '✅ What worked well?'}
                    </span>
                    <button onClick={() => { setShowCommentBox(false); setFeedbackRating(null); }}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: 2 }}>
                      <X size={14} />
                    </button>
                  </div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {AGENT_OPTIONS.map(opt => (
                      <button key={opt.value} onClick={() => setFeedbackAgent(opt.value)}
                        style={{
                          padding: '4px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600, cursor: 'pointer',
                          border: `1px solid ${feedbackAgent === opt.value ? '#4f46e5' : '#e2e8f0'}`,
                          background: feedbackAgent === opt.value ? '#eef2ff' : 'white',
                          color: feedbackAgent === opt.value ? '#4f46e5' : '#64748b',
                        }}>{opt.label}</button>
                    ))}
                  </div>
                  <textarea
                    value={feedbackComment}
                    onChange={e => setFeedbackComment(e.target.value)}
                    placeholder="Optional: describe what was wrong or what could be better..."
                    rows={2}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12, fontFamily: 'inherit', resize: 'vertical', outline: 'none', boxSizing: 'border-box' }}
                  />
                  <button
                    onClick={handleFeedbackSubmit}
                    disabled={feedbackSubmitting}
                    style={{
                      alignSelf: 'flex-end', padding: '8px 18px', borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: 'pointer', border: 'none',
                      background: feedbackSubmitting ? '#e2e8f0' : 'linear-gradient(135deg, #4f46e5, #2563eb)',
                      color: feedbackSubmitting ? '#94a3b8' : 'white',
                    }}
                  >
                    {feedbackSubmitting ? 'Submitting...' : 'Submit Feedback'}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Left Col - Scores & Governance */}
        <div className="space-y-6 xl:col-span-1">
          
          <div className="enterprise-panel">
            <h3 className="font-bold text-slate-800 mb-4 text-sm flex items-center gap-2 uppercase tracking-wider">
               Compliance Readiness
            </h3>
            <div className="flex flex-col gap-4">
              {[
                { label: 'Policy Completeness', val: pack.policy.compliance_scores?.policy_completeness || 100 },
                { label: 'Risk Coverage', val: pack.policy.compliance_scores?.risk_coverage || 100 },
                { label: 'Compliance Readiness', val: pack.policy.compliance_scores?.compliance_readiness || 100 }
              ].map(s => (
                 <div key={s.label}>
                    <div className="flex justify-between text-xs font-bold text-slate-600 mb-1">
                      <span>{s.label}</span>
                      <span className={getScoreColor(s.val)}>{s.val}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className={`h-2 rounded-full ${s.val >= 80 ? 'bg-emerald-500' : s.val >= 60 ? 'bg-amber-500' : 'bg-rose-500'}`} style={{ width: `${s.val}%` }}></div>
                    </div>
                 </div>
              ))}
            </div>
          </div>

          <div className="enterprise-panel">
            <h3 className="font-bold text-slate-800 mb-4 text-sm flex items-center gap-2 uppercase tracking-wider">
               Governance Structure
            </h3>
            <div className="space-y-3">
              {pack.policy.governance_structure?.map((gov, i) => (
                <div key={i} className="p-3 bg-slate-50 border border-slate-100 rounded-xl">
                  <div className="text-xs font-bold text-indigo-600 mb-1">{gov.role}</div>
                  <div className="text-sm text-slate-700">{gov.responsibility}</div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right Col - Policy Content & Matrices */}
        <div className="space-y-6 xl:col-span-2">
          
          <div className="enterprise-panel">
            <div className="flex items-center gap-2 mb-4 border-b pb-2">
               <FileText className="text-indigo-500" size={18} />
               <h3 className="font-bold text-slate-800 text-lg">Policy Document</h3>
            </div>
            
            <div className="prose prose-sm max-w-none text-slate-700">
              <div className="pack-section">
                <div className="pack-section-title">1. Objective</div>
                <p>{pack.policy.objective}</p>
              </div>

              <div className="pack-section">
                <div className="pack-section-title">2. Scope</div>
                <p>{pack.policy.scope}</p>
              </div>

              <div className="pack-section">
                <div className="pack-section-title">3. Policy Statements</div>
                <ul className="space-y-2 mb-4 list-none pl-0">
                  {pack.policy.policy_statements?.map((stmt, i) => (
                    <li key={i} className="flex gap-2">
                       <Check size={16} className="text-emerald-500 shrink-0 mt-0.5" />
                       <span>{stmt}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="pack-section">
                <div className="pack-section-title">4. Procedures</div>
                <div className="space-y-4">
                  {pack.policy.procedures?.map((proc, i) => (
                    <div key={i} className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                      <div className="font-bold text-slate-800 mb-2">{proc.title}</div>
                      <div className="space-y-1">
                        {proc.steps.map((step, j) => (
                          <div key={j} className="procedure-step">
                             <div className="procedure-step-num">{j + 1}</div>
                             <div className="text-sm pt-0.5">{step}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pack-section">
                <div className="pack-section-title">5. Enforcement</div>
                <p>{pack.policy.enforcement}</p>
              </div>
            </div>
          </div>

          <div className="enterprise-panel">
            <div className="flex items-center gap-2 mb-4 border-b pb-2">
               <ShieldCheck className="text-emerald-500" size={18} />
               <h3 className="font-bold text-slate-800 text-lg">Compliance Control Matrix</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="matrix-table">
                <thead>
                  <tr>
                    <th>Framework</th>
                    <th>Control ID</th>
                    <th>Title</th>
                    <th>Coverage</th>
                  </tr>
                </thead>
                <tbody>
                  {pack.compliance_matrix?.map((item, i) => (
                    <tr key={i}>
                      <td className="font-semibold text-indigo-600">{item.framework_id}</td>
                      <td className="font-medium text-slate-700">{item.control_id}</td>
                      <td>{item.title}</td>
                      <td><span className="badge-info bg-emerald-50 text-emerald-700 border-emerald-200">{item.coverage}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="enterprise-panel">
             <div className="flex items-center gap-2 mb-4 border-b pb-2">
               <AlertTriangle className="text-amber-500" size={18} />
               <h3 className="font-bold text-slate-800 text-lg">Risk Mitigation Mapping</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="matrix-table">
                <thead>
                  <tr>
                    <th>Risk ID</th>
                    <th>Risk Type</th>
                    <th>Mitigation Strategy</th>
                    <th>Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {pack.risk_mapping?.map((item, i) => (
                    <tr key={i}>
                      <td className="font-semibold text-slate-700">{item.risk_id}</td>
                      <td>{item.risk_type}</td>
                      <td className="text-slate-600 italic">{item.mitigation}</td>
                      <td><span className={`badge-${item.severity.toLowerCase()}`}>{item.severity}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
