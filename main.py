import asyncio
import json
from orchestrator import run_trial
from interfaces import AgentOutput

# Hardcoded sample case
CASE_SCENARIO = """
Fictional Corporate Fraud Scenario: ApexTech Holdings
On March 3rd, 2024, an unauthorized wire transfer of $40,000 was initiated from ApexTech's operating account to an offshore entity, 'Nimbus Consulting'. 
The prosecution alleges that the CEO, Jane Doe, authorized this transfer to pay off personal gambling debts. 
Evidence includes a recovered email from Jane's corporate account dated March 2nd stating: 'Initiate the Nimbus payment immediately, bypass standard audit'.
The defense claims Jane's email was compromised by a phishing attack and that she was on a flight without Wi-Fi during the time of authorization.
Flight logs confirm Jane was on Flight 882 from NYC to London. 
IT logs show a login to Jane's email from an IP address in Eastern Europe at the time the 'Nimbus' email was sent.
"""

def simple_event_hook(event_name: str, payload: AgentOutput | dict):
    """Callback to print live trial events."""
    if event_name == "phase_change":
        print(f"\n[{'='*10} PHASE CHANGE: {payload.get('phase', '').upper()} {'='*10}]")
    elif event_name == "agent_turn":
        if isinstance(payload, AgentOutput):
            print(f"[{payload.agent_role.upper()}] (Turn {payload.turn}): {payload.statement}")

async def main():
    print("Starting AI Courtroom Trial...")
    
    # Run trial end-to-end with the event hook
    state = await run_trial(CASE_SCENARIO, on_event=simple_event_hook)
    
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
    asyncio.run(main())
