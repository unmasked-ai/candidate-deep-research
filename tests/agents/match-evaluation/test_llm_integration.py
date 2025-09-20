import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../agents/match-evaluation"))
#!/usr/bin/env python3
"""
Real LLM Integration Tests for match-evaluation agent
Tests the full agent including LangChain, LLM calls, and tool execution
"""

import asyncio
import json
import os
from unittest.mock import Mock, AsyncMock, patch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_real_llm_scoring():
    """Test the agent with real LLM calls using mock Coral tools"""

    print("=== Real LLM Integration Test ===")
    print(f"Using Model: {os.getenv('MODEL_NAME')}")
    print(f"Provider: {os.getenv('MODEL_PROVIDER')}")
    print(f"Base URL: {os.getenv('MODEL_BASE_URL')}")
    print()

    # Import after loading env
    from main import create_agent, make_scorecard_tool

    # Create mock Coral tools
    mock_send_message = AsyncMock()
    mock_wait_for_mentions = AsyncMock()

    # Mock tools that simulate Coral protocol with proper attributes
    send_tool = Mock()
    send_tool.name = "send_message"
    send_tool.__name__ = "send_message"
    send_tool.args = {"content": {"type": "string"}, "thread_id": {"type": "string"}}
    send_tool.ainvoke = mock_send_message

    wait_tool = Mock()
    wait_tool.name = "wait_for_mentions"
    wait_tool.__name__ = "wait_for_mentions"
    wait_tool.args = {"timeout": {"type": "number"}}
    wait_tool.ainvoke = mock_wait_for_mentions

    coral_tools = [send_tool, wait_tool]

    # Create local tools
    local_tools = [make_scorecard_tool()]

    # Create the agent
    print("Creating agent with real LLM...")
    agent_executor = await create_agent(coral_tools, local_tools)
    print("✅ Agent created successfully")

    # Test case: High-quality candidate match
    test_input = {
        "agent_scratchpad": [],
        "input": json.dumps({
            "action": "evaluate_match",
            "job_spec": {
                "role_title": "Senior Python Engineer",
                "seniority": "senior",
                "tech_stack": ["python", "postgres", "docker", "kubernetes"],
                "must_have_hard_skills": ["python", "postgres", "docker"],
                "nice_to_have_hard_skills": ["kubernetes", "aws", "terraform"],
                "soft_skills": ["leadership", "communication", "problem-solving"],
                "industry": "fintech",
                "domain_knowledge": ["financial-services", "payments"],
                "experience_requirements": {"years_min": 5.0, "years_pref": 7.0},
                "location": {"type": "hybrid", "cities": ["London", "New York"]},
                "salary_range": {"currency": "GBP", "min": 90000, "max": 130000, "period": "year"}
            },
            "candidate_profile": {
                "name": "Sarah Chen",
                "years_experience": 8.0,
                "current_title": "Senior Software Engineer",
                "skills": ["python", "postgres", "docker", "kubernetes", "aws", "react", "microservices"],
                "certifications": ["aws-solutions-architect", "kubernetes-admin"],
                "education": ["MSc Computer Science", "BSc Mathematics"],
                "roles_history": [
                    "Senior Software Engineer at PayTech Solutions (3 years)",
                    "Software Engineer at FinanceApp Ltd (2 years)",
                    "Junior Developer at StartupCorp (3 years)"
                ],
                "locations": {"type": "hybrid", "cities": ["London"]},
                "salary_expectation": {"currency": "GBP", "min": 95000, "max": 125000, "period": "year"},
                "industry_experience": ["fintech", "financial-services", "payments"]
            },
            "company_profile": {
                "name": "FinTech Innovations Ltd",
                "industry": "fintech",
                "locations": ["London", "Remote-UK"],
                "culture_values": ["innovation", "ownership", "collaboration", "excellence"],
                "tech_stack": ["python", "postgres", "kubernetes", "aws"],
                "salary_benchmarks": {"currency": "GBP", "min": 85000, "max": 135000, "period": "year"},
                "culture_fit": {"score": 88, "notes": ["Strong alignment with innovation mindset", "Excellent collaborative skills"]}
            }
        })
    }

    print("Testing with high-quality candidate match...")

    # Mock the Coral tools to capture what would be sent
    responses = []

    async def mock_send_response(content, thread_id=None, **kwargs):
        responses.append(content)
        return {"status": "sent"}

    mock_send_message.side_effect = mock_send_response

    try:
        # Execute the agent
        result = await agent_executor.ainvoke(test_input)

        print("✅ Agent execution completed")
        print(f"Responses captured: {len(responses)}")

        # Check if we got a response
        if responses:
            response_content = responses[-1]  # Get the last response
            try:
                # Try to parse as JSON
                if isinstance(response_content, str):
                    scorecard = json.loads(response_content)
                else:
                    scorecard = response_content

                print("\n📊 SCORECARD RESULTS:")
                print(f"Overall Score: {scorecard.get('overall_score', 'N/A')}/100")
                print(f"Decision: {scorecard.get('decision', 'N/A')}")
                print(f"Justification: {scorecard.get('justification', 'N/A')}")

                if 'sub_scores' in scorecard:
                    print("\nSub-scores:")
                    for dimension, score in scorecard['sub_scores'].items():
                        print(f"  {dimension.capitalize()}: {score}/100")

                if 'reasons' in scorecard and scorecard['reasons']:
                    print(f"\nKey Reasons:")
                    for reason in scorecard['reasons'][:3]:  # Show top 3
                        print(f"  • {reason}")

                if 'missing_data' in scorecard and scorecard['missing_data']:
                    print(f"\nMissing Data: {scorecard['missing_data']}")

                # Validate the scorecard structure
                assert 'overall_score' in scorecard, "Missing overall_score"
                assert 'decision' in scorecard, "Missing decision"
                assert 'justification' in scorecard, "Missing justification"
                assert 'sub_scores' in scorecard, "Missing sub_scores"

                # Validate score ranges
                assert 0 <= scorecard['overall_score'] <= 100, "Overall score out of range"
                assert scorecard['decision'] in ['proceed', 'maybe', 'reject'], "Invalid decision"

                # Validate justification length
                word_count = len(scorecard['justification'].split())
                assert word_count <= 100, f"Justification too long: {word_count} words"

                print(f"\n✅ High-quality candidate test PASSED")
                print(f"   Score: {scorecard['overall_score']}/100, Decision: {scorecard['decision']}")

                return scorecard

            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse response as JSON: {e}")
                print(f"Raw response: {response_content}")
                return None
        else:
            print("❌ No responses captured from agent")
            return None

    except Exception as e:
        print(f"❌ Agent execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_poor_match_llm():
    """Test with a poor candidate match"""

    print("\n=== Testing Poor Match with Real LLM ===")

    from main import create_agent, make_scorecard_tool

    # Create mock tools with proper attributes
    mock_send_message = AsyncMock()

    send_tool = Mock()
    send_tool.name = "send_message"
    send_tool.__name__ = "send_message"
    send_tool.args = {"content": {"type": "string"}}
    send_tool.ainvoke = mock_send_message

    wait_tool = Mock()
    wait_tool.name = "wait_for_mentions"
    wait_tool.__name__ = "wait_for_mentions"
    wait_tool.args = {"timeout": {"type": "number"}}
    wait_tool.ainvoke = AsyncMock()

    coral_tools = [send_tool, wait_tool]

    local_tools = [make_scorecard_tool()]
    agent_executor = await create_agent(coral_tools, local_tools)

    # Poor match test case
    test_input = {
        "agent_scratchpad": [],
        "input": json.dumps({
            "action": "evaluate_match",
            "job_spec": {
                "role_title": "Senior AI/ML Engineer",
                "seniority": "senior",
                "tech_stack": ["python", "tensorflow", "pytorch", "cuda"],
                "must_have_hard_skills": ["machine-learning", "deep-learning", "python", "tensorflow"],
                "industry": "ai-research",
                "experience_requirements": {"years_min": 7.0},
                "location": {"type": "onsite", "cities": ["San Francisco"]}
            },
            "candidate_profile": {
                "name": "John Smith",
                "years_experience": 2.0,
                "current_title": "Frontend Developer",
                "skills": ["javascript", "react", "css", "html"],
                "industry_experience": ["e-commerce", "web-development"],
                "locations": {"type": "remote", "cities": ["Austin"]}
            }
        })
    }

    responses = []

    async def capture_response(content, **kwargs):
        responses.append(content)
        return {"status": "sent"}

    mock_send_message.side_effect = capture_response

    try:
        result = await agent_executor.ainvoke(test_input)

        if responses:
            response_content = responses[-1]
            if isinstance(response_content, str):
                scorecard = json.loads(response_content)
            else:
                scorecard = response_content

            print(f"Overall Score: {scorecard.get('overall_score', 'N/A')}/100")
            print(f"Decision: {scorecard.get('decision', 'N/A')}")
            print(f"Justification: {scorecard.get('justification', 'N/A')}")

            # Should be a poor match
            assert scorecard['overall_score'] < 50, f"Expected poor score, got {scorecard['overall_score']}"
            assert scorecard['decision'] == 'reject', f"Expected reject, got {scorecard['decision']}"

            print("✅ Poor match test PASSED")
            return scorecard

    except Exception as e:
        print(f"❌ Poor match test failed: {e}")
        return None

async def test_missing_data_llm():
    """Test with incomplete data"""

    print("\n=== Testing Missing Data Handling with Real LLM ===")

    from main import create_agent, make_scorecard_tool

    mock_send_message = AsyncMock()

    send_tool = Mock()
    send_tool.name = "send_message"
    send_tool.__name__ = "send_message"
    send_tool.args = {"content": {"type": "string"}}
    send_tool.ainvoke = mock_send_message

    wait_tool = Mock()
    wait_tool.name = "wait_for_mentions"
    wait_tool.__name__ = "wait_for_mentions"
    wait_tool.args = {"timeout": {"type": "number"}}
    wait_tool.ainvoke = AsyncMock()

    coral_tools = [send_tool, wait_tool]

    local_tools = [make_scorecard_tool()]
    agent_executor = await create_agent(coral_tools, local_tools)

    # Minimal data test case
    test_input = {
        "agent_scratchpad": [],
        "input": json.dumps({
            "action": "evaluate_match",
            "job_spec": {
                "role_title": "Software Engineer",
                "must_have_hard_skills": ["python"]
            },
            "candidate_profile": {
                "name": "Minimal Candidate",
                "skills": ["python", "java"]
            }
            # No company_profile
        })
    }

    responses = []

    async def capture_response(content, **kwargs):
        responses.append(content)
        return {"status": "sent"}

    mock_send_message.side_effect = capture_response

    try:
        result = await agent_executor.ainvoke(test_input)

        if responses:
            response_content = responses[-1]
            if isinstance(response_content, str):
                scorecard = json.loads(response_content)
            else:
                scorecard = response_content

            print(f"Overall Score: {scorecard.get('overall_score', 'N/A')}/100")
            print(f"Decision: {scorecard.get('decision', 'N/A')}")
            print(f"Missing Data: {scorecard.get('missing_data', [])}")

            # Should note missing data
            assert len(scorecard.get('missing_data', [])) > 0, "Should report missing data"

            print("✅ Missing data test PASSED")
            return scorecard

    except Exception as e:
        print(f"❌ Missing data test failed: {e}")
        return None

async def run_all_llm_tests():
    """Run all LLM integration tests"""

    print("🚀 Starting Real LLM Integration Tests for Match Evaluation Agent")
    print("=" * 70)

    try:
        # Test 1: High-quality match
        result1 = await test_real_llm_scoring()

        # Test 2: Poor match
        result2 = await test_poor_match_llm()

        # Test 3: Missing data
        result3 = await test_missing_data_llm()

        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY:")

        if result1:
            print(f"✅ High-quality match: {result1['overall_score']}/100 ({result1['decision']})")
        else:
            print("❌ High-quality match: FAILED")

        if result2:
            print(f"✅ Poor match: {result2['overall_score']}/100 ({result2['decision']})")
        else:
            print("❌ Poor match: FAILED")

        if result3:
            print(f"✅ Missing data: {result3['overall_score']}/100 (missing: {len(result3.get('missing_data', []))} items)")
        else:
            print("❌ Missing data: FAILED")

        success_count = sum([1 for r in [result1, result2, result3] if r is not None])
        print(f"\nOverall: {success_count}/3 tests passed")

        if success_count == 3:
            print("🎉 ALL LLM INTEGRATION TESTS PASSED!")
        else:
            print("⚠️  Some tests failed - check logs above")

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_all_llm_tests())