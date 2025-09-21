import urllib.parse
from dotenv import load_dotenv
import os
import json
import asyncio
import logging
import copy
from typing import List, Dict, Any
from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_tool_calling_agent, AgentExecutor

REQUEST_QUESTION_TOOL = "request-question"
ANSWER_QUESTION_TOOL = "answer-question"
MAX_CHAT_HISTORY = 3
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 8000
SLEEP_INTERVAL = 1
ERROR_RETRY_INTERVAL = 5

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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


def load_config() -> Dict[str, Any]:
    print("[VERBOSE] Starting configuration loading...")
    runtime = os.getenv("CORAL_ORCHESTRATION_RUNTIME", None)
    print(f"[VERBOSE] CORAL_ORCHESTRATION_RUNTIME: {runtime}")

    if runtime is None:
        print("[VERBOSE] Runtime not found, loading .env file...")
        load_dotenv()
        print("[VERBOSE] .env file loaded successfully")
    else:
        print("[VERBOSE] Runtime environment detected, skipping .env file")

    print("[VERBOSE] Building configuration dictionary...")
    config = {
        "runtime": os.getenv("CORAL_ORCHESTRATION_RUNTIME", None),
        "coral_connection_url": os.getenv("CORAL_CONNECTION_URL"),
        "agent_id": os.getenv("CORAL_AGENT_ID"),
        "model_name": os.getenv("MODEL_NAME"),
        "model_provider": os.getenv("MODEL_PROVIDER"),
        "api_key": os.getenv("MODEL_API_KEY"),
        "model_temperature": float(os.getenv("MODEL_TEMPERATURE", DEFAULT_TEMPERATURE)),
        "model_token": int(os.getenv("MODEL_TOKEN_LIMIT", DEFAULT_MAX_TOKENS)),
        "base_url": os.getenv("BASE_URL"),
    }

    print(f"[VERBOSE] Configuration loaded:")
    print(f"[VERBOSE]   - runtime: {config['runtime']}")
    print(f"[VERBOSE]   - agent_id: {config['agent_id']}")
    print(f"[VERBOSE]   - model_name: {config['model_name']}")
    print(f"[VERBOSE]   - model_provider: {config['model_provider']}")
    print(f"[VERBOSE]   - api_key: {'***' if config['api_key'] else None}")
    print(f"[VERBOSE]   - model_temperature: {config['model_temperature']}")
    print(f"[VERBOSE]   - model_token: {config['model_token']}")
    print(f"[VERBOSE]   - base_url: {config['base_url']}")

    print("[VERBOSE] Validating required fields...")
    required_fields = [
        "coral_connection_url",
        "agent_id",
        "model_name",
        "model_provider",
        "api_key",
    ]
    missing = [field for field in required_fields if not config[field]]
    if missing:
        print(f"[VERBOSE] ERROR: Missing required fields: {missing}")
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    print("[VERBOSE] All required fields present")

    print("[VERBOSE] Validating model parameters...")
    if not 0 <= config["model_temperature"] <= 2:
        print(f"[VERBOSE] ERROR: Invalid temperature: {config['model_temperature']}")
        raise ValueError(
            f"Model temperature must be between 0 and 2, got {config['model_temperature']}"
        )
    print(f"[VERBOSE] Temperature validation passed: {config['model_temperature']}")

    if config["model_token"] <= 0:
        print(f"[VERBOSE] ERROR: Invalid token limit: {config['model_token']}")
        raise ValueError(f"Model token must be positive, got {config['model_token']}")
    print(f"[VERBOSE] Token limit validation passed: {config['model_token']}")

    print("[VERBOSE] Configuration loading completed successfully")
    return config


def get_tools_description(tools: List[Any]) -> str:
    print(f"[VERBOSE] Starting tools description generation for {len(tools)} tools...")

    descriptions = []
    for i, tool in enumerate(tools):
        print(f"[VERBOSE] Processing tool {i + 1}/{len(tools)}: {tool.name}")
        tool_desc = f"Tool: {tool.name}, Schema: {json.dumps(tool.args).replace('{', '{{').replace('}', '}}')}"
        descriptions.append(tool_desc)
        print(f"[VERBOSE] Tool description generated: {tool_desc[:100]}...")

    result = "\n".join(descriptions)
    print(
        f"[VERBOSE] Tools description generation completed. Total length: {len(result)} characters"
    )
    return result


