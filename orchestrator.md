## Orchestrator Plan – Match Evaluation Agent

### Scope
- Build the `match-evaluation` agent that scores how well a candidate aligns to a role and company.
- Conform to Coral Protocol agent patterns used by `role-requirements-builder` (LangChain tool-calling agent, Coral SSE tools, strict JSON-only outputs).

### Deliverables
- `agents/match-evaluation/DESIGN.md`: flow, scoring logic, tool usage, error handling.
- `agents/match-evaluation/SCHEMA.md`: Pydantic models and JSON examples for JobSpec, Candidate, Company, ScoreCard.
- `agents/match-evaluation/PROMPT.md`: final system prompt spec with rules and weights.
- `agents/match-evaluation/TESTING.md`: runbook, sample messages, acceptance checks.

### Assumptions
- The orchestrating Interface agent supplies `JobSpec`, `CandidateProfile`, and `CompanyProfile` JSON in the same thread.
- Culture/values alignment is provided by a separate company agent; when absent we degrade gracefully and document missing fields.
- `match-evaluation` has already been registered in `registry.toml`.

### Milestones
1. Planning docs created (this file + four agent docs).
2. Update `main.py` prompt to compute ScoreCard; add local validator tool (like `standardise_spec`).
3. End-to-end dev-mode test via Coral Server; JSON-only output to the sender.
4. Acceptance: stable 0–100 overall score; deterministic on identical input; clear sub-scores and evidence; no hallucinated salary or company facts.

### High-level Flow
1. Receive mention with content:
   - `action: "evaluate_match"`
   - `job_spec: JobSpec`
   - `candidate_profile: CandidateProfile`
   - `company_profile: CompanyProfile` (may include `culture_fit` sub-score)
2. Validate and normalise inputs.
3. Compute sub-scores (skills, experience/seniority, culture/values, domain/industry, logistics: location & salary tolerance).
4. Weight and compose `overall_score` (0–100).
5. Return a JSON `ScoreCard` only, in the same thread.

### Weighting (initial version)
- Skills (must-have emphasis): 45%
- Experience & seniority: 20%
- Culture & values: 20% (supplied by company agent; if missing, cap to 10% with uncertainty penalty)
- Domain/industry familiarity: 10%
- Logistics (location/salary tolerance): 5%

### Runbook (Dev Mode)
```bash
cd /home/adrian/projects/coral/candidate-deep-research/agents/match-evaluation
cp -n .env_sample .env
uv sync
uv run python main.py
```

Troubleshooting (WSL/SSL):
```bash
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
export AWS_CA_BUNDLE=$SSL_CERT_FILE
```

### Definition of Done
- Agent replies with a valid `ScoreCard` JSON (no prose) in the same thread.
- Sub-scores plus concise `reasons` and `missing_data` are included.
- Repeatable scoring on identical inputs.
- No reformatting or non-JSON output; adheres to Coral tool usage.

### Next Actions
- Implement prompt and local validation tool in `match-evaluation/main.py` following `role-requirements-builder` structure.



