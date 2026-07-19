import re
from difflib import SequenceMatcher
from typing import List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from interfaces import AgentOutput, Chunk, ValidationResult

def normalize_text(text: str) -> str:
    """Normalizes whitespace by collapsing internal whitespace runs to a single space, and removes quotes and inline citations."""
    text = re.sub(r'[\'\"\\u2018\\u2019\\u201c\\u201d\u2018\u2019\u201c\u201d]', '', text)
    text = re.sub(r'\[cite:\d+\]', '', text)
    # Remove parenthetical asides for matching flexibility
    text = re.sub(r'\([^)]*\)', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

FUZZY_THRESHOLD = 0.85  # 85% similarity required

def fuzzy_quote_match(normalized_quote: str, normalized_chunk: str) -> bool:
    """Check if the quote appears in the chunk, allowing for minor differences.
    
    First tries exact substring match. If that fails, slides a window
    across the chunk text and checks SequenceMatcher ratio.
    """
    # Fast path: exact substring
    if normalized_quote in normalized_chunk:
        return True
    
    # Fuzzy path: sliding window comparison
    quote_len = len(normalized_quote)
    if quote_len == 0:
        return False
    
    # Use a window slightly larger and smaller than the quote to account for length differences
    for window_delta in range(-20, 21, 5):
        window_size = quote_len + window_delta
        if window_size <= 0 or window_size > len(normalized_chunk):
            continue
        for start in range(0, len(normalized_chunk) - window_size + 1, 10):
            window = normalized_chunk[start:start + window_size]
            ratio = SequenceMatcher(None, normalized_quote, window).ratio()
            if ratio >= FUZZY_THRESHOLD:
                return True
    
    return False

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
        
        if not fuzzy_quote_match(normalized_quote, normalized_chunk_text):
            failed_citations.append(citation)
            feedbacks.append(
                f"Citation to chunk_id '{citation.chunk_id}' had a quote that does not match the text of the chunk. "
                "Please quote the text verbatim."
            )
            
    if failed_citations:
        # Join feedbacks into a single string for the agent
        feedback_str = " ".join(feedbacks)
        return ValidationResult(is_valid=False, failed_citations=failed_citations, feedback=feedback_str)
        
    return ValidationResult(is_valid=True, failed_citations=[], feedback="")
