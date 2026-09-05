# Nirnay Recovery Communication & Explanation Agent

An **explanation and communication layer only**. It takes an
already-approved recovery decision (produced elsewhere, by the decision
engine, compliance engine, recovery-rights engine, RecoveryScore engine)
and turns it into clear, safe, policy-compliant human communication.

It answers: **"How do we explain the approved recovery decision
clearly?"** It never answers: **"What recovery action should we
take?"**

This repo contains **only the agent**. No frontend, backend/API server,
database, payment integration, recovery execution, compliance engine,
recovery-rights engine, RecoveryScore engine, decision engine, UI, or
auth system is included, by design.

## Install / run

Zero mandatory third-party dependencies (standard library only). An
optional real LLM provider (`nirnay_agent/llm/anthropic_provider.py`)
needs the `anthropic` package + `ANTHROPIC_API_KEY`, but is not required
to use or test the agent.

```bash
python -m unittest discover -s tests -v   # run the full test suite (LLM mocked)
python examples/example_usage.py          # end-to-end example
```

## Programmatic interface

```python
from nirnay_agent import NirnayCommunicationAgent, MockCommunicationModel

agent = NirnayCommunicationAgent(llm=MockCommunicationModel())

result = agent.generate({
    "recovery_case_id": "CASE-88213",
    "scenario_type": "CARD_DECLINE",
    "customer_segment": "loyal",
    "amount_at_risk": 1499.0,
    "currency": "INR",
    "diagnosis": "insufficient_funds_temporary",
    "diagnosis_confidence": 0.86,
    "recovery_rights": {"allowed": True},
    "compliance_result": {"status": "APPROVED"},
    "allowed_actions": ["RETRY", "GRACE_PERIOD", "REMINDER"],
    "selected_action": "GRACE_PERIOD",
    "recovery_score": 0.74,
    "decision_mode": "RULE",
    "decision_rationale": "Strong payment history; loyal segment.",
    "recovery_outcome": None,
    "requested_language": "en",
    "requested_tone": "FRIENDLY",
    "communication_purpose": "CUSTOMER_RECOVERY_MESSAGE",
})
```

`agent.generate(...)` is synchronous and returns a plain JSON-serializable
`dict`. Wrapping it in `async def` at the call site (e.g.
`await asyncio.to_thread(agent.generate, payload)`) does not change the
output contract, satisfying the "sync or async" requirement without
duplicating logic.

To go live, swap the provider:

```python
from nirnay_agent.llm.anthropic_provider import AnthropicCommunicationModel
agent = NirnayCommunicationAgent(llm=AnthropicCommunicationModel())
```

No other code changes are required -- the agent only talks to the
provider-independent `CommunicationModel` interface.

## Architecture

```
nirnay_agent/
  agent.py            NirnayCommunicationAgent -- orchestration/pipeline
  models.py            RecoveryCaseInput, CommunicationResult
  enums.py              SelectedAction, CommunicationPurpose, Tone, ...
  validation.py         structural + decision-lock consistency checks
  safety.py             deterministic post-generation safety layer (8 checks)
  templates.py          deterministic fallback templates, per action
  telemetry.py           structured, PII-free observability
  exceptions.py          InputValidationError, DecisionConsistencyError,
                          IncompleteContextError
  llm/
    base.py              CommunicationModel abstract interface
    mock_provider.py      deterministic test double (used by the test suite)
    anthropic_provider.py optional live provider (not used in tests)
tests/
  test_agent.py           25 automated tests, LLM always mocked
examples/
  example_usage.py        end-to-end example
```

### Pipeline (`agent.generate`)

1. **Structural validation** (`validation.validate_input`) -- rejects
   unsupported `scenario_type`, negative amounts, malformed decline
   codes, impossible counts, wrong types, unknown `selected_action`,
   etc. Raises `InputValidationError`. Never repairs/guesses bad data.
2. **Decision-lock consistency** (`validation.validate_decision_lock`)
   -- refuses to communicate a self-contradictory decision (e.g.
   `compliance_result.status == "BLOCKED"` paired with an active-
   recovery `selected_action`). Raises `DecisionConsistencyError`.
3. **Required-context check** -- if a field required for the requested
   `communication_purpose` is missing, raises `IncompleteContextError`
   rather than inventing it.
4. **LLM call** through the provider-independent `CommunicationModel`
   interface, using a `GenerationRequest` built ONLY from fields
   actually present on the validated input.
5. **Deterministic safety layer** (`safety.run_safety_checks`) checks
   the generated text for: action mismatch, contradiction of
   compliance/the decision, unsubstantiated recovery/compliance claims,
   hallucinated amounts, invented deadlines, threatening/manipulative
   language, and sensitive-data exposure.
6. **One retry** with explicit correction notes if the safety layer
   fails.
7. **Deterministic fallback template** (`templates.py`) if the retry
   also fails, or the LLM times out / errors / returns a malformed
   shape. The core workflow always completes.
8. **Structured telemetry** (`telemetry.Telemetry`) is recorded for
   every call (latency, retry count, validation status, fallback flag,
   failure reason) without logging sensitive message content.
9. Returns a strictly-shaped `dict` matching one of the three output
   types below.

### Output types

- `DECISION_EXPLANATION` -- `{summary, reason, business_context, constraints[]}`
- `CUSTOMER_RECOVERY_MESSAGE` -- `{message, tone, language, action_reference}`
- `MERCHANT_EXPLANATION` -- `{summary, why_this_action, expected_business_intent, compliance_context}`

Every result also includes a `type` field and a `_meta` block
(`request_id`, `fallback_used`, `language_fallback`).

### What the agent guarantees

- `selected_action` is never changed, reinterpreted, or second-guessed.
- `compliance_result` and `recovery_rights` are treated as immutable,
  authoritative upstream facts.
- No financial facts, dates, deadlines, penalties, or legal
  consequences are ever invented -- only facts present on the input are
  used.
- A `BLOCKED`/`STOP` decision is never communicated as "recovery in
  progress."
- Recovery/compliance success is never claimed unless the input
  explicitly says so (`recovery_outcome.status == "SUCCESS"`,
  `compliance_result.status == "APPROVED"`, etc.).
- Threatening, urgent, or manipulative language is rejected by the
  safety layer and cannot reach the caller.
- An unsupported `requested_language` falls back to English with
  `language_fallback: true` -- languages are never silently mixed.
- LLM failure (timeout, error, malformed/contradictory output) never
  crashes the caller -- a safe deterministic template is always
  returned instead.
- Unknown/invalid input (bad `scenario_type`, negative amounts,
  malformed decline codes, impossible counts, unknown
  `selected_action`, etc.) is rejected with a structured error, never
  guessed at.

### Note on section "2A / 2B" naming

The spec's sections 2A/2B reference a `RevenueDiagnosisAgent` /
`DiagnosisResult` interface (with `root_cause`, `diagnosis_mode`, etc.).
That is the output contract of a *different*, upstream diagnosis agent
that this agent explicitly does not implement (this agent only
explains/communicates an already-approved decision, per section 3). The
input-validation *rules* described in 2B (reject unsupported
`scenario_type`, negative amounts, malformed decline codes, impossible
payment counts, invalid types) have been applied here to this agent's
own `RecoveryCaseInput`, and the `diagnosis_mode` vocabulary
(`RULE | AI | FALLBACK`) is available in `enums.DiagnosisMode` purely
for schema compatibility if an upstream `diagnosis_mode` value is
echoed through.
