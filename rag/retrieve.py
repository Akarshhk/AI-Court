import math
import hashlib
from typing import List, Dict, Tuple
from collections import Counter
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from interfaces import Chunk
from rag.ingest import tokenize

SURFACED_CHUNK_IDS = set()

def reset_surfaced_chunks():
    global SURFACED_CHUNK_IDS
    SURFACED_CHUNK_IDS.clear()

def cosine_sim(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    dot = sum(v1.get(t, 0) * v2.get(t, 0) for t in set(v1) | set(v2))
    mag1 = math.sqrt(sum(v**2 for v in v1.values()))
    mag2 = math.sqrt(sum(v**2 for v in v2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)

async def retrieve(query: str, store: List[Chunk], idf: Dict[str, float], tfidf_vectors: List[Dict[str, float]], k: int = 3) -> List[Chunk]:
    if not store:
        return []
        
    # Scale k dynamically based on total chunk count
    dynamic_k = max(5, min(15, math.ceil(len(store) / 12)))
    k = dynamic_k

        
    query_tokens = tokenize(query)
    # Compute query vector
    tf = Counter(query_tokens)
    query_vec = {}
    length = len(query_tokens)
    if length > 0:
        for t, count in tf.items():
            query_vec[t] = (count / length) * idf.get(t, 0.0)
            
    scores: List[Tuple[float, int]] = []
    for i, chunk_vec in enumerate(tfidf_vectors):
        score = cosine_sim(query_vec, chunk_vec)
        scores.append((score, i))
        
    # Sort by score descending, then by index to maintain stability
    scores.sort(key=lambda x: (-x[0], x[1]))
    
    max_score = scores[0][0] if scores else 0.0
    print(f"[RETRIEVAL] Query: '{query}' | Top Score: {max_score:.4f}")
    
    # If top scores are very low (near-zero overlap with case text), return a deterministically rotated 
    # slice of chunks based on the query (which contains role+phase), rather than identical top-k or empty list.
    if max_score < 0.05:
        # Hash the query to an offset
        query_hash = int(hashlib.md5(query.encode('utf-8')).hexdigest(), 16)
        offset = query_hash % len(store)
        rotated_indices = [(offset + i) % len(store) for i in range(k)]
        selected_chunks = [store[idx] for idx in rotated_indices]
        for c in selected_chunks:
            SURFACED_CHUNK_IDS.add(c.chunk_id)
        return selected_chunks
        
    # Diversity-Aware Selection (MMR)
    pool_size = min(len(store), max(30, 3 * k))
    candidate_indices = [idx for _, idx in scores[:pool_size]]
    idx_to_query_sim = {idx: score for score, idx in scores[:pool_size]}
    
    if not candidate_indices:
        return []
        
    selected_indices = [candidate_indices[0]] # Pick highest scoring first
    unselected_indices = candidate_indices[1:]
    
    while len(selected_indices) < min(k, len(candidate_indices)):
        best_score = -float('inf')
        best_idx = -1
        
        for idx in unselected_indices:
            # Relevance to query
            sim_to_query = idx_to_query_sim[idx]
            
            # Max similarity to already selected
            max_sim_to_selected = max([cosine_sim(tfidf_vectors[idx], tfidf_vectors[s_idx]) for s_idx in selected_indices])
            
            # Boost if not surfaced yet
            boost = 0.05 if store[idx].chunk_id not in SURFACED_CHUNK_IDS else 0.0
            
            # MMR Score
            mmr_score = (0.7 * sim_to_query) - (0.3 * max_sim_to_selected) + boost

            # ADD THIS DEBUG BLOCK:
            if store[idx].chunk_id.endswith("_005"): # 005 is the 6th chunk (0-indexed)
                print(f"[DEBUG] Chunk 6 -> Sim2Query: {sim_to_query:.4f} | Penalty: {max_sim_to_selected:.4f} | Boost: {boost} | Final MMR: {mmr_score:.4f}")
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx
                
        selected_indices.append(best_idx)
        unselected_indices.remove(best_idx)
        
    selected_chunks = [store[idx] for idx in selected_indices]
    for c in selected_chunks:
        SURFACED_CHUNK_IDS.add(c.chunk_id)
        
    return selected_chunks

