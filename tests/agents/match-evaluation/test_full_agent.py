import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../agents/match-evaluation"))
#!/usr/bin/env python3
"""
Full Agent Test with Mock Coral Server
Tests the complete agent flow including the main event loop
"""

import asyncio
import json
import os
import threading
import time
from unittest.mock import Mock, AsyncMock, patch
from dotenv import load_dotenv

# Load environment
load_dotenv()

class MockCoralServer:
    """Mock Coral Server that simulates SSE and tool interactions"""

    def __init__(self):
        self.messages = []
        self.tools = []
        self.running = False

    def setup_tools(self):
        """Setup mock Coral tools"""

        async def mock_send_message(content, thread_id=None, recipient=None, **kwargs):
            """Mock send_message tool"""
            message = {
                "type": "response",
                "content": content,
                "thread_id": thread_id or "test-thread",
                "recipient": recipient,
                "timestamp": time.time()
            }
            self.messages.append(message)
            print(f"📤 Mock sent message to {recipient}: {content[:100]}...")
            return {"status": "sent", "message_id": f"msg-{len(self.messages)}"}

        async def mock_wait_for_mentions(timeout=30, **kwargs):
            """Mock wait_for_mentions tool - returns test data"""

            # Simulate receiving a mention with evaluation request
            mention = {
                "sender": "interface-agent",
                "thread_id": "test-thread-001",
                "content": json.dumps({
                    "action": "evaluate_match",
                    "job_spec": {
                        "role_title": "Senior Python Developer",
                        "seniority": "senior",
                        "tech_stack": ["python", "postgres", "redis", "docker"],
                        "must_have_hard_skills": ["python", "postgres", "api-development"],
                        "nice_to_have_hard_skills": ["redis", "docker", "kubernetes"],
                        "soft_skills": ["leadership", "mentoring", "communication"],
                        "industry": "fintech",
                        "domain_knowledge": ["payments", "financial-services"],
                        "experience_requirements": {"years_min": 5.0, "years_pref": 8.0},
                        "location": {"type": "hybrid", "cities": ["London"]},
                        "salary_range": {"currency": "GBP", "min": 85000, "max": 120000, "period": "year"},
                        "culture_requirements": ["collaborative", "innovative", "detail-oriented"],
                        "responsibilities": ["lead technical decisions", "mentor junior developers", "architect solutions"]
                    },
                    "candidate_profile": {
                        "name": "Alice Johnson",
                        "years_experience": 7.0,
                        "current_title": "Senior Software Engineer",
                        "skills": ["python", "postgres", "redis", "docker", "fastapi", "pytest", "git"],
                        "certifications": ["aws-developer", "scrum-master"],
                        "education": ["BSc Computer Science", "MSc Software Engineering"],
                        "roles_history": [
                            "Senior Software Engineer at PaymentTech Ltd (3 years)",
                            "Software Engineer at DataCorp (2 years)",
                            "Junior Developer at StartupXYZ (2 years)"
                        ],
                        "locations": {"type": "hybrid", "cities": ["London", "Manchester"]},
                        "salary_expectation": {"currency": "GBP", "min": 90000, "max": 115000, "period": "year"},
                        "industry_experience": ["fintech", "payments", "financial-services"]
                    },
                    "company_profile": {
                        "name": "InnovatePay Solutions",
                        "industry": "fintech",
                        "locations": ["London", "Remote-UK"],
                        "culture_values": ["innovation", "collaboration", "excellence", "customer-focus"],
                        "tech_stack": ["python", "postgres", "redis", "kubernetes", "aws"],
                        "salary_benchmarks": {"currency": "GBP", "min": 80000, "max": 125000, "period": "year"},
                        "culture_fit": {
                            "score": 82,
                            "notes": [
                                "Strong alignment with innovation mindset",
                                "Excellent collaborative approach in previous roles",
                                "Demonstrates customer-focused thinking"
                            ]
                        }
                    }
                }),
                "timestamp": time.time()
            }

            print(f"📥 Mock received mention from {mention['sender']}")
            return [mention]

        # Create tool mocks
        send_tool = Mock(name="send_message")
        send_tool.ainvoke = mock_send_message
        send_tool.args = {"content": {"type": "string"}, "thread_id": {"type": "string"}}

        wait_tool = Mock(name="wait_for_mentions")
        wait_tool.ainvoke = mock_wait_for_mentions
        wait_tool.args = {"timeout": {"type": "number"}}

        self.tools = [send_tool, wait_tool]
        return self.tools

    def get_sent_messages(self):
        """Get all messages sent by the agent"""
        return self.messages

