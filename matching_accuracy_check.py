from matching_engine import calculate_match

# Hand-crafted test cases with a known expected fit tier.
# "expected" is based on manual judgment of the skill/experience/education overlap.
TEST_CASES = [
    {
        "label": "Perfect skill overlap",
        "candidate": {"skills": ["Python", "SQL", "Git", "REST APIs"], "experience": ["3 years experience"], "education": ["B.Tech Computer Science"]},
        "job": {"required_skills": ["Python", "SQL", "Git", "REST APIs"], "required_experience_years": 2, "required_education": ["Bachelor degree"]},
        "expected_tier": "Strong",
    },
    {
        "label": "Most skills match, slightly under-experienced",
        "candidate": {"skills": ["Python", "SQL", "Git"], "experience": ["1 year experience"], "education": ["B.Tech Computer Science"]},
        "job": {"required_skills": ["Python", "SQL", "Git", "Docker"], "required_experience_years": 3, "required_education": ["Bachelor degree"]},
        "expected_tier": "Moderate",
    },
    {
        "label": "Half the required skills missing",
        "candidate": {"skills": ["Java", "SQL"], "experience": ["2 years experience"], "education": ["B.Tech Computer Science"]},
        "job": {"required_skills": ["Python", "TensorFlow", "SQL", "Machine Learning"], "required_experience_years": 2, "required_education": ["Bachelor degree"]},
        "expected_tier": "Weak",
    },
    {
        "label": "Almost no overlap",
        "candidate": {"skills": ["Java", "Spring Boot"], "experience": ["1 year experience"], "education": ["Diploma"]},
        "job": {"required_skills": ["Python", "TensorFlow", "Machine Learning", "SQL"], "required_experience_years": 5, "required_education": ["Master degree"]},
        "expected_tier": "Weak",
    },
    {
        "label": "Full skills, no experience requirement",
        "candidate": {"skills": ["Python", "Java", "SQL"], "experience": [], "education": ["B.E. Computer Science"]},
        "job": {"required_skills": ["Python", "Java", "SQL"], "required_experience_years": 0, "required_education": ["Bachelor degree"]},
        "expected_tier": "Strong",
    },
    {
        "label": "Zero skill overlap",
        "candidate": {"skills": ["Project Management"], "experience": ["4 years experience"], "education": ["MBA"]},
        "job": {"required_skills": ["Python", "Docker", "Kubernetes"], "required_experience_years": 2, "required_education": ["Bachelor degree"]},
        "expected_tier": "Weak",
    },
]

def get_tier(score):
    if score >= 85:
        return "Strong"
    elif score >= 60:
        return "Moderate"
    else:
        return "Weak"

def get_accuracy_results():
    """Returns (accuracy_percent, list_of_result_rows) — used by the Streamlit UI."""
    rows = []
    correct = 0

    for case in TEST_CASES:
        score, _ = calculate_match(case["candidate"], case["job"])
        predicted_tier = get_tier(score)
        is_correct = predicted_tier == case["expected_tier"]
        correct += int(is_correct)

        rows.append({
            "Test Case": case["label"],
            "Score": f"{score}%",
            "Predicted": predicted_tier,
            "Expected": case["expected_tier"],
            "Result": "✅ Pass" if is_correct else "❌ Fail",
        })

    accuracy = round((correct / len(TEST_CASES)) * 100, 1)
    return accuracy, rows

def run_matching_accuracy_check():
    """Terminal/CLI version — prints a readable table."""
    accuracy, rows = get_accuracy_results()
    print(f"{'Test Case':<40} {'Score':<8} {'Predicted':<10} {'Expected':<10} {'Result'}")
    print("-" * 85)
    for row in rows:
        print(f"{row['Test Case']:<40} {row['Score']:<8} {row['Predicted']:<10} {row['Expected']:<10} {row['Result']}")
    print("-" * 85)
    print(f"Matching Accuracy: {accuracy}% ({sum(1 for r in rows if 'Pass' in r['Result'])}/{len(rows)} test cases correct)")
    return accuracy

if __name__ == "__main__":
    run_matching_accuracy_check()