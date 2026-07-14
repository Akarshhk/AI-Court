import React from 'react';
import { UserX, UserCheck, HelpCircle } from 'lucide-react';

export function JuryPanel({ jurors }) {
  return (
    <div className="w-80 border-l border-zinc-900 bg-zinc-950 flex flex-col overflow-hidden">
      <div className="p-4 border-b border-zinc-900 flex-shrink-0 bg-zinc-900/50">
        <h3 className="font-serif font-bold tracking-wide text-zinc-100 flex items-center justify-between">
          <span>Jury Box</span>
          <span className="text-xs font-sans text-zinc-500 font-normal">
            {jurors.filter(j => !j.isFailed).length} Active
          </span>
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {jurors.length === 0 ? (
          <div className="text-sm text-zinc-600 italic text-center mt-10">
            Jury has not yet deliberated.
          </div>
        ) : (
          jurors.map((juror) => {
            const isFailed = juror.isFailed;
            const hasVerdict = !!juror.verdict;
            const isGuilty = juror.verdict === 'guilty';
            const isNotGuilty = juror.verdict === 'not_guilty';

            return (
              <div 
                key={juror.role} 
                className={`relative p-4 rounded-lg border transition-all ${
                  isFailed ? 'border-red-500/30 bg-red-500/5 opacity-75' : 
                  juror.isAlternate ? 'border-amber-500/30 bg-zinc-900/50' :
                  'border-zinc-800 bg-zinc-900/30'
                }`}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex flex-col">
                    <span className={`text-sm font-bold uppercase tracking-wider ${
                      isFailed ? 'text-red-400 line-through decoration-red-500/50' : 
                      juror.isAlternate ? 'text-amber-400' : 'text-zinc-300'
                    }`}>
                      {juror.role.replace(/_/g, ' ')}
                    </span>
                    {juror.isAlternate && (
                      <span className="text-[10px] text-amber-500/70 font-semibold uppercase">Alternate Sworn In</span>
                    )}
                  </div>
                  
                  {isFailed ? (
                    <UserX className="w-5 h-5 text-red-500/50" />
                  ) : hasVerdict ? (
                    <UserCheck className={`w-5 h-5 ${isGuilty ? 'text-red-400' : 'text-emerald-400'}`} />
                  ) : (
                    <HelpCircle className="w-5 h-5 text-zinc-600" />
                  )}
                </div>

                {/* Status/Verdict Badge */}
                {isFailed ? (
                  <div className="inline-block px-2 py-1 bg-red-500/20 text-red-400 text-xs font-semibold rounded mb-2 border border-red-500/20">
                    DISMISSED / FAILED
                  </div>
                ) : hasVerdict ? (
                  <div className={`inline-block px-2 py-1 text-xs font-bold rounded mb-2 border ${
                    isGuilty ? 'bg-red-500/10 text-red-400 border-red-500/30' : 
                    'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  }`}>
                    {juror.verdict.toUpperCase().replace('_', ' ')}
                  </div>
                ) : (
                  <div className="inline-block px-2 py-1 bg-zinc-800/50 text-zinc-400 text-xs font-semibold rounded mb-2">
                    DELIBERATING...
                  </div>
                )}

                {/* Reasoning */}
                {!isFailed && juror.reasoning && (
                  <div className="mt-2 text-sm text-zinc-400 border-t border-zinc-800 pt-2 font-serif italic">
                    "{juror.reasoning}"
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
