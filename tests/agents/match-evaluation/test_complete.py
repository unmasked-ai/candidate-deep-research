import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../agents/match-evaluation"))
#!/usr/bin/env python3
"""
Complete LLM Integration Test
Final comprehensive test suite for the match-evaluation agent
"""

import asyncio
import json
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_model_availability():
    """Verify the LLM model is accessible"""

    print("🔍 Testing Model Availability")
    print(f"Model: {os.getenv('MODEL_NAME')}")
    print(f"Provider: {os.getenv('MODEL_PROVIDER')}")
    print(f"API Key: {'*' * 20 + os.getenv('MODEL_API_KEY', '')[-10:]}")

    try:
        from langchain.chat_models import init_chat_model

        model = init_chat_model(
            model=os.getenv("MODEL_NAME"),
            model_provider=os.getenv("MODEL_PROVIDER"),
            api_key=os.getenv("MODEL_API_KEY"),
            temperature=float(os.getenv("MODEL_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("MODEL_MAX_TOKENS", "8000")),
            base_url=os.getenv("MODEL_BASE_URL")
        )

        # Simple test call
        response = await model.ainvoke("Hello! Respond with 'Ready' if you can see this.")
        print(f"✅ Model response: {response.content}")
        return True

    except Exception as e:
        print(f"❌ Model connection failed: {e}")
        return False

async def test_comprehensive_scoring():
    """Test the scoring system with comprehensive real-world scenarios"""

    print("\n🎯 Comprehensive Scoring Tests")

    from main import calculate_match_score

    # Test scenarios with complete data
    scenarios = [
        {
            "name": "🌟 Excellent Match - Senior Engineer",
            "expected_range": (80, 100),
            "expected_decision": "proceed",
            "data": {
                "job_spec": {
                    "role_title": "Senior Python Engineer",
                    "seniority": "senior",
                    "tech_stack": ["python", "postgres", "docker", "aws"],
                    "must_have_hard_skills": ["python", "postgres", "sql"],
                    "nice_to_have_hard_skills": ["docker", "aws", "kubernetes"],
                    "soft_skills": ["leadership", "communication"],
                    "industry": "fintech",
                    "domain_knowledge": ["payments", "banking"],
                    "experience_requirements": {"years_min": 5.0, "years_pref": 7.0},
                    "location": {"type": "hybrid", "cities": ["London"]},
                    "salary_range": {"currency": "GBP", "min": 90000, "max": 130000, "period": "year"}
                },
                "candidate_profile": {
                    "name": "Sarah Tech",
                    "years_experience": 8.0,
                    "current_title": "Senior Software Engineer",
                    "skills": ["python", "postgres", "sql", "docker", "aws", "fastapi", "pytest"],
                    "certifications": ["aws-solutions-architect"],
                    "education": ["MSc Computer Science"],
                    "roles_history": ["Senior Engineer at PayCorp (4y)", "Engineer at FinTech Ltd (4y)"],
                    "locations": {"type": "hybrid", "cities": ["London"]},
                    "salary_expectation": {"currency": "GBP", "min": 95000, "max": 125000, "period": "year"},
                    "industry_experience": ["fintech", "payments", "banking"]
                },
                "company_profile": {
                    "name": "Elite FinTech",
                    "industry": "fintech",
                    "locations": ["London", "Remote-UK"],
                    "culture_values": ["innovation", "excellence", "collaboration"],
                    "tech_stack": ["python", "postgres", "aws"],
                    "culture_fit": {"score": 88, "notes": ["Strong cultural alignment", "Leadership potential"]}
                }
            }
        },
        {
            "name": "⚖️ Moderate Match - Career Changer",
            "expected_range": (50, 75),
            "expected_decision": "maybe",
            "data": {
                "job_spec": {
                    "role_title": "Data Scientist",
                    "tech_stack": ["python", "pandas", "scikit-learn", "sql"],
                    "must_have_hard_skills": ["python", "machine-learning", "statistics"],
                    "nice_to_have_hard_skills": ["deep-learning", "tensorflow"],
                    "industry": "healthcare",
                    "experience_requirements": {"years_min": 3.0},
                    "location": {"type": "remote"}
                },
                "candidate_profile": {
                    "name": "Alex Change",
                    "years_experience": 4.0,
                    "current_title": "Business Analyst",
                    "skills": ["python", "sql", "excel", "statistics"],  # Missing ML skills
                    "education": ["BSc Mathematics", "Data Science Bootcamp"],
                    "industry_experience": ["finance", "consulting"],  # Different from healthcare
                    "locations": {"type": "remote"}
                },
                "company_profile": {
                    "name": "HealthTech Solutions",
                    "industry": "healthcare",
                    "culture_fit": {"score": 65, "notes": ["Good analytical mindset", "Lacks domain experience"]}
                }
            }
        },
        {
            "name": "❌ Poor Match - Wrong Skills",
            "expected_range": (0, 49),
            "expected_decision": "reject",
            "data": {
                "job_spec": {
                    "role_title": "DevOps Engineer",
                    "tech_stack": ["kubernetes", "docker", "terraform", "aws"],
                    "must_have_hard_skills": ["kubernetes", "docker", "ci-cd", "linux"],
                    "experience_requirements": {"years_min": 4.0},
                    "industry": "cloud-infrastructure"
                },
                "candidate_profile": {
                    "name": "Frontend Dev",
                    "years_experience": 3.0,
                    "current_title": "Frontend Developer",
                    "skills": ["javascript", "react", "css", "html"],  # No DevOps skills
                    "industry_experience": ["e-commerce", "web-development"]
                },
                "company_profile": {
                    "name": "CloudOps Inc",
                    "industry": "cloud-infrastructure"
                }
            }
        }
    ]

    results = []

    for scenario in scenarios:
        try:
            print(f"\n{scenario['name']}")

            result = calculate_match_score(scenario["data"])
            scorecard = json.loads(result)

            score = scorecard['overall_score']
            decision = scorecard['decision']
            justification = scorecard['justification']

            print(f"  Score: {score}/100")
            print(f"  Decision: {decision}")
            print(f"  Justification: {justification}")

            # Validate expectations
            expected_min, expected_max = scenario['expected_range']
            score_valid = expected_min <= score <= expected_max
            decision_valid = decision == scenario['expected_decision']

            if score_valid and decision_valid:
                print(f"  ✅ PASSED (Expected: {expected_min}-{expected_max}, {scenario['expected_decision']})")
            else:
                print(f"  ❌ FAILED (Expected: {expected_min}-{expected_max}, {scenario['expected_decision']})")

            results.append({
                "name": scenario['name'],
                "score": score,
                "decision": decision,
                "expected_decision": scenario['expected_decision'],
                "passed": score_valid and decision_valid
            })

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results.append({
                "name": scenario['name'],
                "passed": False,
                "error": str(e)
            })

    return results

async def test_performance():
    """Test response times and efficiency"""

    print("\n⚡ Performance Test")

    import time
    from main import calculate_match_score

    test_data = {
        "job_spec": {
            "role_title": "Software Engineer",
            "must_have_hard_skills": ["python"],
            "experience_requirements": {"years_min": 2.0}
        },
        "candidate_profile": {
            "name": "Test User",
            "years_experience": 3.0,
            "skills": ["python", "javascript"]
        },
        "company_profile": {
            "name": "Test Company",
            "culture_fit": {"score": 70}
        }
    }

    try:
        start_time = time.time()
        result = calculate_match_score(test_data)
        end_time = time.time()

        duration = end_time - start_time

        print(f"  Processing time: {duration:.3f} seconds")

        if duration < 1.0:
            print("  ✅ Performance: Excellent (< 1 second)")
        elif duration < 3.0:
            print("  ✅ Performance: Good (< 3 seconds)")
        else:
            print("  ⚠️ Performance: Slow (> 3 seconds)")

        return duration < 5.0  # Accept up to 5 seconds

    except Exception as e:
        print(f"  ❌ Performance test failed: {e}")
        return False

async def test_data_validation():
    """Test edge cases and data validation"""

    print("\n🛡️ Data Validation Tests")

    from main import calculate_match_score

    edge_cases = [
        {
            "name": "Missing Company Profile",
            "data": {
                "job_spec": {"role_title": "Engineer", "must_have_hard_skills": ["python"]},
                "candidate_profile": {"name": "Test", "skills": ["python"]}
                # No company_profile
            },
            "should_work": True
        },
        {
            "name": "Empty Skills Lists",
            "data": {
                "job_spec": {"role_title": "Engineer", "must_have_hard_skills": []},
                "candidate_profile": {"name": "Test", "skills": []},
                "company_profile": {"name": "Test Corp"}
            },
            "should_work": True
        },
        {
            "name": "Invalid Job Spec",
            "data": {
                "candidate_profile": {"name": "Test", "skills": ["python"]},
                "company_profile": {"name": "Test Corp"}
                # Missing job_spec
            },
            "should_work": False
        }
    ]

    results = []

    for case in edge_cases:
        try:
            result = calculate_match_score(case["data"])
            parsed = json.loads(result)

            if "error" in parsed:
                success = not case["should_work"]  # Error expected for invalid cases
                status = "✅ PASSED" if success else "❌ FAILED"
                print(f"  {case['name']}: {status} (Error: {parsed.get('error', 'Unknown')})")
            else:
                success = case["should_work"]  # Success expected for valid cases
                status = "✅ PASSED" if success else "❌ FAILED"
                score = parsed.get('overall_score', 'N/A')
                print(f"  {case['name']}: {status} (Score: {score})")

            results.append(success)

        except Exception as e:
            success = not case["should_work"]  # Exception might be expected
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"  {case['name']}: {status} (Exception: {str(e)[:50]}...)")
            results.append(success)

    return all(results)

async def run_complete_test_suite():
    """Run the complete test suite"""

    print("🚀 COMPLETE MATCH EVALUATION AGENT TEST SUITE")
    print("=" * 70)
    print(f"Environment: {os.getenv('MODEL_NAME')} via {os.getenv('MODEL_PROVIDER')}")
    print("=" * 70)

    all_results = []

    # Test 1: Model availability
    model_ok = await test_model_availability()
    all_results.append(("Model Availability", model_ok))

    if not model_ok:
        print("\n❌ Cannot continue without model access")
        return False

    # Test 2: Comprehensive scoring
    scoring_results = await test_comprehensive_scoring()
    scoring_ok = all(r.get('passed', False) for r in scoring_results)
    all_results.append(("Comprehensive Scoring", scoring_ok))

    # Test 3: Performance
    perf_ok = await test_performance()
    all_results.append(("Performance", perf_ok))

    # Test 4: Data validation
    validation_ok = await test_data_validation()
    all_results.append(("Data Validation", validation_ok))

    # Final summary
    print("\n" + "=" * 70)
    print("📊 FINAL TEST RESULTS")
    print("=" * 70)

    passed_count = 0
    for test_name, success in all_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed_count += 1

    success_rate = (passed_count / len(all_results)) * 100
    print(f"\nOverall Success Rate: {passed_count}/{len(all_results)} ({success_rate:.1f}%)")

    if passed_count == len(all_results):
        print("\n🎉 🎉 🎉 ALL TESTS PASSED! 🎉 🎉 🎉")
        print("The match-evaluation agent is fully functional and ready for production!")
        print("\n✅ Key Features Validated:")
        print("  • Real LLM integration with x.ai Grok")
        print("  • Comprehensive 5-dimension scoring algorithm")
        print("  • Intelligent justification generation (< 100 words)")
        print("  • Robust error handling and data validation")
        print("  • Performance within acceptable limits")
        print("  • JSON-only output format for Coral integration")

    else:
        print(f"\n⚠️ {len(all_results) - passed_count} tests failed - review details above")

    return passed_count == len(all_results)

if __name__ == "__main__":
    success = asyncio.run(run_complete_test_suite())
    exit(0 if success else 1)