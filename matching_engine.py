import re

EXPERIENCE_PATTERN = re.compile(r'(\d+)\+?\s*(?:to\s*\d+\s*)?years?', re.I)

DEGREE_LEVELS = {
    "diploma": 1,
    "b.tech": 2, "btech": 2, "b.e.": 2, "be": 2, "bachelor": 2,
    "m.tech": 3, "mtech": 3, "master": 3,
}

def estimate_experience_years(experience_lines):
    max_years = 0
    for line in experience_lines:
        match = EXPERIENCE_PATTERN.search(line)
        if match:
            max_years = max(max_years, int(match.group(1)))
    return max_years

def get_degree_level(education_lines):
    level = 0
    text = " ".join(education_lines).lower()
    for keyword, lvl in DEGREE_LEVELS.items():
        if keyword in text:
            level = max(level, lvl)
    return level

def calculate_match(candidate, job):
    required_skills = set(job.get("required_skills", []))
    candidate_skills = set(candidate.get("skills", []))
    matched_skills = required_skills.intersection(candidate_skills)
    skill_score = (len(matched_skills) / len(required_skills)) if required_skills else 1.0

    cand_years = estimate_experience_years(candidate.get("experience", []))
    req_years = job.get("required_experience_years", 0)
    exp_score = min(cand_years / req_years, 1.0) if req_years > 0 else 1.0

    cand_level = get_degree_level(candidate.get("education", []))
    req_level = get_degree_level(job.get("required_education", []))
    edu_score = 1.0 if req_level == 0 else min(cand_level / req_level, 1.0)

    hiring_score = round((skill_score * 0.6 + exp_score * 0.25 + edu_score * 0.15) * 100, 2)

    return hiring_score, matched_skills

def skill_gap_analysis(candidate, job):
    required_skills = set(job.get("required_skills", []))
    candidate_skills = set(candidate.get("skills", []))
    missing_skills = required_skills - candidate_skills

    return {
        "candidate": candidate.get("name"),
        "job_title": job.get("title"),
        "matched_skills": list(required_skills.intersection(candidate_skills)),
        "missing_skills": list(missing_skills),
        "recommendations": [f"Consider training in {skill}" for skill in missing_skills]
    }

def match_all_candidates(candidates_df, job):
    results = []
    for _, candidate in candidates_df.iterrows():
        candidate_dict = candidate.to_dict()
        score, matched = calculate_match(candidate_dict, job)
        gap_report = skill_gap_analysis(candidate_dict, job)
        results.append({
            "name": candidate_dict.get("name"),
            "email": candidate_dict.get("email"),
            "hiring_score": score,
            "matched_skills": list(matched),
            "missing_skills": gap_report["missing_skills"],
            "recommendations": gap_report["recommendations"],
        })
    results.sort(key=lambda x: x["hiring_score"], reverse=True)
    return results