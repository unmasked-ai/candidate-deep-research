import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../agents/match-evaluation"))
#!/usr/bin/env python3
"""
Mock Coral Protocol test for match-evaluation agent
Simulates the agent receiving mentions and responding
"""

import json
import asyncio
from unittest.mock import Mock, AsyncMock

async def test_coral_integration_mock():
    """Test the agent's Coral integration with mocked tools"""

    # Mock Coral tools
    mock_send_message = AsyncMock()
    mock_wait_for_mentions = AsyncMock()

    # Create mock tools list
    coral_tools = [
        Mock(name="send_message", args={}),
        Mock(name="wait_for_mentions", args={})
    ]

    # Mock mention data (what the agent would receive)
    mock_mention = {
        "content": json.dumps({
            "action": "evaluate_match",
            "job_spec": {
                "role_title": "Python Developer",
                "must_have_hard_skills": ["python", "postgres"],
                "industry": "tech",
                "experience_requirements": {"years_min": 3}
            },
            "candidate_profile": {
                "name": "Test Candidate",
                "years_experience": 5,
                "skills": ["python", "postgres", "docker"],
                "industry_experience": ["tech"]
            },
            "company_profile": {
                "name": "TestCorp",
                "industry": "tech",
                "culture_fit": {"score": 75}
            }
        }),
        "sender": "interface-agent",
        "thread_id": "test-thread-123"
    }

    # Test the mention processing
    print("Mock Coral Integration Test:")
    print(f"Received mention from: {mock_mention['sender']}")
    print(f"Thread ID: {mock_mention['thread_id']}")

    # Parse the mention content
    try:
        mention_data = json.loads(mock_mention['content'])
        print(f"Action: {mention_data['action']}")

        # Import and test the scoring function
        from main import calculate_match_score
        result = calculate_match_score(mention_data)
        result_data = json.loads(result)

        print(f"Response Score: {result_data['overall_score']}")
        print(f"Response Decision: {result_data['decision']}")
        print(f"Justification: {result_data['justification']}")

        # Simulate sending response back to sender
        response_message = {
            "to": mock_mention['sender'],
            "thread_id": mock_mention['thread_id'],
            "content": result
        }

        print(f"Would send response to: {response_message['to']}")
        print("✅ Mock integration test passed!")

        return result_data

    except Exception as e:
        print(f"❌ Mock integration test failed: {e}")
        raise

async def test_error_handling():
    """Test error handling with invalid input"""

    invalid_mention = {
        "content": json.dumps({
            "action": "evaluate_match",
            # Missing required fields
        }),
        "sender": "interface-agent"
    }

    try:
        mention_data = json.loads(invalid_mention['content'])
        from main import calculate_match_score
        result = calculate_match_score(mention_data)
        result_data = json.loads(result)

        print("Error Handling Test:")
        print(f"Error response: {result_data}")

        assert "error" in result_data, "Should return error for invalid input"
        print("✅ Error handling test passed!")

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        raise

if __name__ == "__main__":
    print("=== Match Evaluation Agent - Mock Coral Tests ===\n")

    async def run_tests():
        await test_coral_integration_mock()
        print()
        await test_error_handling()

    asyncio.run(run_tests())