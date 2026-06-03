import { useState, useEffect } from 'react';
import { API_URL } from '../types';
import type { ComplianceFramework, RiskItem } from '../types';
import { Shield, AlertTriangle, X, ChevronRight, CheckCircle2, FolderTree, Server } from 'lucide-react';

export default function DatabaseExplorer() {
  const [activeTab, setActiveTab] = useState<'frameworks' | 'risks'>('frameworks');
  const [frameworks, setFrameworks] = useState<ComplianceFramework[]>([]);
  const [risks, setRisks] = useState<RiskItem[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedFramework, setSelectedFramework] = useState<ComplianceFramework | null>(null);
  const [selectedRisk, setSelectedRisk] = useState<RiskItem | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`${API_URL}/compliance/frameworks`).then(res => res.json()),
      fetch(`${API_URL}/risk/library`).then(res => res.json())
    ])
    .then(([fwData, riskData]) => {
      setFrameworks(fwData);
      setRisks(riskData);
    })
    .catch(err => console.error("Error fetching database items:", err))
    .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in">
      <div className="enterprise-panel">
        <div className="flex items-center gap-3 mb-6 border-b pb-4">
          <div className="p-2 bg-indigo-100 rounded-xl">
            <Server className="text-indigo-600" size={24} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-800">Knowledge Database</h2>
            <p className="text-slate-500 text-sm">Explore the active compliance frameworks and indexed risk library used by the AI agents.</p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 border-b border-slate-200 mb-6">
          <button
            className={`px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${activeTab === 'frameworks' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
            onClick={() => setActiveTab('frameworks')}
          >
            <Shield className="inline mr-2" size={16} /> Compliance Frameworks ({frameworks.length})
          </button>
          <button
            className={`px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${activeTab === 'risks' ? 'border-rose-500 text-rose-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
            onClick={() => setActiveTab('risks')}
          >
            <AlertTriangle className="inline mr-2" size={16} /> Risk Library ({risks.length})
          </button>
        </div>

        {loading ? (
          <div className="py-20 text-center animate-pulse text-slate-400">Loading database records...</div>
        ) : (
          <div className="min-h-[400px]">
            {activeTab === 'frameworks' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {frameworks.map(fw => (
                  <div key={fw.framework_id} 
                       className="border border-slate-200 rounded-xl p-4 hover:border-indigo-300 hover:shadow-md transition-all cursor-pointer bg-white group"
                       onClick={() => {
                         // Fetch full framework details if controls are missing
                         if (!fw.controls) {
                            fetch(`${API_URL}/compliance/frameworks/${fw.framework_id}`)
                              .then(r => r.json())
                              .then(fullFw => setSelectedFramework(fullFw));
                         } else {
                            setSelectedFramework(fw);
                         }
                       }}>
                    <div className="flex justify-between items-start mb-2">
                      <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg group-hover:bg-indigo-100 transition-colors">
                        <FolderTree size={20} />
                      </div>
                      <span className="text-xs font-bold px-2 py-1 bg-slate-100 text-slate-600 rounded-full">{fw.category}</span>
                    </div>
                    <h3 className="font-bold text-slate-800 text-lg line-clamp-1">{fw.name}</h3>
                    <p className="text-xs text-slate-500 mb-3 line-clamp-2 mt-1">{fw.description}</p>
                    <div className="flex items-center justify-between mt-auto pt-3 border-t border-slate-100">
                      <span className="text-xs font-medium text-slate-400">{fw.official_body}</span>
                      <ChevronRight size={16} className="text-slate-300 group-hover:text-indigo-500 transition-colors" />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'risks' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {risks.map(risk => (
                  <div key={risk.risk_id} 
                       className="border border-slate-200 rounded-xl p-4 hover:border-rose-300 hover:shadow-md transition-all cursor-pointer bg-white group"
                       onClick={() => setSelectedRisk(risk)}>
                    <div className="flex justify-between items-start mb-2">
                      <div className={`p-2 rounded-lg transition-colors ${risk.severity === 'High' ? 'bg-rose-50 text-rose-600 group-hover:bg-rose-100' : risk.severity === 'Medium' ? 'bg-amber-50 text-amber-600 group-hover:bg-amber-100' : 'bg-emerald-50 text-emerald-600 group-hover:bg-emerald-100'}`}>
                        <AlertTriangle size={20} />
                      </div>
                      <span className={`text-xs font-bold px-2 py-1 rounded-full ${risk.severity === 'High' ? 'bg-rose-100 text-rose-700' : risk.severity === 'Medium' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                        {risk.severity} Severity
                      </span>
                    </div>
                    <h3 className="font-bold text-slate-800 text-sm line-clamp-2 h-10">{risk.title}</h3>
                    <p className="text-xs text-slate-500 mb-3 line-clamp-2 mt-1">{risk.description}</p>
                    <div className="flex items-center justify-between mt-auto pt-3 border-t border-slate-100">
                      <span className="text-xs font-medium text-slate-400">{risk.category}</span>
                      <ChevronRight size={16} className="text-slate-300 group-hover:text-rose-500 transition-colors" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* MODALS */}
      {selectedFramework && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl animate-in zoom-in-95">
            <div className="p-6 border-b border-slate-100 flex justify-between items-start">
              <div>
                <div className="flex gap-2 items-center mb-1">
                  <span className="text-xs font-bold px-2 py-1 bg-indigo-100 text-indigo-700 rounded-full">{selectedFramework.category}</span>
                  <span className="text-xs font-medium text-slate-500">{selectedFramework.region}</span>
                </div>
                <h2 className="text-2xl font-bold text-slate-800">{selectedFramework.name}</h2>
                <p className="text-sm text-slate-500 mt-1">{selectedFramework.official_body} • {selectedFramework.version}</p>
              </div>
              <button onClick={() => setSelectedFramework(null)} className="p-2 hover:bg-slate-100 rounded-full text-slate-400 transition-colors">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto">
              <div className="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-100 text-sm text-slate-700 leading-relaxed">
                {selectedFramework.description}
                {selectedFramework.trusted_url && (
                  <a href={selectedFramework.trusted_url} target="_blank" rel="noreferrer" className="block mt-2 text-indigo-600 hover:underline font-semibold">
                    View Official Documentation ↗
                  </a>
                )}
              </div>

              <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                <CheckCircle2 className="text-emerald-500" size={18} /> 
                Controls & Requirements ({selectedFramework.controls?.length || 0})
              </h3>
              
              <div className="space-y-3">
                {selectedFramework.controls?.map(control => (
                  <div key={control.control_id} className="p-4 border border-slate-200 rounded-xl hover:border-indigo-200 transition-colors">
                    <div className="flex justify-between items-start mb-2">
                      <div className="font-bold text-slate-800 text-sm">
                        <span className="text-indigo-600 mr-2">{control.control_id}</span>
                        {control.title}
                      </div>
                      <span className={`text-[10px] uppercase tracking-wider font-bold px-2 py-1 rounded-md ${control.severity === 'high' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'}`}>
                        {control.severity}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 mb-3">{control.description}</p>
                    <div className="flex flex-wrap gap-1">
                      {control.keywords?.map(kw => (
                        <span key={kw} className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">{kw}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedRisk && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl animate-in zoom-in-95">
            <div className="p-6 border-b border-slate-100 flex justify-between items-start">
              <div>
                <div className="flex gap-2 items-center mb-2">
                  <span className={`text-xs font-bold px-2 py-1 rounded-full ${selectedRisk.severity === 'High' ? 'bg-rose-100 text-rose-700' : selectedRisk.severity === 'Medium' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
                    {selectedRisk.severity} Severity
                  </span>
                  <span className="text-xs font-bold px-2 py-1 bg-slate-100 text-slate-600 rounded-full">{selectedRisk.category}</span>
                </div>
                <h2 className="text-xl font-bold text-slate-800">{selectedRisk.title}</h2>
                <p className="text-sm text-slate-500 mt-1 font-mono">{selectedRisk.risk_id}</p>
              </div>
              <button onClick={() => setSelectedRisk(null)} className="p-2 hover:bg-slate-100 rounded-full text-slate-400 transition-colors">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto space-y-6">
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Risk Description</h3>
                <p className="text-sm text-slate-700 leading-relaxed">{selectedRisk.description}</p>
              </div>

              <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-xl">
                <h3 className="text-xs font-bold text-emerald-600 uppercase tracking-wider mb-2">Recommended Mitigation</h3>
                <p className="text-sm text-emerald-900 leading-relaxed">{selectedRisk.mitigation}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Affected Domains</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedRisk.affected_domains.map(d => (
                      <span key={d} className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded-md border border-slate-200">{d}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Compliance Mappings</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedRisk.compliance_links.map(l => (
                      <span key={l} className="text-xs bg-indigo-50 text-indigo-600 px-2 py-1 rounded-md border border-indigo-100 font-semibold">{l}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
