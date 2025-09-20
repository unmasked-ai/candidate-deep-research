## Testing & Runbook

### Dev Mode
```bash
cd /home/adrian/projects/coral/candidate-deep-research/agents/match-evaluation
cp -n .env_sample .env
uv sync
uv run python main.py
```

If you hit SSL errors in WSL, export:
```bash
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
export AWS_CA_BUNDLE=$SSL_CERT_FILE
```

### Sample Mention Content
Send from Interface agent in the SAME thread:
```json
{
  "action": "evaluate_match",
  "job_spec": { "role_title": "Senior Python Engineer", "tech_stack": ["python", "postgres"], "must_have_hard_skills": ["python", "postgres"], "nice_to_have_hard_skills": ["docker"], "experience_requirements": {"years_min": 4}, "industry": "fintech" },
  "candidate_profile": { "name": "Alex", "years_experience": 6, "skills": ["python", "postgres", "docker"], "industry_experience": ["fintech"], "locations": {"type": "remote", "cities": ["London"]} },
  "company_profile": { "name": "Acme", "industry": "fintech", "culture_values": ["ownership", "craft"], "culture_fit": {"score": 72} }
}
```

### Acceptance Checks
- Response is a single `ScoreCard` JSON; no prose.
- Sub-scores present and each within 0–100; `overall_score` within 0–100.
- Decision band matches thresholds: proceed ≥ 75, maybe 50–74, reject < 50.
- Contains `justification` field with explanation in 100 words or less.
- Contains concise `reasons` and any `missing_data` when inputs are incomplete.



