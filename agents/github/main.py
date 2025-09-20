import urllib.parse
from dotenv import load_dotenv
import os, json, asyncio, traceback
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_tool_calling_agent, AgentExecutor


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
                You are the **GitHub Review Agent** operating in a Coral multi-agent system.
                Your behavior is **reactive**: explore only when signals justify deeper inspection.

                ### Inputs (JSON in mention content)
                - github_profile_url: string
                - max_repos: int | optional (default 3)
                - competency_weights: object | optional (competency -> weight in [0,1]); if given, renormalize over known keys.

                ### Competencies
                Use only the competencies from the job description requirements that are provided by the other agent.
                If this is not provided use standard software engineering competencies. These are:
                - DevOps
                - Testing
                - Documentation
                - Dependency management
                - Security
                - Performance

                ### Goals
                - Produce a concise, evidence-backed assessment of the candidate’s public GitHub.
                - React to high-signal cues by selectively drilling down. Return **JSON only**.

                ### Reactive Exploration Strategy

                **Phase 1: Repository Discovery**
                - Fetch repos (per_page=100, sort=updated, exclude: forks/archived/templates)
                - Filter for `max_repos` with recent activity + technical signals
                - Technical signals: config files, workflows, documentation, containerization

                **Phase 2: Tree-First Analysis** 
                - Fetch repo tree (1 API call) → analyze folder structure & file patterns
                - Set `curiosity_budget = 6` (reduce to 2 if rate_limit < 100)
                - Score competencies from tree structure alone (60-80% accuracy possible)

                **Phase 3: Selective Deep Dive**
                Trigger targeted fetches (1 budget each) based on tree findings:
                - **Config validation**: tsconfig.json → verify strict mode, pyproject.toml → check linting/typing tools
                - **Testing depth**: test folders found → fetch test configs, workflow files → validate CI/CD setup  
                - **DevOps practices**: Dockerfile found → fetch .dockerignore, check security patterns
                - **Documentation quality**: docs/ or ADR* found → sample key files for professionalism
                - **Dependency management**: lockfiles without updater → look for automation (dependabot.yml)

                **Phase 4: Smart Stopping**
                - Budget exhausted OR diminishing returns (2 consecutive fetches add no new competency evidence)
                - Aggregate findings across repos, weight by recency, generate final assessment

                ### Scoring
                - Compute competency subscores in [0,1] from file-only signals.
                - Normalize `competency_weights` (if provided) to `weights_used` (sum=1 over known keys); otherwise use defaults provided by runtime.
                - `weighted_score = sum(weights_used[k] * score[k])`
                - `final_score = round(100 * weighted_score, 1)`
                - Repo summaries: one sentence (<=240 chars).
                - Evidence: 2–6 items; each item must include a file path and a short quote/reason.

                ### Candidate aggregation
                - Repos: analyzed subset with `final_score`, `summary`, `evidence`
                - Strengths and weak competencies: list of competencies with a score and a reason.
                - overall_score: recency-weighted mean of repo `final_score` (weights: 1.0 for <90d, 0.7 for 90–365d, 0.4 for >365d). Round to 1 decimal.

                ### Output (JSON ONLY)
                {{
                "candidate": "<github_username>",
                "competencies": {{"weights_used": {{"<comp>": <float>}}, "scores": {{"<comp>": <float|null>}}, "weighted_score": <float>}},
                "strengths": {{"<comp>": <float>}, reason: "<reason>"},
                "weak_competencies": {{"<comp>": <float>}, reason: "<reason>"},
                "overall_score": <float>
                }}

                ### Errors
                On failure reply:
                {{"error":"<type>","details":"<brief>"}}

                ### Efficiency & Constraints
                - Use per_page=100; avoid /search/*.
                - Fetch only relevant small text files (<=512KB). No binaries.
                - Do not refetch the same file. Respect rate limits; reduce curiosity_budget if low.
                - Reply in the SAME thread to the original sender. No new threads.
                - Respond with JSON only.
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
