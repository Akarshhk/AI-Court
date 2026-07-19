import asyncio
from typing import Callable, List, Optional, Union, Dict, Any
from interfaces import CaseState, AgentOutput, Chunk

# Import the real agent runtime
from agent_runtime import run_agent
from rag.retrieve import retrieve
from validation import validate_citations
NUM_ARGUMENT_ROUNDS = 1
NUM_JURORS = 5
MAX_CITATION_RETRIES = 2
AGENT_TIMEOUT_SECONDS = 10.0
JUROR_VALID_VOTES = {"guilty", "not_guilty"}

async def safe_run_agent(
    role: str,
    system_prompt: str,
    transcript: List[AgentOutput],
    retrieved_chunks: List[Chunk],
    retry_feedback: Optional[str] = None
) -> AgentOutput:
    """Wraps run_agent with a timeout and one generic failure retry, returning a fallback on complete failure."""
    for attempt in range(2):
        try:
            return await asyncio.wait_for(
                run_agent(role, system_prompt, transcript, retrieved_chunks, retry_feedback),
                timeout=AGENT_TIMEOUT_SECONDS
            )
        except Exception as e:
            if attempt == 1:
                # Return placeholder tagged as FAILED
                fallback = AgentOutput(
                    agent_role=role,
                    turn=len(transcript) + 1,
                    statement=f"[{role} failed to respond: {str(e)}]",
                    evidence_citations=[],
                    confidence=0.0
                )
                fallback.is_failed = True # type: ignore (using pydantic extra='allow')
                if role.startswith("juror"):
                    fallback.verdict = None
                    fallback.reasoning = "Failed to deliberate."
                return fallback
    
    # Should not reach here due to the return in the except block, but just in case
    return AgentOutput(
        agent_role=role,
        turn=len(transcript) + 1,
        statement="[Critical failure]",
        evidence_citations=[],
        confidence=0.0
    )


def build_retrieval_query(role: str, phase: str, state: CaseState) -> str:
    fallback_query = state.case_text[:500]
    
    if phase == "opening":
        return fallback_query
        
    if role in {"prosecution", "defense"}:
        opposing_role = "defense" if role == "prosecution" else "prosecution"
        
        opposing_statement = None
        for turn in reversed(state.transcript):
            if turn.agent_role == opposing_role:
                stmt = turn.statement
                if stmt.startswith("[UNVERIFIED] "):
                    stmt = stmt[len("[UNVERIFIED] "):]
                opposing_statement = stmt
                break
                
        if opposing_statement:
            return opposing_statement
        else:
            return fallback_query
            
    if role == "judge" and phase == "judge_ruling":
        statements = []
        for turn in state.transcript:
            if turn.agent_role in {"prosecution", "defense"}:
                stmt = turn.statement
                if stmt.startswith("[UNVERIFIED] "):
                    stmt = stmt[len("[UNVERIFIED] "):]
                statements.append(stmt)
        if statements:
            return " ".join(statements)
            
    if role.startswith("juror_"):
        statements = []
        for turn in state.transcript:
            if turn.agent_role in {"prosecution", "defense", "judge"}:
                stmt = turn.statement
                if stmt.startswith("[UNVERIFIED] "):
                    stmt = stmt[len("[UNVERIFIED] "):]
                statements.append(stmt)
        if statements:
            return " ".join(statements)
            
    return f"{role} argument for {phase}"

async def execute_agent_turn(
    role: str,
    phase: str,
    state: CaseState,
    on_event: Optional[Callable[[str, Union[AgentOutput, dict]], None]] = None
) -> AgentOutput:
    """Executes a single agent's turn with retrieval, validation, and retry logic."""
    def get_prompt(r: str, p: str, c: str) -> str:
        if r.startswith("juror_"):
            from prompts_jury import get_system_prompt
        else:
            from prompts_trial import get_system_prompt
        return get_system_prompt(r, p, c)
        
    system_prompt = get_prompt(role, phase, state.case_text)
    
    # 1. Retrieve
    query = build_retrieval_query(role, phase, state)
    chunks = await retrieve(query, state.evidence_store, state.idf, state.tfidf_vectors, k=5)
    
    if not chunks:
        if on_event:
            on_event("rag_fallback", {"role": role, "phase": phase, "message": "Using full case text due to retrieval failure."})
        system_prompt += f"\n\n[SYSTEM NOTE: Retrieval failed. Full case text provided instead:]\n{state.case_text}"
    
    # 2. Agent Call with Validation Retry Loop
    feedback = None
    output = None
    is_unverified = False
    
    for attempt in range(MAX_CITATION_RETRIES + 1):
        output = await safe_run_agent(
            role=role,
            system_prompt=system_prompt,
            transcript=state.transcript,
            retrieved_chunks=chunks,
            retry_feedback=feedback
        )
        
        # If it failed entirely (e.g. timeout), break out and accept the FAILED placeholder
        if getattr(output, "is_failed", False):
            break
            
        # 3. Validate
        validation = validate_citations(output, chunks)
        if validation.is_valid:
            is_unverified = False
            break
        else:
            print(f"\n--- [CITATION VALIDATION FAILURE] {role.upper()} (Attempt {attempt + 1}/{MAX_CITATION_RETRIES + 1}) ---")
            print(f"Feedback sent to agent: {validation.feedback}\n")
            feedback = validation.feedback
            is_unverified = True
    
    if output is None:
        raise RuntimeError("Agent output unexpectedly None")

    if is_unverified:
        # Tag as UNVERIFIED via statement prefix to be visibly logged
        output.statement = f"[UNVERIFIED] {output.statement}"
        output.is_unverified = True # type: ignore (using pydantic extra='allow')

    # Append to transcript
    state.transcript.append(output)
    state.turn_counter += 1
    
    if on_event:
        on_event("agent_turn", output)

    if role.startswith("juror_") and not role.endswith("_alternate"):
        is_hard_failure = getattr(output, "is_failed", False)
        needs_alternate = False
        reason = ""
        
        if is_hard_failure:
            needs_alternate = True
            reason = "failed"
        elif output.verdict not in JUROR_VALID_VOTES:
            correction_feedback = "Your response did not include a valid verdict. You must set verdict to exactly 'guilty' or 'not_guilty' — no other value, capitalization, or punctuation is accepted."
            corrected_output = await safe_run_agent(
                role=role,
                system_prompt=system_prompt,
                transcript=state.transcript,
                retrieved_chunks=chunks,
                retry_feedback=correction_feedback
            )
            
            if not getattr(corrected_output, "is_failed", False):
                corrected_validation = validate_citations(corrected_output, chunks)
                if not corrected_validation.is_valid:
                    corrected_output.statement = f"[UNVERIFIED] {corrected_output.statement}"
                    corrected_output.is_unverified = True # type: ignore
                    
            state.transcript.append(corrected_output)
            state.turn_counter += 1
            if on_event:
                on_event("agent_turn", corrected_output)
                
            if not getattr(corrected_output, "is_failed", False) and corrected_output.verdict in JUROR_VALID_VOTES:
                output = corrected_output
            else:
                needs_alternate = True
                reason = "malformed_vote"
                
        if needs_alternate:
            if on_event:
                on_event("juror_alternate_invoked", {"original_role": role, "reason": reason})
            alt_role = f"{role}_alternate"
            output = await execute_agent_turn(alt_role, phase, state, on_event)

    return output

