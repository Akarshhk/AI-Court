import React, { useState, useEffect, useCallback } from 'react';
import { PhaseIndicator } from './components/PhaseIndicator';
import { TranscriptPanel } from './components/TranscriptPanel';
import { JuryPanel } from './components/JuryPanel';
import { VerdictView } from './components/VerdictView';
import { EvidencePanel } from './components/EvidencePanel';
import { AlertCircle, Play } from 'lucide-react';

const DEFAULT_CASE = `OmniCorp Industries is a publicly traded logistics software company.
On October 12, 2023, OmniCorp announced a $50 million quarterly loss.
CEO Marcus Thorne sold 500,000 shares of OmniCorp stock on October 10, 2023.
The October 10 stock sale yielded Marcus Thorne $15 million.
An internal email from CFO Sarah Jenkins to Marcus Thorne was sent on October 8, 2023.
The October 8 email stated: 'The Q3 numbers are finalized and they are disastrous.'
Marcus Thorne claims he never read the October 8 email before selling his stock.
IT records show the October 8 email was marked as 'read' on Marcus Thorne's device at 9:15 AM on October 9.
Marcus Thorne's defense argues his executive assistant manages his inbox and frequently marks emails as read.
A pre-scheduled trading plan (10b5-1) was filed by Marcus Thorne in January 2023.
The 10b5-1 trading plan explicitly mandated the sale of 500,000 shares on October 10, 2023.
The prosecution alleges Marcus Thorne instructed the accounting team to delay the Q3 loss announcement until after his stock sale.
Accounting logs show the Q3 report was finalized on October 8 but not published until October 12.`;

