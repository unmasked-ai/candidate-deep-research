## Schemas – Inputs and Output

### JobSpec (reference)
Provided by `role-requirements-builder`. Fields include `role_title`, `seniority`, `tech_stack`, `must_have_hard_skills`, `nice_to_have_hard_skills`, `experience_requirements`, `location`, `salary_range`, `industry`, `domain_knowledge`, etc.

### CandidateProfile (v1)
```json
{
  "name": "string",
  "years_experience": 0,
  "current_title": "string",
  "skills": ["python", "postgres", "docker"],
  "certifications": ["aws-sa"],
  "education": ["BSc Computer Science"],
  "roles_history": ["Senior Software Engineer at X"],
  "locations": { "type": "remote|hybrid|onsite", "cities": ["London"] },
  "salary_expectation": { "currency": "GBP", "min": 0, "max": 0, "period": "year" },
  "industry_experience": ["fintech", "saas"]
}
```

### CompanyProfile (v1)
```json
{
  "name": "string",
  "industry": "string",
  "locations": ["London", "Remote-UK"],
  "culture_values": ["ownership", "craft", "customer-obsession"],
  "tech_stack": ["python", "postgres"],
  "salary_benchmarks": { "currency": "GBP", "min": 0, "max": 0, "period": "year" },
  "culture_fit": { "score": 0, "notes": ["..."] }
}
```

### ScoreCard (output)
```json
{
  "overall_score": 0,
  "sub_scores": {
    "skills": 0,
    "experience": 0,
    "culture": 0,
    "domain": 0,
    "logistics": 0
  },
  "decision": "proceed|maybe|reject",
  "justification": "Concise explanation of the score in 100 words or less",
  "reasons": ["short, atomic reasons"],
  "missing_data": ["list any missing inputs"],
  "evidence": [
    { "source": "candidate|job|company", "quote": "text", "field": "skills|experience|culture|..." }
  ]
}
```

### Notes
- All scores are integers 0–100.
- Normalise tech names (e.g., "postgresql" → "postgres").
- Never infer salary; when unknown leave null in inputs and reflect impact in `reasons` and `missing_data`.



