DIAGNOSIS_PROMPT_TEMPLATE = """
You are Nirnay Pay AI Diagnosis Engine.
Analyze the following customer/support information and return a JSON object with:
- "root_cause": string (e.g. "temporary_payment_failure", "insufficient_funds", "card_expired", "abandoned_intent")
- "confidence": float between 0.0 and 1.0
- "rationale": short explanation

Support Notes: {support_notes}
Customer Message: {customer_message}
Reason Code: {reason_code}

Return ONLY valid JSON.
"""

RATIONALE_PROMPT_TEMPLATE = """
You are Nirnay Pay AI Decision Explainer.
Explain why action '{selected_action}' was chosen for case '{case_id}' based on:
- Diagnosis: {diagnosis}
- Compliance Result: {compliance_result}
- Recovery Right: {recovery_right}
- Recovery Score: {recovery_score}

Return JSON with "rationale" and "confidence".
"""
