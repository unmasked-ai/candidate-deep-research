#!/usr/bin/env python3
"""
Standalone test script for match-evaluation agent scoring functions
Tests the core logic without requiring Coral Protocol or other agents
"""

import json
import sys
import os

# Add the agent directory to the Python path so we can import main
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../agents/match-evaluation'))

from main import calculate_match_score

def test_perfect_match():
    """Test case: Perfect candidate match"""
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
            "name": "Alex Smith",
            "years_experience": 7.0,
            "current_title": "Senior Software Engineer",
            "skills": ["python", "postgres", "docker", "kubernetes", "react"],
            "industry_experience": ["fintech", "banking"],
            "locations": {"type": "hybrid", "cities": ["London"]},
            "salary_expectation": {"currency": "GBP", "min": 85000, "max": 110000, "period": "year"}
        },
        "company_profile": {
            "name": "TechCorp",
            "industry": "fintech",
            "culture_values": ["ownership", "innovation"],
            "culture_fit": {"score": 85, "notes": ["Strong cultural alignment"]}
        }
    }

    result = calculate_match_score(test_data)
    score_data = json.loads(result)

    print(f"Perfect Match Test:")
    print(f"Overall Score: {score_data['overall_score']}")
    print(f"Decision: {score_data['decision']}")
    print(f"Justification: {score_data['justification']}")
    print(f"Sub-scores: {score_data['sub_scores']}")
    print("---")

    assert score_data['overall_score'] >= 75, "Perfect match should score >= 75"
    assert score_data['decision'] == "proceed", "Perfect match should be 'proceed'"
    return score_data

def test_poor_match():
    """Test case: Poor candidate match"""
    test_data = {
        "job_spec": {
            "role_title": "Senior Python Engineer",
            "seniority": "senior",
            "tech_stack": ["python", "postgres", "kubernetes"],
            "must_have_hard_skills": ["python", "postgres", "kubernetes"],
            "industry": "fintech",
            "experience_requirements": {"years_min": 8.0}
        },
        "candidate_profile": {
            "name": "Junior Dev",
            "years_experience": 1.0,
            "current_title": "Junior Developer",
            "skills": ["javascript", "mongodb"],
            "industry_experience": ["gaming"]
        }
    }

    result = calculate_match_score(test_data)
    score_data = json.loads(result)

    print(f"Poor Match Test:")
    print(f"Overall Score: {score_data['overall_score']}")
    print(f"Decision: {score_data['decision']}")
    print(f"Justification: {score_data['justification']}")
    print("---")

    assert score_data['overall_score'] < 50, "Poor match should score < 50"
    assert score_data['decision'] == "reject", "Poor match should be 'reject'"
    return score_data

def test_moderate_match():
    """Test case: Moderate candidate match"""
    test_data = {
        "job_spec": {
            "role_title": "Senior Python Engineer",
            "seniority": "senior",
            "tech_stack": ["python", "postgres", "kubernetes"],
            "must_have_hard_skills": ["python", "postgres"],
            "nice_to_have_hard_skills": ["kubernetes", "docker"],
            "industry": "fintech",
            "experience_requirements": {"years_min": 5.0}
        },
        "candidate_profile": {
            "name": "Mid Developer",
            "years_experience": 5.0,  # Meets minimum experience
            "current_title": "Software Engineer",  # Not senior level
            "skills": ["python", "postgres", "java"],  # Has must-haves but different tech stack
            "industry_experience": ["ecommerce"]  # Different industry
        },
        "company_profile": {
            "name": "FinTechCorp",
            "industry": "fintech",
            "culture_fit": {"score": 60}  # Moderate culture fit
        }
    }

    result = calculate_match_score(test_data)
    score_data = json.loads(result)

    print(f"Moderate Match Test:")
    print(f"Overall Score: {score_data['overall_score']}")
    print(f"Decision: {score_data['decision']}")
    print(f"Justification: {score_data['justification']}")
    print("---")

    assert 50 <= score_data['overall_score'] < 75, "Moderate match should score 50-74"
    assert score_data['decision'] == "maybe", "Moderate match should be 'maybe'"
    return score_data

def test_missing_data():
    """Test case: Missing company culture data"""
    test_data = {
        "job_spec": {
            "role_title": "Developer",
            "must_have_hard_skills": ["python"],
            "industry": "tech"
        },
        "candidate_profile": {
            "name": "Dev",
            "years_experience": 3.0,
            "skills": ["python", "javascript"]
        }
        # No company_profile - should handle gracefully
    }

    result = calculate_match_score(test_data)
    score_data = json.loads(result)

    print(f"Missing Data Test:")
    print(f"Overall Score: {score_data['overall_score']}")
    print(f"Missing Data: {score_data['missing_data']}")
    print(f"Justification: {score_data['justification']}")
    print("---")

    assert len(score_data['missing_data']) > 0, "Should note missing data"
    return score_data

def test_justification_word_count():
    """Test that justifications stay under 100 words"""
    # Run all tests and check justification lengths
    test_cases = [test_perfect_match(), test_poor_match(), test_moderate_match(), test_missing_data()]

    for i, case in enumerate(test_cases):
        justification = case['justification']
        word_count = len(justification.split())
        print(f"Test case {i+1} justification word count: {word_count}")
        assert word_count <= 100, f"Justification too long: {word_count} words"

if __name__ == "__main__":
    print("=== Match Evaluation Agent - Standalone Tests ===\n")

    try:
        test_perfect_match()
        test_poor_match()
        test_moderate_match()
        test_missing_data()
        test_justification_word_count()

        print("✅ All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()