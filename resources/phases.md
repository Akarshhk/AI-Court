 phases.md — AI Courtroom: Phased Execution Plan

48-hour hackathon, 4 developers. Hour bands are guidance, not handcuffs — but **M2 at hour 24 is a hard gate** (see roadmap.md).

Legend: **D1** = Backend Lead, **D2** = RAG/Data, **D3** = Frontend, **D4** = Prompts/Integration/Demo.

---

## Phase 0 — Setup & Freeze (Hours 0–2)

Goal: nobody is blocked after this phase.

- **All:** Confirm the design from `context.md`. Lock the agent list and turn order.
- **D1 + D2:** Agree and **freeze the inter-agent JSON schema**. Write it down in the repo. This is the contract everyone builds against.
- **D1:** Scaffold the repo — backend folder, orchestrator stub, env/secrets handling, API key working with one test call.
- **D2:** Spin up Chroma locally, confirm you can embed and retrieve a dummy document. Pick the embedding model now.
- **D3:** Frontend scaffold (React + Tailwind), a hardcoded transcript view rendering 2–3 fake agent messages with role badges.
- **D4:** Draft v1 system prompts for Prosecution and Defense. Find/write the first demo case (a fictional corporate fraud scenario).

**Done when:** schema is frozen, everyone has a running local environment, and one real API call returns structured JSON.

---

## Phase 1 — Vertical Slice (Hours 2–12)

Goal: prove the core loop works on the thinnest possible path. **No RAG yet. No jury yet.**

- **D1:** Build the `CaseState` object (case text, transcript log, turn counter) and the core `run_agent()` function: takes a role + system prompt + current transcript, calls the API with tool-use to force the JSON schema, validates the shape, appends to the transcript. Get **Prosecution → Defense, one round each**, running end-to-end and printing valid JSON.
- **D2:** Build the ingestion pipeline — chunk the case doc, embed, store in Chroma. Build and unit-test a `retrieve(query, k)` function. (Not wired into agents yet — runs standalone.)
- **D3:** Replace fake data with a live connection to the backend. Get the transcript to render whatever the backend produces. Stand up the streaming channel (SSE or WebSocket) even if it just streams the stubbed output for now.
- **D4:** Iterate Prosecution/Defense prompts using D1's loop. Start the Judge prompt (charges + admissibility rules). Refine the demo case so it has clear, citable facts.

**Done when (M1):** Prosecution and Defense complete a full round end-to-end, the frontend shows it, and RAG retrieval works in isolation.

---

## Phase 2 — Full Courtroom MVP (Hours 12–24) — THE GATE

Goal: the complete multi-agent system, still **without RAG**. This is the submission floor — if everything after this breaks, we can still demo this.

- **D1:** Add the **Judge** to the loop (opens the case, rules on each argument, issues jury instructions). Build the **jury fan-out**: fire 3–5 parallel API calls, each with a different juror personality prompt, each returning an independent verdict + reasoning. Build the **Clerk tally** (count votes, detect splits/dissents).
- **D2:** Stay one step ahead — prepare the retrieval-injection point so that in Phase 3, agents can call `retrieve()` before arguing with minimal rewiring. Begin a simple citation-validation function (does the cited chunk exist? does the quote appear in it?).
- **D3:** Build the **jury panel view** (individual juror votes + reasoning) and the **verdict view** (final tally, dissents surfaced). Make the live streaming smooth — agents should appear one after another.
- **D4:** Build the **verdict document generator** (the Clerk's final artifact: charges, key arguments, vote breakdown, dissents, each tied to its citations). Pin down the exact demo flow.

**Done when (M2 — HARD GATE):** Feed in the case → Judge → Prosecution → Defense → ruling → 5 jurors vote independently → Clerk tallies → verdict document appears in the UI, with a visible jury split. All without RAG.

> If this gate slips, **stop adding features**. Fix the core until it's green before touching anything below.

---

## Phase 3 — The Differentiator (Hours 24–36)

Goal: turn "plausible arguments" into "verified, grounded arguments." This is where the win lives.

- **D2:** Wire `retrieve()` into the agent loop — each agent retrieves relevant chunks before arguing. Finish the **citation-validation gate**: an argument whose citations don't resolve to real chunks (or whose quotes don't match) is **rejected and retried**. This is the headline feature.
- **D1:** Add the rejection/retry loop in the orchestrator. Make the Judge agent the one that enforces validation, so the rejection is *in character* ("Objection sustained — counsel cited evidence not in the record").
- **D3:** Surface citations in the UI — each argument's claims link to the source chunk. Add a visible "rejected argument" indicator when the Judge throws one out. Polish the whole transcript experience.
- **D4:** Build the **two killer demo paths**: (a) inject a fabricated claim → Judge rejects it; (b) remove one key fact and re-run → verdict flips. Tune juror prompts so disagreement is realistic, not random.

**Done when (M3):** RAG is live, the validation gate provably rejects bad citations, and at least one "wow" demo path works on demand.

---

## Phase 4 — Harden & Prep Demo (Hours 36–44)

Goal: make it survive contact with a live audience.

- **D1:** Add timeouts, retries, and graceful failure on every API call. Build the **local fallback path** (full case text in context instead of retrieval) in case RAG misbehaves on stage.
- **D2:** Stress-test retrieval on the actual demo case. Make sure chunk boundaries don't split key facts in half. Tune `k` and chunk size for accuracy.
- **D3:** Final UI polish — make it look like a courtroom, not a debug console. Mobile/projector-friendly sizing.
- **D4:** Record a **clean backup video** of the full flow. Build the pitch deck (lead with the verdict artifact and the rejected-claim moment, not the architecture). Run a full dry-run with the team.

**Done when (M4):** Everything is hardened, a backup run is recorded, and the team has done at least one clean dry-run end to end.

---

## Phase 5 — Buffer & Submit (Hours 44–48)

Goal: breathe, fix the last things, submit.

- **All:** Final rehearsal of the live demo + pitch.
- Fix only what's broken — resist new features.
- Upload submission assets (repo, video, deck, write-up).
- Make sure the README explains the **3+ distinct agents** and the **verifiable outcome** in the first paragraph — that's what judges scan for against the Track 2 rubric.

---

## Parallelization summary

The build is designed so the four workstreams rarely block each other:

- **D1's loop** is the backbone — D4 tunes prompts against it, D3 renders its output, D2 plugs into it.
- **D2's RAG** is built standalone first and only injected at Phase 3, so a RAG problem never blocks the MVP.
- **D3's frontend** builds against the frozen schema with stubbed data from hour 2, so it's never waiting on the backend.
- **D4 floats** — prompts early, verdict generator mid, demo/pitch late — filling whatever is on the critical path.

The single most important discipline: **freeze the schema in Phase 0 and protect the hour-24 gate.** Everything else is recoverable.
