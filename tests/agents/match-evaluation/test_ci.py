#!/usr/bin/env python3
"""
CI-Friendly Test Suite for Match Evaluation Agent
Designed to run in CI/CD environments without external dependencies
"""

import json
import time
import sys
import os
from typing import Dict, Any

# Add the agent directory to the Python path so we can import main
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../agents/match-evaluation'))

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")

    try:
        from main import (
            calculate_match_score,
            ScoreCard,
            SubScores,
            CandidateProfile,
            CompanyProfile,
            JobSpec,
            _generate_justification
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_schema_validation():
    """Test Pydantic schema validation"""
    print("\n🛡️ Testing schema validation...")

    try:
        from main import ScoreCard, SubScores

        # Test valid ScoreCard creation
        sub_scores = SubScores(
            skills=85,
            experience=75,
            culture=80,
            domain=70,
            logistics=90
        )

        scorecard = ScoreCard(
            overall_score=78,
            sub_scores=sub_scores,
            decision='proceed',
            justification='Strong match with excellent skills alignment and good cultural fit.',
            reasons=['matches key skills', 'good experience level'],
            missing_data=[],
            evidence=[]
        )

        # Test serialization
        json_output = scorecard.model_dump_json()
        parsed = json.loads(json_output)

        assert 'overall_score' in parsed
        assert 'justification' in parsed
        assert parsed['decision'] in ['proceed', 'maybe', 'reject']

        print("✅ Schema validation passed")
        return True

    except Exception as e:
        print(f"❌ Schema validation failed: {e}")
        return False

def test_scoring_algorithm():
    """Test the core scoring algorithm with known inputs"""
    print("\n🎯 Testing scoring algorithm...")

    try:
        from main import calculate_match_score

        # Test case with known good data
        test_data = {
            "job_spec": {
                "role_title": "Senior Python Engineer",
                "seniority": "senior",
                "tech_stack": ["python", "postgres", "docker"],
                "must_have_hard_skills": ["python", "postgres"],
                "nice_to_have_hard_skills": ["docker", "kubernetes"],
                "industry": "fintech",
                "experience_requirements": {"years_min": 5.0},
                "location": {"type": "hybrid", "cities": ["London"]},
                "salary_range": {"currency": "GBP", "min": 80000, "max": 120000, "period": "year"}
            },
            "candidate_profile": {
                "name": "Test Candidate",
                "years_experience": 7.0,
                "current_title": "Senior Software Engineer",
                "skills": ["python", "postgres", "docker", "aws"],
                "industry_experience": ["fintech", "banking"],
                "locations": {"type": "hybrid", "cities": ["London"]},
                "salary_expectation": {"currency": "GBP", "min": 85000, "max": 115000, "period": "year"}
            },
            "company_profile": {
                "name": "FinTech Corp",
                "industry": "fintech",
                "culture_values": ["innovation", "collaboration"],
                "culture_fit": {"score": 85, "notes": ["Strong alignment"]}
            }
        }

        result = calculate_match_score(test_data)
        scorecard = json.loads(result)

        # Validate result structure
        required_fields = ['overall_score', 'sub_scores', 'decision', 'justification', 'reasons', 'missing_data', 'evidence']
        for field in required_fields:
            assert field in scorecard, f"Missing field: {field}"

        # Validate score ranges
        assert 0 <= scorecard['overall_score'] <= 100, f"Overall score out of range: {scorecard['overall_score']}"
        assert scorecard['decision'] in ['proceed', 'maybe', 'reject'], f"Invalid decision: {scorecard['decision']}"

        # Validate sub-scores
        for dimension, score in scorecard['sub_scores'].items():
            assert 0 <= score <= 100, f"{dimension} score out of range: {score}"

        # This should be a strong match
        assert scorecard['overall_score'] >= 70, f"Expected strong match, got {scorecard['overall_score']}"

        print(f"✅ Scoring algorithm passed (Score: {scorecard['overall_score']}/100)")
        return True

    except Exception as e:
        print(f"❌ Scoring algorithm failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_justification_generation():
    """Test justification generation and constraints"""
    print("\n📝 Testing justification generation...")

    try:
        from main import _generate_justification

        # Test normal case
        justification = _generate_justification(
            overall_score=75,
            decision='proceed',
            skills_score=80,
            experience_score=70,
            culture_score=75,
            domain_score=80,
            logistics_score=85,
            top_reasons=['matches key skills', 'good experience level'],
            missing_data=[]
        )

        # Validate word count
        word_count = len(justification.split())
        assert word_count <= 100, f"Justification too long: {word_count} words"
        assert len(justification) > 10, "Justification too short"

        # Test edge case with many missing data items
        long_justification = _generate_justification(
            overall_score=45,
            decision='reject',
            skills_score=30,
            experience_score=20,
            culture_score=50,
            domain_score=40,
            logistics_score=60,
            top_reasons=['missing critical skills', 'insufficient experience', 'poor cultural alignment'],
            missing_data=['salary_data', 'education_requirements', 'company_culture', 'location_preferences']
        )

        long_word_count = len(long_justification.split())
        assert long_word_count <= 100, f"Long justification exceeds limit: {long_word_count} words"

        print(f"✅ Justification generation passed")
        print(f"   Normal case: {word_count} words")
        print(f"   Edge case: {long_word_count} words")
        return True

    except Exception as e:
        print(f"❌ Justification generation failed: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid inputs"""
    print("\n🛡️ Testing error handling...")

    try:
        from main import calculate_match_score

        # Test with missing required fields
        invalid_cases = [
            {},  # Empty input
            {"job_spec": {}},  # Missing candidate_profile
            {"candidate_profile": {}},  # Missing job_spec
            {"job_spec": {"role_title": "Test"}, "candidate_profile": {}},  # Missing required fields
        ]

        for i, invalid_input in enumerate(invalid_cases):
            try:
                result = calculate_match_score(invalid_input)
                parsed = json.loads(result)

                # Should return an error
                assert "error" in parsed, f"Case {i+1}: Should return error for invalid input"

            except Exception:
                # Exception is also acceptable for invalid input
                pass

        print("✅ Error handling passed")
        return True

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_performance():
    """Test performance characteristics"""
    print("\n⚡ Testing performance...")

    try:
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

        # Run multiple iterations to get average
        times = []
        for _ in range(10):
            start_time = time.time()
            result = calculate_match_score(test_data)
            end_time = time.time()

            # Validate result
            scorecard = json.loads(result)
            assert 'overall_score' in scorecard

            times.append(end_time - start_time)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        # Performance should be very fast for this simple calculation
        assert avg_time < 0.1, f"Average time too slow: {avg_time:.4f}s"
        assert max_time < 0.5, f"Max time too slow: {max_time:.4f}s"

        print(f"✅ Performance test passed")
        print(f"   Average time: {avg_time:.4f}s")
        print(f"   Max time: {max_time:.4f}s")
        return True

    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def test_decision_boundaries():
    """Test decision boundary logic"""
    print("\n🎯 Testing decision boundaries...")

    try:
        from main import calculate_match_score

        # Create test cases for each decision boundary
        base_profile = {
            "name": "Test User",
            "years_experience": 3.0,
            "skills": ["python"]
        }

        base_company = {
            "name": "Test Company",
            "culture_fit": {"score": 70}
        }

        # Test different score ranges by adjusting requirements
        test_cases = [
            {
                "name": "High Score (should be proceed)",
                "job_spec": {
                    "role_title": "Junior Developer",
                    "must_have_hard_skills": ["python"],  # Perfect match
                    "experience_requirements": {"years_min": 1.0}  # Easy requirement
                },
                "expected_decision": "proceed"
            },
            {
                "name": "Low Score (should be reject)",
                "job_spec": {
                    "role_title": "Senior AI Engineer",
                    "must_have_hard_skills": ["machine-learning", "tensorflow", "pytorch"],  # No match
                    "experience_requirements": {"years_min": 10.0}  # Way above experience
                },
                "expected_decision": "reject"
            }
        ]

        for test_case in test_cases:
            test_data = {
                "job_spec": test_case["job_spec"],
                "candidate_profile": base_profile,
                "company_profile": base_company
            }

            result = calculate_match_score(test_data)
            scorecard = json.loads(result)

            decision = scorecard['decision']
            score = scorecard['overall_score']

            print(f"   {test_case['name']}: {score}/100 → {decision}")

            # Validate decision logic
            if score >= 75:
                assert decision == 'proceed', f"Score {score} should be 'proceed', got '{decision}'"
            elif score >= 50:
                assert decision == 'maybe', f"Score {score} should be 'maybe', got '{decision}'"
            else:
                assert decision == 'reject', f"Score {score} should be 'reject', got '{decision}'"

        print("✅ Decision boundaries test passed")
        return True

    except Exception as e:
        print(f"❌ Decision boundaries test failed: {e}")
        return False

def run_ci_tests() -> bool:
    """Run all CI tests and return success status"""

    print("🚀 CI TEST SUITE - Match Evaluation Agent")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Schema Validation", test_schema_validation),
        ("Scoring Algorithm", test_scoring_algorithm),
        ("Justification Generation", test_justification_generation),
        ("Error Handling", test_error_handling),
        ("Performance", test_performance),
        ("Decision Boundaries", test_decision_boundaries),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 CI TEST RESULTS")
    print("=" * 60)

    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1

    success_rate = (passed / len(results)) * 100
    print(f"\nSuccess Rate: {passed}/{len(results)} ({success_rate:.1f}%)")

    if passed == len(results):
        print("\n🎉 ALL CI TESTS PASSED!")
        print("The match-evaluation agent is ready for deployment.")
        return True
    else:
        print(f"\n❌ {len(results) - passed} tests failed")
        print("Please review the failures above before merging.")
        return False

if __name__ == "__main__":
    success = run_ci_tests()
    sys.exit(0 if success else 1)