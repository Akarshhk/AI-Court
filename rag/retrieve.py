import math
import hashlib
from typing import List, Dict, Tuple
from collections import Counter
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from interfaces import Chunk
from rag.ingest import STORE, IDF, TFIDF_VECTORS, tokenize

def cosine_sim(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    dot = sum(v1.get(t, 0) * v2.get(t, 0) for t in set(v1) | set(v2))
    mag1 = math.sqrt(sum(v**2 for v in v1.values()))
    mag2 = math.sqrt(sum(v**2 for v in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)

async def retrieve(query: str, k: int = 3) -> List[Chunk]:
    if not STORE:
        return []
        
    query_tokens = tokenize(query)
    # Compute query vector
    tf = Counter(query_tokens)
    query_vec = {}
    length = len(query_tokens)
    if length > 0:
        for t, count in tf.items():
            query_vec[t] = (count / length) * IDF.get(t, 0.0)
            
    scores: List[Tuple[float, int]] = []
    for i, chunk_vec in enumerate(TFIDF_VECTORS):
        score = cosine_sim(query_vec, chunk_vec)
        scores.append((score, i))
        
    # Sort by score descending, then by index to maintain stability
    scores.sort(key=lambda x: (-x[0], x[1]))
    
    # If top scores are 0, we fall back to returning an empty list to trigger the orchestrator's RAG fallback
    if scores[0][0] == 0.0:
        return []
        
    top_k_indices = [idx for score, idx in scores[:k]]
    return [STORE[idx] for idx in top_k_indices]
