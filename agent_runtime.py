import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from interfaces import AgentOutput, Chunk, Citation
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy_key"))

class CitationSchema(BaseModel):
    chunk_id: str = Field(description="Must match a provided Chunk ID exactly")
    quote: str = Field(description="Exact text quoted verbatim from the chunk")
    relevance: str = Field(description="Why this quote is relevant")

class AgentOutputSchema(BaseModel):
    statement: str = Field(description="Your main argument or statement.")
    evidence_citations: List[CitationSchema]
    confidence: float = Field(description="Your confidence level from 0.0 to 1.0")
    
class JurorOutputSchema(AgentOutputSchema):
    verdict: str = Field(description="Must be 'guilty', 'not_guilty', or 'undecided'")
    reasoning: str = Field(description="Reasoning for your verdict")

async def run_agent(
    role: str,
    system_prompt: str,
    transcript: List[AgentOutput],
    retrieved_chunks: List[Chunk],
    retry_feedback: Optional[str] = None,
) -> AgentOutput:
    # 1. Compile Transcript
    transcript_text = ""
    for out in transcript:
        transcript_text += f"[Turn {out.turn} - {out.agent_role.upper()}]:\n{out.statement}\n\n"
    if not transcript_text:
        transcript_text = "No history yet.\n"
        
    # 2. Compile Evidence
    evidence_text = ""
    for c in retrieved_chunks:
        evidence_text += f"--- Chunk ID: {c.chunk_id} ---\n{c.text}\n\n"
    if not evidence_text:
        evidence_text = "No evidence chunks available.\n"
        
    # 3. Build User Message
    user_content = f"TRANSCRIPT HISTORY:\n{transcript_text}\n"
    user_content += f"AVAILABLE EVIDENCE:\n{evidence_text}\n"
    user_content += "INSTRUCTIONS:\n"
    user_content += "Cite ONLY chunk_ids from the AVAILABLE EVIDENCE above. "
    user_content += "Quote text verbatim exactly as it appears in the chunk.\n"
    
    if retry_feedback:
        user_content += f"\nCORRECTION REQUIRED:\nYour previous answer failed validation: {retry_feedback}. Revise using only the evidence listed above, quoting it exactly.\n"

    # 4. Define schema
    is_juror = role.startswith("juror")
    schema = JurorOutputSchema if is_juror else AgentOutputSchema

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.2,
    )
    
    # 5. Call API
    response = await client.aio.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=user_content,
        config=config
    )
    
    # 6. Parse response
    data = json.loads(response.text)
    
    citations = [
        Citation(
            chunk_id=c.get("chunk_id", ""),
            quote=c.get("quote", ""),
            relevance=c.get("relevance", "")
        ) for c in data.get("evidence_citations", [])
    ]
    
    # DEMO TRIGGER: Fabricated citation
    if os.environ.get("FORCE_BAD_CITATION") == role and citations:
        citations[0].quote = "FABRICATED DEMO QUOTE"
        del os.environ["FORCE_BAD_CITATION"]
    
    output = AgentOutput(
        agent_role=role,
        turn=len(transcript) + 1,
        statement=data.get("statement", ""),
        evidence_citations=citations,
        confidence=data.get("confidence", 0.5)
    )
    
    if is_juror:
        output.verdict = data.get("verdict")
        output.reasoning = data.get("reasoning")
        
    return output
