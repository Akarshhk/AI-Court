import { useRef, useCallback } from 'react';

const mockEvents = [
  { type: 'phase_change', payload: { phase: 'opening' }, delay: 1000 },
  { type: 'agent_turn', payload: { agent_role: 'judge', turn: 1, statement: 'Order in the court. The trial will now commence. Prosecution, you may present your opening statement.', confidence: 0.99 }, delay: 2000 },
  { type: 'phase_change', payload: { phase: 'prosecution_argument' }, delay: 3000 },
  { type: 'agent_turn', payload: { agent_role: 'prosecution', turn: 2, statement: 'The evidence clearly shows the defendant\'s involvement. According to the log files...', evidence_citations: [{ chunk_id: 'case_chunk_004', quote: 'User accessed server at 02:00', relevance: 'Proves presence' }], confidence: 0.95 }, delay: 3000 },
  { type: 'agent_turn', payload: { agent_role: 'prosecution', turn: 3, statement: '[UNVERIFIED] The defendant also confessed to the crime in a deleted email.', evidence_citations: [{ chunk_id: 'case_chunk_007', quote: 'The defendant confessed', relevance: 'Confession email' }], confidence: 0.5, is_unverified: true }, delay: 3000 },
  { type: 'phase_change', payload: { phase: 'defense_rebuttal' }, delay: 2000 },
  { type: 'agent_turn', payload: { agent_role: 'defense', turn: 4, statement: 'Objection! The prosecution is relying on unverified claims. The log files were modified.', evidence_citations: [{ chunk_id: 'case_chunk_009', quote: 'Admin access granted to 3rd party', relevance: 'Alternative suspect' }], confidence: 0.9 }, delay: 3000 },
  { type: 'phase_change', payload: { phase: 'judge_ruling' }, delay: 2000 },
  { type: 'agent_turn', payload: { agent_role: 'judge', turn: 5, statement: 'The unverified statement will be stricken from the record. The jury will disregard it.', confidence: 0.99 }, delay: 3000 },
  { type: 'phase_change', payload: { phase: 'jury_deliberation' }, delay: 2000 },
  { type: 'agent_turn', payload: { agent_role: 'juror_1', turn: 6, statement: 'I believe the evidence points to guilt.', verdict: 'guilty', reasoning: 'Log files are convincing.', confidence: 0.8 }, delay: 3000 },
  { type: 'agent_turn', payload: { agent_role: 'juror_2', turn: 7, statement: 'Wait, I am confused...', is_failed: true }, delay: 2000 },
  { type: 'juror_alternate_invoked', payload: { original_role: 'juror_2', reason: 'failed' }, delay: 1000 },
  { type: 'agent_turn', payload: { agent_role: 'juror_2_alternate', turn: 8, statement: 'I find the defense argument compelling. Reasonable doubt exists.', verdict: 'not_guilty', reasoning: 'Third party access introduces doubt.', confidence: 0.85 }, delay: 2000 },
  { type: 'agent_turn', payload: { agent_role: 'juror_3', turn: 9, statement: 'Guilty. The defense lacks proof.', verdict: 'guilty', reasoning: 'Prosecution evidence stands.', confidence: 0.9 }, delay: 2000 },
  { type: 'agent_turn', payload: { agent_role: 'juror_4', turn: 10, statement: 'Guilty. I agree with Juror 1.', verdict: 'guilty', reasoning: 'Strong timeline.', confidence: 0.85 }, delay: 2000 },
  { type: 'agent_turn', payload: { agent_role: 'juror_5', turn: 11, statement: 'Guilty. No other plausible explanation.', verdict: 'guilty', reasoning: 'Process of elimination.', confidence: 0.95 }, delay: 2000 },
  { type: 'phase_change', payload: { phase: 'verdict_complete' }, delay: 2000 },
  { type: 'verdict_document_ready', payload: { 
      final_verdict: 'guilty', 
      vote_breakdown: { guilty: 4, not_guilty: 1 },
      dissenting_opinions: [{ juror: 'juror_2_alternate', verdict: 'not_guilty', reasoning: 'Third party access introduces doubt.' }],
      all_citations_used: [
        { chunk_id: 'case_chunk_004', quote: 'User accessed server at 02:00', relevance: 'Proves presence' },
        { chunk_id: 'case_chunk_009', quote: 'Admin access granted to 3rd party', relevance: 'Alternative suspect' }
      ]
  }, delay: 1000 }
];

export function useMockStream(onEvent, onComplete) {
  const timeoutsRef = useRef([]);
  
  const startStream = useCallback(() => {
    let cumulativeDelay = 0;
    mockEvents.forEach((event, index) => {
      cumulativeDelay += event.delay;
      const timeout = setTimeout(() => {
        onEvent(event);
        if (index === mockEvents.length - 1 && onComplete) {
          onComplete();
        }
      }, cumulativeDelay);
      timeoutsRef.current.push(timeout);
    });
  }, [onEvent, onComplete]);

  const stopStream = useCallback(() => {
    timeoutsRef.current.forEach(clearTimeout);
    timeoutsRef.current = [];
  }, []);

  return { startStream, stopStream };
}
