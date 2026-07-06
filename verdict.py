from interfaces import CaseState

def build_verdict_document(state: CaseState) -> dict:
    """
    Builds a polished verdict document from the CaseState.
    Addresses full transcript citations, explicit hung juries, and failed jurors.
    """
    vote_breakdown = {"guilty": 0, "not_guilty": 0}
    dissenting_opinions = []
    failed_jurors = []
    all_citations_used = []
    
    # 1. Collect all citations from the entire transcript (judge, prosecution, defense, jurors)
    for turn in state.transcript:
        for citation in turn.evidence_citations:
            all_citations_used.append(citation.model_dump())
            
    # 2. Tally votes and identify failed jurors
    juror_outputs = [out for out in state.transcript if out.agent_role.startswith("juror_")]
    
    for jo in juror_outputs:
        if getattr(jo, "is_failed", False):
            failed_jurors.append({
                "juror": jo.agent_role,
                "reasoning": jo.reasoning or "Failed to deliberate."
            })
            continue  # Do not include failed jurors in the normal vote breakdown or dissent list
            
        if jo.verdict in vote_breakdown:
            vote_breakdown[jo.verdict] += 1
        
    # 3. Determine majority verdict or hung jury
    max_votes = max(vote_breakdown.values())
    
    if max_votes == 0:
        final_verdict = "failed_deliberation"
    else:
        top_verdicts = [v for v, count in vote_breakdown.items() if count == max_votes]
        # Detect explicit hung jury
        if len(top_verdicts) > 1:
            final_verdict = "hung_jury"
        else:
            final_verdict = top_verdicts[0]
            
    # 4. Record dissenting opinions
    # Only record dissent if a clear final verdict was reached
    if final_verdict not in ["hung_jury", "failed_deliberation"]:
        for jo in juror_outputs:
            if getattr(jo, "is_failed", False):
                continue
            if jo.verdict in vote_breakdown and jo.verdict != final_verdict:
                dissenting_opinions.append({
                    "juror": jo.agent_role,
                    "verdict": jo.verdict,
                    "reasoning": jo.reasoning
                })
                
    return {
        "final_verdict": final_verdict,
        "vote_breakdown": vote_breakdown,
        "dissenting_opinions": dissenting_opinions,
        "failed_jurors": failed_jurors,
        "all_citations_used": all_citations_used
    }