function App() {
  const [hasStarted, setHasStarted] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [caseText, setCaseText] = useState(DEFAULT_CASE);
  
  // Trial State
  const [currentPhase, setCurrentPhase] = useState('opening');
  const [turns, setTurns] = useState([]);
  const [jurors, setJurors] = useState([]);
  const [verdictDoc, setVerdictDoc] = useState(null);
  const [alternateToast, setAlternateToast] = useState(null);

  // Evidence Panel State
  const [isEvidenceOpen, setIsEvidenceOpen] = useState(false);
  const [activeChunkIds, setActiveChunkIds] = useState([]);
  const [rejectedChunkIds, setRejectedChunkIds] = useState([]);

  const handleEvent = useCallback((event) => {
    switch (event.type) {
      case 'phase_change':
        setCurrentPhase(event.payload.phase);
        break;
      
      case 'agent_turn':
        setTurns(prev => [...prev, event.payload]);
        
        // Handle Citations for Evidence Panel
        const { evidence_citations, is_unverified, statement } = event.payload;
        const hasUnverifiedPrefix = statement && statement.startsWith('[UNVERIFIED]');
        const isUnverified = is_unverified || hasUnverifiedPrefix;
        
        if (evidence_citations && evidence_citations.length > 0) {
          const chunkIds = evidence_citations.map(c => c.chunk_id);
          if (isUnverified) {
            setRejectedChunkIds(chunkIds);
            setActiveChunkIds([]);
          } else {
            setActiveChunkIds(chunkIds);
            setRejectedChunkIds([]);
          }
          setIsEvidenceOpen(true);
        } else {
          // Clear highlights if no citations
          setActiveChunkIds([]);
          setRejectedChunkIds([]);
        }
        
        // Update juror state if it's a juror turn
        if (event.payload.agent_role.startsWith('juror')) {
          setJurors(prev => {
            const role = event.payload.agent_role;
            const existing = prev.find(j => j.role === role);
            if (existing) {
              return prev.map(j => j.role === role ? {
                ...j,
                verdict: event.payload.verdict || j.verdict,
                reasoning: event.payload.reasoning || j.reasoning,
                isFailed: event.payload.is_failed || j.isFailed
              } : j);
            } else {
              return [...prev, {
                role,
                verdict: event.payload.verdict || null,
                reasoning: event.payload.reasoning || null,
                isFailed: event.payload.is_failed || false,
                isAlternate: role.includes('alternate')
              }];
            }
          });
        }
        break;

      case 'juror_alternate_invoked':
        const { original_role, reason } = event.payload;
        
        // Show Toast
        setAlternateToast(`Juror Alert: ${original_role.replace(/_/g, ' ').toUpperCase()} dismissed due to ${reason}. Alternate invoked.`);
        setTimeout(() => setAlternateToast(null), 6000);

        // Update Juror state
        setJurors(prev => prev.map(j => 
          j.role === original_role ? { ...j, isFailed: true } : j
        ));
        break;

      case 'verdict_document_ready':
        setVerdictDoc(event.payload);
        setIsStreaming(false);
        // Show all citations used at the end
        if (event.payload.all_citations_used && event.payload.all_citations_used.length > 0) {
          setActiveChunkIds(event.payload.all_citations_used.map(c => c.chunk_id));
          setRejectedChunkIds([]);
          setIsEvidenceOpen(true);
        }
        break;

      default:
        console.warn('Unknown event type', event.type);
    }
  }, []);

  const [eventSource, setEventSource] = useState(null);

  const handleStart = async () => {
    setHasStarted(true);
    setIsStreaming(true);
    
    try {
      const response = await fetch('http://localhost:8000/trial/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_text: caseText })
      });
      const data = await response.json();
      const trial_id = data.trial_id;
      
      const es = new EventSource('http://localhost:8000/trial/stream/' + trial_id);
      
      const eventTypes = [
        'phase_change',
        'agent_turn',
        'juror_alternate_invoked',
        'verdict_document_ready'
      ];

      eventTypes.forEach(type => {
        es.addEventListener(type, (e) => {
          const eventData = JSON.parse(e.data);
          // Re-wrap the payload into the { type, payload } format expected by handleEvent
          handleEvent({ type: type, payload: eventData });
        });
      });

      setEventSource(es);
    } catch (error) {
      console.error("Failed to start trial:", error);
      setIsStreaming(false);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  return (
    <div className="h-screen w-screen bg-zinc-950 flex flex-col font-sans text-zinc-100 overflow-hidden relative">
      
      {/* Alternate Invoked Banner */}
      {alternateToast && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 z-50 animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="bg-amber-500 text-zinc-950 px-6 py-4 rounded-lg shadow-2xl shadow-amber-500/20 border border-amber-400 flex items-center gap-3 font-bold">
            <AlertCircle className="w-6 h-6" />
            {alternateToast}
          </div>
        </div>
      )}

      {/* Start Overlay */}
      {!hasStarted && (
        <div className="absolute inset-0 bg-zinc-950/80 backdrop-blur-md z-50 flex items-center justify-center p-6">
          <div className="bg-zinc-900 border border-zinc-800 p-8 rounded-2xl flex flex-col items-center max-w-2xl w-full text-center shadow-2xl">
            <div className="w-16 h-16 bg-zinc-800 rounded-full flex items-center justify-center mb-6 border border-zinc-700">
              <span className="text-3xl">🏛️</span>
            </div>
            <h1 className="font-serif text-3xl font-bold mb-3 text-zinc-100">AI Courtroom</h1>
            <p className="text-zinc-400 mb-6">
              A live multi-agent simulation demonstrating structured reasoning, evidence citation, and resilience.
            </p>
            
            <div className="w-full text-left mb-6">
              <label className="block text-sm font-bold uppercase tracking-wider text-zinc-500 mb-2">Case Evidence / Facts</label>
              <textarea 
                value={caseText}
                onChange={(e) => setCaseText(e.target.value)}
                className="w-full h-48 bg-zinc-950 border border-zinc-700 rounded-lg p-4 text-sm text-zinc-300 font-serif leading-relaxed focus:outline-none focus:border-zinc-500 transition-colors"
                placeholder="Enter the case facts here..."
              />
            </div>

            <button 
              onClick={handleStart}
              className="bg-zinc-100 text-zinc-950 hover:bg-white px-8 py-4 rounded-full font-bold flex items-center gap-2 transition-all hover:scale-105 active:scale-95 shadow-lg shadow-white/10"
            >
              <Play className="w-5 h-5 fill-current" />
              Begin Trial Simulation
            </button>
          </div>
        </div>
      )}

      <PhaseIndicator currentPhase={currentPhase} />

      <div className="flex-1 flex overflow-hidden relative">
        <EvidencePanel 
          isOpen={isEvidenceOpen} 
          onClose={() => setIsEvidenceOpen(false)} 
          activeChunkIds={activeChunkIds} 
          rejectedChunkIds={rejectedChunkIds} 
        />
        {/* Transcript Left */}
        <TranscriptPanel turns={turns} />
        
        {/* Jury Right */}
        <JuryPanel jurors={jurors} />
      </div>

      <VerdictView verdictDoc={verdictDoc} />

    </div>
  );
}

export default App;
