# context.md — AI Courtroom Multi-Agent System

## What we are building

An adversarial, multi-agent legal deliberation system. A case (a brief, a news article, or a user-submitted scenario) is fed in, and a network of specialized AI agents plays out the full courtroom process — argument, rebuttal, ruling, jury deliberation — and produces a **structured, evidence-tagged verdict** where every claim is traceable back to a real source in the case material.

**Hackathon track:** Track 2 — Multi-Agent Collaboration Systems.

**The one-line pitch:**
> Every existing AI legal tool is a single model giving one answer. We built the adversarial *process* — because courts work not because judges are smart, but because the system forces every claim to survive a counter-argument before it becomes a verdict.

## Why this wins Track 2

Track 2 is scored on whether **3+ distinct agents collaborate to produce a unified, verifiable outcome**. This design hits all three words deliberately:

- **Distinct:** Prosecution, Defense, Judge, and a 3–5 member Jury each have genuinely different goals and reasoning profiles. They are not the same prompt with different names.
- **Collaborate / self-coordinate:** A fixed procedural turn order (Judge → Prosecution → Defense → ruling → Jury → tally) creates real interaction. Agents respond to each other's actual output, not to a script.
- **Verifiable:** This is our differentiator. Every argument must cite a real source chunk. The Judge agent *rejects* any claim without a valid citation. The verdict document is the artifact, and every line in it is clickable back to its evidence. We can prove this live by trying to inject a false claim and watching the system reject it.

The **jury disagreement** is a feature, not a bug — a 4-1 split with a surfaced dissent is an outcome no single agent could produce, which is exactly what the rubric is asking for.

## The agents

| Agent | Role | Responsibility |
|---|---|---|
| **Judge** | Procedural authority | Sets charges, rules arguments admissible/inadmissible, enforces the evidence-citation rule, issues jury instructions |
| **Prosecution** | Argue guilt / liability | Builds the strongest case *against* the subject, citing evidence |
| **Defense** | Argue innocence | Rebuts every prosecution claim with counter-evidence |
| **Jury (3–5 sub-agents)** | Independent deliberation | Each juror has a distinct profile (skeptic / empath / by-the-book / etc.), reasons and votes independently |
| **Clerk** | Orchestrator + recorder | Manages turn order, validates citations, tallies votes, assembles the final verdict document |

## The RAG / Vector DB layer

RAG is what turns "agents that argue plausibly" into "agents whose every claim is grounded in the actual case." It exists to serve **verifiability**, which is the scored property.

How it works:
1. The case document(s) are chunked and embedded into a vector store at ingestion.
2. Before any agent argues, it retrieves the most relevant chunks for the point it wants to make.
3. Every citation in an agent's output references a real `chunk_id`.
4. The Clerk/Judge **validates** that the cited chunk exists *and* that the quoted text actually appears in it. Citations that fail validation cause the argument to be rejected and retried.

That last step is the whole game. It's the difference between "the AI said it had evidence" and "the system verified the evidence exists." This validation gate is our headline feature in the pitch.

> **Risk note:** RAG is the highest-risk component in a 48-hour window. The plan (see `phases.md`) requires a fully working courtroom **without** RAG by hour 24. RAG is layered on top of a working MVP, never underneath it. If retrieval misbehaves on demo day, we fall back to the non-RAG path and still have a complete, demoable system.

## Inter-agent communication schema

All agents return structured JSON (enforced via tool-use / structured output, not by asking politely in prose). Shared schema:

```json
{
  "agent_role": "prosecution",
  "turn": 3,
  "statement": "The defendant authorized the wire transfer on the disputed date.",
  "evidence_citations": [
    {
      "chunk_id": "case_chunk_017",
      "quote": "Wire transfer of $40,000 authorized by J. Doe on March 3.",
      "relevance": "Directly establishes the defendant initiated the transfer."
    }
  ],
  "confidence": 0.82
}
```

Jury agents add a `verdict` field (`guilty` / `not_guilty` / `undecided`) and a `reasoning` field. The Clerk consumes all of these to build the verdict document and the vote tally.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Agent reasoning | Anthropic API | Strong reasoning, native tool-use for structured output |
| Orchestration | **Custom Python orchestrator** (no framework) | Our flow is a fixed turn order with one fan-out step; raw orchestration is ~200–300 lines and keeps every hour on our differentiator rather than framework plumbing. (LangGraph/CrewAI/n8n all add learning-curve risk for less gain here.) |
| Backend / API | FastAPI | Async, plays well with the Python RAG ecosystem, easy SSE/WebSocket |
| Vector DB | **Chroma** (embedded, zero infra) — fallback to Qdrant if we need a server | Local, no setup cost, fast to integrate in a hackathon |
| Embeddings | Voyage AI *or* sentence-transformers (local) | Voyage for quality; local model as a zero-dependency fallback |
| Streaming to UI | SSE or WebSocket | Lets the transcript stream in live — our best demo visual |
| Frontend | React + Tailwind | Courtroom transcript UI with per-agent role badges |

## Scope: in vs out

**In scope (MVP):** ingest a case, run the full agent loop, enforce citation validation, produce a verdict document with vote tally and dissents, stream it to a live transcript UI.

**Stretch (only if MVP is solid):** RAG retrieval tuning, the "remove one fact and watch the verdict flip" demo path, juror personality dials in the UI, multiple case presets.

**Explicitly out:** real legal advice, real case law databases, anything politically charged as a demo case, authentication, persistence beyond a session, multi-case history.

## Demo strategy

Two scored moments, engineered deliberately:
1. **"It's live"** — the transcript streams in agent by agent, jury splits visibly.
2. **"Here's the proof it's correct"** — try to feed a fabricated claim and show the Judge reject it; OR remove one key piece of evidence and re-run to show the verdict flip.

Always record a clean backup run. Never let a live API hiccup decide the outcome.
