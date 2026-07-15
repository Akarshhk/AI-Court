import React, { useState, useEffect, useRef } from 'react';
import { Database, X } from 'lucide-react';

export function EvidencePanel({ isOpen, onClose, activeChunkIds = [], rejectedChunkIds = [] }) {
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(true);
  const chunkRefs = useRef({});

  useEffect(() => {
    async function fetchChunks() {
      try {
        const res = await fetch('http://localhost:8000/case/chunks');
        if (!res.ok) throw new Error('Failed to fetch chunks');
        const data = await res.json();
        setChunks(data.chunks);
      } catch (err) {
        console.warn('Backend not reachable, falling back to mock chunks for Evidence Panel', err);
        // Fallback for pure UI mock testing
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
        
        const mockChunks = DEFAULT_CASE.split('\n').filter(p => p.trim()).map((text, i) => ({
          chunk_id: `case_chunk_${String(i).padStart(3, '0')}`,
          text: text.trim()
        }));
        setChunks(mockChunks);
      } finally {
        setLoading(false);
      }
    }
    
    if (isOpen && chunks.length === 0) {
      fetchChunks();
    }
  }, [isOpen, chunks.length]);

  // Scroll to the first active or rejected chunk
  useEffect(() => {
    if (isOpen) {
      const targetId = activeChunkIds[0] || rejectedChunkIds[0];
      if (targetId && chunkRefs.current[targetId]) {
        chunkRefs.current[targetId].scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [isOpen, activeChunkIds, rejectedChunkIds]);

  return (
    <div 
      className={`z-40 bg-zinc-950 border-zinc-800 transition-all duration-500 ease-in-out flex flex-col overflow-hidden ${
        isOpen ? 'w-96 border-r shadow-[20px_0_40px_rgba(0,0,0,0.5)]' : 'w-0 border-r-0 shadow-none'
      }`}
    >
      <div className="w-96 flex-1 flex flex-col">
        <div className="p-4 border-b border-zinc-900 flex items-center justify-between bg-zinc-900/50">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-blue-400" />
          <h2 className="font-serif text-lg font-bold text-zinc-100 tracking-wide">Evidence Source</h2>
        </div>
        <button onClick={onClose} className="p-1.5 hover:bg-zinc-800 rounded-md text-zinc-400 transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loading ? (
          <div className="text-zinc-500 text-sm italic text-center mt-10">Loading evidence...</div>
        ) : (
          chunks.map((chunk) => {
            const isActive = activeChunkIds.includes(chunk.chunk_id);
            const isRejected = rejectedChunkIds.includes(chunk.chunk_id);
            
            let containerStyle = "border-zinc-800/50 bg-zinc-900/30 text-zinc-400";
            let badgeStyle = "bg-zinc-800 text-zinc-500 border-zinc-700";
            
            if (isActive) {
              containerStyle = "border-blue-500/50 bg-blue-500/10 text-zinc-100 ring-2 ring-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.3)] scale-[1.02] transition-all duration-300 z-10 relative";
              badgeStyle = "bg-blue-500 text-white border-blue-400 font-bold shadow-[0_0_10px_rgba(59,130,246,0.5)]";
            } else if (isRejected) {
              containerStyle = "border-red-500/50 bg-red-500/10 text-zinc-300 ring-2 ring-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.3)] scale-[1.02] transition-all duration-300 z-10 relative line-through decoration-red-500/50";
              badgeStyle = "bg-red-500 text-white border-red-400 font-bold shadow-[0_0_10px_rgba(239,68,68,0.5)]";
            }

            return (
              <div 
                key={chunk.chunk_id} 
                ref={(el) => chunkRefs.current[chunk.chunk_id] = el}
                className={`p-3.5 rounded-lg border text-sm leading-relaxed transition-all duration-300 ${containerStyle}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono border tracking-wider transition-colors duration-300 ${badgeStyle}`}>
                    {chunk.chunk_id}
                  </span>
                  {isRejected && (
                    <span className="text-[10px] font-bold text-red-400 uppercase tracking-wider bg-red-500/10 px-1.5 py-0.5 rounded border border-red-500/20">
                      Rejected
                    </span>
                  )}
                </div>
                <div className="font-serif">
                  {chunk.text}
                </div>
              </div>
            );
          })
        )}
      </div>
      </div>
    </div>
  );
}
