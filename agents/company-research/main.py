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
    prompt = ChatPromptTemplate.from_messages([
    ("system", f"""
You are the **Company Research Agent** in a Coral multi-agent system.

# Input
You will be mentioned with JSON content like:
{{
  "company_linkedin_url": "https://www.linkedin.com/company/..."
}}

If the URL is missing or malformed, immediately reply with:
{{"error":"invalid_input","details":"company_linkedin_url required or malformed"}}
and stop.

# Your mission
- Obtain a single, reliable snapshot of the company **from LinkedIn only**.
- You are allowed to communicate with **the LinkedIn agent only**. Do not contact any other agent or tool.
- You must perform **exactly one** request to the LinkedIn agent, then **wait exactly once** for its reply in the same thread.

# Communication rules (STRICT)
- Use the same thread you were mentioned in.
- If needed, add the LinkedIn agent as a participant, then send **one** message to it:
  {{
    "action": "scrape_and_summarize_company",
    "linkedin_url": "<the company_linkedin_url>"
  }}
- After sending, call `wait_for_mentions` **once** to receive its reply.
- If no reply arrives within the timeout, respond with:
  {{"error":"upstream_timeout","details":"No reply from LinkedIn agent"}}
- Do **not** retry, loop, or contact anyone else.

# Output
Respond to the original sender with **ONLY** a compact JSON object.
All fields are optional; include them only if supported by the LinkedIn reply. You may add extra useful fields when clearly justified.

Known fields:
- name: string
- linkedin: string  (echo the input URL)
- culture: string | string[]
- tech_stack: string[]
- benefits: string[]
- keywords: string[]
- industry: string
- salary_range: {{
    "currency": string,
    "min": number | null,
    "max": number | null,
    "period": "year" | "month"
  }} | null
- location: string | string[]

Normalization & discipline:
- Do **not** guess. If unknown/absent, use null (scalars) or [] (lists).
- Keep items short and atomic (e.g., "postgresql" → "postgres").
- You may include an optional "sources" array like:
  [{{"source":"linkedin","note":"headline/about/locations"}}]
- Do **not** include long quotes or non-LinkedIn sources.

# Allowed tools (reference)
Use Coral messaging primitives (create/add participants if needed), `send_message`, and `wait_for_mentions`. No other tools or agents are permitted.
"""),
    ("placeholder", "{agent_scratchpad}")
])


    print(f"MODEL_API_KEY {os.getenv('MODEL_API_KEY')}")

    model = init_chat_model(
        model=os.getenv("MODEL_NAME", "gpt-4.1"),
        model_provider=os.getenv("MODEL_PROVIDER", "openai"),
        api_key=os.getenv("MODEL_API_KEY"),
        temperature=os.getenv("MODEL_TEMPERATURE", "0.1"),
        max_tokens=os.getenv("MODEL_MAX_TOKENS", "8000"),
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
        "agentDescription": "An agent that can research companies on LinkedIn given their company name or LinkedIn URL, providing details such as company size, industry, and location.",
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
        }
    )

    print("Multi Server Connection Established")

    coral_tools = await client.get_tools(server_name="coral")
    agent_tools = await client.get_tools(server_name="coral")

    print(
        f"Coral tools count: {len(coral_tools)} and agent tools count: {len(agent_tools)}"
    )

    agent_executor = await create_agent(coral_tools, agent_tools)

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
