import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../agents/match-evaluation"))
#!/usr/bin/env python3
"""
Simple LLM Test - Direct function testing with real LLM model initialization
Tests the scoring logic without complex LangChain agent setup
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_model_connection():
    """Test that we can connect to the LLM"""

    print("🔧 Testing LLM Connection")
    print(f"Model: {os.getenv('MODEL_NAME')}")
    print(f"Provider: {os.getenv('MODEL_PROVIDER')}")
    print(f"Base URL: {os.getenv('MODEL_BASE_URL')}")

    try:
        from langchain.chat_models import init_chat_model

        model = init_chat_model(
            model=os.getenv("MODEL_NAME", "x-ai/grok-4-fast:free"),
            model_provider=os.getenv("MODEL_PROVIDER", "openai"),
            api_key=os.getenv("MODEL_API_KEY"),
            temperature=float(os.getenv("MODEL_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("MODEL_MAX_TOKENS", "8000")),
            base_url=os.getenv("MODEL_BASE_URL", "https://openrouter.ai/api/v1")
        )

        # Test a simple prompt
        response = await model.ainvoke("What is 2+2? Answer with just the number.")

        print(f"✅ Model connection successful")
        print(f"Test response: {response.content}")

        return True

    except Exception as e:
        print(f"❌ Model connection failed: {e}")
        return False

async def test_direct_scoring():
    """Test the scoring function directly with comprehensive data"""

    print("\n🎯 Testing Direct Scoring Function")

    try:
        from main import calculate_match_score

        # High-quality match test
        test_data = {
            "job_spec": {
                "role_title": "Senior Python Engineer",
                "seniority": "senior",
                "tech_stack": ["python", "postgres", "docker", "kubernetes"],
                "must_have_hard_skills": ["python", "postgres", "docker"],
                "nice_to_have_hard_skills": ["kubernetes", "aws"],
                "industry": "fintech",
                "experience_requirements": {"years_min": 5.0},
                "location": {"type": "hybrid", "cities": ["London"]},
                "salary_range": {"currency": "GBP", "min": 85000, "max": 120000, "period": "year"}
            },
            "candidate_profile": {
                "name": "Expert Developer",
                "years_experience": 8.0,
                "current_title": "Senior Software Engineer",
                "skills": ["python", "postgres", "docker", "kubernetes", "aws", "fastapi"],
                "industry_experience": ["fintech", "banking"],
                "locations": {"type": "hybrid", "cities": ["London"]},
                "salary_expectation": {"currency": "GBP", "min": 90000, "max": 115000, "period": "year"}
            },
            "company_profile": {
                "name": "FinTech Corp",
                "industry": "fintech",
                "culture_fit": {"score": 85, "notes": ["Great cultural alignment"]}
            }
        }

        result = calculate_match_score(test_data)
        scorecard = json.loads(result)

        print(f"Overall Score: {scorecard['overall_score']}/100")
        print(f"Decision: {scorecard['decision']}")
        print(f"Justification: {scorecard['justification']}")
        print(f"Sub-scores: {scorecard['sub_scores']}")

        # Validate results
        assert 'overall_score' in scorecard
        assert 'justification' in scorecard
        assert scorecard['overall_score'] >= 70  # Should be high for this perfect match

        print("✅ Direct scoring test passed")
        return scorecard

    except Exception as e:
        print(f"❌ Direct scoring test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_scoring_variations():
    """Test scoring with different candidate quality levels"""

    print("\n📊 Testing Scoring Variations")

    from main import calculate_match_score

    test_cases = [
        {
            "name": "Perfect Match",
            "data": {
                "job_spec": {
                    "role_title": "Python Developer",
                    "must_have_hard_skills": ["python", "postgres"],
                    "experience_requirements": {"years_min": 3.0},
                    "industry": "tech"
                },
                "candidate_profile": {
                    "name": "Perfect Candidate",
                    "years_experience": 5.0,
                    "skills": ["python", "postgres", "docker"],
                    "industry_experience": ["tech"]
                },
                "company_profile": {
                    "industry": "tech",
                    "culture_fit": {"score": 90}
                }
            }
        },
        {
            "name": "Moderate Match",
            "data": {
                "job_spec": {
                    "role_title": "Senior Developer",
                    "seniority": "senior",
                    "must_have_hard_skills": ["python", "postgres"],
                    "experience_requirements": {"years_min": 5.0},
                    "industry": "fintech"
                },
                "candidate_profile": {
                    "name": "Moderate Candidate",
                    "years_experience": 4.0,  # Slightly below requirement
                    "current_title": "Developer",  # Not senior
                    "skills": ["python", "mysql"],  # Has python but mysql instead of postgres
                    "industry_experience": ["ecommerce"]  # Different industry
                },
                "company_profile": {
                    "industry": "fintech",
                    "culture_fit": {"score": 60}
                }
            }
        },
        {
            "name": "Poor Match",
            "data": {
                "job_spec": {
                    "role_title": "Senior AI Engineer",
                    "must_have_hard_skills": ["machine-learning", "python", "tensorflow"],
                    "experience_requirements": {"years_min": 7.0},
                    "industry": "ai"
                },
                "candidate_profile": {
                    "name": "Poor Match",
                    "years_experience": 1.0,
                    "skills": ["javascript", "react"],
                    "industry_experience": ["web-development"]
                }
            }
        }
    ]

    results = []

    for test_case in test_cases:
        try:
            result = calculate_match_score(test_case["data"])
            scorecard = json.loads(result)

            score = scorecard['overall_score']
            decision = scorecard['decision']
            justification = scorecard['justification']

            print(f"\n{test_case['name']}:")
            print(f"  Score: {score}/100")
            print(f"  Decision: {decision}")
            print(f"  Justification: {justification}")

            results.append({
                "name": test_case['name'],
                "score": score,
                "decision": decision,
                "success": True
            })

        except Exception as e:
            print(f"\n{test_case['name']}: ❌ FAILED - {e}")
            results.append({
                "name": test_case['name'],
                "success": False
            })

    return results

async def test_justification_quality():
    """Test that justifications are meaningful and under word limit"""

    print("\n📝 Testing Justification Quality")

    from main import calculate_match_score

    test_data = {
        "job_spec": {
            "role_title": "Full Stack Developer",
            "must_have_hard_skills": ["python", "react", "postgres"],
            "nice_to_have_hard_skills": ["docker", "aws"],
            "experience_requirements": {"years_min": 4.0},
            "industry": "saas"
        },
        "candidate_profile": {
            "name": "Test Candidate",
            "years_experience": 6.0,
            "skills": ["python", "react", "postgres", "docker"],
            "industry_experience": ["saas", "fintech"]
        },
        "company_profile": {
            "industry": "saas",
            "culture_fit": {"score": 75}
        }
    }

    try:
        result = calculate_match_score(test_data)
        scorecard = json.loads(result)

        justification = scorecard['justification']
        word_count = len(justification.split())

        print(f"Justification ({word_count} words):")
        print(f'"{justification}"')

        # Check word count
        assert word_count <= 100, f"Justification too long: {word_count} words"

        # Check content quality
        assert len(justification) > 20, "Justification too short"
        assert str(scorecard['overall_score']) in justification, "Should mention overall score"

        print("✅ Justification quality test passed")
        return True

    except Exception as e:
        print(f"❌ Justification quality test failed: {e}")
        return False

async def run_simple_tests():
    """Run all simple LLM tests"""

    print("🚀 SIMPLE LLM INTEGRATION TESTS")
    print("=" * 50)

    results = []

    # Test 1: Model connection
    connection_ok = await test_model_connection()
    results.append(("Model Connection", connection_ok))

    # Test 2: Direct scoring
    scoring_result = await test_direct_scoring()
    results.append(("Direct Scoring", scoring_result is not None))

    # Test 3: Scoring variations
    if scoring_result:
        variations = await test_scoring_variations()
        variation_success = all(r.get('success', False) for r in variations)
        results.append(("Scoring Variations", variation_success))

        # Test 4: Justification quality
        justification_ok = await test_justification_quality()
        results.append(("Justification Quality", justification_ok))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY:")
    print("=" * 50)

    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1

    print(f"\nOverall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 ALL SIMPLE LLM TESTS PASSED!")
        print("The match-evaluation scoring system is working correctly!")
    else:
        print("\n⚠️  Some tests failed - check logs above")

    return passed == len(results)

if __name__ == "__main__":
    asyncio.run(run_simple_tests())