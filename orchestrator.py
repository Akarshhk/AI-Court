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
                    fallback.verdict = "undecided"
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


async def execute_agent_turn(
    role: str,
    phase: str,
    state: CaseState,
    on_event: Optional[Callable[[str, Union[AgentOutput, dict]], None]] = None
) -> AgentOutput:
    """Executes a single agent's turn with retrieval, validation, and retry logic."""
    from prompts_trial import get_system_prompt
    if role in ["judge", "prosecution", "defense"]:
        system_prompt = get_system_prompt(role, phase, state.case_text)
    else:
        system_prompt = f"You are acting as {role} during the {phase} phase. Here is the case text: {state.case_text}"
    
    # 1. Retrieve
    query = f"{role} argument for {phase}"
    chunks = await retrieve(query)
    
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
        
    return output

def transition_phase(state: CaseState, new_phase: str, on_event: Optional[Callable[[str, Union[AgentOutput, dict]], None]] = None):
    """Helper to transition phase and trigger event."""
    state.phase = new_phase
    if on_event:
        on_event("phase_change", {"phase": new_phase})

async def run_trial(case_text: str, on_event: Optional[Callable[[str, Union[AgentOutput, dict]], None]] = None) -> CaseState:
    """Runs the full multi-agent trial sequence."""
    
    # Initialize state
    state = CaseState(
        case_id="case_001",
        case_text=case_text,
        transcript=[],
        turn_counter=0,
        phase="initialized"
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
    for i in range(1, NUM_JURORS + 1):
        juror_tasks.append(
            execute_agent_turn(f"juror_{i}", state.phase, state, on_event)
        )
    
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
