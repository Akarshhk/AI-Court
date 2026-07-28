import os
import logging
from typing import Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy_key"))

class CaseValidationResult(BaseModel):
    is_valid_case: bool = Field(description="True if the text describes a legal case, dispute, or complaint.")
    confidence: float = Field(description="Confidence level from 0.0 to 1.0.")
    reason: str = Field(description="Short human-readable explanation of the classification.")
    detected_subject: Optional[str] = Field(description="Short description of the dispute, or the subject if not a case (e.g. 'research paper').")

async def validate_case_document(text: str) -> CaseValidationResult:
    """Validates if the provided text looks like a case or dispute."""
    # Truncate input text to roughly the first 5000 characters
    truncated_text = text[:5000]
    
    system_prompt = """You are a case validation utility. Your job is to determine whether the provided text describes an actual case, dispute, or allegation with identifiable parties and some factual claim that could be argued FOR or AGAINST.
    
Explicit Rules:
- DO NOT be overly strict. Informal disputes (e.g., a workplace conflict described in an email, a consumer complaint, an incident report) count as valid cases even without formal legal language.
- ONLY flag content as invalid if it has no dispute or claim at all (e.g., research papers, manuals, recipes, unrelated narrative text)."""

    try:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=CaseValidationResult,
            temperature=0.1,
        )
        
        response = await client.aio.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=truncated_text,
            config=config,
        )
        return response.parsed
    except Exception as e:
        logging.error(f"Error validating case document: {e}")
        return CaseValidationResult(
            is_valid_case=True,
            confidence=0.0,
            reason="Validation check unavailable",
            detected_subject=None
        )
