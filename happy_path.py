import sys
import asyncio
import json
from interfaces import AgentOutput, Citation

class MockAgentRuntime:
    @staticmethod
    async def run_agent(role, system_prompt, transcript, retrieved_chunks, retry_feedback=None):
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
                output.verdict = "guilty"
                output.reasoning = "I am contrarian, but I vote guilty."
        return output

sys.modules['agent_runtime'] = MockAgentRuntime

import orchestrator
from prompts_jury import get_system_prompt
from verdict import build_verdict_document
from validation import ValidationResult

# Mock validation to always return True for happy path
orchestrator.validate_citations = lambda output, chunks: ValidationResult(is_valid=True, failed_citations=[], feedback="")

original_safe_run_agent = orchestrator.safe_run_agent
async def patched_safe_run_agent(role, system_prompt, transcript, retrieved_chunks, retry_feedback=None):
    if role.startswith("juror_"):
        case_text = system_prompt.split("Here is the case text: ")[-1]
        system_prompt = get_system_prompt(role, "jury_deliberation", case_text)
    return await original_safe_run_agent(role, system_prompt, transcript, retrieved_chunks, retry_feedback)
orchestrator.safe_run_agent = patched_safe_run_agent

async def main():
    state = await orchestrator.run_trial("Mock Case Text")
    print(json.dumps(build_verdict_document(state), indent=2))

if __name__ == "__main__":
    asyncio.run(main())
