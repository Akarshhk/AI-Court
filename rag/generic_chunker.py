import re
from typing import List

def chunk_generic(text: str) -> List[str]:
    """
    Splits text into chunks of roughly 300-800 characters.
    1. Splits on paragraph boundaries.
    2. Merges short paragraphs.
    3. Splits overly long paragraphs at sentence boundaries.
    4. Caps total chunks at 60 (merging smallest if needed).
    """
    if not text:
        return []
        
    # Split by double newlines, or single newlines if no double newlines exist
    if "\n\n" in text:
        raw_paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    else:
        raw_paras = [p.strip() for p in text.split("\n") if p.strip()]
        
    if not raw_paras:
        return []

    chunks = []
    
    # Process paragraphs: split long ones, keep others as is (we'll merge short ones next)
    for p in raw_paras:
        if len(p) > 800:
            # Split by sentences (naive regex for . ! ? followed by whitespace/newlines)
            sentences = re.split(r'(?<=[.!?])\s+', p)
            current_chunk = ""
            for s in sentences:
                if len(current_chunk) + len(s) < 800:
                    current_chunk += (" " if current_chunk else "") + s
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = s
            if current_chunk:
                chunks.append(current_chunk.strip())
        else:
            chunks.append(p)
            
    # Merge short chunks
    merged_chunks = []
    current_chunk = ""
    for c in chunks:
        if not current_chunk:
            current_chunk = c
        elif len(current_chunk) + len(c) < 500: # target size to merge up to
            current_chunk += "\n\n" + c
        else:
            merged_chunks.append(current_chunk)
            current_chunk = c
    if current_chunk:
        merged_chunks.append(current_chunk)
        
    chunks = [c for c in merged_chunks if c.strip()]
    
    # Cap based on size: 1 chunk per ~500 chars, min 60, max 250
    cap = min(250, max(60, len(text) // 500))
    while len(chunks) > cap:
        # Find the pair of adjacent chunks with the smallest combined length
        min_combined = float('inf')
        min_idx = 0
        for i in range(len(chunks) - 1):
            combined = len(chunks[i]) + len(chunks[i+1])
            if combined < min_combined:
                min_combined = combined
                min_idx = i
                
        # Merge them
        chunks[min_idx] = chunks[min_idx] + "\n\n" + chunks[min_idx+1]
        chunks.pop(min_idx + 1)
        
    return chunks
