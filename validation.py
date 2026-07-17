import re
from typing import List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from interfaces import AgentOutput, Chunk, ValidationResult

def normalize_text(text: str) -> str:
    """Normalizes whitespace by collapsing internal whitespace runs to a single space, and removes quotes and inline citations."""
    text = re.sub(r'[\'\"\u2018\u2019\u201c\u201d]', '', text)
    text = re.sub(r'\[cite:\d+\]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def validate_citations(output: AgentOutput, available_chunks: List[Chunk]) -> ValidationResult:
    if not output.evidence_citations:
        return ValidationResult(is_valid=True, failed_citations=[], feedback="")
        
    available_chunk_map = {c.chunk_id: c for c in available_chunks}
    failed_citations = []
    feedbacks = []
    
    for citation in output.evidence_citations:
        if citation.chunk_id not in available_chunk_map:
            failed_citations.append(citation)
            feedbacks.append(
                f"Citation to chunk_id '{citation.chunk_id}' was not among the evidence provided this turn. "
                "Only cite chunk_ids listed in your evidence context."
            )
            continue
            
        chunk = available_chunk_map[citation.chunk_id]
        normalized_quote = normalize_text(citation.quote)
        normalized_chunk_text = normalize_text(chunk.text)
        
        if normalized_quote not in normalized_chunk_text:
            failed_citations.append(citation)
            feedbacks.append(
                f"Citation to chunk_id '{citation.chunk_id}' had a quote that does not exactly match the text of the chunk. "
                "Please quote the text verbatim."
            )
            
    if failed_citations:
        # Join feedbacks into a single string for the agent
        feedback_str = " ".join(feedbacks)
        return ValidationResult(is_valid=False, failed_citations=failed_citations, feedback=feedback_str)
        
    return ValidationResult(is_valid=True, failed_citations=[], feedback="")