def transition_phase(state: CaseState, new_phase: str, on_event: Optional[Callable[[str, Union[AgentOutput, dict]], None]] = None):
    """Helper to transition phase and trigger event."""
    state.phase = new_phase
    if on_event:
        on_event("phase_change", {"phase": new_phase})

async def run_trial(case_text: str, rag_state: tuple, on_event: Optional[Callable[[str, Union[AgentOutput, dict]], None]] = None) -> CaseState:
    """Runs the full multi-agent trial sequence."""
    
    # Unpack RAG state
    store, idf, tfidf_vectors = rag_state
    
    # Initialize state
    state = CaseState(
        case_id="case_001",
        case_text=case_text,
        transcript=[],
        turn_counter=0,
        phase="initialized",
        evidence_store=store,
        idf=idf,
        tfidf_vectors=tfidf_vectors
    )
    
    # a. Judge opens the case
    transition_phase(state, "opening", on_event)
    await execute_agent_turn("judge", state.phase, state, on_event)
    
    # b. Prosecution argues & c. Defense rebuts (Configurable rounds)
    for _ in range(NUM_ARGUMENT_ROUNDS):
        transition_phase(state, "prosecution_argument", on_event)
        await execute_agent_turn("prosecution", state.phase, state, on_event)
        
        transition_phase(state, "defense_rebuttal", on_event)
        await execute_agent_turn("defense", state.phase, state, on_event)
        
    # d. Judge issues ruling + jury instructions
    transition_phase(state, "judge_ruling", on_event)
    await execute_agent_turn("judge", state.phase, state, on_event)
    
    # e. Jury fan-out
    transition_phase(state, "jury_deliberation", on_event)
    
    juror_tasks = []
    
    async def staggered_juror(juror_idx: int) -> AgentOutput:
        # Increased stagger to 5.0s to avoid 429 RESOURCE_EXHAUSTED errors on standard API keys
        await asyncio.sleep(juror_idx * 5.0)
        return await execute_agent_turn(f"juror_{juror_idx}", state.phase, state, on_event)

    for i in range(1, NUM_JURORS + 1):
        juror_tasks.append(staggered_juror(i))
    
    # Run jurors concurrently
    await asyncio.gather(*juror_tasks)
    
    # f. Clerk tally
    transition_phase(state, "verdict_complete", on_event)
    
    # Filter transcript for juror outputs for this case
    juror_outputs = [out for out in state.transcript if out.agent_role.startswith("juror_")]
    
    vote_breakdown = {"guilty": 0, "not_guilty": 0, "undecided": 0}
    dissenting_opinions = []
    all_citations = []
    
    for jo in juror_outputs:
        verdict = jo.verdict if jo.verdict else "undecided"
        if verdict in vote_breakdown:
            vote_breakdown[verdict] += 1
        
        all_citations.extend([c.model_dump() for c in jo.evidence_citations])
        
    # Determine majority verdict
    final_verdict = max(vote_breakdown, key=vote_breakdown.get) # type: ignore
    
    # Detect dissent
    for jo in juror_outputs:
        if jo.verdict != final_verdict:
            dissenting_opinions.append({
                "juror": jo.agent_role,
                "verdict": jo.verdict,
                "reasoning": jo.reasoning
            })
            
    verdict_document = {
        "final_verdict": final_verdict,
        "vote_breakdown": vote_breakdown,
        "dissenting_opinions": dissenting_opinions,
        "all_citations_used": all_citations
    }
    
    state.verdict_document = verdict_document
    
    # Clerk does not output an AgentOutput in the requirements, just assembles the doc.
    # However, to broadcast the final result as an event:
    if on_event:
        on_event("verdict_document_ready", verdict_document)

    return state
