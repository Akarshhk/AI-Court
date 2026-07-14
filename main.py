import argparse
import asyncio
import json
import os
from orchestrator import run_trial
from interfaces import AgentOutput
from case import get_case_text
from rag.ingest import ingest_case

def simple_event_hook(event_name: str, payload: AgentOutput | dict):
    """Callback to print live trial events."""
    if event_name == "phase_change":
        print(f"\n[{'='*10} PHASE CHANGE: {payload.get('phase', '').upper()} {'='*10}]")
    elif event_name == "agent_turn":
        if isinstance(payload, AgentOutput):
            print(f"[{payload.agent_role.upper()}] (Turn {payload.turn}): {payload.statement}")

async def main(omit_fact_idx: int = None):
    print("Starting AI Courtroom Trial...")
    
    case_text = get_case_text(omit_fact_idx)
    # Ingest the case document into our vector store
    ingest_case(case_text)
    
    # Run trial end-to-end with the event hook
    state = await run_trial(case_text, on_event=simple_event_hook)
    
    print("\n\n" + "="*40)
    print("TRIAL COMPLETE - FULL TRANSCRIPT:")
    print("="*40)
    
    for turn in sorted(state.transcript, key=lambda x: x.turn):
        role_label = turn.agent_role.upper()
        # Visual indicator for unverified claims
        if getattr(turn, "is_unverified", False):
            role_label = f"!{role_label} (UNVERIFIED)!"
            
        print(f"\n{role_label} (Turn {turn.turn}):")
        print(f"Statement: {turn.statement}")
        print("Citations:")
        for c in turn.evidence_citations:
            print(f"  - Chunk: {c.chunk_id} | Quote: '{c.quote}'")
            print(f"    Relevance: {c.relevance}")
            
        if turn.agent_role.startswith("juror"):
            print(f"Verdict: {turn.verdict}")
            print(f"Reasoning: {turn.reasoning}")

    print("\n" + "="*40)
    print("FINAL VERDICT DOCUMENT:")
    print("="*40)
    try:
        from verdict import build_verdict_document
        polished_verdict = build_verdict_document(state)
        print(json.dumps(polished_verdict, indent=2))
    except Exception as e:
        print(f"Error building polished verdict document: {e}")
        if state.verdict_document:
            print("\nFallback to simple verdict document:")
            print(json.dumps(state.verdict_document, indent=2))
        else:
            print("Error: No verdict document produced.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Courtroom Demo")
    parser.add_argument("--force-bad-citation", type=str, help="Force a bad citation for a specific role (e.g. prosecution)")
    parser.add_argument("--omit-fact", type=int, help="Index of the fact to omit (e.g. 10)")
    args = parser.parse_args()

    if args.force_bad_citation:
        os.environ["FORCE_BAD_CITATION"] = args.force_bad_citation

    asyncio.run(main(args.omit_fact))
