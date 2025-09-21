import urllib.parse
from dotenv import load_dotenv
import os, json, asyncio, traceback, copy
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_tool_calling_agent, AgentExecutor


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


async def create_agent(coral_tools, agent_tools):
    # Prefix coral tool names to avoid conflicts with other agents
    agent_name = "company_research"
    prefixed_coral_tools = prefix_tool_names(coral_tools, agent_name)

    coral_tools_description = get_tools_description(prefixed_coral_tools)
    agent_tools_description = get_tools_description(agent_tools)
    combined_tools = prefixed_coral_tools + agent_tools
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""Goal: Research companies to build a comprehensive profile across multiple sources.

                **IMPORTANT**
                You must wait until you are mentioned in a thread by another agent before taking action, calling the `coral_wait_for_mentions` function.

                1. Receive company name or a URL.
                2. Collect data from available sources:
                    a. Use LinkedIn Agent for employee count, hiring trends, and company profile. Send it the company LinkedIn URL.
                    b. Use Firecrawl Agent to scrape info from the main company website, only search maximum 1 page. If this fails skip to the next step.
                3. Extract key details: size, industry, stage (startup, scaleup, enterprise), tech stack, culture/values, and funding.
                4. Format the data into a structured company profile.
                5. Return the structured profile to the sender agent.
                6. Always respond with something useful rather than just reporting the error.

                These are the list of coral tools: {coral_tools_description}
                These are the list of your tools: {agent_tools_description}""",
            ),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

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
        "agentDescription": "An agent that can perform deep research on companies, searching across LinkedIn and the company website.",
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
    agent_tools = []

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
