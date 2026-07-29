import re
import math
from collections import Counter
from typing import List, Dict
import sys
import os

# Add parent directory to path so interfaces can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from interfaces import Chunk

import re

def tokenize(text: str) -> List[str]:
    return re.findall(r'\w+', text.lower())

from typing import List, Dict, Tuple

def _build_store_from_chunks(chunks: List[str]) -> Tuple[List[Chunk], Dict[str, float], List[Dict[str, float]]]:
    from rag.retrieve import reset_surfaced_chunks
    reset_surfaced_chunks()
    store: List[Chunk] = []
    idf: Dict[str, float] = {}
    tfidf_vectors: List[Dict[str, float]] = []
    
    doc_freqs = Counter()
    doc_tokens = []
    
    for i, text in enumerate(chunks):
        chunk_id = f"case_chunk_{i:03d}"
        chunk = Chunk(
            chunk_id=chunk_id,
            text=text,
            metadata={"source": "case_doc", "section": f"paragraph_{i}"}
        )
        store.append(chunk)
        
        # Tokenize and compute frequencies for TF-IDF
        tokens = tokenize(text)
        doc_tokens.append(tokens)
        for t in set(tokens):
            doc_freqs[t] += 1
            
    # Compute IDF
    N = len(store)
    if N == 0:
        return store, idf, tfidf_vectors
        
    for t, df in doc_freqs.items():
        idf[t] = math.log((N + 1) / (1 + df)) + 1.0  # Smooth IDF formula
        
    # Compute TF-IDF vectors
    for tokens in doc_tokens:
        tf = Counter(tokens)
        vec = {}
        length = len(tokens)
        if length > 0:
            for t, count in tf.items():
                vec[t] = (count / length) * idf.get(t, 0.0)
        tfidf_vectors.append(vec)
        
    return store, idf, tfidf_vectors

def ingest_case(case_text: str) -> Tuple[List[Chunk], Dict[str, float], List[Dict[str, float]]]:
    # 1. Chunking: Split by single or multiple newlines
    # Since the user requested 8-15 short paragraphs, we split on newlines
    raw_chunks = [p.strip() for p in case_text.split('\n') if p.strip()]
    return _build_store_from_chunks(raw_chunks)

def ingest_custom_document(chunks: List[str]) -> Tuple[List[Chunk], Dict[str, float], List[Dict[str, float]]]:
    # Uses generic chunks passed in directly
    return _build_store_from_chunks(chunks)
