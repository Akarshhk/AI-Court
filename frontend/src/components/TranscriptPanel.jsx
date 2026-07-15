import React, { useEffect, useRef } from 'react';
import { Gavel, Scale, Shield, Users, User, AlertTriangle, FileText } from 'lucide-react';

const ROLE_CONFIG = {
  judge: { icon: Gavel, color: 'text-judge', bg: 'bg-judge/10', border: 'border-judge/20', label: 'Judge' },
  prosecution: { icon: Scale, color: 'text-prosecution', bg: 'bg-prosecution/10', border: 'border-prosecution/20', label: 'Prosecution' },
  defense: { icon: Shield, color: 'text-defense', bg: 'bg-defense/10', border: 'border-defense/20', label: 'Defense' },
  clerk: { icon: FileText, color: 'text-clerk', bg: 'bg-clerk/10', border: 'border-clerk/20', label: 'Clerk' },
};

function getRoleConfig(role) {
  if (role.startsWith('juror')) {
    return { icon: Users, color: 'text-juror', bg: 'bg-juror/10', border: 'border-juror/20', label: role.replace(/_/g, ' ').toUpperCase() };
  }
  return ROLE_CONFIG[role] || { icon: User, color: 'text-zinc-400', bg: 'bg-zinc-800/50', border: 'border-zinc-700', label: role };
}

export function TranscriptPanel({ turns }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [turns]);

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-zinc-950">
      <div className="p-6 pb-2 border-b border-zinc-900">
        <h2 className="font-serif text-2xl font-bold tracking-wide text-zinc-100">Courtroom Transcript</h2>
        <p className="text-zinc-500 text-sm mt-1">Live proceedings</p>
      </div>
      
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth"
      >
        {turns.length === 0 ? (
          <div className="h-full flex items-center justify-center text-zinc-600 font-serif italic">
            Awaiting proceedings...
          </div>
        ) : (
          turns.map((turnData, idx) => {
            const { agent_role, statement, evidence_citations, is_failed, is_unverified } = turnData;
            const config = getRoleConfig(agent_role);
            const Icon = config.icon;
            
            // Extract unverified prefix if it's baked into the statement string
            let displayStatement = statement;
            const hasUnverifiedPrefix = displayStatement.startsWith('[UNVERIFIED]');
            if (hasUnverifiedPrefix) {
              displayStatement = displayStatement.replace('[UNVERIFIED]', '').trim();
            }
            
            const isUnverified = is_unverified || hasUnverifiedPrefix;

            return (
              <div 
                key={idx} 
                className={`flex gap-4 p-4 rounded-lg border transition-all
                  ${isUnverified ? 'border-amber-500/50 bg-amber-500/5' : `border-zinc-800/50 hover:border-zinc-700 bg-zinc-900/30`}
                  ${is_failed ? 'opacity-50 grayscale' : ''}
                `}
              >
                {/* Role Badge Column */}
                <div className="flex-shrink-0 flex flex-col items-center gap-2 w-24">
                  <div className={`p-3 rounded-full ${config.bg} ${config.color} border ${config.border}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className={`text-[10px] font-bold tracking-wider uppercase text-center ${config.color}`}>
                    {config.label}
                  </span>
                </div>
                
                {/* Content Column */}
                <div className="flex-1 space-y-3 pt-1">
                  {isUnverified && (
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      UNVERIFIED STATEMENT
                    </div>
                  )}
                  
                  <div className={`font-serif text-[15px] leading-relaxed ${isUnverified ? 'text-amber-100/90' : 'text-zinc-300'}`}>
                    {displayStatement}
                  </div>
                  
                  {/* Citations */}
                  {evidence_citations && evidence_citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-zinc-800/50 space-y-2">
                      <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Citations</span>
                      <div className="grid gap-2">
                        {evidence_citations.map((cite, i) => (
                          <div key={i} className={`flex flex-col gap-1 text-sm p-2.5 rounded border transition-colors ${
                            isUnverified 
                              ? 'bg-red-500/10 border-red-500/20' 
                              : 'bg-zinc-900/50 border-zinc-800'
                          }`}>
                            <div className="flex items-center gap-2">
                              <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${
                                isUnverified 
                                  ? 'bg-red-500/20 text-red-300 border-red-500/30 line-through' 
                                  : 'bg-zinc-800 text-zinc-400 border-zinc-700'
                              }`}>
                                {cite.chunk_id}
                              </span>
                              {isUnverified && (
                                <span className="text-[10px] font-bold text-red-400 uppercase tracking-wider bg-red-500/10 px-1.5 py-0.5 rounded border border-red-500/20">
                                  Rejected
                                </span>
                              )}
                              <span className={`text-xs italic ${isUnverified ? 'text-red-400/70' : 'text-zinc-500'}`}>
                                {cite.relevance}
                              </span>
                            </div>
                            <div className={`pl-2 ml-1 text-[13px] border-l-2 ${
                              isUnverified 
                                ? 'text-red-300/70 border-red-500/30 line-through decoration-red-500/50' 
                                : 'text-zinc-400 border-zinc-700'
                            }`}>
                              "{cite.quote}"
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
