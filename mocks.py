import asyncio
import random
from typing import List, Optional
from interfaces import Chunk, Citation, AgentOutput, ValidationResult

def reset_surfaced_chunks():
    pass

async def retrieve(query: str, store: List[Chunk], idf: dict, tfidf_vectors: list, k: int = 3) -> List[Chunk]:
    """Mock retrieval returning fake chunks."""
    await asyncio.sleep(0.1)  # Simulate network latency
    chunks = []
    for i in range(k):
        chunk_id = f"case_chunk_{random.randint(100, 999)}"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                text=f"This is a retrieved piece of evidence for query: {query}",
                metadata={"source": "case_doc", "section": f"section_{i}"}
            )
        )
    return chunks

def validate_citations(output: AgentOutput, available_chunks: List[Chunk]) -> ValidationResult:
    """Mock validation that fails ~20% of the time to trigger retry logic."""
    # Ensure there's a predictable way to force a fail or pass if needed, 
    # but for now we just use a ~20% random failure rate.
    if not output.evidence_citations:
        return ValidationResult(is_valid=True, failed_citations=[], feedback="")

    is_valid = random.random() > 0.20
    
    if is_valid:
        return ValidationResult(is_valid=True, failed_citations=[], feedback="")
    else:
        failed = output.evidence_citations[0]
        return ValidationResult(
            is_valid=False,
            failed_citations=[failed],
            feedback=f"Citation for chunk {failed.chunk_id} could not be found or quote did not match."
        )

async def run_agent(
    role: str,
    system_prompt: str,
    transcript: List[AgentOutput],
    retrieved_chunks: List[Chunk],
    retry_feedback: Optional[str] = None
) -> AgentOutput:
    """Mock agent call returning plausible outputs and citations."""
    await asyncio.sleep(0.2)  # Simulate API latency
    
    # Generate some fake citations based on the retrieved chunks
    citations = []
    if retrieved_chunks:
        chunk = retrieved_chunks[0]
        citations.append(
            Citation(
                chunk_id=chunk.chunk_id,
                quote=chunk.text[:20] + "...",
                relevance=f"Supports the argument made by {role}."
            )
        )
        
    statement = f"I am the {role}. "
    if retry_feedback:
        statement += f"I have corrected my citations based on the feedback: {retry_feedback}. "
    statement += "Here is my argument."

    output = AgentOutput(
        agent_role=role,
        turn=len(transcript) + 1,
        statement=statement,
        evidence_citations=citations,
        confidence=round(random.uniform(0.7, 0.99), 2)
    )

    if role.startswith("juror"):
        output.verdict = random.choice(["guilty", "guilty", "not_guilty"]) # Bias towards guilty to occasionally have dissent
        output.reasoning = f"Based on the evidence, I vote {output.verdict}."
        
    return output
