import urllib.parse
from dotenv import load_dotenv
import os, json, asyncio, traceback, copy
from typing import Optional, List
from pydantic import BaseModel, Field, ValidationError
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import StructuredTool

# ---------- Spec schema ----------
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
    source: str = Field(description="jd|company")
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

class StandardiseInput(BaseModel):
    raw_spec: dict = Field(description="Partially filled dict for JobSpec built from the JD and research.")

def _dedupe(xs: Optional[List[str]]) -> List[str]:
    if not xs: return []
    return list(dict.fromkeys([x.strip() for x in xs if x and x.strip()]))

def standardise_spec(raw_spec: dict) -> str:
    for k in ["tech_stack","must_have_hard_skills","nice_to_have_hard_skills",
              "soft_skills","keywords","benefits","domain_knowledge",
              "culture_requirements","responsibilities","education_requirements",
              "screening_questions"]:
        if k in raw_spec and isinstance(raw_spec[k], list):
            raw_spec[k] = _dedupe(raw_spec[k])
    try:
        spec = JobSpec.model_validate(raw_spec)
    except ValidationError as e:
        return json.dumps({"error": "validation_failed", "details": json.loads(e.json())})
    return spec.model_dump_json()

def make_standardise_tool():
    return StructuredTool.from_function(
        name="standardise_spec",
        description=("Validate and normalise a partially-filled job requirement object "
                     "into the strict JobSpec JSON. Call this as the FINAL step."),
        func=standardise_spec,
        args_schema=StandardiseInput,
        return_direct=False,
    )

# ---------- utils ----------
def get_tools_description(tools):
    return "\n".join(
        f"Tool: {tool.name}, Schema: {json.dumps(tool.args).replace('{', '{{').replace('}', '}}')}"
        for tool in tools
    )

def prefix_tool_names(tools, agent_name):
    """Prefix tool names with agent name to avoid conflicts across agents"""
    prefixed_tools = []
    for tool in tools:
        # Create a copy of the tool
        new_tool = copy.deepcopy(tool)
        # Add agent prefix to tool name
        new_tool.name = f"{agent_name}_{tool.name}"
        prefixed_tools.append(new_tool)
    return prefixed_tools

async def create_agent(coral_tools, local_tools, company_research_agent_id: str):
    # Prefix coral tool names to avoid conflicts with other agents
    agent_name = "role_requirements_builder"
    prefixed_coral_tools = prefix_tool_names(coral_tools, agent_name)

    coral_tools_description = get_tools_description(prefixed_coral_tools)
    local_tools_description = get_tools_description(local_tools)
    combined_tools = prefixed_coral_tools + local_tools

    COMPANY_RESEARCH_AGENT_ID = company_research_agent_id

    prompt = ChatPromptTemplate.from_messages([
        ("system",
"""
You are the **Job Requirement Builder Agent**.

Inputs you will receive (as a JSON string in the mention content):
- job_description: string (raw JD)
- company_linkedin_url: string | null

Goal:
1) Parse the JD into a partial spec (fields listed below).
2) If company_linkedin_url is present, request enrichment from the **Company Research Agent** (agentId="{company_research_agent_id}"):
   - Send a Coral message using `role_requirements_builder_coral_send_message` in the SAME thread with content:
     {{
       "action":"company_snapshot",
       "company_linkedin_url":"<url>",
       "need_fields":["industry","culture_signals","locations","salary_benchmarks","common_tech_stack"]
     }}
   - Then call `role_requirements_builder_coral_wait_for_mentions` repeatedly (short timeouts ok) UNTIL you receive a reply in the SAME thread FROM that agent. Expect JSON content with any of those fields.
3) Merge the JD parse + company snapshot into a single dict.
4) Call the local tool **standardise_spec** with that dict to get the final JobSpec JSON.
5) Reply to the ORIGINAL sender in the SAME thread with ONLY that JSON.
6) On any error, send a JSON with {{"error":"...", "details":"..."}}.

Partial spec you should assemble BEFORE calling standardise_spec:
- role_title, seniority, employment_type
- salary_range (only if explicit in JD or clearly benchmarked in reply)
- location {{type, cities}}
- tech_stack, must_have_hard_skills, nice_to_have_hard_skills, soft_skills
- industry, domain_knowledge, culture_requirements
- responsibilities, education_requirements, experience_requirements
- keywords, benefits, screening_questions
- extracted_evidence: 2–6 short quotes with source="jd" or "company"

Important rules:
- Be faithful to text; do NOT invent salary. If unknown, leave null/empty and add a brief note in extracted_evidence.
- Keep list items short and atomic; normalise tech names (e.g., "postgresql" -> "postgres").
- Always respond to the sender, even if you only have an error message.

Available Coral tools:
{coral_tools_description}

Local validation tools:
{local_tools_description}
"""),
        ("placeholder", "{agent_scratchpad}")
    ]).partial(
        company_research_agent_id=company_research_agent_id,
        coral_tools_description=coral_tools_description,
        local_tools_description=local_tools_description
    )

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
    company_research_agent_id = os.getenv("COMPANY_RESEARCH_AGENT_ID")  # REQUIRED

    coral_params = {
        "agentId": agentID,
        "agentDescription": "Job Requirement Builder Agent: standardises job specs and enriches via Company Research Agent"
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
    local_tools = [make_standardise_tool()]

    print(f"Coral tools: {len(coral_tools)} | local tools: {len(local_tools)}")

    agent_executor = await create_agent(coral_tools, local_tools, company_research_agent_id)

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