def format_chat_history(chat_history: List[Dict[str, str]]) -> str:
    print(
        f"[VERBOSE] Starting chat history formatting with {len(chat_history)} conversations..."
    )

    if not chat_history:
        print("[VERBOSE] No chat history found, returning default message")
        return "No previous chat history available."

    print(f"[VERBOSE] Processing {len(chat_history)} chat history entries...")
    history_str = (
        "Previous Conversations (use this to resolve ambiguous references like 'it'):\n"
    )

    for i, chat in enumerate(chat_history, 1):
        print(f"[VERBOSE] Processing conversation {i}/{len(chat_history)}")
        print(f"[VERBOSE] User input length: {len(chat.get('user_input', ''))} chars")
        print(f"[VERBOSE] Agent response length: {len(chat.get('response', ''))} chars")

        history_str += f"Conversation {i}:\n"
        history_str += f"User: {chat['user_input']}\n"
        history_str += f"Agent: {chat['response']}\n\n"

    print(
        f"[VERBOSE] Chat history formatting completed. Total formatted length: {len(history_str)} characters"
    )
    return history_str


async def get_user_input(runtime: str, agent_tools: Dict[str, Any]) -> str:
    print(
        f"[VERBOSE] Starting user input retrieval. Runtime mode: {runtime is not None}"
    )

    # Check if we have a USER_REQUEST environment variable for testing
    user_request = os.getenv("USER_REQUEST")
    if user_request:
        print(f"[VERBOSE] Using USER_REQUEST from environment: {user_request}")
        return user_request

    # Check if we have the get-initial-request custom tool (for Coral sessions)
    initial_request_tool = "interface_get-initial-request"
    if runtime is not None and initial_request_tool in agent_tools:
        try:
            print(
                f"[VERBOSE] Calling {initial_request_tool} to retrieve initial research data..."
            )
            initial_result = await agent_tools[initial_request_tool].ainvoke({})
            print(f"[VERBOSE] Initial request tool result: {initial_result}")

            # Extract research data from the response
            if isinstance(initial_result, dict) and "research_data" in initial_result:
                research_data = initial_result["research_data"]
                if (
                    research_data
                    and research_data != "No initial research data available"
                ):
                    print(
                        f"[VERBOSE] Successfully retrieved initial research data: {len(research_data)} chars"
                    )
                    return research_data
                else:
                    print(
                        f"[VERBOSE] No initial research data available, falling back to Coral messages"
                    )
            else:
                print(
                    f"[VERBOSE] Unexpected response format from initial request tool: {initial_result}"
                )
        except Exception as e:
            print(
                f"[VERBOSE] ERROR: Failed to retrieve initial research data: {str(e)}"
            )
            logger.error(f"Error getting initial research data: {str(e)}")

    if runtime is not None:
        print(f"[VERBOSE] Using runtime mode - waiting for messages from Coral system")
        print(f"[VERBOSE] Available agent tools: {list(agent_tools.keys())}")

        # Check if we have the wait_for_mentions tool (with prefix)
        wait_tool_name = "interface_coral_wait_for_mentions"
        if wait_tool_name in agent_tools:
            try:
                print(f"[VERBOSE] Calling {wait_tool_name} to wait for instructions...")
                # Wait for messages from the Coral system - this should contain the research instructions
                message_result = await agent_tools[wait_tool_name].ainvoke(
                    {"timeout": 30000}
                )  # 30 second timeout
                print(f"[VERBOSE] Received message from Coral system: {message_result}")

                # Extract the actual instruction content from the message
                if isinstance(message_result, dict) and "content" in message_result:
                    user_input = message_result["content"]
                elif isinstance(message_result, str):
                    user_input = message_result
                else:
                    user_input = str(message_result)

                print(
                    f"[VERBOSE] Successfully received input from Coral system: {len(str(user_input))} chars"
                )
            except Exception as e:
                print(
                    f"[VERBOSE] ERROR: Failed to receive messages from Coral system: {str(e)}"
                )
                logger.error(f"Error waiting for Coral messages: {str(e)}")
                # Fallback to default task
                user_input = "Begin candidate research task as configured"
        else:
            print(f"[VERBOSE] Warning: {wait_tool_name} not found, using default task")
            user_input = "Begin candidate research task as configured"
    else:
        print("[VERBOSE] Using interactive mode - prompting user directly")
        user_input = input("How can I assist you today? ").strip()
        print(f"[VERBOSE] Raw user input received: '{user_input}'")

        if not user_input:
            print("[VERBOSE] Empty input detected, using default message")
            user_input = "No input provided"

    print(f"[VERBOSE] Final processed user input: {user_input}")
    logger.info(f"User input: {user_input}")
    return user_input


