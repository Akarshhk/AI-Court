CASE_FACTS = [
    "OmniCorp Industries is a publicly traded logistics software company.",
    "On October 12, 2023, OmniCorp announced a $50 million quarterly loss.",
    "CEO Marcus Thorne sold 500,000 shares of OmniCorp stock on October 10, 2023.",
    "The October 10 stock sale yielded Marcus Thorne $15 million.",
    "An internal email from CFO Sarah Jenkins to Marcus Thorne was sent on October 8, 2023.",
    "The October 8 email stated: 'The Q3 numbers are finalized and they are disastrous.'",
    "Marcus Thorne claims he never read the October 8 email before selling his stock.",
    "IT records show the October 8 email was marked as 'read' on Marcus Thorne's device at 9:15 AM on October 9.",
    "Marcus Thorne's defense argues his executive assistant manages his inbox and frequently marks emails as read.",
    "A pre-scheduled trading plan (10b5-1) was filed by Marcus Thorne in January 2023.",
    "The 10b5-1 trading plan explicitly mandated the sale of 500,000 shares on October 10, 2023.",
    "The prosecution alleges Marcus Thorne instructed the accounting team to delay the Q3 loss announcement until after his stock sale.",
    "Accounting logs show the Q3 report was finalized on October 8 but not published until October 12."
]

def get_case_text(omit_fact_idx: int = None) -> str:
    facts = CASE_FACTS.copy()
    if omit_fact_idx is not None and 0 <= omit_fact_idx < len(facts):
        facts.pop(omit_fact_idx)
    return "\n\n".join(facts)
