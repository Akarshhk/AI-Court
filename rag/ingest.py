import re
import math
from collections import Counter
from typing import List, Dict
import sys
import os

# Add parent directory to path so interfaces can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from interfaces import Chunk

# Global state for the single-process vector store
STORE: List[Chunk] = []
IDF: Dict[str, float] = {}
TFIDF_VECTORS: List[Dict[str, float]] = []

def tokenize(text: str) -> List[str]:
    return re.findall(r'\w+', text.lower())

def ingest_case(case_text: str) -> None:
    global STORE, IDF, TFIDF_VECTORS
    
    # 1. Chunking: Split by single or multiple newlines
    # Since the user requested 8-15 short paragraphs, we split on newlines
    raw_chunks = [p.strip() for p in case_text.split('\n') if p.strip()]
    
    STORE.clear()
    doc_freqs = Counter()
    doc_tokens = []
    
    for i, text in enumerate(raw_chunks):
        chunk_id = f"case_chunk_{i:03d}"
        chunk = Chunk(
            chunk_id=chunk_id,
            text=text,
            metadata={"source": "case_doc", "section": f"paragraph_{i}"}
        )
        STORE.append(chunk)
        
        # Tokenize and compute frequencies for TF-IDF
        tokens = tokenize(text)
        doc_tokens.append(tokens)
        for t in set(tokens):
            doc_freqs[t] += 1
            
    # Compute IDF
    N = len(STORE)
    if N == 0:
        return
        
    IDF.clear()
    for t, df in doc_freqs.items():
        IDF[t] = math.log((N + 1) / (1 + df)) + 1.0  # Smooth IDF formula
        
    # Compute TF-IDF vectors
    TFIDF_VECTORS.clear()
    for tokens in doc_tokens:
        tf = Counter(tokens)
        vec = {}
        length = len(tokens)
        if length > 0:
            for t, count in tf.items():
                vec[t] = (count / length) * IDF.get(t, 0.0)
        TFIDF_VECTORS.append(vec)
