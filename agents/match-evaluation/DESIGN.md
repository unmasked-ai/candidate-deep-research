## Match Evaluation – Design

### Overview
The `match-evaluation` agent receives normalised inputs and returns a single `ScoreCard` JSON describing the alignment between a candidate, a role (`JobSpec`), and a company. It follows the same LangChain + Coral tools pattern as `role-requirements-builder`.

### Inputs
- **JobSpec**: output from `role-requirements-builder`.
- **CandidateProfile**: skills, experience, roles, education, locations, salary expectations.
- **CompanyProfile**: industry/domain, culture/values, locations; may include a `culture_fit` object derived by the Company Research/Match agent.

All three are provided by the orchestrating Interface agent in the same thread mention:
```json
{
  "action": "evaluate_match",
  "job_spec": { /* JobSpec */ },
  "candidate_profile": { /* CandidateProfile */ },
  "company_profile": { /* CompanyProfile (may include culture_fit) */ }
}
```

### Output
- **ScoreCard** JSON only. No prose.

### Flow
1. Validate presence of `job_spec` and `candidate_profile`; accept optional `company_profile`.
2. Normalise lists (dedupe, lower-case tech names, trim whitespace).
3. Compute sub-scores:
   - Skills match (must-have vs nice-to-have, normalised tech names).
   - Experience & seniority alignment.
   - Culture & values (uses `company_profile.culture_fit` if present; otherwise estimate from inputs with uncertainty penalty and note in `missing_data`).
   - Domain/industry familiarity.
   - Logistics: location feasibility and salary tolerance checks.
4. Weighted composition to `overall_score` (0–100).
5. Build concise `reasons` and `evidence` from the inputs; include `missing_data` list when fields are absent.
6. Reply to the original sender (same thread) with the `ScoreCard` JSON only.

### Weights (v1)
- Skills: 45%
- Experience & seniority: 20%
- Culture & values: 20% (capped to 10% if no explicit culture signal provided)
- Domain/industry: 10%
- Logistics (location/salary): 5%

### Decision Bands
- `proceed` ≥ 75
- `maybe` 50–74
- `reject` < 50

### Error Handling
- If inputs are malformed or critical fields are missing, respond with:
```json
{ "error": "validation_failed", "details": "..." }
```
- Never invent salary or culture facts; when unknown, leave null and record in `missing_data`.

### Coral Tools Usage
- Uses the Coral SSE tools exposed by the server (`send_message`, `wait_for_mentions`, etc.).
- This agent does not crawl or call external MCP servers; it works with provided JSON. If culture evaluation is delegated, the orchestrator should include that result in `company_profile`.

### Implementation Parity with `role-requirements-builder`
- Same runtime wrapper (`run_agent.sh`), environment loading, and agent loop via `AgentExecutor`.
- Introduce a local Structured Tool `standardise_scorecard` mirroring the validation approach used by `standardise_spec` in the builder agent.