async def send_response(
    runtime: str, agent_tools: Dict[str, Any], response: str
) -> None:
    print(f"[VERBOSE] Starting response sending. Runtime mode: {runtime is not None}")
    print(f"[VERBOSE] Response length: {len(response)} characters")
    print(f"[VERBOSE] Response preview: {response[:200]}...")

    logger.info(f"Agent response: {response}")

    if runtime is not None:
        print(f"[VERBOSE] Using runtime mode - checking for send-research-result tool")
        print(f"[VERBOSE] Available agent tools: {list(agent_tools.keys())}")

        # Try to find the send-research-result tool (this is the custom tool from backend)
        send_result_tool = None
        for tool_name, tool in agent_tools.items():
            if (
                "send-research-result" in tool_name
                or tool_name == "send-research-result"
            ):
                send_result_tool = tool
                break

        if send_result_tool:
            try:
                print("[VERBOSE] Calling send-research-result tool with response...")
                await send_result_tool.ainvoke({"result": response})
                print(
                    "[VERBOSE] Successfully sent response via send-research-result tool"
                )
            except Exception as e:
                print(
                    f"[VERBOSE] ERROR: Failed to invoke send-research-result tool: {str(e)}"
                )
                logger.error(f"Error invoking send-research-result tool: {str(e)}")
                # Don't raise - just log the error and continue
        else:
            print(
                "[VERBOSE] Warning: send-research-result tool not found - response logged only"
            )
    else:
        print("[VERBOSE] Interactive mode - response logged only (no runtime tool)")

    print("[VERBOSE] Response sending completed")


