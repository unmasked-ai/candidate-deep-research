import urllib.parse
from dotenv import load_dotenv
import os, json, asyncio, traceback
from typing import Optional, List
from pydantic import BaseModel, Field, ValidationError
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import StructuredTool

# ---------- Match Evaluation Schemas ----------
class SalaryRange(BaseModel):
    currency: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    period: Optional[str] = Field(default="year", description="year or month")

class Location(BaseModel):
    type: Optional[str] = Field(default=None, description="onsite|hybrid|remote")
    cities: Optional[List[str]] = None

class ExperienceReq(BaseModel):
    years_min: Optional[float] = None
    years_pref: Optional[float] = None

class Evidence(BaseModel):
    source: str = Field(description="candidate|job|company")
    quote: str
    field: str

class JobSpec(BaseModel):
    role_title: str
    seniority: Optional[str] = "unspecified"
    employment_type: Optional[str] = None
    salary_range: Optional[SalaryRange] = None
    location: Optional[Location] = None
    tech_stack: List[str] = []
    must_have_hard_skills: List[str] = []
    nice_to_have_hard_skills: List[str] = []
    soft_skills: List[str] = []
    industry: Optional[str] = None
    domain_knowledge: List[str] = []
    culture_requirements: List[str] = []
    responsibilities: List[str] = []
    education_requirements: List[str] = []
    experience_requirements: Optional[ExperienceReq] = None
    keywords: List[str] = []
    benefits: List[str] = []
    screening_questions: List[str] = []
    extracted_evidence: List[Evidence] = []

class CandidateProfile(BaseModel):
    name: str
    years_experience: float = 0
    current_title: Optional[str] = None
    skills: List[str] = []
    certifications: List[str] = []
    education: List[str] = []
    roles_history: List[str] = []
    locations: Optional[Location] = None
    salary_expectation: Optional[SalaryRange] = None
    industry_experience: List[str] = []

class CultureFit(BaseModel):
    score: int = Field(ge=0, le=100)
    notes: List[str] = []

class CompanyProfile(BaseModel):
    name: str
    industry: Optional[str] = None
    locations: List[str] = []
    culture_values: List[str] = []
    tech_stack: List[str] = []
    salary_benchmarks: Optional[SalaryRange] = None
    culture_fit: Optional[CultureFit] = None

class SubScores(BaseModel):
    skills: int = Field(ge=0, le=100)
    experience: int = Field(ge=0, le=100)
    culture: int = Field(ge=0, le=100)
    domain: int = Field(ge=0, le=100)
    logistics: int = Field(ge=0, le=100)

