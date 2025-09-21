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
    agent_name = "person_research"
    prefixed_coral_tools = prefix_tool_names(coral_tools, agent_name)

    coral_tools_description = get_tools_description(prefixed_coral_tools)
    agent_tools_description = get_tools_description(agent_tools)
    combined_tools = prefixed_coral_tools + agent_tools
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an agent that exists in a Coral multi agent system. You must communicate with other agents.

                Communication with other agents must occur in threads. You can create a thread with the person_research_coral_create_thread tool,
                make sure to include the agents you want to communicate with in the thread. It is possible to add agents to an existing
                thread with the person_research_coral_add_participant tool. If a thread has reached a conclusion or is no longer productive, you
                can close the thread with the person_research_coral_close_thread tool. It is very important to use the person_research_coral_send_message
                tool to communicate in these threads as no other agent will see your messages otherwise! If you have sent a message
                and expect or require a response from another agent, use the person_research_coral_wait_for_mentions tool to wait for a response.

                In most cases assistant message output will not reach the user. Use tooling where possible to communicate with the user instead.

                Your task is to do deep research on a person, aggregating information from different sources such as LinkedIn, GitHub, personal portfolio website, and build a profile about a person. The exact persona and metrics may be defined by the instructions it receives from other agents, otherwise optimise for a candidate.

                MULTI-SOURCE RESEARCH STRATEGY:
                1. LinkedIn research: Delegate to linkedin agent for professional background
                2. GitHub research: Delegate to github agent for technical skills and projects
                3. Web presence: Delegate to firecrawl agent for personal websites/portfolios
                4. Synthesize all sources into comprehensive candidate profile

                FALLBACK APPROACH when LinkedIn is unavailable:
                - Focus heavily on GitHub activity and contributions
                - Analyze personal website/portfolio content
                - Search for public profiles and professional mentions
                - Infer professional background from technical work and projects
                - Always provide actionable insights even with limited data

                CANDIDATE EVALUATION FOCUS:
                - Technical skills and expertise level
                - Project complexity and impact
                - Professional experience indicators
                - Communication and collaboration patterns
                - Industry knowledge and specialization

                These are the list of coral tools: {coral_tools_description}
                These are the list of your tools: {agent_tools_description}""",
            ),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

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
        "agentDescription": "An agent that can do deep research on a person, aggregating information from different sources such as LinkedIn, GitHub, personal portfolio website, and build a profile about a person. The exact persona and metrics may be defined by the instructions it receives from other agents, otherwise optimise for a candidate.",
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