async def create_agent(coral_tools: List[Any]) -> AgentExecutor:
    print(f"[VERBOSE] Starting agent creation with {len(coral_tools)} coral tools...")

    print("[VERBOSE] Generating tools description...")
    coral_tools_description = get_tools_description(coral_tools)
    print(
        f"[VERBOSE] Tools description generated: {len(coral_tools_description)} characters"
    )

    query = os.getenv("USER_REQUEST")

    print("[VERBOSE] Creating chat prompt template...")
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an agent that exists in a Coral multi agent system.  You must communicate with other agents.

                Communication with other agents must occur in threads. You can create a thread with the interface_coral_create_thread tool,
                make sure to include the agents you want to communicate with in the thread. It is possible to add agents to an existing
                thread with the interface_coral_add_participant tool. If a thread has reached a conclusion or is no longer productive, you
                can close the thread with the interface_coral_close_thread tool. It is very important to use the interface_coral_send_message
                tool to communicate in these threads as no other agent will see your messages otherwise! If you have sent a message
                and expect or require a response from another agent, use the interface_coral_wait_for_mentions tool to wait for a response.

                In most cases assistant message output will not reach the user.  Use tooling where possible to communicate with the user instead.

                Your primary role is to orchestrate the complete candidate research workflow that produces a final match score and justification.

                CANDIDATE RESEARCH WORKFLOW (Execute in this order):
                1. **Parse Input**: Extract candidate LinkedIn URL and job description
                2. **Role Requirements**: Create thread with role-requirements-builder agent to standardize job spec
                3. **Person Research**: Create thread with person-research agent to profile candidate
                4. **Match Evaluation**: Create thread with match-evaluation agent for final scoring - WAIT for match-evaluation to send score back to you
                5. **Deliver Results**: Receive final score from match-evaluation agent and send to user via send-research-result

                REQUIRED THREAD COORDINATION:
                - Create separate threads for each phase
                - Wait for each agent to complete before proceeding to next phase
                - Pass results between phases (job spec → candidate profile → company profile → match evaluation)
                - Ensure match-evaluation agent receives all required inputs
                - WAIT for match-evaluation to send final score back to you
                - When you receive the final score, immediately send it to user via send-research-result

                INPUT REQUIREMENTS:
                - Candidate LinkedIn URL or profile information
                - Job description for role requirements
                - Company information (if available)

                IMPORTANT: If you do not have these specific inputs, ask the user to provide them.
                Do NOT attempt to gather general information or news from other agents.

                FINAL OUTPUT REQUIREMENT:
                You MUST ensure the workflow culminates in a match-evaluation agent producing:
                - Overall match score (0-100)
                - Sub-scores (skills, experience, culture, domain, logistics)
                - Decision (proceed/maybe/reject)
                - Detailed justification
                - Supporting evidence

                CRITICAL:
                - Only execute candidate research workflow when you have specific candidate research inputs
                - Do not call other agents (like firecrawl) for general tasks or news gathering
                - Do not endlessly chat. Follow the workflow, get the match score, deliver results, and complete.

                Available tools: {coral_tools_description}
                Current task: {query if query else "Execute candidate research workflow"}
                """,
            ),
            ("human", "{user_input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    print("[VERBOSE] Chat prompt template created successfully")

    print("[VERBOSE] Initializing chat model...")
    print("[VERBOSE] Model configuration:")
    print(f"[VERBOSE]   - model: {os.getenv('MODEL_NAME')}")
    print(f"[VERBOSE]   - provider: {os.getenv('MODEL_PROVIDER')}")
    print(f"[VERBOSE]   - api_key: {'***' if os.getenv('MODEL_API_KEY') else None}")
    print(
        f"[VERBOSE]   - temperature: {float(os.getenv('MODEL_TEMPERATURE', DEFAULT_TEMPERATURE))}"
    )
    print(
        f"[VERBOSE]   - max_tokens: {int(os.getenv('MODEL_MAX_TOKENS', DEFAULT_MAX_TOKENS))}"
    )
    print(f"[VERBOSE]   - base_url: {os.getenv('MODEL_BASE_URL', None)}")

    model = init_chat_model(
        model=os.getenv("MODEL_NAME"),
        model_provider=os.getenv("MODEL_PROVIDER"),
        api_key=os.getenv("MODEL_API_KEY"),
        temperature=float(os.getenv("MODEL_TEMPERATURE", DEFAULT_TEMPERATURE)),
        max_tokens=int(os.getenv("MODEL_MAX_TOKENS", DEFAULT_MAX_TOKENS)),
        base_url=os.getenv("MODEL_BASE_URL", None),
    )
    print("[VERBOSE] Chat model initialized successfully")

    print("[VERBOSE] Prefixing tool names to avoid conflicts...")
    agent_name = "interface"
    prefixed_coral_tools = prefix_tool_names(coral_tools, agent_name)

    print("[VERBOSE] Creating tool calling agent...")
    agent = create_tool_calling_agent(model, prefixed_coral_tools, prompt)
    print("[VERBOSE] Tool calling agent created successfully")

    print(
        "[VERBOSE] Creating agent executor with verbose=True and return_intermediate_steps=True"
    )
    executor = AgentExecutor(
        agent=agent,
        tools=prefixed_coral_tools,
        verbose=True,
        return_intermediate_steps=True,
    )
    print("[VERBOSE] Agent executor created successfully")

    return executor


async def main():
    """Main function to run the agent in a continuous loop with chat history."""
    print("[VERBOSE] ========== STARTING MAIN FUNCTION ==========")

    try:
        print("[VERBOSE] Loading configuration...")
        config = load_config()
        print("[VERBOSE] Configuration loaded successfully")

        print("[VERBOSE] Preparing Coral Server connection parameters...")

        coral_server_url = config["coral_connection_url"]
        print(f"[VERBOSE] Coral server URL constructed: {coral_server_url}")
        logger.info(f"Connecting to Coral Server: {coral_server_url}")

        print("[VERBOSE] Setting up MCP client...")
        timeout = float(os.getenv("TIMEOUT_MS", "30000"))
        print(f"[VERBOSE] Using timeout: {timeout}ms")

        client = MultiServerMCPClient(
            connections={
                "coral": {
                    "transport": "sse",
                    "url": coral_server_url,
                    "timeout": timeout,
                    "sse_read_timeout": timeout,
                }
            }
        )
        print("[VERBOSE] MCP client created")
        logger.info("Coral Server connection established")

        print("[VERBOSE] Retrieving coral tools...")
        coral_tools = await client.get_tools(server_name="coral")
        print(f"[VERBOSE] Retrieved {len(coral_tools)} coral tools:")
        for i, tool in enumerate(coral_tools):
            print(f"[VERBOSE]   Tool {i + 1}: {tool.name}")
        logger.info(f"Retrieved {len(coral_tools)} coral tools")

        print("[VERBOSE] Checking runtime mode...")
        if config["runtime"] is not None:
            print(
                "[VERBOSE] Runtime mode detected - will wait for Coral system messages"
            )
            available_tools = [tool.name for tool in coral_tools]
            print(f"[VERBOSE] Available tools: {available_tools}")
        else:
            print("[VERBOSE] Interactive mode - will use direct user input")

        print("[VERBOSE] Creating agent tools dictionary...")
        agent_tools = {tool.name: tool for tool in coral_tools}
        print(f"[VERBOSE] Agent tools dictionary created with {len(agent_tools)} tools")

        print("[VERBOSE] Creating agent executor...")
        agent_executor = await create_agent(coral_tools)
        logger.info("Agent executor created")

        print("[VERBOSE] Initializing chat history...")
        chat_history: List[Dict[str, str]] = []
        print(f"[VERBOSE] Chat history initialized (max size: {MAX_CHAT_HISTORY})")

        print("[VERBOSE] ========== ENTERING TASK EXECUTION ==========")

        # Check if we're in single-task mode (for testing) or continuous mode
        single_task_mode = os.getenv("SINGLE_TASK_MODE", "false").lower() == "true"
        max_iterations = (
            1 if single_task_mode else 10
        )  # Limit iterations even in continuous mode

        loop_iteration = 0
        task_completed = False

        while loop_iteration < max_iterations and not task_completed:
            try:
                loop_iteration += 1
                print(
                    f"[VERBOSE] --- Task iteration {loop_iteration} (max: {max_iterations}) ---"
                )

                print("[VERBOSE] Getting user input...")
                user_input = await get_user_input(config["runtime"], agent_tools)

                # Check for task completion signals
                if user_input.lower() in ["exit", "quit", "done", "complete"]:
                    print("[VERBOSE] Task completion signal received")
                    task_completed = True
                    break

                print("[VERBOSE] Formatting chat history...")
                formatted_history = format_chat_history(chat_history)
                print(
                    f"[VERBOSE] Chat history formatted: {len(formatted_history)} characters"
                )

                print("[VERBOSE] Invoking agent executor...")
                print("[VERBOSE] Agent executor input:")
                print(f"[VERBOSE]   - user_input: {user_input}")
                print(
                    f"[VERBOSE]   - chat_history length: {len(formatted_history)} chars"
                )

                result = await agent_executor.ainvoke(
                    {
                        "user_input": user_input,
                        "agent_scratchpad": [],
                        "chat_history": formatted_history,
                    }
                )

                print(
                    f"[VERBOSE] Agent executor completed. Result keys: {list(result.keys())}"
                )
                response = result.get("output", "No output returned")
                print(f"[VERBOSE] Extracted response: {len(response)} characters")

                print("[VERBOSE] Sending response...")
                await send_response(config["runtime"], agent_tools, response)

                print("[VERBOSE] Updating chat history...")
                chat_history.append({"user_input": user_input, "response": response})
                print(
                    f"[VERBOSE] Chat history updated. Current size: {len(chat_history)}"
                )

                if len(chat_history) > MAX_CHAT_HISTORY:
                    removed = chat_history.pop(0)
                    print(
                        f"[VERBOSE] Chat history size exceeded {MAX_CHAT_HISTORY}, removed oldest entry"
                    )
                    print(
                        f"[VERBOSE] Removed entry preview: {removed['user_input'][:50]}..."
                    )

                # In single task mode, complete after processing one request
                if single_task_mode:
                    print("[VERBOSE] Single task mode - completing after one iteration")
                    task_completed = True
                else:
                    print(f"[VERBOSE] Sleeping for {SLEEP_INTERVAL} seconds...")
                    await asyncio.sleep(SLEEP_INTERVAL)

                print(
                    f"[VERBOSE] Task iteration {loop_iteration} completed successfully"
                )

            except Exception as e:
                print(
                    f"[VERBOSE] ERROR in agent loop iteration {loop_iteration}: {str(e)}"
                )
                print(f"[VERBOSE] Exception type: {type(e).__name__}")
                logger.error(f"Error in agent loop: {str(e)}")
                print(
                    f"[VERBOSE] Sleeping for {ERROR_RETRY_INTERVAL} seconds before retry..."
                )
                await asyncio.sleep(ERROR_RETRY_INTERVAL)

        # Task execution completed
        if task_completed:
            print("[VERBOSE] ========== TASK COMPLETED SUCCESSFULLY ==========")
        else:
            print(
                f"[VERBOSE] ========== MAXIMUM ITERATIONS ({max_iterations}) REACHED =========="
            )

        print(f"[VERBOSE] Final iteration count: {loop_iteration}")
        print("[VERBOSE] Interface agent terminating gracefully")

    except Exception as e:
        print(f"[VERBOSE] FATAL ERROR in main function: {str(e)}")
        print(f"[VERBOSE] Fatal exception type: {type(e).__name__}")
        logger.error(f"Fatal error in main: {str(e)}")
        print("[VERBOSE] ========== MAIN FUNCTION TERMINATING ==========")
        raise


if __name__ == "__main__":
    asyncio.run(main())
