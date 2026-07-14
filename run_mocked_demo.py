import sys
import os
import argparse
import asyncio
from interfaces import AgentOutput, Citation

# Define a Mock agent runtime that mimics the trigger logic
class MockAgentRuntime:
    @staticmethod
    async def run_agent(role, system_prompt, transcript, retrieved_chunks, retry_feedback=None):
        citations = []
        if retrieved_chunks:
            # We mock the citation to match the retrieved chunk's text
            citations = [
                Citation(
                    chunk_id=retrieved_chunks[0].chunk_id,
                    quote=retrieved_chunks[0].text[:30],
                    relevance="Mock relevance"
                )
            ]
        
        # Simulate fabricated citation trigger
        if os.environ.get("FORCE_BAD_CITATION") == role and citations:
            citations[0].quote = "FABRICATED DEMO QUOTE"
            # We clear it so the retry is allowed to succeed
            del os.environ["FORCE_BAD_CITATION"]

        output = AgentOutput(
            agent_role=role,
            turn=len(transcript) + 1,
            statement=f"Mock statement from {role}. Citing {citations[0].chunk_id if citations else 'none'}.",
            evidence_citations=citations,
            confidence=0.9
        )
        
        if role.startswith("juror"):
            # If the 10b5-1 fact (Index 10) is omitted, let's make jurors vote guilty.
            # Otherwise, they vote not_guilty (or split).
            # We check for "mandated" because "10b5-1" is also in fact index 9 (which is not omitted).
            has_10b5_1_mandated = "mandated" in system_prompt
            
            if not has_10b5_1_mandated:
                output.verdict = "guilty"
                output.reasoning = "Without the 10b5-1 plan mandating the sale, the stock sale is extremely suspicious insider trading."
            else:
                # Normal clean run: split jury (3 not_guilty vs 2 guilty) -> majority not_guilty
                if role in ["juror_1", "juror_2", "juror_5"]:
                    output.verdict = "not_guilty"
                    output.reasoning = "The pre-scheduled 10b5-1 plan mandates the sale, showing lack of insider intent."
                else:
                    output.verdict = "guilty"
                    output.reasoning = "Even with a 10b5-1 plan, the timing of reading the email remains suspicious."
                    
        return output

sys.modules['agent_runtime'] = MockAgentRuntime

# Monkey patch retrieve to use mocks so we don't hit real APIs
import mocks
sys.modules['rag.retrieve'] = mocks

import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mocked AI Courtroom Demo")
    parser.add_argument("--force-bad-citation", type=str, help="Force a bad citation for a specific role (e.g. prosecution)")
    parser.add_argument("--omit-fact", type=int, help="Index of the fact to omit (e.g. 10)")
    args = parser.parse_args()

    if args.force_bad_citation:
        os.environ["FORCE_BAD_CITATION"] = args.force_bad_citation

    asyncio.run(main.main(args.omit_fact))