class ScoreCard(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    sub_scores: SubScores
    decision: str = Field(pattern="^(proceed|maybe|reject)$")
    justification: str = Field(description="Concise explanation of the score in 100 words or less")
    reasons: List[str] = []
    missing_data: List[str] = []
    evidence: List[Evidence] = []

class MatchEvaluationInput(BaseModel):
    job_spec: dict = Field(description="JobSpec from role-requirements-builder")
    candidate_profile: dict = Field(description="Candidate information and skills")
    company_profile: Optional[dict] = Field(default=None, description="Company culture and context")
    company_details: Optional[List[dict]] = Field(default=None, description="List of company details (alternative to company_profile)")

def _dedupe(xs: Optional[List[str]]) -> List[str]:
    if not xs: return []
    return list(dict.fromkeys([x.strip().lower() for x in xs if x and x.strip()]))

def _normalize_tech(tech_list: List[str]) -> List[str]:
    """Normalize technology names for better matching"""
    normalization_map = {
        "postgresql": "postgres",
        "javascript": "js",
        "typescript": "ts",
        "node.js": "nodejs",
        "react.js": "react",
        "vue.js": "vue"
    }
    normalized = []
    for tech in tech_list:
        tech_lower = tech.lower().strip()
        normalized.append(normalization_map.get(tech_lower, tech_lower))
    return _dedupe(normalized)

def _generate_justification(overall_score: int, decision: str, skills_score: int, experience_score: int,
                          culture_score: int, domain_score: int, logistics_score: int,
                          top_reasons: List[str], missing_data: List[str]) -> str:
    """Generate a concise justification for the match score in 100 words or less"""

    # Start with overall assessment
    if overall_score >= 75:
        justification = f"Strong match ({overall_score}/100). "
    elif overall_score >= 50:
        justification = f"Moderate match ({overall_score}/100). "
    else:
        justification = f"Poor match ({overall_score}/100). "

    # Highlight strongest and weakest dimensions
    scores = {
        "skills": skills_score,
        "experience": experience_score,
        "culture": culture_score,
        "domain": domain_score,
        "logistics": logistics_score
    }

    best_dimension = max(scores, key=scores.get)
    worst_dimension = min(scores, key=scores.get)

    justification += f"Strongest: {best_dimension} ({scores[best_dimension]}/100). "

    if scores[worst_dimension] < 60:
        justification += f"Weakest: {worst_dimension} ({scores[worst_dimension]}/100). "

    # Add top reasons (limit to avoid exceeding 100 words)
    if top_reasons:
        reason_text = "; ".join(top_reasons[:2])  # Max 2 reasons to stay under word limit
        justification += f"Key factors: {reason_text}. "

    # Note missing data if significant
    if missing_data and len(missing_data) > 1:
        justification += f"Limited by missing data ({len(missing_data)} items)."

    # Ensure under 100 words by truncating if necessary
    words = justification.split()
    if len(words) > 100:
        justification = " ".join(words[:97]) + "..."

    return justification

def calculate_match_score(match_data: dict) -> str:
    """Calculate candidate-job match scores and return ScoreCard JSON"""
    try:
        # Validate input schemas
        job_spec = JobSpec.model_validate(match_data["job_spec"])
        candidate = CandidateProfile.model_validate(match_data["candidate_profile"])
        company = None

        # Handle both single company_profile and list of company_details
        if match_data.get("company_profile"):
            company = CompanyProfile.model_validate(match_data["company_profile"])
        elif match_data.get("company_details") and isinstance(match_data["company_details"], list) and len(match_data["company_details"]) > 0:
            # Use the first company details if multiple are provided
            company = CompanyProfile.model_validate(match_data["company_details"][0])

        missing_data = []
        evidence = []
        reasons = []

        # Skills scoring (45%)
        skills_score = _calculate_skills_score(job_spec, candidate, evidence, reasons)

        # Experience scoring (20%)
        experience_score = _calculate_experience_score(job_spec, candidate, evidence, reasons, missing_data)

        # Culture scoring (20% or 10% if no culture data)
        culture_score, culture_weight = _calculate_culture_score(job_spec, candidate, company, evidence, reasons, missing_data)

        # Domain scoring (10%)
        domain_score = _calculate_domain_score(job_spec, candidate, evidence, reasons)

        # Logistics scoring (5%)
        logistics_score = _calculate_logistics_score(job_spec, candidate, evidence, reasons, missing_data)

        # Calculate weighted overall score
        if culture_weight == 10:  # Reduced culture weight due to missing data
            weights = {"skills": 45, "experience": 20, "culture": 10, "domain": 15, "logistics": 10}
        else:
            weights = {"skills": 45, "experience": 20, "culture": 20, "domain": 10, "logistics": 5}

        overall_score = int(
            (skills_score * weights["skills"] +
             experience_score * weights["experience"] +
             culture_score * weights["culture"] +
             domain_score * weights["domain"] +
             logistics_score * weights["logistics"]) / 100
        )

        # Determine decision band
        if overall_score >= 75:
            decision = "proceed"
        elif overall_score >= 50:
            decision = "maybe"
        else:
            decision = "reject"

        # Generate justification (100 words or less)
        justification = _generate_justification(
            overall_score, decision, skills_score, experience_score,
            culture_score, domain_score, logistics_score, reasons[:3], missing_data
        )

        scorecard = ScoreCard(
            overall_score=overall_score,
            sub_scores=SubScores(
                skills=skills_score,
                experience=experience_score,
                culture=culture_score,
                domain=domain_score,
                logistics=logistics_score
            ),
            decision=decision,
            justification=justification,
            reasons=reasons[:8],  # Limit to 8 reasons max
            missing_data=missing_data,
            evidence=evidence[:6]  # Limit to 6 evidence items max
        )

        return scorecard.model_dump_json()

    except ValidationError as e:
        return json.dumps({"error": "validation_failed", "details": json.loads(e.json())})
    except Exception as e:
        return json.dumps({"error": "calculation_failed", "details": str(e)})

def _calculate_skills_score(job_spec: JobSpec, candidate: CandidateProfile, evidence: List[Evidence], reasons: List[str]) -> int:
    """Calculate skills alignment score (0-100)"""
    candidate_skills = _normalize_tech(candidate.skills)
    job_tech_stack = _normalize_tech(job_spec.tech_stack)
    must_have = _normalize_tech(job_spec.must_have_hard_skills)
    nice_to_have = _normalize_tech(job_spec.nice_to_have_hard_skills)

    # Must-have skills (critical)
    must_have_matches = set(must_have) & set(candidate_skills)
    must_have_coverage = len(must_have_matches) / max(len(must_have), 1)

    # Nice-to-have skills (bonus)
    nice_to_have_matches = set(nice_to_have) & set(candidate_skills)
    nice_to_have_coverage = len(nice_to_have_matches) / max(len(nice_to_have), 1) if nice_to_have else 0

    # Tech stack alignment
    tech_matches = set(job_tech_stack) & set(candidate_skills)
    tech_coverage = len(tech_matches) / max(len(job_tech_stack), 1) if job_tech_stack else 0

    # Calculate weighted score
    skills_score = int(must_have_coverage * 70 + nice_to_have_coverage * 15 + tech_coverage * 15)

    # Add evidence and reasons
    if must_have_matches:
        evidence.append(Evidence(source="candidate", quote=f"Skills: {', '.join(sorted(must_have_matches))}", field="skills"))
        reasons.append(f"matches {len(must_have_matches)}/{len(must_have)} must-have skills")

    if len(must_have) > len(must_have_matches):
        missing_skills = set(must_have) - must_have_matches
        reasons.append(f"missing {len(missing_skills)} must-have skills: {', '.join(sorted(missing_skills))}")

    return skills_score

def _calculate_experience_score(job_spec: JobSpec, candidate: CandidateProfile, evidence: List[Evidence], reasons: List[str], missing_data: List[str]) -> int:
    """Calculate experience and seniority alignment score (0-100)"""
    score = 50  # Base score

    # Years of experience check
    if job_spec.experience_requirements and job_spec.experience_requirements.years_min is not None:
        years_min = job_spec.experience_requirements.years_min
        candidate_years = candidate.years_experience

        if candidate_years >= years_min:
            score += 30
            reasons.append(f"{candidate_years} years meets {years_min}+ requirement")
            evidence.append(Evidence(source="candidate", quote=f"{candidate_years} years experience", field="experience"))
        else:
            score -= 20
            reasons.append(f"{candidate_years} years below {years_min}+ requirement")
    else:
        missing_data.append("experience_requirements.years_min")

    # Seniority alignment
    if job_spec.seniority and job_spec.seniority != "unspecified":
        job_seniority = job_spec.seniority.lower()
        candidate_title = (candidate.current_title or "").lower()

        seniority_keywords = {
            "junior": ["junior", "graduate", "entry"],
            "mid": ["mid", "intermediate", "engineer", "developer"],
            "senior": ["senior", "sr", "lead"],
            "lead": ["lead", "principal", "staff", "architect"]
        }

        if job_seniority in seniority_keywords:
            if any(keyword in candidate_title for keyword in seniority_keywords[job_seniority]):
                score += 20
                reasons.append(f"seniority aligned: {job_seniority}")
            else:
                score -= 10
                reasons.append(f"seniority mismatch: expects {job_seniority}")

    return max(0, min(100, score))

def _calculate_culture_score(job_spec: JobSpec, candidate: CandidateProfile, company: Optional[CompanyProfile], evidence: List[Evidence], reasons: List[str], missing_data: List[str]) -> tuple[int, int]:
    """Calculate culture and values alignment score. Returns (score, weight_used)"""
    if company and company.culture_fit:
        # Use explicit culture fit score from company agent
        score = company.culture_fit.score
        reasons.append(f"culture fit assessed: {score}/100")
        evidence.append(Evidence(source="company", quote=f"Culture fit score: {score}", field="culture"))
        return score, 20  # Full weight

    # Fallback: estimate from available data with uncertainty penalty
    score = 60  # Conservative base
    weight = 10  # Reduced weight due to missing explicit culture assessment

    if company and company.culture_values:
        # Basic overlap check
        evidence.append(Evidence(source="company", quote=f"Values: {', '.join(company.culture_values[:3])}", field="culture"))
        reasons.append("culture estimated from company values")
    else:
        missing_data.append("company_profile.culture_fit")
        reasons.append("limited culture data available")

    return score, weight

def _calculate_domain_score(job_spec: JobSpec, candidate: CandidateProfile, evidence: List[Evidence], reasons: List[str]) -> int:
    """Calculate domain and industry familiarity score (0-100)"""
    score = 50  # Base score

    # Industry match
    if job_spec.industry and candidate.industry_experience:
        job_industry = job_spec.industry.lower()
        candidate_industries = [ind.lower() for ind in candidate.industry_experience]

        if job_industry in candidate_industries:
            score += 40
            reasons.append(f"industry experience: {job_spec.industry}")
            evidence.append(Evidence(source="candidate", quote=f"Industry: {job_spec.industry}", field="domain"))
        else:
            # Check for related industries
            related_matches = any(job_industry in ind or ind in job_industry for ind in candidate_industries)
            if related_matches:
                score += 20
                reasons.append(f"related industry experience")

    # Domain knowledge overlap
    if job_spec.domain_knowledge and candidate.industry_experience:
        domain_overlap = set([d.lower() for d in job_spec.domain_knowledge]) & set([i.lower() for i in candidate.industry_experience])
        if domain_overlap:
            score += 10
            reasons.append(f"domain knowledge overlap")

    return max(0, min(100, score))

def _calculate_logistics_score(job_spec: JobSpec, candidate: CandidateProfile, evidence: List[Evidence], reasons: List[str], missing_data: List[str]) -> int:
    """Calculate logistics compatibility score (0-100)"""
    score = 70  # Base score assuming general compatibility

    # Location compatibility
    if job_spec.location and candidate.locations:
        job_type = (job_spec.location.type or "").lower()
        candidate_type = (candidate.locations.type or "").lower()

        if job_type == candidate_type or candidate_type == "remote":
            score += 20
            reasons.append(f"location type compatible: {job_type}")
        elif job_type == "hybrid" and candidate_type in ["onsite", "remote"]:
            score += 10
            reasons.append("location type partially compatible")
        else:
            score -= 15
            reasons.append(f"location type mismatch: needs {job_type}")

    # Salary compatibility
    if job_spec.salary_range and candidate.salary_expectation:
        if (job_spec.salary_range.max is not None and candidate.salary_expectation.min is not None):
            if job_spec.salary_range.max >= candidate.salary_expectation.min:
                score += 10
                reasons.append("salary expectations aligned")
            else:
                score -= 20
                reasons.append("salary expectations misaligned")
        else:
            missing_data.append("complete_salary_information")
    else:
        missing_data.append("salary_range_or_expectation")

    return max(0, min(100, score))

def make_scorecard_tool():
    return StructuredTool.from_function(
        name="calculate_match_score",
        description=("Calculate candidate-job match scores and return ScoreCard JSON. "
                     "Call this as the FINAL step after validating inputs."),
        func=calculate_match_score,
        args_schema=MatchEvaluationInput,
        return_direct=False,
    )

# ---------- utils ----------
def get_tools_description(tools):
    return "\n".join(
        f"Tool: {tool.name}, Schema: {json.dumps(tool.args).replace('{', '{{').replace('}', '}}')}"
        for tool in tools
    )

async def create_agent(coral_tools, local_tools):
    coral_tools_description = get_tools_description(coral_tools)
    local_tools_description = get_tools_description(local_tools)
    combined_tools = coral_tools + local_tools

    prompt = ChatPromptTemplate.from_messages([
        ("system",
f"""
You are the **Match Evaluation Agent**.

Inputs you will receive (as a JSON string in the mention content):
- action: "evaluate_match"
- job_spec: JobSpec (from role-requirements-builder)
- candidate_profile: CandidateProfile
- company_profile: CompanyProfile (optional) OR company_details: List[CompanyProfile] (alternative format)

Goal:
1) Validate inputs; if missing or malformed, return JSON with error field and validation_failed code.
2) Normalize strings and lists; dedupe; canonicalize tech names.
3) Compute sub-scores:
   - Skills: emphasize must_have_hard_skills vs candidate skills. Nice-to-have provides partial credit.
   - Experience: align years_experience and experience_requirements; check seniority and responsibilities alignment.
   - Culture: use company_profile.culture_fit.score if present; otherwise estimate conservatively from overlapping culture_values and note uncertainty.
   - Domain: overlap between job_spec.industry/domain_knowledge and candidate industry_experience.
   - Logistics: feasibility for location type/cities and salary tolerance.
4) Compose overall_score using weights: skills 45%, experience 20%, culture 20% (cap 10% without explicit signal), domain 10%, logistics 5%.
5) Build concise reasons (max 8 short items), missing_data, evidence, and a justification (100 words or less explaining the score).
6) Call the local tool **calculate_match_score** to get the final ScoreCard JSON.
7) Reply to the ORIGINAL sender in the SAME thread with ONLY that JSON.

Important rules:
- Do not fabricate salary, titles, or company facts. If unknown, leave null and record as missing_data.
- Keep list items short and atomic; British English.
- Never output prose, code fences, or explanations—only JSON.
- Decision bands: proceed ≥ 75, maybe 50–74, reject < 50.

Available Coral tools:
{coral_tools_description}

Local scoring tools:
{local_tools_description}
"""),
        ("placeholder", "{agent_scratchpad}")
    ])

    model = init_chat_model(
        model=os.getenv("MODEL_NAME", "gpt-4.1"),
        model_provider=os.getenv("MODEL_PROVIDER", "openai"),
        api_key=os.getenv("MODEL_API_KEY"),
        temperature=float(os.getenv("MODEL_TEMPERATURE", "0.1")),
        max_tokens=int(os.getenv("MODEL_MAX_TOKENS", "8000")),
        base_url=os.getenv("MODEL_BASE_URL", None)
    )
    agent = create_tool_calling_agent(model, combined_tools, prompt)
    return AgentExecutor(agent=agent, tools=combined_tools, verbose=True, handle_parsing_errors=True)

# ---------- main ----------
async def main():
    runtime = os.getenv("CORAL_ORCHESTRATION_RUNTIME", None)
    if runtime is None:
        load_dotenv()

    base_url = os.getenv("CORAL_SSE_URL")
    agentID = os.getenv("CORAL_AGENT_ID")

    coral_params = {
        "agentId": agentID,
        "agentDescription": "Match Evaluation Agent: calculates candidate-job alignment scores with culture, skills, and experience analysis"
    }

    query_string = urllib.parse.urlencode(coral_params)
    CORAL_SERVER_URL = f"{base_url}?{query_string}"
    print(f"Connecting to Coral Server: {CORAL_SERVER_URL}")

    timeout = float(os.getenv("TIMEOUT_MS", "300"))
    client = MultiServerMCPClient(
        connections={
            "coral": {
                "transport": "sse",
                "url": CORAL_SERVER_URL,
                "timeout": timeout,
                "sse_read_timeout": timeout,
            }
        }
    )

    print("Multi Server Connection Established")

    coral_tools = await client.get_tools(server_name="coral")
    local_tools = [make_scorecard_tool()]

    print(f"Coral tools: {len(coral_tools)} | local tools: {len(local_tools)}")

    agent_executor = await create_agent(coral_tools, local_tools)

    while True:
        try:
            print("Starting new agent invocation")
            await agent_executor.ainvoke({"agent_scratchpad": []})
            print("Completed agent invocation, restarting loop")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error in agent loop: {str(e)}")
            print(traceback.format_exc())
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())