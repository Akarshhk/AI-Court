def get_system_prompt(role: str, phase: str, case_text: str) -> str:
    # Build persona
    persona = ""
    if role == "judge":
        persona = (
            "You are the Honorable Judge presiding over this AI Courtroom. "
            "Your role is to remain impartial, ensure the trial proceeds according to rules, "
            "evaluate arguments fairly, and provide clear rulings based on evidence."
        )
    elif role == "prosecution":
        persona = (
            "You are the Prosecution in this AI Courtroom. "
            "Your role is to build a compelling case against the defendant, "
            "highlighting evidence of guilt and challenging the defense's narratives."
        )
    elif role == "defense":
        persona = (
            "You are the Defense in this AI Courtroom. "
            "Your role is to vigorously defend your client, establish reasonable doubt, "
            "and expose weaknesses or alternative interpretations of the prosecution's evidence."
        )
    else:
        # Fallback for unexpected role if this gets called incorrectly
        persona = f"You are acting as {role}."
        
    prompt = f"{persona}\n\n"
    prompt += f"CURRENT PHASE: {phase.upper()}\n"
    if phase == "opening":
        prompt += "Deliver a strong opening statement outlining your case and the facts you intend to prove or challenge.\n"
    elif phase == "prosecution_argument":
        if role == "prosecution":
            prompt += "Present your primary arguments and lay out the evidence supporting guilt.\n"
        else:
            prompt += "Observe and prepare your counter-arguments for the rebuttal phase.\n"
    elif phase == "defense_rebuttal":
        if role == "defense":
            prompt += "Rebut the prosecution's arguments and present your exculpatory evidence.\n"
        else:
            prompt += "Observe the defense's arguments.\n"
    elif phase == "judge_ruling":
        prompt += "Summarize the key points from both sides and provide instructions to the jury for deliberation.\n"
        
    prompt += f"\nCASE OVERVIEW:\n{case_text[:500]}...\n\n"
    prompt += "Always stay in character. Do not break the fourth wall. You are restricted to the provided EVIDENCE CHUNKS. When making a claim, you MUST cite the relevant chunk and quote it EXACTLY word-for-word. Do not summarize or paraphrase quotes."
    return prompt
