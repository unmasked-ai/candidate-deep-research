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
    agent_name = "linkedin"
    prefixed_coral_tools = prefix_tool_names(coral_tools, agent_name)

    coral_tools_description = get_tools_description(prefixed_coral_tools)
    agent_tools_description = get_tools_description(agent_tools)
    combined_tools = prefixed_coral_tools + agent_tools
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""Your goal is to research people and companies on LinkedIn, given either their name or LinkedIn URL, and return structured JSON output with relevant details.
                
                You are an agent that exists in a Coral multi agent system.  You must communicate with other agents.

                **IMPORTANT**
                You must wait until you are mentioned in a thread by another agent before taking action, calling the `coral_wait_for_mentions` function.

                Goal
                1. Accept input containing a target LinkedIn URL (person or company).
                2. Extract data using the apify linkedin tools, always passing the LinkedIn URL as input to these calls:
                    - For candidates: work history, education, endorsements, skills.
                    - For companies: size, industry, employees, hiring trends.
                3. Clean and normalize the extracted information.
                4. Return structured JSON output to the requesting agent.
                5. Always respond with something useful rather than just reporting the error

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
        "agentDescription": "An agent that can fetch data from LinkedIn, for both people and companies. This works for person/company name or LinkedIn URL.",
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
            "apify": {
                "transport": "sse",
                "url": "https://mcp.apify.com/sse?tools=fetch-actor-details,call-actor,docs,apimaestro/linkedin-profile-detail,apimaestro/linkedin-profile-full-sections-scraper,apimaestro/linkedin-profile-search-scraper,apimaestro/linkedin-companies-search-scraper,apimaestro/linkedin-company-detail",
                "headers": {"Authorization": f"Bearer {os.getenv('APIFY_API_KEY')}"},
            },
        }
    )

    print("Multi Server Connection Established")

    coral_tools = await client.get_tools(server_name="coral")
    agent_tools = await client.get_tools(server_name="apify")

    print(
        f"Coral tools count: {len(coral_tools)} and agent tools count: {len(agent_tools)}"
    )

    agent_executor = await create_agent(coral_tools, agent_tools)

    # Check if we're in single-task mode (for testing) or continuous mode
    single_task_mode = os.getenv("SINGLE_TASK_MODE", "false").lower() == "true"
    max_iterations = (
        1 if single_task_mode else 50
    )  # Limit iterations to prevent endless loops

    iteration = 0
    task_completed = False

    print(
        f"LinkedIn agent starting: single_task_mode={single_task_mode}, max_iterations={max_iterations}"
    )

    while True:
        try:
            iteration += 1
            print(f"Starting agent invocation {iteration}/{max_iterations}")

            result = await agent_executor.ainvoke({"agent_scratchpad": []})
            print(f"Completed agent invocation {iteration}")

            # In single task mode, complete after one iteration
            if single_task_mode:
                print(
                    "Single task mode - LinkedIn agent completing after one iteration"
                )
                task_completed = True
            else:
                await asyncio.sleep(1)

        except Exception as e:
            print(f"Error in agent loop iteration {iteration}: {str(e)}")
            print(traceback.format_exc())
            await asyncio.sleep(5)

    # Agent execution completed
    if task_completed:
        print("LinkedIn agent task completed successfully")
    else:
        print(f"LinkedIn agent reached maximum iterations ({max_iterations})")

    print("LinkedIn agent terminating gracefully")


if __name__ == "__main__":
    asyncio.run(main())
