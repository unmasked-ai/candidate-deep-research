import urllib.parse
from dotenv import load_dotenv
import os, json, asyncio, traceback
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_tool_calling_agent, AgentExecutor
from pydantic import BaseModel
from typing import List

# typing for making outputs structured in json format
class SkilsScore(BaseModel):
    skill: str
    score: float
    reason: str

class GitHubReviewAgentOutput(BaseModel):
    summary: str
    bio: str
    repos: int
    skills: List[SkilsScore]
    overall_score: float

class ErrorOutput(BaseModel):
    error: str
    details: str

output_json = json.dumps(GitHubReviewAgentOutput.model_json_schema(), indent=2)
error_json = json.dumps(ErrorOutput.model_json_schema(), indent=2)

def get_tools_description(tools):
    return "\n".join(
        f"Tool: {tool.name}, Schema: {json.dumps(tool.args).replace('{', '{{').replace('}', '}}')}"
        for tool in tools
    )


async def create_agent(coral_tools, agent_tools):
    coral_tools_description = get_tools_description(coral_tools)
    agent_tools_description = get_tools_description(agent_tools)
    combined_tools = coral_tools + agent_tools
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                    
                f"""    
                # GitHub Review Agent (Coral)

- **Mode**: Reactive → wait for mentions via `coral_wait_for_mentions` before acting.  
- **Inputs (JSON)**:
  - `github_profile_url`: str  
  - `max_repos`: int (default 3)  
  - `competency_weights`: competency: weight, renormalize if given  

---

## Competencies  
If job-specific list is missing, default to:
- DevOps  
- Testing  
- Documentation  
- Dependency Mgmt  
- Security  
- Performance  

---

## Goal  
Concise, evidence-backed GitHub review. **Output JSON only**.

---

## Strategy  

### 1. Discovery  
- Fetch repos (`per_page=100`, sort=updated, skip forks/archived/templates).  
- Pick top `max_repos` with technical signals (workflows, configs, docs, container files).  

### 2. Tree-first scan  
- One tree call per repo. Score ~70% from structure/signals.  
- Curiosity budget: 6 (2 if <100 rate limit).  

### 3. Targeted deep dives  
Spend budget only if signals found:  
- **Config**: tsconfig, pyproject → strict/linting/typing.  
- **Testing**: test dirs, CI configs.  
- **DevOps**: Dockerfile, .dockerignore, security hints.  
- **Docs**: README/docs/ADR → quality check.  
- **Deps**: lockfiles + dependabot.  

### 4. Stop smart  
- Stop if budget gone or 2 useless fetches in a row.  

---

## Scoring  
- Subscores ∈ [0,1].  
- Weight with `competency_weights` (else defaults).  
- `final_score = 100 * weighted sum`.  
- Repo summary ≤240 chars.  
- Evidence: 2–6 items (`file + reason`).  
- Overall score = recency-weighted mean (1.0 <90d, 0.7 90–365d, 0.4 >365d).  

---

## After research ONLY after being asked to do so, output JSON  


  "summary": "str",
  "bio": "str",
  "repos": int,
  "skills": [
    "skill": "str", "score": 0.0, "reason": "str"
  ],
  "overall_score": 0.0


                """
            ),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    model = init_chat_model(
        model=os.getenv("MODEL_NAME", "gpt-4.1-mini"),
        model_provider=os.getenv("MODEL_PROVIDER", "openai"),
        api_key=os.getenv("MODEL_API_KEY"),
        temperature=os.getenv("MODEL_TEMPERATURE", "0.3"),
        max_tokens=os.getenv("MODEL_MAX_TOKENS", "16000"),
        base_url=os.getenv("MODEL_BASE_URL", None),
    )

    agent = create_tool_calling_agent(model, combined_tools, prompt)
    return AgentExecutor(
        agent=agent, tools=combined_tools, verbose=True, handle_parsing_errors=True
    )


async def main():
    runtime = os.getenv("CORAL_ORCHESTRATION_RUNTIME", None)
    if runtime is None:
        load_dotenv()

    base_url = os.getenv("CORAL_SSE_URL")
    agentID = os.getenv("CORAL_AGENT_ID")

    coral_params = {
        "agentId": agentID,
        "agentDescription": "Github agent can create, update, and search for repositories and files, as well as view/edit issues and pull requests (depending on permissions)",
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
            },
            "github": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv(
                        "GITHUB_PERSONAL_ACCESS_TOKEN"
                    )
                },
            },
        }
    )

    print("Multi Server Connection Initialized")

    coral_tools = await client.get_tools(server_name="coral")
    github_tools = await client.get_tools(server_name="github")
    print(
        f"Coral tools count: {len(coral_tools)}, GitHub tools count: {len(github_tools)}"
    )

    agent_executor = await create_agent(coral_tools, github_tools)

    while True:
        try:
            print("Starting new agent invocation")
            await agent_executor.ainvoke({"agent_scratchpad": []})
            print("Completed agent invocation, restarting loop")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error in agent loop: {e}")
            traceback.print_exc()
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
