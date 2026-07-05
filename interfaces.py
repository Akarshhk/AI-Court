from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any

class Chunk(BaseModel):
    chunk_id: str
    text: str
    metadata: dict  # e.g. {"source": "case_doc", "section": "witness_statement_2"}

class Citation(BaseModel):
    chunk_id: str
    quote: str
    relevance: str

class AgentOutput(BaseModel):
    model_config = ConfigDict(extra='allow')
    
    agent_role: str            # "judge" | "prosecution" | "defense" | "juror_1".."juror_n" | "clerk"
    turn: int
    statement: str
    evidence_citations: List[Citation]
    confidence: float          # 0.0-1.0
    verdict: Optional[str] = None     # jurors only: "guilty" | "not_guilty" | "undecided"
    reasoning: Optional[str] = None   # jurors only

class ValidationResult(BaseModel):
    is_valid: bool
    failed_citations: List[Citation]
    feedback: str   # human-readable reason, fed back to the agent on retry

class CaseState(BaseModel):
    case_id: str
    case_text: str
    transcript: List[AgentOutput]
    turn_counter: int
    phase: str   # "opening" | "prosecution_argument" | "defense_rebuttal" | "judge_ruling" | "jury_deliberation" | "verdict_complete"
    verdict_document: Optional[dict] = None