async def test_full_agent_with_llm():
    """Test the complete agent including the event loop"""

    print("🚀 Full Agent Test with Real LLM")
    print("=" * 50)

    # Setup mock server
    mock_server = MockCoralServer()
    coral_tools = mock_server.setup_tools()

    # Import agent components
    from main import create_agent, make_scorecard_tool

    # Create agent
    local_tools = [make_scorecard_tool()]
    agent_executor = await create_agent(coral_tools, local_tools)

    print("✅ Agent created with real LLM")

    try:
        # Simulate one iteration of the agent loop
        print("🔄 Simulating agent event loop iteration...")

        # The agent will:
        # 1. Call wait_for_mentions and get our test data
        # 2. Process the mention with the LLM
        # 3. Call the calculate_match_score tool
        # 4. Send the response back via send_message

        result = await agent_executor.ainvoke({"agent_scratchpad": []})

        print("✅ Agent iteration completed")

        # Check what messages were sent
        sent_messages = mock_server.get_sent_messages()

        print(f"\n📊 RESULTS:")
        print(f"Messages sent by agent: {len(sent_messages)}")

        if sent_messages:
            latest_message = sent_messages[-1]

            print(f"Recipient: {latest_message.get('recipient', 'N/A')}")
            print(f"Thread ID: {latest_message.get('thread_id', 'N/A')}")

            # Try to parse the response as a ScoreCard
            content = latest_message['content']

            try:
                if isinstance(content, str):
                    scorecard = json.loads(content)
                else:
                    scorecard = content

                print(f"\n🎯 MATCH EVALUATION RESULTS:")
                print(f"Overall Score: {scorecard.get('overall_score', 'N/A')}/100")
                print(f"Decision: {scorecard.get('decision', 'N/A')}")
                print(f"Justification: {scorecard.get('justification', 'N/A')}")

                if 'sub_scores' in scorecard:
                    print(f"\nDetailed Scores:")
                    for dimension, score in scorecard['sub_scores'].items():
                        print(f"  {dimension.capitalize()}: {score}/100")

                if 'reasons' in scorecard and scorecard['reasons']:
                    print(f"\nKey Factors:")
                    for i, reason in enumerate(scorecard['reasons'][:5], 1):
                        print(f"  {i}. {reason}")

                # Validate the scorecard
                assert 'overall_score' in scorecard, "Missing overall_score"
                assert 'decision' in scorecard, "Missing decision"
                assert 'justification' in scorecard, "Missing justification"
                assert scorecard['decision'] in ['proceed', 'maybe', 'reject'], "Invalid decision"
                assert 0 <= scorecard['overall_score'] <= 100, "Score out of range"

                # Check justification length
                word_count = len(scorecard['justification'].split())
                assert word_count <= 100, f"Justification too long: {word_count} words"

                print(f"\n✅ FULL AGENT TEST PASSED!")
                print(f"   The agent successfully processed the evaluation request")
                print(f"   and returned a valid ScoreCard with real LLM reasoning")

                return scorecard

            except json.JSONDecodeError:
                print(f"❌ Could not parse agent response as JSON")
                print(f"Raw content: {content}")
                return None

        else:
            print("❌ No messages sent by agent")
            return None

    except Exception as e:
        print(f"❌ Full agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_agent_error_handling():
    """Test agent error handling with invalid data"""

    print("\n🔧 Testing Agent Error Handling")
    print("=" * 40)

    mock_server = MockCoralServer()

    # Setup tools with invalid data
    async def mock_wait_invalid(**kwargs):
        mention = {
            "sender": "interface-agent",
            "thread_id": "error-test",
            "content": json.dumps({
                "action": "evaluate_match",
                # Missing required job_spec and candidate_profile
                "invalid": "data"
            })
        }
        return [mention]

    async def mock_send_error(content, **kwargs):
        print(f"📤 Agent sent error response: {content}")
        return {"status": "sent"}

    wait_tool = Mock(name="wait_for_mentions")
    wait_tool.ainvoke = mock_wait_invalid
    wait_tool.args = {"timeout": {"type": "number"}}

    send_tool = Mock(name="send_message")
    send_tool.ainvoke = mock_send_error
    send_tool.args = {"content": {"type": "string"}}

    coral_tools = [send_tool, wait_tool]

    from main import create_agent, make_scorecard_tool
    local_tools = [make_scorecard_tool()]
    agent_executor = await create_agent(coral_tools, local_tools)

    try:
        result = await agent_executor.ainvoke({"agent_scratchpad": []})
        print("✅ Error handling test completed")
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

async def run_comprehensive_tests():
    """Run all comprehensive agent tests"""

    print("🎯 COMPREHENSIVE MATCH EVALUATION AGENT TESTS")
    print("=" * 60)
    print(f"Model: {os.getenv('MODEL_NAME')}")
    print(f"Provider: {os.getenv('MODEL_PROVIDER')}")
    print(f"Base URL: {os.getenv('MODEL_BASE_URL')}")
    print("=" * 60)

    results = []

    # Test 1: Full agent with real LLM
    result1 = await test_full_agent_with_llm()
    results.append(("Full Agent Test", result1 is not None))

    # Test 2: Error handling
    result2 = await test_agent_error_handling()
    results.append(("Error Handling", result2))

    # Print summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST SUMMARY:")
    print("=" * 60)

    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1

    print(f"\nOverall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 ALL COMPREHENSIVE TESTS PASSED!")
        print("The match-evaluation agent is fully functional with real LLM integration!")
    else:
        print("\n⚠️  Some tests failed - check details above")

    return passed == len(results)

if __name__ == "__main__":
    asyncio.run(run_comprehensive_tests())