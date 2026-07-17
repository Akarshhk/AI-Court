import React from 'react';
import { FileSignature, AlertCircle, CheckCircle2, XCircle, Scale } from 'lucide-react';

export function VerdictView({ verdictDoc, isOpen, onClose, onReset }) {
  if (!verdictDoc || !isOpen) return null;

  const { final_verdict, vote_breakdown, dissenting_opinions, all_citations_used } = verdictDoc;

  const getVerdictStyle = (verdict) => {
    switch (verdict) {
      case 'guilty':
        return { bg: 'bg-red-500/10', border: 'border-red-500/50', text: 'text-red-400', icon: XCircle, label: 'GUILTY' };
      case 'not_guilty':
        return { bg: 'bg-emerald-500/10', border: 'border-emerald-500/50', text: 'text-emerald-400', icon: CheckCircle2, label: 'NOT GUILTY' };
      case 'hung_jury':
        return { bg: 'bg-amber-500/10', border: 'border-amber-500/50', text: 'text-amber-400', icon: Scale, label: 'HUNG JURY' };
      case 'failed_deliberation':
        return { bg: 'bg-zinc-800', border: 'border-zinc-600', text: 'text-zinc-400', icon: AlertCircle, label: 'MISTRIAL (FAILED DELIBERATION)' };
      default:
        return { bg: 'bg-zinc-900', border: 'border-zinc-700', text: 'text-zinc-100', icon: FileSignature, label: verdict };
    }
  };

  const style = getVerdictStyle(final_verdict);
  const Icon = style.icon;

  return (
    <div className="absolute inset-0 bg-zinc-950/80 backdrop-blur-sm z-50 flex items-start justify-center p-6 overflow-y-auto">
      <div className="bg-zinc-900 border border-zinc-700 rounded-xl max-w-2xl w-full shadow-2xl overflow-hidden mt-10 mb-10">
        
        {/* Header */}
        <div className={`p-8 flex flex-col items-center border-b ${style.border} ${style.bg}`}>
          <Icon className={`w-16 h-16 ${style.text} mb-4`} />
          <h2 className="font-serif text-xl text-zinc-400 tracking-widest uppercase mb-2">Final Verdict</h2>
          <h1 className={`font-serif text-5xl font-bold tracking-tight ${style.text} text-center`}>
            {style.label}
          </h1>
        </div>

        {/* Content */}
        <div className="p-8 space-y-8">
          
          {/* Vote Breakdown */}
          {vote_breakdown && (
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-500 mb-4 border-b border-zinc-800 pb-2">Vote Breakdown</h3>
              <div className="flex gap-4">
                <div className="flex-1 bg-zinc-950 rounded-lg p-4 border border-zinc-800 flex flex-col items-center">
                  <span className="text-red-400 text-3xl font-bold mb-1">{vote_breakdown.guilty || 0}</span>
                  <span className="text-zinc-500 text-xs font-semibold uppercase">Guilty</span>
                </div>
                <div className="flex-1 bg-zinc-950 rounded-lg p-4 border border-zinc-800 flex flex-col items-center">
                  <span className="text-emerald-400 text-3xl font-bold mb-1">{vote_breakdown.not_guilty || 0}</span>
                  <span className="text-zinc-500 text-xs font-semibold uppercase">Not Guilty</span>
                </div>
              </div>
            </div>
          )}

          {/* Dissenting Opinions */}
          {dissenting_opinions && dissenting_opinions.length > 0 && (
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-500 mb-4 border-b border-zinc-800 pb-2">Dissenting Opinions</h3>
              <div className="space-y-3">
                {dissenting_opinions.map((dissent, idx) => (
                  <div key={idx} className="bg-zinc-950 rounded p-4 border border-zinc-800">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-zinc-300 font-bold uppercase text-xs">{dissent.juror.replace(/_/g, ' ')}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase border
                        ${dissent.verdict === 'guilty' ? 'bg-red-500/10 text-red-400 border-red-500/30' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'}`}>
                        Voted {dissent.verdict.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-zinc-400 text-sm font-serif italic">"{dissent.reasoning}"</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* All Citations */}
          {all_citations_used && all_citations_used.length > 0 && (
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-500 mb-4 border-b border-zinc-800 pb-2">Key Evidence Cited</h3>
              <div className="grid grid-cols-2 gap-2">
                {all_citations_used.map((cite, idx) => (
                  <div key={idx} className="bg-zinc-950 rounded p-3 border border-zinc-800 flex flex-col">
                    <span className="text-[10px] font-mono text-zinc-500 mb-1">{cite.chunk_id}</span>
                    <span className="text-zinc-300 text-sm leading-snug">"{cite.quote}"</span>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
        
        {/* Footer */}
        <div className="bg-zinc-950 p-4 border-t border-zinc-800 flex justify-between items-center">
          <p className="text-zinc-600 text-xs uppercase tracking-widest font-semibold">Proceeding Concluded</p>
          <div className="flex gap-3">
            <button 
              onClick={onReset}
              className="text-zinc-300 hover:text-white bg-zinc-900 hover:bg-zinc-800 px-4 py-2 rounded text-sm font-bold transition-all border border-zinc-700 hover:border-zinc-500"
            >
              New Case
            </button>
            <button 
              onClick={onClose}
              className="text-zinc-400 hover:text-white bg-zinc-900 hover:bg-zinc-800 px-4 py-2 rounded text-sm font-bold transition-colors border border-zinc-800 hover:border-zinc-700"
            >
              Review Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
