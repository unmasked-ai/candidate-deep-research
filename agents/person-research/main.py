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
                f"""Your task is to do deep research on a person, aggregating information from different sources such as LinkedIn, GitHub, personal portfolio website, and build a profile about a person. The exact persona and metrics may be defined by the instructions it receives from other agents, otherwise optimise for a candidate.

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

                OUTPUT FORMAT REQUIREMENT:
                When asked to provide candidate profile for match evaluation, respond with XML in this format:
                ```xml
                <candidate_profile>
                  <name>Candidate Name</name>
                  <years_experience>5.0</years_experience>
                  <current_title>Software Engineer</current_title>
                  <skills>
                    <skill>python</skill>
                    <skill>react</skill>
                    <skill>kubernetes</skill>
                  </skills>
                  <certifications>
                    <certification>AWS Certified</certification>
                  </certifications>
                  <education>
                    <degree>BS Computer Science</degree>
                  </education>
                  <roles_history>
                    <role>Software Engineer at Company X</role>
                    <role>Developer at Company Y</role>
                  </roles_history>
                  <locations>
                    <type>remote</type>
                    <cities>
                      <city>San Francisco</city>
                    </cities>
                  </locations>
                  <salary_expectation>
                    <currency>USD</currency>
                    <min>80000</min>
                    <max>120000</max>
                    <period>year</period>
                  </salary_expectation>
                  <industry_experience>
                    <industry>tech</industry>
                    <industry>fintech</industry>
                  </industry_experience>
                </candidate_profile>
                ```

                WORKFLOW INTEGRATION:
                - When interface agent requests candidate research, gather comprehensive profile data
                - Structure output as CandidateProfile XML for match-evaluation agent
                - Include all available information even if some fields are null/empty
                - Reply with structured XML when research is complete

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
