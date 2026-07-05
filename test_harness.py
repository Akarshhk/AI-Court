import sys
import asyncio
import json
from interfaces import AgentOutput, Citation

# Mock agent_runtime BEFORE orchestrator imports it to avoid google.genai dependency issues
class MockAgentRuntime:
    @staticmethod
    async def run_agent(role, system_prompt, transcript, retrieved_chunks, retry_feedback=None):
        if role == "juror_5":
            raise RuntimeError("Simulated failure for juror_5 in run_agent")
            
        citations = []
        if retrieved_chunks:
            citations = [Citation(chunk_id=retrieved_chunks[0].chunk_id, quote="Mock quote", relevance="Mock relevance")]
        
        output = AgentOutput(
            agent_role=role,
            turn=len(transcript) + 1,
            statement=f"Mock statement from {role}. Prompt snippet: {system_prompt[:50]}...",
            evidence_citations=citations,
            confidence=0.9
        )
        if role.startswith("juror_"):
            # Simple deterministic verdicts to test explicitly
            if role == "juror_1":
                output.verdict = "not_guilty"
                output.reasoning = "I am a skeptic. There are gaps."
            elif role == "juror_2":
                output.verdict = "guilty"
                output.reasoning = "I am an empath. But wait, let's tie this."
            elif role == "juror_3":
                output.verdict = "not_guilty"
                output.reasoning = "I am textualist. Literal evidence matters."
            elif role == "juror_4":
                output.verdict = "guilty"
                output.reasoning = "I am pragmatist. Most likely guilty."
            elif role == "juror_5":
                output.verdict = "undecided"
                output.reasoning = "I am contrarian. No clear conclusion."
        return output

sys.modules['agent_runtime'] = MockAgentRuntime

import orchestrator
from prompts_jury import get_system_prompt
from verdict import build_verdict_document

CASE_SCENARIO = "Mock Case Text"

from typing import Union
def simple_event_hook(event_name: str, payload: Union[AgentOutput, dict]):
    if event_name == "agent_turn" and isinstance(payload, AgentOutput):
        print(f"[{payload.agent_role.upper()}] Statement: {payload.statement}")

# Monkey patch orchestrator to use our juror prompts and simulate failure for one juror
original_safe_run_agent = orchestrator.safe_run_agent
async def patched_safe_run_agent(role, system_prompt, transcript, retrieved_chunks, retry_feedback=None):
    if role.startswith("juror_"):
        case_text = system_prompt.split("Here is the case text: ")[-1]
        system_prompt = get_system_prompt(role, "jury_deliberation", case_text)
        
        if role == "juror_5":
            # Just let it pass here, the failure happens in run_agent
            pass
            
    return await original_safe_run_agent(role, system_prompt, transcript, retrieved_chunks, retry_feedback)
orchestrator.safe_run_agent = patched_safe_run_agent

async def main():
    print("Running Mock Trial...")
    state = await orchestrator.run_trial(CASE_SCENARIO, on_event=simple_event_hook)
    
    print("\nPOLISHED VERDICT DOCUMENT:")
    polished_verdict = build_verdict_document(state)
    print(json.dumps(polished_verdict, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
