# roadmap.md — AI Courtroom

## Time estimate

**Optimal completion: ~40–44 working hours of the 48 available**, leaving a 4–8 hour buffer for the things that always go wrong (API rate limits, demo machine issues, last-minute prompt tuning).

Breakdown of effort (these overlap because 4 people work in parallel — this is *not* the calendar time):

| Component | Solo effort | Notes |
|---|---|---|
| Core multi-agent loop (no RAG) | ~24–30 h | The critical path. Must work by hour 24. |
| RAG / vector DB + citation validation | +8–12 h | Layered on top of the working MVP. Cuttable. |
| Frontend transcript UI | ~12–16 h | Runs in parallel from hour 2. |
| Integration, demo prep, pitch | ~8 h | The last stretch. Do not skip. |

With 4 people in parallel, the critical path through the calendar is roughly **40–44 of the 48 hours**, with RAG gated behind a working hour-24 MVP.

## The non-negotiable gate

> **By hour 24, the courtroom must run end-to-end WITHOUT RAG**: ingest case → all agents argue → jury votes → verdict document produced → visible in the UI.

If we hit that gate, everything after is upside. If we don't, we stop adding features and fix the core. RAG only gets wired in *after* this gate is green.


## Milestones

| Milestone | Target hour | Definition of done |
|---|---|---|
| **M0 — Setup locked** | 2 | Repo live, API keys working, schema frozen, stack decisions final, everyone unblocked |
| **M1 — Vertical slice** | 12 | Prosecution + Defense complete one full round end-to-end (no RAG, no jury); frontend skeleton renders a stubbed transcript; RAG ingestion prototype running on the side |
| **M2 — MVP complete (THE GATE)** | 24 | Full agent set: Judge + Defense + Prosecution + 5-juror jury + Clerk tally + verdict doc, all without RAG, visible in UI |
| **M3 — Differentiator live** | 36 | RAG retrieval wired in; citation-validation gate enforcing rejections; the "flip the verdict" demo path working; UI polished |
| **M4 — Demo ready** | 44 | Integration hardened, demo cases prepped, backup run recorded, pitch deck done, dry-run complete |
| **M5 — Buffer / polish** | 48 | Rehearsal, final fixes, submission assets uploaded |

## Priority order (what to cut, in order, if we fall behind)

Cut from the bottom up — never cut from the top:

1. **(Never cut)** 3+ distinct agents producing a unified verdict — this *is* the track requirement.
2. **(Never cut)** Jury disagreement surfaced in the output.
3. **(Protect hard)** Citation-validation gate — this is the "verifiable" proof.
4. RAG retrieval — degrade to feeding full case text into each agent's context instead of retrieving. Still works, just less scalable. The pitch survives.
5. The "flip the verdict" demo path — nice-to-have.
6. Juror personality dials in the UI — cosmetic.
7. Multiple case presets — one solid demo case is enough.

## Demo asset checklist

- [ ] One bulletproof demo case (fact-rich, outcome-contested, **not** politically charged — a fictional corporate fraud or IP-theft scenario is safest)
- [ ] A second case with one key fact removable, to show the verdict flipping
- [ ] A fabricated-claim test to show the Judge rejecting an uncited argument
- [ ] Clean recorded backup run of the full flow
- [ ] Pitch deck leading with the *verifiable artifact*, not the architecture diagram
- [ ] Local fallback path if live APIs throttle on stage
