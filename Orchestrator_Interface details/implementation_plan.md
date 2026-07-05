# Goal Description
Build the Orchestrator & Integration layer for the "AI Courtroom" multi-agent legal deliberation system. This layer manages the shared state, sequences the trial phases, coordinates parallel jury execution, and implements a citation-validation retry loop, entirely abstracted from the real agent, RAG, and UI implementations via frozen interfaces and mocks.

## User Review Required
The provided specification is highly detailed and explicit about the frozen interface contracts and architectural requirements. No significant architectural decisions need review since the constraints are tightly defined by the hackathon track rules.

## Proposed Changes

### Core Models & Interfaces
#### [NEW] [interfaces.py](file:///c:/Users/Aryan/CS-PROJECTS/AI-Court/interfaces.py)
Define the frozen Pydantic models: `Chunk`, `Citation`, `AgentOutput`, `ValidationResult`, and `CaseState`. Use Pydantic BaseModel as requested for schema consistency.

### Mock Implementations
#### [NEW] [mocks.py](file:///c:/Users/Aryan/CS-PROJECTS/AI-Court/mocks.py)
Implement mock async functions for `run_agent` and `retrieve`, and a synchronous `validate_citations`.
- `retrieve`: Returns dummy chunks.
- `validate_citations`: Fails ~20% of the time to trigger the retry loop.
- `run_agent`: Returns a dummy `AgentOutput` with fake citations.

### Trial Orchestration Engine
#### [NEW] [orchestrator.py](file:///c:/Users/Aryan/CS-PROJECTS/AI-Court/orchestrator.py)
Implement the turn engine sequencing the trial:
1. Initialize `CaseState`.
2. Process phases in order: Judge Opening -> Prosecution -> Defense -> Judge Ruling -> Jury Deliberation -> Verdict Complete.
3. Include the robust retry loop for citations (MAX_CITATION_RETRIES=2) handling `validate_citations` failures, tagging `UNVERIFIED` if exhausted.
4. Implement `asyncio.gather` for independent and concurrent Juror fan-out (NUM_JURORS=5).
5. Implement Clerk tally to assemble the `verdict_document`.
6. Provide an optional `on_event` callback hook to emit events without UI coupling.
7. Wrap agent calls in try/except with a timeout and retry mechanism for resilience.

### Entrypoint & Demo Script
#### [NEW] [main.py](file:///c:/Users/Aryan/CS-PROJECTS/AI-Court/main.py)
A runnable script defining a hardcoded fictional corporate fraud scenario. It instantiates the orchestrator, registers a simple print-based `on_event` callback, and runs the trial end-to-end, producing a formatted terminal transcript.

## Verification Plan

### Manual Verification
- Run `python main.py` and verify zero errors.
- Confirm all 6 phases execute in correct order.
- Verify the presence of at least one visible citation-retry or UNVERIFIED flag in the output.
- Verify 5 independent juror votes with non-identical outputs and potential dissent.
- Confirm the final verdict document contains vote breakdowns and citations.
- Check that the `on_event` callback successfully prints phase transitions and agent turns.
