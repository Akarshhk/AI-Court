import React from 'react';
import { Check, ChevronRight } from 'lucide-react';

const PHASES = [
  { id: 'opening', label: 'Opening' },
  { id: 'prosecution_argument', label: 'Prosecution Argument' },
  { id: 'defense_rebuttal', label: 'Defense Rebuttal' },
  { id: 'judge_ruling', label: 'Judge Ruling' },
  { id: 'jury_deliberation', label: 'Jury Deliberation' },
  { id: 'verdict_complete', label: 'Verdict Complete' }
];

export function PhaseIndicator({ currentPhase }) {
  const currentIndex = PHASES.findIndex(p => p.id === currentPhase);

  return (
    <div className="w-full bg-zinc-900 border-b border-zinc-800 p-4 sticky top-0 z-10">
      <div className="flex items-center justify-between w-full max-w-7xl mx-auto">
        {PHASES.map((phase, index) => {
          const isCompleted = currentIndex > index;
          const isCurrent = currentIndex === index;
          
          return (
            <div key={phase.id} className="flex items-center">
              <div className="flex items-center space-x-2">
                <div 
                  className={`flex items-center justify-center w-8 h-8 rounded-full border-2 text-sm font-medium transition-colors
                    ${isCompleted ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 
                      isCurrent ? 'bg-zinc-800 border-zinc-500 text-zinc-100' : 
                      'bg-zinc-950 border-zinc-800 text-zinc-600'}`}
                >
                  {isCompleted ? <Check className="w-4 h-4" /> : (index + 1)}
                </div>
                <span className={`text-sm font-medium whitespace-nowrap transition-colors
                  ${isCurrent ? 'text-zinc-100' : isCompleted ? 'text-zinc-400' : 'text-zinc-600'}`}>
                  {phase.label}
                </span>
              </div>
              
              {index < PHASES.length - 1 && (
                <ChevronRight className={`w-4 h-4 md:w-5 md:h-5 mx-1 md:mx-4 ${isCompleted ? 'text-zinc-600' : 'text-zinc-800'}`} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
