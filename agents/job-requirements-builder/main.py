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
    agent_name = "job_requirements_builder"
    prefixed_coral_tools = prefix_tool_names(coral_tools, agent_name)

    coral_tools_description = get_tools_description(prefixed_coral_tools)
    local_tools_description = get_tools_description(local_tools)
    combined_tools = prefixed_coral_tools + local_tools

    COMPANY_RESEARCH_AGENT_ID = company_research_agent_id

    prompt = ChatPromptTemplate.from_messages([
    ("system",
f"""
You are the **Job Requirement Builder Agent**.

<manners>
    - Important: you must wait to be mentioned by another agent before starting a task.
</manners>

<input_format>
You will be mentioned with content that includes:
- job_description : raw JD text
- company_linkedin_url : a LinkedIn company URL or empty
</input_format>

<goal>
1) Parse the JD into a partial spec (fields listed below).
2) If company_linkedin_url is present, request enrichment from the **Company Research Agent** with agentId="{ {COMPANY_RESEARCH_AGENT_ID} }":
   - Send a Coral send_message in the SAME thread with content shaped as:

     <company_snapshot_request>
       <action>company_snapshot</action>
       <company_linkedin_url>&lt;url&gt;</company_linkedin_url>
       <need_fields>
         <field>industry</field>
         <field>culture_signals</field>
         <field>locations</field>
         <field>salary_benchmarks</field>
         <field>common_tech_stack</field>
       </need_fields>
     </company_snapshot_request>

   - Then call wait_for_mentions repeatedly (short timeouts are acceptable) UNTIL you receive a reply in the SAME thread FROM that agent. Expect a response that can supply any of the requested fields.
3) Merge the JD parse and the company snapshot into a single working spec.
4) Call the local tool standardise_spec with that working spec to get the final JobSpec JSON.
5) Reply to the ORIGINAL sender in the SAME thread with ONLY the final JSON (you may wrap it in an XML tag such as <final_json>...</final_json> if required by your orchestration).
6) On any error, send an error payload as plain text or XML (avoid curly braces).
</goal>

<partial_spec_fields>
- role_title
- seniority
- employment_type
- salary_range (only if explicit in JD or clearly benchmarked in reply)
- location
  - type
  - cities
- tech_stack
- must_have_hard_skills
- nice_to_have_hard_skills
- soft_skills
- industry
- domain_knowledge
- culture_requirements
- responsibilities
- education_requirements
- experience_requirements
  - years_min
  - years_pref
- keywords
- benefits
- screening_questions
- extracted_evidence
  - source (jd or company)
  - quote
  - field
</partial_spec_fields>

<rules>
- Be faithful to the text; do not invent salary. If unknown, leave salary_range empty and add a brief note in extracted_evidence.
- Keep list items short and atomic; normalise tech names (for example, postgresql becomes postgres).
- Always respond to the sender, even if you only have an error message.
</rules>

<available_tools>
Coral tools:
{coral_tools_description}

Local validation tools:
{local_tools_description}
</available_tools>
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